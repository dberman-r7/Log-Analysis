#!/bin/bash
# Generate CR Template with Next Sequential ID

set -e

# Get current date
YEAR=$(date +%Y)
MONTH=$(date +%m)
DAY=$(date +%d)
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

# Find existing CRs for today
CR_DIR="docs/processes/change-requests"
PATTERN="CR-${YEAR}-${MONTH}-${DAY}-"

# Find the highest number for today
HIGHEST=0
if [ -d "$CR_DIR" ]; then
    for file in "$CR_DIR"/$PATTERN*.md; do
        if [ -f "$file" ]; then
            NUM=$(basename "$file" | sed "s/${PATTERN}//" | sed 's/.md//')
            if [ "$NUM" -gt "$HIGHEST" ]; then
                HIGHEST=$NUM
            fi
        fi
    done
fi

# Calculate next number
NEXT=$((HIGHEST + 1))
NEXT_PADDED=$(printf "%03d" $NEXT)

# Generate CR-ID
CR_ID="CR-${YEAR}-${MONTH}-${DAY}-${NEXT_PADDED}"
CR_FILE="${CR_DIR}/${CR_ID}.md"

echo "Generating Change Request: ${CR_ID}"
echo "File: ${CR_FILE}"
echo ""

# Create CR file from template
cat > "$CR_FILE" << 'EOF'
# Change Request: CR_ID_PLACEHOLDER

**Status**: DRAFT

**Created**: TIMESTAMP_PLACEHOLDER
**Last Updated**: TIMESTAMP_PLACEHOLDER

---

## Basic Information

**Title**: [Brief description of the change]

**Requestor**: [Name/Email]

**Category**: [FEATURE | BUG | REFACTOR | SECURITY | PERFORMANCE | DOCUMENTATION | INFRASTRUCTURE]

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

**Downstream Impact** (will affect these):
- [Feature/CR: Description]

**External Dependencies**:
- [Third-party coordination required]

---

## Stakeholders

**Approver(s)**:
- [Name] - [Role] - [Approval Status]

**Implementer(s)**:
- [Name] - [Role]

**Reviewers**:
- [Name] - [Role]

---

## Approval Status

**Approved by**:
- [ ] Technical Lead: ____________ (Date: ______)
- [ ] Security Team: ____________ (Date: ______) [if security-related]
- [ ] Product Owner: ____________ (Date: ______) [if feature]

**Approval Token Received**: [PENDING | ATP | Approved to Proceed]
**Approval Date**: PENDING

---

## Impact Assessment

**Assessment Date**: TIMESTAMP_PLACEHOLDER
**Assessed By**: [Name]

### 1. Code Impact

**Scope**:
- **Files to Create**: N files
- **Files to Modify**: N files
- **Files to Delete**: N files

**Complexity Estimate**: [Low | Medium | High | Very High]

**Breaking Changes**: [YES | NO]

---

### 2. Security Impact

**Security Assessment**: [LOW | MEDIUM | HIGH | CRITICAL]

**Threat Model**:
- [List potential security threats]
- [Mitigation for each threat]

---

### 3. Performance Impact

**Performance Assessment**: [POSITIVE | NEUTRAL | NEGATIVE | UNKNOWN]

**Expected Changes**:
- **Latency**: [+/- XX ms or N/A]
- **Throughput**: [+/- XX req/s or N/A]

---

### 4. Testing Impact

**Test Strategy**: [Unit | Integration | E2E | All]

**New Tests Required**:
- **Unit Tests**: N tests
- **Integration Tests**: N tests

---

### 5. Documentation Impact

**Documentation Updates Required**:
- [ ] README.md
- [ ] RTM
- [ ] ADR
- [ ] Runbooks
- [ ] Other: _______

---

### 6. Operational Impact

**Deployment Requirements**:
- [ ] Standard deployment
- [ ] Database migration required
- [ ] Configuration changes required

**Rollback Plan**:
[How to rollback if issues occur]

---

### 7. Risk Assessment

**Overall Risk Level**: [LOW | MEDIUM | HIGH | CRITICAL]

**Identified Risks**:
1. **Risk**: [Description]
   - **Probability**: [Low | Medium | High]
   - **Impact**: [Low | Medium | High]
   - **Mitigation**: [How to mitigate]

---

### 8. Blast Radius Summary

**Blast Radius Size**: [SMALL | MEDIUM | LARGE | CRITICAL]

---

## Implementation Tracking

**Branch**: [feat/REQ-XXX-description]
**Pull Request**: [#NNN]
**Implementation Start**: [YYYY-MM-DD]
**Implementation End**: [YYYY-MM-DD]

---

## Change History

| Date | Status | Notes |
|------|--------|-------|
| TIMESTAMP_PLACEHOLDER | DRAFT | CR created |

---

**End of Change Request CR_ID_PLACEHOLDER**
EOF

# Replace placeholders
sed -i '' "s/CR_ID_PLACEHOLDER/${CR_ID}/g" "$CR_FILE"
sed -i '' "s/TIMESTAMP_PLACEHOLDER/${TIMESTAMP}/g" "$CR_FILE"

echo "✓ Change Request created: ${CR_FILE}"
echo ""
echo "Next steps:"
echo "1. Edit the CR file and fill in all sections"
echo "2. Perform Impact Assessment"
echo "3. Submit for approval"
echo "4. Wait for ATP (Approved to Proceed) before implementation"
echo ""
