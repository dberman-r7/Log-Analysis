# IP-2026-02-18-001: End-of-run observability, parquet summaries, and reconciliation

**Status**: IN_PROGRESS  
**Created**: 2026-02-18  
**Last Updated**: 2026-02-18

## Quick Impact Assessment (QIA)
- **Functional change?** NO — additive metrics/logging + summary output; no API/CLI contract changes intended.
- **Touches any CR-required triggers?** NO — no security/architecture/breaking changes; low blast radius.
- **CR required?** NO — performance/observability enhancement; backwards-compatible.

## Requirements / Traceability
Assumption: enhancements map to existing requirements (no new REQ needed).
- **REQ-010 [NFR-OBS]**: End-of-run structured logging and summary.
- **REQ-026 [NFR-OBS]**: Cache/segment observability.
- **REQ-027 [FUNC/NFR-OBS]**: Parquet summary output (schema/aggregates).
- **REQ-028 [NFR-PERF]**: Streaming + bounded memory (flush-by-rows) behavior.
- **REQ-011 [NFR-PERF]**: Keep overhead minimal.

(We’ll confirm exact REQ IDs in `docs/requirements/rtm.md` and adjust references if needed.)

## Technical Design
### Goal
Improve the end-of-run output so we can reconcile:
- what the API returned (raw events),
- what we wrote (unique/processed rows),
- what was dropped (duplicates),
- and what landed on disk (parquet parts + bytes, plus dataset summary).

### Proposed “run summary” contract (returned result + logs)
Add/ensure these **result dict keys** are populated consistently:
- `raw_events_seen` (int)
- `rows_processed` (int, unique rows written)
- `duplicates_dropped` (int)
- `dedupe_enabled` (bool)
- `observed_min_ts_ms` (int|None)
- `observed_max_ts_ms` (int|None)
- `parquet_parts_written` (int)
- `parquet_total_bytes_written` (int)
- `parquet_part_bytes_min` (int|None)
- `parquet_part_bytes_max` (int|None)

And emit a single end-of-run structured log event, e.g. `run_summary`, containing:
- requested window (start/end)
- observed window (min/max timestamps)
- reconciliation tuple (raw/unique/dupes)
- parquet write metrics (parts, bytes)
- parquet dataset summary (rows/columns)

### Parquet dataset summary
Prefer a lightweight summary from parquet metadata when possible (avoid loading full dataset).
Fallback to safe minimal reads if metadata stats aren’t available.

### Failure behavior (“fail loudly”)
If summary generation fails:
- emit an ERROR structured log with `dataset_path` and exception.
- if the dataset exists but can’t be summarized because it’s corrupt, fail the run (raise).

## Implementation Checklist
- [ ] Confirm REQ IDs in RTM and update traceability lines.
- [ ] RED: tests for end-of-run result keys and end-of-run structured log.
- [ ] GREEN: implement end-of-run metrics aggregation (service).
- [ ] GREEN: implement parquet dataset summary aggregation.
- [ ] REFACTOR: keep result/log construction DRY.
- [ ] Update RTM (Implemented In / Test Coverage).
- [ ] Quality gates: unit tests + coverage ≥ 80%.

## Progress Log
- **2026-02-18**: Draft plan created; ready to implement end-of-run summary metrics + tests.
