# Title: Remove debug print statements from production code

## Problem Description

The codebase contains **debug print statements** in production code, specifically in `excel_toolkit/fp/_result.py`. These debug statements pollute output and are unprofessional in a production tool.

### Current Debug Code

In `excel_toolkit/fp/_result.py` (lines 69, 85):

```python
# Line 69 in Ok.map()
def map(self, fn: Callable[[T], U]) -> 'Result[U, E]':
    """Apply function to the value."""
    print("Success!")  # ← DEBUG CODE IN PRODUCTION
    return Ok(fn(self._value))

# Line 85 in Err.map()
def map(self, fn: Callable[[T], U]) -> 'Result[U, E]':
    """Pass through error."""
    print("Failed!")  # ← DEBUG CODE IN PRODUCTION
    return self
```

### Impact

**1. Polluted Output**
```bash
$ xl filter data.xlsx "age > 30"
Success!          # ← Unwanted debug output
Success!          # ← More unwanted debug output
Filtered 5000 rows to 1250 rows
```

**2. Pipelines Break**
```bash
$ xl filter data.xlsx "age > 30" | xl sort --by name
Success!          # ← This breaks JSON/CSV output
Success!          # ← Multiple times
id,name,age
1,John,35
```

**3. Unprofessional**
- Users see "Success!" / "Failed!" messages randomly
- Looks like incomplete/beta software
- Confuses users (is this an error? info?)

**4. Performance Impact**
- Print statements executed on every operation
- For 500k rows with 10 operations = 5 million print calls!
- Adds overhead even if output is redirected

### Why This Exists

Developers likely added these for debugging Result type behavior and forgot to remove them. They should have used proper logging instead.

## Affected Files

- `excel_toolkit/fp/_result.py` (lines 69, 85)
- Potentially other files with debug prints

## Proposed Solution

### 1. Remove Debug Prints (Immediate Fix)

```python
# excel_toolkit/fp/_result.py

@dataclass(frozen=True)
class Ok(Result[T, E]):
    """Success variant containing a value."""

    _value: T

    def map(self, fn: Callable[[T], U]) -> 'Result[U, E]':
        """Apply function to the value."""
        # REMOVE: print("Success!")
        return Ok(fn(self._value))

    # ... rest of class ...


@dataclass(frozen=True)
class Err(Result[T, E]):
    """Error variant containing an error."""

    _error: E

    def map(self, fn: Callable[[T], U]) -> 'Result[U, E]':
        """Pass through error."""
        # REMOVE: print("Failed!")
        return self

    # ... rest of class ...
```

### 2. Use Proper Logging Instead (If Debug Info Needed)

```python
# excel_toolkit/fp/_result.py

import logging

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Ok(Result[T, E]):
    """Success variant containing a value."""

    _value: T

    def map(self, fn: Callable[[T], U]) -> 'Result[U, E]':
        """Apply function to the value."""
        # Use logger instead of print
        logger.debug(f"Result.map: Applying function to Ok value")
        return Ok(fn(self._value))
```

Then enable debug logging when needed:
```bash
$ xl filter data.xlsx "age > 30" --log-level debug
```

### 3. Add Verbose Mode for Users (Optional)

If users want to see operation details:

```python
# cli.py

@app.command()
def filter(
    file_path: str,
    condition: str,
    verbose: bool = typer.Option(False, "--verbose", "-v")
):
    """Filter with optional verbose output."""

    if verbose:
        typer.echo("Loading file...", err=True)  # To stderr
        typer.echo(f"Applying filter: {condition}", err=True)
        typer.echo(f"Original rows: {len(df)}", err=True)

    result = apply_filter(df, condition)

    if verbose:
        typer.echo(f"Filtered rows: {len(result)}", err=True)
```

### 4. Audit for Other Debug Code

Search entire codebase for debug statements:

```bash
# Find all print statements
grep -r "print(" excel_toolkit/

# Find debug comments
grep -r "debug\|DEBUG\|FIXME\|XXX" excel_toolkit/

# Find commented-out code
grep -r "# print\|# print(" excel_toolkit/
```

## Testing

```python
# tests/unit/test_fp_result.py

def test_no_debug_output(capsys):
    """Test that Result operations don't produce debug output."""

    result = ok(42)
    mapped = result.map(lambda x: x * 2)

    # Capture output
    captured = capsys.readouterr()

    # Should be no output
    assert captured.out == ""
    assert captured.err == ""

def test_pipeline_no_output(capsys):
    """Test that Result pipeline doesn't produce output."""

    result = ok(42)
    pipeline = (
        result
        .map(lambda x: x * 2)
        .and_then(lambda x: ok(x + 10))
        .map(lambda x: x / 2)
    )

    captured = capsys.readouterr()
    assert captured.out == ""
```

## Best Practices Going Forward

1. **Never use print() in production code**
2. **Use logging module** for debug information
3. **Use stderr** for user-facing messages (not stdout)
4. **Add --verbose flag** for optional debugging
5. **Review code before commit** for debug statements

## Implementation

This is a **quick fix** - just remove the print statements:

1. Remove lines 69 and 85 in `excel_toolkit/fp/_result.py`
2. Search codebase for other debug prints
3. Add tests to prevent regression
4. Add pre-commit hook to catch future debug prints

## Related Issues

- None (standalone code quality issue)
