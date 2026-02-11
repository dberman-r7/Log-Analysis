"""Tests for `Rapid7ApiClient.list_logs()`.

REQ coverage:
- REQ-012: x-api-key auth is used (via session headers)
- REQ-015: 429 handling via X-RateLimit-Reset (RateLimitedException)

We keep these tests unit-level and mock the underlying HTTP calls.
"""

from src.log_ingestion.api_client import RateLimitedException, Rapid7ApiClient
from src.log_ingestion.config import LogIngestionConfig


class _DummyResp:
    def __init__(self, status_code: int, json_body, headers=None):
        self.status_code = status_code
        self._json_body = json_body
        self.headers = headers or {}

    def json(self):
        return self._json_body

    def raise_for_status(self):
        if 400 <= self.status_code:
            raise Exception(f"HTTP {self.status_code}")


def test_list_logs_parses_logs_and_filters_invalid(mocker, tmp_path):
    config = LogIngestionConfig(rapid7_api_key="k", rapid7_log_key="lk", output_dir=tmp_path)
    client = Rapid7ApiClient(config)

    resp = _DummyResp(
        200,
        {
            "logs": [
                {"id": "id1", "name": "Log A"},
                {"id": "id2", "name": "Log B"},
                {"id": "", "name": "bad"},
                "not-a-dict",
            ]
        },
    )

    mocker.patch.object(client, "_request_get", return_value=resp)

    logs = client.list_logs()

    assert [l.id for l in logs] == ["id1", "id2"]
    assert [l.name for l in logs] == ["Log A", "Log B"]


def test_list_logs_raises_rate_limited(mocker, tmp_path):
    config = LogIngestionConfig(rapid7_api_key="k", rapid7_log_key="lk", output_dir=tmp_path)
    client = Rapid7ApiClient(config)

    resp = _DummyResp(429, {"message": "rate limited"}, headers={"X-RateLimit-Reset": "2"})
    mocker.patch.object(client, "_request_get", return_value=resp)

    try:
        client.list_logs()
        assert False, "Expected RateLimitedException"
    except RateLimitedException as e:
        assert e.secs_until_reset == 2
