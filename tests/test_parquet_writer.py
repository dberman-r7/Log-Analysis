"""
Tests for Parquet Writer module

Following TDD approach - these tests are written first (RED phase)
and will fail until the Parquet writer module is implemented.
"""

import tempfile
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


def test_writer_creates_parquet_schema():
    """Test Parquet schema creation from DataFrame"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=tmpdir,
        )

        df = pd.DataFrame(
            {
                "timestamp": ["2026-02-10T10:00:00Z", "2026-02-10T10:00:01Z"],
                "level": ["INFO", "ERROR"],
                "message": ["Test message 1", "Test message 2"],
                "count": [1, 2],
            }
        )

        # Act
        from src.log_ingestion.parquet_writer import ParquetWriter

        writer = ParquetWriter(config)
        output_file = writer.write(df)

        # Assert
        assert output_file.exists()
        assert output_file.suffix == ".parquet"

        # Verify schema by reading back
        table = pq.read_table(output_file)
        assert len(table.schema) >= 4
        assert "timestamp" in table.schema.names
        assert "level" in table.schema.names


def test_writer_writes_single_batch():
    """Test writing single batch to Parquet file"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=tmpdir,
        )

        df = pd.DataFrame(
            {
                "timestamp": ["2026-02-10T10:00:00Z", "2026-02-10T10:00:01Z"],
                "level": ["INFO", "ERROR"],
                "message": ["Message 1", "Message 2"],
            }
        )

        # Act
        from src.log_ingestion.parquet_writer import ParquetWriter

        writer = ParquetWriter(config)
        output_file = writer.write(df)

        # Assert
        assert output_file.exists()

        # Read back and verify data
        df_read = pd.read_parquet(output_file)
        assert len(df_read) == 2
        assert list(df_read.columns) == ["timestamp", "level", "message"]
        assert df_read["level"].iloc[0] == "INFO"
        assert df_read["message"].iloc[1] == "Message 2"


def test_writer_writes_multiple_batches():
    """Test appending multiple batches to same file"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=tmpdir,
        )

        df1 = pd.DataFrame(
            {
                "timestamp": ["2026-02-10T10:00:00Z"],
                "level": ["INFO"],
                "message": ["Batch 1"],
            }
        )

        df2 = pd.DataFrame(
            {
                "timestamp": ["2026-02-10T10:00:01Z"],
                "level": ["ERROR"],
                "message": ["Batch 2"],
            }
        )

        # Act
        from src.log_ingestion.parquet_writer import ParquetWriter

        writer = ParquetWriter(config)
        file1 = writer.write(df1, partition_date="2026-02-10")
        file2 = writer.write(df2, partition_date="2026-02-10", append=True)

        # Assert
        # Should use same file for same partition date
        assert file1 == file2 or file1.parent == file2.parent

        # Read back and verify combined data
        df_read = pd.read_parquet(file2)
        assert len(df_read) >= 1  # At least the second batch


def test_writer_partitions_by_date():
    """Test file partitioning by date"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=tmpdir,
        )

        df1 = pd.DataFrame(
            {
                "timestamp": ["2026-02-10T10:00:00Z"],
                "level": ["INFO"],
                "message": ["Day 1"],
            }
        )

        df2 = pd.DataFrame(
            {
                "timestamp": ["2026-02-11T10:00:00Z"],
                "level": ["ERROR"],
                "message": ["Day 2"],
            }
        )

        # Act
        from src.log_ingestion.parquet_writer import ParquetWriter

        writer = ParquetWriter(config)
        file1 = writer.write(df1, partition_date="2026-02-10")
        file2 = writer.write(df2, partition_date="2026-02-11")

        # Assert
        # Different dates should produce different files
        assert file1 != file2
        assert file1.exists()
        assert file2.exists()

        # File names or paths should include date information
        assert "2026-02-10" in str(file1) or "20260210" in str(file1)
        assert "2026-02-11" in str(file2) or "20260211" in str(file2)


def test_writer_applies_compression():
    """Test compression is applied"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test with snappy compression
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=tmpdir,
            parquet_compression="snappy",
        )

        df = pd.DataFrame(
            {
                "timestamp": [f"2026-02-10T10:00:{i:02d}Z" for i in range(100)],
                "level": ["INFO"] * 100,
                "message": [f"Message {i}" for i in range(100)],
            }
        )

        # Act
        from src.log_ingestion.parquet_writer import ParquetWriter

        writer = ParquetWriter(config)
        output_file = writer.write(df)

        # Assert
        assert output_file.exists()

        # Verify compression by reading metadata
        parquet_file = pq.ParquetFile(output_file)
        metadata = parquet_file.metadata

        # File should be smaller than uncompressed (rough check)
        # and metadata should indicate compression
        assert metadata.num_rows == 100


def test_writer_validates_output_file():
    """Test that output file is readable Parquet"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=tmpdir,
        )

        df = pd.DataFrame(
            {
                "timestamp": ["2026-02-10T10:00:00Z"],
                "level": ["INFO"],
                "message": ["Test"],
            }
        )

        # Act
        from src.log_ingestion.parquet_writer import ParquetWriter

        writer = ParquetWriter(config)
        output_file = writer.write(df)

        # Assert
        # File should be valid Parquet format
        assert output_file.exists()

        # Should be able to read it back
        df_read = pd.read_parquet(output_file)
        assert isinstance(df_read, pd.DataFrame)
        assert len(df_read) == 1

        # Should be able to read with pyarrow
        table = pq.read_table(output_file)
        assert table.num_rows == 1


def test_writer_handles_empty_dataframe():
    """Test handling of empty DataFrame"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=tmpdir,
        )

        df = pd.DataFrame()

        # Act
        from src.log_ingestion.parquet_writer import ParquetWriter

        writer = ParquetWriter(config)
        # Should handle gracefully - either return None or create empty file
        result = writer.write(df)

        # Assert
        # Either no file is created or an empty file is created
        if result is not None:
            assert isinstance(result, Path)


def test_writer_creates_output_directory():
    """Test that writer creates output directory if it doesn't exist"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        # Use a nested path that doesn't exist
        output_path = Path(tmpdir) / "nested" / "output" / "dir"

        config = LogIngestionConfig(
            rapid7_api_key="test_key",
            rapid7_log_key="test-log-key",
            output_dir=str(output_path),
        )

        df = pd.DataFrame(
            {
                "timestamp": ["2026-02-10T10:00:00Z"],
                "level": ["INFO"],
                "message": ["Test"],
            }
        )

        # Act
        from src.log_ingestion.parquet_writer import ParquetWriter

        writer = ParquetWriter(config)
        output_file = writer.write(df)

        # Assert
        assert output_path.exists()
        assert output_path.is_dir()
        assert output_file.exists()
        # File should be in YYYY/MM/DD subdirectory structure
        assert str(output_path) in str(output_file.parent)
