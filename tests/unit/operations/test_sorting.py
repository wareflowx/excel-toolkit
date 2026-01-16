"""Comprehensive tests for sorting operations.

Tests for:
- validate_sort_columns()
- sort_dataframe()
"""

import pytest
import pandas as pd
import numpy as np
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err
from excel_toolkit.operations.sorting import (
    validate_sort_columns,
    sort_dataframe,
)
from excel_toolkit.models.error_types import (
    NoColumnsError,
    ColumnNotFoundError,
    NotComparableError,
    SortFailedError,
)


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'age': [25, 30, 35, 28, 32],
        'city': ['Paris', 'London', 'Paris', 'Berlin', 'London'],
        'salary': [50000, 60000, 70000, 55000, 65000],
    })


@pytest.fixture
def dataframe_with_nan():
    """Create a DataFrame with NaN values."""
    return pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie', 'David'],
        'age': [25, 30, None, 28],
        'salary': [50000, None, 70000, 55000],
    })


@pytest.fixture
def dataframe_with_mixed_types():
    """Create a DataFrame with mixed types in a column."""
    return pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'value': [100, 200, 'text'],  # Mixed types
        'age': [25, 30, 35],
    })


# =============================================================================
# validate_sort_columns() Tests
# =============================================================================

class TestValidateSortColumns:
    """Tests for validate_sort_columns function."""

    def test_valid_single_column(self, sample_dataframe):
        """Test validation with single valid column."""
        result = validate_sort_columns(sample_dataframe, ['age'])
        assert is_ok(result)

    def test_valid_multiple_columns(self, sample_dataframe):
        """Test validation with multiple valid columns."""
        result = validate_sort_columns(sample_dataframe, ['city', 'age'])
        assert is_ok(result)

    def test_empty_column_list(self, sample_dataframe):
        """Test validation with empty column list."""
        result = validate_sort_columns(sample_dataframe, [])

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, NoColumnsError)

    def test_invalid_single_column(self, sample_dataframe):
        """Test validation with single invalid column."""
        result = validate_sort_columns(sample_dataframe, ['invalid'])

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, ColumnNotFoundError)
        assert error.column == 'invalid'
        assert 'age' in error.available

    def test_invalid_multiple_columns(self, sample_dataframe):
        """Test validation with multiple columns, one invalid."""
        result = validate_sort_columns(sample_dataframe, ['age', 'invalid'])

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, ColumnNotFoundError)


# =============================================================================
# sort_dataframe() Tests
# =============================================================================

class TestSortDataFrame:
    """Tests for sort_dataframe function."""

    def test_sort_single_column_ascending(self, sample_dataframe):
        """Test sorting by single column in ascending order."""
        result = sort_dataframe(sample_dataframe, ['age'])

        assert is_ok(result)
        df_sorted = unwrap(result)
        assert list(df_sorted['age']) == [25, 28, 30, 32, 35]
        assert list(df_sorted['name']) == ['Alice', 'David', 'Bob', 'Eve', 'Charlie']

    def test_sort_single_column_descending(self, sample_dataframe):
        """Test sorting by single column in descending order."""
        result = sort_dataframe(sample_dataframe, ['age'], ascending=False)

        assert is_ok(result)
        df_sorted = unwrap(result)
        assert list(df_sorted['age']) == [35, 32, 30, 28, 25]

    def test_sort_multiple_columns(self, sample_dataframe):
        """Test sorting by multiple columns."""
        result = sort_dataframe(sample_dataframe, ['city', 'age'])

        assert is_ok(result)
        df_sorted = unwrap(result)
        # Berlin: David (28), London: Bob (30), Eve (32), Paris: Alice (25), Charlie (35)
        assert df_sorted.iloc[0]['name'] == 'David'
        assert df_sorted.iloc[1]['name'] == 'Bob'
        assert df_sorted.iloc[2]['name'] == 'Eve'
        assert df_sorted.iloc[3]['name'] == 'Alice'
        assert df_sorted.iloc[4]['name'] == 'Charlie'

    def test_sort_with_nan_first(self, dataframe_with_nan):
        """Test sorting with NaN values placed first."""
        result = sort_dataframe(dataframe_with_nan, ['age'], na_position='first')

        assert is_ok(result)
        df_sorted = unwrap(result)
        assert pd.isna(df_sorted.iloc[0]['age'])
        assert df_sorted.iloc[1]['age'] == 25

    def test_sort_with_nan_last(self, dataframe_with_nan):
        """Test sorting with NaN values placed last."""
        result = sort_dataframe(dataframe_with_nan, ['age'], na_position='last')

        assert is_ok(result)
        df_sorted = unwrap(result)
        assert pd.isna(df_sorted.iloc[-1]['age'])
        assert df_sorted.iloc[0]['age'] == 25

    def test_sort_with_limit(self, sample_dataframe):
        """Test sorting with row limit."""
        result = sort_dataframe(sample_dataframe, ['age'], limit=3)

        assert is_ok(result)
        df_sorted = unwrap(result)
        assert len(df_sorted) == 3
        assert list(df_sorted['age']) == [25, 28, 30]

    def test_sort_with_limit_descending(self, sample_dataframe):
        """Test sorting descending with row limit."""
        result = sort_dataframe(sample_dataframe, ['salary'], ascending=False, limit=2)

        assert is_ok(result)
        df_sorted = unwrap(result)
        assert len(df_sorted) == 2
        assert df_sorted.iloc[0]['salary'] == 70000
        assert df_sorted.iloc[1]['salary'] == 65000

    def test_sort_invalid_na_position(self, sample_dataframe):
        """Test sorting with invalid na_position."""
        result = sort_dataframe(sample_dataframe, ['age'], na_position='invalid')

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, SortFailedError)
        assert "Invalid na_position" in error.message

    def test_sort_with_invalid_column(self, sample_dataframe):
        """Test sorting with non-existent column."""
        result = sort_dataframe(sample_dataframe, ['nonexistent'])

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, SortFailedError)
        assert "not found" in error.message

    def test_sort_with_empty_columns(self, sample_dataframe):
        """Test sorting with empty column list."""
        result = sort_dataframe(sample_dataframe, [])

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, SortFailedError)
        assert "No columns" in error.message

    def test_sort_mixed_types_error(self, dataframe_with_mixed_types):
        """Test sorting column with mixed data types."""
        result = sort_dataframe(dataframe_with_mixed_types, ['value'])

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, NotComparableError)
        assert error.column == 'value'

    def test_sort_string_column(self, sample_dataframe):
        """Test sorting by string column."""
        result = sort_dataframe(sample_dataframe, ['name'])

        assert is_ok(result)
        df_sorted = unwrap(result)
        assert list(df_sorted['name']) == ['Alice', 'Bob', 'Charlie', 'David', 'Eve']

    def test_sort_preserves_all_columns(self, sample_dataframe):
        """Test that sorting preserves all columns."""
        result = sort_dataframe(sample_dataframe, ['age'])

        assert is_ok(result)
        df_sorted = unwrap(result)
        assert list(df_sorted.columns) == list(sample_dataframe.columns)

    def test_sort_single_row_dataframe(self):
        """Test sorting a DataFrame with only one row."""
        df = pd.DataFrame({'name': ['Alice'], 'age': [25]})
        result = sort_dataframe(df, ['age'])

        assert is_ok(result)
        df_sorted = unwrap(result)
        assert len(df_sorted) == 1

    def test_sort_all_same_values(self):
        """Test sorting when all values are the same."""
        df = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [30, 30, 30]
        })
        result = sort_dataframe(df, ['age'])

        assert is_ok(result)
        df_sorted = unwrap(result)
        assert all(df_sorted['age'] == 30)


# =============================================================================
# Integration Tests
# =============================================================================

class TestSortingIntegration:
    """Integration tests for sorting operations."""

    def test_validate_and_sort_workflow(self, sample_dataframe):
        """Test complete workflow: validate then sort."""
        columns = ['city', 'salary']

        # Step 1: Validate
        validation_result = validate_sort_columns(sample_dataframe, columns)
        assert is_ok(validation_result)

        # Step 2: Sort
        sort_result = sort_dataframe(sample_dataframe, columns)
        assert is_ok(sort_result)

        df_sorted = unwrap(sort_result)
        assert len(df_sorted) == len(sample_dataframe)

    def test_complex_sort_workflow(self, sample_dataframe):
        """Test complex sorting with multiple options."""
        result = sort_dataframe(
            sample_dataframe,
            columns=['city', 'age'],
            ascending=True,
            na_position='last',
            limit=3
        )

        assert is_ok(result)
        df_sorted = unwrap(result)
        assert len(df_sorted) == 3

    def test_sort_with_nan_limit_and_columns(self, dataframe_with_nan):
        """Test sorting with NaN, limit, and column selection."""
        result = sort_dataframe(
            dataframe_with_nan,
            columns=['age'],
            ascending=True,
            na_position='first',
            limit=2
        )

        assert is_ok(result)
        df_sorted = unwrap(result)
        assert len(df_sorted) == 2
        # First row should be NaN (placed first due to na_position='first')
        assert pd.isna(df_sorted.iloc[0]['age'])
