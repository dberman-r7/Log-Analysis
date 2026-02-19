# Implementation Plan: IP-2026-02-12-001-multi-parquet-cache-and-streaming-flush

**Status**: IN_PROGRESS  
**Created**: 2026-02-12  
**Last Updated**: 2026-02-16

## Ownership & Links

- **Related CR**: `docs/processes/change-requests/CR-2026-02-12-001.md`
- **Branch**: `feat/CR-2026-02-12-001-multi-parquet-cache-streaming-flush` (recommended)
- **PR**: TBD

---

## Quick Impact Assessment (QIA)

- **Functional change?** YES
  - Adds local Parquet caching keyed by `(log_id, subrange)`; can skip/reduce API calls.
  - Adds partial-range fetch for missing subranges.
  - Adds multi-Parquet analysis and Parquet-derived summary output.
  - Changes memory behavior via streaming flush.
- **Touches any CR-required triggers?** YES
  - Requirements/approach change (cache semantics), performance/reliability impacts, new on-disk artifacts.
- **CR required?** YES — new caching/partial-fetch workflow and output semantics.

---

## Amendment Notes (2026-02-16)

User correction/clarification applied:
- **Partial coverage** must fetch **only missing subranges**.
- For partial coverage, persist **additional segment datasets** (do not require compaction/merge).
- Analysis should be able to read **multiple Parquet datasets** (segments) for the requested window.
- **Memory-bounded processing** is required: process page-by-page and flush to Parquet periodically so buffers can be cleared.

---

## Full Impact Assessment (IA)

### 1) Functional / UX impact
- Operators can re-run ingestion for the same `(log_id, time window)` and avoid repeated downloads.
- If cached coverage is partial, the system fetches **only missing subranges** and persists additional segments (no compaction).
- Output includes an additional **Parquet-derived summary** and cache decision details (additive fields and logs).

### 2) Data / storage impact
- New on-disk cache footprint under `LOG_INGESTION_CACHE_DIR`.
- File count can grow (segments × parts). This is intentional to avoid compaction/merge complexity.
- Requires runbook guidance for:
  - cache growth/retention
  - safe deletion
  - how to interpret segment directories

### 3) Performance / SLO impact
- Expected improvement on reruns and partial windows (fewer API calls).
- Streaming flush bounds memory at the cost of writing more Parquet parts.
- Risk: too-small flush threshold -> many small part files -> slower reads. Mitigate with config defaults + guidance.

### 4) Reliability / failure-mode impact (fail loudly)
New failure modes and required handling:
- Cache dir not writable / permission denied -> `ERROR` log + raise.
- Parquet segment corrupt/unreadable -> `ERROR` log + raise (unless bypass is enabled).
- Range-math bugs (off-by-one at `[start,end)`) -> prevented via unit tests (REQ-029).
- Overlapping cached segments for same `log_id` and overlapping ranges -> treat as suspicious/corruption by default.

### 5) Security / compliance impact
- Local data-at-rest increases sensitivity of workstation storage.
- Cache paths must be constrained to cache root; no directory traversal.
- Do not log raw event payloads at INFO/WARN (keep to counts/ids/ranges).

### 6) Observability impact
- Add explicit cache decision events (`cache_hit`, `cache_partial`, `cache_miss`) with the missing-range plan.
- Add explicit write/flush events (part counts, rows buffered, segment paths).
- Add explicit summary event (`parquet_summary_generated`) with top-line stats.
- Errors must be structured and actionable.

### 7) Testing impact
- Add/extend tests for missing-subrange planning, partial fetch orchestration, streaming flush, multi-segment summary.
- Ensure tests cover multiple-gap windows and ordering invariants.

### 8) Documentation impact
- RTM must be updated if `src/` changes.
- Runbook must include cache layout, tuning, retention, and troubleshooting.

---

## Requirements & Traceability (RTM)

**Governance rule**: no source changes without RTM updates.

### Requirements in scope (already present in `/docs/requirements/rtm.md`)

- **REQ-023**: [FUNC] Local Parquet cache keyed by `log_id` + time window; reuse cached data.
- **REQ-024**: [FUNC] Compute cache coverage for requested half-open `[start,end)` and fetch only missing subranges (supports multiple gaps).
- **REQ-025**: [NFR-REL] Fail loudly on cache corruption/read failures unless bypass enabled.
- **REQ-026**: [NFR-OBS] Structured logs for cache decisions including missing ranges.
- **REQ-027**: [FUNC] Parquet-derived summary (row count, columns/types, timestamp aggregates).
- **REQ-028**: [NFR-PERF] Page-by-page processing + configurable flush threshold to bound memory; buffer cleared after flush.
- **REQ-029**: [FUNC] Missing-range planner returns canonical, sorted, non-overlapping intervals using half-open semantics.

---

## Contract (Inputs/Outputs/Error Modes)

### Inputs
- `log_id` / log key (existing config)
- `start_time`, `end_time` (ISO8601) normalized to epoch-ms
- Cache config: `LOG_INGESTION_CACHE_DIR`, `BYPASS_CACHE`
- Streaming config:
  - `FLUSH_ROWS` (rows per flush)
  - `FLUSH_BYTES` (approximate bytes per flush; optional; flush when either threshold met)

### Outputs
- Existing service result keys preserved:
  - `output_file`: path or None
  - `rows_processed`: int
  - `batches_processed`: int
  - `duration_seconds`: float
- Additive keys (non-breaking):
  - `segments_used`, `segments_written`
  - `cache_missing_ranges`, `cache_cached_ranges`
  - `summary_output` (path) + `summary` (dict)

### Fail-loudly errors
- Cache unreadable/corrupt → log `ERROR` with remediation (“delete segment dir” / enable bypass) and raise.
- Cache not writable → log `ERROR` and raise.
- API failure on missing subrange → raise (default; do not silently proceed).
- Summary generation failure → raise (unless explicitly disabled by config).

---

## Technical Design

### Range semantics
All windows are **half-open**: `[start_ms, end_ms)`.

**Invariants**:
- `start_ms < end_ms`.
- Missing-range planner returns:
  - sorted by start
  - non-overlapping
  - non-adjacent ranges (adjacent ranges should be merged)
  - each range strictly within requested window

### Cache keys + layout
Base directory: `LOG_INGESTION_CACHE_DIR`.

Proposed layout:
- `logs/{log_id}/from={start_ms}/to={end_ms}/part-00000.parquet`
- More parts: `part-00001.parquet`, etc.

Notes:
- Each `from=.../to=.../` directory is one “segment dataset”.
- No compaction: partial coverage fetch writes additional segments. Analysis reads multiple segments.

### Cache discovery
- Implement segment listing in `src/log_ingestion/cache_index.py`:
  - `list_segments(cache_root, log_id) -> list[Segment]` where `Segment` includes `start_ms`, `end_ms`, `path`.
- Define segment intersection:
  - A segment is eligible if it intersects requested window: `seg.start < req.end and req.start < seg.end`.

### Coverage planning + missing subrange algorithm

Inputs:
- Requested range `R=[r0,r1)`
- Cached segments `C = {[c0,c1), ...}` for same `log_id`

Algorithm:
1. Filter cached segments to ones that intersect `R`.
2. Normalize cached segments to `R` by clamping each to `R`:
   - `[max(c0,r0), min(c1,r1))`
3. Sort by start, merge overlaps/adjacency to produce cached union `U`.
4. Compute missing ranges `M = R \\ U`.
5. Decision:
   - **hit** if `M` empty
   - **miss** if no cached intersecting segments and `M == [R]`
   - **partial** otherwise

### Fetch orchestration (partial coverage)
For each missing range `m=[m0,m1)`:
1. Log `fetch_subrange_start`.
2. Call API for that subrange only.
3. Stream/process events page-by-page and write Parquet parts into segment dir for `[m0,m1)`.
4. Log `fetch_subrange_complete` with rows parts duration.

### Streaming flush (memory-bounded writes)
- Maintain an in-memory buffer of parsed events (list[dict]).
- Maintain an approximate byte counter for the buffer.
- Flush condition:
  - `len(buffer) >= FLUSH_ROWS` OR (`FLUSH_BYTES` set and `buffer_bytes >= FLUSH_BYTES`).
- On each flush:
  - write `part-{idx:05d}.parquet`
  - clear buffer and reset bytes counter

### Multi-parquet analysis reading
- For a requested window `R`, determine `segments_used` = all cached segments intersecting `R`.
- Read all segments used as a single logical dataset for summary.

### Parquet-derived summary
Summary fields (minimum):
- `row_count`
- `columns`: list of names
- `schema`: map `{col_name: data_type}` when available
- `timestamp_min`, `timestamp_max` if `timestamp` column exists

Summary artifact:
- write JSON alongside the run output and/or under the cache root using a deterministic filename.

---

## Observability Events (Structured Logs)

All events must be structured JSON.

Required event shapes (minimum fields):
- `cache_scan_start` / `cache_scan_complete`: `log_id`, `cache_dir`, `segment_count`
- `cache_coverage_planned`: `log_id`, `requested_range`, `cached_ranges`, `missing_ranges`
- `cache_hit` / `cache_partial` / `cache_miss`: include `requested_range`
- `fetch_subrange_start/complete`: `subrange`, `duration_ms`, `rows_fetched`, `parts_written`, `segment_dir`
- `flush_start/complete`: `segment_dir`, `part_index`, `rows_buffered`, `bytes_buffered`
- `parquet_summary_generated`: `summary_output`, `row_count`, `timestamp_min`, `timestamp_max`, `columns`

Error events (must be `ERROR`):
- `cache_read_failed`, `cache_write_failed`, `parquet_summary_failed`

---

## Test Plan (TDD)

### Unit tests
- Missing-subranges planner:
  - multiple gaps
  - adjacency (touching ranges merge)
  - overlap
  - cached segments outside window ignored
  - invalid window fails loudly
- Segment selection intersection

### Service/integration tests (mock API)
- Full cache hit: no API calls; output from cache
- Partial coverage: fetch only missing ranges; writes new segment
- Multiple gaps: fetch per gap
- Streaming flush: multiple parts written; buffer cleared
- Parquet summary: multi-segment summary correct

---

## Checklist

### Governance
- [ ] Confirm CR-2026-02-12-001 is APPROVED/ATP
- [ ] Ensure RTM rows REQ-023..REQ-029 have correct trace links (impl + tests)
- [ ] Update runbook `docs/runbooks/log-ingestion-service.md` (cache layout, tuning, retention)
- [ ] (Optional) Update `docs/requirements/slos.md` for cache+streaming SLIs/SLOs

### Local Dev Environment (blocking)
- [ ] Confirm Python toolchain available for tests (`python3 -m pytest`) and required deps installed

### TDD / Implementation
- [ ] RED: tests for missing-subrange planning (REQ-029)
- [ ] GREEN: implement missing-subrange planning + canonicalization (REQ-029)
- [ ] RED: tests for cache decision + partial fetch orchestration (REQ-023/024)
- [ ] GREEN: implement cache discovery + coverage planning + per-gap fetch (REQ-023/024)
- [ ] RED: tests for fail-loudly cache read/write errors + bypass behavior (REQ-025)
- [ ] GREEN: implement fail-loudly + bypass paths (REQ-025)
- [ ] RED: tests for structured cache decision logs (REQ-026)
- [ ] GREEN: implement structured decision logs with required fields (REQ-026)
- [ ] RED: tests for streaming flush threshold(s) incl. rows (and bytes if configured) (REQ-028)
- [ ] GREEN: implement streaming flush (REQ-028)
- [ ] RED: tests for parquet-derived summary across multiple segments (REQ-027)
- [ ] GREEN: implement parquet summary + JSON artifact (REQ-027)
- [ ] REFACTOR: clean up and keep behavior stable

### Validation
- [ ] Unit tests pass; coverage ≥ 80%
- [ ] Lint/format/typecheck pass (as applicable)
- [ ] Security/dependency audit pass (as applicable)

---

## Progress Log

- 2026-02-12 00:00 UTC — Plan created and linked to CR.
- 2026-02-16 00:00 UTC — Amended plan per user correction: fetch missing subranges, keep multi-parquet segments, add memory-bounded streaming flush requirement.

---

## Restart / Continue Instructions

On any restart/continue:
1. Open this file.
2. Resume from the first unchecked item.
3. Update the checklist and Progress Log as you complete steps.
