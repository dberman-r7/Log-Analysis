from pathlib import Path

import pytest

from src.log_ingestion.env_utils import upsert_env_var


def test_upsert_env_var_creates_file(tmp_path: Path):
    env_path = tmp_path / ".env"

    result = upsert_env_var(env_path, "RAPID7_LOG_KEY", "abc")

    assert result.created is True
    assert env_path.exists()
    assert "RAPID7_LOG_KEY=abc" in env_path.read_text(encoding="utf-8")


def test_upsert_env_var_updates_existing_key_and_preserves_comments(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "# comment\nRAPID7_LOG_KEY=old\nOTHER=1\nRAPID7_LOG_KEY=dup\n",
        encoding="utf-8",
    )

    upsert_env_var(env_path, "RAPID7_LOG_KEY", "new")

    text = env_path.read_text(encoding="utf-8")
    assert "# comment" in text
    assert "OTHER=1" in text
    assert text.count("RAPID7_LOG_KEY=") == 1
    assert "RAPID7_LOG_KEY=new" in text


def test_upsert_env_var_appends_key_if_missing(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text("A=1\n", encoding="utf-8")

    upsert_env_var(env_path, "RAPID7_LOG_KEY", "x")

    text = env_path.read_text(encoding="utf-8")
    assert "A=1" in text
    assert "RAPID7_LOG_KEY=x" in text


def test_upsert_env_var_rejects_bad_key(tmp_path: Path):
    env_path = tmp_path / ".env"
    with pytest.raises(ValueError):
        upsert_env_var(env_path, "BAD=KEY", "x")
