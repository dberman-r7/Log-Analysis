# Implementation Plan Requirements

> Requirements for creating and maintaining implementation plans.
> Template: #[[file:docs/processes/templates/implementation-plan-template.md]]

---

## When Implementation Plans Are Required

**ALWAYS REQUIRED** for code changes, typically:
- Changes to `src/` directory
- Changes to `tests/` directory
- Changes to dependency manifests (`requirements.txt`, `pyproject.toml`, `package.json`, etc.)

**NOT REQUIRED** for:
- Pure documentation updates (no code changes)
- README-only changes
- Comment-only changes

---

## Implementation Plan Location

- **Directory**: `docs/processes/implementation-plans/`
- **Naming**: `IP-YYYY-MM-DD-XXX-brief-description.md`
- **Template**: `docs/processes/templates/implementation-plan-template.md`

---

## Required Sections

Every implementation plan must include:

1. **Ownership & Links**
   - Owner/Agent name
   - Branch name
   - PR link (when created)
   - Related CR (if applicable)
   - Related REQ-IDs

2. **Quick Impact Assessment (QIA)**
   - Functional change? YES/NO
   - Touches CR-required triggers? YES/NO
   - CR required? YES/NO with rationale

3. **Implementation Checklist**
   - Pre-implementation items
   - TDD phases (if code changes)
   - Observability items
   - Documentation items
   - Validation items

4. **Progress Log**
   - Timestamped updates
   - Milestone completions
   - Status changes

5. **Restart/Continue Instructions**
   - How to resume work

---

## Progress Tracking (Mandatory for Agents)

### Maintain Visible Checklist
- Use `[ ]` for unchecked items
- Use `[x]` for completed items
- Keep checklist up-to-date

### Add Progress Log Entries
```markdown
## Progress Log

- 2026-02-19 10:00 UTC - Started. QIA complete; CR not required.
- 2026-02-19 10:30 UTC - Completed RED phase; 5 tests written and failing.
- 2026-02-19 11:00 UTC - GREEN phase complete; all tests passing.
- 2026-02-19 11:30 UTC - REFACTOR complete; coverage at 85%.
```

### Update Status Field
- DRAFT → IN_PROGRESS → BLOCKED → COMPLETE

---

## Restart / Continue Behavior (Agents)

**On "Continue" / restart / follow-up instruction:**

1. Open the active implementation plan
2. Read the Progress Log to understand current state
3. Summarize: "Currently at [phase], completed [X items], next: [Y]"
4. Resume from the first unchecked item in the checklist
5. Continue updating checklist and Progress Log

**DO NOT start over. DO NOT ignore existing progress.**

---

## QIA Template (Copy-Paste Ready)

```markdown
## Quick Impact Assessment (QIA)

- **Functional change?** [YES/NO]
  - YES if alters externally observable behavior, modifies existing REQ, changes pagination/correctness, or changes error-handling semantics users can observe
- **Touches CR-required triggers?** [YES/NO]
  - Requirements change, major approach change, architecture, security, performance/SLO, breaking change, large blast radius
- **CR required?** [YES/NO]
  - Rationale: [one sentence]
```

---

## Implementation Checklist Template

```markdown
## Implementation Checklist

### Pre-implementation
- [ ] Requirement traceability confirmed
- [ ] Implementation plan created
- [ ] (If CR-required) CR + IA created and ATP received

### TDD (if code changes)
- [ ] RED: write failing test(s)
- [ ] GREEN: implement minimal change
- [ ] REFACTOR: clean up without behavior change

### Observability
- [ ] Logs/metrics/traces updated as required
- [ ] Fail loudly on error paths

### Documentation
- [ ] RTM updated as needed
- [ ] ADR created/updated if architectural
- [ ] Runbook/README updated if needed

### Validation
- [ ] Unit tests pass; coverage ≥80%
- [ ] Lint/format/typecheck pass
- [ ] Security/dependency audit pass
```

---

## Example Implementation Plan

```markdown
# Implementation Plan: IP-2026-02-19-001-add-logging

**Status**: IN_PROGRESS

**Created**: 2026-02-19 10:00:00 UTC  
**Last Updated**: 2026-02-19 11:30:00 UTC

## Ownership & Links

- **Owner / Agent**: Kiro AI Agent
- **Branch**: feat/REQ-042-structured-logging
- **PR**: #123
- **Related CR**: N/A (Standard Change)
- **Related REQ(s)**: REQ-042

---

## Quick Impact Assessment (QIA)

- **Functional change?** NO (adds observability, no behavior change)
- **Touches CR-required triggers?** NO (additive, low impact)
- **CR required?** NO - Rationale: Adds logging without changing functionality

### Scope Summary
- **Files expected to change**:
  - [x] `src/log_ingestion/service.py`
  - [x] `tests/test_service.py`

---

## Implementation Checklist

### Pre-implementation
- [x] Requirement traceability confirmed (REQ-042)
- [x] Implementation plan created

### TDD
- [x] RED: write failing test for structured logging
- [x] GREEN: implement structured logging
- [x] REFACTOR: clean up logging calls

### Observability
- [x] JSON-formatted logs implemented
- [x] Trace context added

### Documentation
- [x] RTM updated with REQ-042 implementation details

### Validation
- [x] Unit tests pass; coverage at 85%
- [x] Lint passes

---

## Progress Log

- 2026-02-19 10:00 UTC - Started. QIA complete; no CR required.
- 2026-02-19 10:30 UTC - RED phase complete; tests failing as expected.
- 2026-02-19 11:00 UTC - GREEN phase complete; all tests passing.
- 2026-02-19 11:30 UTC - REFACTOR complete; ready for PR.

---

## Restart / Continue Instructions

Work is complete. Ready to create PR.
```

---

## For AI Agents: Key Rules

1. **Always create an implementation plan for code changes**
2. **Update the plan as you work** (don't let it go stale)
3. **On restart, open the plan first** (don't start from scratch)
4. **Keep Progress Log factual and timestamped**
5. **Mark items complete as you finish them**

---

**Last Updated**: 2026-02-19
