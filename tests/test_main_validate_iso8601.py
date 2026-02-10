"""Unit tests for `src.log_ingestion.main.validate_iso8601`.

These tests improve coverage on `main.py` while validating the CLI's date/time
input validation.
"""

from src.log_ingestion.main import validate_iso8601


def test_validate_iso8601_accepts_zulu_timestamp():
    assert validate_iso8601("2026-02-10T00:00:00Z") is True


def test_validate_iso8601_rejects_non_iso_string():
    assert validate_iso8601("not-a-timestamp") is False


def test_validate_iso8601_rejects_empty_string():
    assert validate_iso8601("") is False
