# Excel Toolkit - Implementation Roadmap

**Last Updated:** 2026-01-16
**Status:** ✅ Phase 1 COMPLETE (5/5 operations implemented)

---

## Overview

This roadmap tracks the implementation of the operations layer for the Excel Toolkit. The operations layer separates business logic from CLI concerns, enabling:
- Unit testing without CLI dependencies
- Code reuse in pipelines and templates
- Import by external packages
- Clear separation of concerns

**Current Progress:** ✅ Phase 1 COMPLETE - 100% of core operations implemented

---

## Phase 1: Core Operations (✅ COMPLETE)

**Status:** 5/5 operations implemented
**Completed:** 2026-01-16
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

#### 5. Pivoting Operations
**File:** `excel_toolkit/operations/pivoting.py`
**Status:** ✅ Complete
**Tests:** 56 passing
**Commit:** `da246eb`

Functions:
- `validate_aggregation_function()` - Function validation and normalization
- `validate_pivot_columns()` - Column existence validation
- `parse_fill_value()` - Fill value parsing (None, 0, nan, int, float, string)
- `flatten_multiindex()` - MultiIndex flattening for columns and index
- `create_pivot_table()` - Create pivot tables

Features:
- 11 aggregation functions (sum, mean, avg→mean, count, min, max, median, std, var, first, last)
- Multiple rows, columns, and values
- Fill value handling
- MultiIndex flattening
- Column name generation

#### 6. Aggregating Operations
**File:** `excel_toolkit/operations/aggregating.py`
**Status:** ✅ Complete
**Tests:** 38 passing
**Commit:** `86848cb`

Functions:
- `parse_aggregation_specs()` - Parse "column:func1,func2" format
- `validate_aggregation_columns()` - Validate columns exist and don't overlap
- `aggregate_groups()` - Groupby and aggregation

Features:
- Smart parsing with stateful handling of functions
- Normalizes "avg" to "mean"
- Merges duplicate column specs
- 11 aggregation functions
- MultiIndex flattening with trailing underscore removal
- Empty group handling

#### 7. Comparing Operations
**File:** `excel_toolkit/operations/comparing.py`
**Status:** ✅ Complete
**Tests:** 44 passing
**Commit:** `318719a`

Functions:
- `validate_key_columns()` - Validate key columns exist in both DataFrames
- `compare_rows()` - Compare two rows for equality with NaN handling
- `find_differences()` - Find added, deleted, and modified rows
- `build_comparison_result()` - Build result DataFrame with status column
- `compare_dataframes()` - Main comparison function

Features:
- Key columns or row position comparison
- NaN equality handling (NaN == NaN is OK)
- MultiIndex support via dict conversion
- Comprehensive difference tracking
- Status column ("added", "deleted", "modified", "unchanged")
- Column ordering (keys, status, others)

---

### ✅ Phase 1 Summary

**All 5 core operations completed:**

1. ✅ Filtering Operations (46 tests, commit `3fabc0f`)
2. ✅ Sorting Operations (23 tests, commit `6b3c2bb`)
3. ✅ Pivoting Operations (56 tests, commit `da246eb`)
4. ✅ Aggregating Operations (38 tests, commit `86848cb`)
5. ✅ Comparing Operations (44 tests, commit `318719a`)

**Total Statistics:**
- 207 tests passing
- 5 core operations implemented
- 5 commits (atomic per operation)
- ~3,500 lines of production code
- ~3,000 lines of test code
- Zero CLI dependencies in operations
- All operations return Result types for explicit error handling
- Comprehensive error types with immutable dataclasses
- Full test coverage of all error paths

**Key Achievements:**
- ✅ Complete separation of business logic from CLI
- ✅ Unit testable without CLI dependencies
- ✅ Reusable in pipelines and templates
- ✅ Importable by external packages
- ✅ Type-safe error handling with Result types
- ✅ Immutable error data structures
- ✅ Comprehensive test coverage
- ✅ All operations follow consistent patterns

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
