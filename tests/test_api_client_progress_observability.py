"""Observability tests for Log Search polling + pagination progress.

REQ coverage:
- REQ-014: pagination via links[rel=Next]
- REQ-025: poll debug/log visibility
- REQ-026: (added by CR-2026-02-11-004) progress logs for pagination/poll correlation
"""

from __future__ import annotations

import json
from unittest.mock import Mock

import pytest

from src.log_ingestion.api_client import Rapid7ApiClient


def _make_response(*, status_code: int, body: dict) -> Mock:
    resp = Mock()
    resp.status_code = status_code
    resp.headers = {"Content-Type": "application/json"}
    resp.json.return_value = body
    resp.text = json.dumps(body)
    return resp


def _json_events_from_caplog(caplog) -> list[dict]:
    out: list[dict] = []
    for rec in caplog.records:
        try:
            out.append(json.loads(rec.getMessage()))
        except Exception:
            # Ignore non-JSON messages.
            continue
    return out


def test_fetch_logs_emits_per_page_progress_logs(caplog, test_config, monkeypatch):
    caplog.set_level("INFO")

    # Arrange: two pages.
    # Page 1 is returned after polling completes, and contains Next.
    page1_body = {
        "logs": ["log-key"],
        "events": [
            {"message": "a", "timestamp": 1000},
            {"message": "a", "timestamp": 2000},
        ],
        "links": [
            {"rel": "Next", "href": "https://example.test/next?page=2"},
        ],
    }
    # Page 2 is terminal.
    page2_body = {
        "logs": ["log-key"],
        "events": [
            {"message": "b", "timestamp": 1500},
            {"message": "b", "timestamp": 4000},
            {"message": "b", "timestamp": 3000},
        ],
        "links": [],
    }

    seed_query_resp = _make_response(
        status_code=202,
        body={"links": [{"rel": "Self", "href": "https://example.test/self?page=1"}]},
    )
    seed_next_resp = _make_response(
        status_code=202,
        body={"links": [{"rel": "Self", "href": "https://example.test/self?page=2"}]},
    )

    client = Rapid7ApiClient(test_config)

    def fake_get(url, params=None, timeout=None):
        if "query/logs" in url:
            return seed_query_resp
        if url.startswith("https://example.test/next"):
            return seed_next_resp
        if url.startswith("https://example.test/self?page=1"):
            return _make_response(status_code=200, body=page1_body)
        if url.startswith("https://example.test/self?page=2"):
            return _make_response(status_code=200, body=page2_body)
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(client.session, "get", fake_get)
    monkeypatch.setattr("time.sleep", lambda *_args, **_kwargs: None)

    # Act
    from unittest.mock import patch

    with patch("src.log_ingestion.api_client.logger") as mock_logger:
        out = client.fetch_logs("1", "2")

    # Assert returned JSON includes pages and fetch_id.
    parsed = json.loads(out)
    assert len(parsed["pages"]) == 2
    fetch_id = parsed["fetch_id"]

    # Assert on structured logger calls (stable regardless of structlog processors).
    info_events = [c.args[0] for c in mock_logger.info.call_args_list]
    error_events = [c.args[0] for c in mock_logger.error.call_args_list]
    event_names = info_events + error_events

    assert "logsearch_fetch_start" in event_names
    assert "logsearch_page_complete" in event_names
    assert "logsearch_fetch_complete" in event_names

    page_complete_calls = [
        c
        for c in mock_logger.info.call_args_list
        if c.args and c.args[0] == "logsearch_page_complete"
    ]
    assert len(page_complete_calls) == 2
    assert {c.kwargs.get("page_num") for c in page_complete_calls} == {1, 2}
    assert all(c.kwargs.get("fetch_id") == fetch_id for c in page_complete_calls)

    # REQ-027: per-page max event timestamp emitted to show dataset progress.
    page_max_by_num = {c.kwargs.get("page_num"): c.kwargs.get("page_max_event_timestamp") for c in page_complete_calls}
    assert page_max_by_num[1] == 2000
    assert page_max_by_num[2] == 4000

    page_min_by_num = {c.kwargs.get("page_num"): c.kwargs.get("page_min_event_timestamp") for c in page_complete_calls}
    assert page_min_by_num[1] == 1000
    assert page_min_by_num[2] == 1500

    # ISO8601 fields make progress human-readable.
    page_max_iso_by_num = {
        c.kwargs.get("page_num"): c.kwargs.get("page_max_event_timestamp_iso") for c in page_complete_calls
    }
    assert page_max_iso_by_num[1] == "1970-01-01T00:00:02Z"
    assert page_max_iso_by_num[2] == "1970-01-01T00:00:04Z"

    page_min_iso_by_num = {
        c.kwargs.get("page_num"): c.kwargs.get("page_min_event_timestamp_iso") for c in page_complete_calls
    }
    assert page_min_iso_by_num[1] == "1970-01-01T00:00:01Z"
    assert page_min_iso_by_num[2] == "1970-01-01T00:00:01.500000Z"


def test_pagination_not_advancing_is_fail_loud(caplog, test_config, monkeypatch):
    caplog.set_level("INFO")

    # Arrange: page repeats the same Next URL.
    repeating_next = "https://example.test/next?page=2"
    page_body = {
        "logs": ["log-key"],
        "events": [{"message": "x"}],
        "links": [{"rel": "Next", "href": repeating_next}],
    }

    seed_query_resp = _make_response(
        status_code=202,
        body={"links": [{"rel": "Self", "href": "https://example.test/self?page=1"}]},
    )

    client = Rapid7ApiClient(test_config)

    def fake_get(url, params=None, timeout=None):
        if "query/logs" in url:
            return seed_query_resp
        if url.startswith("https://example.test/self?page=1"):
            return _make_response(status_code=200, body=page_body)
        if url.startswith(repeating_next):
            # Next seed keeps returning a body that points to the same Next.
            return _make_response(status_code=200, body=page_body)
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(client.session, "get", fake_get)
    monkeypatch.setattr("time.sleep", lambda *_args, **_kwargs: None)

    from unittest.mock import patch

    with patch("src.log_ingestion.api_client.logger") as mock_logger:
        with pytest.raises(RuntimeError):
            client.fetch_logs("1", "2")

    assert any(
        c.args and c.args[0] == "logsearch_pagination_not_advancing"
        for c in mock_logger.error.call_args_list
    )


def test_polling_json_parsed_once_per_iteration(test_config, monkeypatch):
    """Perf guardrail: polling loop should avoid redundant Response.json() calls."""

    client = Rapid7ApiClient(test_config)

    # Seed query returns in-progress (Self), then completion body.
    seed_query_resp = _make_response(
        status_code=202,
        body={"links": [{"rel": "Self", "href": "https://example.test/self"}]},
    )

    completed_body = {"logs": ["log-key"], "events": [{"message": "a", "timestamp": 1}], "links": []}

    # The polling GET response should have json() called at most 2x total:
    # - once for debug/info summary
    # - (at most) once for the in-progress / completion decision
    # After our code change, it should be 1x.
    polling_resp = _make_response(status_code=200, body=completed_body)

    # Make json() count calls.
    polling_resp.json = Mock(return_value=completed_body)

    def fake_get(url, params=None, timeout=None):
        if "query/logs" in url:
            return seed_query_resp
        if url == "https://example.test/self":
            return polling_resp
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(client.session, "get", fake_get)
    monkeypatch.setattr("time.sleep", lambda *_args, **_kwargs: None)

    from unittest.mock import patch

    with patch("src.log_ingestion.api_client.logger"):
        client.fetch_logs("1", "2")

    assert polling_resp.json.call_count == 1

