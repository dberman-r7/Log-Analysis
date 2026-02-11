"""Unit tests for `Rapid7ApiClient.list_logs_in_log_set` behavior.

In this repository's target environment, log membership is provided inline in the
`list_log_sets()` response via `logs_info`. Per-logset membership endpoints are
unsupported and/or can return 404.

Requirement intent (REQ-019): this method must **fail loudly** with actionable
guidance and must **not** attempt network calls.
"""

import pytest

from src.log_ingestion.api_client import Rapid7ApiClient
from src.log_ingestion.config import LogIngestionConfig


def test_list_logs_in_log_set_fails_loudly_without_network_calls(mocker, tmp_path):
    cfg = LogIngestionConfig(rapid7_api_key="k", rapid7_log_key="lk", output_dir=tmp_path)
    client = Rapid7ApiClient(cfg)

    # Ensure we don't make HTTP calls from this method.
    mocker.patch.object(client, "_request_get", side_effect=AssertionError("network not allowed"))

    with pytest.raises(ValueError) as exc:
        client.list_logs_in_log_set("ls-1")

    assert "logs_info" in str(exc.value)
