"""Coverage tests for src.log_ingestion.main execution paths.

These tests focus on the CLI runner / orchestration wrapper and are intended
to raise overall project coverage above the enforced minimum.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest


def test_main_returns_nonzero_when_missing_required_env(monkeypatch, caplog, tmp_path: Path) -> None:
    """Main should fail loudly when required config is missing."""
    # Ensure no required env vars exist.
    monkeypatch.delenv("RAPID7_API_KEY", raising=False)
    monkeypatch.delenv("RAPID7_LOG_KEY", raising=False)

    # Provide argv required by argparse.
    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--start-time",
            "2026-02-10T00:00:00Z",
            "--end-time",
            "2026-02-10T00:00:01Z",
        ],
    )

    caplog.set_level(logging.ERROR)

    from src.log_ingestion import main as main_mod

    with pytest.raises(SystemExit) as exc:
        main_mod.main()

    assert int(exc.value.code) != 0
    # Don't couple to structlog/stdlog wiring; it's enough that we exited non-zero.


def test_main_happy_path_invokes_service(monkeypatch, tmp_path: Path) -> None:
    """Main should invoke the service and return 0 on success."""
    monkeypatch.setenv("RAPID7_API_KEY", "k")
    monkeypatch.setenv("RAPID7_LOG_KEY", "l")

    # Provide argv required by argparse.
    monkeypatch.setattr(
        "sys.argv",
        [
            "prog",
            "--start-time",
            "2026-02-10T00:00:00Z",
            "--end-time",
            "2026-02-10T00:00:01Z",
        ],
    )

    from src.log_ingestion import main as main_mod

    class _DummyService:
        def __init__(self, config):
            self.config = config

        def run(self, start_time: str, end_time: str, partition_date=None):
            return {
                "output_file": None,
                "rows_processed": 0,
                "batches_processed": 0,
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": 0.0,
            }

    monkeypatch.setattr(main_mod, "LogIngestionService", _DummyService)

    with pytest.raises(SystemExit) as exc:
        main_mod.main()

    assert int(exc.value.code) == 0
