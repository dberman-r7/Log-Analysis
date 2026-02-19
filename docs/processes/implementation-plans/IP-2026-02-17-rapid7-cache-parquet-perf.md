# Implementation Plan: IP-2026-02-17-001 Rapid7 polling + cache/parquet performance & instrumentation

**Status**: IN_PROGRESS

**Created**: 2026-02-17 00:00:00 UTC  
**Last Updated**: 2026-02-17 00:00:00 UTC

## Ownership & Links

- **Owner / Agent**: Copilot
- **Branch**: perf/rapid7-polling-cache-instrumentation
- **PR**: TBD
- **Related CR (if any)**: None (QIA: Standard Change)
- **Related REQ(s)**: REQ-013, REQ-014, REQ-015, REQ-023, REQ-024, REQ-026, REQ-027, REQ-028

---

## Quick Impact Assessment (QIA)

- **Functional change?** NO (no CLI/API semantics change; same cache/parquet contents; additional logs only)
- **Touches CR-required triggers?** NO (no breaking change, no new deps, no architecture change)
- **CR required?** NO — performance/observability enhancement with low blast radius

### Scope Summary
- **Files expected to change**:
  - [ ] `src/log_ingestion/api_client.py`
  - [ ] `src/log_ingestion/service.py`
  - [ ] `src/log_ingestion/parquet_writer.py`
  - [ ] `tests/test_api_client_progress_observability.py`
  - [ ] `tests/test_service_streaming.py`
  - [ ] `docs/runbooks/log-ingestion-service.md`
  - [ ] `docs/requirements/rtm.md` (only if new REQs are required)

---

## Problem Statement (performance reconciliation)

Observed runtime symptom: a small manual window shows ~402 log lines, but the pipeline retrieved and wrote ~18,957 events for the same 10s window.

This plan focuses on:
- making it *measurable* why the API client returns many events (pagination semantics, timestamp overlaps, ingestion vs event time)
- eliminating avoidable overhead (redundant JSON parsing / heavy log payloads)
- adding instrumentation around parquet flushing so we can see CPU/wall time split

---

## Technical Design (targeted, low-risk)

### A) API client polling/pagination instrumentation hardening

**Files**: `src/log_ingestion/api_client.py`

1) Avoid redundant JSON parsing in `_poll_request_to_completion()`
- Parse `resp.json()` at most once per poll iteration and reuse the parsed object for:
  - in-progress decision
  - summary fields
  - event counts

2) Reduce heavy INFO logging
- Ensure `body_preview` is DEBUG-only.
- Keep INFO logs compact: counts, keys, link rels, elapsed_seconds, status_code.

3) Add “progress correctness” signals to reconcile event counts
- Per page emit:
  - `page_min_event_timestamp` / `page_max_event_timestamp`
  - requested window
  - derived `next_from_millis`
  - `events_total` counter
- Emit a warning when the page max timestamp is not advancing while pagination continues.

### B) Cache/parquet write instrumentation

**Files**: `src/log_ingestion/service.py`, `src/log_ingestion/parquet_writer.py`

1) Flush timing breakdown
- During `flush_start/flush_complete`, add:
  - `dataframe_build_ms`
  - `parquet_write_ms`
  - `flush_total_ms`

2) Ensure cache path never uses quadratic append
- Cache segment path should continue writing `part-*.parquet` and must not call `ParquetWriter.write(... append=True)`.
- Add a small defensive trace log in `write_part()` path to confirm part write mode.

### C) Runbook update

**File**: `docs/runbooks/log-ingestion-service.md`

Add a short section:
- what the key perf events mean (`logsearch_page_complete`, `flush_complete`, `parquet_part_write_success`)
- how to reconcile API “event_count” vs expectations (ingestion timestamps vs event timestamps; pagination overlap avoidance)

---

## Implementation Checklist

### Pre-implementation
- [x] Requirement traceability confirmed (existing REQs cover perf + streaming; new REQ not required for additive instrumentation)
- [x] Implementation plan created

### TDD (code changes)
- [ ] RED: add tests for (a) no redundant `.json()` calls in polling loop, (b) flush timing fields present
- [ ] GREEN: implement minimal code changes
- [ ] REFACTOR: clean up logging fields and reduce duplication

### Observability
- [ ] Logs updated with timing fields; INFO payload remains small
- [ ] Fail loudly remains intact

### Documentation
- [ ] Runbook updated
- [ ] RTM updated only if we introduce new REQ-IDs

### Validation
- [ ] Unit tests pass; coverage ≥ 80%

---

## Progress Log

- 2026-02-17 00:00 UTC — Started. QIA: Standard change (no CR). Plan drafted; hotspots identified in polling loop JSON parsing and flush/write timing.

---

## Restart / Continue Instructions

On any restart/continue:
1. Open this file.
2. Resume from the first unchecked item.
3. Update the checklist and Progress Log as you complete steps.
