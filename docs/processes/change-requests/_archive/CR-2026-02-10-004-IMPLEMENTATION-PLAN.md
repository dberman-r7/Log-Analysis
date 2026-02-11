# Implementation Plan — CR-2026-02-10-004

## Checklist

### Pre-Implementation
- [x] Requirement decomposition completed (documentation-only)
- [ ] RTM updated (N/A — no requirement changes)
- [x] Security review performed (ensure secrets guidance remains)
- [x] Performance baseline established (N/A)

### Implementation
- [ ] Update `docs/runbooks/log-ingestion-service.md`:
  - [ ] Add/verify IntelliJ IDEA Run Configuration steps for running `src.log_ingestion.main`
  - [ ] Add/verify Run Configuration for `--select-log` utility
  - [ ] Add troubleshooting section:
    - [ ] `python` vs `python3` on macOS
    - [ ] urllib3 LibreSSL warning and recommended mitigations
    - [ ] 404 on `GET /management/logs` and how to confirm correct region/endpoint

### Validation
- [ ] Confirm documentation accuracy against current CLI flags and env vars
- [ ] Run unit tests (smoke) to ensure no accidental code changes

## Files to Modify
- `docs/runbooks/log-ingestion-service.md` — add IDE execution instructions + troubleshooting.
