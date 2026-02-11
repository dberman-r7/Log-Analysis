# Change Requests Folder

This folder contains **Governed Change Requests (CRs)** only.

## When to create a CR
Create a CR **only** when the change:
- updates/deprecates requirements (RTM REQ-IDs), or
- is a major approach/architecture/security/performance change, or
- introduces breaking behavior / large blast radius.

Routine bug fixes, clarifications, and low-risk refactors/features follow the **standard change path** (feature branch + PR) and do **not** need a CR.

See `docs/processes/change-management.md` for the full policy.

## File naming convention

- **Canonical record**: `CR-YYYY-MM-DD-XXX.md`
- Optional supporting artifacts (if you really need to split):
  - `CR-YYYY-MM-DD-XXX-IMPACT-ASSESSMENT.md`
  - `CR-YYYY-MM-DD-XXX-IMPLEMENTATION-PLAN.md`

## Archive

Historical or superseded CR artifacts may be moved into the `_archive/` subfolder.
