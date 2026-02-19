# Implementation Plan: Pagination correctness + per_page plumbing + event-volume reconciliation

**Date**: 2026-02-17  
**Owner**: AI (with user)  
**Change Type**: Standard Change (no CR)

## Quick Impact Assessment (QIA)
- **Functional change?** YES
  - Pagination behavior and request parameters are externally observable (events returned and runtime).
- **Touches any CR-required triggers?** NO
  - No requirements change, no architecture change, no breaking interface changes; correction/bugfix + performance/observability improvements.
- **CR required?** NO
  - Low-risk, backward-compatible bugfix/perf + instrumentation; user explicitly approved no-CR path.

## Problem Statement
We’re seeing:
- Extremely high event counts for narrow windows vs manual expectations (e.g., 18,957 events for 10 seconds vs expected ~402).
- Evidence pagination “advances” via tiny timestamp increments and returns many pages.
- End-of-run output doesn’t clearly reconcile: requested window vs observed event timestamps, expected vs raw vs written, parquet bytes/parts.

We need to:
1) Ensure pagination relies strictly on provider `links[rel=Next]` (no “from boundary” mutation).
2) Ensure `per_page` config is actually sent and honored by the request.
3) Add targeted instrumentation to diagnose and reconcile why event volumes are higher than expected.
4) Improve end-of-run structured summary so we can tell exactly what was fetched, deduped, written, and cached.

## Current Hypotheses (to validate)
- Manual count is from a different UI query context (filters, log set vs log, time zones, ingestion vs event time).
- API returns multiple events per displayed line (e.g., structured events, multi-line stack traces, internal metrics lines).
- Window semantics: API may interpret `during.from` inclusive and `to` exclusive; our client may be requesting larger span than intended.
- Duplication: pages overlap at the timestamp boundary; if we don’t de-dup by (log_id, sequence_number_str) we may count duplicates.

## Technical Design (target behavior)
### Pagination
- Treat each *completed* page as authoritative.
- If `links.Next` exists:
  - Fetch that URL.
  - Poll its `links.Self` until complete.
  - Repeat.
- Never mutate the `Next` url.
- Safety: detect repeated `Next` URL and fail loudly.

### Request sizing (`per_page`)
- Add `per_page=<config>` to the **initial** query request params.
- Do not attempt to add/override `per_page` on `Next` URLs (provider controls that).
- Instrument the effective `per_page` at query submit.

### Reconciliation instrumentation
Add INFO logs:
- `page_min_event_timestamp`, `page_max_event_timestamp` and ISO conversions (already present).
- `unique_event_keys_in_page` sample count (or at least detect duplicates by sequence_number_str within page).
- `distinct_sequence_numbers_total` and `duplicate_sequence_numbers_total` (bounded memory: use small bloom-like set per page only, plus optional full run when configured).

### End-of-run reconciliation summary (new)
Emit one final structured INFO event (and return additional metrics in the result dict) with:
- Requested window (ISO + millis)
- Observed min/max event timestamps (from stream, no parquet re-read)
- API totals: pages, events_raw_total (sum of `len(events)`), optional provider `events_total` if present
- Dedupe totals (raw_seen, duplicates_dropped, unique_written)
- Parquet output totals: parts_written, total_bytes_written, bytes_min/max per part
- Cache decision + segments used/reused

If provider `events_total` is present and differs materially from what we saw/wrote, emit a WARN `run_event_count_reconciliation` with a compact diagnostic blob.

## Requirements Traceability
No new REQ IDs proposed (bugfix/perf/obs under existing ingestion/client requirements).
If we discover missing explicit REQ around pagination de-dup or count semantics, we’ll propose a new REQ and update RTM.

## Work Checklist
- [ ] Inspect current `Rapid7ApiClient.fetch_logs()` pagination loop and confirm it solely follows `Next`.
- [ ] Verify `per_page` is included in the initial request and is configurable.
- [x] Add minimal instrumentation / guardrails to detect page overlap/duplicates.
- [x] Implement configurable de-duplication of events (DEDUPE_EVENTS) by (log_id, sequence_number).
- [x] Add/adjust tests to lock in dedupe behavior.
- [ ] Add end-of-run summary + reconciliation diagnostics (structured logs + return metrics).
- [ ] Add/adjust tests to validate summary metrics and reconciliation logging.
- [ ] Run unit test suite and ensure coverage >= 80%.
- [ ] Update docs/runbook with new summary fields/events.

## Progress Log
- 2026-02-17: Plan created.
- 2026-02-17: Implemented configurable event de-dupe (DEDUPE_EVENTS), added streaming tests, and confirmed `python3 -m pytest` passes (127/127) with coverage 80.21%.
- 2026-02-17: (next) Add end-of-run summary + reconciliation diagnostics to help explain high event totals vs manual expectations.
