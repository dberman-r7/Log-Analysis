"""Tests for cache decision and partial fetch orchestration (REQ-023/024/025/026).

TDD: RED phase - tests written before implementation.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest


def _write_dummy_segment(cache_dir: Path, log_id: str, start_ms: int, end_ms: int, rows: int = 2):
    """Helper to create a cached segment with dummy data."""
    from src.log_ingestion.cache_index import segment_dir_for_range

    seg_dir = segment_dir_for_range(cache_dir, log_id, start_ms, end_ms)
    seg_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame({
        "message": [f"cached_msg_{i}" for i in range(rows)],
        "timestamp": [start_ms + i for i in range(rows)],
        "sequence_number": [i + 1 for i in range(rows)],
    })
    table = pa.Table.from_pandas(df)
    pq.write_table(table, seg_dir / "part-00000.parquet")
    return seg_dir


class TestCacheHit:
    """Test full cache hit - no API calls when cache fully covers the requested window."""

    def test_cache_hit_no_api_call(self):
        """When cache fully covers requested window, service should not call API."""
        from src.log_ingestion.config import LogIngestionConfig
        from src.log_ingestion.service import LogIngestionService

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            log_id = "test-log-123"

            # Create cached segment covering [0, 10000) ms
            _write_dummy_segment(cache_dir, log_id, 0, 10000, rows=5)

            config = LogIngestionConfig(
                rapid7_api_key="test_key",
                rapid7_log_key=log_id,
                output_dir=str(Path(tmpdir) / "output"),
                cache_dir=str(cache_dir),
            )

            with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
                service = LogIngestionService(config)
                # Request window [1000, 5000) which is fully within cached [0, 10000)
                result = service.run(
                    start_time="1970-01-01T00:00:01Z",  # 1000ms
                    end_time="1970-01-01T00:00:05Z",    # 5000ms
                )

                # API should NOT be called
                mock_fetch.assert_not_called()

            # Result should reflect cached data
            assert result["rows_processed"] >= 0
            assert result.get("cache_hit") is True

    def test_cache_hit_emits_structured_log(self, caplog):
        """Cache hit should emit structured log with cache_hit event."""
        import logging
        from src.log_ingestion.config import LogIngestionConfig
        from src.log_ingestion.service import LogIngestionService

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            log_id = "log-for-cache-hit-log-test"

            _write_dummy_segment(cache_dir, log_id, 0, 100000, rows=3)

            config = LogIngestionConfig(
                rapid7_api_key="test_key",
                rapid7_log_key=log_id,
                output_dir=str(Path(tmpdir) / "output"),
                cache_dir=str(cache_dir),
            )

            with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs"):
                with caplog.at_level(logging.INFO):
                    service = LogIngestionService(config)
                    service.run(
                        start_time="1970-01-01T00:00:00Z",
                        end_time="1970-01-01T00:01:00Z",  # 60000ms
                    )

            # Should have cache_hit log
            assert any("cache_hit" in r.message for r in caplog.records), \
                f"Expected cache_hit log. Records: {[r.message for r in caplog.records]}"


class TestCacheMiss:
    """Test full cache miss - API called for full window when no cache exists."""

    def test_cache_miss_calls_api_for_full_window(self):
        """When no cache exists, service should call API for full window."""
        from src.log_ingestion.config import LogIngestionConfig
        from src.log_ingestion.service import LogIngestionService

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            log_id = "test-log-miss"

            config = LogIngestionConfig(
                rapid7_api_key="test_key",
                rapid7_log_key=log_id,
                output_dir=str(Path(tmpdir) / "output"),
                cache_dir=str(cache_dir),
            )

            payload = {
                "fetch_id": "fetch-miss-001",
                "pages": [
                    {
                        "events": [
                            {"message": "from_api", "timestamp": 1000, "sequence_number": 1},
                        ]
                    }
                ],
            }

            with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
                mock_fetch.return_value = json.dumps(payload)
                service = LogIngestionService(config)
                result = service.run(
                    start_time="1970-01-01T00:00:01Z",
                    end_time="1970-01-01T00:00:05Z",
                )

                # API should be called once
                mock_fetch.assert_called_once()

            assert result["rows_processed"] == 1
            assert result.get("cache_hit") is False

    def test_cache_miss_emits_structured_log(self, caplog):
        """Cache miss should emit structured log with cache_miss event."""
        import logging
        from src.log_ingestion.config import LogIngestionConfig
        from src.log_ingestion.service import LogIngestionService

        with tempfile.TemporaryDirectory() as tmpdir:
            config = LogIngestionConfig(
                rapid7_api_key="test_key",
                rapid7_log_key="log-miss-log-test",
                output_dir=str(Path(tmpdir) / "output"),
                cache_dir=str(Path(tmpdir) / "cache"),
            )

            payload = {
                "fetch_id": "fetch-miss-log",
                "pages": [{"events": [{"message": "m", "timestamp": 1, "sequence_number": 1}]}],
            }

            with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
                mock_fetch.return_value = json.dumps(payload)
                with caplog.at_level(logging.INFO):
                    service = LogIngestionService(config)
                    service.run(
                        start_time="1970-01-01T00:00:00Z",
                        end_time="1970-01-01T00:00:10Z",
                    )

            assert any("cache_miss" in r.message for r in caplog.records), \
                f"Expected cache_miss log. Records: {[r.message for r in caplog.records]}"


class TestCachePartial:
    """Test partial cache coverage - API called only for missing subranges."""

    def test_partial_cache_fetches_only_missing_subranges(self):
        """When cache partially covers window, service should fetch only missing ranges."""
        from src.log_ingestion.config import LogIngestionConfig
        from src.log_ingestion.service import LogIngestionService

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            log_id = "test-log-partial"

            # Create cached segment covering [0, 5000) ms
            _write_dummy_segment(cache_dir, log_id, 0, 5000, rows=2)

            config = LogIngestionConfig(
                rapid7_api_key="test_key",
                rapid7_log_key=log_id,
                output_dir=str(Path(tmpdir) / "output"),
                cache_dir=str(cache_dir),
            )

            payload = {
                "fetch_id": "fetch-partial",
                "pages": [
                    {
                        "events": [
                            {"message": "from_api_partial", "timestamp": 6000, "sequence_number": 1},
                        ]
                    }
                ],
            }

            with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
                mock_fetch.return_value = json.dumps(payload)
                service = LogIngestionService(config)
                # Request [0, 10000) - cache has [0, 5000), missing [5000, 10000)
                result = service.run(
                    start_time="1970-01-01T00:00:00Z",
                    end_time="1970-01-01T00:00:10Z",
                )

                # API should be called once with the missing range params
                mock_fetch.assert_called_once()
                call_args = mock_fetch.call_args
                # The API should be called for [5000, 10000) or equivalent
                start_arg, end_arg = call_args[0]
                assert int(start_arg) == 5000
                assert int(end_arg) == 10000

            assert result.get("cache_hit") is False
            assert result.get("cache_partial") is True

    def test_partial_cache_multiple_gaps_fetches_each_gap(self):
        """When cache has multiple gaps, service should fetch each missing subrange."""
        from src.log_ingestion.config import LogIngestionConfig
        from src.log_ingestion.service import LogIngestionService

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            log_id = "test-log-multi-gap"

            # Create segments: [0, 5000) and [10000, 15000)
            # Missing: [5000, 10000) and [15000, 20000)
            _write_dummy_segment(cache_dir, log_id, 0, 5000, rows=2)
            _write_dummy_segment(cache_dir, log_id, 10000, 15000, rows=2)

            config = LogIngestionConfig(
                rapid7_api_key="test_key",
                rapid7_log_key=log_id,
                output_dir=str(Path(tmpdir) / "output"),
                cache_dir=str(cache_dir),
            )

            call_count = [0]
            def mock_fetch_impl(start_ms, end_ms):
                call_count[0] += 1
                return json.dumps({
                    "fetch_id": f"fetch-gap-{call_count[0]}",
                    "pages": [
                        {"events": [{"message": f"gap{call_count[0]}", "timestamp": int(start_ms), "sequence_number": call_count[0]}]}
                    ],
                })

            with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
                mock_fetch.side_effect = mock_fetch_impl
                service = LogIngestionService(config)
                # Request [0, 20000)
                result = service.run(
                    start_time="1970-01-01T00:00:00Z",
                    end_time="1970-01-01T00:00:20Z",
                )

                # API should be called twice (once per gap)
                assert mock_fetch.call_count == 2

            assert result.get("cache_partial") is True

    def test_partial_cache_emits_structured_log_with_missing_ranges(self, caplog):
        """Partial cache should emit structured log with missing_ranges."""
        import logging
        from src.log_ingestion.config import LogIngestionConfig
        from src.log_ingestion.service import LogIngestionService

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            log_id = "log-partial-log-test"

            _write_dummy_segment(cache_dir, log_id, 0, 5000, rows=2)

            config = LogIngestionConfig(
                rapid7_api_key="test_key",
                rapid7_log_key=log_id,
                output_dir=str(Path(tmpdir) / "output"),
                cache_dir=str(cache_dir),
            )

            payload = {
                "fetch_id": "partial-log",
                "pages": [{"events": [{"message": "m", "timestamp": 6000, "sequence_number": 1}]}],
            }

            with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
                mock_fetch.return_value = json.dumps(payload)
                with caplog.at_level(logging.INFO):
                    service = LogIngestionService(config)
                    service.run(
                        start_time="1970-01-01T00:00:00Z",
                        end_time="1970-01-01T00:00:10Z",
                    )

            assert any("cache_partial" in r.message for r in caplog.records), \
                f"Expected cache_partial log. Records: {[r.message for r in caplog.records]}"


class TestBypassCache:
    """Test bypass_cache config option."""

    def test_bypass_cache_ignores_existing_cache(self):
        """When bypass_cache=True, service should call API even if cache exists."""
        from src.log_ingestion.config import LogIngestionConfig
        from src.log_ingestion.service import LogIngestionService

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            log_id = "test-log-bypass"

            # Create cached segment fully covering the window
            _write_dummy_segment(cache_dir, log_id, 0, 100000, rows=5)

            config = LogIngestionConfig(
                rapid7_api_key="test_key",
                rapid7_log_key=log_id,
                output_dir=str(Path(tmpdir) / "output"),
                cache_dir=str(cache_dir),
                bypass_cache=True,  # Bypass the cache
            )

            payload = {
                "fetch_id": "fetch-bypass",
                "pages": [
                    {"events": [{"message": "from_api_bypass", "timestamp": 1000, "sequence_number": 1}]}
                ],
            }

            with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
                mock_fetch.return_value = json.dumps(payload)
                service = LogIngestionService(config)
                result = service.run(
                    start_time="1970-01-01T00:00:01Z",
                    end_time="1970-01-01T00:00:05Z",
                )

                # API should be called even though cache exists
                mock_fetch.assert_called_once()

            assert result["rows_processed"] == 1


class TestCacheReadFailure:
    """Test fail-loudly behavior on cache read errors (REQ-025)."""

    def test_corrupt_cache_segment_raises_error(self):
        """When cache segment is corrupt, service should fail loudly unless bypass enabled."""
        from src.log_ingestion.config import LogIngestionConfig
        from src.log_ingestion.service import LogIngestionService

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            log_id = "test-log-corrupt"

            # Create a corrupt segment (not valid parquet)
            from src.log_ingestion.cache_index import segment_dir_for_range
            seg_dir = segment_dir_for_range(cache_dir, log_id, 0, 10000)
            seg_dir.mkdir(parents=True, exist_ok=True)
            (seg_dir / "part-00000.parquet").write_text("not a valid parquet file")

            config = LogIngestionConfig(
                rapid7_api_key="test_key",
                rapid7_log_key=log_id,
                output_dir=str(Path(tmpdir) / "output"),
                cache_dir=str(cache_dir),
                bypass_cache=False,
            )

            service = LogIngestionService(config)

            with pytest.raises(Exception) as exc_info:
                service.run(
                    start_time="1970-01-01T00:00:00Z",
                    end_time="1970-01-01T00:00:10Z",
                )

            # Error should mention cache read failure or similar
            assert "cache" in str(exc_info.value).lower() or "parquet" in str(exc_info.value).lower()

    def test_corrupt_cache_with_bypass_falls_back_to_api(self):
        """When bypass_cache=True, corrupt cache should not block API fetch."""
        from src.log_ingestion.config import LogIngestionConfig
        from src.log_ingestion.service import LogIngestionService

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            log_id = "test-log-corrupt-bypass"

            # Create a corrupt segment
            from src.log_ingestion.cache_index import segment_dir_for_range
            seg_dir = segment_dir_for_range(cache_dir, log_id, 0, 10000)
            seg_dir.mkdir(parents=True, exist_ok=True)
            (seg_dir / "part-00000.parquet").write_text("not valid")

            config = LogIngestionConfig(
                rapid7_api_key="test_key",
                rapid7_log_key=log_id,
                output_dir=str(Path(tmpdir) / "output"),
                cache_dir=str(cache_dir),
                bypass_cache=True,  # Bypass should allow fallback
            )

            payload = {
                "fetch_id": "fetch-bypass-corrupt",
                "pages": [{"events": [{"message": "api", "timestamp": 1000, "sequence_number": 1}]}],
            }

            with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
                mock_fetch.return_value = json.dumps(payload)
                service = LogIngestionService(config)
                result = service.run(
                    start_time="1970-01-01T00:00:00Z",
                    end_time="1970-01-01T00:00:10Z",
                )

                mock_fetch.assert_called_once()

            assert result["rows_processed"] == 1


class TestMultiSegmentReads:
    """Test reading from multiple cached segments for analysis."""

    def test_summary_includes_all_segments_in_window(self):
        """Summary should include data from all cached segments covering the window."""
        from src.log_ingestion.config import LogIngestionConfig
        from src.log_ingestion.service import LogIngestionService
        from src.log_ingestion.parquet_writer import ParquetWriter

        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            log_id = "test-log-multi-read"

            # Create two adjacent segments
            _write_dummy_segment(cache_dir, log_id, 0, 5000, rows=3)
            _write_dummy_segment(cache_dir, log_id, 5000, 10000, rows=4)

            config = LogIngestionConfig(
                rapid7_api_key="test_key",
                rapid7_log_key=log_id,
                output_dir=str(Path(tmpdir) / "output"),
                cache_dir=str(cache_dir),
            )

            with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
                service = LogIngestionService(config)
                result = service.run(
                    start_time="1970-01-01T00:00:00Z",
                    end_time="1970-01-01T00:00:10Z",
                )

                # No API call since cache fully covers
                mock_fetch.assert_not_called()

            # Total rows should be 3 + 4 = 7
            assert result["rows_processed"] == 7
            assert result.get("segments_used") == 2


def test_compute_missing_subranges_rejects_invalid_window():
    """REQ-029: compute_missing_subranges must fail loudly on invalid requested windows."""
    from src.log_ingestion.cache_index import compute_missing_subranges

    with pytest.raises(ValueError):
        compute_missing_subranges(requested_start_ms=1000, requested_end_ms=1000, cached_ranges_ms=[])


def test_compute_missing_subranges_ignores_invalid_and_outside_cached_ranges():
    """REQ-029: missing-range planner should ignore invalid cached ranges and ranges outside window."""
    from src.log_ingestion.cache_index import compute_missing_subranges

    # Cached includes:
    # - invalid (end <= start) -> ignored
    # - fully before window -> ignored
    # - partial overlap -> contributes
    missing = compute_missing_subranges(
        requested_start_ms=100,
        requested_end_ms=200,
        cached_ranges_ms=[
            (50, 50),    # invalid
            (0, 10),     # before window
            (120, 150),  # overlap
        ],
    )

    assert missing == [(100, 120), (150, 200)]
