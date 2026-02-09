# Technical Debt Log

> **Version:** 1.0.0  
> **Last Updated:** 2026-02-09  
> **Owner:** Engineering Team

This document tracks all technical debt in the system - compromises made for speed, temporary solutions, and areas needing improvement.

---

## What is Technical Debt?

Technical debt is the implied cost of additional rework caused by choosing an easy (limited) solution now instead of using a better approach that would take longer.

**Types of Technical Debt**:
- **Design Debt**: Suboptimal architecture or design patterns
- **Code Quality Debt**: Poor code quality, duplication, complexity
- **Testing Debt**: Missing tests, low coverage, flaky tests
- **Documentation Debt**: Missing or outdated documentation
- **Security Debt**: Known vulnerabilities or security weaknesses
- **Performance Debt**: Known performance issues or bottlenecks

---

## Debt Categories and Urgency

### Zero-Tolerance Debt (Must Fix Before Merge)

These **MUST** be resolved before code is merged:
- Security vulnerabilities (HIGH or CRITICAL)
- Data corruption risks
- Silent failure modes
- Memory leaks
- Resource exhaustion issues

### Document-and-Schedule Debt (Fix Within 2 Sprints)

These must be documented and scheduled for resolution:
- Performance degradations > 20% from baseline
- Test coverage < 80%
- Missing critical documentation
- Moderate security vulnerabilities
- Breaking changes to internal APIs

### Backlog Debt (Prioritize in Roadmap)

These should be tracked and prioritized in the product backlog:
- Refactoring opportunities
- Design improvements
- Developer experience enhancements
- Minor performance optimizations
- Nice-to-have features

---

## Technical Debt Register

### Active Debt Items

---

#### TD-001: Example Technical Debt Item

**Status**: ACTIVE  
**Category**: CODE_QUALITY  
**Priority**: P2  
**Estimated Effort**: M (Medium)

**Date Added**: 2026-02-09  
**Added By**: System  
**Target Resolution**: 2026-04-09

##### Context
[This is an example entry showing the format. Replace with actual technical debt items.]

Example: During rapid prototyping, we implemented a quick-and-dirty CSV parser that doesn't handle edge cases properly. This was acceptable for the MVP but needs to be replaced with a robust solution.

##### Impact
- **Current State**: Manual testing required for each CSV import
- **Risk**: Data corruption possible with malformed CSV files
- **User Impact**: Users may experience import failures
- **Developer Impact**: Difficult to maintain and extend

**Blast Radius**: MEDIUM
- Affects CSV import module only
- Used by 3 different features
- ~500 lines of code

##### Technical Details
- **File**: `/src/parsers/csv_parser.py`
- **Lines**: 45-200
- **Dependencies**: None (standalone)
- **Complexity**: [cyclomatic complexity = 15]

##### Repayment Strategy

**Approach**: Replace with well-tested library or rewrite with proper error handling

**Steps**:
- [ ] Research suitable CSV parsing libraries
- [ ] Create ADR for library selection
- [ ] Write comprehensive tests for edge cases
- [ ] Implement new parser
- [ ] Migrate existing code
- [ ] Deprecate old parser
- [ ] Remove old code after 1 sprint grace period

**Estimated Timeline**: 2 weeks

**Dependencies**: None

**Breaking Changes**: Yes - API signature will change
- Migration guide required
- Deprecation notice: 1 sprint

##### Related Items
- **ADR**: None yet (will create: ADR-NNNN)
- **REQ**: REQ-001 (CSV parsing requirement)
- **CR**: None (will create when scheduled)
- **Issues**: #42

##### Metrics

**Business Impact**:
- Support tickets: 5 per month related to CSV issues
- User frustration: Medium
- Revenue impact: None

**Technical Impact**:
- Maintenance cost: 4 hours per month
- Bug frequency: 2-3 per sprint
- Test coverage: 45% (below threshold)

---

### Resolved Debt Items

---

#### TD-000: Example Resolved Item

**Status**: RESOLVED  
**Category**: PERFORMANCE  
**Priority**: P1  
**Effort**: L (Large)

**Date Added**: 2026-01-15  
**Date Resolved**: 2026-02-01  
**Resolution Time**: 17 days

**Context**: Database queries were performing full table scans.

**Solution**: Added indexes on frequently queried columns.

**Results**:
- Query time reduced from 5s to 50ms (90% improvement)
- User satisfaction increased
- Zero regression issues

**Lessons Learned**:
- Always profile database queries before deployment
- Add performance tests to CI pipeline
- Monitor query performance in production

---

## Debt by Category

### Design Debt

| TD-ID | Description | Priority | Effort | Status |
|-------|-------------|----------|--------|--------|
| - | No items yet | - | - | - |

**Total Design Debt**: 0 items

---

### Code Quality Debt

| TD-ID | Description | Priority | Effort | Status |
|-------|-------------|----------|--------|--------|
| TD-001 | CSV parser needs refactoring | P2 | M | ACTIVE |

**Total Code Quality Debt**: 1 item

---

### Testing Debt

| TD-ID | Description | Priority | Effort | Status |
|-------|-------------|----------|--------|--------|
| - | No items yet | - | - | - |

**Total Testing Debt**: 0 items

---

### Documentation Debt

| TD-ID | Description | Priority | Effort | Status |
|-------|-------------|----------|--------|--------|
| - | No items yet | - | - | - |

**Total Documentation Debt**: 0 items

---

### Security Debt

| TD-ID | Description | Priority | Effort | Status |
|-------|-------------|----------|--------|--------|
| - | No items yet | - | - | - |

**Total Security Debt**: 0 items

---

### Performance Debt

| TD-ID | Description | Priority | Effort | Status |
|-------|-------------|----------|--------|--------|
| - | No items yet | - | - | - |

**Total Performance Debt**: 0 items

---

## Debt Metrics and Reporting

### Summary Statistics

**As of**: 2026-02-09

**Active Debt**:
- Total Items: 1
- High Priority (P0-P1): 0
- Medium Priority (P2): 1
- Low Priority (P3): 0

**By Category**:
- Design: 0
- Code Quality: 1
- Testing: 0
- Documentation: 0
- Security: 0
- Performance: 0

**By Effort**:
- Small (< 1 day): 0
- Medium (1-3 days): 1
- Large (4-7 days): 0
- X-Large (> 1 week): 0

**Debt Trends**:
- Items Added This Month: 1
- Items Resolved This Month: 0
- Net Change: +1

### Debt Ratio

```
Debt Ratio = (Estimated Effort to Resolve All Debt) / (Total Development Capacity per Sprint)

Current Debt Ratio: 0.15 (15%)
Target Debt Ratio: < 0.20 (20%)
Status: HEALTHY
```

### Burn-Down Progress

| Sprint | Opened | Closed | Net Change | Total Debt |
|--------|--------|--------|------------|------------|
| 2026-02 | 1 | 0 | +1 | 1 |

---

## Governance and Process

### When to Create a Tech Debt Item

Create a TD entry when:
1. You make a conscious compromise for speed
2. You discover suboptimal existing code
3. A security scan reveals a vulnerability you can't fix immediately
4. Test coverage falls below threshold
5. Documentation becomes outdated
6. Performance degrades below SLO

### How to Create a Tech Debt Item

1. Assign next available TD-ID (TD-NNN)
2. Choose category
3. Set priority based on impact
4. Estimate effort (S/M/L/XL)
5. Document context and impact
6. Create repayment strategy
7. Link related items (REQ, ADR, CR)
8. Add to appropriate category table
9. Update summary metrics

### Debt Review Cadence

**Weekly**: Review new debt items in sprint planning
**Monthly**: Review debt metrics and trends
**Quarterly**: Strategic debt reduction planning

### Debt Reduction Strategies

**Strategy 1: Dedicated Debt Sprints**
- Allocate 1 sprint per quarter to debt reduction
- Target high-impact items first

**Strategy 2: Incremental Cleanup**
- Reserve 20% of each sprint for debt reduction
- "Scout Rule": Leave code better than you found it

**Strategy 3: Debt Gardening**
- Assign debt ownership to teams/individuals
- Regular debt grooming sessions

**Strategy 4: Zero-Tolerance Categories**
- Security and data corruption issues: Fix immediately
- Never accumulate zero-tolerance debt

---

## Debt Repayment Guidelines

### Prioritization Framework

Use this matrix to prioritize debt repayment:

**Impact vs. Effort**:

```
High Impact, Low Effort    -> DO FIRST (Quick wins)
High Impact, High Effort   -> DO SECOND (Strategic)
Low Impact, Low Effort     -> DO THIRD (Fill capacity)
Low Impact, High Effort    -> DO LAST (Avoid if possible)
```

### Repayment Process

1. **Schedule**: Add to sprint backlog
2. **Plan**: Create or reference CR for the work
3. **Implement**: Follow standard TDD process
4. **Validate**: Ensure debt is fully resolved
5. **Document**: Update TD entry to RESOLVED
6. **Learn**: Document lessons learned

---

## Templates

### New Tech Debt Entry Template

Copy this template to add a new debt item:

```markdown
---

#### TD-NNN: [Brief Description]

**Status**: ACTIVE
**Category**: [DESIGN | CODE_QUALITY | TESTING | DOCUMENTATION | SECURITY | PERFORMANCE]
**Priority**: [P0 | P1 | P2 | P3]
**Estimated Effort**: [S | M | L | XL]

**Date Added**: YYYY-MM-DD
**Added By**: [Name]
**Target Resolution**: YYYY-MM-DD

##### Context
[Why was the compromise made? What were the circumstances?]

##### Impact
- **Current State**: [Describe current situation]
- **Risk**: [What could go wrong?]
- **User Impact**: [How does this affect users?]
- **Developer Impact**: [How does this affect developers?]

**Blast Radius**: [SMALL | MEDIUM | LARGE | CRITICAL]

##### Technical Details
- **File**: [File path]
- **Lines**: [Line numbers]
- **Dependencies**: [What depends on this?]
- **Complexity**: [Metrics if available]

##### Repayment Strategy

**Approach**: [High-level approach to resolve]

**Steps**:
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

**Estimated Timeline**: [Duration]

**Dependencies**: [What must be done first?]

**Breaking Changes**: [YES | NO]
- [Details if yes]

##### Related Items
- **ADR**: [Link or "None"]
- **REQ**: [Link or "None"]
- **CR**: [Link or "None"]
- **Issues**: [Link or "None"]

##### Metrics

**Business Impact**:
- [Relevant business metrics]

**Technical Impact**:
- [Relevant technical metrics]

---
```

---

## Exemptions and Acceptance

Some technical debt may be acceptable or unavoidable. Document these with justification.

### Accepted Debt (Won't Fix)

| TD-ID | Reason | Accepted By | Date |
|-------|--------|-------------|------|
| - | No items yet | - | - |

**Criteria for Accepting Debt**:
- Cost to fix exceeds benefit
- Component will be deprecated soon
- No user or business impact
- Workaround is sufficient
- External constraint (vendor, platform, etc.)

---

## Dashboard and Visualization

### Debt Heat Map

```
Category        | P0 | P1 | P2 | P3 | Total |
----------------|----|----|----|----|-------|
Design          |  0 |  0 |  0 |  0 |   0   |
Code Quality    |  0 |  0 |  1 |  0 |   1   |
Testing         |  0 |  0 |  0 |  0 |   0   |
Documentation   |  0 |  0 |  0 |  0 |   0   |
Security        |  0 |  0 |  0 |  0 |   0   |
Performance     |  0 |  0 |  0 |  0 |   0   |
----------------|----|----|----|----|-------|
Total           |  0 |  0 |  1 |  0 |   1   |
```

### Effort Distribution

```
Effort Size | Count | Total Days |
------------|-------|------------|
Small       |   0   |     0      |
Medium      |   1   |     2      |
Large       |   0   |     0      |
X-Large     |   0   |     0      |
------------|-------|------------|
Total       |   1   |     2      |
```

---

## Continuous Improvement

### Lessons Learned

Track patterns in technical debt to prevent recurrence:

**Common Debt Causes**:
1. Time pressure leading to shortcuts
2. Incomplete understanding of requirements
3. Lack of upfront design
4. Missing or inadequate testing
5. Poor code review practices

**Prevention Strategies**:
1. Better estimation and planning
2. Mandatory design phase for complex features
3. Enforce TDD and coverage thresholds
4. Strengthen code review checklist
5. Regular architecture reviews

### Process Improvements

Document improvements to the debt management process:

| Date | Improvement | Impact |
|------|-------------|--------|
| 2026-02-09 | Created tech debt log | Improved visibility |

---

## References

- [Change Management Process](/docs/processes/change-management.md)
- [Definition of Done](/docs/processes/definition-of-done.md)
- [RTM](/docs/requirements/rtm.md)
- [ADR Template](/docs/arch/adr-template.md)

---

**End of Technical Debt Log v1.0.0**
