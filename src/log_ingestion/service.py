"""
Log Ingestion Service (Main Orchestration)

Orchestrates the complete log ingestion pipeline:
1. Fetch logs from Rapid7 API
2. Parse CSV data
3. Write to Parquet files

See ADR-0001 for architecture decisions.
"""

from datetime import datetime
from typing import Any, Optional

from pathlib import Path

import structlog

import time

import json

import pandas as pd

import logging


from .api_client import Rapid7ApiClient
from .config import LogIngestionConfig
from .parquet_writer import ParquetWriter
from .parser import LogParser
from .cache_index import (
    CacheSegment,
    compute_missing_subranges,
    list_segments,
    segment_dir_for_range,
)
from src.log_ingestion.parquet_summary import generate_summary

logger = structlog.get_logger()


class LogIngestionService:
    """
    Main service orchestrating the log ingestion pipeline.

    Coordinates API client, CSV parser, and Parquet writer to fetch logs
    from Rapid7 InsightOps API and store them in Parquet format.

    Attributes:
        config: Configuration object
        api_client: Rapid7 API client
        parser: CSV log parser
        writer: Parquet file writer

    Example:
        config = LogIngestionConfig()
        service = LogIngestionService(config)
        result = service.run("2026-02-10T00:00:00Z", "2026-02-10T01:00:00Z")
    """

    def __init__(self, config: LogIngestionConfig):
        """Initialize the log ingestion service.

        Creates and configures all pipeline components.

        Args:
            config: LogInestionConfig object with service settings
        """
        self.config = config

        # Ensure cache_dir is always a Path (tests pass cache_dir as a str)
        if not isinstance(self.config.cache_dir, Path):
            self.config.cache_dir = Path(self.config.cache_dir)

        # Initialize components
        self.api_client = Rapid7ApiClient(config)
        self.parser = LogParser()
        self.writer = ParquetWriter(config)

        logger.info(
            "service_initialized",
            batch_size=config.batch_size,
            rate_limit=config.rate_limit,
            output_dir=str(config.output_dir),
            cache_dir=str(self.config.cache_dir),
            bypass_cache=bool(self.config.bypass_cache),
        )

    @staticmethod
    def _iso8601_to_epoch_millis(ts: str) -> str:
        """Convert ISO8601 timestamp to epoch milliseconds (as a string).

        Accepts timestamps ending with 'Z' and offsets (e.g., +00:00).
        Raises ValueError on invalid inputs.
        """
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        # Ensure timezone-aware.
        if dt.tzinfo is None:
            raise ValueError("Timestamp must include timezone information")
        return str(int(dt.timestamp() * 1000))

    @staticmethod
    def _looks_like_json_payload(value: str) -> bool:
        """Best-effort check for JSON-ish payloads.

        Important: empty/whitespace strings are NOT JSON payloads.
        """
        if not isinstance(value, str):
            return False
        s = value.lstrip()
        if not s:
            return False
        return s.startswith("{") or s.startswith("[")

    @staticmethod
    def _decode_events_payload(page_events: Any) -> Optional[list[dict[str, Any]]]:
        """Decode provider `events` field into a list[dict].

        Provider behaviors we handle:
        - events is already a list[dict]
        - events is a JSON string encoding a list[dict]
        - events is a JSON string encoding an object with an `events` list
        - events is a JSON string encoding a list[str], where each str is a JSON object
        """

        # Fast path: already a list
        if isinstance(page_events, list):
            out: list[dict[str, Any]] = []
            for ev in page_events:
                if isinstance(ev, dict):
                    out.append(ev)
                elif isinstance(ev, str) and LogIngestionService._looks_like_json_payload(ev):
                    try:
                        decoded_ev = json.loads(ev)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(decoded_ev, dict):
                        out.append(decoded_ev)
            return out

        if isinstance(page_events, str) and LogIngestionService._looks_like_json_payload(page_events):
            try:
                decoded = json.loads(page_events)
            except json.JSONDecodeError:
                return None

            if isinstance(decoded, list):
                # Could be list[dict] or list[str]
                return LogIngestionService._decode_events_payload(decoded)

            if isinstance(decoded, dict) and isinstance(decoded.get("events"), list):
                return LogIngestionService._decode_events_payload(decoded.get("events"))

        return None

    @staticmethod
    def _event_dedupe_key(ev: dict[str, Any]) -> Optional[str]:
        """Build a stable dedupe key for a Log Search event.

        Prefers provider-unique identifiers when present.
        """

        if not isinstance(ev, dict):
            return None

        log_id = ev.get("log_id")
        seq = ev.get("sequence_number_str")
        if seq is None:
            seq = ev.get("sequence_number")

        if log_id is None or seq is None:
            return None

        return f"{log_id}:{seq}"

    def _write_events_streaming_to_cache_segment(
        self,
        *,
        log_id: str,
        start_ms: int,
        end_ms: int,
        pages: list[dict[str, Any]],
    ) -> tuple[Optional[str], int, int, dict[str, Any]]:
        """Stream events page-by-page and flush to parquet parts in a cache segment dir.

        Returns:
            (dataset_path_str, rows_processed, parts_written, stream_stats)

        stream_stats keys (best-effort):
            raw_events_seen, duplicates_dropped, observed_min_ts_ms, observed_max_ts_ms,
            parquet_total_bytes_written, parquet_part_bytes_min, parquet_part_bytes_max
        """
        segment_dir = segment_dir_for_range(self.config.cache_dir, log_id, start_ms, end_ms)

        buffer: list[dict[str, Any]] = []
        rows_processed = 0
        part_idx = 0

        # Dedupe state (bounded by run, but avoids API page boundary duplication)
        dedupe_enabled = bool(getattr(self.config, "dedupe_events", True))
        seen_keys: set[str] = set()
        duplicates_dropped = 0
        raw_events_seen = 0

        observed_min_ts_ms: Optional[int] = None
        observed_max_ts_ms: Optional[int] = None

        parquet_total_bytes_written = 0
        parquet_part_bytes_min: Optional[int] = None
        parquet_part_bytes_max: Optional[int] = None

        def _update_part_bytes(num_bytes: Optional[int]) -> None:
            nonlocal parquet_total_bytes_written, parquet_part_bytes_min, parquet_part_bytes_max
            if num_bytes is None:
                return
            parquet_total_bytes_written += int(num_bytes)
            if parquet_part_bytes_min is None or int(num_bytes) < parquet_part_bytes_min:
                parquet_part_bytes_min = int(num_bytes)
            if parquet_part_bytes_max is None or int(num_bytes) > parquet_part_bytes_max:
                parquet_part_bytes_max = int(num_bytes)

        for page in pages:
            if not isinstance(page, dict):
                continue
            page_events_raw = page.get("events")
            page_events = self._decode_events_payload(page_events_raw)
            if not page_events:
                continue

            for ev in page_events:
                raw_events_seen += 1

                ts_val = ev.get("timestamp") if isinstance(ev, dict) else None
                if isinstance(ts_val, (int, float)):
                    ts_ms = int(ts_val)
                    observed_min_ts_ms = ts_ms if observed_min_ts_ms is None else min(observed_min_ts_ms, ts_ms)
                    observed_max_ts_ms = ts_ms if observed_max_ts_ms is None else max(observed_max_ts_ms, ts_ms)

                if dedupe_enabled:
                    key = self._event_dedupe_key(ev)
                    if key is not None:
                        if key in seen_keys:
                            duplicates_dropped += 1
                            continue
                        seen_keys.add(key)

                buffer.append(ev)
                rows_processed += 1

                if len(buffer) >= self.config.flush_rows:
                    logger.info(
                        "flush_start",
                        log_id=log_id,
                        segment_dir=str(segment_dir),
                        part_index=part_idx,
                        rows_buffered=len(buffer),
                        dedupe_enabled=dedupe_enabled,
                        raw_events_seen=raw_events_seen,
                        duplicates_dropped=duplicates_dropped,
                        unique_events_written_so_far=rows_processed,
                    )
                    df_part = pd.DataFrame(buffer)
                    output_file, file_size_bytes = self.writer.write_part(df_part, segment_dir, part_idx)
                    _update_part_bytes(file_size_bytes)
                    logger.info(
                        "flush_complete",
                        log_id=log_id,
                        segment_dir=str(segment_dir),
                        part_index=part_idx,
                        rows_written=len(df_part),
                        output_file=str(output_file) if output_file else None,
                        file_size_bytes=int(file_size_bytes) if file_size_bytes is not None else None,
                    )
                    part_idx += 1
                    buffer = []

        # Final flush
        if buffer:
            logger.info(
                "flush_start",
                log_id=log_id,
                segment_dir=str(segment_dir),
                part_index=part_idx,
                rows_buffered=len(buffer),
                dedupe_enabled=dedupe_enabled,
                raw_events_seen=raw_events_seen,
                duplicates_dropped=duplicates_dropped,
                unique_events_written_so_far=rows_processed,
            )
            df_part = pd.DataFrame(buffer)
            output_file, file_size_bytes = self.writer.write_part(df_part, segment_dir, part_idx)
            _update_part_bytes(file_size_bytes)
            logger.info(
                "flush_complete",
                log_id=log_id,
                segment_dir=str(segment_dir),
                part_index=part_idx,
                rows_written=len(df_part),
                output_file=str(output_file) if output_file else None,
                file_size_bytes=int(file_size_bytes) if file_size_bytes is not None else None,
            )
            part_idx += 1

        if rows_processed == 0:
            return None, 0, 0, {
                "dedupe_enabled": dedupe_enabled,
                "raw_events_seen": raw_events_seen,
                "duplicates_dropped": duplicates_dropped,
                "observed_min_ts_ms": observed_min_ts_ms,
                "observed_max_ts_ms": observed_max_ts_ms,
                "parquet_total_bytes_written": parquet_total_bytes_written,
                "parquet_part_bytes_min": parquet_part_bytes_min,
                "parquet_part_bytes_max": parquet_part_bytes_max,
            }

        logger.info(
            "dedupe_summary",
            log_id=log_id,
            segment_dir=str(segment_dir),
            dedupe_enabled=dedupe_enabled,
            raw_events_seen=raw_events_seen,
            duplicates_dropped=duplicates_dropped,
            unique_events_written=rows_processed,
        )

        # Return the directory path as the dataset location.
        return str(segment_dir), rows_processed, part_idx, {
            "dedupe_enabled": dedupe_enabled,
            "raw_events_seen": raw_events_seen,
            "duplicates_dropped": duplicates_dropped,
            "observed_min_ts_ms": observed_min_ts_ms,
            "observed_max_ts_ms": observed_max_ts_ms,
            "parquet_total_bytes_written": parquet_total_bytes_written,
            "parquet_part_bytes_min": parquet_part_bytes_min,
            "parquet_part_bytes_max": parquet_part_bytes_max,
        }

    def _emit_run_summary(
        self,
        *,
        log_id: str,
        cache_decision: str,
        result: dict[str, Any],
        requested_start_ms: Optional[int],
        requested_end_ms: Optional[int],
        missing_ranges: Optional[list[tuple[int, int]]] = None,
        cache_segments: Optional[list[CacheSegment]] = None,
        fetched_ranges: Optional[list[tuple[int, int]]] = None,
        fetch_stats: Optional[dict[str, Any]] = None,
        dataset_dirs: Optional[list[Path]] = None,
    ) -> None:
        """Emit a single end-of-run structured summary to reconcile what happened.

        This is additive observability: it should never change pipeline behavior.
        """
        dataset_path = result.get("output_file")

        # Prefer explicit dataset dirs when provided (multi-segment windows).
        dataset_paths: list[str] = []
        if dataset_dirs:
            dataset_paths = [str(p) for p in dataset_dirs]
        elif dataset_path is not None:
            dataset_paths = [str(dataset_path)]

        parquet_summary_dict: Optional[dict[str, Any]] = None
        parquet_dataset_stats: Optional[dict[str, Any]] = None

        # Derive dataset stats from the filesystem (helps reconcile CLI output).
        try:
            if dataset_dirs:
                total_bytes, part_files = self._dataset_disk_footprint(dataset_dirs)
                parquet_dataset_stats = {
                    "dataset_kind": "multi_directory",
                    "segment_count": int(len(dataset_dirs)),
                    "part_count": int(part_files),
                    "total_bytes": int(total_bytes),
                }
            elif dataset_path:
                dataset_path_p = Path(str(dataset_path))
                if dataset_path_p.exists():
                    if dataset_path_p.is_file():
                        total_bytes = int(dataset_path_p.stat().st_size)
                        parquet_dataset_stats = {
                            "dataset_kind": "file",
                            "part_count": 1,
                            "total_bytes": total_bytes,
                            "part_bytes_min": total_bytes,
                            "part_bytes_max": total_bytes,
                        }
                    elif dataset_path_p.is_dir():
                        parts = sorted(dataset_path_p.glob("*.parquet"))
                        part_sizes = [int(p.stat().st_size) for p in parts if p.exists() and p.is_file()]
                        parquet_dataset_stats = {
                            "dataset_kind": "directory",
                            "part_count": int(len(part_sizes)),
                            "total_bytes": int(sum(part_sizes)),
                            "part_bytes_min": int(min(part_sizes)) if part_sizes else None,
                            "part_bytes_max": int(max(part_sizes)) if part_sizes else None,
                        }
        except Exception as e:
            logger.warning(
                "parquet_dataset_stats_failed",
                dataset_paths=dataset_paths,
                error=str(e),
                exc_info=True,
            )

        # Parquet summary: if multiple dirs exist, summarize each and aggregate min/max timestamps.
        try:
            ts_min = None
            ts_max = None
            columns_union: set[str] = set()
            row_count_total = 0
            any_summary = False

            for p in (dataset_dirs or ([Path(str(dataset_path))] if dataset_path else [])):
                s = generate_summary(str(p))
                if s is None:
                    continue
                any_summary = True
                if s.columns:
                    columns_union.update(list(s.columns))
                if s.row_count is not None:
                    try:
                        row_count_total += int(s.row_count)
                    except Exception:
                        pass
                if s.timestamp_min is not None:
                    try:
                        v = int(s.timestamp_min)
                        ts_min = v if ts_min is None else min(ts_min, v)
                    except Exception:
                        pass
                if s.timestamp_max is not None:
                    try:
                        v = int(s.timestamp_max)
                        ts_max = v if ts_max is None else max(ts_max, v)
                    except Exception:
                        pass

            if any_summary:
                parquet_summary_dict = {
                    "row_count": int(row_count_total),
                    "columns": sorted(columns_union) if columns_union else None,
                    "timestamp_min": ts_min,
                    "timestamp_max": ts_max,
                }
        except Exception as e:
            logger.error(
                "parquet_summary_failed",
                dataset_paths=dataset_paths,
                error=str(e),
                exc_info=True,
            )

        raw_events_seen = result.get("raw_events_seen")
        duplicates_dropped = result.get("duplicates_dropped")
        rows_processed = result.get("rows_processed")
        dedupe_enabled = result.get("dedupe_enabled")

        reconciliation_ok = None
        reconciliation_delta = None
        try:
            if (
                isinstance(raw_events_seen, (int, float))
                and isinstance(duplicates_dropped, (int, float))
                and isinstance(rows_processed, (int, float))
            ):
                reconciliation_ok = int(raw_events_seen) == int(rows_processed) + int(duplicates_dropped)
                reconciliation_delta = int(raw_events_seen) - (int(rows_processed) + int(duplicates_dropped))
        except Exception:
            reconciliation_ok = None
            reconciliation_delta = None

        requested_start_iso = None
        requested_end_iso = None
        observed_min_iso = None
        observed_max_iso = None
        try:
            if requested_start_ms is not None:
                requested_start_iso = self._epoch_millis_to_iso8601(int(requested_start_ms))
            if requested_end_ms is not None:
                requested_end_iso = self._epoch_millis_to_iso8601(int(requested_end_ms))

            if result.get("observed_min_ts_ms") is not None:
                observed_min_iso = self._epoch_millis_to_iso8601(int(result.get("observed_min_ts_ms")))
            if result.get("observed_max_ts_ms") is not None:
                observed_max_iso = self._epoch_millis_to_iso8601(int(result.get("observed_max_ts_ms")))
        except Exception:
            pass

        cached_ranges = None
        if cache_segments:
            cached_ranges = [(int(s.start_ms), int(s.end_ms)) for s in cache_segments]

        logger.info(
            "run_summary",
            log_id=log_id,
            cache_decision=cache_decision,
            cache={
                "cache_hit": result.get("cache_hit"),
                "cache_partial": result.get("cache_partial"),
                "segments_used": result.get("segments_used"),
                "cached_ranges": cached_ranges,
                "missing_ranges": missing_ranges,
                "fetched_ranges": fetched_ranges,
            },
            requested_time_bounds={
                "requested_start_ms": requested_start_ms,
                "requested_end_ms": requested_end_ms,
                "requested_start_iso": requested_start_iso,
                "requested_end_iso": requested_end_iso,
            },
            observed_time_bounds={
                "observed_min_ts_ms": result.get("observed_min_ts_ms"),
                "observed_max_ts_ms": result.get("observed_max_ts_ms"),
                "observed_min_ts_iso": observed_min_iso,
                "observed_max_ts_iso": observed_max_iso,
            },
            duration_seconds=result.get("duration_seconds"),
            reconciliation={
                "raw_events_seen": raw_events_seen,
                "rows_processed": rows_processed,
                "duplicates_dropped": duplicates_dropped,
                "dedupe_enabled": dedupe_enabled,
                "reconciliation_ok": reconciliation_ok,
                "reconciliation_delta": reconciliation_delta,
            },
            fetch_stats=fetch_stats,
            parquet_write={
                "dataset_paths": dataset_paths,
                "parquet_parts_written": result.get("parquet_parts_written"),
                "parquet_total_bytes_written": result.get("parquet_total_bytes_written"),
                "parquet_part_bytes_min": result.get("parquet_part_bytes_min"),
                "parquet_part_bytes_max": result.get("parquet_part_bytes_max"),
            },
            parquet_dataset_stats=parquet_dataset_stats,
            parquet_summary=parquet_summary_dict,
        )

    def run(
        self, start_time: str, end_time: str, partition_date: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Execute the complete log ingestion pipeline.

        Fetches logs from Rapid7 API, parses CSV data, and writes to Parquet.

        Args:
            start_time: Start timestamp in ISO 8601 format (e.g., "2026-02-10T00:00:00Z")
            end_time: End timestamp in ISO 8601 format
            partition_date: Optional date for file partitioning (YYYY-MM-DD).
                          If None, extracted from start_time.

        Returns:
            Dictionary with pipeline results:
                - output_file: Path to written Parquet file (or None if empty)
                - rows_processed: Number of log rows processed
                - batches_processed: Number of batches processed
                - start_time: Pipeline start time
                - end_time: Pipeline end time

        Raises:
            Exception: If API fetch fails or critical error occurs

        Example:
            result = service.run("2026-02-10T00:00:00Z", "2026-02-10T01:00:00Z")
            print(f"Processed {result['rows_processed']} rows")
        """
        pipeline_start = datetime.now()

        try:
            # Convert ISO8601 -> epoch millis for Rapid7 query endpoint.
            start_time_millis = self._iso8601_to_epoch_millis(start_time)
            end_time_millis = self._iso8601_to_epoch_millis(end_time)
            if int(end_time_millis) <= int(start_time_millis):
                raise ValueError("end_time must be after start_time")

            requested_start_ms = int(start_time_millis)
            requested_end_ms = int(end_time_millis)
            log_id = self.config.rapid7_log_key

            # Derive partition_date if not provided (legacy CSV writer expectation)
            if partition_date is None:
                try:
                    partition_date = datetime.fromisoformat(start_time.replace("Z", "+00:00")).date().isoformat()
                except Exception:
                    partition_date = None

            logger.info(
                "pipeline_start",
                start_time=start_time,
                end_time=end_time,
                start_time_millis=start_time_millis,
                end_time_millis=end_time_millis,
                partition_date=partition_date,
            )

            # If cache is bypassed, use a non-caching ingestion path
            if self.config.bypass_cache:
                raw_payload = self.api_client.fetch_logs(str(requested_start_ms), str(requested_end_ms))

                if not raw_payload:
                    logger.warning(
                        "pipeline_empty_data",
                        rows_processed=0,
                        payload_format="empty",
                    )
                    logging.getLogger(__name__).warning("pipeline_empty_data")
                    return {
                        "output_file": None,
                        "rows_processed": 0,
                        "batches_processed": 0,
                        "cache_hit": False,
                        "cache_partial": False,
                        "segments_used": 0,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_seconds": (datetime.now() - pipeline_start).total_seconds(),
                    }

                # CSV path
                if not self._looks_like_json_payload(raw_payload):
                    df = self.parser.parse(raw_payload)
                    if df.empty:
                        logger.warning(
                            "pipeline_empty_data",
                            rows_processed=0,
                            payload_format="csv",
                        )
                        logging.getLogger(__name__).warning("pipeline_empty_data")
                        return {
                            "output_file": None,
                            "rows_processed": 0,
                            "batches_processed": 0,
                            "cache_hit": False,
                            "cache_partial": False,
                            "segments_used": 0,
                            "start_time": start_time,
                            "end_time": end_time,
                            "duration_seconds": (datetime.now() - pipeline_start).total_seconds(),
                        }

                    output_file = self.writer.write(df, partition_date=partition_date, append=False)
                    rows = int(len(df))
                    batches = (rows + max(1, int(self.config.batch_size)) - 1) // max(1, int(self.config.batch_size))
                    return {
                        "output_file": str(output_file) if output_file else None,
                        "rows_processed": rows,
                        "batches_processed": int(batches),
                        "cache_hit": False,
                        "cache_partial": False,
                        "segments_used": 0,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_seconds": (datetime.now() - pipeline_start).total_seconds(),
                    }

                # JSON pages path (streaming to bound memory)
                try:
                    payload = json.loads(raw_payload)
                except json.JSONDecodeError:
                    logger.warning(
                        "pipeline_empty_data",
                        rows_processed=0,
                        payload_format="json_decode_error",
                    )
                    logging.getLogger(__name__).warning("pipeline_empty_data")
                    return {
                        "output_file": None,
                        "rows_processed": 0,
                        "batches_processed": 0,
                        "cache_hit": False,
                        "cache_partial": False,
                        "segments_used": 0,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_seconds": (datetime.now() - pipeline_start).total_seconds(),
                    }

                pages = payload.get("pages")
                if not isinstance(pages, list):
                    logger.warning(
                        "pipeline_empty_data",
                        rows_processed=0,
                        payload_format="logsearch_json_pages",
                        fetch_id=payload.get("fetch_id"),
                    )
                    logging.getLogger(__name__).warning("pipeline_empty_data")
                    return {
                        "output_file": None,
                        "rows_processed": 0,
                        "batches_processed": 0,
                        "cache_hit": False,
                        "cache_partial": False,
                        "segments_used": 0,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_seconds": (datetime.now() - pipeline_start).total_seconds(),
                    }

                # Treat JSON as empty unless we can extract at least one event.
                extracted_any_events = False
                try:
                    for page in pages:
                        if not isinstance(page, dict):
                            continue
                        if "events" not in page:
                            continue
                        decoded = self._decode_events_payload(page.get("events"))
                        if decoded:
                            extracted_any_events = True
                            break
                except Exception:
                    extracted_any_events = False

                if not extracted_any_events:
                    logger.warning(
                        "pipeline_empty_data",
                        rows_processed=0,
                        payload_format="logsearch_json_pages",
                        fetch_id=payload.get("fetch_id"),
                        pages=len(pages),
                        events_total=0,
                    )
                    logging.getLogger(__name__).warning("pipeline_empty_data")
                    return {
                        "output_file": None,
                        "rows_processed": 0,
                        "batches_processed": 0,
                        "cache_hit": False,
                        "cache_partial": False,
                        "segments_used": 0,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_seconds": (datetime.now() - pipeline_start).total_seconds(),
                    }

                dataset_dir, rows_processed, parts_written, stream_stats = self._write_events_streaming_to_cache_segment(
                    log_id=log_id,
                    start_ms=requested_start_ms,
                    end_ms=requested_end_ms,
                    pages=pages,
                )

                if rows_processed == 0 or not dataset_dir:
                    logger.warning(
                        "pipeline_empty_data",
                        rows_processed=0,
                        payload_format="logsearch_json_pages",
                        fetch_id=payload.get("fetch_id"),
                        pages=len(pages),
                        events_total=0,
                    )
                    logging.getLogger(__name__).warning("pipeline_empty_data")
                    return {
                        "output_file": None,
                        "rows_processed": 0,
                        "batches_processed": 0,
                        "cache_hit": False,
                        "cache_partial": False,
                        "segments_used": 0,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_seconds": (datetime.now() - pipeline_start).total_seconds(),
                    }

                # Batches in the LogSearch streaming path map to parquet flushes (parts).
                result = {
                    "output_file": dataset_dir,
                    "rows_processed": int(rows_processed),
                    "batches_processed": int(parts_written),
                    "parquet_parts_written": int(parts_written),
                    "parquet_total_bytes_written": int(stream_stats.get("parquet_total_bytes_written", 0) or 0),
                    "parquet_part_bytes_min": stream_stats.get("parquet_part_bytes_min"),
                    "parquet_part_bytes_max": stream_stats.get("parquet_part_bytes_max"),
                    "raw_events_seen": int(stream_stats.get("raw_events_seen", 0) or 0),
                    "duplicates_dropped": int(stream_stats.get("duplicates_dropped", 0) or 0),
                    "observed_min_ts_ms": stream_stats.get("observed_min_ts_ms"),
                    "observed_max_ts_ms": stream_stats.get("observed_max_ts_ms"),
                    "dedupe_enabled": bool(stream_stats.get("dedupe_enabled")),
                    "cache_hit": False,
                    "cache_partial": False,
                    "segments_used": 1,
                    "start_time": start_time,
                    "end_time": end_time,
                    "start_time_millis": requested_start_ms,
                    "end_time_millis": requested_end_ms,
                    "duration_seconds": (datetime.now() - pipeline_start).total_seconds(),
                }

                logger.info(
                    "run_complete_summary",
                    log_id=log_id,
                    cache_decision="bypassed",
                    segments_used=1,
                    requested_start_ms=requested_start_ms,
                    requested_end_ms=requested_end_ms,
                    observed_min_ts_ms=result.get("observed_min_ts_ms"),
                    observed_max_ts_ms=result.get("observed_max_ts_ms"),
                    rows_processed=result.get("rows_processed"),
                    raw_events_seen=result.get("raw_events_seen"),
                    duplicates_dropped=result.get("duplicates_dropped"),
                    parquet_parts_written=result.get("parquet_parts_written"),
                    parquet_total_bytes_written=result.get("parquet_total_bytes_written"),
                    parquet_part_bytes_min=result.get("parquet_part_bytes_min"),
                    parquet_part_bytes_max=result.get("parquet_part_bytes_max"),
                    dedupe_enabled=result.get("dedupe_enabled"),
                )

                self._emit_run_summary(
                    log_id=log_id,
                    cache_decision="bypassed",
                    result=result,
                    requested_start_ms=requested_start_ms,
                    requested_end_ms=requested_end_ms,
                    cache_segments=list(segments_used),
                    dataset_dirs=final_dirs,
                )

                return result

            # Cache-enabled path: decide hit/partial/miss and fetch only missing ranges.
            decision_info = self._compute_cache_decision(
                log_id=log_id,
                requested_start_ms=requested_start_ms,
                requested_end_ms=requested_end_ms,
            )
            decision = decision_info["decision"]
            missing_ranges = decision_info["missing_ranges"]
            segments_used = decision_info["segments_used"]

            stdlog = logging.getLogger(__name__)

            if decision == "hit":
                logger.info(
                    "cache_hit",
                    log_id=log_id,
                    requested_start_ms=requested_start_ms,
                    requested_end_ms=requested_end_ms,
                    segments_used=len(segments_used),
                )
                stdlog.info("cache_hit")

                total_rows, segment_dirs = self._read_cached_segments(segments_used)

                parquet_total_bytes_written = None
                parquet_parts_written = None
                if segment_dirs:
                    parquet_total_bytes_written, parquet_parts_written = self._dataset_disk_footprint(segment_dirs)

                # Summarize across all segment dirs so multi-segment windows reconcile correctly.
                observed_min_ts_ms = None
                observed_max_ts_ms = None
                if segment_dirs:
                    try:
                        for d in segment_dirs:
                            s = generate_summary(str(d))
                            if s is None:
                                continue
                            if s.timestamp_min is not None:
                                try:
                                    v = int(s.timestamp_min)
                                    observed_min_ts_ms = v if observed_min_ts_ms is None else min(observed_min_ts_ms, v)
                                except Exception:
                                    pass
                            if s.timestamp_max is not None:
                                try:
                                    v = int(s.timestamp_max)
                                    observed_max_ts_ms = v if observed_max_ts_ms is None else max(observed_max_ts_ms, v)
                                except Exception:
                                    pass
                    except Exception:
                        # Observability only; cache hit behavior should still work.
                        observed_min_ts_ms = None
                        observed_max_ts_ms = None

                batches = (int(total_rows) + max(1, int(self.config.batch_size)) - 1) // max(1, int(self.config.batch_size))
                result = {
                    "output_file": str(segment_dirs[0]) if segment_dirs else None,
                    "rows_processed": int(total_rows),
                    "batches_processed": int(batches),
                    "cache_hit": True,
                    "cache_partial": False,
                    "segments_used": len(segment_dirs),
                    "start_time": start_time,
                    "end_time": end_time,
                    "start_time_millis": requested_start_ms,
                    "end_time_millis": requested_end_ms,
                    "observed_min_ts_ms": observed_min_ts_ms,
                    "observed_max_ts_ms": observed_max_ts_ms,
                    "raw_events_seen": None,
                    "duplicates_dropped": None,
                    "dedupe_enabled": None,
                    "parquet_parts_written": int(parquet_parts_written) if parquet_parts_written is not None else None,
                    "parquet_total_bytes_written": int(parquet_total_bytes_written) if parquet_total_bytes_written is not None else None,
                    "duration_seconds": (datetime.now() - pipeline_start).total_seconds(),
                }

                logger.info(
                    "service_complete",
                    result=result,
                    cache_decision="hit",
                )

                self._emit_run_summary(
                    log_id=log_id,
                    cache_decision="hit",
                    result=result,
                    requested_start_ms=requested_start_ms,
                    requested_end_ms=requested_end_ms,
                    cache_segments=list(segments_used),
                    dataset_dirs=final_dirs,
                )

                return result

            # If we have cached segments but we're not a hit, try reading them now.
            # This ensures corrupt cache fails loudly *before* hitting the API.
            if decision == "partial":
                if segments_used:
                    self._read_cached_segments(segments_used)

                logger.info(
                    "cache_partial",
                    log_id=log_id,
                    requested_start_ms=requested_start_ms,
                    requested_end_ms=requested_end_ms,
                    missing_ranges=missing_ranges,
                    segments_used=len(segments_used),
                )
                stdlog.info("cache_partial")
            else:
                logger.info(
                    "cache_miss",
                    log_id=log_id,
                    requested_start_ms=requested_start_ms,
                    requested_end_ms=requested_end_ms,
                )
                stdlog.info("cache_miss")

            if not missing_ranges:
                missing_ranges = [(requested_start_ms, requested_end_ms)]

            fetched_rows = 0
            parts_written_total = 0
            fetched_subranges = 0
            empty_subranges = 0
            pages_payloads_seen = 0
            api_payloads_seen = 0
            fetched_ranges: list[tuple[int, int]] = []

            # Track which segments we should include in the final row-count for this run.
            # - on miss: only segments created by this run (because the request window had no cache coverage)
            # - on partial: pre-existing overlapping segments + segments created by this run
            segments_to_count: list[CacheSegment] = []
            if decision == "partial":
                segments_to_count.extend(list(segments_used))

            # Reconciliation stats across all fetched segments in this run (best-effort)
            recon = {
                "raw_events_seen": 0,
                "duplicates_dropped": 0,
                "observed_min_ts_ms": None,
                "observed_max_ts_ms": None,
                "parquet_total_bytes_written": 0,
                "parquet_part_bytes_min": None,
                "parquet_part_bytes_max": None,
                "dedupe_enabled": bool(getattr(self.config, "dedupe_events", True)),
            }

            def _recon_update(part: dict[str, Any]) -> None:
                # ints
                for k in ("raw_events_seen", "duplicates_dropped", "parquet_total_bytes_written"):
                    v = part.get(k)
                    if isinstance(v, (int, float)):
                        recon[k] = int(recon.get(k, 0) or 0) + int(v)

                # observed ts min/max
                for src_key, dst_key, fn in (
                    ("observed_min_ts_ms", "observed_min_ts_ms", min),
                    ("observed_max_ts_ms", "observed_max_ts_ms", max),
                ):
                    v = part.get(src_key)
                    if isinstance(v, (int, float)):
                        v = int(v)
                        cur = recon.get(dst_key)
                        recon[dst_key] = v if cur is None else fn(int(cur), v)

                # part bytes min/max
                for src_key, dst_key, fn in (
                    ("parquet_part_bytes_min", "parquet_part_bytes_min", min),
                    ("parquet_part_bytes_max", "parquet_part_bytes_max", max),
                ):
                    v = part.get(src_key)
                    if isinstance(v, (int, float)):
                        v = int(v)
                        cur = recon.get(dst_key)
                        recon[dst_key] = v if cur is None else fn(int(cur), v)

            for (sub_start, sub_end) in missing_ranges:
                fetched_ranges.append((int(sub_start), int(sub_end)))
                raw_payload = self.api_client.fetch_logs(str(int(sub_start)), str(int(sub_end)))
                api_payloads_seen += 1

                # Empty response: treat this subrange as empty.
                if not raw_payload or (isinstance(raw_payload, str) and raw_payload.strip() == ""):
                    empty_subranges += 1
                    continue

                # CSV path: parse and write a regular parquet file under output_dir.
                if raw_payload and not self._looks_like_json_payload(raw_payload):
                    df = self.parser.parse(raw_payload)
                    if df.empty:
                        logger.warning(
                            "pipeline_empty_data",
                            rows_processed=0,
                            payload_format="csv",
                        )
                        logging.getLogger(__name__).warning("pipeline_empty_data")
                        return {
                            "output_file": None,
                            "rows_processed": 0,
                            "batches_processed": 0,
                            "cache_hit": False,
                            "cache_partial": False,
                            "segments_used": 0,
                            "start_time": start_time,
                            "end_time": end_time,
                            "duration_seconds": (datetime.now() - pipeline_start).total_seconds(),
                        }

                    output_file = self.writer.write(df, partition_date=partition_date, append=False)
                    rows = int(len(df))
                    batches = (rows + max(1, int(self.config.batch_size)) - 1) // max(1, int(self.config.batch_size))
                    return {
                        "output_file": str(output_file) if output_file else None,
                        "rows_processed": rows,
                        "batches_processed": int(batches),
                        "cache_hit": False,
                        "cache_partial": False,
                        "segments_used": 0,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration_seconds": (datetime.now() - pipeline_start).total_seconds(),
                    }

                # JSON path
                try:
                    payload = json.loads(raw_payload)
                except json.JSONDecodeError:
                    empty_subranges += 1
                    continue

                pages = payload.get("pages")
                if not isinstance(pages, list):
                    empty_subranges += 1
                    continue

                pages_payloads_seen += 1

                extracted_any_events = False
                try:
                    for page in pages:
                        if not isinstance(page, dict):
                            continue
                        decoded = self._decode_events_payload(page.get("events"))
                        if decoded:
                            extracted_any_events = True
                            break
                except Exception:
                    extracted_any_events = False

                if not extracted_any_events:
                    empty_subranges += 1
                    continue

                seg_dir_str, rows_processed, parts_written, stream_stats = (
                    self._write_events_streaming_to_cache_segment(
                        log_id=log_id,
                        start_ms=int(sub_start),
                        end_ms=int(sub_end),
                        pages=pages,
                    )
                )

                _recon_update(stream_stats)

                if int(rows_processed) == 0:
                    empty_subranges += 1
                    continue

                if seg_dir_str:
                    try:
                        segments_to_count.append(
                            CacheSegment(
                                log_id=log_id,
                                start_ms=int(sub_start),
                                end_ms=int(sub_end),
                                path=Path(seg_dir_str),
                            )
                        )
                    except Exception:
                        pass

                if rows_processed > 0:
                    fetched_subranges += 1

                fetched_rows += int(rows_processed)
                parts_written_total += int(parts_written)

            # If we extracted zero events across all missing ranges, treat window as empty.
            if fetched_rows == 0 and (empty_subranges == len(missing_ranges) or pages_payloads_seen == 0):
                logger.warning(
                    "pipeline_empty_data",
                    rows_processed=0,
                    payload_format="logsearch_json_pages",
                    missing_ranges=missing_ranges,
                    cached_segments=len(segments_used),
                )
                logging.getLogger(__name__).warning("pipeline_empty_data")
                result = {
                    "output_file": None,
                    "rows_processed": 0,
                    "batches_processed": 0,
                    "cache_hit": False,
                    "cache_partial": decision == "partial",
                    "segments_used": 0,
                    "start_time": start_time,
                    "end_time": end_time,
                    "start_time_millis": requested_start_ms,
                    "end_time_millis": requested_end_ms,
                    "raw_events_seen": int(recon.get("raw_events_seen") or 0),
                    "duplicates_dropped": int(recon.get("duplicates_dropped") or 0),
                    "dedupe_enabled": bool(recon.get("dedupe_enabled")),
                    "observed_min_ts_ms": recon.get("observed_min_ts_ms"),
                    "observed_max_ts_ms": recon.get("observed_max_ts_ms"),
                    "parquet_parts_written": int(parts_written_total),
                    "parquet_total_bytes_written": int(recon.get("parquet_total_bytes_written") or 0),
                    "parquet_part_bytes_min": recon.get("parquet_part_bytes_min"),
                    "parquet_part_bytes_max": recon.get("parquet_part_bytes_max"),
                    "duration_seconds": (datetime.now() - pipeline_start).total_seconds(),
                }
                self._emit_run_summary(
                    log_id=log_id,
                    cache_decision="empty",
                    result=result,
                    requested_start_ms=requested_start_ms,
                    requested_end_ms=requested_end_ms,
                    missing_ranges=missing_ranges,
                )
                return result

            # Build the final segment set to count.
            final_segments = [
                seg
                for seg in segments_to_count
                if (seg.start_ms < requested_end_ms and seg.end_ms > requested_start_ms)
            ]

            # If we fetched something this run, refresh from disk to account for concurrent writers,
            # but only in contexts where it won't inflate results with stale segments.
            if fetched_rows > 0:
                disk_overlapping = [
                    seg
                    for seg in list_segments(self.config.cache_dir, log_id)
                    if (seg.start_ms < requested_end_ms and seg.end_ms > requested_start_ms)
                ]
                if decision == "partial":
                    final_segments = disk_overlapping
                else:
                    # decision == "miss" --> only include segments that correspond to the missing ranges we fetched
                    fetched_ranges_set = {(int(s), int(e)) for (s, e) in missing_ranges}
                    final_segments = [
                        seg
                        for seg in disk_overlapping
                        if (int(seg.start_ms), int(seg.end_ms)) in fetched_ranges_set
                    ]

            total_rows, final_dirs = self._read_cached_segments(final_segments) if final_segments else (0, [])

            # New: compute final dataset size/parts across all final dirs (best-effort)
            parquet_total_bytes_written_final = None
            parquet_parts_written_final = None
            if final_dirs:
                parquet_total_bytes_written_final, parquet_parts_written_final = self._dataset_disk_footprint(final_dirs)

            # Emit summary info (best-effort)
            # If multiple segments were used/produced, summarize *all* directories that exist.
            try:
                for d in final_dirs:
                    generate_summary(str(d))
            except Exception:
                logger.error(
                    "parquet_summary_failed",
                    dataset_paths=[str(d) for d in final_dirs] if final_dirs else [],
                    exc_info=True,
                )

            # In segment-cache mode, we treat each subrange fetch as a batch.
            batches_processed = int(fetched_subranges)

            fetch_stats = {
                "missing_ranges_count": int(len(missing_ranges or [])),
                "fetched_subranges": int(fetched_subranges),
                "empty_subranges": int(empty_subranges),
                "api_payloads_seen": int(api_payloads_seen),
                "pages_payloads_seen": int(pages_payloads_seen),
                "parts_written_total": int(parts_written_total),
            }

            result = {
                "output_file": str(final_dirs[0]) if final_dirs else None,
                "rows_processed": int(total_rows),
                "batches_processed": int(batches_processed),
                "parquet_parts_written": int(parquet_parts_written_final) if parquet_parts_written_final is not None else int(parts_written_total),
                "cache_hit": False,
                "cache_partial": decision == "partial",
                "segments_used": len(final_dirs),
                "start_time": start_time,
                "end_time": end_time,
                "start_time_millis": requested_start_ms,
                "end_time_millis": requested_end_ms,
                "duration_seconds": (datetime.now() - pipeline_start).total_seconds(),
            }

            # Recon metrics across fetched segments + final disk footprint (if available)
            if recon is not None:
                result.update(
                    {
                        "raw_events_seen": recon.get("raw_events_seen"),
                        "duplicates_dropped": recon.get("duplicates_dropped"),
                        "observed_min_ts_ms": recon.get("observed_min_ts_ms"),
                        "observed_max_ts_ms": recon.get("observed_max_ts_ms"),
                        "parquet_total_bytes_written": int(parquet_total_bytes_written_final)
                        if parquet_total_bytes_written_final is not None
                        else recon.get("parquet_total_bytes_written"),
                        "parquet_part_bytes_min": recon.get("parquet_part_bytes_min"),
                        "parquet_part_bytes_max": recon.get("parquet_part_bytes_max"),
                        "dedupe_enabled": recon.get("dedupe_enabled"),
                    }
                )

            logger.info(
                "service_complete",
                result=result,
                cache_decision=decision,
                missing_ranges=missing_ranges if decision == "partial" else None,
            )

            self._emit_run_summary(
                log_id=log_id,
                cache_decision=decision,
                result=result,
                requested_start_ms=requested_start_ms,
                requested_end_ms=requested_end_ms,
                missing_ranges=missing_ranges if decision == "partial" else None,
                cache_segments=list(segments_used),
                fetched_ranges=fetched_ranges,
                fetch_stats=fetch_stats,
                dataset_dirs=final_dirs,
            )

            return result

        except Exception as e:
            logger.error(
                "pipeline_failed",
                error=str(e),
                start_time=start_time,
                end_time=end_time,
                exc_info=True,
            )
            raise

    def _compute_cache_decision(
        self,
        log_id: str,
        requested_start_ms: int,
        requested_end_ms: int,
    ) -> dict[str, Any]:
        """Compute cache decision: hit, miss, or partial.

        Cache plan + segment directory layout use half-open semantics:
            - requested window: [requested_start_ms, requested_end_ms)
            - cached segments:  [start_ms, end_ms)

        This matches `compute_missing_subranges` (REQ-029) and the cache tests.

        IMPORTANT:
        A cached segment may fully *contain* the requested window (e.g. cached [0,10000),
        requested [1000,5000)). In that case, we must treat the request as a cache *hit*
        (missing_ranges == []).
        """
        if self.config.bypass_cache:
            logger.info(
                "cache_bypass_enabled",
                log_id=log_id,
                requested_start_ms=requested_start_ms,
                requested_end_ms=requested_end_ms,
            )
            return {
                "decision": "miss",
                "missing_ranges": [(requested_start_ms, requested_end_ms)],
                "cached_ranges": [],
                "segments_used": [],
            }

        requested_start_ms = int(requested_start_ms)
        requested_end_ms = int(requested_end_ms)

        all_segments = list_segments(self.config.cache_dir, log_id)

        # Include only segments that overlap the requested window.
        segments_used = [
            seg
            for seg in all_segments
            if (int(seg.start_ms) < int(requested_end_ms) and int(seg.end_ms) > int(requested_start_ms))
        ]

        cached_ranges = [(int(s.start_ms), int(s.end_ms)) for s in segments_used]

        if not segments_used:
            return {
                "decision": "miss",
                "missing_ranges": [(requested_start_ms, requested_end_ms)],
                "cached_ranges": [],
                "segments_used": [],
            }

        # Coverage check must be computed relative to the requested window.
        # We do this by intersecting cached ranges with the requested window before
        # computing gaps.
        clipped_ranges: list[tuple[int, int]] = []
        for s, e in cached_ranges:
            s2 = max(int(s), requested_start_ms)
            e2 = min(int(e), requested_end_ms)
            if e2 > s2:
                clipped_ranges.append((s2, e2))

        missing_ranges = compute_missing_subranges(
            requested_start_ms=requested_start_ms,
            requested_end_ms=requested_end_ms,
            cached_ranges_ms=clipped_ranges,
        )

        decision = "hit" if not missing_ranges else "partial"

        return {
            "decision": decision,
            "missing_ranges": missing_ranges,
            "cached_ranges": cached_ranges,
            "segments_used": segments_used,
        }

    def _read_cached_segments(
        self,
        segments: list[CacheSegment],
    ) -> tuple[int, list[Path]]:
        """Read all parquet parts from cached segments and return total row count.

        Returns (total_rows, list_of_segment_dirs).

        NOTE: Each cache segment is a parquet *dataset directory* containing one or more
        part files. We count rows per directory by reading it as a dataset.
        """
        import pyarrow.dataset as ds

        total_rows = 0
        segment_dirs: list[Path] = []

        for seg in segments:
            try:
                dataset = ds.dataset(seg.path, format="parquet")
                total_rows += int(dataset.count_rows())
                segment_dirs.append(seg.path)
            except Exception as e:
                if self.config.bypass_cache:
                    logger.warning(
                        "cache_read_failed_bypass",
                        segment_path=str(seg.path),
                        error=str(e),
                    )
                    continue
                logger.error(
                    "cache_read_failed",
                    segment_path=str(seg.path),
                    error=str(e),
                    guidance="Set BYPASS_CACHE=true to skip corrupted cache or delete the segment directory.",
                )
                raise RuntimeError(
                    f"Cache read failed for segment {seg.path}: {e}. "
                    "Set BYPASS_CACHE=true to ignore cache or delete the corrupt segment."
                ) from e

        return total_rows, segment_dirs

    def _fetch_and_write_subrange(
        self,
        log_id: str,
        start_ms: int,
        end_ms: int,
    ) -> tuple[Optional[str], int, int]:
        """Fetch a subrange from API and write to cache segment.

        Returns (segment_dir_str, rows_processed, parts_written)
        """
        logger.info(
            "fetch_subrange_start",
            log_id=log_id,
            start_ms=start_ms,
            end_ms=end_ms,
        )
        fetch_start = time.time()

        raw_payload = self.api_client.fetch_logs(str(start_ms), str(end_ms))

        if not self._looks_like_json_payload(raw_payload):
            # Fallback for non-JSON payloads - this shouldn't happen with Log Search
            logger.warning(
                "fetch_subrange_non_json_payload",
                log_id=log_id,
                start_ms=start_ms,
                end_ms=end_ms,
            )
            return None, 0, 0

        payload = json.loads(raw_payload)
        pages = payload.get("pages")
        if not isinstance(pages, list):
            logger.warning(
                "fetch_subrange_no_pages",
                log_id=log_id,
                start_ms=start_ms,
                end_ms=end_ms,
            )
            return None, 0, 0

        segment_dir, rows_processed, parts_written, _stream_stats = self._write_events_streaming_to_cache_segment(
            log_id=log_id,
            start_ms=start_ms,
            end_ms=end_ms,
            pages=pages,
        )

        logger.info(
            "fetch_subrange_complete",
            log_id=log_id,
            start_ms=start_ms,
            end_ms=end_ms,
            duration_ms=int((time.time() - fetch_start) * 1000),
            rows_fetched=rows_processed,
            parts_written=parts_written,
            segment_dir=segment_dir,
        )

        return segment_dir, rows_processed, parts_written

    @staticmethod
    def _dataset_disk_footprint(segment_dirs: list[Path]) -> tuple[int, int]:
        """Return (total_bytes, part_file_count) for one-or-more parquet dataset dirs.

        This is best-effort observability only; callers use it to reconcile what was written
        to disk vs. what was processed.
        """
        total_bytes = 0
        part_files = 0
        for d in segment_dirs:
            try:
                if not d.exists() or not d.is_dir():
                    continue
                for p in d.glob("**/*.parquet"):
                    part_files += 1
                    try:
                        total_bytes += int(p.stat().st_size)
                    except OSError:
                        continue
            except Exception:
                continue
        return total_bytes, part_files
