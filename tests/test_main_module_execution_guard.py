"""Tests for module execution guard.

REQ-020: CLI should support module execution; direct script execution should fail loudly.

These tests validate the guard logic in a unit-friendly way. We don't spawn a
subprocess here to keep the tests fast and hermetic.
"""

import pytest


def test_main_raises_actionable_error_when_run_as_script(monkeypatch):
    """REQ-020: provide actionable guidance when script-run is detected."""
    from src.log_ingestion import main as main_module

    # Simulate direct script execution (i.e., no package context)
    monkeypatch.setattr(main_module, "__package__", None, raising=False)
    monkeypatch.setattr(main_module, "__name__", "__main__", raising=False)

    with pytest.raises(RuntimeError) as excinfo:
        main_module._ensure_module_execution_context()

    msg = str(excinfo.value)
    assert "python -m" in msg
    assert "src.log_ingestion.main" in msg
