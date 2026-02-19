# Governance Framework - AI Agent Quick Reference

> This steering file provides quick access to the core governance principles for this repository.
> For complete details, see: #[[file:.github/copilot-instructions.md]]

---

## Core Principles

### 1. "No Ghost Code"
**If it isn't in the RTM, it shouldn't be in the PR.**

Every line of code must trace back to a documented requirement in `/docs/requirements/rtm.md`.

### 2. "Docs are Code"
**Documentation drift is treated as a breaking build.**

Documentation must be updated alongside code changes. Outdated docs are critical defects.

### 3. "Fail Loudly"
**Observability must be implemented so failures are immediately obvious.**

Silent failures are unacceptable. All features need structured logging, tracing, and metrics.

---

## Change Management Quick Decision

### Do I need a Change Request (CR)?

A CR is **REQUIRED** if the change meets **ANY** of these triggers:

- ✅ **Requirements change**: adds/modifies/deprecates existing REQ-IDs
- ✅ **Major approach change**: substantially changes how a requirement is implemented
- ✅ **Architecture change**: crosses component boundaries or introduces new components
- ✅ **Security-impacting**: auth/authz, data exposure, secrets, encryption, compliance
- ✅ **Performance/SLO-impacting**: affects latency, throughput, memory, storage, rate limits
- ✅ **Breaking change**: any user-facing or API-breaking behavior
- ✅ **Large blast radius**: touches many modules, high regression risk

A CR is **NOT REQUIRED** for:

- ❌ Bug fixes correcting behavior under existing requirements
- ❌ Clarifications improving wording/comments/docs without changing requirements
- ❌ Minor refactors preserving behavior (no public API changes)
- ❌ Additive features that don't change existing REQ-IDs and have low impact

**When in doubt**: Perform a Quick Impact Assessment (QIA) first.

See: #[[file:docs/processes/change-management.md]]

---

## Implementation Plan Requirement

**ALWAYS REQUIRED** for code changes (typically `src/`, `tests/`, or dependency manifests):

- Create a written, saved Markdown implementation plan
- Location: `docs/processes/implementation-plans/`
- Template: `docs/processes/templates/implementation-plan-template.md`
- Must include QIA and checklist
- Update as work progresses

See: #[[file:.kiro/steering/implementation-plan-requirements.md]]

---

## Test-Driven Development (TDD)

**The Golden Rule**: Tests are written **BEFORE** implementation. No exceptions.

### The TDD Cycle

1. **RED**: Write a failing test
2. **GREEN**: Write minimum code to pass
3. **REFACTOR**: Improve code quality

**If a test fails, the code is wrong** (unless the requirement changed).

See: #[[file:.kiro/steering/tdd-requirements.md]]

---

## Security First

**Zero Tolerance for Hardcoded Secrets**

```python
# ❌ FORBIDDEN
API_KEY = "sk-1234567890abcdef"

# ✅ REQUIRED
API_KEY = os.getenv('API_KEY')
```

See: #[[file:.kiro/steering/security-requirements.md]]

---

## Definition of Done (DoD)

Every PR must complete the DoD checklist. Key items:

- [ ] CR created and ATP received (if CR-required)
- [ ] Implementation plan created (for code changes)
- [ ] Tests written first (TDD Red)
- [ ] Code works (TDD Green)
- [ ] Code refactored (TDD Refactor)
- [ ] Coverage ≥ 80%
- [ ] Linter passes (zero warnings)
- [ ] Security scan clean
- [ ] RTM updated
- [ ] Documentation updated
- [ ] ADR created (if architectural)

See: #[[file:docs/processes/definition-of-done.md]]

---

## Quick Links

- **Full Governance**: #[[file:.github/copilot-instructions.md]]
- **Change Management**: #[[file:docs/processes/change-management.md]]
- **Definition of Done**: #[[file:docs/processes/definition-of-done.md]]
- **RTM**: #[[file:docs/requirements/rtm.md]]
- **Quick Start**: #[[file:docs/processes/QUICKSTART.md]]

---

## For AI Agents: Mandatory Workflow

1. **On every user request**: Perform Quick Impact Assessment (QIA)
2. **Create/update implementation plan** (for code changes)
3. **If CR-required**: Create CR + IA, wait for ATP before implementation
4. **If not CR-required**: Follow Standard Change Path (REQ traceability + TDD)
5. **Always use feature branch + PR** (no direct commits to main)
6. **Complete DoD** before requesting review

**NEVER start implementation for CR-required changes without ATP.**

---

**Last Updated**: 2026-02-19
