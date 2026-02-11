# Implementation Plan: CR-2026-02-10-006

## Pre-Implementation Tasks
- [x] Requirement decomposition completed (targets REQ-016..REQ-018; adds REQ-019)
- [ ] RTM updated with new REQ-019 and updated REQ-017 trace links
- [x] Security review performed (no new data exposure; ensure no secret logging)
- [x] Performance baseline established (remove 1–2 HTTP calls per selection)

## Implementation Tasks (TDD)
- [ ] **RED**: Update/add unit test asserting `list_logs_in_log_set()` fails loudly **without** attempting network calls.
- [ ] **GREEN**: Update `Rapid7ApiClient.list_logs_in_log_set()` to raise `ValueError` with actionable guidance without performing HTTP requests.
- [ ] **REFACTOR**: Ensure `main._run_log_selection()` uses only embedded `logs_info` and logs structured events for missing-logs failure.
- [ ] Add observability instrumentation (structured log events already present; add/adjust event names if needed).
- [ ] Update documentation (RTM; optional runbook note).

## Validation Tasks
- [ ] Unit tests pass (coverage ≥ 80%)
- [ ] Integration tests pass (N/A)
- [ ] Linter passes with zero warnings
- [ ] Security scan clean (no new vulnerabilities)
- [ ] Documentation reviewed for accuracy (RTM updated)

## Files to Modify
- `/docs/requirements/rtm.md` — add REQ-019; update REQ-016/017 test links and implementation mapping
- `/src/log_ingestion/api_client.py` — hard-fail `list_logs_in_log_set()` without HTTP calls
- `/tests/test_api_client_list_logs_in_log_set_fallback_404.py` — update to new contract

(Expect no changes required to `/src/log_ingestion/main.py`; it already uses embedded `logs_info`.)
