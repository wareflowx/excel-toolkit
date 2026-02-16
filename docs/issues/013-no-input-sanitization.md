# Title: Add input sanitization for user-provided column names, file paths, and parameters

## Problem Description

The excel-toolkit **does not sanitize** user-provided column names, sheet names, file paths, or other parameters. This allows potential injection attacks, crashes, or unexpected behavior.

### Current Behavior

Throughout the codebase, user input is used directly without sanitization:

```python
# commands/filter.py - Line 76
col_list = [c.strip() for c in columns.split(",")]
# No validation of column names

# commands/common.py
def resolve_column_references(columns: list[str], df: pd.DataFrame):
    # No validation before using column names
```

### Attack Vectors

**1. SQL/Code Injection in column names**
```bash
# Attacker provides malicious column name
xl filter data.xlsx "'; DROP TABLE users; --' == 'value'"

# Or for column selection
xl select data.xlsx --columns "id,'; DROP TABLE users; --'"
```

**2. Path traversal attacks**
```bash
# Attacker uses path traversal
xl transform "../../../../etc/passwd" --col "Amount" --expr "Amount * 2"

# Or for output
xl filter data.xlsx "age > 30" --output "../../../malicious.xlsx"
```

**3. Sheet name injection**
```bash
xl select data.xlsx --sheet "../../malicious" --columns "id,name"
```

**4. Command injection in parameters**
```bash
# If parameters are used in shell commands
xl export data.xlsx --output "file.xlsx; rm -rf /"
```

### Real-World Impact Scenarios

**Scenario 1: Crash with special characters**
```bash
# Column name with quotes causes syntax error
xl filter data.xlsx 'user"s_name' == 'value'
# Error: Invalid condition, no helpful message
```

**Scenario 2: Unexpected behavior with Unicode**
```bash
# Homograph attacks (visually similar characters)
xl filter data.xlsx "рrice > 100"  # 'р' is Cyrillic, not 'p'
```

**Scenario 3: File system manipulation**
```bash
xl filter data.xlsx "age > 30" --output "../sensitive/filtered.xlsx"
# Writes to unexpected location
```

## Affected Files

All command files that accept user input:
- `excel_toolkit/commands/filter.py`
- `excel_toolkit/commands/select.py`
- `excel_toolkit/commands/transform.py`
- `excel_toolkit/commands/group.py`
- `excel_toolkit/commands/join.py`
- `excel_toolkit/commands/merge.py`
- Basically all commands in `commands/`

## Proposed Solution

### 1. Column Name Sanitization

```python
# excel_toolkit/core/validation.py

import re
from pathlib import Path

def sanitize_column_name(name: str) -> Result[str, ValidationError]:
    """
    Sanitize and validate column name.

    Rules:
    - Must start with letter or underscore
    - Can contain letters, numbers, underscores
    - Max length 100 characters
    - No special characters except underscore
    - No SQL/Code injection patterns

    Args:
        name: Raw column name from user

    Returns:
        Sanitized column name or error
    """
    # Remove whitespace
    name = name.strip()

    # Check length
    if len(name) > 100:
        return err(ValidationError("Column name too long (max 100 characters)"))

    # Check for dangerous patterns
    dangerous_patterns = [
        r';',  # SQL injection
        r'--',  # SQL comment
        r'\bDROP\b',  # SQL commands
        r'\bDELETE\b',
        r'\bINSERT\b',
        r'\bUPDATE\b',
        r'\bIMPORT\b',  # Python import
        r'\bEXEC\b',  # Execute
        r'\bEVAL\b',  # Eval
    ]

    name_upper = name.upper()
    for pattern in dangerous_patterns:
        if re.search(pattern, name_upper):
            return err(ValidationError(f"Dangerous pattern in column name: {pattern}"))

    # Validate format (alphanumeric + underscore)
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        return err(ValidationError(
            "Column name must start with letter/underscore and contain only letters, numbers, underscores"
        ))

    return ok(name)
```

### 2. File Path Validation

```python
def validate_file_path(path: str, must_exist: bool = False) -> Result[Path, ValidationError]:
    """
    Validate and sanitize file path.

    Prevents:
    - Path traversal attacks
    - Access to sensitive system files
    - Writing to dangerous locations

    Args:
        path: User-provided file path
        must_exist: Whether file must exist (for input files)

    Returns:
        Validated Path object or error
    """
    path_obj = Path(path).resolve()

    # Check for path traversal
    if '..' in str(path_obj):
        # Only allow if within current directory tree
        try:
            path_obj.relative_to(Path.cwd())
        except ValueError:
            return err(ValidationError("Path traversal detected - access denied"))

    # For input files, check existence
    if must_exist and not path_obj.exists():
        return err(ValidationError(f"File not found: {path}"))

    # Prevent access to sensitive locations
    sensitive_patterns = [
        '/etc/',  # Linux system files
        '/sys/',
        '/proc/',
        'C:\\Windows\\',  # Windows system files
        '~/.ssh/',
        '~/.gnupg/',
    ]

    path_str = str(path_obj)
    for pattern in sensitive_patterns:
        if pattern in path_str:
            return err(ValidationError(f"Access to system files denied: {pattern}"))

    return ok(path_obj)
```

### 3. Sheet Name Validation

```python
def validate_sheet_name(name: str) -> Result[str, ValidationError]:
    """
    Validate Excel sheet name.

    Excel sheet name rules:
    - Max 31 characters
    - No special characters: : \ / ? * [ ]
    - Cannot start or end with single quote

    Args:
        name: User-provided sheet name

    Returns:
        Validated sheet name or error
    """
    # Excel limits
    if len(name) > 31:
        return err(ValidationError("Sheet name too long (max 31 characters)"))

    # Banned characters
    banned_chars = [':', '\\', '/', '?', '*', '[', ']']
    for char in banned_chars:
        if char in name:
            return err(ValidationError(f"Invalid character in sheet name: '{char}'"))

    # Cannot start/end with quote
    if name.startswith("'") or name.endswith("'"):
        return err(ValidationError("Sheet name cannot start or end with quote"))

    return ok(name)
```

### 4. Expression Parameter Validation

```python
def validate_parameter(name: str, value: str) -> Result[str, ValidationError]:
    """
    Validate command parameter value.

    Args:
        name: Parameter name (for error messages)
        value: Parameter value from user

    Returns:
        Validated value or error
    """
    # Check for shell injection
    if re.search(r'[;&|`$()]', value):
        return err(ValidationError(f"Shell metacharacters not allowed in {name}"))

    # Check length
    if len(value) > 1000:
        return err(ValidationError(f"{name} too long (max 1000 characters)"))

    return ok(value)
```

### 5. Update Commands to Use Validation

```python
# commands/filter.py

from excel_toolkit.core.validation import (
    sanitize_column_name,
    validate_file_path
)

def filter(
    file_path: str = typer.Argument(...),
    condition: str = typer.Argument(...),
    output: str | None = typer.Option(None),
    columns: str | None = typer.Option(None),
    ...
):
    # Validate input file path
    validated_path = validate_file_path(file_path, must_exist=True)
    if is_err(validated_path):
        error = unwrap_err(validated_path)
        typer.echo(f"Invalid file path: {error}", err=True)
        raise typer.Exit(1)

    # Validate output file path if provided
    if output:
        validated_output = validate_file_path(output, must_exist=False)
        if is_err(validated_output):
            error = unwrap_err(validated_output)
            typer.echo(f"Invalid output path: {error}", err=True)
            raise typer.Exit(1)

    # Validate column names
    if columns:
        col_list = [c.strip() for c in columns.split(",")]
        validated_cols = []
        for col in col_list:
            result = sanitize_column_name(col)
            if is_err(result):
                error = unwrap_err(result)
                typer.echo(f"Invalid column name '{col}': {error}", err=True)
                raise typer.Exit(1)
            validated_cols.append(unwrap(result))
```

## Testing

```python
# tests/unit/test_validation.py

def test_rejects_sql_injection():
    """Test that SQL injection is blocked."""
    with pytest.raises(ValidationError):
        sanitize_column_name("'; DROP TABLE users; --'")

def test_rejects_path_traversal():
    """Test that path traversal is blocked."""
    with pytest.raises(ValidationError):
        validate_file_path("../../../etc/passwd")

def test_rejects_special_chars_in_sheet_names():
    """Test that special characters are blocked in sheet names."""
    with pytest.raises(ValidationError):
        validate_sheet_name("sheet:name")

def test_allows_valid_inputs():
    """Test that valid inputs are allowed."""
    assert sanitize_column_name("user_id") == ok("user_id")
    assert validate_file_path("data.xlsx") == ok(Path("data.xlsx"))
    assert validate_sheet_name("Sheet1") == ok("Sheet1")
```

## Implementation Priority

1. **High Priority**: File path validation (prevents filesystem access)
2. **High Priority**: Column name sanitization (prevents injection)
3. **Medium Priority**: Sheet name validation (Excel-specific)
4. **Medium Priority**: Parameter validation (general safety)

## Related Issues

- eval() security vulnerability (#011)
- Inconsistent security validation (#012)
- Weak validation in operations layer (#018)
