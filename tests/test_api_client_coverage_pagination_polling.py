"""Coverage-focused tests for API client edge cases.

These tests exist to exercise fail-loudly branches in `Rapid7ApiClient` that are
hard to hit in higher-level service tests.

No new behavior is introduced; they validate existing contracts.
"""

from unittest.mock import Mock, patch

import pytest


def _config(**env: str):
    from src.log_ingestion.config import LogIngestionConfig

    return LogIngestionConfig(**env)


def test_poll_request_to_completion_times_out_after_max_iterations():
    """NFR-REL: polling must stop after max iterations, even if server stays in-progress."""

    from src.log_ingestion.api_client import Rapid7ApiClient

    config = _config(
        RAPID7_API_KEY="test_key",
        RAPID7_LOG_KEY="logkey_1",
        OUTPUT_DIR="/tmp/test",
        RAPID7_DATA_STORAGE_REGION="eu",
        POLL_MAX_ITERATIONS="1",
        POLL_MAX_WALL_SECONDS="999",
        POLL_PROGRESS_LOG_EVERY="0",
    )

    in_progress = Mock()
    in_progress.status_code = 200
    in_progress.headers = {"Content-Type": "application/json"}
    in_progress.text = "{\"links\":[{\"rel\":\"Self\",\"href\":\"https://cont/self\"}]}"
    in_progress.json.return_value = {
        "links": [{"rel": "Self", "href": "https://cont/self"}]
    }

    client = Rapid7ApiClient(config)

    # Force the subsequent poll GET to always return in-progress.
    with patch.object(client, "_request_get", return_value=in_progress), patch("time.sleep"):
        with pytest.raises(TimeoutError):
            client._poll_request_to_completion(in_progress, fetch_id="f1", page_num=1)


def test_fetch_logs_errors_when_next_link_missing_but_has_next_is_true():
    """Fail loudly if the response indicates Next but doesn't provide an href."""

    from src.log_ingestion.api_client import Rapid7ApiClient

    config = _config(
        RAPID7_API_KEY="test_key",
        RAPID7_LOG_KEY="logkey_1",
        OUTPUT_DIR="/tmp/test",
        RAPID7_DATA_STORAGE_REGION="eu",
    )

    seed = Mock()
    seed.status_code = 200
    seed.headers = {"Content-Type": "application/json"}
    seed.text = "{}"
    seed.json.return_value = {
        "events": [],
        # Malformed: Next link present but missing href.
        "links": [{"rel": "Next"}],
    }

    client = Rapid7ApiClient(config)

    with patch.object(client, "_request_get", return_value=seed):
        with pytest.raises(ValueError):
            client.fetch_logs("1", "2")
