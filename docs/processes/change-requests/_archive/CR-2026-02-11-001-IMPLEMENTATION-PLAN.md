# Implementation Plan: CR-2026-02-11-001

## Pre-Implementation Tasks
- [x] Requirement decomposition completed (REQ-013..REQ-019, REQ-020..REQ-024 already exist in RTM)
- [ ] Update RTM if any requirement wording/trace links need adjustment for provider sample parity
- [ ] Confirm no architectural change requiring new ADR (expected: none)

## Implementation Tasks (TDD)
### A) Query polling + pagination (provider sample parity)
- [ ] **RED**: Add failing tests for polling-to-completion via `links[rel=Self]`
- [ ] **RED**: Add failing tests for pagination via `links[rel=Next]` (multi-page)
- [ ] **RED**: Add failing tests for 429 handling using `Retry-After` then `X-RateLimit-Reset` (bounded)
- [ ] **GREEN**: Implement minimal changes in `src/log_ingestion/api_client.py`
- [ ] **REFACTOR**: Keep structured logs; improve 404 guidance; keep helpers small

### B) Interactive log selection (single management call)
- [ ] **RED**: Add/adjust tests that selection uses embedded `logs_info` only
- [ ] **GREEN**: Ensure `main._run_log_selection()` uses `LogSetDescriptor.logs` from `list_log_sets()`
- [ ] **REFACTOR**: Improve fail-loudly messaging when embedded membership is missing

### C) macOS-friendly defaults + CLI ergonomics
- [ ] **RED**: Add failing tests for default output directory behavior when `OUTPUT_DIR` is not set
- [ ] **RED**: Add failing test for direct-script execution guard (actionable error)
- [ ] **GREEN**: Ensure default `output_dir` in `LogIngestionConfig` remains `./data/logs`
- [ ] **GREEN**: Ensure `ParquetWriter` fails loudly when directory creation fails
- [ ] **GREEN**: Ensure CLI docs/help mention `python3 -m ...`

### D) Docs
- [ ] Update README + runbook to prevent drift

## Validation Tasks
- [ ] Unit tests pass (coverage ≥ 80%)
- [ ] Linter passes with zero warnings
- [ ] No new dependency vulnerabilities
- [ ] Documentation reviewed for accuracy (RTM + runbook/README)

## Files to Modify
- `src/log_ingestion/api_client.py` — polling/pagination/429 + guidance
- `src/log_ingestion/main.py` — selection flow + module exec guard text
- `src/log_ingestion/config.py` — confirm default output dir
- `src/log_ingestion/parquet_writer.py` — fail-loudly behavior
- `README.md`, `docs/runbooks/log-ingestion-service.md` — usage + config updates
- `tests/test_api_client.py` and selection/config tests
