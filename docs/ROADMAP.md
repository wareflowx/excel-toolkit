# Excel Toolkit - Implementation Roadmap

**Last Updated:** 2026-01-16
**Status:** Phase 1 in Progress (2/5 operations completed)

---

## Overview

This roadmap tracks the implementation of the operations layer for the Excel Toolkit. The operations layer separates business logic from CLI concerns, enabling:
- Unit testing without CLI dependencies
- Code reuse in pipelines and templates
- Import by external packages
- Clear separation of concerns

**Current Progress:** 40% of Phase 1 complete

---

## Phase 1: Core Operations (In Progress)

**Status:** 2/5 operations implemented
**Estimated Remaining:** 1-2 days
**Priority:** CRITICAL

### ✅ Completed Operations

#### 1. Immutable Dataclass Decorator
**File:** `excel_toolkit/fp/immutable.py`
**Status:** ✅ Complete
**Tests:** 39 passing
**Commit:** `d740279`

Features:
- `@immutable` decorator for frozen dataclasses
- Must be applied AFTER `@dataclass` decorator
- Creates immutable data structures

#### 2. Error Type ADTs
**File:** `excel_toolkit/models/error_types.py`
**Status:** ✅ Complete
**Tests:** 39 passing
**Commit:** `d740279`

Error Types (20+):
- Validation Errors (12 types)
- Filter Errors (4 types)
- Sort Errors (2 types)
- Pivot Errors (4 types)
- Parse Errors (3 types)
- Aggregation Errors (3 types)
- Compare Errors (3 types)

#### 3. Filtering Operations
**File:** `excel_toolkit/operations/filtering.py`
**Status:** ✅ Complete
**Tests:** 46 passing
**Commit:** `3fabc0f`

Functions:
- `validate_condition()` - Security and syntax validation
- `normalize_condition()` - Transform user syntax to pandas
- `apply_filter()` - Apply filter with column selection and limits
- `_extract_column_name()` - Helper function

Features:
- Security validation against dangerous patterns (import, exec, eval, __, etc.)
- Syntax validation (balanced parentheses, brackets, quotes)
- Max condition length check (1000 characters)
- Normalization: "is None" → `.isna()`, "between X and Y" → ">= X and <= Y"
- Column selection after filtering
- Row limiting

#### 4. Sorting Operations
**File:** `excel_toolkit/operations/sorting.py`
**Status:** ✅ Complete
**Tests:** 23 passing
**Commit:** `6b3c2bb`

Functions:
- `validate_sort_columns()` - Column existence validation
- `sort_dataframe()` - Sort with multiple options

Features:
- Single and multi-column sorting
- Ascending and descending order
- NaN placement control (first/last)
- Row limiting
- Mixed type error detection

---

### ⏳ Pending Operations

#### 5. Pivoting Operations
**File:** `excel_toolkit/operations/pivoting.py`
**Status:** ❌ Not Started
**Estimated:** 3-4 hours
**Priority:** High

Required Functions:
```python
def validate_aggregation_function(func: str) -> Result[str, ValidationError]
    """Validate and normalize aggregation function name."""

def validate_pivot_columns(
    df: pd.DataFrame,
    rows: list[str],
    columns: list[str],
    values: list[str]
) -> Result[None, PivotValidationError]
    """Validate pivot columns exist in DataFrame."""

def parse_fill_value(value: str | None) -> Any
    """Parse fill value for pivot table."""

def flatten_multiindex(df: pd.DataFrame) -> pd.DataFrame
    """Flatten MultiIndex columns and index in pivot table."""

def create_pivot_table(
    df: pd.DataFrame,
    rows: list[str],
    columns: list[str],
    values: list[str],
    aggfunc: str = "sum",
    fill_value: Any = None
) -> Result[pd.DataFrame, PivotError]
    """Create pivot table from DataFrame."""
```

Implementation Requirements:
1. Validate aggregation function (sum, mean, avg, count, min, max, median, std, var, first, last)
2. Normalize "avg" to "mean"
3. Validate all column lists exist
4. Parse fill value (None, 0, nan, int, float, string)
5. Execute `pd.pivot_table()` with MultiIndex handling
6. Flatten MultiIndex columns/rows
7. Reset index to make rows into columns

Test Cases Required:
- Valid function names (sum, mean, avg → mean, count, etc.)
- Invalid function name
- Missing row columns
- Missing column columns
- Missing value columns
- Fill value parsing (None, "none", "0", "nan", numbers, strings)
- Simple pivot (single row, column, value)
- Multiple values
- MultiIndex flattening
- Empty groups
- Dry-run preview

#### 6. Aggregating Operations
**File:** `excel_toolkit/operations/aggregating.py`
**Status:** ❌ Not Started
**Estimated:** 3-4 hours
**Priority:** High

Required Functions:
```python
def parse_aggregation_specs(
    specs: str
) -> Result[dict[str, list[str]], ParseError]
    """Parse aggregation specifications from command line."""

def validate_aggregation_columns(
    df: pd.DataFrame,
    group_columns: list[str],
    agg_columns: list[str]
) -> Result[None, AggregationValidationError]
    """Validate aggregation columns."""

def aggregate_groups(
    df: pd.DataFrame,
    group_columns: list[str],
    aggregations: dict[str, list[str]]
) -> Result[pd.DataFrame, AggregationError]
    """Group and aggregate DataFrame."""
```

Implementation Requirements:
1. Parse specs format: "column:func1,func2,column2:func3"
2. Validate each function name
3. Normalize "avg" to "mean"
4. Merge multiple specs for same column
5. Validate group columns exist
6. Validate agg columns exist
7. Check no overlap between group and agg columns
8. Execute `df.groupby().agg()` with MultiIndex flattening

Test Cases Required:
- Simple spec: "Revenue:sum"
- Multiple functions: "Sales:sum,mean"
- Multiple columns: "Amount:sum,Profit:mean"
- Invalid format (missing colon)
- Invalid function name
- Overlapping group/agg columns
- Missing group columns
- Missing agg columns
- MultiIndex column flattening
- Empty groups

#### 7. Comparing Operations
**File:** `excel_toolkit/operations/comparing.py`
**Status:** ❌ Not Started
**Estimated:** 4-5 hours
**Priority:** High

Required Functions:
```python
def validate_key_columns(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    key_columns: list[str] | None
) -> Result[list[str], ComparisonValidationError]
    """Validate key columns for comparison."""

def find_differences(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    key_columns: list[str]
) -> DifferencesResult
    """Find differences between two DataFrames."""

def compare_rows(row1: pd.Series, row2: pd.Series) -> bool
    """Compare two rows for equality."""

def build_comparison_result(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    differences: DifferencesResult,
    key_columns: list[str]
) -> pd.DataFrame
    """Build comparison result DataFrame."""

def compare_dataframes(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    key_columns: list[str] | None = None
) -> Result[ComparisonResult, CompareError]
    """Compare two DataFrames."""
```

Implementation Requirements:
1. Handle None key_columns → use row position
2. Validate key columns exist in both DataFrames
3. Set key columns as index
4. Find rows only in df1 (deleted)
5. Find rows only in df2 (added)
6. Find common indices and compare values
7. Handle NaN comparisons (NaN == NaN is OK)
8. Build result with `_diff_status` column
9. Reset index and reorder columns

Data Structures Needed:
```python
@dataclass
class DifferencesResult:
    only_df1: set  # Indices only in df1 (deleted)
    only_df2: set  # Indices only in df2 (added)
    modified_rows: list  # Indices with different values

@dataclass
class ComparisonResult:
    df_result: pd.DataFrame
    added_count: int
    deleted_count: int
    modified_count: int
```

Test Cases Required:
- Compare with key columns
- Compare without key columns (row position)
- Added rows only
- Deleted rows only
- Modified rows
- No differences
- All differences types
- Empty DataFrames
- NaN handling
- Key columns missing in df1
- Key columns missing in df2

---

## Phase 2: Support Operations (Not Started)

**Status:** 0/4 operations implemented
**Estimated:** 1-2 days
**Priority:** Medium

### Pending Operations

#### 1. Cleaning Operations
**File:** `excel_toolkit/operations/cleaning.py`
**Functions:**
- `clean_dataframe()` - Apply multiple cleaning operations
- `trim_whitespace()` - Trim whitespace from strings
- `remove_duplicates()` - Remove duplicate rows
- `fill_missing_values()` - Fill missing values
- `standardize_columns()` - Standardize column names

#### 2. Transforming Operations
**File:** `excel_toolkit/operations/transforming.py`
**Functions:**
- `transform_column()` - Transform column values
- `apply_expression()` - Apply expression to create/modify column
- `cast_columns()` - Cast columns to specified types

#### 3. Joining Operations
**File:** `excel_toolkit/operations/joining.py`
**Functions:**
- `join_dataframes()` - Join two DataFrames
- `validate_join_columns()` - Validate join columns
- `merge_dataframes()` - Merge multiple DataFrames

#### 4. Validation Operations
**File:** `excel_toolkit/operations/validation.py`
**Functions:**
- `validate_dataframe()` - Validate against rules
- `validate_column_exists()` - Validate column exists
- `validate_column_type()` - Validate column type
- `validate_value_range()` - Validate value ranges
- `check_null_values()` - Check null values

---

## Phase 3: Command Refactoring (Not Started)

**Status:** 0/23 command files
**Estimated:** 2-3 days
**Priority:** High

### Commands to Refactor

For each command file:
1. Remove business logic
2. Import from operations
3. Keep only CLI concerns
4. Update error handling to use Result types
5. Reduce to <100 lines each

**Commands Using Implemented Operations:**
- `commands/filter.py` → Use `operations/filtering.py`
- `commands/sort.py` → Use `operations/sorting.py`

**Commands Pending Operations Implementation:**
- `commands/pivot.py` → Use `operations/pivoting.py`
- `commands/aggregate.py` → Use `operations/aggregating.py`
- `commands/compare.py` → Use `operations/comparing.py`

**Other Commands to Refactor:**
- `commands/clean.py` → Use `operations/cleaning.py`
- `commands/dedupe.py` → Use `operations/cleaning.py`
- `commands/fill.py` → Use `operations/cleaning.py`
- `commands/strip.py` → Use `operations/cleaning.py`
- `commands/transform.py` → Use `operations/transforming.py`
- `commands/join.py` → Use `operations/joining.py`
- `commands/merge.py` → Use `operations/joining.py`
- `commands/append.py` → Use `operations/joining.py`
- `commands/validate.py` → Use `operations/validation.py`

---

## Phase 4: Testing Infrastructure (Not Started)

**Status:** Partially complete (error_types, filtering, sorting have tests)
**Estimated:** 1-2 days
**Priority:** High

### Test Coverage Goals

**Unit Tests:**
- [x] Error types (39 tests)
- [x] Filtering operations (46 tests)
- [x] Sorting operations (23 tests)
- [ ] Pivoting operations (~50 tests)
- [ ] Aggregating operations (~50 tests)
- [ ] Comparing operations (~60 tests)
- [ ] Cleaning operations (~40 tests)
- [ ] Transforming operations (~30 tests)
- [ ] Joining operations (~35 tests)
- [ ] Validation operations (~30 tests)

**Target:** >90% code coverage

**Integration Tests:**
- Command workflow tests
- File I/O tests
- Format conversion tests

**Test Fixtures:**
- Sample Excel files
- Sample CSV files
- Edge case files (empty, large files, special characters)

---

## Phase 5: Documentation (Not Started)

**Estimated:** 1 day
**Priority:** Medium

### Documentation Tasks

- [ ] Update API documentation
- [ ] Add architecture diagrams
- [ ] Create contribution guide (CONTRIBUTING.md)
- [ ] Document operations layer patterns
- [ ] Add usage examples for each operation
- [ ] Document Result type patterns

---

## Success Metrics

### Quantitative
- [ ] 5 core operation modules created
- [ ] 4 support operation modules created
- [ ] 50+ functions implemented
- [ ] 400+ unit tests written
- [ ] >90% test coverage
- [ ] Zero CLI dependencies in operations
- [ ] All commands reduced to <100 lines

### Qualitative
- [ ] Clear separation of concerns
- [ ] Reusable business logic
- [ ] Type-safe error handling
- [ ] Comprehensive documentation
- [ ] All tests passing

---

## Dependencies

**Blockers:**
- None - operations can be implemented independently

**Recommended Order:**
1. Pivoting (most complex of remaining)
2. Aggregating (medium complexity)
3. Comparing (most complex overall)

**Can Be Done in Parallel:**
- Test writing alongside implementation
- Documentation alongside development

---

## Risks and Mitigations

### High Risk
- **Security in filtering** - ⚠️ Partially addressed
  - Risk: Code injection through pandas.eval()
  - Mitigation: Comprehensive validation implemented, needs review

### Medium Risk
- **Type handling in sorting** - ✅ Addressed
  - Risk: Mixed type columns cause crashes
  - Mitigation: Pre-validation and clear errors implemented

- **Memory usage in comparing** - ⚠️ Pending
  - Risk: Large DataFrames cause memory issues
  - Mitigation: Will need chunking/streaming (Phase 3)

### Low Risk
- **MultiIndex flattening** - ⚠️ Pending
  - Risk: Column name collisions
  - Mitigation: Thorough testing required

---

## Next Steps

### Immediate (This Session)

1. **Complete Phase 1 Core Operations**
   - [ ] Implement `operations/pivoting.py`
   - [ ] Implement `operations/aggregating.py`
   - [ ] Implement `operations/comparing.py`
   - [ ] Write tests for all three operations

2. **Update Operations Index**
   - [ ] Update `operations/__init__.py` to export all operations

### Short Term (Next Session)

1. **Refactor Commands**
   - [ ] Update `commands/filter.py` to use operations
   - [ ] Update `commands/sort.py` to use operations
   - [ ] Update `commands/pivot.py` to use operations
   - [ ] Update `commands/aggregate.py` to use operations
   - [ ] Update `commands/compare.py` to use operations

2. **Run Integration Tests**
   - [ ] Verify all commands work with operations layer
   - [ ] Fix any broken tests

### Medium Term (Future Sessions)

1. **Implement Support Operations**
   - Cleaning, Transforming, Joining, Validation

2. **Complete Command Refactoring**
   - All commands using operations layer

3. **Documentation**
   - API documentation
   - Architecture updates
   - Contribution guide

---

## Implementation Guidelines

### Code Style
- Follow existing patterns in filtering.py and sorting.py
- Use Result types for all fallible operations
- Comprehensive type hints
- Detailed docstrings
- Handle all error cases

### Testing Requirements
- Test all success paths
- Test all error paths
- Test edge cases (empty, NaN, single row, etc.)
- Test integration between functions
- Use fixtures for test data

### Commit Strategy
- Atomic commits per operation module
- Commit tests with implementation
- Write clear commit messages
- No push until complete

---

## Resources

### Design Documents
- `docs/issues/ISSUE_001_OPERATIONS_LAYER.md` - Detailed issue analysis
- `docs/issues/PHASE_1_DETAILED_SPEC.md` - Complete Phase 1 specification
- `docs/issues/MAIN.md` - All issues analysis

### Code References
- `excel_toolkit/operations/filtering.py` - Example implementation
- `excel_toolkit/operations/sorting.py` - Example implementation
- `excel_toolkit/models/error_types.py` - All error types

### Test References
- `tests/unit/operations/test_filtering.py` - Example test suite
- `tests/unit/operations/test_sorting.py` - Example test suite

---

**Total Estimated Time for Phase 1 Completion:** 5-7 hours
**Current Progress:** ~2 hours invested
**Remaining:** ~3-5 hours
