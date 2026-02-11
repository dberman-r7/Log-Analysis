# Impact Assessment: CR-2026-02-10-002

**Change Request**: CR-2026-02-10-002 - Align API client with provider Log Search polling + link pagination  
**Assessment Date**: 2026-02-10  
**Assessed By**: Automated agent

---

## 1. Code Impact

### Files to Create/Modify/Delete

**Create**:
- None (expected)

**Modify**:
- `src/log_ingestion/api_client.py` — implement provider Log Search flow (polling, link pagination, rate-limit reset handling)
- `src/log_ingestion/config.py` — add required provider configuration fields (region, log key, query)
- `tests/test_api_client.py` — add/adjust tests for new behaviors
- `docs/requirements/rtm.md` — add atomic requirements + trace links

**Delete**:
- None

### Dependencies affected
- No new third-party dependencies expected (continue using `requests`)

### API surface changes
- Internal API behavior changes in `Rapid7ApiClient.fetch_logs()`.
- Breaking changes: **POTENTIAL YES** if existing workflow relies on `/logs` endpoint + Bearer auth.

**Mitigation** (recommended): introduce a config switch for API mode, or create a separate `fetch_logs_logsearch()` method and keep `fetch_logs()` stable.

---

## 2. Security Impact

- Authentication header changes from Bearer token to `x-api-key` (per provider).
- Must ensure structured logs never include the API key.
- Secrets remain sourced from environment variables (aligns with REQ-009).

Compliance considerations:
- No new data types introduced; still log data.

Risk: **Low–Medium** (integration correctness + secret handling).

---

## 3. Performance Impact

- Polling increases number of HTTP requests; bounded exponential backoff mitigates excessive calls.
- Need to ensure polling intervals respect provider constraint that continuation links expire after ~10 seconds.

Expected impact: **Neutral to Moderate overhead**, acceptable for ingestion use.

---

## 4. Testing Impact

New unit tests required:
- Polling until completion using `links[rel=Self]`
- Pagination using `links[rel=Next]`
- HTTP 429 handling using `X-RateLimit-Reset`
- Defensive handling of invalid/missing `links` shapes

---

## 5. Documentation Impact

- RTM must be updated with new atomic requirements for Log Search support.
- Optional: add/expand SLOs for query completion time and error rate.

---

## Summary

**Blast radius**: Medium (core API client logic)  
**Breaking change risk**: Medium unless mitigated via config/mode separation  
**Security risk**: Low–Medium  
**Performance risk**: Low–Medium  
**Test impact**: Medium
