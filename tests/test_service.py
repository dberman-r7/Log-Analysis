"""
Tests for Log Ingestion Service (Main Orchestration)

Following TDD approach - these tests are written first (RED phase)
and will fail until the main service module is implemented.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest


def test_service_orchestrates_complete_pipeline():
    """Test end-to-end pipeline: API fetch → CSV parse → Parquet write"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=tmpdir,
        )

        # Mock CSV response from API
        csv_response = (
            "timestamp,level,message\n"
            "2026-02-10T10:00:00Z,INFO,Test message 1\n"
            "2026-02-10T10:00:01Z,ERROR,Test message 2\n"
        )

        # Act
        from src.log_ingestion.service import LogIngestionService

        with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
            mock_fetch.return_value = csv_response

            service = LogIngestionService(config)
            result = service.run(start_time="2026-02-10T00:00:00Z", end_time="2026-02-10T01:00:00Z")

        # Assert
        assert result is not None
        assert "output_file" in result
        assert result["output_file"] is not None
        assert Path(result["output_file"]).exists()
        assert result["rows_processed"] == 2

        # Verify parquet file is readable
        df = pd.read_parquet(result["output_file"])
        assert len(df) == 2
        assert "timestamp" in df.columns
        assert "level" in df.columns
        assert "message" in df.columns


def test_service_handles_api_errors():
    """Test error handling when API fetch fails"""
    # Arrange
    import requests

    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=tmpdir,
        )

        # Act & Assert
        from src.log_ingestion.service import LogIngestionService

        with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
            # Simulate API error
            mock_fetch.side_effect = requests.exceptions.HTTPError("401 Unauthorized")

            service = LogIngestionService(config)

            # Should raise the API error
            with pytest.raises((requests.exceptions.HTTPError, Exception)):
                service.run(start_time="2026-02-10T00:00:00Z", end_time="2026-02-10T01:00:00Z")


def test_service_handles_empty_logs():
    """Test handling of empty log response from API"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=tmpdir,
        )

        # Act
        from src.log_ingestion.service import LogIngestionService

        with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
            # Empty response
            mock_fetch.return_value = ""

            service = LogIngestionService(config)
            result = service.run(start_time="2026-02-10T00:00:00Z", end_time="2026-02-10T01:00:00Z")

        # Assert
        # Should handle gracefully
        assert result is not None
        assert result["rows_processed"] == 0


def test_service_handles_malformed_csv():
    """Test handling of malformed CSV data"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=tmpdir,
        )

        # Malformed CSV - inconsistent columns
        csv_response = (
            "timestamp,level,message\n"
            "2026-02-10T10:00:00Z,INFO\n"  # Missing column
            "2026-02-10T10:00:01Z,ERROR,Test message 2\n"
        )

        # Act
        from src.log_ingestion.service import LogIngestionService

        with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
            mock_fetch.return_value = csv_response

            service = LogIngestionService(config)
            result = service.run(start_time="2026-02-10T00:00:00Z", end_time="2026-02-10T01:00:00Z")

        # Assert
        # Should handle gracefully - parser handles malformed data
        assert result is not None
        # At least one valid row should be processed
        assert result["rows_processed"] >= 1


def test_service_processes_batches():
    """Test batch processing of large log sets"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=tmpdir,
            batch_size=100,  # Min allowed batch size
        )

        # Generate CSV with 250 rows (should process in 3 batches: 100, 100, 50)
        rows = ["timestamp,level,message"]
        for i in range(250):
            rows.append(f"2026-02-10T10:00:{i:02d}Z,INFO,Message {i}")
        csv_response = "\n".join(rows)

        # Act
        from src.log_ingestion.service import LogIngestionService

        with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
            mock_fetch.return_value = csv_response

            service = LogIngestionService(config)
            result = service.run(start_time="2026-02-10T00:00:00Z", end_time="2026-02-10T01:00:00Z")

        # Assert
        assert result is not None
        assert result["rows_processed"] == 250
        # Should have batches information
        if "batches_processed" in result:
            assert result["batches_processed"] == 3  # 250 rows / 100 batch_size = 3 batches


def test_service_initializes_components():
    """Test that service properly initializes all components"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=tmpdir,
        )

        # Act
        from src.log_ingestion.service import LogIngestionService

        service = LogIngestionService(config)

        # Assert
        # Service should have initialized components
        assert hasattr(service, "config")
        assert hasattr(service, "api_client")
        assert hasattr(service, "parser")
        assert hasattr(service, "writer")

        # Components should be properly instantiated
        from src.log_ingestion.api_client import Rapid7ApiClient
        from src.log_ingestion.parquet_writer import ParquetWriter
        from src.log_ingestion.parser import LogParser

        assert isinstance(service.api_client, Rapid7ApiClient)
        assert isinstance(service.parser, LogParser)
        assert isinstance(service.writer, ParquetWriter)


def test_service_generates_partition_date():
    """Test partition date generation from time range"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=tmpdir,
        )

        csv_response = "timestamp,level,message\n2026-02-10T10:00:00Z,INFO,Test message\n"

        # Act
        from src.log_ingestion.service import LogIngestionService

        with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
            mock_fetch.return_value = csv_response

            service = LogIngestionService(config)
            result = service.run(start_time="2026-02-10T00:00:00Z", end_time="2026-02-10T23:59:59Z")

        # Assert
        assert result is not None
        assert result["output_file"] is not None

        # File should include date in path or name
        output_file = str(result["output_file"])
        assert "2026" in output_file or "20260210" in output_file


def test_service_logs_pipeline_events():
    """Test that service logs important pipeline events"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=tmpdir,
        )

        csv_response = "timestamp,level,message\n2026-02-10T10:00:00Z,INFO,Test message\n"

        # Act
        from src.log_ingestion.service import LogIngestionService

        with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
            mock_fetch.return_value = csv_response

            with patch("src.log_ingestion.service.logger") as mock_logger:
                service = LogIngestionService(config)
                service.run(start_time="2026-02-10T00:00:00Z", end_time="2026-02-10T01:00:00Z")

                # Assert
                # Should log initialization and completion
                assert mock_logger.info.called
                # Check for specific log events
                call_args = [call[0][0] for call in mock_logger.info.call_args_list]
                assert "service_initialized" in call_args or any(
                    "initialized" in str(arg) for arg in call_args
                )


def test_service_converts_iso8601_to_epoch_millis_for_api_client():
    """REQ-023: Service must convert ISO8601 inputs to epoch-millis for the Log Search query endpoint."""
    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=tmpdir,
        )

        # Minimal CSV for the pipeline to proceed.
        csv_response = "timestamp,level,message\n2026-02-10T00:00:00Z,INFO,ok\n"

        from src.log_ingestion.service import LogIngestionService

        with patch("src.log_ingestion.service.Rapid7ApiClient.fetch_logs") as mock_fetch:
            mock_fetch.return_value = csv_response

            service = LogIngestionService(config)
            service.run(start_time="2026-02-10T00:00:00Z", end_time="2026-02-10T01:00:00Z")

        # Assert: service called API with epoch-millis strings.
        called_start, called_end = mock_fetch.call_args[0]
        assert called_start.isdigit()
        assert called_end.isdigit()
        assert int(called_end) > int(called_start)

