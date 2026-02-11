# Implementation Plan — CR-2026-02-10-005

## Checklist

### Pre-Implementation
- [x] Requirement decomposition completed
- [ ] RTM updated with new REQ-IDs (log set + log selection)
- [x] Security review performed (no secrets; validate user input)
- [x] Performance baseline established (N/A — interactive utility)

### Implementation (TDD)
- [ ] **RTM**: Add requirements for log set listing + selection flow.
- [ ] **RED**: Add failing tests:
  - [ ] `Rapid7ApiClient.list_log_sets()`
  - [ ] `Rapid7ApiClient.list_logs_in_log_set(log_set_id)`
  - [ ] Selection helper for log set selection
- [ ] **GREEN**: Implement:
  - [ ] New dataclasses: `LogSetDescriptor`, (reuse) `LogDescriptor`
  - [ ] New selection helper `choose_log_set_id()` (index or id)
  - [ ] API client methods to call management endpoints and validate response shapes
  - [ ] Update CLI selection flow in `main._run_log_selection()`
- [ ] **REFACTOR**: Consolidate shared selection logic; improve error messaging.
- [ ] Add structured logs for each step (start/complete/fail).
- [ ] Update runbook documentation.

### Validation
- [ ] Unit tests pass
- [ ] Lint/typecheck pass (if configured)
- [ ] Governance: RTM updated because `src/` changes

## Files to Modify
- `docs/requirements/rtm.md` — add REQ entries for log set selection.
- `src/log_ingestion/api_client.py` — add two management API methods.
- `src/log_ingestion/log_selection.py` — add log set descriptor + chooser.
- `src/log_ingestion/main.py` — implement new interactive flow.
- `tests/test_api_client.py` — add tests for new API calls.
- `tests/test_log_selection.py` — new tests for chooser.
- `docs/runbooks/log-ingestion-service.md` — update usage.
