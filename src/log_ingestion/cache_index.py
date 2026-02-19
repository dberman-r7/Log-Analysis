"""Cache index and missing-range planning for Parquet segment cache.

Implements REQ-023/REQ-024/REQ-025/REQ-029.

Range semantics are half-open: [start_ms, end_ms).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import structlog

logger = structlog.get_logger()


RangeMs = Tuple[int, int]


def _normalize_ranges(ranges: Iterable[RangeMs]) -> List[RangeMs]:
    """Sort and merge overlapping/adjacent ranges."""
    sorted_ranges = sorted((int(s), int(e)) for s, e in ranges)
    merged: List[RangeMs] = []
    for s, e in sorted_ranges:
        if e <= s:
            continue
        if not merged:
            merged.append((s, e))
            continue
        ps, pe = merged[-1]
        if s <= pe:  # overlap or adjacency
            merged[-1] = (ps, max(pe, e))
        else:
            merged.append((s, e))
    return merged


def compute_missing_subranges(
    *,
    requested_start_ms: int,
    requested_end_ms: int,
    cached_ranges_ms: Sequence[RangeMs],
) -> List[RangeMs]:
    """Return missing subranges of requested window not covered by cached ranges.

    Args:
        requested_start_ms: inclusive start
        requested_end_ms: exclusive end
        cached_ranges_ms: list of half-open intervals [s,e)

    Returns:
        Sorted, non-overlapping list of missing intervals.
    """

    requested_start_ms = int(requested_start_ms)
    requested_end_ms = int(requested_end_ms)

    if requested_end_ms <= requested_start_ms:
        raise ValueError("requested_end_ms must be greater than requested_start_ms")

    normalized = _normalize_ranges(cached_ranges_ms)

    missing: List[RangeMs] = []
    cursor = requested_start_ms
    for s, e in normalized:
        if e <= requested_start_ms:
            continue
        if s >= requested_end_ms:
            break
        s = max(s, requested_start_ms)
        e = min(e, requested_end_ms)
        if s > cursor:
            missing.append((cursor, s))
        cursor = max(cursor, e)
        if cursor >= requested_end_ms:
            break

    if cursor < requested_end_ms:
        missing.append((cursor, requested_end_ms))

    return missing


@dataclass(frozen=True)
class CacheSegment:
    log_id: str
    start_ms: int
    end_ms: int
    path: Path


def segment_dir_for_range(cache_root: Path, log_id: str, start_ms: int, end_ms: int) -> Path:
    # Layout (REQ-023): {cache_root}/{log_id}/from={start}/to={end}/part-*.parquet
    # Note: tests create segments using this function and pass cache_root directly.
    return Path(cache_root) / log_id / f"from={int(start_ms)}" / f"to={int(end_ms)}"


def list_segments(cache_root: Path, log_id: str) -> List[CacheSegment]:
    base = Path(cache_root) / log_id
    if not base.exists():
        return []

    segments: List[CacheSegment] = []
    # Layout: {cache_root}/{log_id}/from={start}/to={end}/part-*.parquet
    for from_dir in base.glob("from=*"):
        try:
            start_ms = int(from_dir.name.split("=", 1)[1])
        except Exception:
            continue
        for to_dir in from_dir.glob("to=*"):
            try:
                end_ms = int(to_dir.name.split("=", 1)[1])
            except Exception:
                continue
            if end_ms <= start_ms:
                continue
            if not to_dir.exists():
                continue
            segments.append(
                CacheSegment(
                    log_id=log_id,
                    start_ms=start_ms,
                    end_ms=end_ms,
                    path=to_dir,
                )
            )

    return sorted(segments, key=lambda s: (s.start_ms, s.end_ms, str(s.path)))


def cached_ranges_for_log(cache_root: Path, log_id: str) -> List[RangeMs]:
    return [(s.start_ms, s.end_ms) for s in list_segments(cache_root, log_id)]
