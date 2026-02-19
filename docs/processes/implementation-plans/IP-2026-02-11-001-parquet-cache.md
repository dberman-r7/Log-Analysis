# Implementation Plan: IP-2026-02-11-001

**Status**: DRAFT

**Created**: 2026-02-11 00:00:00 UTC  
**Last Updated**: 2026-02-11 00:00:00 UTC

## Ownership & Links

- **Owner / Agent**: Copilot
- **Branch**: feat/REQ-XXX-parquet-cache
- **PR**: TBD
- **Related CR (if any)**: CR-2026-02-11-007
- **Related REQ(s)**: TBD (new REQs will be added to RTM)

---

## Quick Impact Assessment (QIA)

- **Functional change?** YES
- **Touches CR-required triggers?** YES
- **CR required?** YES — Rationale: adds new requirements and introduces a new cache workflow with storage/performance implications.

### Scope Summary
- **Files expected to change**:
  - [ ] `src/log_ingestion/service.py`
  - [ ] `src/log_ingestion/config.py`
  - [ ] `src/log_ingestion/main.py`
  - [ ] `src/log_ingestion/parquet_writer.py`
  - [ ] `src/log_ingestion/api_client.py` (only if range-based fetch API changes are necessary)
  - [ ] New: `src/log_ingestion/cache_index.py` (cache coverage + range math)
  - [ ] New: `src/log_ingestion/parquet_summary.py` (summary/aggregates from parquet)
  - [ ] `tests/test_service.py`
  - [ ] New tests: `tests/test_cache_index.py`, `tests/test_parquet_summary.py`
  - [ ] `docs/requirements/rtm.md`
  - [ ] `docs/runbooks/log-ingestion-service.md`
  - [ ] (Optional) `docs/requirements/slos.md`

---

## Contract (what we’re building)

### Inputs
- `log_id` (or “log name”/set+name mapping already used in the app)
- Requested time window: `[start_time, end_time]` (ISO8601; current CLI supports)
- Cached events persisted as Parquet on local disk

### Outputs
- Pipeline processes **exactly** the events in the requested window.
- If cache is complete: **no API fetch** is made.
- If cache is partial: fetch only missing sub-ranges, append to cache, then process.
- Emit a **parquet-derived summary**: columns, row count, min/max timestamps, and a small set of safe aggregates.

### Error modes / “fail loudly”
- Cache read/metadata corruption must log `ERROR` with enough context and fail (unless explicitly configured to bypass cache).
- Range computation must be tested to avoid gaps/overlaps and off-by-one boundaries.

---

## Implementation Checklist

### Pre-implementation
- [ ] Update `docs/requirements/rtm.md` with new REQ-IDs for cache, partial-range fetch, and summary
- [ ] Ensure CR exists (CR-2026-02-11-007) and add a brief IA section (or link)
- [ ] Obtain ATP/approval token before code changes (CR-required)

### TDD
- [ ] RED: add failing tests for range subtraction + cache coverage decisions
- [ ] RED: add failing tests for service orchestration (cache hit / partial / miss)
- [ ] RED: add failing tests for parquet summary output
- [ ] GREEN: implement cache index + service wiring
- [ ] GREEN: implement summary generation
- [ ] REFACTOR: clean up; keep behavior stable

### Observability
- [ ] Structured logs for cache decision (`cache_hit`, `cache_miss`, `cache_partial`, `cache_write`, `cache_read_error`)
- [ ] Include key fields: `log_id`, `requested_from`, `requested_to`, `cached_ranges`, `missing_ranges`, `rows_reused`, `rows_fetched`

### Documentation
- [ ] RTM links updated to point at implementing code + test cases
- [ ] Runbook updated: cache location, retention, troubleshooting
- [ ] (If needed) update SLO doc for cache hit latency expectations

### Validation
- [ ] `pytest` passes
- [ ] Coverage meets policy (>=80%)
- [ ] Lint/format checks pass

---

## Progress Log

- 2026-02-11 00:00 UTC — Created CR-2026-02-11-007 draft and this implementation plan (DRAFT). Next: RTM updates + await ATP.
