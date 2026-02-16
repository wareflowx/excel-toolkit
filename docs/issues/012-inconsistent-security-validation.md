# Title: Fix inconsistent security validation between filtering and transforming

## Problem Description

The filtering and transforming operations use **different security validation approaches**, creating inconsistent security guarantees and potential gaps that could be exploited.

### Current Behavior

**Filtering** (`excel_toolkit/operations/filtering.py`):
- Uses **pattern matching** with regex for dangerous patterns
- Checks for: `import`, `exec`, `eval`, `__`, `open(`, `file(`, `os.`, `sys.`, etc.
- Validation happens before query execution

**Transforming** (`excel_toolkit/operations/transforming.py`):
- Uses **regex validation** for dangerous patterns
- Checks for similar but not identical patterns
- Uses `eval()` for expression evaluation
- Has additional patterns like `compile`, `getattr`, `setattr`, `globals`, `locals`

### The Inconsistency Problem

```python
# filtering.py - Line 33-44
DANGEROUS_PATTERNS = [
    r"\w+\s*[=!<>]+\s*[\w'\"]+",  # Comparisons
    r"\w+\s+in\s+\[[^\]]+\]",       # in operator
    r"\w+\.isna\(\)",               # Null check
    ...
]

# transforming.py - Line 29-46
DANGEROUS_PATTERNS = [
    r'\bimport\b',
    r'\bexec\b',
    r'\beval\b',
    r'\b__',
    r'\\_|__',
    ...
]
```

The patterns are **different formats**, **different scopes**, and **different implementations**.

### Security Risks

1. **Different patterns blocked**: An attack vector blocked in one module might work in another
2. **Different validation approaches**: Pattern matching vs regex means different bypass techniques
3. **No unified security policy**: Each module implements its own idea of "safe"
4. **Maintenance burden**: Security updates need to be applied in multiple places

### Real-World Example

```python
# Filter operation:
xl filter data.xlsx "column == 'value' and 1/0"  # May pass or fail depending on regex

# Transform operation:
xl transform data.xlsx --expr "column * (1/0)"  # Different behavior

# Attacker could test which module allows what
```

## Affected Files

- `excel_toolkit/operations/filtering.py` (lines 33-44, 65-130)
- `excel_toolkit/operations/transforming.py` (lines 29-46, 49-84)
- Potentially other operations that evaluate user input

## Proposed Solution

### Create Unified Security Validation Module

```python
# excel_toolkit/core/security.py

"""Unified security validation for all user-provided expressions."""

import re
from typing import List, Tuple

# Centralized dangerous patterns
DANGEROUS_PATTERNS: List[Tuple[str, str]] = [
    (r'\bimport\b', "import statements"),
    (r'\bexec\b', "exec function"),
    (r'\beval\b', "eval function"),
    (r'\b__', "dunder methods"),
    (r'\borg\.', "os module"),
    (r'\bsys\.', "sys module"),
    (r'\bos\.', "os module"),
    (r'\bopen\b', "file operations"),
    (r'\bcompile\b', "compile function"),
    (r'\bgetattr\b', "getattr function"),
    (r'\bsetattr\b', "setattr function"),
    (r'\b__class__\b', "class introspection"),
    (r'\b__base__\b', "base class access"),
    (r'\b__subclasses__\b', "subclass access"),
    (r'\bglobals\b', "globals access"),
    (r'\blocals\b', "locals access"),
    (r'\bvars\b', "vars access"),
    (r'\blambda\b', "lambda expressions"),
    (r'\[.*for.*in.*\]', "list comprehensions"),
]

class SecurityValidationError(Exception):
    """Security validation failed."""
    def __init__(self, expression: str, reason: str):
        self.expression = expression
        self.reason = reason
        super().__init__(f"Security violation: {reason}")

def validate_user_input(expression: str, context: str = "expression") -> None:
    """
    Validate user-provided input for security issues.

    Args:
        expression: User-provided input to validate
        context: Context (for error messages)

    Raises:
        SecurityValidationError: If input contains dangerous patterns

    Examples:
        >>> validate_user_input("age > 30", "filter condition")
        >>> validate_user_input("Amount * 2", "transform expression")
    """
    expression_lower = expression.lower()

    for pattern, description in DANGEROUS_PATTERNS:
        if re.search(pattern, expression_lower, re.IGNORECASE):
            raise SecurityValidationError(
                expression,
                f"{description} are not allowed in {context}"
            )

    # Check expression length
    if len(expression) > 1000:
        raise SecurityValidationError(
            expression,
            f"{context} too long (max 1000 characters)"
        )

    # Check for balanced parentheses/brackets
    if expression.count('(') != expression.count(')'):
        raise SecurityValidationError(
            expression,
            f"Unbalanced parentheses in {context}"
        )

    if expression.count('[') != expression.count(']'):
        raise SecurityValidationError(
            expression,
            f"Unbalanced brackets in {context}"
        )
```

### Update All Operations to Use Unified Validation

```python
# filtering.py
from excel_toolkit.core.security import validate_user_input, SecurityValidationError

def validate_condition(condition: str) -> Result[str, ValidationError]:
    """Validate filter condition for security."""
    try:
        validate_user_input(condition, "filter condition")
        return ok(condition)
    except SecurityValidationError as e:
        return err(ValidationError(str(e)))

# transforming.py
from excel_toolkit.core.security import validate_user_input, SecurityValidationError

def validate_expression_security(expression: str) -> Result[None, InvalidExpressionError]:
    """Validate expression for security."""
    try:
        validate_user_input(expression, "transform expression")
        return ok(None)
    except SecurityValidationError as e:
        return err(InvalidExpressionError(str(e)))
```

### Additional Benefits

1. **Single source of truth**: Security policy defined once
2. **Easier to audit**: Security team reviews one file
3. **Easier to update**: Add new patterns in one place
4. **Consistent error messages**: Users get same feedback everywhere
5. **Testable**: Can write comprehensive security tests

### Testing

```python
# tests/unit/test_security.py

def test_dangerous_patterns_blocked():
    """Test that all dangerous patterns are blocked."""
    dangerous_inputs = [
        "import os",
        "exec('print(1)')",
        "__class__",
        "os.system",
        "[1 for i in range(10)]",
    ]

    for input_str in dangerous_inputs:
        with pytest.raises(SecurityValidationError):
            validate_user_input(input_str)

def test_safe_inputs_allowed():
    """Test that safe inputs are allowed."""
    safe_inputs = [
        "age > 30",
        "Amount * 2",
        "column == 'value'",
        "price >= 100 and quantity < 50",
    ]

    for input_str in safe_inputs:
        validate_user_input(input_str)  # Should not raise
```

## Migration Plan

1. Create `excel_toolkit/core/security.py` with unified validation
2. Update `filtering.py` to use unified validation
3. Update `transforming.py` to use unified validation
4. Add comprehensive security tests
5. Update documentation
6. Audit all other operations that accept user input

## Related Issues

- eval() security vulnerability (#011)
- No input sanitization for user parameters (#014)
