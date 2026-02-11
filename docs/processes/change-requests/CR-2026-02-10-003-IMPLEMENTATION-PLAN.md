# Implementation Plan: CR-2026-02-10-003
**Change Request**: CR-2026-02-10-003  
**Date**: 2026-02-10

## Checklist

### Pre-Implementation
- [x] Requirement decomposition completed (adds/extends REQ entries in RTM)
- [x] Security review performed (no secrets logged; .env update minimal)
- [ ] Performance baseline established (N/A; single call utility)

### Implementation (TDD)
- [x] RED: add unit tests for log selection flow (`tests/test_main_select_log.py`)
- [x] GREEN: implement `Rapid7ApiClient.list_logs()` parsing + network behavior
- [x] GREEN: implement selection helper `choose_log_id()`
- [x] GREEN: implement `.env` upsert helper `upsert_env_var()`
- [x] GREEN: wire CLI flag `--select-log` in `src/log_ingestion/main.py`
- [x] REFACTOR: keep logic testable; avoid subprocess-based tests
- [x] Observability: structured log events for request + selection + update

### Validation
- [ ] Unit tests pass (coverage ≥ 80%)
- [ ] Linter/typecheck clean (repo defaults)
- [ ] Documentation updated and accurate

### Files to Modify
- `src/log_ingestion/api_client.py`: add `list_logs()` method.
- `src/log_ingestion/main.py`: add `--select-log` and `.env` update path.
- `docs/runbooks/log-ingestion-service.md`: document new flow.
- `docs/requirements/rtm.md`: update traceability for new/changed behaviors.
- `tests/`: add/ensure unit tests for selection flow.

