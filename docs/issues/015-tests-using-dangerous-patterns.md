# Title: Fix tests that use dangerous patterns for validation

## Problem Description

Some unit tests use **dangerous code execution patterns** (like `exec()`, `eval()`, etc.) to test security validation. If the security validation itself has a bug, these tests will **actually execute the malicious code** instead of just testing the validation.

### Current Behavior

In `tests/unit/operations/test_filtering.py` (line 103):

```python
def test_dangerous_patterns_blocked():
    """Test that dangerous patterns are blocked."""
    dangerous_inputs = [
        "import os",
        "exec('print(1)')",
        "__import__('os').system('ls')",
        ...
    ]

    for pattern in dangerous_inputs:
        result = validate_condition(pattern)
        assert is_err(result)
```

**The Problem**: If `validate_condition()` has a bug and doesn't block these patterns, the test **passes the dangerous string to downstream code** which may execute it!

### Real-World Risk

**Scenario 1: Security validation bug**
```python
# Suppose validate_condition has a bug and misses "exec"
# The test calls:
result = validate_condition("exec('rm -rf /')")

# If validation fails (bug), the test continues
# and the string might be executed!
```

**Scenario 2: Test environment compromise**
```python
# Test runs:
validate_condition("__import__('os').system(' malicious_command ')")

# If validation fails, command executes on test machine
# Could steal test data, install malware, etc.
```

### Why This Happens

The tests assume validation **will** block dangerous patterns, but don't protect against the case where validation **fails** to block them. This creates a paradox:
- Tests need to use dangerous patterns to verify they're blocked
- But if they're NOT blocked, the test executes them

## Affected Files

- `tests/unit/operations/test_filtering.py`
- `tests/unit/operations/test_transforming.py`
- Any other test files that test security validation

## Proposed Solution

### Option 1: Mock the Execution (Recommended)

Instead of testing with real dangerous patterns, mock the execution:

```python
from unittest.mock import patch, MagicMock

def test_dangerous_patterns_blocked():
    """Test that dangerous patterns are blocked before execution."""

    dangerous_inputs = [
        "import os",
        "exec('print(1)')",
        "__import__('os').system('ls')",
    ]

    for pattern in dangerous_inputs:
        # Mock the actual execution function
        with patch('excel_toolkit.operations.filtering.pd.DataFrame.query') as mock_query:
            mock_query.side_effect = RuntimeError("Should not be called!")

            # Call validation
            result = validate_condition(pattern)

            # Verify validation failed
            assert is_err(result)

            # Verify query was NEVER called (pattern blocked)
            mock_query.assert_not_called()
```

### Option 2: Use Test-Specific Validator

Create a test-only version that doesn't execute:

```python
# test_helpers.py

class TestValidator:
    """Test-only validator that doesn't execute code."""

    def __init__(self):
        self.blocked_patterns = []

    def would_block(self, expression: str) -> bool:
        """Check if expression would be blocked (without executing)."""
        # Import the real validation logic
        from excel_toolkit.operations.filtering import DANGEROUS_PATTERNS

        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, expression.lower()):
                self.blocked_patterns.append(pattern)
                return True

        return False

# tests/unit/operations/test_filtering.py

def test_dangerous_patterns_blocked():
    """Test dangerous patterns are blocked."""

    validator = TestValidator()

    dangerous_inputs = [
        "import os",
        "exec('print(1)')",
        "__import__('os').system('ls')",
    ]

    for pattern in dangerous_inputs:
        # Check if would be blocked (no execution)
        blocked = validator.would_block(pattern)
        assert blocked, f"Pattern '{pattern}' should be blocked but wasn't"
```

### Option 3: Sandboxed Test Execution

Run tests in a sandboxed environment:

```python
import subprocess
import tempfile

def test_dangerous_patterns_blocked_sandboxed():
    """Test dangerous patterns in sandboxed process."""

    dangerous_inputs = [
        "import os",
        "exec('print(1)')",
    ]

    for pattern in dangerous_inputs:
        # Create test script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
            f.write(f"""
import sys
sys.path.insert(0, '.')

from excel_toolkit.operations.filtering import validate_condition
from excel_toolkit.fp import is_err

result = validate_condition("{pattern}")
if is_err(result):
    print("BLOCKED")
    sys.exit(0)
else:
    print("NOT_BLOCKED")
    sys.exit(1)
""")
            f.flush()

            # Run in subprocess with limited permissions
            result = subprocess.run(
                ['python', f.name],
                capture_output=True,
                timeout=5,  # Kill if hangs
                # Add sandbox restrictions:
                # - No network
                # - Limited filesystem access
                # - Limited CPU/memory
            )

            assert result.returncode == 0
            assert b"BLOCKED" in result.stdout
```

### Option 4: Use Safe Mock Patterns

Replace dangerous patterns with safe equivalents:

```python
# Instead of:
dangerous_inputs = [
    "exec('rm -rf /')",
    "__import__('os').system('ls')",
]

# Use:
safe_but_blocked_patterns = [
    "exec('safe_placeholder')",  # Contains 'exec' but safe
    "__import__('os').placeholder",  # Contains '__import__' but safe
]

# The validation should block based on pattern matching,
# not on whether the code is actually dangerous
```

## Additional Safeguards

### 1. Test Environment Isolation

```python
# conftest.py

import os

@pytest.fixture(autouse=True)
def isolate_test_environment():
    """Isolate tests to prevent side effects."""

    # Set restricted environment
    old_env = os.environ.copy()

    try:
        # Restrict dangerous environment variables
        os.environ.pop('PYTHONPATH', None)
        os.environ.pop('PATH', None)  # Prevent command execution

        yield

    finally:
        # Restore environment
        os.environ.clear()
        os.environ.update(old_env)
```

### 2. Timeout for All Tests

```python
# conftest.py

import pytest
import signal

from contextlib import contextmanager

@contextmanager
def time_limit(seconds):
    """Context manager to limit test execution time."""

    def signal_handler(signum, frame):
        raise TimeoutError("Test timed out")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        signal.alarm(0)

@pytest.fixture(autouse=True)
def limit_test_time():
    """Add timeout to all tests."""

    with time_limit(30):  # 30 second max per test
        yield
```

### 3. Warn in Test Documentation

```python
# tests/unit/operations/test_filtering.py

"""
Tests for filtering operations.

WARNING: This file tests security validation.
- Tests use patterns that LOOK dangerous but are MOCKED
- Never execute actual dangerous code
- Always mock execution functions
- If adding new security tests, follow patterns in test_dangerous_patterns_blocked()
"""
```

## Best Practices Going Forward

1. **Never execute dangerous code in tests**
2. **Always mock execution functions** when testing security
3. **Use test-specific validators** that check without executing
4. **Sandbox tests** that must execute code
5. **Add timeouts** to prevent hanging tests
6. **Document security test patterns** for future developers

## Migration Plan

1. Audit all test files for dangerous patterns
2. Replace with mocked/test-safe versions
3. Add test execution timeouts
4. Add documentation warnings
5. Add CI checks to prevent dangerous tests

## Related Issues

- eval() security vulnerability (#011)
- Missing integration tests (#014)
- Inconsistent security validation (#012)
