"""Tests for `src.log_ingestion.main` CLI helpers.

These tests are intentionally lightweight. They focus on the pure helper
functions (`validate_iso8601`) and argument parsing wiring (`parse_args`).

This helps keep overall coverage above the configured threshold without
needing to spawn subprocesses.
"""

import pytest


def test_validate_iso8601_accepts_zulu_timestamp():
    from src.log_ingestion.main import validate_iso8601

    assert validate_iso8601("2026-02-10T10:00:00Z") is True


def test_validate_iso8601_rejects_invalid_timestamp():
    from src.log_ingestion.main import validate_iso8601

    assert validate_iso8601("not-a-timestamp") is False


def test_parse_args_parses_required_args():
    from src.log_ingestion.main import parse_args

    args = parse_args(["--start-time", "2026-02-10T00:00:00Z", "--end-time", "2026-02-10T01:00:00Z"])

    assert args.start_time == "2026-02-10T00:00:00Z"
    assert args.end_time == "2026-02-10T01:00:00Z"
    assert args.partition_date is None


def test_parse_args_optional_partition_date():
    from src.log_ingestion.main import parse_args

    args = parse_args(
        [
            "--start-time",
            "2026-02-10T00:00:00Z",
            "--end-time",
            "2026-02-10T01:00:00Z",
            "--partition-date",
            "2026-02-10",
        ]
    )

    assert args.partition_date == "2026-02-10"


def test_parse_args_missing_required_args_exits():
    from src.log_ingestion.main import parse_args

    with pytest.raises(SystemExit):
        parse_args([])


def test_parse_args_select_log_and_env_file():
    from src.log_ingestion.main import parse_args

    args = parse_args(
        [
            "--select-log",
            "--env-file",
            "custom.env",
            "--start-time",
            "2026-02-10T00:00:00Z",
            "--end-time",
            "2026-02-10T01:00:00Z",
        ]
    )

    assert args.select_log is True
    assert args.env_file == "custom.env"
