"""
Tests for Rapid7 API Client module

Following TDD approach - these tests are written first (RED phase)
and will fail until the API client module is implemented.
"""

import time
from unittest.mock import Mock, patch

import pytest
import requests


def test_api_client_constructs_auth_header():
    """Test that API client creates proper authentication header"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_api_key_123",
        rapid7_api_endpoint="https://api.example.com",
        output_dir="/tmp/test",
    )

    # Act
    from src.log_ingestion.api_client import Rapid7ApiClient

    client = Rapid7ApiClient(config)

    # Assert
    assert "Authorization" in client.session.headers
    assert client.session.headers["Authorization"] == "Bearer test_api_key_123"
    assert client.session.headers["Content-Type"] == "application/json"


def test_api_client_fetches_logs_successfully():
    """Test successful log fetch from API"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_key",
        rapid7_api_endpoint="https://api.example.com",
        output_dir="/tmp/test",
    )

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "logs": [
            {"timestamp": "2026-02-10T10:00:00Z", "message": "Test log 1"},
            {"timestamp": "2026-02-10T10:00:01Z", "message": "Test log 2"},
        ],
        "next_page": None,
    }

    # Act
    from src.log_ingestion.api_client import Rapid7ApiClient

    with patch("requests.Session.get", return_value=mock_response):
        client = Rapid7ApiClient(config)
        result = client.fetch_logs("2026-02-10T10:00:00Z", "2026-02-10T10:01:00Z")

    # Assert
    assert "logs" in result
    assert len(result["logs"]) == 2
    assert result["logs"][0]["message"] == "Test log 1"


def test_api_client_handles_401_unauthorized():
    """Test handling of authentication failure"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="invalid_key",
        rapid7_api_endpoint="https://api.example.com",
        output_dir="/tmp/test",
    )

    mock_response = Mock()
    mock_response.status_code = 401

    # Create HTTPError with response attribute
    error_401 = requests.exceptions.HTTPError("401 Unauthorized")
    error_401.response = mock_response

    mock_response.raise_for_status.side_effect = error_401

    # Act & Assert
    from src.log_ingestion.api_client import Rapid7ApiClient

    with patch("requests.Session.get", return_value=mock_response):
        client = Rapid7ApiClient(config)
        with pytest.raises(requests.exceptions.HTTPError):
            client.fetch_logs("2026-02-10T10:00:00Z", "2026-02-10T10:01:00Z")


def test_api_client_handles_429_rate_limit():
    """Test retry with exponential backoff on rate limit"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_key",
        rapid7_api_endpoint="https://api.example.com",
        output_dir="/tmp/test",
        retry_attempts=3,
    )

    # First two calls return 429, third succeeds
    mock_response_429 = Mock()
    mock_response_429.status_code = 429
    mock_response_429.headers = {"Retry-After": "1"}

    mock_response_200 = Mock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"logs": [], "next_page": None}

    # Act
    from src.log_ingestion.api_client import Rapid7ApiClient

    with patch("requests.Session.get") as mock_get:
        mock_get.side_effect = [mock_response_429, mock_response_429, mock_response_200]

        client = Rapid7ApiClient(config)
        start_time = time.time()
        result = client.fetch_logs("2026-02-10T10:00:00Z", "2026-02-10T10:01:00Z")
        elapsed = time.time() - start_time

        # Assert - should have retried and eventually succeeded
        assert mock_get.call_count == 3
        assert "logs" in result
        # Should have waited (exponential backoff)
        assert elapsed >= 1.0  # At least some delay


def test_api_client_handles_500_server_error():
    """Test retry logic on server errors"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_key",
        rapid7_api_endpoint="https://api.example.com",
        output_dir="/tmp/test",
        retry_attempts=2,
    )

    mock_response_500 = Mock()
    mock_response_500.status_code = 500

    # Create HTTPError with response attribute
    error_500 = requests.exceptions.HTTPError("500 Server Error")
    error_500.response = mock_response_500

    mock_response_500.raise_for_status.side_effect = error_500

    mock_response_200 = Mock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"logs": [], "next_page": None}

    # Act
    from src.log_ingestion.api_client import Rapid7ApiClient

    with patch("requests.Session.get") as mock_get:
        # First call fails, second succeeds
        mock_get.side_effect = [mock_response_500, mock_response_200]

        client = Rapid7ApiClient(config)
        result = client.fetch_logs("2026-02-10T10:00:00Z", "2026-02-10T10:01:00Z")

        # Assert
        assert mock_get.call_count == 2
        assert "logs" in result


def test_api_client_respects_rate_limiting():
    """Test that client enforces rate limit"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_key",
        rapid7_api_endpoint="https://api.example.com",
        output_dir="/tmp/test",
        rate_limit=120,  # 120 requests per minute = 2 per second
    )

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"logs": [], "next_page": None}

    # Act
    from src.log_ingestion.api_client import Rapid7ApiClient

    with patch("requests.Session.get", return_value=mock_response):
        client = Rapid7ApiClient(config)

        # Make multiple requests quickly
        start_time = time.time()
        for _ in range(3):
            client.fetch_logs("2026-02-10T10:00:00Z", "2026-02-10T10:01:00Z")
        elapsed = time.time() - start_time

        # Assert - should have rate limited (3 requests at 2/sec = ~1.5 seconds minimum)
        # Being lenient with timing for CI environments
        assert elapsed >= 0.5  # At least some rate limiting applied


def test_api_client_timeout_handling():
    """Test timeout configuration and handling"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_key",
        rapid7_api_endpoint="https://api.example.com",
        output_dir="/tmp/test",
    )

    # Act & Assert
    from src.log_ingestion.api_client import Rapid7ApiClient

    with patch("requests.Session.get") as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

        client = Rapid7ApiClient(config)
        with pytest.raises(requests.exceptions.Timeout):
            client.fetch_logs("2026-02-10T10:00:00Z", "2026-02-10T10:01:00Z")


def test_api_client_handles_connection_error():
    """Test handling of network connection errors"""
    # Arrange
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_key",
        rapid7_api_endpoint="https://api.example.com",
        output_dir="/tmp/test",
        retry_attempts=2,
    )

    # Act & Assert
    from src.log_ingestion.api_client import Rapid7ApiClient

    with patch("requests.Session.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

        client = Rapid7ApiClient(config)
        # Should retry and eventually raise
        with pytest.raises(requests.exceptions.ConnectionError):
            client.fetch_logs("2026-02-10T10:00:00Z", "2026-02-10T10:01:00Z")

        # Should have retried
        assert mock_get.call_count >= 2
