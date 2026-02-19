import json
import tempfile
from unittest.mock import patch


def test_flush_threshold_writes_multiple_parts_and_clears_buffer():
    """When flush threshold is exceeded, service should write multiple parquet parts."""
    from src.log_ingestion.config import LogIngestionConfig
    from src.log_ingestion.parquet_writer import ParquetWriter
    from src.log_ingestion.service import LogIngestionService

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="log-123",
            output_dir=tmpdir,
            cache_dir=tmpdir,
            flush_rows=2,
            bypass_cache=True,
        )

        payload = {
            "fetch_id": "fetch-123",
            "pages": [
                {
                    "events": [
                        {"message": "m1", "timestamp": 1, "sequence_number": 1},
                        {"message": "m2", "timestamp": 2, "sequence_number": 2},
                        {"message": "m3", "timestamp": 3, "sequence_number": 3},
                        {"message": "m4", "timestamp": 4, "sequence_number": 4},
                        {"message": "m5", "timestamp": 5, "sequence_number": 5},
                    ]
                }
            ],
        }

        with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
            mock_fetch.return_value = json.dumps(payload)

            service = LogIngestionService(config)
            result = service.run(
                start_time="2026-02-10T00:00:00Z",
                end_time="2026-02-10T00:00:02Z",
            )

        assert result["rows_processed"] == 5
        assert result.get("parquet_parts_written") == 3

        # New end-of-run metrics
        assert result.get("raw_events_seen") == 5
        assert result.get("duplicates_dropped") == 0
        assert result.get("parquet_total_bytes_written") is not None
        assert int(result.get("parquet_total_bytes_written")) > 0
        assert result.get("observed_min_ts_ms") == 1
        assert result.get("observed_max_ts_ms") == 5

        # Read the directory dataset (all parts) via PyArrow.
        df = ParquetWriter.read_dataset(result["output_file"])
        assert len(df) == 5



def test_dedupe_events_drops_duplicates_across_pages():
    """REQ-014/REQ-028: pagination may overlap; service should optionally dedupe by sequence number."""
    import json
    import tempfile
    from unittest.mock import patch

    from src.log_ingestion.config import LogIngestionConfig
    from src.log_ingestion.parquet_writer import ParquetWriter
    from src.log_ingestion.service import LogIngestionService

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="log-123",
            output_dir=tmpdir,
            cache_dir=tmpdir,
            flush_rows=10,
            dedupe_events=True,
            bypass_cache=True,
        )

        payload = {
            "fetch_id": "fetch-123",
            "pages": [
                {
                    "events": [
                        {"log_id": "log-123", "message": "m1", "timestamp": 1, "sequence_number": 1},
                        {"log_id": "log-123", "message": "m2", "timestamp": 2, "sequence_number": 2},
                    ]
                },
                {
                    "events": [
                        # duplicate
                        {"log_id": "log-123", "message": "m2", "timestamp": 2, "sequence_number": 2},
                        {"log_id": "log-123", "message": "m3", "timestamp": 3, "sequence_number": 3},
                    ]
                },
            ],
        }

        with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
            mock_fetch.return_value = json.dumps(payload)
            service = LogIngestionService(config)
            result = service.run(
                start_time="2026-02-10T00:00:00Z",
                end_time="2026-02-10T00:00:02Z",
            )

        assert result["rows_processed"] == 3
        assert result.get("raw_events_seen") == 4
        assert result.get("duplicates_dropped") == 1
        assert bool(result.get("dedupe_enabled")) is True
        assert int(result.get("raw_events_seen")) == int(result.get("rows_processed")) + int(result.get("duplicates_dropped"))

        df = ParquetWriter.read_dataset(result["output_file"])
        assert len(df) == 3


def test_dedupe_events_can_be_disabled():
    """If dedupe is disabled, service should preserve raw event count."""
    import json
    import tempfile
    from unittest.mock import patch

    from src.log_ingestion.config import LogIngestionConfig
    from src.log_ingestion.parquet_writer import ParquetWriter
    from src.log_ingestion.service import LogIngestionService

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="log-123",
            output_dir=tmpdir,
            cache_dir=tmpdir,
            flush_rows=10,
            dedupe_events=False,
            bypass_cache=True,
        )

        payload = {
            "fetch_id": "fetch-123",
            "pages": [
                {
                    "events": [
                        {"log_id": "log-123", "message": "m1", "timestamp": 1, "sequence_number": 1},
                        {"log_id": "log-123", "message": "m2", "timestamp": 2, "sequence_number": 2},
                    ]
                },
                {
                    "events": [
                        # duplicate retained
                        {"log_id": "log-123", "message": "m2", "timestamp": 2, "sequence_number": 2},
                        {"log_id": "log-123", "message": "m3", "timestamp": 3, "sequence_number": 3},
                    ]
                },
            ],
        }

        with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
            mock_fetch.return_value = json.dumps(payload)
            service = LogIngestionService(config)
            result = service.run(
                start_time="2026-02-10T00:00:00Z",
                end_time="2026-02-10T00:00:02Z",
            )

        assert result["rows_processed"] == 4
        assert result.get("raw_events_seen") == 4
        assert result.get("duplicates_dropped") == 0
        assert bool(result.get("dedupe_enabled")) is False

        df = ParquetWriter.read_dataset(result["output_file"])
        assert len(df) == 4


def test_run_summary_includes_dataset_stats_and_reconciliation(caplog, tmp_path):
    """run_summary should include dataset stats + reconciliation to explain what was written.

    We verify via the rendered structured log payload (JSON string) to avoid coupling
    to logger formatting.
    """
    import json
    import logging

    from src.log_ingestion.config import LogIngestionConfig
    from src.log_ingestion.service import LogIngestionService

    caplog.set_level(logging.INFO)

    config = LogIngestionConfig(
        rapid7_api_key="test_key",
        rapid7_log_key="test-log-summary",
        output_dir=tmp_path / "out",
        cache_dir=tmp_path / "cache",
        bypass_cache=True,
        flush_rows=2,
        dedupe_events=True,
    )

    payload = {
        "fetch_id": "fetch-sum-1",
        "pages": [
            {
                "events": [
                    {"message": "m1", "timestamp": 1, "sequence_number": 1, "log_id": "test-log-summary"},
                    {"message": "m2", "timestamp": 2, "sequence_number": 2, "log_id": "test-log-summary"},
                ]
            }
        ],
    }

    service = LogIngestionService(config)

    from unittest.mock import patch

    with caplog.at_level(logging.INFO):
        with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
            mock_fetch.return_value = json.dumps(payload)
            result = service.run(start_time="1970-01-01T00:00:00Z", end_time="1970-01-01T00:00:01Z")

    assert result["rows_processed"] == 2
    assert result.get("raw_events_seen") == 2
    assert result.get("duplicates_dropped") == 0

    # Find the structured run_summary log line (JSON payload). Some handlers render
    # it as a JSON string in `record.message`.
    parsed = []
    for r in caplog.records:
        msg = r.message
        if not isinstance(msg, str):
            continue
        if not msg.lstrip().startswith("{"):
            continue
        try:
            parsed.append(json.loads(msg))
        except Exception:
            continue

    run_summaries = [p for p in parsed if p.get("event") == "run_summary"]
    assert run_summaries, f"Expected run_summary log. Parsed events: {[p.get('event') for p in parsed]}"

    rs = run_summaries[-1]
    assert rs.get("log_id") == "test-log-summary"
    assert "reconciliation" in rs
    assert rs["reconciliation"].get("rows_processed") == 2
    assert rs["reconciliation"].get("raw_events_seen") == 2

    # New fields added by this change
    assert "parquet_dataset_stats" in rs
    assert rs["parquet_dataset_stats"] is None or "total_bytes" in rs["parquet_dataset_stats"]
