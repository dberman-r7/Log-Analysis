# Impact Assessment: CR-2026-02-11-001

## 1) Code Impact
- **Files to modify**:
  - `src/log_ingestion/api_client.py` — align query polling/pagination to provider sample; improve 404 guidance and 429 handling where needed.
  - `src/log_ingestion/main.py` — ensure interactive log selection uses embedded `logs_info` (single `logsets` call), with fail-loudly guidance when missing.
  - `src/log_ingestion/config.py` — default to a writable output dir (`./data/logs`) and allow override via `OUTPUT_DIR`.
  - `src/log_ingestion/parquet_writer.py` — fail loudly with actionable guidance if output directory cannot be created/written.
  - `docs/requirements/rtm.md` — update traceability for query semantics + selection behavior + output defaults.
  - `README.md`, `docs/runbooks/log-ingestion-service.md` — align docs with supported invocation and defaults.
  - Tests: `tests/test_api_client.py`, selection tests, `tests/test_config.py`, possibly `tests/test_parquet_writer.py`.

- **Dependencies**: none expected.
- **API surface changes**: behavior correction in query execution; selection flow relies on embedded membership.
- **Breaking changes**: **NO** (signatures unchanged; behavior becomes more correct).

## 2) Security Impact
- Low risk.
- Ensure no secrets are logged; output directory path and log ids only.
- Rate-limit header parsing remains bounded to avoid untrusted long sleeps.

## 3) Performance Impact
- Net improvement: selection requires only one call (`/management/logsets`).
- Query will poll and paginate per provider spec; total calls depend on result size, but poll cadence remains bounded.

## 4) Testing Impact
- Add/adjust tests for:
  - polling to completion using `links[rel=Self]`.
  - pagination using `links[rel=Next]` across multiple pages.
  - 429 handling (`Retry-After` preferred; fallback `X-RateLimit-Reset`).
  - selection uses embedded `logs_info` only and errors clearly when missing.
  - default output dir behavior when OUTPUT_DIR absent.

## 5) Documentation Impact
- Update README + runbook:
  - clarify `python3 -m src.log_ingestion.main ...` usage.
  - document selection flow (log set -> log) and default output dir.
