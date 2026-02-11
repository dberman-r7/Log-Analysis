# Impact Assessment: CR-2026-02-11-002

## 1) Code Impact

### Files to modify
- `src/log_ingestion/service.py`
  - Convert ISO8601 timestamps to epoch-millis before calling `Rapid7ApiClient.fetch_logs()`.
  - Add structured logs that include both formats.
- `src/log_ingestion/api_client.py`
  - Ensure query params use epoch-millis.
  - Ensure link-based polling uses `Self` until completion.
  - Ensure pagination follows `Next` links until exhaustion.
  - Improve 429 handling to support `Retry-After` (when present) and validate reset values.
- `tests/test_service.py`
  - Add a unit test asserting epoch-millis conversion.
- `tests/test_api_client.py`
  - Update tests so `fetch_logs()` is clearly passed epoch-millis and verify link-based polling/pagination behavior.
  - Add tests for `Retry-After` preference and invalid/missing reset headers.
- `docs/requirements/rtm.md`
  - Add new REQ(s) for ISO8601->epoch-millis conversion and for 429 header handling upgrades.

### Dependencies
- No new external dependencies required (use stdlib `datetime`).

### API surface changes
- Internal contract change: `Rapid7ApiClient.fetch_logs()` will require epoch-millis values (as strings or ints). The CLI will remain ISO8601.

### Breaking changes
- **NO** user-facing breaking changes (CLI still ISO8601).
- Potentially breaking for internal callers of `Rapid7ApiClient.fetch_logs()` (only used by `LogIngestionService` in this repo).

## 2) Security Impact
- Low.
- Ensure API keys remain in headers only and never logged.
- Ensure logged timestamps do not include sensitive data.

## 3) Performance Impact
- Minor improvement potential: fewer failed calls and faster time-to-first-success.
- Additional time conversion is negligible.

## 4) Testing Impact
- Add unit tests in `tests/test_service.py` and expand `tests/test_api_client.py`.
- Existing tests should remain fast (no real sleeps; patch `time.sleep`).

## 5) Documentation Impact
- RTM must be updated.
- Optional: clarify timestamp formats in README/runbook (if present) to prevent operator confusion.
