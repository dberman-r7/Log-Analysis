# Change Requests Folder

This folder contains **Governed Change Requests (CRs)** only.

## When to create a CR
Create a CR **only** when the change:
- updates/modifies/deprecates requirements (RTM REQ-IDs), or
- is a major change in approach/architecture/security/performance, or
- introduces breaking behavior / large blast radius.

Routine bug fixes, clarifications, and low-risk refactors/features follow the **standard change path** (feature branch + PR) and do **not** need a CR.

> All changes — even no-CR changes — must be made via a **feature branch** and **Pull Request**.

See `docs/processes/change-management.md` for the full policy.

## File naming convention

- **Canonical record**: `CR-YYYY-MM-DD-XXX.md`
  - This is the durable record.
- Optional supporting artifacts (only if you really need to split):
  - `CR-YYYY-MM-DD-XXX-IMPACT-ASSESSMENT.md`
  - `CR-YYYY-MM-DD-XXX-IMPLEMENTATION-PLAN.md`

## Archive

Historical, superseded, or split-out CR artifacts should be moved into `_archive/`.

- `_archive/` must not be treated as active work-in-progress.
- Prefer keeping the canonical `CR-...md` in the top-level folder.
