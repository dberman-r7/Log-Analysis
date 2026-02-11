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
    """Test that API client creates provider Log Search authentication header"""
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_api_key_123",
        rapid7_log_key="logkey_1",
        output_dir="/tmp/test",
    )

    from src.log_ingestion.api_client import Rapid7ApiClient

    client = Rapid7ApiClient(config)

    assert "x-api-key" in client.session.headers
    assert client.session.headers["x-api-key"] == "test_api_key_123"
    assert "Authorization" not in client.session.headers


def test_api_client_fetches_logs_successfully():
    """Test successful Log Search query fetch"""
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_key",
        rapid7_log_key="logkey_1",
        output_dir="/tmp/test",
        rapid7_data_storage_region="eu",
        rapid7_query="",
    )

    # First response returns completed result set (no Self link)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.json.return_value = {"events": [{"message": "hello"}]}

    from src.log_ingestion.api_client import Rapid7ApiClient

    with patch("requests.Session.get", return_value=mock_response) as mock_get:
        client = Rapid7ApiClient(config)
        result = client.fetch_logs("2026-02-10T10:00:00Z", "2026-02-10T10:01:00Z")

    assert mock_get.call_count == 1
    assert isinstance(result, str)
    assert "events" in result


def test_api_client_polls_self_until_complete():
    """If API returns rel=Self, client should poll until completion"""
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_key",
        rapid7_log_key="logkey_1",
        output_dir="/tmp/test",
        rapid7_data_storage_region="eu",
    )

    in_progress = Mock()
    in_progress.status_code = 200
    in_progress.headers = {"Content-Type": "application/json"}
    in_progress.json.return_value = {
        "links": [{"rel": "Self", "href": "https://cont/self"}]
    }

    completed = Mock()
    completed.status_code = 200
    completed.headers = {"Content-Type": "application/json"}
    completed.json.return_value = {"events": [{"message": "done"}]}

    from src.log_ingestion.api_client import Rapid7ApiClient

    with patch("requests.Session.get") as mock_get, patch("time.sleep") as mock_sleep:
        mock_get.side_effect = [in_progress, completed]
        client = Rapid7ApiClient(config)
        result = client.fetch_logs("2026-02-10T10:00:00Z", "2026-02-10T10:01:00Z")

    assert mock_get.call_count == 2
    assert mock_sleep.call_count >= 1
    assert "events" in result


def test_api_client_follows_next_page_links():
    """If response contains rel=Next, client should fetch next pages"""
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_key",
        rapid7_log_key="logkey_1",
        output_dir="/tmp/test",
        rapid7_data_storage_region="eu",
    )

    page1 = Mock()
    page1.status_code = 200
    page1.headers = {"Content-Type": "application/json"}
    page1.json.return_value = {
        "events": [{"message": "p1"}],
        "links": [{"rel": "Next", "href": "https://cont/next"}],
    }

    page2 = Mock()
    page2.status_code = 200
    page2.headers = {"Content-Type": "application/json"}
    page2.json.return_value = {"events": [{"message": "p2"}]}

    from src.log_ingestion.api_client import Rapid7ApiClient

    with patch("requests.Session.get") as mock_get:
        mock_get.side_effect = [page1, page2]
        client = Rapid7ApiClient(config)
        result = client.fetch_logs("2026-02-10T10:00:00Z", "2026-02-10T10:01:00Z")

    assert mock_get.call_count == 2
    assert "p1" in result
    assert "p2" in result


def test_api_client_handles_401_unauthorized():
    """Test handling of authentication failure"""
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="invalid_key",
        rapid7_log_key="logkey_1",
        output_dir="/tmp/test",
        rapid7_data_storage_region="eu",
    )

    mock_response = Mock()
    mock_response.status_code = 401

    error_401 = requests.exceptions.HTTPError("401 Unauthorized")
    error_401.response = mock_response
    mock_response.raise_for_status.side_effect = error_401

    from src.log_ingestion.api_client import Rapid7ApiClient

    with patch("requests.Session.get", return_value=mock_response):
        client = Rapid7ApiClient(config)
        with pytest.raises(requests.exceptions.HTTPError):
            client.fetch_logs("2026-02-10T10:00:00Z", "2026-02-10T10:01:00Z")


def test_api_client_handles_429_rate_limit():
    """Handle 429 using Retry-After/X-RateLimit-Reset and retry"""
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_key",
        rapid7_log_key="logkey_1",
        output_dir="/tmp/test",
        rapid7_data_storage_region="eu",
    )

    rate_limited = Mock()
    rate_limited.status_code = 429
    rate_limited.headers = {"Retry-After": "2", "X-RateLimit-Reset": "99"}

    completed = Mock()
    completed.status_code = 200
    completed.headers = {"Content-Type": "application/json"}
    completed.json.return_value = {"events": []}

    from src.log_ingestion.api_client import Rapid7ApiClient

    with patch("requests.Session.get") as mock_get, patch("time.sleep") as mock_sleep:
        mock_get.side_effect = [rate_limited, completed]
        client = Rapid7ApiClient(config)
        result = client.fetch_logs("1700000000000", "1700000001000")

    assert mock_get.call_count == 2
    # The client may also sleep briefly due to its own per-minute rate limiting; ensure we slept for the Retry-After duration.
    assert any(call.args == (2,) for call in mock_sleep.call_args_list)
    assert "events" in result


def test_api_client_timeout_handling():
    """Test timeout configuration and handling"""
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_key",
        rapid7_log_key="logkey_1",
        output_dir="/tmp/test",
        rapid7_data_storage_region="eu",
    )

    from src.log_ingestion.api_client import Rapid7ApiClient

    with patch("requests.Session.get") as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

        client = Rapid7ApiClient(config)
        with pytest.raises(requests.exceptions.Timeout):
            client.fetch_logs("2026-02-10T10:00:00Z", "2026-02-10T10:01:00Z")


def test_api_client_handles_connection_error():
    """Test handling of network connection errors"""
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_key",
        rapid7_log_key="logkey_1",
        output_dir="/tmp/test",
        rapid7_data_storage_region="eu",
        retry_attempts=2,
    )

    from src.log_ingestion.api_client import Rapid7ApiClient

    with patch("requests.Session.get") as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

        client = Rapid7ApiClient(config)
        with pytest.raises(requests.exceptions.ConnectionError):
            client.fetch_logs("2026-02-10T10:00:00Z", "2026-02-10T10:01:00Z")

        assert mock_get.call_count >= 2


def test_api_client_list_log_sets_success():
    """REQ-016: list available log sets via management API."""
    from unittest.mock import Mock, patch

    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_key",
        rapid7_log_key="logkey_1",
        output_dir="/tmp/test",
        rapid7_data_storage_region="eu",
    )

    resp = Mock()
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = {
        "logsets": [
            {"id": "ls-1", "name": "Set One", "description": "desc"},
            {"id": "ls-2", "name": "Set Two"},
        ]
    }

    from src.log_ingestion.api_client import Rapid7ApiClient

    with patch("requests.Session.get", return_value=resp):
        client = Rapid7ApiClient(config)
        log_sets = client.list_log_sets()

    assert len(log_sets) == 2
    assert log_sets[0].id == "ls-1"
    assert log_sets[0].name == "Set One"


def test_api_client_list_logs_in_log_set_success():
    """REQ-019: per-logset membership endpoints are unsupported; fail loudly."""
    from unittest.mock import patch

    from src.log_ingestion.api_client import Rapid7ApiClient
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_key",
        rapid7_log_key="logkey_1",
        output_dir="/tmp/test",
        rapid7_data_storage_region="eu",
    )

    client = Rapid7ApiClient(config)

    # Ensure no HTTP is attempted.
    with patch.object(client, "_request_get", side_effect=AssertionError("network not allowed")):
        with pytest.raises(ValueError) as exc:
            client.list_logs_in_log_set("ls-1")

    assert "logs_info" in str(exc.value)


def test_api_client_query_404_logs_actionable_guidance(capsys):
    """REQ-010/NFR-REL: Fail loudly with actionable guidance on 404 query endpoint."""
    from unittest.mock import ANY, Mock, patch

    import requests

    from src.log_ingestion.api_client import Rapid7ApiClient
    from src.log_ingestion.config import LogIngestionConfig

    config = LogIngestionConfig(
        rapid7_api_key="test_key",
        rapid7_log_key="logkey_404",
        output_dir="/tmp/test",
        rapid7_data_storage_region="eu",
        rapid7_query="",
    )

    resp = Mock()
    resp.status_code = 404

    http_error = requests.exceptions.HTTPError("404 Not Found")
    http_error.response = resp
    resp.raise_for_status.side_effect = http_error

    with patch("requests.Session.get", return_value=resp), patch(
        "src.log_ingestion.api_client.logger"
    ) as mock_logger:
        client = Rapid7ApiClient(config)
        with pytest.raises(requests.exceptions.HTTPError):
            client.fetch_logs("2026-02-10T10:00:00Z", "2026-02-10T10:01:00Z")

    # We should emit a structured error event with actionable guidance.
    mock_logger.error.assert_any_call(
        "logsearch_query_endpoint_not_found",
        url="https://eu.rest.logs.insight.rapid7.com/query/logs/logkey_404",
        region="eu",
        log_key="logkey_404",
        guidance=ANY,
    )

    guidance_values = [
        call.kwargs.get("guidance")
        for call in mock_logger.error.call_args_list
        if call.args and call.args[0] == "logsearch_query_endpoint_not_found"
    ]
    assert guidance_values, "Expected logsearch_query_endpoint_not_found event"
    assert isinstance(guidance_values[-1], str)
    assert "region" in guidance_values[-1].lower()
    assert "log" in guidance_values[-1].lower()
