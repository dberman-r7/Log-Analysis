# Implementation Plan: CR-2026-02-11-002

## Pre-Implementation Tasks
- [x] Requirement decomposition completed
- [ ] Update RTM with new REQ-IDs for epoch-millis conversion and enhanced 429 handling
- [ ] Confirm no ADR needed (expected: no architectural boundary changes)

## Implementation Tasks (TDD)
- [ ] **RED**: Add service test that asserts ISO8601 inputs are converted to epoch-millis before calling `Rapid7ApiClient.fetch_logs()`.
- [ ] **RED**: Extend API client tests to cover:
  - `Self` polling until completion
  - `Next` pagination traversal
  - 429 handling preferring `Retry-After` over `X-RateLimit-Reset`
  - invalid/missing reset header behavior (bounded default)
- [ ] **GREEN**: Implement ISO8601 -> epoch-millis conversion in `LogIngestionService.run()`.
- [ ] **GREEN**: Update `Rapid7ApiClient.fetch_logs()` docstring + parameter expectations (epoch millis), and ensure params use the converted millis values.
- [ ] **GREEN**: Improve `_raise_rate_limited()` to support `Retry-After` and validate/reset bounds.
- [ ] **REFACTOR**: Keep polling/pagination logic readable and consistent with provider sample; ensure logs remain structured.

## Validation Tasks
- [ ] Unit tests pass
- [ ] Coverage = 80%
- [ ] Lint/typecheck passes (if configured)
- [ ] Docs are accurate (RTM updated)

## Files to Modify
- `docs/requirements/rtm.md` — add REQ entries and trace to code/tests
- `src/log_ingestion/service.py` — timestamp conversion boundary + logs
- `src/log_ingestion/api_client.py` — rate-limit header parsing + clarification
- `tests/test_service.py` — new conversion test
- `tests/test_api_client.py` — new/updated polling/pagination/rate-limit tests
