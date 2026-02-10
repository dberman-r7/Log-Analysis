# Implementation Plan: CR-2026-02-10-002

**Change Request**: CR-2026-02-10-002  
**Plan Version**: 1.0  
**Created**: 2026-02-10  

---

## 0. Contract (what “done” means)

**Input**:
- Start/end time range
- Provider configuration: `region`, `log_key`, optional `query`

**Output**:
- A complete set of results across all pages, fetched via provider `links` semantics.

**Error modes**:
- 401/403: fail fast with loud logging
- 429: sleep per `X-RateLimit-Reset` then retry
- Invalid body: raise descriptive exception

---

## 1. Pre-Implementation Tasks

- [ ] Add atomic requirements to RTM for Log Search polling + pagination + 429 reset
- [ ] Decide on backward compatibility approach:
  - Option A: add `rapid7_api_mode` config (`export` vs `logsearch`) and branch behavior
  - Option B: replace behavior to “just provider’s” Log Search semantics

> Assumption for this plan: user requested **“just the providers”** → proceed with **Option B** (replace behavior).

---

## 2. Implementation Tasks (TDD)

### 2.1 RED – Write failing tests

- [ ] `test_api_client_constructs_auth_header_logsearch()`
  - expects `x-api-key` header (and not `Authorization: Bearer`)

- [ ] `test_api_client_polls_self_until_complete()`
  - initial response includes `links: [{rel: Self, href: ...}]` then completion response without Self

- [ ] `test_api_client_follows_next_page_links()`
  - first completed page includes `Next` link; client fetches it and accumulates results

- [ ] `test_api_client_429_uses_x_ratelimit_reset()`
  - 429 response should sleep reset seconds and retry

### 2.2 GREEN – Implement minimum code

- [ ] Implement helpers in `Rapid7ApiClient`:
  - `is_query_in_progress(resp)`
  - `_poll_request_to_completion(resp)` with exponential backoff 0.5s → 6s
  - `_has_next_page(resp)` and `_get_next_page(resp)`

- [ ] Implement `fetch_logs(start_time, end_time)` to:
  - submit initial query
  - poll to completion
  - iterate pages
  - return a serialized representation compatible with downstream parsing (initially JSON pretty string or raw JSON text; adjust once confirmed by provider)

### 2.3 REFACTOR

- [ ] Consolidate duplicated 429 handling
- [ ] Ensure logs are structured and do not leak secrets

---

## 3. Observability Tasks

- [ ] Emit logs:
  - `logsearch_query_submitted` (region, log_key, from/to)
  - `logsearch_poll` (attempt, delay_seconds)
  - `logsearch_page_fetched` (page_index)
  - `logsearch_rate_limited` (secs_until_reset)
  - `logsearch_complete` (pages, duration)

---

## 4. Validation Tasks

- [ ] Unit tests pass
- [ ] Coverage remains ≥ 80%
- [ ] Lint/typecheck passes

---

## 5. Files to Modify

- `src/log_ingestion/api_client.py` — implement provider semantics
- `src/log_ingestion/config.py` — add provider-specific config
- `tests/test_api_client.py` — add tests
- `docs/requirements/rtm.md` — update traceability
