# Change Request Template

**Instructions**: Copy this template to `/docs/processes/change-requests/CR-YYYY-MM-DD-XXX.md` and fill it out.

---

# Change Request: CR-YYYY-MM-DD-XXX

**Status**: DRAFT

**Created**: YYYY-MM-DD HH:MM:SS UTC  
**Last Updated**: YYYY-MM-DD HH:MM:SS UTC

---

## Basic Information

**Title**: [Brief description of the change]

**Requestor**: [Name/Email of person requesting change]

**Category**: 
- [ ] FEATURE
- [ ] BUG
- [ ] REFACTOR
- [ ] SECURITY
- [ ] PERFORMANCE
- [ ] DOCUMENTATION
- [ ] INFRASTRUCTURE

**Priority**: 
- [ ] P0 - CRITICAL (System down, security breach)
- [ ] P1 - HIGH (Major feature, significant bug)
- [ ] P2 - MEDIUM (Minor feature, moderate bug)
- [ ] P3 - LOW (Enhancement, minor issue)

**Urgency**:
- [ ] IMMEDIATE (Within 24 hours)
- [ ] HIGH (Within 1 week)
- [ ] NORMAL (Within 2 weeks)
- [ ] LOW (Next sprint/release)

---

## Description

### Problem Statement
[What problem are we solving? What is the current pain point?]

### Proposed Solution
[What is the proposed change? How will it solve the problem?]

### Business Justification
[Why is this change needed? What value does it provide?]

### Alternatives Considered
[What other approaches were considered? Why were they rejected?]

---

## Affected Components

**Systems**:
- [ ] Web Application
- [ ] API Backend
- [ ] Database
- [ ] Message Queue
- [ ] Cache Layer
- [ ] External Integrations
- [ ] CI/CD Pipeline
- [ ] Infrastructure
- [ ] Documentation
- [ ] Other: _______

**Modules/Services**:
- [List specific modules or services affected]

**Files** (Estimated):
- [List key files that will be modified]

---

## Dependencies

**Upstream Dependencies** (must complete before this CR):
- [CR-XXXX: Description]
- [REQ-XXX: Description]

**Downstream Impact** (will affect these):
- [CR-YYYY: Description]
- [Feature Z: Description]

**External Dependencies**:
- [Third-party API update required]
- [Infrastructure changes required]
- [Vendor coordination required]

---

## Stakeholders

**Approver(s)**:
- [Name] - [Role] - [ ] Approved

**Implementer(s)**:
- [Name] - [Role]

**Reviewers**:
- [Name] - [Role]

**Notified Parties**:
- [Team/Person to keep informed]

---

## Impact Assessment

[See /docs/processes/change-management.md for full IA template]

**Assessment Date**: YYYY-MM-DD  
**Assessed By**: [Name]

### 1. Code Impact
- **Files to Create**: N
- **Files to Modify**: N
- **Files to Delete**: N
- **Breaking Changes**: YES/NO

### 2. Security Impact
- **Assessment Level**: LOW/MEDIUM/HIGH/CRITICAL
- **Security Review Required**: YES/NO

### 3. Performance Impact
- **Assessment**: POSITIVE/NEUTRAL/NEGATIVE/UNKNOWN
- **Expected Latency Change**: +/- XX ms

### 4. Testing Impact
- **Unit Tests**: N new tests
- **Integration Tests**: N new tests
- **Expected Coverage**: XX%

### 5. Documentation Impact
- [ ] RTM update required
- [ ] ADR required
- [ ] README update required
- [ ] API docs update required

### 6. Blast Radius
- **Size**: SMALL/MEDIUM/LARGE/CRITICAL
- **Affected Users**: All/Subset/None
- **Reversibility**: Easy/Moderate/Difficult/Irreversible

---

## Implementation Plan

### Prerequisites
- [ ] CR approved and ATP received
- [ ] Branch created
- [ ] Requirements decomposed into REQ-IDs
- [ ] RTM updated

### Implementation Steps
1. [ ] Write failing tests (TDD Red)
2. [ ] Implement minimum code (TDD Green)
3. [ ] Refactor code (TDD Refactor)
4. [ ] Add observability
5. [ ] Update documentation
6. [ ] Create ADR (if needed)

### Validation
- [ ] All tests pass
- [ ] Coverage ≥ 80%
- [ ] Linter passes
- [ ] Security scan clean
- [ ] Performance benchmarks pass

### Timeline
**Estimated Duration**: [X hours/days]  
**Start Date**: YYYY-MM-DD  
**Target End Date**: YYYY-MM-DD

---

## Approval

**Approval Token Received**: [ ] Yes [ ] No  
**Approval Date**: YYYY-MM-DD

**Approved by**:
- [ ] Technical Lead: ____________ (Date: ______)
- [ ] Security Team: ____________ (Date: ______) [if applicable]
- [ ] Product Owner: ____________ (Date: ______) [if applicable]

---

## Implementation Tracking

**Branch**: [branch-name]  
**Pull Request**: #[number]  
**Status**: [DRAFT|PROPOSED|APPROVED|IN_PROGRESS|COMPLETED|REJECTED]

**Implementation Start**: YYYY-MM-DD  
**Implementation End**: YYYY-MM-DD  
**Deployed to Production**: YYYY-MM-DD

---

## Change History

| Date | Status | Notes |
|------|--------|-------|
| YYYY-MM-DD | DRAFT | CR created |
| YYYY-MM-DD | PROPOSED | Submitted for approval |
| YYYY-MM-DD | APPROVED | Approval received |
| YYYY-MM-DD | IN_PROGRESS | Implementation started |
| YYYY-MM-DD | COMPLETED | Deployed and verified |

---

## Lessons Learned

[To be filled after completion]

**What went well**:
- 

**What could be improved**:
- 

**Action items for future CRs**:
- 

---

**End of CR Template**
