# Change Management - Quick Reference for AI Agents

> Quick reference for the Change Management process.
> Full details: #[[file:docs/processes/change-management.md]]

---

## Quick Impact Assessment (QIA) Template

**REQUIRED for all work** - Use this to decide CR vs Standard Change:

```markdown
### Quick Impact Assessment (QIA)

- **Functional change?** [YES/NO]
  - YES if alters externally observable behavior, modifies existing REQ, changes pagination/correctness, or changes error-handling semantics users can observe
- **Touches CR-required triggers?** [YES/NO]
  - Requirements change, major approach change, architecture, security, performance/SLO, breaking change, large blast radius
- **CR required?** [YES/NO]
  - Rationale: [one sentence]
```

---

## CR-Required Triggers Checklist

Use this checklist to determine if a CR is needed:

- [ ] **Requirements change**: Adds/modifies/deprecates REQ-IDs in RTM
- [ ] **Major approach change**: Substantially changes implementation approach
- [ ] **Architecture change**: Crosses boundaries, new components, ADR-worthy
- [ ] **Security-impacting**: Auth/authz, data exposure, secrets, encryption, compliance
- [ ] **Performance/SLO-impacting**: Affects latency, throughput, memory, storage, rate limits
- [ ] **Breaking change**: User-facing or API-breaking behavior
- [ ] **Large blast radius**: Many modules, high regression risk, complex rollout

**If ANY box is checked → CR REQUIRED**

---

## Standard Change Path (No CR Required)

For changes that don't trigger CR requirements:

1. **Confirm requirement traceability**
   - Map to existing REQ-ID or add new REQ-ID (PROPOSED)
   
2. **Create implementation plan** (for code changes)
   - Location: `docs/processes/implementation-plans/`
   - Template: `docs/processes/templates/implementation-plan-template.md`
   
3. **Feature branch + PR** (mandatory)
   - Branch: `feat/REQ-XXX-...` or `fix/Issue-NNN-...`
   
4. **TDD** (for code changes)
   - Red → Green → Refactor
   
5. **Update docs**
   - RTM, README, etc. as needed
   
6. **Validation**
   - Tests, lint, security checks

---

## Governed Change Path (CR Required)

For changes that trigger CR requirements:

1. **Create Change Request (CR)**
   - Location: `docs/processes/change-requests/CR-YYYY-MM-DD-XXX.md`
   - Template: `docs/processes/templates/cr-template.md`
   - Use script: `scripts/generate-cr-template.sh` (if available)
   
2. **Perform Impact Assessment (IA)**
   - Include in CR document
   - Analyze blast radius across 8 dimensions
   
3. **Draft Implementation Plan**
   - Link from CR or embed
   
4. **Wait for ATP (Approved to Proceed)**
   - Acceptable tokens: "Approved to Proceed", "ATP", "Go Ahead", "Implement"
   - **DO NOT START IMPLEMENTATION WITHOUT ATP**
   
5. **Implement on feature branch**
   - Follow implementation plan
   - Update progress regularly
   
6. **Submit PR with DoD complete**

---

## Forbidden Actions Without ATP (CR-Required Work Only)

- ❌ Creating/modifying code files
- ❌ Installing/upgrading dependencies
- ❌ Running migrations
- ❌ Deploying changes

## Allowed Actions Without ATP

- ✅ Reading existing code
- ✅ Analyzing architecture
- ✅ Drafting plans and designs
- ✅ Answering questions
- ✅ Running read-only commands

---

## CR Document Structure (Quick Reference)

Required sections in every CR:

1. **Basic Information**: Title, category, priority, urgency
2. **Description**: Problem, solution, justification, alternatives
3. **Affected Components**: Systems, modules, files
4. **Dependencies**: Upstream, downstream, external
5. **Stakeholders**: Approvers, implementers, reviewers
6. **Approval Status**: ATP tracking
7. **Impact Assessment**: 8-dimension analysis
8. **Implementation Plan**: Step-by-step execution
9. **Implementation Tracking**: Branch, PR, dates

---

## Branch Naming Convention

```
feat/REQ-XXX-brief-description      # For features
fix/Issue-NNN-brief-description     # For bug fixes
hotfix/PROD-Issue-description       # For production hotfixes
refactor/Component-description      # For refactoring
docs/Topic-description              # For documentation
```

---

## PR Title Format

**With CR**:
```
[CR-YYYY-MM-DD-XXX] Brief description of change
```

**Without CR**:
```
[REQ-XXX] Brief description of change
[BUG] Brief description of fix
```

---

## Common Scenarios

### Scenario: Bug Fix

**QIA**:
- Functional change? YES (fixes incorrect behavior)
- CR-required triggers? NO (corrects existing REQ)
- CR required? NO

**Path**: Standard Change
- Map to existing REQ-ID
- Create implementation plan
- Fix bug with TDD
- Update tests

---

### Scenario: New Feature (Additive, Low Impact)

**QIA**:
- Functional change? YES (new behavior)
- CR-required triggers? NO (additive, no breaking changes, low blast radius)
- CR required? NO

**Path**: Standard Change
- Add new REQ-ID (PROPOSED)
- Create implementation plan
- Implement with TDD
- Update RTM and docs

---

### Scenario: Changing Storage Format (CSV → Parquet)

**QIA**:
- Functional change? YES (changes data format)
- CR-required triggers? YES (architecture change, breaking change, large blast radius)
- CR required? YES

**Path**: Governed Change
- Create CR with full IA
- Wait for ATP
- Implement with careful migration plan

---

### Scenario: Performance Optimization

**QIA**:
- Functional change? NO (same behavior, faster)
- CR-required triggers? MAYBE (depends on SLO impact)
- CR required? YES if SLO-impacting, NO if minor optimization

**Decision**: If changes affect SLO targets → CR required

---

## For AI Agents: Decision Tree

```
User Request
    ↓
Perform QIA
    ↓
Functional change? ──NO──→ Clarification/Doc update
    ↓ YES                  (Standard Change, no CR)
    ↓
Touches CR triggers? ──NO──→ Standard Change Path
    ↓ YES                    (Implementation Plan + TDD)
    ↓
Create CR + IA
    ↓
Wait for ATP
    ↓
Implement
```

---

## Progress Tracking (Agents)

For any work with an implementation plan:

1. **Maintain visible checklist** in the plan
2. **Add Progress Log** with timestamped notes
3. **Update status** after each session
4. **On restart/continue**: Open plan, resume from first unchecked item

---

## Quick Commands

```bash
# Generate new CR (if script exists)
./scripts/generate-cr-template.sh

# Validate QIA format (if script exists)
./scripts/validate-qia.sh

# Check implementation plan (if script exists)
./scripts/check-implementation-plan.sh

# Pre-flight governance check (if script exists)
./scripts/governance-preflight.sh
```

---

**Last Updated**: 2026-02-19
