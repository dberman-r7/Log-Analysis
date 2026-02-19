# Governance Quick Reference

> One-page cheat sheet for the governance framework

---

## Core Principles

1. **No Ghost Code**: If it isn't in the RTM, it shouldn't be in the PR
2. **Docs are Code**: Documentation drift is a breaking build
3. **Fail Loudly**: Observability must make failures immediately obvious

---

## Do I Need a CR?

**CR REQUIRED if ANY of these**:
- ✅ Requirements change (adds/modifies/deprecates REQ-IDs)
- ✅ Major approach change
- ✅ Architecture change
- ✅ Security impact
- ✅ Performance/SLO impact
- ✅ Breaking change
- ✅ Large blast radius

**NO CR if**:
- ❌ Bug fix (existing REQ)
- ❌ Clarification/docs
- ❌ Minor refactor
- ❌ Additive feature (low impact)

---

## Workflow Decision Tree

```
User Request
    ↓
Perform QIA
    ↓
CR required? ──NO──→ Standard Change
    ↓ YES           (Impl Plan + TDD + PR)
    ↓
Create CR + IA
    ↓
Wait for ATP
    ↓
Impl Plan + TDD + PR
```

---

## Standard Change Path (No CR)

1. Perform QIA
2. Create implementation plan (for code changes)
3. Feature branch: `feat/REQ-XXX-description`
4. TDD: RED → GREEN → REFACTOR
5. Update docs (RTM, README, etc.)
6. PR with DoD complete

---

## Governed Change Path (CR Required)

1. Perform QIA
2. Create CR + Impact Assessment
3. Wait for ATP ("Approved to Proceed")
4. Create implementation plan
5. Feature branch: `feat/REQ-XXX-description`
6. TDD: RED → GREEN → REFACTOR
7. Update docs (RTM, ADR, etc.)
8. PR with DoD complete

---

## TDD Cycle

1. **RED**: Write failing test
2. **GREEN**: Write minimum code to pass
3. **REFACTOR**: Clean up code

**Golden Rule**: If test fails, fix the code (not the test)

---

## DoD Checklist (Essential Items)

- [ ] CR + ATP (if CR-required)
- [ ] Implementation plan (for code changes)
- [ ] Tests first (TDD Red)
- [ ] Code works (TDD Green)
- [ ] Code refactored (TDD Refactor)
- [ ] Coverage ≥ 80%
- [ ] Linter passes (zero warnings)
- [ ] Security scan clean
- [ ] RTM updated
- [ ] Docs updated
- [ ] ADR created (if architectural)
- [ ] Feature branch + PR
- [ ] Code review approved

---

## Security Checklist

- [ ] No hardcoded secrets
- [ ] Use environment variables
- [ ] Input validation
- [ ] Dependency audit clean
- [ ] No sensitive data in logs

---

## Branch Naming

```
feat/REQ-XXX-description      # Features
fix/Issue-NNN-description     # Bug fixes
docs/Topic-description        # Documentation
refactor/Component            # Refactoring
```

---

## PR Title Format

```
[CR-YYYY-MM-DD-XXX] Description    # With CR
[REQ-XXX] Description              # Without CR (feature)
[BUG] Description                  # Without CR (bug fix)
```

---

## File Locations

```
.kiro/steering/                    # Steering files (auto-loaded)
.kiro/agent-memory.md              # Agent context/memory

docs/processes/
├── change-requests/               # CRs
├── implementation-plans/          # Implementation plans
├── decision-trees/                # Decision trees
└── templates/                     # Templates

docs/requirements/rtm.md           # Requirements
docs/arch/adr/                     # ADRs
docs/processes/definition-of-done.md
docs/processes/change-management.md

scripts/
├── governance-preflight.sh        # Pre-flight check
├── generate-cr-template.sh        # Generate CR
├── validate-qia.sh                # Validate QIA
└── check-implementation-plan.sh   # Check plans
```

---

## Common Commands

```bash
# Pre-flight check
./scripts/governance-preflight.sh

# Generate new CR
./scripts/generate-cr-template.sh

# Validate QIA
./scripts/validate-qia.sh docs/processes/implementation-plans/IP-*.md

# Check implementation plans
./scripts/check-implementation-plan.sh

# Run tests with coverage
pytest --cov=src --cov-report=term

# Lint code
ruff check .

# Format code
black .

# Security audit
pip-audit
```

---

## Quick QIA Template

```markdown
## Quick Impact Assessment (QIA)

- **Functional change?** [YES/NO]
- **Touches CR-required triggers?** [YES/NO]
- **CR required?** [YES/NO]
  - Rationale: [one sentence]
```

---

## When to Create ADR

**ADR REQUIRED if**:
- Affects system structure
- Introduces new technology
- Changes data flow/storage
- Significant security/performance impact
- Sets precedent
- Hard to reverse
- Future devs need to know why

---

## Coverage Requirements

- Unit Test Coverage: ≥ 80%
- Branch Coverage: ≥ 75%
- Critical Path Coverage: 100%

---

## Forbidden Actions (Without ATP for CR-required work)

- ❌ Creating/modifying code files
- ❌ Installing/upgrading dependencies
- ❌ Running migrations
- ❌ Deploying changes

---

## Allowed Actions (Without ATP)

- ✅ Reading code
- ✅ Analyzing architecture
- ✅ Drafting plans
- ✅ Answering questions

---

## For AI Agents: Mandatory Workflow

1. On every request: Perform QIA
2. Create/update implementation plan (for code changes)
3. If CR-required: Create CR + IA, wait for ATP
4. If not CR-required: Follow Standard Change Path
5. Always use feature branch + PR
6. Complete DoD before review

**NEVER start implementation for CR-required changes without ATP**

---

## Decision Trees

- **CR Required?**: `docs/processes/decision-trees/cr-required-decision-tree.md`
- **DoD Items?**: `docs/processes/decision-trees/dod-selector.md`
- **ADR Required?**: `docs/processes/decision-trees/adr-required-decision-tree.md`

---

## Key Documentation

- **Governance Framework**: `.github/copilot-instructions.md`
- **Change Management**: `docs/processes/change-management.md`
- **Definition of Done**: `docs/processes/definition-of-done.md`
- **RTM**: `docs/requirements/rtm.md`
- **Quick Start**: `docs/processes/QUICKSTART.md`

---

## Common Scenarios

### Bug Fix
- QIA: Functional=YES, CR-triggers=NO, CR=NO
- Path: Standard Change
- Create impl plan → Fix with TDD → Update tests → PR

### New Feature (Low Impact)
- QIA: Functional=YES, CR-triggers=NO, CR=NO
- Path: Standard Change
- Add REQ-ID → Impl plan → TDD → Update RTM → PR

### Architecture Change
- QIA: Functional=YES, CR-triggers=YES, CR=YES
- Path: Governed Change
- CR + IA → ATP → Impl plan → TDD → ADR → Update RTM → PR

---

## Help & Support

**Questions?**
1. Check documentation first
2. Review decision trees
3. Run pre-flight check
4. Ask in team chat
5. Create issue

---

**Last Updated**: 2026-02-19
