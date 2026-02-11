# Impact Assessment: CR-2026-02-11-001

## 1) Code Impact
- **Files to modify**:
  - `src/log_ingestion/config.py` — make `OUTPUT_DIR` optional; default to a writable directory.
  - `src/log_ingestion/parquet_writer.py` — fail loudly with actionable guidance if output directory cannot be created.
  - `src/log_ingestion/main.py` — update usage/help text and add a guard for direct script execution to prevent confusing relative-import errors.
  - `docs/requirements/rtm.md` — add/update requirements covering output directory defaults and CLI module execution.
  - `README.md`, `docs/runbooks/log-ingestion-service.md` — align docs with supported invocation and new defaults.
  - Tests: `tests/test_config.py`, `tests/test_main.py` (or new test), possibly `tests/test_parquet_writer.py`.

- **Dependencies**: none expected.
- **API surface changes**: configuration behavior change (OUTPUT_DIR no longer required).
- **Breaking changes**: **NO** (existing OUTPUT_DIR overrides remain valid).

## 2) Security Impact
- Low risk.
- Ensure no secrets are logged; output directory path only.
- Default output directory should be local to the project (or user-home) to avoid unexpected writes to privileged/unsafe locations.

## 3) Performance Impact
- Negligible.

## 4) Testing Impact
- Add tests for:
  - default output dir selection when OUTPUT_DIR is absent.
  - clear failure behavior when output dir cannot be created.
  - module execution guard / actionable error on direct `python src/log_ingestion/main.py`.

## 5) Documentation Impact
- Update README + runbook:
  - clarify `python -m src.log_ingestion.main ...` usage.
  - document default output dir and `OUTPUT_DIR` override.
