# Definition of Done (DoD)

> **Version:** 1.0.0  
> **Last Updated:** 2026-02-09  
> **Owner:** Engineering Team

This document defines the **mandatory checklist** that must be completed before any work item can be considered "Done."

---

## What is "Done"?

A work item is **Done** when:
1. All acceptance criteria are met
2. All DoD checklist items are completed
3. The work is potentially shippable to production
4. No known defects remain (unless explicitly accepted as tech debt)

**Not Done** means **Not Merged**. Period.

---

## Master Definition of Done Checklist

Use this checklist for **every** pull request:

### 1. Requirements & Planning

- [ ] **Requirements Documented**: All requirements are documented in RTM with REQ-IDs
- [ ] **CR Created (if required)**: CR is created and approved **only when the change meets CR-required triggers** (see `docs/processes/change-management.md`)
- [ ] **Impact Assessment (if CR-required)**: Blast radius analysis completed for governed changes
- [ ] **Implementation Plan (required for code changes)**: A written, saved Markdown implementation plan exists for any code change (typically `src/`, `tests/`, or dependency manifests) and is updated as work progresses
- [ ] **ATP Received (if CR-required)**: "Approved to Proceed" token received from user before implementation for governed changes

---

### 2. Code Quality

- [ ] **Tests Written First**: TDD followed - tests written before implementation (Red phase)
- [ ] **Implementation Complete**: Code written to make tests pass (Green phase)
- [ ] **Code Refactored**: Code cleaned up and optimized (Refactor phase)
- [ ] **Linter Passes**: Zero warnings from linter
  ```bash
  ruff check . --exit-zero
  # Must return no issues
  ```
- [ ] **Formatter Passes**: Code is properly formatted
  ```bash
  black --check .
  # Must return no formatting issues
  ```
- [ ] **Type Checker Passes**: Static type checking passes (if applicable)
  ```bash
  mypy src/
  # Must return no type errors
  ```
- [ ] **Code Complexity**: No functions exceed cyclomatic complexity threshold (< 10)
- [ ] **No Code Smells**: No duplicate code, god objects, or other anti-patterns
- [ ] **Code Review Complete**: At least one approval from qualified reviewer
- [ ] **All Review Comments Addressed**: No unresolved review threads

---

### 3. Testing

- [ ] **Unit Tests**: All new logic has unit tests
  - [ ] Tests are focused and fast (< 100ms each)
  - [ ] Tests follow Arrange-Act-Assert pattern
  - [ ] Tests have descriptive names
  - [ ] Edge cases covered
  
- [ ] **Integration Tests**: Component interactions tested
  - [ ] API endpoints tested
  - [ ] Database interactions tested
  - [ ] External service mocks configured
  
- [ ] **E2E Tests**: Critical user flows tested (if applicable)
  - [ ] Happy path tested
  - [ ] Error scenarios tested
  
- [ ] **Test Coverage**: Minimum 80% line coverage
  ```bash
  pytest --cov=src --cov-report=term
  # Coverage must be >= 80%
  ```
  
- [ ] **All Tests Pass**: 100% test pass rate
  ```bash
  pytest -v
  # All tests must pass
  ```
  
- [ ] **No Flaky Tests**: All tests are deterministic
- [ ] **Test Data**: Test fixtures and mocks properly configured
- [ ] **Performance Tests**: Performance benchmarks pass (if applicable)

---

### 4. Security

- [ ] **No Hardcoded Secrets**: Zero hardcoded credentials, API keys, or passwords
- [ ] **Environment Variables**: All secrets loaded from environment or secret manager
- [ ] **Input Validation**: All inputs validated and sanitized
- [ ] **Output Encoding**: All outputs properly encoded
- [ ] **Dependency Audit**: No HIGH or CRITICAL vulnerabilities
  ```bash
  pip-audit
  # Must return zero HIGH/CRITICAL issues
  ```
- [ ] **Security Scan**: SAST scan passes with no new issues
- [ ] **Authentication**: Auth checks implemented where required
- [ ] **Authorization**: Permission checks implemented where required
- [ ] **Least Privilege**: Service accounts follow least privilege principle
- [ ] **Encryption**: Sensitive data encrypted at rest and in transit
- [ ] **Security Review**: Security-impacting changes reviewed by security team

---

### 5. Performance

- [ ] **Performance Baseline**: Baseline metrics documented
- [ ] **Performance Tests**: Performance benchmarks executed
- [ ] **SLO Compliance**: Changes meet SLO requirements
  - [ ] Latency within targets (P50, P95, P99)
  - [ ] Throughput within targets
  - [ ] Error rate within targets
- [ ] **Resource Usage**: No memory leaks or resource exhaustion
- [ ] **Database Queries**: Queries optimized, indexes in place
- [ ] **Caching**: Appropriate caching strategy implemented
- [ ] **No Performance Regression**: Performance equal or better than baseline

---

### 6. Observability

- [ ] **Structured Logging**: JSON-formatted logs implemented
  - [ ] Log level appropriate (ERROR, WARN, INFO, DEBUG)
  - [ ] Required fields present (timestamp, trace_id, etc.)
  - [ ] Sensitive data not logged
  
- [ ] **Tracing**: OpenTelemetry spans added for service boundaries
  - [ ] Trace context propagated
  - [ ] Critical operations traced
  
- [ ] **Metrics**: Relevant metrics exposed
  - [ ] Request counts
  - [ ] Latency histograms
  - [ ] Error rates
  - [ ] Resource utilization
  
- [ ] **Health Checks**: Health endpoints implemented/updated
  - [ ] `/health` liveness check
  - [ ] `/ready` readiness check
  - [ ] `/metrics` Prometheus metrics
  
- [ ] **Alerts**: Alerting rules configured (if applicable)
  - [ ] SLO breach alerts
  - [ ] Error rate alerts
  - [ ] Runbook links included
  
- [ ] **Dashboards**: Monitoring dashboards updated (if applicable)

---

### 7. Documentation

- [ ] **RTM Updated**: Requirements Traceability Matrix updated
  - [ ] New REQ-IDs added
  - [ ] Status updated
  - [ ] Implementation details linked
  - [ ] Test coverage documented
  
- [ ] **ADR Created**: Architectural Decision Record created (if architectural change)
  - [ ] MADR template used
  - [ ] Status set to ACCEPTED
  - [ ] Options considered documented
  - [ ] Decision justified
  
- [ ] **Diagrams Updated**: Architecture diagrams updated (if applicable)
  - [ ] Mermaid.js format
  - [ ] Context diagram
  - [ ] Component diagram
  - [ ] Sequence diagram (if needed)
  
- [ ] **README Updated**: README.md reflects changes (if applicable)
- [ ] **API Documentation**: API docs updated (if API changes)
  - [ ] Endpoints documented
  - [ ] Parameters documented
  - [ ] Responses documented
  - [ ] Examples provided
  
- [ ] **Code Comments**: Complex logic explained with inline comments
  - [ ] "Why" not "what" explained
  - [ ] TODOs have ticket references
  
- [ ] **CHANGELOG Updated**: Notable changes added to CHANGELOG.md
- [ ] **Runbook Updated**: Operational runbook updated (if needed)
  - [ ] Deployment steps
  - [ ] Rollback procedure
  - [ ] Troubleshooting guide
  
- [ ] **Migration Guide**: Migration instructions provided (if breaking change)

---

### 8. Git & PR

- [ ] **Feature Branch Used**: All changes are made on a feature branch (no direct commits to `main`)
- [ ] **Branch Named Correctly**: `feat/REQ-XXX-description` or `fix/Issue-NNN-description`
- [ ] **Commit Messages**: Clear, descriptive commit messages
  - [ ] Follow conventional commits format
  - [ ] Include context and reasoning
  
- [ ] **PR Title**: Format: `[CR-YYYY-MM-DD-XXX] Brief description` (if CR-required) **or** `[REQ-XXX] Brief description` / `[BUG] Brief description` (if no CR)
- [ ] **PR Description**: Complete PR template filled out
  - [ ] CR-ID included
  - [ ] Requirements listed
  - [ ] RTM link provided
  - [ ] Impact assessment summary
  - [ ] ADR link (if applicable)
  - [ ] Definition of Done checklist
  - [ ] Rollback plan included
  
- [ ] **PR Size**: PR is reasonably sized (< 500 lines preferred)
- [ ] **PR Labels**: Appropriate labels applied
  - [ ] `type: feature|bug|refactor|docs|security|performance`
  - [ ] `priority: P0|P1|P2|P3`
  - [ ] `status: needs-review|in-progress|approved`
  
- [ ] **No Merge Conflicts**: Branch is up to date with main
- [ ] **Squash Commits**: Ready for squash merge (if using squash strategy)

---

### 9. CI/CD Pipeline

- [ ] **CI Passes**: All CI checks pass
  - [ ] Build succeeds
  - [ ] Tests pass
  - [ ] Linter passes
  - [ ] Security scan passes
  - [ ] Coverage threshold met
  
- [ ] **Governance Check**: RTM and ADR validation passes
- [ ] **No Broken Links**: Documentation links are valid
- [ ] **Deployment Ready**: Changes can be deployed without manual intervention
- [ ] **Feature Flags**: Feature flags configured (if applicable)

---

### 10. Operational Readiness

- [ ] **Deployment Plan**: Deployment steps documented
  - [ ] Environment variables configured
  - [ ] Secrets provisioned
  - [ ] Infrastructure changes applied
  - [ ] Database migrations ready
  
- [ ] **Rollback Plan**: Rollback procedure documented and tested
  - [ ] Steps to revert documented
  - [ ] Time to rollback estimated
  - [ ] No data loss risk
  
- [ ] **Configuration**: Configuration changes documented
  - [ ] Environment-specific configs
  - [ ] Feature flags
  - [ ] Service discovery
  
- [ ] **Dependencies**: External dependencies coordinated
  - [ ] Third-party services notified
  - [ ] Internal services coordinated
  - [ ] Breaking changes communicated
  
- [ ] **Support Prepared**: Support team briefed (if needed)
  - [ ] Known issues documented
  - [ ] Troubleshooting steps provided
  - [ ] Escalation path defined
  
- [ ] **Monitoring Configured**: Production monitoring ready
  - [ ] Alerts configured
  - [ ] Dashboards created
  - [ ] Log aggregation configured

---

### 11. Stakeholder Communication

- [ ] **Reviewers Assigned**: Appropriate reviewers assigned
- [ ] **Stakeholders Notified**: Relevant stakeholders informed
- [ ] **Demo Prepared**: Demo ready (if user-facing change)
- [ ] **Release Notes**: User-facing changes documented for release notes

---

### 12. Compliance & Governance

- [ ] **No Existing Tests Disabled**: All pre-existing tests still pass
- [ ] **No Tech Debt Without Documentation**: Any tech debt is documented in tech-debt.md
- [ ] **License Compliance**: All dependencies have acceptable licenses
- [ ] **Data Privacy**: GDPR/privacy requirements met (if handling PII)
- [ ] **Audit Trail**: Changes are traceable via CR and commits

---

## Category-Specific DoD Extensions

### For Features (in addition to Master DoD)

- [ ] **User Story Acceptance Criteria**: All acceptance criteria met
- [ ] **User Documentation**: User guide updated
- [ ] **Beta Testing**: Feature tested by beta users (if applicable)
- [ ] **Feature Flag**: Feature can be toggled on/off
- [ ] **Analytics**: Usage tracking configured
- [ ] **A/B Test Setup**: A/B test configured (if applicable)

---

### For Bug Fixes (in addition to Master DoD)

- [ ] **Root Cause Identified**: Root cause documented
- [ ] **Regression Test**: Test added to prevent recurrence
- [ ] **Related Bugs Checked**: Similar bugs identified and fixed
- [ ] **Issue Linked**: GitHub issue linked in PR
- [ ] **Issue Closed**: GitHub issue closed when merged

---

### For Refactoring (in addition to Master DoD)

- [ ] **Behavior Unchanged**: All existing tests still pass
- [ ] **No New Features**: Refactor doesn't add functionality
- [ ] **Metrics Improved**: Code quality metrics improved (complexity, duplication)
- [ ] **Tech Debt Reduced**: Tech debt item marked as resolved

---

### For Documentation (in addition to Master DoD)

- [ ] **Accuracy Verified**: Documentation matches actual behavior
- [ ] **Examples Tested**: All code examples work
- [ ] **Links Valid**: All links work
- [ ] **Spelling/Grammar**: Prose is well-written and clear
- [ ] **Diagrams Render**: All diagrams render correctly

---

### For Security Fixes (in addition to Master DoD)

- [ ] **Vulnerability Confirmed**: CVE or security advisory reviewed
- [ ] **Fix Verified**: Security scan confirms vulnerability resolved
- [ ] **No New Vulnerabilities**: Fix doesn't introduce new issues
- [ ] **Incident Report**: Security incident documented (if applicable)
- [ ] **Disclosure Coordinated**: Responsible disclosure followed (if applicable)

---

### For Performance Improvements (in addition to Master DoD)

- [ ] **Benchmark Results**: Performance improvements quantified
- [ ] **Before/After Metrics**: Baseline and improved metrics documented
- [ ] **No Regressions**: Other performance metrics unchanged
- [ ] **Load Testing**: Changes tested under load
- [ ] **Production Validation**: Performance improvement verified in production

---

## DoD Validation Process

### Self-Review (Developer)

1. **Before Requesting Review**: Developer completes full DoD checklist
2. **Evidence Gathered**: Screenshots, test results, metrics collected
3. **Checklist Updated**: PR description includes completed checklist

### Peer Review (Reviewer)

1. **DoD Verification**: Reviewer verifies checklist completion
2. **Spot Checks**: Reviewer samples evidence (tests, docs, code)
3. **Approval**: Reviewer approves only if DoD fully met

### Automated Checks (CI)

1. **Build & Test**: Automated tests execute
2. **Quality Gates**: Coverage, linting, security scans enforce standards
3. **Governance**: RTM and ADR presence validated
4. **Block Merge**: CI fails if any check fails

---

## DoD Exemptions

In rare cases, DoD items may be exempted. This requires:

1. **Exemption Request**: Document in `/docs/processes/exemptions/EX-NNNN.md`
2. **Justification**: Clear business or technical reason
3. **Approval**: Tech lead or architect approval
4. **Tech Debt**: Create tech debt item for missing DoD items
5. **Expiration**: Set deadline for completing exempted items

**Exemption Template**:
```markdown
# DoD Exemption: EX-NNNN

**CR**: CR-YYYY-MM-DD-XXX
**PR**: #NNN
**Date**: YYYY-MM-DD

## Exempted Items
- [ ] [DoD item description]
- [ ] [DoD item description]

## Justification
[Why is this exemption necessary?]

## Risk Assessment
[What are the risks?]

## Mitigation
[How will risks be mitigated?]

## Remediation Plan
- [ ] Step 1: [Action] by [Date]
- [ ] Step 2: [Action] by [Date]

**Tech Debt**: TD-NNNN

**Approved By**: [Name]
**Expiration**: [Date]
```

---

## DoD Anti-Patterns (What NOT to Do)

### ❌ "We'll fix it later"
- Unfinished work is not "Done"
- Create tech debt item if must ship incomplete

### ❌ "Tests slow us down"
- Tests are non-negotiable
- TDD is faster in the long run

### ❌ "Documentation can wait"
- Docs are code - they must be updated
- Outdated docs are worse than no docs

### ❌ "It's just a small change"
- Size doesn't matter - DoD always applies
- Small changes can have big impacts

### ❌ "We don't have time for quality"
- Quality is not optional
- Technical debt costs more later

### ❌ "The test is wrong, not the code"
- Tests are truth (unless requirement changed)
- Fix code, not tests

---

## Continuous Improvement

### DoD Retrospectives

Review DoD effectiveness quarterly:
- Are items preventing real issues?
- Are items too burdensome?
- Are new items needed?
- Can automation help?

### Metrics to Track

- **DoD Compliance Rate**: % of PRs meeting DoD on first review
- **Rework Rate**: % of PRs requiring changes after review
- **Escape Rate**: % of issues found in production
- **Time to Done**: Average time from start to Done

**Target Metrics**:
- DoD Compliance: > 80%
- Rework Rate: < 20%
- Escape Rate: < 5%

---

## Quick Reference Card

Print this and keep it visible:

```
═══════════════════════════════════════════════════
     DEFINITION OF DONE - QUICK CHECKLIST
═══════════════════════════════════════════════════

✅ REQUIREMENTS
   □ CR created & approved
   □ REQ-IDs in RTM
   □ ATP received

✅ CODE
   □ Tests first (Red)
   □ Code works (Green)
   □ Code clean (Refactor)
   □ Linter passes
   □ Reviewed & approved

✅ TESTING
   □ Coverage ≥ 80%
   □ All tests pass
   □ No flaky tests

✅ SECURITY
   □ No secrets
   □ Audit clean
   □ Inputs validated

✅ OBSERVABILITY
   □ Logs (JSON)
   □ Traces
   □ Metrics
   □ Health checks

✅ DOCS
   □ RTM updated
   □ ADR (if needed)
   □ README (if needed)
   □ API docs (if needed)

✅ CI/CD
   □ All checks pass
   □ No merge conflicts

✅ OPERATIONS
   □ Deployment plan
   □ Rollback plan
   □ Monitoring ready

═══════════════════════════════════════════════════
     NOT DONE = NOT MERGED
═══════════════════════════════════════════════════
```

---

## References

- [Change Management Process](/docs/processes/change-management.md)
- [Technical Debt Log](/docs/processes/tech-debt.md)
- [RTM](/docs/requirements/rtm.md)
- [ADR Template](/docs/arch/adr-template.md)
- [Copilot Instructions](/.github/copilot-instructions.md)

---

**End of Definition of Done v1.0.0**
