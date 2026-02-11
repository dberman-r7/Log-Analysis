# Implementation Plan: CR-2026-02-11-001

## Pre-Implementation Tasks
- [x] Requirement decomposition completed (adds REQ-020..REQ-022)
- [ ] RTM updated with REQ-020..REQ-022 and trace links
- [ ] Confirm no architectural change requiring new ADR (expected: none)

## Implementation Tasks (TDD)
- [ ] **RED**: Add failing tests for default output directory behavior when `OUTPUT_DIR` is not set
- [ ] **RED**: Add failing test for direct-script execution guard (actionable error message)
- [ ] **GREEN**: Implement default `output_dir` in `LogIngestionConfig`
- [ ] **GREEN**: Improve `ParquetWriter` init to raise a clear exception when directory creation fails
- [ ] **GREEN**: Add `main.py` guard to fail loudly when executed as a script (relative import context)
- [ ] **REFACTOR**: Keep logging structured and consistent; ensure no secrets are logged
- [ ] Update docs (README + runbook)

## Validation Tasks
- [ ] Unit tests pass (coverage ≥ 80%)
- [ ] Linter passes with zero warnings
- [ ] No new dependency vulnerabilities
- [ ] Documentation reviewed for accuracy (RTM + runbook/README)

## Files to Modify
- `docs/requirements/rtm.md` — add REQ-020..REQ-022; trace to implementation/tests
- `src/log_ingestion/config.py` — default output dir and make OUTPUT_DIR optional
- `src/log_ingestion/parquet_writer.py` — fail-loudly on directory creation errors
- `src/log_ingestion/main.py` — script-execution guard + updated help text
- `README.md`, `docs/runbooks/log-ingestion-service.md` — usage + config updates
- `tests/test_config.py`, `tests/test_main.py` (or new test file), `tests/test_parquet_writer.py`
