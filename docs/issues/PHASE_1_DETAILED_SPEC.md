# Phase 1: Core Operations - Detailed Specification

**Phase:** 1 - Extract Core Operations
**Status:** Planning
**Duration Estimate:** 2-3 days
**Priority:** Critical (blocks testing and reusability)

---

## Overview

Phase 1 focuses on extracting the 5 core data manipulation operations from command files into the operations layer. These operations form the foundation of the toolkit and are used by multiple commands.

**Operations to Extract:**
1. `filtering.py` - Filter rows based on conditions
2. `sorting.py` - Sort rows by column values
3. `pivoting.py` - Create pivot table summaries
4. `aggregating.py` - Group and aggregate data
5. `comparing.py` - Compare two datasets

---

## Operation 1: Filtering

**Source File:** `commands/filter.py` (315 lines)
**Target:** `operations/filtering.py`

### Current Implementation Analysis

**Lines 24-50:** Security patterns and validation
```python
ALLOWED_PATTERNS = [
    r"\w+\s*[=!<>]+\s*[\w'\"]+",  # Comparisons
    r"\w+\s+in\s+\[[^\]]+\]",      # in operator
    r"\w+\.isna\(\)",               # Null checks
    # ... more patterns
]

DANGEROUS_PATTERNS = [
    "import", "exec", "eval", "__", "open(", "file(",
    "os.", "sys.", "subprocess", "pickle",
]
```

**Lines 243-280:** Condition validation function
**Lines 283-307:** Condition normalization function
**Lines 136-158:** Core filtering logic with error handling

**Lines 162-175:** Column selection logic
**Lines 178-179:** Row limiting logic

### Required Functions

#### 1.1 `validate_condition()`

**Signature:**
```python
def validate_condition(condition: str) -> Result[str, ValidationError]:
    """Validate filter condition for security and syntax.

    Args:
        condition: User-provided condition string

    Returns:
        Result[str, ValidationError] - Valid condition or error

    Errors:
        - DangerousPatternError: Contains dangerous code
        - ConditionTooLongError: Exceeds max length
        - UnbalancedParenthesesError: Mismatched parentheses
        - UnbalancedBracketsError: Mismatched brackets
        - UnbalancedQuotesError: Mismatched quotes
    """
```

**Implementation Requirements:**
- Check against `DANGEROUS_PATTERNS` (case-insensitive)
- Validate max length (1000 characters)
- Check balanced parentheses: `count('(') == count(')')`
- Check balanced brackets: `count('[') == count(']')`
- Check balanced single quotes: `count("'") % 2 == 0`
- Check balanced double quotes: `count('"') % 2 == 0`

**Test Cases:**
- ✅ Valid: `"age > 30"`
- ✅ Valid: `"name == 'Alice' and city == 'Paris'"`
- ❌ Invalid: `"age > __import__('os').system('rm -rf /')"` (dangerous)
- ❌ Invalid: `"age > 30 and"` (unbalanced quotes)
- ❌ Invalid: `"age > (30 and name == 'test'"`
- ❌ Invalid: Condition with 1001 characters

#### 1.2 `normalize_condition()`

**Signature:**
```python
def normalize_condition(condition: str) -> str:
    """Normalize condition syntax for pandas.query().

    Args:
        condition: User-provided condition

    Returns:
        Normalized condition string

    Transformations:
        1. "value is None" → "value.isna()"
        2. "value is not None" → "value.notna()"
        3. "value between X and Y" → "value >= X and value <= Y"
        4. "value not in " → "value not in " (case normalization)
    """
```

**Implementation Requirements:**
- Convert `(\w+)\s+is\s+None\b` → `\1.isna()`
- Convert `(\w+)\s+is\s+not\s+None\b` → `\1.notna()`
- Convert `(\w+)\s+between\s+([^ ]+)\s+and\s+([^ ]+)` → `\1 >= \2 and \1 <= \3` (case-insensitive)
- Normalize "not in" to ensure proper spacing (case-insensitive)

**Test Cases:**
- `"age is None"` → `"age.isna()"`
- `"value is not None"` → `"value.notna()"`
- `"price between 10 and 100"` → `"price >= 10 and price <= 100"`
- `"id NOT IN [1,2,3]"` → `"id not in [1,2,3]"`

#### 1.3 `apply_filter()`

**Signature:**
```python
def apply_filter(
    df: pd.DataFrame,
    condition: str,
    columns: list[str] | None = None,
    limit: int | None = None
) -> Result[pd.DataFrame, FilterError]:
    """Apply filter condition to DataFrame.

    Args:
        df: Source DataFrame
        condition: Normalized filter condition (pandas query syntax)
        columns: Optional list of columns to select after filtering
        limit: Optional maximum number of rows to return

    Returns:
        Result[pd.DataFrame, FilterError] - Filtered DataFrame or error

    Errors:
        - ColumnNotFoundError: Referenced column doesn't exist
        - QueryFailedError: Query execution failed
        - ColumnMismatchError: Type mismatch in comparison
        - ColumnsNotFoundError: Selected columns don't exist
    """
```

**Implementation Requirements:**
1. Execute `df.query(condition)`
2. Catch `pd.errors.UndefinedVariableError`:
   - Extract column name from error message using regex: `r"'([^']+)'"`3. Handle other exceptions:
   - Detect "could not convert" → TypeMismatchError
   - Other errors → QueryFailedError
4. If columns specified:
   - Check all columns exist
   - Return ColumnsNotFoundError if any missing
   - Select columns
5. If limit specified: `df.head(limit)`

**Test Cases:**
- ✅ Filter numeric: `df, "age > 30"`
- ✅ Filter string: `df, "name == 'Alice'"`
- ✅ Filter with and: `df, "age > 25 and city == 'Paris'"`
- ✅ Filter with in: `df, "category in ['A', 'B']"`
- ✅ Filter with columns: `df, "age > 30", ["name", "age"]`
- ✅ Filter with limit: `df, "age > 30", None, 10`
- ❌ Invalid column: `df, "nonexistent > 30"` → ColumnNotFoundError
- ❌ Type mismatch: `df, "age > 'thirty'"` → ColumnMismatchError
- ❌ Missing columns: `df, "age > 30", ["name", "missing"]` → ColumnsNotFoundError

#### 1.4 Helper Functions

**`_extract_column_name()`**
```python
def _extract_column_name(error_msg: str) -> str:
    """Extract column name from pandas error message.

    Args:
        error_msg: Error message from pandas

    Returns:
        Extracted column name or "unknown"
    """
    match = re.search(r"'([^']+)'", error_msg)
    return match.group(1) if match else "unknown"
```

### Error Types Required

```python
# In models/error_types.py

@immutable
@dataclass
class DangerousPatternError:
    """Condition contains dangerous code pattern."""
    pattern: str

@immutable
@dataclass
class ConditionTooLongError:
    """Condition exceeds maximum length."""
    length: int
    max_length: int

@immutable
@dataclass
class UnbalancedParenthesesError:
    """Condition has unbalanced parentheses."""
    open_count: int
    close_count: int

@immutable
@dataclass
class UnbalancedBracketsError:
    """Condition has unbalanced brackets."""
    open_count: int
    close_count: int

@immutable
@dataclass
class UnbalancedQuotesError:
    """Condition has unbalanced quotes."""
    quote_type: str  # "'" or '"'
    count: int

@immutable
@dataclass
class ColumnNotFoundError:
    """Referenced column doesn't exist in DataFrame."""
    column: str
    available: list[str]

@immutable
@dataclass
class QueryFailedError:
    """Query execution failed."""
    message: str
    condition: str

@immutable
@dataclass
class ColumnMismatchError:
    """Type mismatch in comparison."""
    message: str
    condition: str

@immutable
@dataclass
class ColumnsNotFoundError:
    """Selected columns don't exist."""
    missing: list[str]
    available: list[str]

# Union type
ValidationError = (
    DangerousPatternError |
    ConditionTooLongError |
    UnbalancedParenthesesError |
    UnbalancedBracketsError |
    UnbalancedQuotesError
)

FilterError = (
    ColumnNotFoundError |
    QueryFailedError |
    ColumnMismatchError |
    ColumnsNotFoundError
)
```

### Constants Required

```python
# In operations/filtering.py

MAX_CONDITION_LENGTH = 1000

ALLOWED_PATTERNS = [
    r"\w+\s*[=!<>]+\s*[\w'\"]+",       # Comparisons: x == 5, x > 3
    r"\w+\s+in\s+\[[^\]]+\]",           # in operator: x in [a, b, c]
    r"\w+\.isna\(\)",                   # Null check: x.isna()
    r"\w+\.notna\(\)",                  # Null check: x.notna()
    r"\w+\s+contains\s+['\"][^'\"]+['\"]",    # String contains
    r"\w+\s+startswith\s+['\"][^'\"]+['\"]",  # String starts with
    r"\w+\s+endswith\s+['\"][^'\"]+['\"]",    # String ends with
    r"\s+and\s+",                        # Logical AND
    r"\s+or\s+",                         # Logical OR
    r"\s+not\s+",                        # Logical NOT
    r"\([^)]+\)",                        # Parentheses for grouping
]

DANGEROUS_PATTERNS = [
    "import",
    "exec",
    "eval",
    "__",
    "open(",
    "file(",
    "os.",
    "sys.",
    "subprocess",
    "pickle",
]
```

### Migration Example

**Before (commands/filter.py):**
```python
# Lines 136-158
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
        # ... more handling
    raise typer.Exit(1)
```

**After (operations/filtering.py):**
```python
def apply_filter(
    df: pd.DataFrame,
    condition: str,
    columns: list[str] | None = None,
    limit: int | None = None
) -> Result[pd.DataFrame, FilterError]:
    try:
        df_filtered = df.query(condition)
    except pd.errors.UndefinedVariableError as e:
        col = _extract_column_name(str(e))
        return err(ColumnNotFoundError(col, list(df.columns)))
    except Exception as e:
        error_msg = str(e)
        if "could not convert" in error_msg:
            return err(ColumnMismatchError(error_msg, condition))
        return err(QueryFailedError(error_msg, condition))

    if columns:
        missing = [c for c in columns if c not in df_filtered.columns]
        if missing:
            return err(ColumnsNotFoundError(missing, list(df_filtered.columns)))
        df_filtered = df_filtered[columns]

    if limit is not None:
        df_filtered = df_filtered.head(limit)

    return ok(df_filtered)
```

**After (commands/filter.py - CLI only):**
```python
def filter(file_path: str, condition: str, ...) -> None:
    # ... file reading ...

    # Validation
    validation = validate_condition(condition)
    if is_err(validation):
        handle_validation_error(unwrap_err(validation))
        raise typer.Exit(1)

    # Normalize
    normalized = normalize_condition(condition)

    # Apply filter
    result = apply_filter(df, normalized, column_list, rows)

    if is_err(result):
        handle_filter_error(unwrap_err(result))
        raise typer.Exit(1)

    df_filtered = unwrap(result)

    # ... output ...
```

---

## Operation 2: Sorting

**Source File:** `commands/sort.py` (215 lines)
**Target:** `operations/sorting.py`

### Current Implementation Analysis

**Lines 54-57:** na_placement validation
**Lines 59-63:** Column parsing
**Lines 105-110:** Column validation
**Lines 112-142:** Optional filter logic (imports from filter command)
**Lines 152-170:** Core sorting logic with error handling

### Required Functions

#### 2.1 `validate_sort_columns()`

**Signature:**
```python
def validate_sort_columns(
    df: pd.DataFrame,
    columns: list[str]
) -> Result[None, SortValidationError]:
    """Validate that sort columns exist in DataFrame.

    Args:
        df: DataFrame to validate against
        columns: List of column names to sort by

    Returns:
        Result[None, SortValidationError]

    Errors:
        - NoColumnsError: No columns specified
        - ColumnNotFoundError: Column doesn't exist
    """
```

**Implementation Requirements:**
- Check columns list is not empty
- Check all columns exist in DataFrame
- Return list of missing columns if any

**Test Cases:**
- ✅ Valid: `df, ["age"]`
- ✅ Valid: `df, ["city", "age"]`
- ❌ Invalid: `df, []` → NoColumnsError
- ❌ Invalid: `df, ["missing"]` → ColumnNotFoundError

#### 2.2 `sort_dataframe()`

**Signature:**
```python
def sort_dataframe(
    df: pd.DataFrame,
    columns: list[str],
    ascending: bool = True,
    na_position: str = "last",
    limit: int | None = None
) -> Result[pd.DataFrame, SortError]:
    """Sort DataFrame by column values.

    Args:
        df: Source DataFrame
        columns: List of column names to sort by
        ascending: Sort direction (True=asc, False=desc)
        na_position: Where to place NaN values ("first" or "last")
        limit: Optional maximum number of rows to return

    Returns:
        Result[pd.DataFrame, SortError] - Sorted DataFrame or error

    Errors:
        - NotComparableError: Cannot sort mixed data types
        - SortFailedError: Sorting failed for other reason
    """
```

**Implementation Requirements:**
1. Validate na_position is "first" or "last"
2. Execute `df.sort_values(by=columns, ascending=ascending, na_position=na_position)`
3. Catch `TypeError`:
   - Detect "not comparable" or "unorderable types" → NotComparableError
   - Other TypeErrors → SortFailedError
4. If limit specified: `df.head(limit)`

**Test Cases:**
- ✅ Simple sort: `df, ["age"]`
- ✅ Multi-column sort: `df, ["city", "age"]`
- ✅ Descending: `df, ["age"], False`
- ✅ With NaN first: `df, ["age"], True, "first"`
- ✅ With limit: `df, ["age"], True, "last", 10`
- ❌ Mixed types: `df, ["mixed_column"]` → NotComparableError

### Error Types Required

```python
@immutable
@dataclass
class NoColumnsError:
    """No columns specified for sorting."""
    pass

@immutable
@dataclass
class NotComparableError:
    """Cannot sort mixed data types in column."""
    column: str
    message: str

@immutable
@dataclass
class SortFailedError:
    """Sorting failed."""
    message: str

SortValidationError = NoColumnsError | ColumnNotFoundError
SortError = NotComparableError | SortFailedError
```

### Migration Example

**Before (commands/sort.py):**
```python
# Lines 153-170
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
        typer.echo("Ensure all values in the column are of the same type", err=True)
    else:
        typer.echo(f"Error sorting data: {error_msg}", err=True)
    raise typer.Exit(1)
```

**After (operations/sorting.py):**
```python
def sort_dataframe(
    df: pd.DataFrame,
    columns: list[str],
    ascending: bool = True,
    na_position: str = "last",
    limit: int | None = None
) -> Result[pd.DataFrame, SortError]:
    # Validate na_position
    if na_position not in ("first", "last"):
        return err(SortFailedError(f"Invalid na_position: {na_position}"))

    # Sort
    try:
        df_sorted = df.sort_values(
            by=columns,
            ascending=ascending,
            na_position=na_position,
        )
    except TypeError as e:
        error_msg = str(e)
        if "not comparable" in error_msg or "unorderable types" in error_msg:
            # Find the problematic column
            for col in columns:
                if df[col].dtype == "object":
                    return err(NotComparableError(col, error_msg))
            return err(NotComparableError(columns[0], error_msg))
        return err(SortFailedError(error_msg))

    # Limit rows
    if limit is not None:
        df_sorted = df_sorted.head(limit)

    return ok(df_sorted)
```

---

## Operation 3: Pivoting

**Source File:** `commands/pivot.py` (220 lines)
**Target:** `operations/pivoting.py`

### Current Implementation Analysis

**Lines 47-58:** Required parameter validation
**Lines 60-68:** Aggregation function validation
**Lines 110-133:** Column parsing and validation
**Lines 135-152:** Fill value parsing
**Lines 154-178:** Core pivot logic with MultiIndex flattening

### Required Functions

#### 3.1 `validate_aggregation_function()`

**Signature:**
```python
def validate_aggregation_function(func: str) -> Result[str, ValidationError]:
    """Validate and normalize aggregation function name.

    Args:
        func: Aggregation function name

    Returns:
        Result[str, ValidationError] - Normalized function name or error

    Errors:
        - InvalidFunctionError: Function not supported

    Normalization:
        "avg" → "mean"
    """
```

**Implementation Requirements:**
- Check if function is in valid list
- Normalize "avg" to "mean"
- Return InvalidFunctionError with list of valid functions

**Test Cases:**
- ✅ Valid: `"sum"` → `"sum"`
- ✅ Valid: `"avg"` → `"mean"`
- ✅ Valid: `"mean"` → `"mean"`
- ❌ Invalid: `"invalid"` → InvalidFunctionError

**Valid functions:** `["sum", "mean", "avg", "count", "min", "max", "median", "std", "var", "first", "last"]`

#### 3.2 `validate_pivot_columns()`

**Signature:**
```python
def validate_pivot_columns(
    df: pd.DataFrame,
    rows: list[str],
    columns: list[str],
    values: list[str]
) -> Result[None, PivotValidationError]:
    """Validate pivot columns exist in DataFrame.

    Args:
        df: DataFrame to validate against
        rows: Row columns
        columns: Column columns
        values: Value columns

    Returns:
        Result[None, PivotValidationError]

    Errors:
        - NoRowsError: No row columns specified
        - NoColumnsError: No column columns specified
        - NoValuesError: No value columns specified
        - RowColumnsNotFoundError: Row columns don't exist
        - ColumnColumnsNotFoundError: Column columns don't exist
        - ValueColumnsNotFoundError: Value columns don't exist
    """
```

**Implementation Requirements:**
- Check each list is not empty
- Check all columns exist in DataFrame
- Return appropriate error for each case

**Test Cases:**
- ✅ Valid: `df, ["Date"], ["Product"], ["Sales"]`
- ❌ Invalid: `df, [], ["Product"], ["Sales"]` → NoRowsError
- ❌ Invalid: `df, ["Date"], [], ["Sales"]` → NoColumnsError
- ❌ Invalid: `df, ["Date"], ["Product"], []` → NoValuesError
- ❌ Invalid: `df, ["Missing"], ["Product"], ["Sales"]` → RowColumnsNotFoundError

#### 3.3 `parse_fill_value()`

**Signature:**
```python
def parse_fill_value(value: str | None) -> Any:
    """Parse fill value for pivot table.

    Args:
        value: String value to parse

    Returns:
        Parsed value (None, 0, float('nan'), int, float, or str)

    Parsing rules:
        - None or "none" → None
        - "0" → 0
        - "nan" → float('nan')
        - Try int → int
        - Try float → float
        - Otherwise → keep as string
    """
```

**Test Cases:**
- `None` → `None`
- `"none"` → `None`
- `"0"` → `0`
- `"nan"` → `float('nan')`
- `"123"` → `123`
- `"45.67"` → `45.67`
- `"text"` → `"text"`

#### 3.4 `flatten_multiindex()`

**Signature:**
```python
def flatten_multiindex(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten MultiIndex columns and index in pivot table.

    Args:
        df: DataFrame with potential MultiIndex

    Returns:
        DataFrame with flattened columns and index

    Implementation:
        1. Check if columns are MultiIndex
        2. If yes, join with '_' and strip
        3. Check if index is MultiIndex
        4. If yes, join with '_' and strip
        5. Reset index to make rows into columns
    """
```

**Implementation:**
```python
def flatten_multiindex(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    # Flatten columns if MultiIndex
    if isinstance(result.columns, pd.MultiIndex):
        result.columns = ['_'.join(map(str, col)).strip()
                         for col in result.columns.values]

    # Flatten index if MultiIndex
    if isinstance(result.index, pd.MultiIndex):
        result.index = ['_'.join(map(str, idx)).strip()
                       for idx in result.index.values]

    # Reset index
    result = result.reset_index()

    return result
```

#### 3.5 `create_pivot_table()`

**Signature:**
```python
def create_pivot_table(
    df: pd.DataFrame,
    rows: list[str],
    columns: list[str],
    values: list[str],
    aggfunc: str = "sum",
    fill_value: Any = None
) -> Result[pd.DataFrame, PivotError]:
    """Create pivot table from DataFrame.

    Args:
        df: Source DataFrame
        rows: Columns to use as rows (index)
        columns: Columns to use as columns
        values: Columns to use as values
        aggfunc: Aggregation function
        fill_value: Value to fill NaN with

    Returns:
        Result[pd.DataFrame, PivotError] - Pivot table or error

    Errors:
        - PivotFailedError: Pivot table creation failed
    """
```

**Implementation Requirements:**
1. Validate aggregation function
2. Validate pivot columns
3. Execute `df.pivot_table()` with:
   - `index=rows`
   - `columns=columns`
   - `values=values`
   - `aggfunc=aggfunc`
   - `fill_value=fill_value`
   - `observed=True` (for categorical data)
4. Flatten MultiIndex
5. Catch any exception → PivotFailedError

**Test Cases:**
- ✅ Simple pivot: `df, ["Date"], ["Product"], ["Sales"]`
- ✅ Multiple values: `df, ["Date"], ["Product"], ["Sales", "Quantity"]`
- ✅ Custom agg: `df, ["Region"], ["Year"], ["Employees"], "count"`
- ✅ With fill: `df, ["Date"], ["Product"], ["Sales"], "sum", 0`

### Error Types Required

```python
@immutable
@dataclass
class InvalidFunctionError:
    """Invalid aggregation function."""
    function: str
    valid_functions: list[str]

@immutable
@dataclass
class NoRowsError:
    """No row columns specified."""
    pass

@immutable
@dataclass
class NoColumnsError:
    """No column columns specified."""
    pass

@immutable
@dataclass
class NoValuesError:
    """No value columns specified."""
    pass

@immutable
@dataclass
class RowColumnsNotFoundError:
    """Row columns don't exist."""
    missing: list[str]
    available: list[str]

@immutable
@dataclass
class ColumnColumnsNotFoundError:
    """Column columns don't exist."""
    missing: list[str]
    available: list[str]

@immutable
@dataclass
class ValueColumnsNotFoundError:
    """Value columns don't exist."""
    missing: list[str]
    available: list[str]

@immutable
@dataclass
class PivotFailedError:
    """Pivot table creation failed."""
    message: str

PivotValidationError = (
    InvalidFunctionError |
    NoRowsError |
    NoColumnsError |
    NoValuesError |
    RowColumnsNotFoundError |
    ColumnColumnsNotFoundError |
    ValueColumnsNotFoundError
)

PivotError = PivotFailedError
```

---

## Operation 4: Aggregating

**Source File:** `commands/aggregate.py` (211 lines)
**Target:** `operations/aggregating.py`

### Current Implementation Analysis

**Lines 44-54:** Required parameter validation
**Lines 56-94:** Aggregation specification parsing
**Lines 56-94:** Aggregation specification parsing with error collection
**Lines 136-157:** Column validation
**Lines 164-174:** Core aggregation logic with MultiIndex flattening

### Required Functions

#### 4.1 `parse_aggregation_specs()`

**Signature:**
```python
def parse_aggregation_specs(
    specs: str
) -> Result[dict[str, list[str]], ParseError]:
    """Parse aggregation specifications from command line.

    Args:
        specs: Comma-separated aggregation specs
               Format: "column:func1,func2,column2:func3"

    Returns:
        Result[dict[str, list[str]], ParseError]
        Dictionary mapping column names to function lists

    Errors:
        - InvalidFormatError: Invalid format (missing colon)
        - InvalidFunctionError: Invalid aggregation function
        - NoValidSpecsError: No valid specifications

    Examples:
        "Revenue:sum" → {"Revenue": ["sum"]}
        "Sales:sum,mean" → {"Sales": ["sum", "mean"]}
        "Amount:sum,count,Profit:mean" → {"Amount": ["sum", "count"], "Profit": ["mean"]}
    """
```

**Implementation Requirements:**
1. Split specs by comma
2. For each spec:
   - Check for ":" separator
   - Split on ":"
   - Parse function list (comma-separated after colon)
   - Validate each function
   - Normalize "avg" to "mean"
   - Merge with existing dict if column already present
3. Collect all errors
4. Return errors if any, otherwise return dict

**Test Cases:**
- ✅ Simple: `"Revenue:sum"` → `{"Revenue": ["sum"]}`
- ✅ Multiple functions: `"Sales:sum,mean"` → `{"Sales": ["sum", "mean"]}`
- ✅ Multiple columns: `"Amount:sum,Profit:mean"` → `{"Amount": ["sum"], "Profit": ["mean"]}`
- ❌ Invalid format: `"Revenue"` → InvalidFormatError
- ❌ Invalid function: `"Sales:invalid"` → InvalidFunctionError

**Valid functions:** `["sum", "mean", "avg", "median", "min", "max", "count", "std", "var", "first", "last"]`

#### 4.2 `validate_aggregation_columns()`

**Signature:**
```python
def validate_aggregation_columns(
    df: pd.DataFrame,
    group_columns: list[str],
    agg_columns: list[str]
) -> Result[None, AggregationValidationError]:
    """Validate aggregation columns.

    Args:
        df: DataFrame to validate against
        group_columns: Columns to group by
        agg_columns: Columns to aggregate

    Returns:
        Result[None, AggregationValidationError]

    Errors:
        - GroupColumnsNotFoundError: Group columns don't exist
        - AggColumnsNotFoundError: Aggregation columns don't exist
        - OverlappingColumnsError: Group and agg columns overlap
    """
```

**Implementation Requirements:**
- Check group columns exist
- Check agg columns exist
- Check no overlap between group and agg columns

**Test Cases:**
- ✅ Valid: `df, ["Region"], ["Sales"]`
- ❌ Invalid group: `df, ["Missing"], ["Sales"]` → GroupColumnsNotFoundError
- ❌ Invalid agg: `df, ["Region"], ["Missing"]` → AggColumnsNotFoundError
- ❌ Overlap: `df, ["Region"], ["Region", "Sales"]` → OverlappingColumnsError

#### 4.3 `aggregate_groups()`

**Signature:**
```python
def aggregate_groups(
    df: pd.DataFrame,
    group_columns: list[str],
    aggregations: dict[str, list[str]]
) -> Result[pd.DataFrame, AggregationError]:
    """Group and aggregate DataFrame.

    Args:
        df: Source DataFrame
        group_columns: Columns to group by
        aggregations: Dict mapping column names to function lists

    Returns:
        Result[pd.DataFrame, AggregationError] - Aggregated DataFrame or error

    Errors:
        - AggregationFailedError: Aggregation failed
    """
```

**Implementation Requirements:**
1. Execute `df.groupby(group_columns, as_index=False, dropna=False).agg(aggregations)`
2. Flatten MultiIndex columns (if multiple functions)
3. Catch any exception → AggregationFailedError

**Test Cases:**
- ✅ Simple: `df, ["Region"], {"Sales": ["sum"]}`
- ✅ Multiple functions: `df, ["Region"], {"Sales": ["sum", "mean"]}`
- ✅ Multiple columns: `df, ["Region", "Category"], {"Sales": ["sum"], "Profit": ["mean"]}`

### Error Types Required

```python
@immutable
@dataclass
class InvalidFormatError:
    """Invalid aggregation format."""
    spec: str
    expected_format: str = "column:func1,func2"

@immutable
@dataclass
class NoValidSpecsError:
    """No valid aggregation specifications."""
    pass

@immutable
@dataclass
class GroupColumnsNotFoundError:
    """Group columns don't exist."""
    missing: list[str]
    available: list[str]

@immutable
@dataclass
class AggColumnsNotFoundError:
    """Aggregation columns don't exist."""
    missing: list[str]
    available: list[str]

@immutable
@dataclass
class OverlappingColumnsError:
    """Group and aggregation columns overlap."""
    overlap: list[str]

@immutable
@dataclass
class AggregationFailedError:
    """Aggregation failed."""
    message: str

ParseError = InvalidFormatError | InvalidFunctionError | NoValidSpecsError
AggregationValidationError = (
    GroupColumnsNotFoundError |
    AggColumnsNotFoundError |
    OverlappingColumnsError
)
AggregationError = AggregationFailedError
```

---

## Operation 5: Comparing

**Source File:** `commands/compare.py` (324 lines)
**Target:** `operations/comparing.py`

### Current Implementation Analysis

**Lines 146-174:** Key columns parsing and validation
**Lines 176-218:** Core comparison logic
**Lines 220-281:** Result building

### Required Functions

#### 5.1 `validate_key_columns()`

**Signature:**
```python
def validate_key_columns(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    key_columns: list[str] | None
) -> Result[list[str], ComparisonValidationError]:
    """Validate key columns for comparison.

    Args:
        df1: First DataFrame
        df2: Second DataFrame
        key_columns: Columns to use as key, or None for row position

    Returns:
        Result[list[str], ComparisonValidationError]
        Validated key columns (or ['_row_num'] if None)

    Errors:
        - KeyColumnsNotFoundError: Key columns don't exist in df1
        - KeyColumnsNotFoundError2: Key columns don't exist in df2
    """
```

**Implementation Requirements:**
- If key_columns is None, return `['_row_num']`
- Check all key columns exist in df1
- Check all key columns exist in df2
- Return appropriate error if missing

**Test Cases:**
- ✅ With keys: `df1, df2, ["ID"]`
- ✅ Without keys: `df1, df2, None` → `['_row_num']`
- ❌ Missing in df1: `df1, df2, ["Missing"]` → KeyColumnsNotFoundError
- ❌ Missing in df2: `df1, df2, ["ID", "Missing"]` → KeyColumnsNotFoundError2

#### 5.2 `find_differences()`

**Signature:**
```python
def find_differences(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    key_columns: list[str]
) -> DifferencesResult:
    """Find differences between two DataFrames.

    Args:
        df1: First DataFrame (baseline)
        df2: Second DataFrame (comparison)
        key_columns: Columns to use as key for matching rows

    Returns:
        DifferencesResult with:
            - only_df1: Index of rows only in df1 (deleted)
            - only_df2: Index of rows only in df2 (added)
            - modified_rows: Index of rows in both but with different values
    """
```

**Implementation Requirements:**
1. Set key columns as index for both DataFrames
2. Find `df1.index.difference(df2.index)` → only in df1
3. Find `df2.index.difference(df1.index)` → only in df2
4. Find `df1.index.intersection(df2.index)` → in both
5. For common indices, compare rows:
   - Iterate through common index
   - Compare each column value
   - Handle NaN comparisons (NaN == NaN is OK)
   - Collect indices where values differ

**Test Cases:**
- ✅ Added rows: df2 has new rows
- ✅ Deleted rows: df2 missing rows from df1
- ✅ Modified rows: Same keys, different values
- ✅ No differences: Identical DataFrames

#### 5.3 `compare_rows()`

**Signature:**
```python
def compare_rows(row1: pd.Series, row2: pd.Series) -> bool:
    """Compare two rows for equality.

    Args:
        row1: First row
        row2: Second row

    Returns:
        True if rows are equal, False otherwise

    Comparison rules:
        - NaN values are considered equal
        - Different types are not equal
        - Values must be exactly equal
    """
```

**Implementation Requirements:**
- Iterate through columns in row1
- Handle NaN: `pd.isna(val1) and pd.isna(val2)` → equal
- Handle mixed NaN: `pd.isna(val1) or pd.isna(val2)` → not equal
- Compare values: `val1 != val2` → not equal
- Return False on first difference, True if all equal

#### 5.4 `build_comparison_result()`

**Signature:**
```python
def build_comparison_result(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    differences: DifferencesResult,
    key_columns: list[str]
) -> pd.DataFrame:
    """Build comparison result DataFrame.

    Args:
        df1: First DataFrame (indexed by key_columns)
        df2: Second DataFrame (indexed by key_columns)
        differences: DifferencesResult from find_differences()
        key_columns: Key columns (for reset)

    Returns:
        DataFrame with _diff_status column indicating:
            - 'added': Row only in df2
            - 'deleted': Row only in df1
            - 'modified (old)': Old version of modified row
            - 'modified (new)': New version of modified row
    """
```

**Implementation Requirements:**
1. Initialize empty result list
2. For rows in `only_df2`:
   - Get row from df2
   - Add `_diff_status = 'added'`
   - Add to result
3. For rows in `only_df1`:
   - Get row from df1
   - Add `_diff_status = 'deleted'`
   - Add to result
4. For rows in `modified_rows`:
   - Get row from df1, add `_diff_status = 'modified (old)'`
   - Get row from df2, add `_diff_status = 'modified (new)'`
   - Add both to result
5. Create DataFrame from result list
6. Reset index (make key_columns regular columns)
7. Remove `_row_num` if present
8. Reorder columns to put `_diff_status` first

#### 5.5 `compare_dataframes()`

**Signature:**
```python
def compare_dataframes(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    key_columns: list[str] | None = None
) -> Result[ComparisonResult, CompareError]:
    """Compare two DataFrames.

    Args:
        df1: First DataFrame (baseline)
        df2: Second DataFrame (comparison)
        key_columns: Columns to use as key, or None for row position

    Returns:
        Result[ComparisonResult, CompareError]

    Errors:
        - ComparisonFailedError: Comparison failed

    ComparisonResult contains:
        - df_result: Comparison DataFrame with _diff_status
        - added_count: Number of added rows
        - deleted_count: Number of deleted rows
        - modified_count: Number of modified rows
    """
```

**Implementation Requirements:**
1. Validate key columns
2. Handle empty DataFrames
3. Set key columns as index (or add `_row_num` if None)
4. Find differences
5. Build comparison result
6. Return counts and DataFrame

### Error Types Required

```python
@immutable
@dataclass
class KeyColumnsNotFoundError:
    """Key columns don't exist in first DataFrame."""
    missing: list[str]
    available: list[str]

@immutable
@dataclass
class KeyColumnsNotFoundError2:
    """Key columns don't exist in second DataFrame."""
    missing: list[str]
    available: list[str]

@immutable
@dataclass
class ComparisonFailedError:
    """Comparison failed."""
    message: str

@immutable
@dataclass
class DifferencesResult:
    """Result of finding differences."""
    only_df1: set  # Indices only in df1
    only_df2: set  # Indices only in df2
    modified_rows: list  # Indices with different values

@immutable
@dataclass
class ComparisonResult:
    """Result of comparing DataFrames."""
    df_result: pd.DataFrame
    added_count: int
    deleted_count: int
    modified_count: int

ComparisonValidationError = (
    KeyColumnsNotFoundError |
    KeyColumnsNotFoundError2
)

CompareError = ComparisonFailedError
```

---

## Implementation Order

### Recommended Sequence

**Day 1:**
1. Create `models/error_types.py` (foundational)
2. Implement `operations/filtering.py` (most complex, establishes patterns)

**Day 2:**
3. Implement `operations/sorting.py` (simpler, reuses patterns)
4. Implement `operations/pivoting.py` (medium complexity)

**Day 3:**
5. Implement `operations/aggregating.py` (medium complexity)
6. Implement `operations/comparing.py` (most complex logic)

### Dependency Graph

```
error_types.py (foundational)
    ↓
filtering.py (establishes patterns)
    ↓
sorting.py (reuses patterns)
    ↓
pivoting.py, aggregating.py (similar complexity)
    ↓
comparing.py (most complex)
```

---

## File Structure

### New Files to Create

```
excel_toolkit/
├── models/
│   └── error_types.py          # NEW: All error ADTs
├── operations/
│   ├── __init__.py             # UPDATE: Export operations
│   ├── filtering.py            # NEW: Filter operations
│   ├── sorting.py              # NEW: Sort operations
│   ├── pivoting.py             # NEW: Pivot operations
│   ├── aggregating.py          # NEW: Aggregate operations
│   └── comparing.py            # NEW: Compare operations
```

### Updated Files

```
excel_toolkit/
├── operations/
│   └── __init__.py             # UPDATE: Add exports
```

---

## Testing Requirements

### Unit Tests Structure

```
tests/unit/operations/
├── __init__.py
├── test_filtering.py           # Test filtering operations
├── test_sorting.py             # Test sorting operations
├── test_pivoting.py            # Test pivoting operations
├── test_aggregating.py         # Test aggregating operations
└── test_comparing.py           # Test comparing operations
```

### Test Coverage Goals

- **Line Coverage:** >90%
- **Branch Coverage:** >80%
- **All error paths tested**
- **All edge cases covered**

### Test Cases Summary

| Operation | Test Cases | Edge Cases |
|-----------|------------|------------|
| Filtering | 15+ | Empty result, type errors, security |
| Sorting | 10+ | Mixed types, NaN handling |
| Pivoting | 12+ | MultiIndex, empty groups |
| Aggregating | 12+ | Multi functions, empty groups |
| Comparing | 15+ | Empty files, all differences types |

---

## Validation Checklist

For each operation module:

### Code Quality
- [ ] All functions have type hints
- [ ] All functions have docstrings
- [ ] Result types used consistently
- [ ] Error types are immutable dataclasses
- [ ] No CLI dependencies (no typer, no typer.echo)
- [ ] Pure functions (no side effects)

### Functionality
- [ ] All error cases handled
- [ ] All edge cases tested
- [ ] NaN handling correct
- [ ] Empty DataFrame handling correct
- [ ] Type conversions safe

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass (after command refactoring)
- [ ] Coverage threshold met
- [ ] All error paths tested

### Documentation
- [ ] Module docstring
- [ ] Function docstrings complete
- [ ] Type hints accurate
- [ ] Error types documented

---

## Migration Command Checklist

For each command file after operations are created:

### Remove from Command
- [ ] Business logic functions
- [ ] Internal helper functions
- [ ] Error handling logic (moved to operations)
- [ ] Validation logic (moved to operations)

### Add to Command
- [ ] Imports from operations
- [ ] Error-to-message conversion functions
- [ ] Result handling with is_ok/is_err

### Keep in Command
- [ ] Typer command function definition
- [ ] File I/O coordination
- [ ] Output formatting/display
- [ ] User-friendly error messages

---

## Risk Assessment

### High Risk Areas

1. **Security in filtering**
   - Risk: Code injection through pandas.eval()
   - Mitigation: Comprehensive validation, sandboxing

2. **Type handling in sorting**
   - Risk: Mixed type columns cause crashes
   - Mitigation: Pre-validation, clear error messages

3. **Memory usage in comparing**
   - Risk: Large DataFrames cause memory issues
   - Mitigation: Chunking, streaming (future)

### Medium Risk Areas

1. **MultiIndex flattening**
   - Risk: Column name collisions
   - Mitigation: Thorough testing

2. **NaN handling**
   - Risk: Inconsistent NaN comparisons
   - Mitigation: Explicit NaN checks everywhere

### Low Risk Areas

1. **Column validation**
   - Risk: Missing columns not caught
   - Mitigation: Comprehensive validation

---

## Success Metrics

### Quantitative
- [ ] 5 operation modules created
- [ ] 50+ functions implemented
- [ ] 100+ unit tests written
- [ ] >90% test coverage
- [ ] Zero CLI dependencies in operations

### Qualitative
- [ ] Commands reduced to <100 lines each
- [ ] Clear separation of concerns
- [ ] Reusable business logic
- [ ] Type-safe error handling
- [ ] Comprehensive documentation

---

## Next Steps

1. **Review this specification** with team
2. **Confirm approach and priorities**
3. **Create error_types.py** (foundational)
4. **Implement filtering.py** (establish patterns)
5. **Write comprehensive tests** for each module
6. **Refactor commands** to use operations
7. **Run integration tests** to verify functionality

---

**Document Version:** 1.0
**Last Updated:** 2026-01-16
**Author:** Claude Code Analysis
**Status:** Ready for Implementation
