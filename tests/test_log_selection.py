import pytest
from src.log_ingestion.log_selection import LogDescriptor, choose_log_id
from src.log_ingestion.log_selection import LogSetDescriptor, choose_log_set_id


# --- existing tests for log selection by log id (REQ-018 predecessor) ---
def test_choose_log_id_by_index():
    logs = [LogDescriptor(id="id1", name="a"), LogDescriptor(id="id2", name="b")]
    assert choose_log_id(logs, "2") == "id2"


def test_choose_log_id_by_direct_id():
    logs = [LogDescriptor(id="id1", name="a"), LogDescriptor(id="id2", name="b")]
    assert choose_log_id(logs, "id1") == "id1"


def test_choose_log_id_invalid_selection():
    logs = [LogDescriptor(id="id1", name="a")]
    with pytest.raises(ValueError):
        choose_log_id(logs, "999")


def test_choose_log_id_empty_logs():
    with pytest.raises(ValueError):
        choose_log_id([], "1")


# --- new tests for Log Set selection (REQ-017) ---
def test_choose_log_set_id_by_index():
    log_sets = [
        LogSetDescriptor(id="ls-1", name="Set One", description=""),
        LogSetDescriptor(id="ls-2", name="Set Two", description=""),
    ]
    assert choose_log_set_id(log_sets, "1") == "ls-1"
    assert choose_log_set_id(log_sets, "2") == "ls-2"


def test_choose_log_set_id_by_direct_id():
    log_sets = [
        LogSetDescriptor(id="ls-1", name="Set One", description=""),
        LogSetDescriptor(id="ls-2", name="Set Two", description=""),
    ]
    assert choose_log_set_id(log_sets, "ls-2") == "ls-2"


def test_choose_log_set_id_invalid_selection():
    log_sets = [LogSetDescriptor(id="ls-1", name="Set One", description="")]

    with pytest.raises(ValueError):
        choose_log_set_id(log_sets, "")

    with pytest.raises(ValueError):
        choose_log_set_id(log_sets, "0")

    with pytest.raises(ValueError):
        choose_log_set_id(log_sets, "999")


def test_choose_log_set_id_empty_log_sets():
    with pytest.raises(ValueError):
        choose_log_set_id([], "1")
