# TDD Requirements - Test-Driven Development

> Quick reference for TDD practices in this repository.
> Full details: #[[file:.github/copilot-instructions.md]]

---

## The Golden Rule

**Tests are written BEFORE implementation. No exceptions.**

If a test fails, the code is wrong (unless the requirement changed).

---

## The TDD Cycle

### 1. RED Phase: Write a Failing Test
- Test must fail for the right reason
- Test must be minimal and focused
- Test must clearly express the requirement

### 2. GREEN Phase: Write Minimum Code to Pass
- Do the simplest thing that could possibly work
- Don't optimize prematurely
- Get to green quickly

### 3. REFACTOR Phase: Improve Without Changing Behavior
- Eliminate duplication
- Improve naming and structure
- Maintain 100% test pass rate

---

## Test Commandments

### Thou Shalt:
1. Write unit tests for all new logic
2. Write integration tests for component interactions
3. Write end-to-end tests for critical user paths
4. Mock external dependencies appropriately
5. Use descriptive test names that explain "what" and "why"
6. Keep tests fast (unit tests < 100ms each)

### Thou Shalt Not:
1. **NEVER** "fix the test" to match broken code
2. **NEVER** skip tests to "move faster"
3. **NEVER** commit code with failing tests
4. **NEVER** disable tests without documenting why
5. **NEVER** write tests that depend on execution order

---

## Coverage Requirements

**Minimum Standards**:
- Unit Test Coverage: ≥ 80% (line coverage)
- Branch Coverage: ≥ 75%
- Critical Path Coverage: 100%

**Pre-Merge Check**:
- Coverage must not decrease from baseline
- New code must meet 80% threshold
- CI will fail if coverage drops

---

## The Only Valid Reasons to Modify a Failing Test

1. **The requirement itself has changed** (documented in updated REQ-ID)
2. **The test has a bug** (prove with another test)
3. **The test is flaky** (fix flakiness, don't delete test)

---

## Forbidden Actions

❌ Changing test assertions to match new (wrong) behavior
❌ Commenting out failing tests
❌ Widening test tolerances to mask failures
❌ Removing tests because they're "too strict"

---

## Test Structure: Arrange-Act-Assert

```python
def test_feature_does_something():
    # ARRANGE: Set up test data and conditions
    input_data = create_test_data()
    expected_result = calculate_expected()
    
    # ACT: Execute the code under test
    actual_result = feature_under_test(input_data)
    
    # ASSERT: Verify the outcome
    assert actual_result == expected_result
```

---

## Test Naming Convention

Use descriptive names that explain the scenario:

```python
# ✅ GOOD
def test_parse_log_with_missing_timestamp_raises_validation_error():
    ...

def test_api_client_retries_on_rate_limit_with_exponential_backoff():
    ...

# ❌ BAD
def test_parser():
    ...

def test_api_1():
    ...
```

---

## Coverage Exemptions

Must be justified in code comments:

```python
# pragma: no cover - justification required
def legacy_integration_code():
    # Reason: External system unavailable in test environment
    # TD-0042: Add integration test harness
    pass
```

---

## Quick TDD Workflow

```
1. Write failing test (RED)
   └─ Run test → Verify it fails for right reason
   
2. Write minimal code (GREEN)
   └─ Run test → Verify it passes
   
3. Refactor (REFACTOR)
   └─ Run all tests → Verify 100% pass rate
   
4. Repeat for next requirement
```

---

## Common TDD Patterns

### Test Fixtures (pytest)

```python
@pytest.fixture
def sample_log_data():
    return {
        "timestamp": "2026-02-19T10:00:00Z",
        "level": "INFO",
        "message": "Test log entry"
    }

def test_parser_handles_valid_log(sample_log_data):
    result = parse_log(sample_log_data)
    assert result.is_valid
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch

def test_api_client_handles_network_error():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = ConnectionError("Network unreachable")
        
        client = APIClient()
        with pytest.raises(NetworkError):
            client.fetch_data()
```

### Parameterized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("valid_input", True),
    ("invalid_input", False),
    ("", False),
    (None, False),
])
def test_validation_with_various_inputs(input, expected):
    assert validate(input) == expected
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term

# Run specific test file
pytest tests/test_parser.py

# Run specific test
pytest tests/test_parser.py::test_parse_valid_log

# Run with verbose output
pytest -v

# Run fast (skip slow tests)
pytest -m "not slow"
```

---

## Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_api_client.py       # Unit tests for API client
├── test_parser.py           # Unit tests for parser
├── test_service.py          # Unit tests for service
├── integration/             # Integration tests
│   ├── test_end_to_end.py
│   └── test_api_integration.py
└── fixtures/                # Test data
    ├── sample_logs.json
    └── mock_responses.json
```

---

## For AI Agents: TDD Checklist

Before writing implementation code:

- [ ] Requirement is clear and testable
- [ ] Test case written and failing (RED)
- [ ] Test fails for the right reason
- [ ] Test is minimal and focused

After writing implementation:

- [ ] Test passes (GREEN)
- [ ] All other tests still pass
- [ ] Coverage meets threshold
- [ ] Code is refactored (REFACTOR)

---

**Last Updated**: 2026-02-19
