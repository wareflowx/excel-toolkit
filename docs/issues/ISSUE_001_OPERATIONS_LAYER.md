# Issue #001: Missing Operations Layer - Detailed Analysis

**Issue ID:** #001
**Severity:** Critical
**Status:** Open
**Date Identified:** 2026-01-16
**Component:** Architecture / Operations Layer

---

## Executive Summary

The operations layer (`excel_toolkit/operations/`) exists but is **completely empty** (only contains an empty `__init__.py` file). This represents a critical architectural violation: all business logic is currently embedded directly in CLI command files instead of being properly separated into the operations layer as designed.

**Key Finding:** Commands do not reference missing operations - they simply don't use the operations layer at all, violating the documented architecture.

---

## Current State Analysis

### Directory Structure

```
excel_toolkit/operations/
├── __init__.py          # Empty file (0 bytes)
└── [MISSING FILES]
    ├── filtering.py
    ├── sorting.py
    ├── pivoting.py
    ├── aggregating.py
    ├── comparing.py
    ├── cleaning.py
    ├── transforming.py
    ├── joining.py
    └── validation.py
```

### Architecture Documented vs. Reality

| Layer | Documented Responsibility | Current Reality |
|-------|---------------------------|-----------------|
| **commands/** | CLI interface, validation, display | **Contains ALL business logic** |
| **operations/** | Pure business logic on DataFrames | **Completely empty** |
| **core/** | File I/O abstraction | Used directly by commands |

### Evidence from Code

**1. Empty operations module:**
```bash
$ ls -la excel_toolkit/operations/
total 4
drwxr-xr-x 1 dpereira 1049089 0 Jan 15 11:20 .
drwxr-xr-x 1 dpereira 1049089 0 Jan 16 09:13 ..
-rw-r--r-- 1 dpereira 1049089 0 Jan 15 11:20 __init__.py
```

**2. Commands implement business logic directly:**

Example from `commands/filter.py` (lines 136-158):
```python
# Step 7: Apply filter
try:
    df_filtered = df.query(normalized_condition)
except pd.errors.UndefinedVariableError as e:
    # Extract column name from error
    error_str = str(e)
    col_match = re.search(r"'([^']+)'", error_str)
    if col_match:
        col = col_match.group(1)
        typer.echo(f"Error: Column '{col}' not found", err=True)
        typer.echo(f"Available columns: {', '.join(df.columns)}")
```

This logic should be in `operations/filtering.py`.

Example from `commands/sort.py` (lines 153-170):
```python
# Step 9: Sort data
try:
    df_sorted = df.sort_values(
        by=column_list,
        ascending=not desc,
        na_position=na_placement,
    )
except TypeError as e:
    error_msg = str(e)
    if "not comparable" in error_msg or "unorderable types" in error_msg:
        typer.echo("Error: Cannot sort mixed data types in column", err=True)
```

This logic should be in `operations/sorting.py`.

**3. No imports from operations:**

```bash
$ grep -r "from excel_toolkit.operations" excel_toolkit/commands/
# No results - commands don't import from operations
```

---

## Documented Architecture (from PROJECT_STRUCTURE.md)

According to `docs/PROJECT_STRUCTURE.md`, the architecture should be:

### Operations Module Responsibilities

> **Responsibility: Pure business logic separated from CLI concerns.**
>
> Each file contains functions that perform actual data manipulations on pandas DataFrames. These functions have no knowledge of Typer or CLI - they take parameters and return results.
>
> This separation enables:
> - Unit testing without CLI dependencies
> - Reuse in pipelines and templates
> - Import by external packages
> - Clear separation of concerns

### Module Boundaries

```
- **commands/** may import from operations, core, utils, models, fp
- **operations/** may import from core, utils, models, fp, but NOT commands
- **core/** may import from models, utils, fp, but NOT commands or operations
```

### Command Implementation Pattern

> Each command file follows this pattern:
> 1. Define Typer command function with parameters
> 2. Validate inputs
> 3. **Call corresponding operation function** ← NOT IMPLEMENTED
> 4. Handle output formatting
> 5. Manage exit codes

---

## Impact Assessment

### 1. Violation of Single Responsibility Principle

**Commands currently do everything:**
- CLI argument parsing (Typer)
- Input validation
- **Business logic** ← should be in operations
- Error handling
- Output formatting
- File I/O coordination

### 2. Untestable Business Logic

**Current state:**
- Cannot test filtering/sorting/grouping logic without Typer
- No way to write unit tests for data operations
- Tests would need to simulate entire CLI context

**Should be:**
```python
# Testable pure function
def filter_dataframe(df: pd.DataFrame, condition: str) -> Result[pd.DataFrame, FilterError]:
    """Pure function - easy to test"""
    ...

# CLI command (thin wrapper)
def filter(file_path: str, condition: str, ...) -> None:
    df = read_file(file_path)
    result = filter_dataframe(df, condition)  # Call operation
    handle_result(result)
```

### 3. Code Duplication

Business logic is duplicated across commands because it can't be reused:

**Example - filtering logic:**
- `filter.py` implements `df.query()` with error handling
- `sort.py` imports and reuses filter's validation functions
- Other commands will need to duplicate this pattern

**Should be:**
```python
# In operations/filtering.py
def apply_filter(df: pd.DataFrame, condition: str) -> Result[DataFrame, FilterError]:
    """Reusable filter operation"""
    ...

# Used by filter.py, sort.py, aggregate.py, etc.
```

### 4. Non-reusable as Library

**Current state:**
```python
# Cannot import business logic without CLI dependencies
from excel_toolkit.commands.filter import filter  # ❌ Requires Typer
```

**Should be:**
```python
# Clean business logic import
from excel_toolkit.operations.filtering import filter_dataframe  # ✅ Pure function
```

### 5. Architecture Violation

Per PROJECT_STRUCTURE.md:
> **Operations are called from commands, not the reverse. Operations layer has no Typer dependencies.**

**Reality:** Operations layer doesn't exist. All logic in commands with Typer dependencies.

---

## Required Operation Modules

Based on existing commands and PROJECT_STRUCTURE.md, the following operation modules must be implemented:

### 1. `operations/filtering.py`

**Required functions:**
```python
def apply_filter(
    df: pd.DataFrame,
    condition: str,
    columns: list[str] | None = None
) -> Result[pd.DataFrame, FilterError]
    """Filter DataFrame by condition"""

def validate_condition(condition: str) -> Result[str, ValidationError]
    """Validate filter condition for security"""

def normalize_condition(condition: str) -> str
    """Normalize condition syntax for pandas"""
```

**Used by:** `commands/filter.py`, `commands/sort.py`

### 2. `operations/sorting.py`

**Required functions:**
```python
def sort_dataframe(
    df: pd.DataFrame,
    columns: list[str],
    ascending: bool = True,
    na_position: str = "last"
) -> Result[pd.DataFrame, SortError]
    """Sort DataFrame by columns"""

def validate_sort_columns(df: pd.DataFrame, columns: list[str]) -> Result[None, ValidationError]
    """Validate sort columns exist"""
```

**Used by:** `commands/sort.py`

### 3. `operations/pivoting.py`

**Required functions:**
```python
def create_pivot_table(
    df: pd.DataFrame,
    rows: list[str],
    columns: list[str],
    values: list[str],
    aggfunc: str = "sum",
    fill_value: Any = None
) -> Result[pd.DataFrame, PivotError]
    """Create pivot table from DataFrame"""

def flatten_multiindex(df: pd.DataFrame) -> pd.DataFrame
    """Flatten MultiIndex columns/rows"""

def validate_aggregation_function(func: str) -> Result[str, ValidationError]
    """Validate aggregation function name"""
```

**Used by:** `commands/pivot.py`

### 4. `operations/aggregating.py`

**Required functions:**
```python
def aggregate_groups(
    df: pd.DataFrame,
    group_columns: list[str],
    aggregations: dict[str, list[str]]
) -> Result[pd.DataFrame, AggregateError]
    """Group and aggregate DataFrame"""

def parse_aggregation_specs(
    specs: str
) -> Result[dict[str, list[str]], ParseError]
    """Parse aggregation specifications"""

def validate_aggregation_specs(
    df: pd.DataFrame,
    group_columns: list[str],
    agg_columns: list[str]
) -> Result[None, ValidationError]
    """Validate aggregation columns"""
```

**Used by:** `commands/aggregate.py`

### 5. `operations/comparing.py`

**Required functions:**
```python
def compare_dataframes(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    key_columns: list[str] | None = None
) -> Result[ComparisonResult, CompareError]
    """Compare two DataFrames"""

def find_differences(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    key_columns: list[str]
) -> tuple[set, set, list]
    """Find added, deleted, and modified rows"""

def compare_rows(row1: pd.Series, row2: pd.Series) -> bool
    """Compare two rows for equality"""
```

**Used by:** `commands/compare.py`

### 6. `operations/cleaning.py`

**Required functions:**
```python
def clean_dataframe(
    df: pd.DataFrame,
    operations: list[CleanOperation]
) -> Result[pd.DataFrame, CleanError]
    """Apply multiple cleaning operations"""

def trim_whitespace(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame
    """Trim whitespace from string columns"""

def remove_duplicates(
    df: pd.DataFrame,
    subset: list[str] | None = None,
    keep: str = "first"
) -> pd.DataFrame
    """Remove duplicate rows"""

def fill_missing_values(
    df: pd.DataFrame,
    strategy: dict[str, FillStrategy]
) -> Result[pd.DataFrame, CleanError]
    """Fill missing values"""

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame
    """Standardize column names"""
```

**Used by:** `commands/clean.py`, `commands/dedupe.py`, `commands/fill.py`, `commands/strip.py`

### 7. `operations/transforming.py`

**Required functions:**
```python
def transform_column(
    df: pd.DataFrame,
    column: str,
    transformation: Transformation
) -> Result[pd.DataFrame, TransformError]
    """Transform column values"""

def apply_expression(
    df: pd.DataFrame,
    column: str,
    expression: str
) -> Result[pd.DataFrame, TransformError]
    """Apply expression to create/modify column"""

def cast_columns(
    df: pd.DataFrame,
    type_mapping: dict[str, str]
) -> Result[pd.DataFrame, TransformError]
    """Cast columns to specified types"""
```

**Used by:** `commands/transform.py`

### 8. `operations/joining.py`

**Required functions:**
```python
def join_dataframes(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    on: list[str] | str,
    how: str = "inner"
) -> Result[pd.DataFrame, JoinError]
    """Join two DataFrames"""

def validate_join_columns(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    on: list[str]
) -> Result[None, ValidationError]
    """Validate join columns exist"""

def merge_dataframes(
    dfs: list[pd.DataFrame],
    axis: str = "rows"
) -> Result[pd.DataFrame, MergeError]
    """Merge multiple DataFrames"""
```

**Used by:** `commands/join.py`, `commands/merge.py`, `commands/append.py`

### 9. `operations/validation.py`

**Required functions:**
```python
def validate_dataframe(
    df: pd.DataFrame,
    rules: list[ValidationRule]
) -> ValidationResult
    """Validate DataFrame against rules"""

def validate_column_exists(df: pd.DataFrame, column: str) -> Result[None, ValidationError]
    """Validate column exists"""

def validate_column_type(df: pd.DataFrame, column: str, expected_type: type) -> Result[None, ValidationError]
    """Validate column type"""

def validate_value_range(
    df: pd.DataFrame,
    column: str,
    min_val: Any | None = None,
    max_val: Any | None = None
) -> Result[None, ValidationError]
    """Validate value ranges"""

def check_null_values(
    df: pd.DataFrame,
    columns: list[str] | None = None
) -> dict[str, int]
    """Check null values in columns"""
```

**Used by:** `commands/validate.py`, `commands/stats.py`

---

## Implementation Strategy

### Phase 1: Extract Core Operations

**Priority: High - Blocks testing and reusability**

1. **Create `operations/filtering.py`**
   - Extract filter logic from `commands/filter.py`
   - Create pure functions with Result types
   - Add comprehensive type hints

2. **Create `operations/sorting.py`**
   - Extract sort logic from `commands/sort.py`
   - Implement validation functions

3. **Create `operations/pivoting.py`**
   - Extract pivot logic from `commands/pivot.py`
   - Implement MultiIndex flattening

4. **Create `operations/aggregating.py`**
   - Extract aggregate logic from `commands/aggregate.py`
   - Implement specification parser

5. **Create `operations/comparing.py`**
   - Extract compare logic from `commands/compare.py`
   - Implement difference detection

### Phase 2: Extract Support Operations

**Priority: Medium - Enables advanced features**

6. **Create `operations/cleaning.py`**
   - Consolidate logic from `clean.py`, `dedupe.py`, `fill.py`, `strip.py`
   - Implement cleaning operation builder

7. **Create `operations/transforming.py`**
   - Extract transform logic from `commands/transform.py`

8. **Create `operations/joining.py`**
   - Consolidate logic from `join.py`, `merge.py`, `append.py`

9. **Create `operations/validation.py`**
   - Consolidate logic from `validate.py`, `stats.py`

### Phase 3: Refactor Commands

**Priority: High - Complete architecture alignment**

For each command file:
1. Remove business logic
2. Import from operations
3. Keep only CLI concerns (Typer, validation, display)
4. Update error handling to use Result types

**Before:**
```python
# commands/filter.py - 315 lines with business logic
def filter(file_path: str, condition: str, ...) -> None:
    # File reading
    df = handler.read(path)

    # Business logic (should be in operations)
    df_filtered = df.query(normalized_condition)

    # Output
    display_table(df_filtered)
```

**After:**
```python
# commands/filter.py - ~50 lines, CLI only
from excel_toolkit.operations.filtering import apply_filter, validate_condition

def filter(file_path: str, condition: str, ...) -> None:
    # File reading
    df = handler.read(path)

    # Validation
    validation = validate_condition(condition)
    if is_err(validation):
        handle_error(unwrap_err(validation))

    # Business logic (delegated to operations)
    result = apply_filter(df, condition, columns)

    if is_err(result):
        handle_error(unwrap_err(result))

    # Output
    display_table(unwrap(result))
```

### Phase 4: Add Tests

**Priority: High - Ensure reliability**

1. **Unit tests for each operation**
   - Test pure functions without CLI
   - Test error cases
   - Test edge cases

2. **Integration tests for commands**
   - Test CLI invocation
   - Test error handling
   - Test file I/O

---

## Migration Example: Filter Command

### Current Implementation (commands/filter.py)

**Lines 136-158** (business logic in command):
```python
# Step 7: Apply filter
try:
    df_filtered = df.query(normalized_condition)
except pd.errors.UndefinedVariableError as e:
    error_str = str(e)
    col_match = re.search(r"'([^']+)'", error_str)
    if col_match:
        col = col_match.group(1)
        typer.echo(f"Error: Column '{col}' not found", err=True)
        typer.echo(f"Available columns: {', '.join(df.columns)}")
    else:
        typer.echo(f"Error: {error_str}", err=True)
    raise typer.Exit(1)
except Exception as e:
    error_msg = str(e)
    if "could not convert" in error_msg:
        typer.echo("Error: Type mismatch in condition", err=True)
        # ... more error handling
    raise typer.Exit(1)
```

### Target Implementation

**Step 1: Create `operations/filtering.py`**
```python
"""Filtering operations on DataFrames."""

import pandas as pd
import re
from excel_toolkit.fp import ok, err, Result
from excel_toolkit.models.error_types import FilterError

def apply_filter(
    df: pd.DataFrame,
    condition: str,
    columns: list[str] | None = None
) -> Result[pd.DataFrame, FilterError]:
    """Apply filter condition to DataFrame.

    Args:
        df: Source DataFrame
        condition: Filter condition (pandas query syntax)
        columns: Optional columns to select after filtering

    Returns:
        Result[DataFrame, FilterError]
    """
    try:
        df_filtered = df.query(condition)
    except pd.errors.UndefinedVariableError as e:
        col = _extract_column_name(str(e))
        return err(FilterError.ColumnNotFound(col, list(df.columns)))
    except Exception as e:
        return err(FilterError.QueryFailed(str(e), condition))

    # Select columns if specified
    if columns:
        missing = [c for c in columns if c not in df_filtered.columns]
        if missing:
            return err(FilterError.ColumnsNotFound(missing, list(df.columns)))
        df_filtered = df_filtered[columns]

    return ok(df_filtered)

def _extract_column_name(error_str: str) -> str:
    """Extract column name from pandas error."""
    match = re.search(r"'([^']+)'", error_str)
    return match.group(1) if match else "unknown"
```

**Step 2: Update `commands/filter.py`**
```python
# imports
from excel_toolkit.operations.filtering import apply_filter
from excel_toolkit.models.error_types import FilterError

def filter(file_path: str, condition: str, ...) -> None:
    # ... file reading code ...

    # Business logic (delegated)
    result = apply_filter(df, normalized_condition, column_list)

    if is_err(result):
        error = unwrap_err(result)
        _handle_filter_error(error)
        raise typer.Exit(1)

    df_filtered = unwrap(result)

    # ... output code ...

def _handle_filter_error(error: FilterError) -> None:
    """Handle filter errors with user-friendly messages."""
    if isinstance(error, FilterError.ColumnNotFound):
        typer.echo(f"Error: Column '{error.column}' not found", err=True)
        typer.echo(f"Available columns: {', '.join(error.available)}")
    elif isinstance(error, FilterError.QueryFailed):
        typer.echo(f"Error filtering data: {error.message}", err=True)
        typer.echo(f"Condition: {error.condition}")
```

---

## Benefits of Implementation

### 1. Testability
```python
# Unit test - no CLI required
def test_apply_filter():
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    result = apply_filter(df, "a > 1")
    assert is_ok(result)
    assert len(unwrap(result)) == 2
```

### 2. Reusability
```python
# Can be imported as library
from excel_toolkit.operations.filtering import apply_filter

# Use in scripts, notebooks, other packages
df_filtered = apply_filter(df, "price > 100")
```

### 3. Maintainability
- Single responsibility: operations only do data manipulation
- Easy to locate bugs
- Clear API boundaries

### 4. Composition
```python
# Can chain operations
from excel_toolkit.operations import filtering, sorting

result = (
    apply_filter(df, "price > 100")
    .and_then(lambda d: sort_dataframe(d, ["date"]))
)
```

---

## Dependencies to Create

### 1. `models/error_types.py` (if not exists)

Define error ADTs for operations:

```python
from dataclasses import dataclass
from excel_toolkit.fp.immutable import immutable

@immutable
@dataclass
class FilterError:
    """Errors from filtering operations."""

    column: str
    available: list[str]

@immutable
@dataclass
class QueryFailed:
    """Query execution failed."""

    message: str
    condition: str

FilterError = ColumnNotFound | QueryFailed | TypeMismatch
```

### 2. `operations/__init__.py`

Export public API:

```python
"""Business logic operations for data manipulation."""

from excel_toolkit.operations.filtering import (
    apply_filter,
    validate_condition,
    normalize_condition,
)
from excel_toolkit.operations.sorting import (
    sort_dataframe,
    validate_sort_columns,
)
# ... etc

__all__ = [
    "apply_filter",
    "validate_condition",
    "sort_dataframe",
    # ...
]
```

---

## Testing Requirements

### Unit Tests (tests/unit/operations/)

```python
# test_filtering.py
def test_apply_filter_simple_condition():
    ...

def test_apply_filter_invalid_column():
    ...

def test_apply_filter_type_mismatch():
    ...

def test_validate_condition_dangerous_pattern():
    ...

def test_normalize_condition_between_operator():
    ...
```

### Integration Tests (tests/integration/)

```python
# test_filter_command.py
def test_filter_command_cli():
    """Test CLI integration."""
    result = runner.invoke(app, ["filter", "test.xlsx", "age > 30"])
    assert result.exit_code == 0
```

---

## Metrics for Success

### Code Organization
- [ ] All operations modules created
- [ ] All business logic extracted from commands
- [ ] Commands reduced to <100 lines each
- [ ] No circular dependencies

### Test Coverage
- [ ] Unit tests for all operations
- [ ] >90% code coverage for operations
- [ ] Integration tests pass

### Architecture
- [ ] Module boundaries respected (PROJECT_STRUCTURE.md)
- [ ] Operations have no CLI dependencies
- [ ] Commands import from operations, not core
- [ ] Result types used consistently

---

## Timeline Estimate

| Phase | Tasks | Estimate |
|-------|-------|----------|
| Phase 1 | Create 5 core operation modules | 2-3 days |
| Phase 2 | Create 4 support operation modules | 1-2 days |
| Phase 3 | Refactor all command files | 2-3 days |
| Phase 4 | Write unit tests | 2-3 days |
| **Total** | | **7-11 days** |

---

## Related Issues

- **Issue #002:** Fix import errors for exceptions (blocks operations)
- **Issue #005:** Security vulnerabilities in filter (needs operations extraction)
- **Issue #011:** Missing test coverage (operations enable unit tests)

---

## Next Steps

1. **Immediate:**
   - Review this analysis with team
   - Confirm approach and priorities
   - Create GitHub issues for each phase

2. **Implementation:**
   - Start with Phase 1 (core operations)
   - Implement one operation module at a time
   - Add tests immediately after each module

3. **Verification:**
   - Run test suite after each module
   - Ensure no functionality broken
   - Measure code reduction in commands

---

**Document Version:** 1.0
**Last Updated:** 2026-01-16
**Author:** Claude Code Analysis
**Status:** Awaiting Implementation
