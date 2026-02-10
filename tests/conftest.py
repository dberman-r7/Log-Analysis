"""
Pytest configuration and shared fixtures for log ingestion tests.

This module provides common fixtures used across multiple test modules.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

from src.log_ingestion.config import LogIngestionConfig


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_config(temp_dir, monkeypatch):
    """
    Provide a test configuration with temporary output directory.

    Args:
        temp_dir: Temporary directory fixture
        monkeypatch: Pytest monkeypatch fixture for environment variables

    Returns:
        LogIngestionConfig: Test configuration instance
    """
    # Set required environment variables
    monkeypatch.setenv("RAPID7_API_KEY", "test-api-key-12345")
    monkeypatch.setenv("RAPID7_API_ENDPOINT", "https://api.test.rapid7.com")
    monkeypatch.setenv("OUTPUT_DIR", str(temp_dir))

    # Optional settings with test values
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("BATCH_SIZE", "100")
    monkeypatch.setenv("RATE_LIMIT", "10")
    monkeypatch.setenv("RETRY_ATTEMPTS", "2")
    monkeypatch.setenv("PARQUET_COMPRESSION", "snappy")

    return LogIngestionConfig()


@pytest.fixture
def sample_csv_data():
    """Provide sample CSV data for testing."""
    return """timestamp,level,message,user_id
2026-02-10T10:00:00Z,INFO,User login,12345
2026-02-10T10:01:00Z,WARNING,Failed login attempt,67890
2026-02-10T10:02:00Z,ERROR,Database connection lost,12345"""


@pytest.fixture
def sample_dataframe():
    """Provide sample DataFrame for testing."""
    return pd.DataFrame({
        "timestamp": ["2026-02-10T10:00:00Z", "2026-02-10T10:01:00Z", "2026-02-10T10:02:00Z"],
        "level": ["INFO", "WARNING", "ERROR"],
        "message": ["User login", "Failed login attempt", "Database connection lost"],
        "user_id": [12345, 67890, 12345],
    })


@pytest.fixture
def mock_api_response():
    """Provide a mock API response for testing."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "text/csv"}
    mock_response.text = """timestamp,level,message
2026-02-10T10:00:00Z,INFO,Test log entry
2026-02-10T10:01:00Z,WARNING,Another test entry"""
    mock_response.json.return_value = {
        "data": mock_response.text,
        "next_page_token": None,
    }
    return mock_response


@pytest.fixture
def mock_api_response_json():
    """Provide a mock JSON API response for testing."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {
        "data": """timestamp,level,message
2026-02-10T10:00:00Z,INFO,Test log entry
2026-02-10T10:01:00Z,WARNING,Another test entry""",
        "next_page_token": None,
    }
    return mock_response


@pytest.fixture
def mock_paginated_response():
    """Provide mock paginated API responses for testing."""
    # First page
    page1 = Mock()
    page1.status_code = 200
    page1.headers = {"Content-Type": "application/json"}
    page1.json.return_value = {
        "data": """timestamp,level,message
2026-02-10T10:00:00Z,INFO,Page 1 entry 1
2026-02-10T10:01:00Z,INFO,Page 1 entry 2""",
        "next_page_token": "token123",
    }

    # Second page
    page2 = Mock()
    page2.status_code = 200
    page2.headers = {"Content-Type": "application/json"}
    page2.json.return_value = {
        "data": """timestamp,level,message
2026-02-10T10:02:00Z,INFO,Page 2 entry 1
2026-02-10T10:03:00Z,INFO,Page 2 entry 2""",
        "next_page_token": None,  # No more pages
    }

    return [page1, page2]
