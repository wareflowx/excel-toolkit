# Phase 2: Support Operations - Detailed Specification

**Last Updated:** 2026-01-16
**Status:** Specification Complete - Ready for Implementation
**Dependencies:** Phase 1 (Core Operations) Complete

---

## Overview

Phase 2 implements support operations that complement the core operations from Phase 1. These operations focus on data preparation, transformation, and validation - essential steps in real-world data processing workflows.

**Design Principles:**
- Follow same patterns as Phase 1 operations
- Return `Result[T, E]` types for all operations
- Comprehensive error handling with specific error types
- Full test coverage for all operations
- No CLI dependencies
- Reusable and composable

**Estimated Implementation Time:** 6-8 hours
**Priority:** Medium (supports but doesn't block Phase 3)

---

## Operation 1: Cleaning Operations

**File:** `excel_toolkit/operations/cleaning.py`
**Estimated Time:** 2 hours
**Complexity:** Medium
**Test Count:** ~40 tests

### Purpose

Clean and sanitize DataFrames by handling common data quality issues like whitespace, duplicates, missing values, and inconsistent column names.

### Function Specifications

#### 1.1 `trim_whitespace()`

```python
def trim_whitespace(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    side: str = "both"
) -> Result[pd.DataFrame, CleaningError]:
    """Trim whitespace from string columns.

    Args:
        df: Source DataFrame
        columns: Columns to trim (None = all string columns)
        side: Which side to trim ("left", "right", "both")

    Returns:
        Result[pd.DataFrame, CleaningError] - Cleaned DataFrame or error

    Errors:
        - ColumnNotFoundError: Specified columns don't exist
        - CleaningFailedError: Trimming operation failed

    Implementation:
        - If columns is None, detect all string/object dtype columns
        - Apply str.strip() for "both", str.lstrip() for "left", str.rstrip() for "right"
        - Handle NaN values (preserve them)
        - Return modified copy of DataFrame

    Examples:
        columns=["Name"], side="both" → Trim " John " to "John"
        columns=None, side="left" → Trim all string columns on left
    """
```

**Test Cases:**
- Trim single column both sides
- Trim single column left side
- Trim single column right side
- Trim multiple columns
- Trim all string columns (columns=None)
- Handle NaN values (should preserve NaN)
- Column not found error
- Mixed dtype columns (should only trim strings)
- Empty DataFrame
- No string columns in DataFrame
- Whitespace-only strings become empty strings

#### 1.2 `remove_duplicates()`

```python
def remove_duplicates(
    df: pd.DataFrame,
    subset: list[str] | None = None,
    keep: str = "first"
) -> Result[pd.DataFrame, CleaningError]:
    """Remove duplicate rows from DataFrame.

    Args:
        df: Source DataFrame
        subset: Columns to consider for duplicates (None = all columns)
        keep: Which duplicate to keep ("first", "last", False)

    Returns:
        Result[pd.DataFrame, CleaningError] - Deduplicated DataFrame or error

    Errors:
        - ColumnNotFoundError: Specified columns don't exist
        - InvalidParameterError: Invalid keep value
        - CleaningFailedError: Deduplication failed

    Implementation:
        - Validate keep parameter is "first", "last", or False
        - If subset is provided, validate columns exist
        - Use df.drop_duplicates(subset=subset, keep=keep)
        - Return new DataFrame without duplicates

    Examples:
        subset=["ID"], keep="first" → Keep first occurrence of each ID
        subset=None, keep=False → Remove all duplicates entirely
    """
```

**Test Cases:**
- Remove duplicates with subset (single column)
- Remove duplicates with subset (multiple columns)
- Remove duplicates considering all columns
- Keep first occurrence
- Keep last occurrence
- Remove all duplicates (keep=False)
- No duplicates in DataFrame
- Column not found error
- Invalid keep parameter
- Empty DataFrame
- Single row DataFrame
- All rows are duplicates

#### 1.3 `fill_missing_values()`

```python
def fill_missing_values(
    df: pd.DataFrame,
    strategy: str | dict = "forward",
    columns: list[str] | None = None,
    value: Any = None
) -> Result[pd.DataFrame, CleaningError]:
    """Fill missing values in DataFrame.

    Args:
        df: Source DataFrame
        strategy: Fill strategy ("forward", "backward", "mean", "median", "constant", "drop")
                 Or dict mapping column names to strategies
        columns: Columns to fill (None = all columns with missing values)
        value: Value to use when strategy="constant"

    Returns:
        Result[pd.DataFrame, CleaningError] - DataFrame with filled values or error

    Errors:
        - ColumnNotFoundError: Specified columns don't exist
        - InvalidParameterError: Invalid strategy or parameters
        - CleaningFailedError: Fill operation failed

    Implementation:
        - Validate strategy parameter
        - If strategy is dict, validate each column exists
        - Apply fill based on strategy:
          - "forward": ffill()
          - "backward": bfill()
          - "mean": fillna with column mean
          - "median": fillna with column median
          - "constant": fillna with value
          - "drop": dropna()
        - Handle numeric vs non-numeric columns appropriately
        - Return modified copy

    Examples:
        strategy="forward", columns=["Age"] → Forward fill Age column
        strategy={"Age": "mean", "Name": "constant"}, value="Unknown"
    """
```

**Test Cases:**
- Forward fill single column
- Backward fill single column
- Mean fill numeric column
- Median fill numeric column
- Constant fill with value
- Drop rows with missing values
- Dict strategy with different strategies per column
- All columns with default strategy
- Column not found error
- Invalid strategy error
- Mean/median on non-numeric column (should error)
- Empty DataFrame
- No missing values
- All values missing

#### 1.4 `standardize_columns()`

```python
def standardize_columns(
    df: pd.DataFrame,
    case: str = "lower",
    separator: str = "_",
    remove_special: bool = True
) -> Result[pd.DataFrame, CleaningError]:
    """Standardize column names.

    Args:
        df: Source DataFrame
        case: Case conversion ("lower", "upper", "title", "snake")
        separator: Separator to use for multi-word columns
        remove_special: Whether to remove special characters

    Returns:
        Result[pd.DataFrame, CleaningError] - DataFrame with standardized columns or error

    Errors:
        - InvalidParameterError: Invalid case parameter
        - CleaningFailedError: Standardization failed

    Implementation:
        - Validate case parameter
        - Convert column names:
          - "lower": all lowercase
          - "upper": all uppercase
          - "title": Title Case
          - "snake": snake_case (Title Case with underscores)
        - Replace spaces with separator
        - If remove_special, remove non-alphanumeric chars (except separator)
        - Ensure column names are unique
        - Rename columns and return DataFrame

    Examples:
        case="snake", separator="_" → "First Name" → "First_Name"
        case="lower", remove_special=True → "First Name!" → "first_name"
    """
```

**Test Cases:**
- Lowercase conversion
- Uppercase conversion
- Title case conversion
- Snake case conversion
- Custom separator
- Remove special characters True
- Remove special characters False
- Handle existing separators
- Ensure uniqueness (duplicate after transformation)
- Invalid case parameter
- Empty DataFrame
- Single column
- Column names with spaces
- Column names with special characters
- Column names with numbers

#### 1.5 `clean_dataframe()`

```python
def clean_dataframe(
    df: pd.DataFrame,
    trim: bool = False,
    trim_columns: list[str] | None = None,
    remove_duplicates: bool = False,
    dup_subset: list[str] | None = None,
    dup_keep: str = "first",
    fill_strategy: str | dict | None = None,
    fill_value: Any = None,
    standardize: bool = False,
    standardize_case: str = "lower"
) -> Result[pd.DataFrame, CleaningError]:
    """Apply multiple cleaning operations in sequence.

    Args:
        df: Source DataFrame
        trim: Whether to trim whitespace
        trim_columns: Columns to trim (None = all string columns)
        remove_duplicates: Whether to remove duplicates
        dup_subset: Columns to check for duplicates
        dup_keep: Which duplicate to keep
        fill_strategy: Strategy for filling missing values
        fill_value: Value for constant fill
        standardize: Whether to standardize column names
        standardize_case: Case conversion for standardization

    Returns:
        Result[pd.DataFrame, CleaningError] - Cleaned DataFrame or error

    Errors:
        - Any errors from sub-operations

    Implementation:
        - Apply operations in order: standardize → trim → fill → remove_duplicates
        - Stop and return error if any operation fails
        - Return cleaned DataFrame

    Examples:
        Clean with all operations
        Clean with only trim and remove_duplicates
        Clean with custom parameters for each operation
    """
```

**Test Cases:**
- Apply all cleaning operations
- Apply subset of operations
- Apply operations in correct order
- Error propagates from sub-operations
- Empty DataFrame
- DataFrame with no issues

### Error Types Needed

```python
@dataclass
@immutable
class CleaningError(Error):
    """Base error for cleaning operations."""
    message: str

@dataclass
@immutable
class InvalidFillStrategyError(CleaningError):
    """Invalid fill strategy specified."""
    strategy: str
    valid_strategies: list[str]

@dataclass
@immutable
class FillFailedError(CleaningError):
    """Fill operation failed."""
    column: str
    reason: str
```

---

## Operation 2: Transforming Operations

**File:** `excel_toolkit/operations/transforming.py`
**Estimated Time:** 1.5 hours
**Complexity:** Medium
**Test Count:** ~30 tests

### Purpose

Transform DataFrame columns by applying expressions, casting types, or applying custom transformations. Essential for data preparation and feature engineering.

### Function Specifications

#### 2.1 `apply_expression()`

```python
def apply_expression(
    df: pd.DataFrame,
    column: str,
    expression: str,
    validate: bool = True
) -> Result[pd.DataFrame, TransformError]:
    """Apply expression to create or modify column.

    Args:
        df: Source DataFrame
        column: Column name to create or modify
        expression: Expression to evaluate (e.g., "Age * 2", "Name.upper()")
        validate: Whether to validate expression security

    Returns:
        Result[pd.DataFrame, TransformError] - Transformed DataFrame or error

    Errors:
        - DangerousPatternError: Expression contains dangerous patterns
        - InvalidExpressionError: Expression is invalid
        - ColumnNotFoundError: Referenced columns don't exist
        - TransformFailedError: Transformation failed

    Implementation:
        - If validate, check for dangerous patterns (same as filtering)
        - Use pandas.eval() with local_vars=df for column references
        - Support basic operations: +, -, *, /, **, comparisons, string methods
        - Create/modify column with result
        - Return modified DataFrame copy

    Security:
        - Validate against dangerous patterns if validate=True
        - Use restricted eval environment
        - Only allow column references and safe operations

    Examples:
        column="Total", expression="Price * Quantity"
        column="FullName", expression="FirstName + ' ' + LastName"
    """
```

**Test Cases:**
- Simple arithmetic expression
- Multiple column reference
- String concatenation
- Comparison expression
- Method calls (upper(), lower(), strip())
- Create new column
- Modify existing column
- Dangerous pattern detection
- Invalid expression syntax
- Column not found in expression
- Division by zero handling
- Empty DataFrame
- Expression with constants
- Complex nested expression

#### 2.2 `cast_columns()`

```python
def cast_columns(
    df: pd.DataFrame,
    column_types: dict[str, str]
) -> Result[pd.DataFrame, TransformError]:
    """Cast columns to specified types.

    Args:
        df: Source DataFrame
        column_types: Dictionary mapping column names to types
                     Types: "int", "float", "str", "bool", "datetime", "category"

    Returns:
        Result[pd.DataFrame, TransformError] - DataFrame with casted columns or error

    Errors:
        - ColumnNotFoundError: Specified columns don't exist
        - InvalidTypeError: Invalid type specified
        - CastFailedError: Casting failed (e.g., "abc" to int)

    Implementation:
        - Validate all columns exist
        - Validate all types are supported
        - For each column, apply conversion:
          - "int": pd.to_numeric(..., errors="raise").astype(int)
          - "float": pd.to_numeric(..., errors="raise")
          - "str": astype(str)
          - "bool": map to boolean (handle "true"/"false", "yes"/"no", 1/0)
          - "datetime": pd.to_datetime(..., errors="raise")
          - "category": astype("category")
        - Return modified DataFrame copy

    Examples:
        {"Age": "int", "Price": "float", "Active": "bool"}
    """
```

**Test Cases:**
- Cast single column to int
- Cast single column to float
- Cast single column to str
- Cast single column to bool
- Cast single column to datetime
- Cast single column to category
- Cast multiple columns to different types
- Invalid type error
- Column not found error
- Cast failed error (e.g., "abc" to int)
- Bool conversion from various formats ("yes", "no", 1, 0)
- Datetime parsing from different formats
- Empty DataFrame
- Column already correct type

#### 2.3 `transform_column()`

```python
def transform_column(
    df: pd.DataFrame,
    column: str,
    transformation: str | Callable,
    params: dict[str, Any] | None = None
) -> Result[pd.DataFrame, TransformError]:
    """Apply transformation to column.

    Args:
        df: Source DataFrame
        column: Column name to transform
        transformation: Named transformation or callable
                       Named: "log", "sqrt", "abs", "exp", "standardize", "normalize"
        params: Additional parameters for transformation

    Returns:
        Result[pd.DataFrame, TransformError] - Transformed DataFrame or error

    Errors:
        - ColumnNotFoundError: Column doesn't exist
        - InvalidTransformationError: Invalid transformation name
        - TransformFailedError: Transformation failed

    Implementation:
        - Validate column exists
        - If transformation is string, apply named transformation:
          - "log": np.log (handle negative/zero values)
          - "sqrt": np.sqrt (handle negative values)
          - "abs": np.abs
          - "exp": np.exp
          - "standardize": (x - mean) / std
          - "normalize": (x - min) / (max - min)
        - If transformation is callable, apply it to column
        - Handle errors (e.g., log of negative number)
        - Return modified DataFrame copy

    Examples:
        transformation="log" → Apply logarithm
        transformation="standardize" → Z-score normalization
        transformation=lambda x: x ** 2 → Square values
    """
```

**Test Cases:**
- Log transformation
- Sqrt transformation
- Abs transformation
- Exp transformation
- Standardize transformation (z-score)
- Normalize transformation (min-max)
- Custom callable transformation
- Invalid transformation name
- Column not found
- Log of negative/zero (should error)
- Sqrt of negative (should error)
- With params dict
- Empty column values
- Single value column

### Error Types Needed

```python
@dataclass
@immutable
class TransformError(Error):
    """Base error for transform operations."""
    message: str

@dataclass
@immutable
class InvalidExpressionError(TransformError):
    """Invalid expression provided."""
    expression: str
    reason: str

@dataclass
@immutable
class InvalidTypeError(TransformError):
    """Invalid type specified for casting."""
    type_name: str
    valid_types: list[str]

@dataclass
@immutable
class CastFailedError(TransformError):
    """Casting operation failed."""
    column: str
    target_type: str
    reason: str
```

---

## Operation 3: Joining Operations

**File:** `excel_toolkit/operations/joining.py`
**Estimated Time:** 1.5 hours
**Complexity:** High
**Test Count:** ~35 tests

### Purpose

Combine multiple DataFrames using various join operations. Essential for merging data from different sources.

### Function Specifications

#### 3.1 `validate_join_columns()`

```python
def validate_join_columns(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    on: list[str] | None = None,
    left_on: list[str] | None = None,
    right_on: list[str] | None = None,
    left_index: bool = False,
    right_index: bool = False
) -> Result[None, JoinValidationError]:
    """Validate join columns exist.

    Args:
        df1: Left DataFrame
        df2: Right DataFrame
        on: Columns to join on (both DataFrames)
        left_on: Left DataFrame join columns
        right_on: Right DataFrame join columns
        left_index: Use left DataFrame index
        right_index: Use right DataFrame index

    Returns:
        Result[None, JoinValidationError] - Success or error

    Errors:
        - InvalidJoinParametersError: Invalid parameter combination
        - JoinColumnsNotFoundError: Join columns don't exist

    Implementation:
        - Validate parameter combinations (e.g., can't use both 'on' and 'left_on')
        - If 'on' is specified, validate columns exist in both DataFrames
        - If 'left_on'/'right_on' specified, validate each in respective DataFrame
        - If index flags set, validate no conflicting parameters
        - Return ok(None) if valid

    Examples:
        on=["ID"] → Validate ID exists in both
        left_on=["Key1"], right_on=["Key2"] → Validate each in respective DataFrame
    """
```

**Test Cases:**
- Valid join with 'on'
- Valid join with 'left_on' and 'right_on'
- Valid join with left_index=True
- Valid join with right_index=True
- Valid join with both indexes
- Invalid combination (on with left_on)
- Column not found in left DataFrame
- Column not found in right DataFrame
- Empty column lists
- Invalid parameter combination

#### 3.2 `join_dataframes()`

```python
def join_dataframes(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    how: str = "inner",
    on: list[str] | None = None,
    left_on: list[str] | None = None,
    right_on: list[str] | None = None,
    left_index: bool = False,
    right_index: bool = False,
    suffixes: tuple[str, str] = ("_x", "_y")
) -> Result[pd.DataFrame, JoinError]:
    """Join two DataFrames.

    Args:
        df1: Left DataFrame
        df2: Right DataFrame
        how: Join type ("inner", "left", "right", "outer", "cross")
        on: Columns to join on (both DataFrames)
        left_on: Left DataFrame join columns
        right_on: Right DataFrame join columns
        left_index: Use left DataFrame index
        right_index: Use right DataFrame index
        suffixes: Suffixes for overlapping columns

    Returns:
        Result[pd.DataFrame, JoinError] - Joined DataFrame or error

    Errors:
        - InvalidJoinTypeError: Invalid join type
        - JoinColumnsNotFoundError: Join columns don't exist
        - JoinFailedError: Join operation failed

    Implementation:
        - Validate join type
        - Validate join columns using validate_join_columns()
        - Use pd.merge() with specified parameters
        - Handle suffixes for overlapping columns
        - Return joined DataFrame

    Examples:
        how="inner", on=["ID"] → Inner join on ID
        how="left", left_on=["Key1"], right_on=["Key2"] → Left join on different keys
    """
```

**Test Cases:**
- Inner join
- Left join
- Right join
- Outer join
- Cross join
- Join with 'on' parameter
- Join with 'left_on'/'right_on' parameters
- Join with indexes
- Custom suffixes
- Overlapping column handling
- Invalid join type
- Column not found
- Empty DataFrames
- No matching rows (inner join)
- All matching rows (inner join)
- Duplicate join keys

#### 3.3 `merge_dataframes()`

```python
def merge_dataframes(
    dataframes: list[pd.DataFrame],
    how: str = "inner",
    on: list[str] | None = None,
    suffixes: tuple[str, str] = ("_x", "_y")
) -> Result[pd.DataFrame, MergeError]:
    """Merge multiple DataFrames sequentially.

    Args:
        dataframes: List of DataFrames to merge (must have 2+)
        how: Join type for all merges
        on: Columns to join on (must exist in all DataFrames)
        suffixes: Suffixes for overlapping columns

    Returns:
        Result[pd.DataFrame, MergeError] - Merged DataFrame or error

    Errors:
        - InsufficientDataFramesError: Less than 2 DataFrames provided
        - MergeColumnsNotFoundError: Join columns don't exist in all DataFrames
        - MergeFailedError: Merge operation failed

    Implementation:
        - Validate at least 2 DataFrames
        - If 'on' specified, validate exists in all DataFrames
        - Sequentially merge DataFrames using reduce
        - Generate unique suffixes for each merge (_0, _1, _2, etc.)
        - Return final merged DataFrame

    Examples:
        Merge [df1, df2, df3] on ["ID"]
        Merge [df1, df2, df3] with no keys (cross merge)
    """
```

**Test Cases:**
- Merge 2 DataFrames
- Merge 3 DataFrames
- Merge 4+ DataFrames
- Merge with 'on' parameter
- Merge without 'on' parameter
- Different join types
- Column not found in one DataFrame
- Single DataFrame (error)
- Empty list (error)
- All DataFrames empty
- Some DataFrames empty
- Overlapping columns across all DataFrames

### Error Types Needed

```python
@dataclass
@immutable
class JoinError(Error):
    """Base error for join operations."""
    message: str

@dataclass
@immutable
class InvalidJoinTypeError(JoinError):
    """Invalid join type specified."""
    join_type: str
    valid_types: list[str]

@dataclass
@immutable
class MergeColumnsNotFoundError(JoinError):
    """Merge columns not found in all DataFrames."""
    missing: dict[int, list[str]]  # DataFrame index -> missing columns

@dataclass
@immutable
class InsufficientDataFramesError(JoinError):
    """Less than 2 DataFrames provided for merge."""
    count: int
```

---

## Operation 4: Validation Operations

**File:** `excel_toolkit/operations/validation.py`
**Estimated Time:** 2 hours
**Complexity:** Medium
**Test Count:** ~40 tests

### Purpose

Validate DataFrame data quality against business rules and constraints. Essential for ensuring data integrity and catching issues early.

### Function Specifications

#### 4.1 `validate_column_exists()`

```python
def validate_column_exists(
    df: pd.DataFrame,
    columns: list[str] | str
) -> Result[None, ValidationError]:
    """Validate that columns exist in DataFrame.

    Args:
        df: DataFrame to validate
        columns: Column name or list of column names

    Returns:
        Result[None, ValidationError] - Success or error

    Errors:
        - ColumnNotFoundError: One or more columns don't exist

    Implementation:
        - Convert single column to list
        - Check each column exists in df.columns
        - Collect missing columns
        - Return error with missing columns if any
        - Return ok(None) if all exist

    Examples:
        columns=["ID", "Name", "Age"]
        columns="ID"
    """
```

**Test Cases:**
- Single column exists
- Single column missing
- Multiple columns all exist
- Multiple columns some missing
- Multiple columns all missing
- Empty column list
- Empty DataFrame

#### 4.2 `validate_column_type()`

```python
def validate_column_type(
    df: pd.DataFrame,
    column_types: dict[str, str | list[str]]
) -> Result[None, ValidationError]:
    """Validate column data types.

    Args:
        df: DataFrame to validate
        column_types: Dictionary mapping column names to expected types
                      Types: "int", "float", "str", "bool", "datetime", "numeric"
                      Can specify list of valid types (e.g., ["int", "float"])

    Returns:
        Result[None, ValidationError] - Success or error

    Errors:
        - ColumnNotFoundError: Column doesn't exist
        - InvalidTypeError: Column type doesn't match expected

    Implementation:
        - Validate all columns exist
        - For each column, check dtype:
          - "int": check for integer dtype
          - "float": check for float dtype
          - "str": check for object/string dtype
          - "bool": check for boolean dtype
          - "datetime": check for datetime64 dtype
          - "numeric": check for int or float
        - If type is list, check if any match
        - Collect mismatches
        - Return error with mismatches if any

    Examples:
        {"Age": "int", "Name": "str", "Salary": ["int", "float"]}
    """
```

**Test Cases:**
- Single column type match
- Single column type mismatch
- Multiple columns all match
- Multiple columns some mismatch
- Multiple valid types (list)
- Column not found
- Numeric type check (int or float)
- Datetime type check
- Bool type check
- Empty column_types dict

#### 4.3 `validate_value_range()`

```python
def validate_value_range(
    df: pd.DataFrame,
    column: str,
    min_value: Any | None = None,
    max_value: Any | None = None,
    allow_equal: bool = True
) -> Result[None, ValidationError]:
    """Validate values are within range.

    Args:
        df: DataFrame to validate
        column: Column to validate
        min_value: Minimum value (None = no minimum)
        max_value: Maximum value (None = no maximum)
        allow_equal: Whether to allow equality with bounds

    Returns:
        Result[None, ValidationError] - Success or error

    Errors:
        - ColumnNotFoundError: Column doesn't exist
        - ValueOutOfRangeError: Values outside range

    Implementation:
        - Validate column exists
        - If both min_value and max_value are None, return ok(None)
        - Check values against range:
          - If allow_equal: value >= min and value <= max
          - If not allow_equal: value > min and value < max
        - Count violations
        - Return error with violation details if any

    Examples:
        column="Age", min_value=0, max_value=120
        column="Score", min_value=0, max_value=100, allow_equal=False
    """
```

**Test Cases:**
- All values in range
- Some values below minimum
- Some values above maximum
- Values on boundary (allow_equal=True)
- Values on boundary (allow_equal=False)
- Only min_value specified
- Only max_value specified
- Column not found
- Empty DataFrame
- All values violate
- NaN handling (should skip or error)

#### 4.4 `check_null_values()`

```python
def check_null_values(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    max_null_percent: float | None = None
) -> Result[dict[str, int], ValidationError]:
    """Check for null values in columns.

    Args:
        df: DataFrame to check
        columns: Columns to check (None = all columns)
        max_null_percent: Maximum allowed null percentage (0-100)
                          If specified and exceeded, return error

    Returns:
        Result[dict[str, int], ValidationError] - Null counts or error
        Dictionary maps column names to null counts

    Errors:
        - ColumnNotFoundError: Specified columns don't exist
        - NullValueThresholdExceededError: Null percentage exceeds threshold

    Implementation:
        - Validate columns exist
        - If columns is None, use all columns
        - Count null values in each column
        - If max_null_percent specified:
          - Calculate percentage for each column
          - Check if any exceed threshold
          - Return error if exceeded
        - Return dictionary of null counts

    Examples:
        columns=["Name", "Age"], max_null_percent=10
        columns=None → Check all columns
    """
```

**Test Cases:**
- No null values
- Some null values (no threshold)
- Some null values (below threshold)
- Some null values (above threshold)
- All null values
- Specific columns
- All columns
- Column not found
- Invalid max_null_percent (>100 or <0)
- Empty DataFrame
- Mix of columns with/without nulls

#### 4.5 `validate_dataframe()`

```python
def validate_dataframe(
    df: pd.DataFrame,
    rules: list[dict]
) -> Result[ValidationReport, ValidationError]:
    """Validate DataFrame against multiple rules.

    Args:
        df: DataFrame to validate
        rules: List of validation rule dictionaries
               Each rule: {"type": "...", "params": {...}}

    Returns:
        Result[ValidationReport, ValidationError] - Validation report or error

    Errors:
        - InvalidRuleError: Invalid rule type or parameters
        - ValidationError: Validation failed (returns report with errors)

    Rule Types:
        - "column_exists": Check columns exist
        - "column_type": Check column types
        - "value_range": Check value ranges
        - "null_check": Check null values
        - "unique": Check values are unique
        - "regex": Check values match regex pattern
        - "length": Check string lengths

    Implementation:
        - Validate each rule dictionary
        - Execute each rule in order
        - Collect all results
        - Return ValidationReport with:
          - passed: Number of rules passed
          - failed: Number of rules failed
          - errors: List of error details
          - warnings: List of warnings

    Examples:
        rules=[
            {"type": "column_exists", "params": {"columns": ["ID", "Name"]}},
            {"type": "value_range", "params": {"column": "Age", "min": 0, "max": 120}}
        ]
    """
```

**Test Cases:**
- All rules pass
- Some rules fail
- All rules fail
- Empty rules list
- Invalid rule type
- Missing required parameters in rule
- Multiple rule types
- Rule order execution
- Stop on first failure vs continue
- ValidationReport structure
- Empty DataFrame

#### 4.6 `validate_unique()`

```python
def validate_unique(
    df: pd.DataFrame,
    columns: list[str] | str,
    ignore_null: bool = True
) -> Result[None, ValidationError]:
    """Validate values are unique.

    Args:
        df: DataFrame to validate
        columns: Column(s) to check for uniqueness
        ignore_null: Whether to ignore null values when checking uniqueness

    Returns:
        Result[None, ValidationError] - Success or error

    Errors:
        - ColumnNotFoundError: Column doesn't exist
        - UniquenessViolationError: Duplicate values found

    Implementation:
        - Validate columns exist
        - If ignore_null, drop null values before checking
        - Check for duplicates
        - Return error with duplicate details if found
        - Return ok(None) if unique

    Examples:
        columns="ID"
        columns=["First Name", "Last Name"]
        columns="Email", ignore_null=False
    """
```

**Test Cases:**
- All values unique
- Some duplicates found
- All duplicates
- Single column uniqueness
- Multi-column uniqueness
- Ignore null True
- Ignore null False
- Column not found
- Empty DataFrame
- Single row

### Error Types Needed

```python
@dataclass
@immutable
class ValidationError(Error):
    """Base error for validation operations."""
    message: str

@dataclass
@immutable
class ValueOutOfRangeError(ValidationError):
    """Values outside specified range."""
    column: str
    min_value: Any
    max_value: Any
    violation_count: int

@dataclass
@immutable
class NullValueThresholdExceededError(ValidationError):
    """Null values exceed threshold."""
    column: str
    null_count: int
    null_percent: float
    threshold: float

@dataclass
@immutable
class UniquenessViolationError(ValidationError):
    """Duplicate values found."""
    columns: list[str]
    duplicate_count: int
    sample_duplicates: list

@dataclass
@immutable
class ValidationReport:
    """Report from validate_dataframe()."""
    passed: int
    failed: int
    errors: list[dict]
    warnings: list[dict]
```

---

## Implementation Order

**Recommended sequence:** 1 → 2 → 3 → 4

1. **Cleaning** (2 hours) - Foundation for other operations
2. **Transforming** (1.5 hours) - Builds on clean data
3. **Joining** (1.5 hours) - Independent, moderate complexity
4. **Validation** (2 hours) - Uses concepts from all previous

**Total Estimated Time:** 7 hours

---

## Test Coverage Goals

**Unit Tests:** ~145 tests total
- Cleaning: ~40 tests
- Transforming: ~30 tests
- Joining: ~35 tests
- Validation: ~40 tests

**Target:** >90% code coverage

**Integration Tests:**
- Multi-operation workflows (clean → transform → join → validate)
- Error propagation across operations
- Edge cases and boundary conditions

---

## Dependencies and Blockers

**Dependencies:**
- Phase 1 (Core Operations) - ✅ Complete
- Error types from `models/error_types.py`
- Result types from `fp/`
- Pandas operations

**Blockers:** None

**Can Start Immediately:** Yes

---

## Success Criteria

### Quantitative
- [ ] 4 support operation modules created
- [ ] 20+ functions implemented
- [ ] 145+ unit tests written
- [ ] >90% test coverage
- [ ] Zero CLI dependencies in operations
- [ ] All operations follow Phase 1 patterns

### Qualitative
- [ ] Consistent API with Phase 1 operations
- [ ] Comprehensive error handling
- [ ] Clear function documentation
- [ ] Reusable and composable operations
- [ ] All tests passing
- [ ] Code follows project style guidelines

---

## Integration with Phase 1

### How Phase 2 Uses Phase 1

1. **Cleaning → Filtering:** Clean data before filtering
2. **Transforming → Aggregating:** Transform before aggregating
3. **Joining → Comparing:** Join before comparing
4. **Validation → All:** Validate before any operation

### Example Workflows

**Data Import and Preparation:**
```
import_file → clean_dataframe → cast_columns → validate_dataframe → filter/sort/aggregate
```

**Data Merge and Analysis:**
```
join_dataframes → remove_duplicates → fill_missing_values → aggregate_groups → create_pivot_table
```

**Data Quality Pipeline:**
```
validate_dataframe → clean_dataframe → transform_column → validate_dataframe → export
```

---

## Next Steps After Phase 2

1. **Phase 3: Command Refactoring**
   - Update CLI commands to use Phase 1 and Phase 2 operations
   - Remove business logic from commands
   - Reduce command files to <100 lines each

2. **Integration Testing**
   - Test full workflows from CLI to operations
   - Verify all commands work with operations layer
   - Performance testing

3. **Documentation**
   - Update API documentation
   - Add usage examples for each operation
   - Create architecture diagrams

---

## Conclusion

Phase 2 completes the operations layer by adding support operations that complement the core operations from Phase 1. Together, they provide a comprehensive toolkit for data manipulation and validation that can be used independently from the CLI.

**Ready for Implementation:** Yes
**Estimated Completion:** 1-2 days
**Risk Level:** Low (builds on proven patterns from Phase 1)
