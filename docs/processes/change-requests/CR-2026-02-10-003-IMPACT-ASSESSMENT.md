# Impact Assessment: CR-2026-02-10-003
**Change Request**: CR-2026-02-10-003  
**Date**: 2026-02-10
---
## 1) Code Impact
- **Files to modify**:
  - `src/log_ingestion/api_client.py`: add `list_logs()` for `GET /management/logs`.
  - `src/log_ingestion/main.py`: add a CLI mode to list logs and prompt for selection; update `.env`.
  - `docs/runbooks/log-ingestion-service.md`: document usage.
- **Files to create**:
  - `src/log_ingestion/env_utils.py`: safe `.env` read/update helper.
  - `tests/test_env_utils.py`: unit tests for `.env` updates.
  - `tests/test_log_selection.py`: unit tests for selection helper.
- **Dependencies**: No new third-party dependencies planned.
- **API surface changes**:
  - `Rapid7ApiClient` gains `list_logs()`.
  - CLI gains a new option (non-breaking).
- **Breaking changes**: **NO**.
## 2) Security Impact
- Uses existing `RAPID7_API_KEY`; do not log it.
- `.env` update concerns:
  - Update only `RAPID7_LOG_KEY` and preserve the rest.
  - Don't print `.env` contents in logs.
- No authn/authz model changes.
## 3) Performance Impact
- Listing logs is a single API call; negligible overhe- Li- No ingestion- Listing logs is ## 4) Testing Impact
- Unit tests for:
  - `.env` update/insert semantics.
  - `Rapid7ApiClient.list_logs()` response parsing + error handling.
  - selection parsing without interactive prompts.
## 5) Documentation Impact
- Runbook updates:
  - How to li  - How to li  -  - Example `.env` after update.
  - Known failure modes and what logs to expect.
---
## Risk Summary
**Overall risk**: Low. Main risks are `.env` corruption and inadvertent secret logging.
