"""Additional coverage for `src.log_ingestion.main` helpers.

Governance note:
- REQ-020 includes ISO8601 validation behavior.
- These tests increase coverage without changing production semantics.
"""

import pytest


@pytest.mark.parametrize(
    "ts",
    [
        "2026-02-10T00:00:00Z",
        "2026-02-10T00:00:00+00:00",
        "2026-02-10T12:34:56.123456Z",
        "2026-02-10T12:34:56.123456+00:00",
        "2026-02-10T12:34:56-05:00",
    ],
)
def test_validate_iso8601_accepts_common_forms(ts: str) -> None:
    from src.log_ingestion.main import validate_iso8601

    assert validate_iso8601(ts) is True


@pytest.mark.parametrize(
    "ts",
    [
        "",
        "not-a-timestamp",
        "2026-02-10",  # date only (no timezone)
        "2026-02-10T00:00:00",  # missing timezone
        "2026-13-10T00:00:00Z",  # invalid month
        "2026-02-30T00:00:00Z",  # invalid day
        "2026-02-10T25:00:00Z",  # invalid hour
    ],
)
def test_validate_iso8601_rejects_invalid(ts: str) -> None:
    from src.log_ingestion.main import validate_iso8601

    assert validate_iso8601(ts) is False
