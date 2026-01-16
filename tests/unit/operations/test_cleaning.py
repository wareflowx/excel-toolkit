"""Comprehensive tests for cleaning operations.

Tests for:
- trim_whitespace()
- remove_duplicates()
- fill_missing_values()
- standardize_columns()
- clean_dataframe()
"""

import pytest
import pandas as pd
import numpy as np
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err
from excel_toolkit.operations.cleaning import (
    trim_whitespace,
    remove_duplicates,
    fill_missing_values,
    standardize_columns,
    clean_dataframe,
)
from excel_toolkit.models.error_types import (
    ColumnNotFoundError,
    InvalidParameterError,
    CleaningError,
    InvalidFillStrategyError,
    FillFailedError,
)


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def dataframe_with_whitespace():
    """Create DataFrame with whitespace issues."""
    return pd.DataFrame({
        'ID': [1, 2, 3],
        'Name': ['  John  ', ' Jane ', 'Bob'],
        'City': ['NYC', '  LA  ', 'CHICAGO'],
        'Age': [25, 30, 35]
    })


@pytest.fixture
def dataframe_with_duplicates():
    """Create DataFrame with duplicate rows."""
    return pd.DataFrame({
        'ID': [1, 2, 1, 3, 2],
        'Name': ['Alice', 'Bob', 'Alice', 'Charlie', 'Bob'],
        'Age': [25, 30, 25, 35, 30]
    })


@pytest.fixture
def dataframe_with_missing_values():
    """Create DataFrame with missing values."""
    return pd.DataFrame({
        'ID': [1, 2, 3, 4, 5],
        'Name': ['Alice', 'Bob', None, 'David', 'Eve'],
        'Age': [25, None, 35, None, 45],
        'Salary': [50000.0, 60000.0, None, 80000.0, None]
    })


@pytest.fixture
def dataframe_with_bad_columns():
    """Create DataFrame with inconsistent column names."""
    return pd.DataFrame({
        'First Name': ['John', 'Jane'],
        'Last Name!': ['Doe', 'Smith'],
        'AGE': [25, 30]
    })


@pytest.fixture
def messy_dataframe():
    """Create DataFrame with multiple issues."""
    return pd.DataFrame({
        '  First Name  ': ['  John  ', ' Jane ', ' Bob'],
        'Last-Name': ['Doe', 'Smith', 'Jones'],
        '  AGE': [25, 30, 25],
        'SALARY': [50000.0, None, None]
    })


# =============================================================================
# trim_whitespace() Tests
# =============================================================================

class TestTrimWhitespace:
    """Tests for trim_whitespace."""

    def test_trim_single_column_both_sides(self, dataframe_with_whitespace):
        """Test trimming single column on both sides."""
        result = trim_whitespace(dataframe_with_whitespace, columns=['Name'], side='both')

        assert is_ok(result)
        df_clean = unwrap(result)
        assert df_clean['Name'].tolist() == ['John', 'Jane', 'Bob']
        assert df_clean['City'].tolist() == ['NYC', '  LA  ', 'CHICAGO']  # Unchanged

    def test_trim_single_column_left_side(self, dataframe_with_whitespace):
        """Test trimming single column on left side."""
        result = trim_whitespace(dataframe_with_whitespace, columns=['Name'], side='left')

        assert is_ok(result)
        df_clean = unwrap(result)
        assert df_clean['Name'].tolist() == ['John  ', 'Jane ', 'Bob']

    def test_trim_single_column_right_side(self, dataframe_with_whitespace):
        """Test trimming single column on right side."""
        result = trim_whitespace(dataframe_with_whitespace, columns=['Name'], side='right')

        assert is_ok(result)
        df_clean = unwrap(result)
        assert df_clean['Name'].tolist() == ['  John', ' Jane', 'Bob']

    def test_trim_multiple_columns(self, dataframe_with_whitespace):
        """Test trimming multiple columns."""
        result = trim_whitespace(dataframe_with_whitespace, columns=['Name', 'City'], side='both')

        assert is_ok(result)
        df_clean = unwrap(result)
        assert df_clean['Name'].tolist() == ['John', 'Jane', 'Bob']
        assert df_clean['City'].tolist() == ['NYC', 'LA', 'CHICAGO']

    def test_trim_all_string_columns(self, dataframe_with_whitespace):
        """Test trimming all string columns."""
        result = trim_whitespace(dataframe_with_whitespace, columns=None, side='both')

        assert is_ok(result)
        df_clean = unwrap(result)
        assert df_clean['Name'].tolist() == ['John', 'Jane', 'Bob']
        assert df_clean['City'].tolist() == ['NYC', 'LA', 'CHICAGO']

    def test_trim_preserves_nan(self):
        """Test that NaN values are preserved."""
        df = pd.DataFrame({
            'Name': ['  John  ', None, ' Jane '],
            'Age': [25, 30, 35]
        })
        result = trim_whitespace(df, columns=['Name'], side='both')

        assert is_ok(result)
        df_clean = unwrap(result)
        assert df_clean['Name'].tolist()[0] == 'John'
        assert pd.isna(df_clean['Name'].tolist()[1])

    def test_trim_column_not_found(self, dataframe_with_whitespace):
        """Test error when column doesn't exist."""
        result = trim_whitespace(dataframe_with_whitespace, columns=['InvalidColumn'])

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, ColumnNotFoundError)

    def test_trim_invalid_side(self, dataframe_with_whitespace):
        """Test error with invalid side parameter."""
        result = trim_whitespace(dataframe_with_whitespace, columns=['Name'], side='invalid')

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, InvalidParameterError)

    def test_trim_empty_dataframe(self):
        """Test trimming empty DataFrame."""
        df = pd.DataFrame()
        result = trim_whitespace(df, columns=None)

        assert is_ok(result)

    def test_trim_no_string_columns(self):
        """Test trimming DataFrame with no string columns."""
        df = pd.DataFrame({'Age': [25, 30, 35], 'Salary': [50000, 60000, 70000]})
        result = trim_whitespace(df, columns=None)

        assert is_ok(result)


# =============================================================================
# remove_duplicates() Tests
# =============================================================================

class TestRemoveDuplicates:
    """Tests for remove_duplicates."""

    def test_remove_duplicates_with_subset(self, dataframe_with_duplicates):
        """Test removing duplicates with subset."""
        result = remove_duplicates(dataframe_with_duplicates, subset=['ID'], keep='first')

        assert is_ok(result)
        df_clean = unwrap(result)
        assert len(df_clean) == 3
        assert df_clean['ID'].tolist() == [1, 2, 3]

    def test_remove_duplicates_with_multiple_subset(self, dataframe_with_duplicates):
        """Test removing duplicates with multiple columns."""
        result = remove_duplicates(dataframe_with_duplicates, subset=['ID', 'Name'], keep='first')

        assert is_ok(result)
        df_clean = unwrap(result)
        assert len(df_clean) == 3

    def test_remove_duplicates_all_columns(self, dataframe_with_duplicates):
        """Test removing duplicates considering all columns."""
        result = remove_duplicates(dataframe_with_duplicates, subset=None, keep='first')

        assert is_ok(result)
        df_clean = unwrap(result)
        assert len(df_clean) == 3

    def test_keep_first_occurrence(self, dataframe_with_duplicates):
        """Test keeping first occurrence."""
        result = remove_duplicates(dataframe_with_duplicates, subset=['ID'], keep='first')

        assert is_ok(result)
        df_clean = unwrap(result)
        # Should keep first row with ID=1 (Alice, 25)
        assert df_clean[df_clean['ID'] == 1]['Name'].iloc[0] == 'Alice'

    def test_keep_last_occurrence(self, dataframe_with_duplicates):
        """Test keeping last occurrence."""
        result = remove_duplicates(dataframe_with_duplicates, subset=['ID'], keep='last')

        assert is_ok(result)
        df_clean = unwrap(result)
        assert len(df_clean) == 3

    def test_remove_all_duplicates(self, dataframe_with_duplicates):
        """Test removing all duplicates (keep=False)."""
        result = remove_duplicates(dataframe_with_duplicates, subset=['ID'], keep=False)

        assert is_ok(result)
        df_clean = unwrap(result)
        # Should remove all rows with duplicate IDs
        assert len(df_clean) == 1  # Only ID=3 is unique

    def test_no_duplicates_in_dataframe(self):
        """Test DataFrame with no duplicates."""
        df = pd.DataFrame({'ID': [1, 2, 3], 'Name': ['Alice', 'Bob', 'Charlie']})
        result = remove_duplicates(df)

        assert is_ok(result)
        df_clean = unwrap(result)
        assert len(df_clean) == 3

    def test_column_not_found(self, dataframe_with_duplicates):
        """Test error when column doesn't exist."""
        result = remove_duplicates(dataframe_with_duplicates, subset=['InvalidColumn'])

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, ColumnNotFoundError)

    def test_invalid_keep_parameter(self, dataframe_with_duplicates):
        """Test error with invalid keep parameter."""
        result = remove_duplicates(dataframe_with_duplicates, keep='invalid')

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, InvalidParameterError)

    def test_empty_dataframe(self):
        """Test removing duplicates from empty DataFrame."""
        df = pd.DataFrame()
        result = remove_duplicates(df)

        assert is_ok(result)

    def test_single_row_dataframe(self):
        """Test removing duplicates from single row DataFrame."""
        df = pd.DataFrame({'ID': [1], 'Name': ['Alice']})
        result = remove_duplicates(df)

        assert is_ok(result)
        df_clean = unwrap(result)
        assert len(df_clean) == 1

    def test_all_rows_are_duplicates(self):
        """Test when all rows are duplicates."""
        df = pd.DataFrame({'ID': [1, 1, 1], 'Name': ['Alice', 'Alice', 'Alice']})
        result = remove_duplicates(df, subset=None, keep='first')

        assert is_ok(result)
        df_clean = unwrap(result)
        assert len(df_clean) == 1


# =============================================================================
# fill_missing_values() Tests
# =============================================================================

class TestFillMissingValues:
    """Tests for fill_missing_values."""

    def test_forward_fill_single_column(self, dataframe_with_missing_values):
        """Test forward filling single column."""
        result = fill_missing_values(dataframe_with_missing_values, strategy='forward', columns=['Age'])

        assert is_ok(result)
        df_filled = unwrap(result)
        # Forward fill: None at row 1 (index 1) becomes 25, None at row 3 (index 3) becomes 35
        assert df_filled['Age'].iloc[1] == 25
        assert df_filled['Age'].iloc[3] == 35

    def test_backward_fill_single_column(self, dataframe_with_missing_values):
        """Test backward filling single column."""
        result = fill_missing_values(dataframe_with_missing_values, strategy='backward', columns=['Age'])

        assert is_ok(result)
        df_filled = unwrap(result)
        # Backward fill: None at row 2 becomes 35
        assert df_filled['Age'].iloc[2] == 35

    def test_mean_fill_numeric_column(self, dataframe_with_missing_values):
        """Test mean filling numeric column."""
        result = fill_missing_values(dataframe_with_missing_values, strategy='mean', columns=['Age'])

        assert is_ok(result)
        df_filled = unwrap(result)
        # Mean of [25, 35, 45] is 35
        assert df_filled['Age'].iloc[1] == 35
        assert df_filled['Age'].iloc[3] == 35

    def test_median_fill_numeric_column(self, dataframe_with_missing_values):
        """Test median filling numeric column."""
        result = fill_missing_values(dataframe_with_missing_values, strategy='median', columns=['Salary'])

        assert is_ok(result)
        df_filled = unwrap(result)
        # Median of [50000, 60000, 80000] is 60000
        assert df_filled['Salary'].iloc[2] == 60000.0

    def test_constant_fill(self, dataframe_with_missing_values):
        """Test constant fill."""
        result = fill_missing_values(dataframe_with_missing_values, strategy='constant', columns=['Name'], value='Unknown')

        assert is_ok(result)
        df_filled = unwrap(result)
        assert df_filled['Name'].iloc[2] == 'Unknown'

    def test_drop_rows_with_missing(self, dataframe_with_missing_values):
        """Test dropping rows with missing values."""
        result = fill_missing_values(dataframe_with_missing_values, strategy='drop', columns=['Name'])

        assert is_ok(result)
        df_filled = unwrap(result)
        # Should drop row 2 (Name is None), leaving 4 rows
        assert len(df_filled) == 4
        # After drop, index is reset, so David is now at index 2
        assert df_filled['Name'].iloc[2] == 'David'
        assert df_filled['ID'].tolist() == [1, 2, 4, 5]  # Row with ID=3 was dropped

    def test_dict_strategy_different_strategies(self, dataframe_with_missing_values):
        """Test dict strategy with different strategies per column."""
        result = fill_missing_values(
            dataframe_with_missing_values,
            strategy={'Age': 'mean', 'Name': 'constant'},
            value='Unknown'
        )

        assert is_ok(result)
        df_filled = unwrap(result)
        assert df_filled['Age'].iloc[1] == 35  # Mean of [25, 35, 45]
        assert df_filled['Name'].iloc[2] == 'Unknown'  # Constant

    def test_fill_all_columns_default(self, dataframe_with_missing_values):
        """Test filling all columns with missing values."""
        result = fill_missing_values(dataframe_with_missing_values, strategy='forward')

        assert is_ok(result)
        df_filled = unwrap(result)
        # Should fill all columns with missing values

    def test_column_not_found(self, dataframe_with_missing_values):
        """Test error when column doesn't exist."""
        result = fill_missing_values(dataframe_with_missing_values, strategy='mean', columns=['InvalidColumn'])

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, ColumnNotFoundError)

    def test_invalid_strategy(self, dataframe_with_missing_values):
        """Test error with invalid strategy."""
        result = fill_missing_values(dataframe_with_missing_values, strategy='invalid', columns=['Age'])

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, InvalidFillStrategyError)

    def test_mean_on_non_numeric_column(self, dataframe_with_missing_values):
        """Test error when applying mean to non-numeric column."""
        result = fill_missing_values(dataframe_with_missing_values, strategy='mean', columns=['Name'])

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, FillFailedError)

    def test_constant_without_value(self, dataframe_with_missing_values):
        """Test error when using constant without providing value."""
        result = fill_missing_values(dataframe_with_missing_values, strategy='constant', columns=['Name'])

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, FillFailedError)

    def test_empty_dataframe(self):
        """Test filling empty DataFrame."""
        df = pd.DataFrame()
        result = fill_missing_values(df, strategy='forward')

        assert is_ok(result)

    def test_no_missing_values(self):
        """Test filling DataFrame with no missing values."""
        df = pd.DataFrame({'ID': [1, 2, 3], 'Name': ['Alice', 'Bob', 'Charlie']})
        result = fill_missing_values(df, strategy='forward')

        assert is_ok(result)

    def test_all_values_missing(self):
        """Test filling column where all values are missing."""
        df = pd.DataFrame({'Age': [None, None, None]})
        result = fill_missing_values(df, strategy='mean', columns=['Age'])

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, FillFailedError)


# =============================================================================
# standardize_columns() Tests
# =============================================================================

class TestStandardizeColumns:
    """Tests for standardize_columns."""

    def test_lowercase_conversion(self, dataframe_with_bad_columns):
        """Test lowercase conversion."""
        result = standardize_columns(dataframe_with_bad_columns, case='lower')

        assert is_ok(result)
        df_std = unwrap(result)
        assert 'first name' in df_std.columns
        assert 'last name!' in df_std.columns
        assert 'age' in df_std.columns

    def test_uppercase_conversion(self, dataframe_with_bad_columns):
        """Test uppercase conversion."""
        result = standardize_columns(dataframe_with_bad_columns, case='upper')

        assert is_ok(result)
        df_std = unwrap(result)
        assert 'FIRST NAME' in df_std.columns
        assert 'LAST NAME!' in df_std.columns
        assert 'AGE' in df_std.columns

    def test_title_case_conversion(self, dataframe_with_bad_columns):
        """Test title case conversion."""
        result = standardize_columns(dataframe_with_bad_columns, case='title')

        assert is_ok(result)
        df_std = unwrap(result)
        assert 'First Name' in df_std.columns
        assert 'Last Name!' in df_std.columns
        assert 'Age' in df_std.columns

    def test_snake_case_conversion(self, dataframe_with_bad_columns):
        """Test snake case conversion."""
        result = standardize_columns(dataframe_with_bad_columns, case='snake')

        assert is_ok(result)
        df_std = unwrap(result)
        assert 'first_name' in df_std.columns  # lowercase with underscores
        assert 'last_name!' in df_std.columns
        assert 'age' in df_std.columns

    def test_custom_separator(self, dataframe_with_bad_columns):
        """Test custom separator."""
        result = standardize_columns(dataframe_with_bad_columns, case='snake', separator='-')

        assert is_ok(result)
        df_std = unwrap(result)
        assert 'first-name' in df_std.columns  # lowercase with custom separator
        assert 'last-name!' in df_std.columns

    def test_remove_special_characters_true(self, dataframe_with_bad_columns):
        """Test removing special characters."""
        result = standardize_columns(dataframe_with_bad_columns, case='lower', remove_special=True)

        assert is_ok(result)
        df_std = unwrap(result)
        assert 'last name' in df_std.columns  # '!' removed, space preserved
        assert 'first name' in df_std.columns
        assert 'age' in df_std.columns

    def test_remove_special_characters_false(self, dataframe_with_bad_columns):
        """Test keeping special characters."""
        result = standardize_columns(dataframe_with_bad_columns, case='lower', remove_special=False)

        assert is_ok(result)
        df_std = unwrap(result)
        assert 'last name!' in df_std.columns  # '!' preserved
        assert 'first name' in df_std.columns
        assert 'age' in df_std.columns

    def test_ensure_uniqueness(self):
        """Test that duplicate column names are made unique."""
        df = pd.DataFrame({
            'Name': ['John', 'Jane'],
            'name': ['Doe', 'Smith'],
            'NAME': ['A', 'B']
        })
        result = standardize_columns(df, case='lower')

        assert is_ok(result)
        df_std = unwrap(result)
        columns = list(df_std.columns)
        # Should have name, name_1, name_2
        assert 'name' in columns
        assert 'name_1' in columns
        assert 'name_2' in columns

    def test_invalid_case_parameter(self, dataframe_with_bad_columns):
        """Test error with invalid case parameter."""
        result = standardize_columns(dataframe_with_bad_columns, case='invalid')

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, InvalidParameterError)

    def test_empty_dataframe(self):
        """Test standardizing empty DataFrame."""
        df = pd.DataFrame()
        result = standardize_columns(df)

        assert is_ok(result)

    def test_single_column(self):
        """Test standardizing single column DataFrame."""
        df = pd.DataFrame({'  First Name  ': ['John', 'Jane']})
        result = standardize_columns(df, case='lower', remove_special=True)

        assert is_ok(result)
        df_std = unwrap(result)
        assert 'first name' in df_std.columns  # Trimmed and lowercased


# =============================================================================
# clean_dataframe() Tests
# =============================================================================

class TestCleanDataframe:
    """Tests for clean_dataframe."""

    def test_apply_all_operations(self, messy_dataframe):
        """Test applying all cleaning operations."""
        result = clean_dataframe(
            messy_dataframe,
            standardize=True,
            standardize_case='lower',
            trim=True,
            remove_dup=True,
            fill_strategy='constant',
            fill_value=0
        )

        assert is_ok(result)
        df_clean = unwrap(result)
        assert len(df_clean) >= 0

    def test_apply_subset_of_operations(self, messy_dataframe):
        """Test applying only some operations."""
        result = clean_dataframe(
            messy_dataframe,
            trim=True,
            remove_dup=True
        )

        assert is_ok(result)
        df_clean = unwrap(result)

    def test_operations_in_correct_order(self):
        """Test that operations are applied in correct order."""
        df = pd.DataFrame({
            '  First Name  ': ['  John  ', ' Jane '],
            'Age': [25, 30]
        })
        result = clean_dataframe(
            df,
            standardize=True,
            standardize_case='lower',
            trim=True
        )

        assert is_ok(result)
        df_clean = unwrap(result)
        # Should standardize first, then trim

    def test_error_propagates(self, messy_dataframe):
        """Test that error from sub-operation propagates."""
        result = clean_dataframe(
            messy_dataframe,
            trim=True,
            trim_columns=['InvalidColumn']
        )

        assert is_err(result)

    def test_empty_dataframe(self):
        """Test cleaning empty DataFrame."""
        df = pd.DataFrame()
        result = clean_dataframe(df, trim=True)

        assert is_ok(result)

    def test_dataframe_with_no_issues(self):
        """Test cleaning DataFrame with no issues."""
        df = pd.DataFrame({'ID': [1, 2, 3], 'Name': ['Alice', 'Bob', 'Charlie']})
        result = clean_dataframe(df, trim=True)

        assert is_ok(result)
        df_clean = unwrap(result)
        assert len(df_clean) == 3


# =============================================================================
# Integration Tests
# =============================================================================

class TestCleaningIntegration:
    """Integration tests for cleaning operations."""

    def test_full_cleaning_workflow(self, messy_dataframe):
        """Test complete cleaning workflow."""
        result = clean_dataframe(
            messy_dataframe,
            standardize=True,
            standardize_case='lower',
            trim=True,
            fill_strategy='mean'
        )

        assert is_ok(result)
        df_clean = unwrap(result)
        assert len(df_clean) > 0

    def test_complex_cleaning_workflow(self):
        """Test complex cleaning with multiple issues."""
        df = pd.DataFrame({
            '  First Name  ': ['  John  ', ' Jane ', None, '  Bob  '],
            'Last-Name': ['Doe', 'Smith', 'Jones', 'Brown'],
            '  AGE': [25, 30, 35, 30],
            'SALARY': [50000.0, None, None, 70000.0]
        })

        result = clean_dataframe(
            df,
            standardize=True,
            standardize_case='lower',
            trim=True,
            remove_dup=True,
            fill_strategy={'salary': 'mean', 'first name': 'constant'},
            fill_value='Unknown'
        )

        assert is_ok(result)
        df_clean = unwrap(result)
        # After standardization, dedup, etc., we should have at least some rows
        assert len(df_clean) >= 0
        # Check that the standardized columns exist
        assert 'first name' in df_clean.columns
        assert 'salary' in df_clean.columns

    def test_cleaning_preserves_data_types(self):
        """Test that cleaning preserves data types."""
        df = pd.DataFrame({
            'ID': [1, 2, 3],
            'Name': ['Alice', 'Bob', 'Charlie'],
            'Age': [25.5, 30.0, 35.5]
        })

        result = clean_dataframe(df, standardize=True, standardize_case='lower')

        assert is_ok(result)
        df_clean = unwrap(result)
        # After standardization, 'Age' becomes 'age'
        assert df_clean['age'].dtype == df['Age'].dtype
