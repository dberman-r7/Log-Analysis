"""
Tests for configuration management module

Following TDD approach - these tests are written first (RED phase)
and will fail until the configuration module is implemented.
"""

import os
from pathlib import Path

import pytest


def test_config_loads_from_environment(monkeypatch):
    """Test that configuration loads from environment variables"""
    # Arrange
    monkeypatch.setenv("RAPID7_API_KEY", "test_key_123")
    monkeypatch.setenv("RAPID7_API_ENDPOINT", "https://api.example.com")
    monkeypatch.setenv("OUTPUT_DIR", "/tmp/test_output")

    # Act
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig()

    # Assert
    assert config.rapid7_api_key == "test_key_123"
    assert str(config.rapid7_api_endpoint) == "https://api.example.com/"
    assert config.output_dir == Path("/tmp/test_output")


def test_config_validates_required_fields():
    """Test that missing required fields raise validation error"""
    # Clear any environment variables that might be set
    for key in ["RAPID7_API_KEY", "RAPID7_API_ENDPOINT", "OUTPUT_DIR"]:
        os.environ.pop(key, None)

    # Act & Assert
    from pydantic import ValidationError

    from src.log_ingestion.config import LogIngestionConfig

    with pytest.raises(ValidationError):
        LogIngestionConfig()


def test_config_uses_default_values(monkeypatch):
    """Test that optional fields have sensible defaults"""
    # Arrange - set only required fields
    monkeypatch.setenv("RAPID7_API_KEY", "test_key_123")
    monkeypatch.setenv("RAPID7_API_ENDPOINT", "https://api.example.com")
    monkeypatch.setenv("OUTPUT_DIR", "/tmp/test_output")

    # Act
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig()

    # Assert - check defaults
    assert config.log_level == "INFO"
    assert config.batch_size == 1000
    assert config.rate_limit == 60
    assert config.retry_attempts == 3
    assert config.parquet_compression == "snappy"


def test_config_validates_api_endpoint_format(monkeypatch):
    """Test that API endpoint must be valid URL"""
    # Arrange - invalid URL
    monkeypatch.setenv("RAPID7_API_KEY", "test_key_123")
    monkeypatch.setenv("RAPID7_API_ENDPOINT", "not-a-valid-url")
    monkeypatch.setenv("OUTPUT_DIR", "/tmp/test_output")

    # Act & Assert
    from pydantic import ValidationError

    from src.log_ingestion.config import LogIngestionConfig

    with pytest.raises(ValidationError):
        LogIngestionConfig()


def test_config_accepts_valid_log_levels(monkeypatch):
    """Test that valid log levels are accepted"""
    # Arrange
    monkeypatch.setenv("RAPID7_API_KEY", "test_key_123")
    monkeypatch.setenv("RAPID7_API_ENDPOINT", "https://api.example.com")
    monkeypatch.setenv("OUTPUT_DIR", "/tmp/test_output")

    for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
        monkeypatch.setenv("LOG_LEVEL", level)

        # Act
        from src.log_ingestion.config import LogIngestionConfig

        config = LogIngestionConfig()

        # Assert
        assert config.log_level == level


def test_config_validates_batch_size_range(monkeypatch):
    """Test that batch size must be within valid range"""
    # Arrange
    monkeypatch.setenv("RAPID7_API_KEY", "test_key_123")
    monkeypatch.setenv("RAPID7_API_ENDPOINT", "https://api.example.com")
    monkeypatch.setenv("OUTPUT_DIR", "/tmp/test_output")

    # Test valid batch size
    monkeypatch.setenv("BATCH_SIZE", "5000")
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig()
    assert config.batch_size == 5000

    # Test minimum batch size
    monkeypatch.setenv("BATCH_SIZE", "100")
    config = LogIngestionConfig()
    assert config.batch_size == 100

    # Test maximum batch size
    monkeypatch.setenv("BATCH_SIZE", "10000")
    config = LogIngestionConfig()
    assert config.batch_size == 10000


def test_config_output_dir_as_path(monkeypatch):
    """Test that output_dir is converted to Path object"""
    # Arrange
    monkeypatch.setenv("RAPID7_API_KEY", "test_key_123")
    monkeypatch.setenv("RAPID7_API_ENDPOINT", "https://api.example.com")
    monkeypatch.setenv("OUTPUT_DIR", "/tmp/test_output")

    # Act
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig()

    # Assert
    assert isinstance(config.output_dir, Path)
    assert config.output_dir == Path("/tmp/test_output")
