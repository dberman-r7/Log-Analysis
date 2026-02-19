# AI Agent Memory - Project Context

> This file maintains context and learnings across agent sessions.
> Agents should read this file at the start of each session and update it with new learnings.

---

## Recent Decisions

### 2026-02-19: Governance Enhancement Implementation
- **Decision**: Implemented Kiro steering files for governance framework
- **Rationale**: Improve AI agent compliance with governance rules through automatic context loading
- **CR-ID**: CR-2026-02-19-001
- **Key Learning**: Steering files are automatically loaded by Kiro and provide immediate context

### 2026-02-19: Implementation Plan Requirement Clarified
- **Decision**: Implementation plans required for ALL code changes (src/, tests/, dependencies)
- **Rationale**: Ensures consistent tracking and restart/continue capability
- **Key Learning**: Plans are NOT required for pure documentation updates

---

## Common Patterns

### Pattern: Standard Change (No CR)
- **When to use**: Bug fixes, minor refactors, additive features with low impact
- **Process**: QIA → Implementation Plan → Feature Branch → TDD → PR
- **Example**: Adding logging, fixing typos in code, minor performance improvements

### Pattern: Governed Change (CR Required)
- **When to use**: Requirements changes, architecture changes, security/performance impacts, breaking changes
- **Process**: QIA → CR + IA → Wait for ATP → Implementation Plan → Feature Branch → TDD → PR
- **Example**: Changing storage format, adding authentication, modifying API contracts

### Pattern: TDD Workflow
- **Always**: RED (failing test) → GREEN (minimal code) → REFACTOR (clean up)
- **Never**: Write code first, then tests
- **Key**: If test fails, fix the code (not the test) unless requirement changed

---

## Anti-Patterns Observed

### Anti-Pattern: Starting Implementation Without ATP
- **Problem**: Beginning code changes for CR-required work before receiving "Approved to Proceed"
- **Why problematic**: Violates governance gate; wastes effort if CR rejected
- **Correct approach**: Wait for explicit ATP token before any implementation

### Anti-Pattern: Skipping Implementation Plans
- **Problem**: Making code changes without creating/updating implementation plan
- **Why problematic**: Loses context on restart; no progress tracking; violates governance
- **Correct approach**: Always create plan for code changes; update as you work

### Anti-Pattern: Fixing Tests to Match Broken Code
- **Problem**: Changing test assertions when tests fail instead of fixing code
- **Why problematic**: Tests are truth; changing them masks bugs
- **Correct approach**: Fix code to make tests pass (unless requirement changed)

### Anti-Pattern: Hardcoding Secrets
- **Problem**: Including API keys, passwords, or credentials directly in code
- **Why problematic**: Security vulnerability; will fail security scan
- **Correct approach**: Use environment variables or secret management service

---

## Frequently Referenced Requirements

### REQ-001 through REQ-011: Log Ingestion Service
- **Context**: Core log ingestion functionality from Rapid7 API to Parquet storage
- **Status**: IMPLEMENTED and TESTED
- **Key files**: `src/log_ingestion/`, `tests/test_*.py`
- **Why frequently referenced**: Foundation of the system; most changes touch these

### Governance Requirements (Implicit)
- **Context**: Change management, TDD, security, documentation requirements
- **Status**: ACTIVE and ENFORCED
- **Key files**: `.github/copilot-instructions.md`, `docs/processes/`
- **Why frequently referenced**: Apply to every change

---

## Project-Specific Conventions

### Branch Naming
- Features: `feat/REQ-XXX-description`
- Bug fixes: `fix/Issue-NNN-description`
- Documentation: `docs/Topic-description`
- **Never**: Direct commits to `main`

### PR Title Format
- With CR: `[CR-YYYY-MM-DD-XXX] Description`
- Without CR: `[REQ-XXX] Description` or `[BUG] Description`

### File Organization
- Source code: `src/log_ingestion/`
- Tests: `tests/` (mirror src structure)
- Documentation: `docs/`
- Governance: `docs/processes/`
- Implementation plans: `docs/processes/implementation-plans/`
- Change requests: `docs/processes/change-requests/`

### Testing Standards
- Coverage: ≥80% required
- Test naming: `test_<component>_<scenario>_<expected_outcome>`
- Fixtures: Use pytest fixtures in `tests/conftest.py`

---

## Lessons Learned

### 2026-02-19: Steering Files Improve Compliance
- **Lesson**: Kiro automatically loads steering files from `.kiro/steering/`
- **Context**: Implemented governance steering files; immediately loaded in subsequent interactions
- **Application**: Use steering files for project-specific rules and quick references
- **Impact**: Reduces governance violations; improves consistency

### 2026-02-11: Implementation Plans Enable Continuity
- **Lesson**: Implementation plans with checklists and progress logs enable seamless restart/continue
- **Context**: Multiple CRs implemented with detailed plans
- **Application**: Always create plan; update progress log; resume from first unchecked item
- **Impact**: No lost context; efficient restarts

### 2026-02-10: QIA Prevents Unnecessary CRs
- **Lesson**: Quick Impact Assessment helps distinguish Standard vs Governed changes
- **Context**: Many changes don't require full CR process
- **Application**: Always perform QIA first; only create CR when triggers are hit
- **Impact**: Faster workflow for low-risk changes; governance where needed

---

## Technology Stack

### Primary Languages
- Python 3.11+ (main application language)

### Key Libraries
- `pyarrow`: Parquet file handling
- `requests`: HTTP client for API calls
- `pytest`: Testing framework
- `ruff`: Linting
- `black`: Code formatting

### Development Tools
- Git: Version control
- GitHub Actions: CI/CD
- pytest: Test runner with coverage

---

## Common Commands

```bash
# Run tests with coverage
pytest --cov=src --cov-report=term

# Lint code
ruff check .

# Format code
black .

# Security audit
pip-audit

# Create new branch
git checkout -b feat/REQ-XXX-description

# Generate CR (when script exists)
./scripts/generate-cr-template.sh
```

---

## Quick Reference Links

- **Governance Framework**: `.github/copilot-instructions.md`
- **Change Management**: `docs/processes/change-management.md`
- **Definition of Done**: `docs/processes/definition-of-done.md`
- **RTM**: `docs/requirements/rtm.md`
- **Quick Start**: `docs/processes/QUICKSTART.md`
- **Implementation Plan Template**: `docs/processes/templates/implementation-plan-template.md`

---

## Notes for Future Sessions

### Current State (2026-02-19)
- Governance enhancement (CR-2026-02-19-001) in progress
- Branch: `feat/governance-enhancement`
- Implementation plan: `docs/processes/implementation-plans/IP-2026-02-19-001-governance-enhancement.md`
- Status: Creating steering files, decision trees, and helper scripts

### Next Steps
- Complete decision trees
- Create helper scripts
- Create CI/CD enhancements
- Update main documentation
- Create PR

---

## Agent Instructions

**On every new session:**
1. Read this file to understand project context
2. Check for active implementation plans in `docs/processes/implementation-plans/`
3. If continuing work, open the relevant plan and resume from first unchecked item
4. Update this file with new learnings and decisions

**When adding entries:**
- Keep entries concise and actionable
- Include dates and context
- Link to relevant CRs, REQs, or files
- Focus on patterns and learnings, not minutiae

---

**Last Updated**: 2026-02-19
