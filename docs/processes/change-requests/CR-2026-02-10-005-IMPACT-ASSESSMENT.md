# Impact Assessment — CR-2026-02-10-005

**CR ID**: CR-2026-02-10-005  
**Date**: 2026-02-10  

## 1) Code Impact

- **Files to modify**:
  - `src/log_ingestion/api_client.py` — add API methods to list log sets and list logs within a log set.
  - `src/log_ingestion/log_selection.py` — add dataclasses + selection helpers for log sets and logs.
  - `src/log_ingestion/main.py` — update interactive `--select-log` flow to: list log sets → choose → list logs → choose → persist.
  - `tests/test_api_client.py` — add tests for new API client methods.
  - `tests/` (new test file likely `tests/test_log_selection.py`) — unit tests for selection helpers.
  - `docs/requirements/rtm.md` — add new REQ IDs for log set selection.
  - `docs/runbooks/log-ingestion-service.md` — refresh usage docs.

- **Dependencies affected**: None expected (reuse `requests`, `structlog`).
- **API surface changes**:
  - New public methods on `Rapid7ApiClient`.
  - New dataclasses in `log_selection.py`.
- **Breaking changes**: **NO**. Existing `--select-log` remains, but prompt sequence changes.

## 2) Security Impact

- No auth/authz changes; continues to use `x-api-key` header.
- Ensure **no secret values** are logged or printed.
- Input validation: interactive selection must validate index/id and fail loudly.
- No new secret management implications.

## 3) Performance Impact

- Minimal: two small management API calls during interactive selection.
- No ingestion-path performance change.

## 4) Testing Impact

- Add unit tests for:
  - API client: list log sets, list logs within log set, unexpected response shapes.
  - Selection helpers: choosing by index and id, out-of-range and empty input.
  - CLI helper: can be tested via monkeypatching input + mocking API calls (optional).

## 5) Documentation Impact

- RTM: add/extend requirements for selecting log sets and logs.
- Runbook: update `--select-log` section to reflect new prompts.
- No ADR expected (no architectural boundary changes).
