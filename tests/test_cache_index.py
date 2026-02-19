import pytest


def test_missing_subranges_half_open_no_gap_for_adjacent_segments():
    """Adjacent cached segments [0,10) and [10,20) cover [0,20) fully (no missing)."""
    from src.log_ingestion.cache_index import compute_missing_subranges

    missing = compute_missing_subranges(
        requested_start_ms=0,
        requested_end_ms=20,
        cached_ranges_ms=[(0, 10), (10, 20)],
    )
    assert missing == []


def test_missing_subranges_multiple_gaps_returns_two_intervals():
    """Planner should return multiple disjoint gaps inside the requested window."""
    from src.log_ingestion.cache_index import compute_missing_subranges

    missing = compute_missing_subranges(
        requested_start_ms=0,
        requested_end_ms=100,
        cached_ranges_ms=[(0, 10), (20, 30), (80, 100)],
    )
    assert missing == [(10, 20), (30, 80)]


def test_planner_rejects_invalid_window_end_before_start():
    from src.log_ingestion.cache_index import compute_missing_subranges

    with pytest.raises(ValueError, match="requested_end_ms must be greater than requested_start_ms"):
        compute_missing_subranges(
            requested_start_ms=10,
            requested_end_ms=10,
            cached_ranges_ms=[],
        )
