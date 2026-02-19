# Decision Tree: Which Definition of Done (DoD) Items Apply?

> Use this guide to determine which DoD checklist items are relevant for your specific change type.

---

## Master DoD Checklist

All changes must complete these core items:

### Universal Items (Apply to ALL changes)

- [ ] **Feature Branch Used**: All changes on feature branch (no direct commits to `main`)
- [ ] **Branch Named Correctly**: `feat/REQ-XXX-...` or `fix/Issue-NNN-...` or `docs/...`
- [ ] **PR Created**: Pull request created with proper template
- [ ] **PR Title Correct**: `[CR-YYYY-MM-DD-XXX]` or `[REQ-XXX]` or `[BUG]` format
- [ ] **Code Review Complete**: At least one approval from qualified reviewer
- [ ] **All Review Comments Addressed**: No unresolved review threads
- [ ] **No Merge Conflicts**: Branch is up to date with main
- [ ] **CI Passes**: All CI checks pass

---

## Change Type Selector

Select your change type to see applicable DoD items:

1. [Feature (New Functionality)](#feature-new-functionality)
2. [Bug Fix](#bug-fix)
3. [Refactoring](#refactoring)
4. [Documentation Only](#documentation-only)
5. [Security Fix](#security-fix)
6. [Performance Improvement](#performance-improvement)
7. [Dependency Update](#dependency-update)
8. [Configuration Change](#configuration-change)

---

## Feature (New Functionality)

### Requirements & Planning
- [ ] Requirements documented in RTM with REQ-IDs
- [ ] CR created and approved (if CR-required triggers met)
- [ ] Impact Assessment complete (if CR-required)
- [ ] Implementation Plan created
- [ ] ATP received (if CR-required)

### Code Quality
- [ ] Tests written first (TDD Red)
- [ ] Implementation complete (TDD Green)
- [ ] Code refactored (TDD Refactor)
- [ ] Linter passes (zero warnings)
- [ ] Formatter passes
- [ ] Type checker passes (if applicable)
- [ ] Code complexity acceptable (< 10 cyclomatic complexity)

### Testing
- [ ] Unit tests for all new logic
- [ ] Integration tests for component interactions
- [ ] E2E tests for critical user paths (if applicable)
- [ ] Test coverage ≥ 80%
- [ ] All tests pass (100% pass rate)
- [ ] No flaky tests

### Security
- [ ] No hardcoded secrets
- [ ] Environment variables for all secrets
- [ ] Input validation implemented
- [ ] Output encoding implemented
- [ ] Dependency audit clean (no HIGH/CRITICAL)
- [ ] Security scan passes

### Performance
- [ ] Performance baseline documented
- [ ] Performance tests executed
- [ ] SLO compliance verified
- [ ] No performance regression
- [ ] No resource leaks

### Observability
- [ ] Structured logging (JSON format)
- [ ] OpenTelemetry tracing added
- [ ] Metrics exposed
- [ ] Health checks updated
- [ ] Alerts configured (if applicable)

### Documentation
- [ ] RTM updated
- [ ] ADR created (if architectural)
- [ ] Diagrams updated (if applicable)
- [ ] README updated (if applicable)
- [ ] API documentation updated (if applicable)
- [ ] Code comments for complex logic
- [ ] CHANGELOG updated

### Operational Readiness
- [ ] Deployment plan documented
- [ ] Rollback plan documented
- [ ] Configuration changes documented
- [ ] Support team briefed (if needed)
- [ ] Monitoring configured

### Feature-Specific
- [ ] User story acceptance criteria met
- [ ] User documentation updated
- [ ] Feature flag configured (if applicable)
- [ ] Analytics tracking configured (if applicable)

---

## Bug Fix

### Requirements & Planning
- [ ] Root cause identified and documented
- [ ] Mapped to existing REQ-ID
- [ ] Implementation Plan created (if code changes)
- [ ] Issue linked in PR

### Code Quality
- [ ] Tests written first (TDD Red) - regression test
- [ ] Bug fixed (TDD Green)
- [ ] Code refactored (TDD Refactor)
- [ ] Linter passes
- [ ] Formatter passes

### Testing
- [ ] Regression test added to prevent recurrence
- [ ] Related bugs checked and fixed
- [ ] Test coverage maintained or improved
- [ ] All tests pass

### Security
- [ ] No hardcoded secrets
- [ ] Dependency audit clean (if dependencies changed)
- [ ] Security scan passes

### Documentation
- [ ] RTM updated (if implementation details changed)
- [ ] Code comments explain fix
- [ ] Issue closed when merged

### Bug-Specific
- [ ] Similar bugs identified and addressed
- [ ] Root cause analysis documented

---

## Refactoring

### Requirements & Planning
- [ ] Implementation Plan created
- [ ] Refactoring goal documented

### Code Quality
- [ ] Behavior unchanged (all existing tests still pass)
- [ ] No new features added
- [ ] Linter passes
- [ ] Formatter passes
- [ ] Code complexity reduced
- [ ] Duplication eliminated

### Testing
- [ ] All existing tests pass (100%)
- [ ] Test coverage maintained or improved
- [ ] No tests modified (unless improving test quality)

### Security
- [ ] No hardcoded secrets
- [ ] Security scan passes

### Documentation
- [ ] Code comments updated
- [ ] RTM updated (if implementation details changed)

### Refactoring-Specific
- [ ] Metrics improved (complexity, duplication, etc.)
- [ ] Tech debt item marked as resolved (if applicable)

---

## Documentation Only

### Requirements & Planning
- [ ] No implementation plan required (pure docs)

### Documentation Quality
- [ ] Accuracy verified (matches actual behavior)
- [ ] Examples tested (all code examples work)
- [ ] Links valid (all links work)
- [ ] Spelling/grammar checked
- [ ] Diagrams render correctly

### Documentation-Specific
- [ ] No code changes (if code changed, not "documentation only")
- [ ] RTM updated (if requirements docs changed)

---

## Security Fix

### Requirements & Planning
- [ ] Vulnerability confirmed (CVE or security advisory reviewed)
- [ ] Implementation Plan created
- [ ] Security team notified

### Code Quality
- [ ] Tests written first (TDD Red)
- [ ] Fix implemented (TDD Green)
- [ ] Code refactored (TDD Refactor)
- [ ] Linter passes
- [ ] Formatter passes

### Testing
- [ ] Security test added
- [ ] All tests pass
- [ ] Test coverage ≥ 80%

### Security
- [ ] Fix verified (security scan confirms vulnerability resolved)
- [ ] No new vulnerabilities introduced
- [ ] Dependency audit clean
- [ ] No hardcoded secrets

### Documentation
- [ ] Security incident documented (if applicable)
- [ ] RTM updated
- [ ] Runbook updated (if applicable)

### Security-Specific
- [ ] Responsible disclosure followed (if applicable)
- [ ] Incident report created (if applicable)
- [ ] Related vulnerabilities checked

---

## Performance Improvement

### Requirements & Planning
- [ ] Implementation Plan created
- [ ] Performance goal documented

### Code Quality
- [ ] Tests written first (TDD Red)
- [ ] Optimization implemented (TDD Green)
- [ ] Code refactored (TDD Refactor)
- [ ] Linter passes
- [ ] Formatter passes

### Testing
- [ ] All tests pass
- [ ] Test coverage maintained

### Security
- [ ] No hardcoded secrets
- [ ] Security scan passes

### Performance
- [ ] Benchmark results documented
- [ ] Before/after metrics documented
- [ ] Performance improvement quantified
- [ ] No other performance regressions
- [ ] Load testing completed

### Documentation
- [ ] RTM updated
- [ ] Performance metrics documented

### Performance-Specific
- [ ] Baseline metrics captured
- [ ] Target metrics achieved
- [ ] Production validation plan

---

## Dependency Update

### Requirements & Planning
- [ ] Implementation Plan created
- [ ] Update reason documented (security, features, bug fixes)

### Code Quality
- [ ] Tests pass with new dependency version
- [ ] Linter passes
- [ ] Formatter passes

### Testing
- [ ] All tests pass
- [ ] Integration tests verify compatibility
- [ ] Test coverage maintained

### Security
- [ ] Dependency audit clean
- [ ] No new vulnerabilities introduced
- [ ] Security scan passes
- [ ] License compliance checked

### Documentation
- [ ] CHANGELOG updated
- [ ] Breaking changes documented (if any)
- [ ] Migration guide provided (if breaking changes)

### Dependency-Specific
- [ ] Change notes reviewed
- [ ] Breaking changes assessed
- [ ] Compatibility verified

---

## Configuration Change

### Requirements & Planning
- [ ] Implementation Plan created
- [ ] Configuration change documented

### Code Quality
- [ ] Tests updated for new configuration
- [ ] Linter passes

### Testing
- [ ] Configuration validated
- [ ] All tests pass with new configuration
- [ ] Edge cases tested

### Security
- [ ] No hardcoded secrets
- [ ] Secrets in environment variables or secret manager
- [ ] Security scan passes

### Documentation
- [ ] Configuration documented
- [ ] Environment-specific configs noted
- [ ] Deployment guide updated

### Operational Readiness
- [ ] Deployment plan includes configuration steps
- [ ] Rollback plan includes configuration revert
- [ ] Configuration changes coordinated

### Configuration-Specific
- [ ] Default values appropriate
- [ ] Validation rules implemented
- [ ] Configuration tested in all environments

---

## Quick Selector Matrix

| Change Type | Tests Required | Security Scan | Performance Tests | Documentation | Observability |
|-------------|----------------|---------------|-------------------|---------------|---------------|
| Feature | ✅ Yes (TDD) | ✅ Yes | ✅ Yes | ✅ Full | ✅ Yes |
| Bug Fix | ✅ Yes (Regression) | ✅ Yes | ⚠️ If perf-related | ⚠️ Minimal | ⚠️ If needed |
| Refactoring | ✅ Yes (Existing) | ✅ Yes | ⚠️ No regression | ⚠️ Code comments | ❌ No |
| Documentation | ❌ No | ❌ No | ❌ No | ✅ Full | ❌ No |
| Security Fix | ✅ Yes (Security) | ✅ Yes | ⚠️ If needed | ✅ Full | ⚠️ If needed |
| Performance | ✅ Yes (TDD) | ✅ Yes | ✅ Yes | ✅ Metrics | ⚠️ If needed |
| Dependency | ✅ Yes (Existing) | ✅ Yes | ⚠️ Verify no regression | ⚠️ Changelog | ❌ No |
| Configuration | ✅ Yes (Config) | ✅ Yes | ⚠️ If needed | ✅ Config docs | ❌ No |

**Legend**:
- ✅ Required
- ⚠️ Conditional (depends on specific change)
- ❌ Not required

---

## Related Documentation

- **Full DoD Checklist**: `docs/processes/definition-of-done.md`
- **Change Management**: `docs/processes/change-management.md`
- **TDD Requirements**: `.kiro/steering/tdd-requirements.md`
- **Security Requirements**: `.kiro/steering/security-requirements.md`

---

**Last Updated**: 2026-02-19
