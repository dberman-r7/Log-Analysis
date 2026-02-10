# Impact Assessment: CR-2026-02-10-006

## 1) Code Impact
- **Files to modify**:
  - `/src/log_ingestion/main.py`: ensure log selection lists logs using embedded `logs_info` from `list_log_sets()` and never calls per-logset membership endpoints.
  - `/src/log_ingestion/api_client.py`: change `list_logs_in_log_set()` to fail loudly without making HTTP calls (or deprecate it) because membership endpoints are unsupported in target env.
  - `/tests/test_api_client_list_logs_in_log_set_fallback_404.py`: update test to match the new “no network calls; fail loudly” behavior.
  - `/docs/requirements/rtm.md`: add/modify requirements, update trace links.

- **Dependencies affected**: None.
- **API surface changes**: `Rapid7ApiClient.list_logs_in_log_set()` behavior changes to raise a clear error without attempting HTTP.
- **Breaking changes**: NO for internal CLI flow; POSSIBLE for any third-party callers using `list_logs_in_log_set()` (repo-local usage appears test-only).

## 2) Security Impact
- No auth/authz changes.
- Reduced external calls slightly reduces metadata exposure.
- Ensure errors/logs do not include API secrets; keep structured logs.

## 3) Performance Impact
- Removes 1–2 API calls per selection and avoids retry/exception overhead.
- Improves interactive selection latency and reduces rate-limit usage.

## 4) Testing Impact
- Update unit tests to:
  - Verify `list_log_sets()` continues parsing embedded `logs_info`.
  - Verify selection flow works without any membership endpoint calls.
  - Verify `list_logs_in_log_set()` fails loudly with actionable guidance and makes no HTTP calls.

## 5) Documentation Impact
- RTM update required (new/updated requirement around embedded logs + forbidding membership endpoints).
- No ADR or diagrams expected (no architectural boundary change).
