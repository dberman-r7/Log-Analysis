# Implementation Plan: IMPL-[CR-ID]

**Related CR**: [CR-[ID]](/docs/processes/change-requests/CR-[ID].md)  
**Plan Version**: 1.0  
**Created**: YYYY-MM-DD  
**Last Updated**: YYYY-MM-DD

---

## Overview

**Objective**: [What this implementation achieves]  
**CR Summary**: [Brief summary of the change request]  
**Complexity**: [Low | Medium | High | Very High]  
**Estimated Duration**: [X hours/days]

---

## Prerequisites

**Before Starting Implementation**:
- [ ] CR approved and ATP token received
- [ ] Branch created: [branch-name]
- [ ] Development environment setup
- [ ] Required tools installed
- [ ] Dependencies updated
- [ ] Test data prepared (if applicable)

**Environment Setup Commands**:
```bash
# Example commands agent should run
cd /path/to/repository
git checkout -b [branch-name]
# Add any other setup commands
```

---

## Detailed Step-by-Step Instructions

> **For Agent Execution**: These instructions should be detailed enough that an AI agent can execute them independently with minimal ambiguity.

### Phase 1: Preparation

#### Step 1.1: Requirement Decomposition
**Goal**: Break CR into atomic requirements and update RTM

**Commands to Execute**:
```bash
# Open RTM for editing
vim /path/to/docs/requirements/rtm.md

# Or using edit tool
# Add new REQ-XXX entries to the requirements table
```

**Detailed Actions**:
1. Identify all atomic requirements from the CR
2. Assign sequential REQ-IDs (REQ-XXX format)
3. Add each to the RTM with:
   - Category (FUNC, NFR-PERF, NFR-SEC, etc.)
   - Description (clear, testable statement)
   - Status (start as PROPOSED or IN_PROGRESS)
   - Priority (P0-P3)
   - Link to this CR
4. Save and commit RTM changes

**Expected Outcome**:
- [ ] RTM contains all new requirements
- [ ] Each requirement has proper REQ-ID
- [ ] Requirements linked to CR-[ID]

---

#### Step 1.2: Write Failing Tests (TDD Red Phase)
**Goal**: Create tests that verify the requirements before implementation

**Files to Create/Modify**:
- `/path/to/tests/test_[component].py` (or appropriate test file)

**Detailed Actions**:
1. For each REQ-ID identified above, create corresponding test(s)
2. Test naming convention: `test_[requirement_description]`
3. Each test should:
   - Import necessary modules
   - Set up test fixtures
   - Execute the functionality to be implemented
   - Assert expected outcomes
   - Clean up resources

**Example Test Structure**:
```python
def test_req_xxx_description():
    """Test REQ-XXX: [Description]"""
    # Arrange
    test_input = [setup test data]
    
    # Act
    result = function_to_implement(test_input)
    
    # Assert
    assert result == expected_output
    assert [other conditions]
```

**Commands to Execute**:
```bash
# Run tests to verify they fail
pytest tests/test_[component].py -v

# Expected: Tests should FAIL because functionality not yet implemented
```

**Expected Outcome**:
- [ ] Tests written for all REQ-IDs
- [ ] Tests fail for the right reason (not implemented)
- [ ] Test coverage framework shows gaps

---

### Phase 2: Implementation (TDD Green Phase)

#### Step 2.1: Implement Core Functionality
**Goal**: Write minimum code to make tests pass

**Files to Create/Modify**:
- `/path/to/src/[component].py` (or appropriate source file)

**Detailed Actions**:
1. Create/modify the source file
2. Implement the minimum functionality needed
3. Follow existing code style and patterns
4. Add error handling
5. Add input validation

**Example Implementation**:
```python
def function_to_implement(input_data):
    """
    Implements REQ-XXX: [Description]
    
    Args:
        input_data: [Description]
    
    Returns:
        [Description]
    
    Raises:
        ValueError: [When]
    """
    # Input validation
    if not input_data:
        raise ValueError("Input cannot be empty")
    
    # Core logic
    result = [implement functionality]
    
    return result
```

**Commands to Execute**:
```bash
# Run tests to verify they pass
pytest tests/test_[component].py -v

# Expected: Tests should PASS
```

**Expected Outcome**:
- [ ] All tests pass
- [ ] Functionality implements all REQ-IDs
- [ ] Code follows project conventions

---

#### Step 2.2: Integration
**Goal**: Integrate new functionality with existing components

**Files to Modify**:
- [List specific integration points]

**Detailed Actions**:
1. Import new functionality in dependent modules
2. Update call sites to use new functions
3. Ensure backward compatibility (if required)
4. Update configuration files (if needed)

**Commands to Execute**:
```bash
# Run integration tests
pytest tests/integration/ -v

# Or run specific integration test
pytest tests/integration/test_[integration].py -v
```

**Expected Outcome**:
- [ ] Integration tests pass
- [ ] No breaking changes to existing functionality
- [ ] All components work together

---

### Phase 3: Quality & Refinement (TDD Refactor Phase)

#### Step 3.1: Code Refactoring
**Goal**: Improve code quality without changing behavior

**Detailed Actions**:
1. Eliminate code duplication
2. Improve variable and function naming
3. Extract complex logic into helper functions
4. Add type hints (if using Python 3.5+)
5. Optimize algorithms (if needed)

**Refactoring Checklist**:
- [ ] No duplicated code
- [ ] Clear, descriptive names
- [ ] Functions have single responsibility
- [ ] Complex logic is documented
- [ ] All tests still pass after refactoring

**Commands to Execute**:
```bash
# Re-run tests after each refactoring
pytest tests/ -v

# Run linter
pylint src/[component].py
# or
ruff check src/[component].py

# Run formatter
black src/[component].py
```

**Expected Outcome**:
- [ ] Code is clean and maintainable
- [ ] All tests still pass
- [ ] Linter passes with zero warnings
- [ ] Code formatted consistently

---

#### Step 3.2: Add Observability
**Goal**: Instrument code for monitoring and debugging

**Detailed Actions**:
1. Add structured logging at key points
2. Add metrics/counters for monitoring
3. Add tracing spans (if using OpenTelemetry)
4. Add health check support (if applicable)

**Example Logging**:
```python
import logging
import json

logger = logging.getLogger(__name__)

def function_to_implement(input_data):
    logger.info(
        json.dumps({
            "event": "function_start",
            "function": "function_to_implement",
            "input_size": len(input_data)
        })
    )
    
    try:
        result = [implementation]
        
        logger.info(
            json.dumps({
                "event": "function_success",
                "function": "function_to_implement",
                "result_size": len(result)
            })
        )
        
        return result
    except Exception as e:
        logger.error(
            json.dumps({
                "event": "function_error",
                "function": "function_to_implement",
                "error": str(e)
            })
        )
        raise
```

**Expected Outcome**:
- [ ] Key operations are logged
- [ ] Logs are structured (JSON)
- [ ] Errors are captured with context
- [ ] Metrics added where appropriate

---

### Phase 4: Documentation

#### Step 4.1: Update Documentation
**Goal**: Ensure all documentation reflects the changes

**Files to Update**:
- [ ] `/README.md` (if user-facing changes)
- [ ] `/docs/[relevant].md` (if architecture changes)
- [ ] Inline code comments (docstrings)
- [ ] API documentation (if API changes)

**Detailed Actions**:
1. Update README with new features/changes
2. Update architecture diagrams (if needed)
3. Add/update docstrings for all new functions
4. Update API documentation
5. Add examples if helpful

**Commands to Execute**:
```bash
# Generate API docs (if using tool)
# Example for Python:
pydoc-markdown

# Validate markdown links
markdown-link-check docs/**/*.md
```

**Expected Outcome**:
- [ ] All documentation is current
- [ ] Examples are working
- [ ] Links are valid
- [ ] Diagrams are updated

---

### Phase 5: Validation

#### Step 5.1: Comprehensive Testing
**Goal**: Verify all quality gates pass

**Commands to Execute**:
```bash
# Run all tests
pytest tests/ -v --cov=src --cov-report=term

# Verify coverage >= 80%
# Check output for coverage percentage

# Run linter
pylint src/
ruff check .

# Run formatter check
black --check .

# Run type checker (if applicable)
mypy src/

# Run security scan
bandit -r src/
# or
safety check
```

**Quality Gates**:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Code coverage ≥ 80%
- [ ] Linter passes (zero warnings)
- [ ] Formatter passes
- [ ] Type checker passes (if applicable)
- [ ] Security scan clean

**Expected Outcome**:
- [ ] All quality gates pass
- [ ] No new vulnerabilities introduced
- [ ] Code meets project standards

---

#### Step 5.2: Manual Verification
**Goal**: Manually test the changes work as expected

**Test Scenarios**:
1. [Scenario 1: Normal case]
   - Input: [Specific input]
   - Expected Output: [Specific output]
   - Actual Output: [To be filled during testing]

2. [Scenario 2: Edge case]
   - Input: [Specific input]
   - Expected Output: [Specific output]
   - Actual Output: [To be filled during testing]

3. [Scenario 3: Error case]
   - Input: [Invalid input]
   - Expected Output: [Error message]
   - Actual Output: [To be filled during testing]

**Commands to Execute**:
```bash
# Run the application manually
python src/main.py [args]

# Or start server and test endpoints
python src/server.py
curl http://localhost:8000/endpoint
```

**Expected Outcome**:
- [ ] All scenarios work as expected
- [ ] Error handling works correctly
- [ ] Performance is acceptable

---

### Phase 6: Pull Request Creation

#### Step 6.1: Prepare for PR
**Goal**: Ensure all changes are ready for review

**Commands to Execute**:
```bash
# Check git status
git status

# Review all changes
git diff

# Stage all changes
git add .

# Or stage selectively
git add [specific files]

# Commit with meaningful message
git commit -m "[CR-[ID]] Brief description of change"

# Push to remote
git push origin [branch-name]
```

**Pre-PR Checklist**:
- [ ] All changes committed
- [ ] Commit messages are clear
- [ ] No sensitive data in commits
- [ ] .gitignore excludes build artifacts
- [ ] Branch is up to date with main

**Expected Outcome**:
- [ ] Clean git history
- [ ] All changes pushed
- [ ] Ready for PR creation

---

#### Step 6.2: Create Pull Request
**Goal**: Create PR with complete information

**PR Information**:
- **Title**: `[CR-[ID]] [Brief description]`
- **Description**: Use PR template, include:
  - Link to CR document
  - Link to this Implementation Plan
  - Summary of changes
  - Testing performed
  - Definition of Done checklist

**Commands to Execute**:
```bash
# Create PR using GitHub CLI
gh pr create --title "[CR-[ID]] Brief description" --body-file pr-description.md

# Or create via web interface
gh pr view --web
```

**Expected Outcome**:
- [ ] PR created successfully
- [ ] All required information included
- [ ] Reviewers assigned
- [ ] CI/CD pipeline triggered

---

## Rollback Plan

**If Implementation Fails or Issues Arise**:

### Quick Rollback Steps
1. Identify the issue severity
2. If P0/P1: Execute immediate rollback
3. If P2/P3: Assess if hotfix or rollback needed

### Rollback Commands
```bash
# Option 1: Revert commits
git revert [commit-hash]
git push origin [branch-name]

# Option 2: Reset branch (if not merged)
git reset --hard origin/main
git push --force origin [branch-name]

# Option 3: Close PR and create new fix
gh pr close [pr-number]
```

**Time to Rollback**: [Estimated time]  
**Data Loss Risk**: [None | Low | Medium | High]

---

## Success Criteria

**Implementation is complete when**:
- [ ] All REQ-IDs from CR are implemented
- [ ] All tests pass (coverage ≥ 80%)
- [ ] All quality gates pass
- [ ] Documentation is updated
- [ ] PR is approved and merged
- [ ] Changes deployed to production (if applicable)
- [ ] Monitoring shows no issues
- [ ] CR status updated to COMPLETED

---

## Notes & Lessons Learned

**During Implementation** (update as you go):
- [Note 1: Any deviations from plan]
- [Note 2: Unexpected issues encountered]
- [Note 3: Solutions that worked well]

**Post-Implementation** (after completion):
- [Lesson 1: What went well]
- [Lesson 2: What could be improved]
- [Lesson 3: Recommendations for future]

---

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| YYYY-MM-DD | 1.0 | Initial plan created | [Name/Agent] |
| YYYY-MM-DD | 1.1 | [Updated section X based on feedback] | [Name/Agent] |
