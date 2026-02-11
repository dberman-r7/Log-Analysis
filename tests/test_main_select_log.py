"""Unit tests for the `--select-log` flow.

We avoid end-to-end subprocess execution; instead we call the internal helper
`_run_log_selection()` so we can deterministically mock:
- API client listing
- user input
- env file update

This boosts coverage for `src.log_ingestion.main` without touching network.
"""

from pathlib import Path

from src.log_ingestion.config import LogIngestionConfig
from src.log_ingestion.log_selection import LogDescriptor, LogSetDescriptor


def test_run_log_selection_updates_env_file(mocker, tmp_path: Path):
    from src.log_ingestion import main

    config = LogIngestionConfig(rapid7_api_key="k", rapid7_log_key="lk", output_dir=tmp_path)

    # Patch both the symbol used by main and the underlying class definition
    # to avoid accidental real network calls.
    client_cls = mocker.patch("src.log_ingestion.main.Rapid7ApiClient")
    api_client_cls = mocker.patch("src.log_ingestion.api_client.Rapid7ApiClient")
    api_client_cls.return_value = client_cls.return_value

    client = client_cls.return_value
    client.list_log_sets.return_value = [
        LogSetDescriptor(
            id="ls-1",
            name="Set One",
            logs=[
                LogDescriptor(id="id1", name="Log A"),
                LogDescriptor(id="id2", name="Log B"),
            ],
        ),
    ]

    # The CLI must not hit per-logset membership endpoints in this environment.
    client.list_logs_in_log_set.side_effect = AssertionError(
        "list_logs_in_log_set() should not be called"
    )

    # First input selects the only log set; second selects the log.
    mocker.patch("builtins.input", side_effect=["1", "2"])

    env_path = tmp_path / ".env"
    rc = main._run_log_selection(config, str(env_path))

    assert rc == 0
    assert env_path.exists()
    assert "RAPID7_LOG_KEY=id2" in env_path.read_text(encoding="utf-8")


def test_run_log_selection_no_embedded_logs_returns_error(mocker, tmp_path: Path):
    from src.log_ingestion import main

    config = LogIngestionConfig(rapid7_api_key="k", rapid7_log_key="lk", output_dir=tmp_path)

    client_cls = mocker.patch("src.log_ingestion.main.Rapid7ApiClient")
    api_client_cls = mocker.patch("src.log_ingestion.api_client.Rapid7ApiClient")
    api_client_cls.return_value = client_cls.return_value

    client = client_cls.return_value
    client.list_log_sets.return_value = [
        LogSetDescriptor(id="ls-1", name="Set One", logs=[]),
    ]

    # Should never be called now.
    client.list_logs_in_log_set.side_effect = AssertionError(
        "list_logs_in_log_set() should not be called"
    )

    mocker.patch("builtins.input", return_value="1")

    env_path = tmp_path / ".env"
    rc = main._run_log_selection(config, str(env_path))

    assert rc == 1
