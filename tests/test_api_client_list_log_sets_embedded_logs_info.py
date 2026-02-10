"""Tests for parsing `logs_info` from the logsets listing response.

Requirement intent:
- When `/management/logsets` includes `logs_info` for each log set, selection flows
  should be able to use it without making per-logset membership calls.

These tests are unit-level: no network calls.
"""

from src.log_ingestion.api_client import Rapid7ApiClient
from src.log_ingestion.config import LogIngestionConfig


def test_list_log_sets_parses_embedded_logs_info(mocker, tmp_path):
    cfg = LogIngestionConfig(rapid7_api_key="k", rapid7_log_key="lk", output_dir=tmp_path)
    client = Rapid7ApiClient(cfg)

    resp = mocker.Mock()
    resp.status_code = 200
    resp.json.return_value = {
        "logsets": [
            {
                "id": "ls-1",
                "name": "Set One",
                "description": "Desc",
                "logs_info": [
                    {"id": "log-1", "name": "Log A"},
                    {"id": "log-2", "name": "Log B"},
                ],
            }
        ]
    }
    resp.raise_for_status.return_value = None

    mocker.patch.object(client, "_request_get", return_value=resp)

    log_sets = client.list_log_sets()

    assert len(log_sets) == 1
    assert log_sets[0].id == "ls-1"
    assert log_sets[0].logs is not None
    assert [l.id for l in log_sets[0].logs] == ["log-1", "log-2"]


def test_list_log_sets_handles_missing_logs_info(mocker, tmp_path):
    cfg = LogIngestionConfig(rapid7_api_key="k", rapid7_log_key="lk", output_dir=tmp_path)
    client = Rapid7ApiClient(cfg)

    resp = mocker.Mock()
    resp.status_code = 200
    resp.json.return_value = {
        "logsets": [
            {
                "id": "ls-1",
                "name": "Set One",
                "description": "",
                # no logs_info
            }
        ]
    }
    resp.raise_for_status.return_value = None

    mocker.patch.object(client, "_request_get", return_value=resp)

    log_sets = client.list_log_sets()

    assert len(log_sets) == 1
    # We normalize to an empty list when logs_info isn't present.
    assert log_sets[0].logs == []
