"""Comprehensive tests for aggregating operations.

Tests for:
- parse_aggregation_specs()
- validate_aggregation_columns()
- aggregate_groups()
"""

import pytest
import pandas as pd
import numpy as np
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err
from excel_toolkit.operations.aggregating import (
    parse_aggregation_specs,
    validate_aggregation_columns,
    aggregate_groups,
)
from excel_toolkit.models.error_types import (
    InvalidFormatError,
    NoValidSpecsError,
    GroupColumnsNotFoundError,
    AggColumnsNotFoundError,
    OverlappingColumnsError,
    AggregationFailedError,
)


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sales_dataframe():
    """Create a sales DataFrame for testing."""
    return pd.DataFrame({
        'Region': ['North', 'North', 'South', 'South', 'East', 'East', 'West', 'West'],
        'Category': ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B'],
        'Sales': [100, 150, 200, 250, 120, 180, 90, 110],
        'Quantity': [10, 15, 20, 25, 12, 18, 9, 11],
        'Profit': [20, 30, 40, 50, 24, 36, 18, 22],
    })


@pytest.fixture
def simple_dataframe():
    """Create a simple DataFrame for testing."""
    return pd.DataFrame({
        'Group': ['A', 'A', 'B', 'B', 'C', 'C'],
        'Value1': [10, 20, 30, 40, 50, 60],
        'Value2': [1, 2, 3, 4, 5, 6],
    })


# =============================================================================
# parse_aggregation_specs() Tests
# =============================================================================

class TestParseAggregationSpecs:
    """Tests for parse_aggregation_specs."""

    def test_simple_spec(self):
        """Test parsing simple spec: column:func"""
        result = parse_aggregation_specs("Revenue:sum")

        assert is_ok(result)
        specs = unwrap(result)
        assert specs == {"Revenue": ["sum"]}

    def test_multiple_functions_same_column(self):
        """Test parsing multiple functions for same column."""
        result = parse_aggregation_specs("Sales:sum,mean,count")

        assert is_ok(result)
        specs = unwrap(result)
        assert specs == {"Sales": ["sum", "mean", "count"]}

    def test_multiple_columns(self):
        """Test parsing multiple columns."""
        result = parse_aggregation_specs("Amount:sum,Profit:mean")

        assert is_ok(result)
        specs = unwrap(result)
        assert specs == {"Amount": ["sum"], "Profit": ["mean"]}

    def test_multiple_columns_multiple_functions(self):
        """Test parsing multiple columns with multiple functions."""
        result = parse_aggregation_specs("Sales:sum,count,Profit:mean,max,Quantity:sum")

        assert is_ok(result)
        specs = unwrap(result)
        assert specs == {
            "Sales": ["sum", "count"],
            "Profit": ["mean", "max"],
            "Quantity": ["sum"]
        }

    def test_avg_normalizes_to_mean(self):
        """Test that 'avg' is normalized to 'mean'."""
        result = parse_aggregation_specs("Sales:avg")

        assert is_ok(result)
        specs = unwrap(result)
        assert specs == {"Sales": ["mean"]}

    def test_avg_uppercase_normalizes_to_mean(self):
        """Test that 'AVG' (uppercase) is normalized to 'mean'."""
        result = parse_aggregation_specs("Sales:AVG")

        assert is_ok(result)
        specs = unwrap(result)
        assert specs == {"Sales": ["mean"]}

    def test_avg_in_list_normalizes_to_mean(self):
        """Test that 'avg' in list is normalized to 'mean'."""
        result = parse_aggregation_specs("Sales:sum,avg,count")

        assert is_ok(result)
        specs = unwrap(result)
        assert specs == {"Sales": ["sum", "mean", "count"]}

    def test_duplicate_columns_merge(self):
        """Test that duplicate column specs merge functions."""
        result = parse_aggregation_specs("Sales:sum,Sales:mean")

        assert is_ok(result)
        specs = unwrap(result)
        assert specs == {"Sales": ["sum", "mean"]}

    def test_missing_colon_error(self):
        """Test error when colon is missing."""
        result = parse_aggregation_specs("Sales")

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, InvalidFormatError)

    def test_invalid_function_error(self):
        """Test error when function is invalid."""
        result = parse_aggregation_specs("Sales:invalid")

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, InvalidFormatError)
        assert "Invalid functions" in error.spec

    def test_multiple_errors_collected(self):
        """Test that multiple parse errors are collected."""
        result = parse_aggregation_specs("Sales,sum,Profit:invalid")

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, InvalidFormatError)
        assert "Invalid format" in error.spec or "Invalid functions" in error.spec

    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly."""
        result = parse_aggregation_specs(" Sales : sum , Profit : mean ")

        assert is_ok(result)
        specs = unwrap(result)
        assert specs == {"Sales": ["sum"], "Profit": ["mean"]}

    def test_empty_string_error(self):
        """Test error when specs is empty."""
        result = parse_aggregation_specs("")

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, NoValidSpecsError)


# =============================================================================
# validate_aggregation_columns() Tests
# =============================================================================

class TestValidateAggregationColumns:
    """Tests for validate_aggregation_columns."""

    def test_valid_columns(self, sales_dataframe):
        """Test validation with valid columns."""
        result = validate_aggregation_columns(
            sales_dataframe,
            group_columns=['Region'],
            agg_columns=['Sales']
        )
        assert is_ok(result)

    def test_valid_multiple_group_columns(self, sales_dataframe):
        """Test validation with multiple group columns."""
        result = validate_aggregation_columns(
            sales_dataframe,
            group_columns=['Region', 'Category'],
            agg_columns=['Sales']
        )
        assert is_ok(result)

    def test_valid_multiple_agg_columns(self, sales_dataframe):
        """Test validation with multiple aggregation columns."""
        result = validate_aggregation_columns(
            sales_dataframe,
            group_columns=['Region'],
            agg_columns=['Sales', 'Quantity', 'Profit']
        )
        assert is_ok(result)

    def test_missing_group_column(self, sales_dataframe):
        """Test error when group column doesn't exist."""
        result = validate_aggregation_columns(
            sales_dataframe,
            group_columns=['InvalidRegion'],
            agg_columns=['Sales']
        )

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, GroupColumnsNotFoundError)
        assert error.missing == ['InvalidRegion']

    def test_missing_agg_column(self, sales_dataframe):
        """Test error when aggregation column doesn't exist."""
        result = validate_aggregation_columns(
            sales_dataframe,
            group_columns=['Region'],
            agg_columns=['InvalidSales']
        )

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, AggColumnsNotFoundError)
        assert error.missing == ['InvalidSales']

    def test_overlapping_columns(self, sales_dataframe):
        """Test error when group and agg columns overlap."""
        result = validate_aggregation_columns(
            sales_dataframe,
            group_columns=['Region'],
            agg_columns=['Region', 'Sales']
        )

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, OverlappingColumnsError)
        assert error.overlap == ['Region']


# =============================================================================
# aggregate_groups() Tests
# =============================================================================

class TestAggregateGroups:
    """Tests for aggregate_groups."""

    def test_simple_sum_aggregation(self, simple_dataframe):
        """Test simple sum aggregation."""
        aggregations = {"Value1": ["sum"]}
        result = aggregate_groups(simple_dataframe, ["Group"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        assert len(df_agg) == 3  # 3 groups
        assert "Value1_sum" in df_agg.columns

    def test_mean_aggregation(self, simple_dataframe):
        """Test mean aggregation."""
        aggregations = {"Value1": ["mean"]}
        result = aggregate_groups(simple_dataframe, ["Group"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        assert "Value1_mean" in df_agg.columns

    def test_count_aggregation(self, simple_dataframe):
        """Test count aggregation."""
        aggregations = {"Value1": ["count"]}
        result = aggregate_groups(simple_dataframe, ["Group"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        assert "Value1_count" in df_agg.columns

    def test_multiple_functions_same_column(self, simple_dataframe):
        """Test multiple aggregation functions on same column."""
        aggregations = {"Value1": ["sum", "mean", "min", "max"]}
        result = aggregate_groups(simple_dataframe, ["Group"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        assert "Value1_sum" in df_agg.columns
        assert "Value1_mean" in df_agg.columns
        assert "Value1_min" in df_agg.columns
        assert "Value1_max" in df_agg.columns

    def test_multiple_columns(self, simple_dataframe):
        """Test aggregation on multiple columns."""
        aggregations = {"Value1": ["sum"], "Value2": ["sum"]}
        result = aggregate_groups(simple_dataframe, ["Group"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        assert "Value1_sum" in df_agg.columns
        assert "Value2_sum" in df_agg.columns

    def test_multiple_groups(self, sales_dataframe):
        """Test grouping by multiple columns."""
        aggregations = {"Sales": ["sum"]}
        result = aggregate_groups(sales_dataframe, ["Region", "Category"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        assert len(df_agg) > 0

    def test_median_aggregation(self, simple_dataframe):
        """Test median aggregation."""
        aggregations = {"Value1": ["median"]}
        result = aggregate_groups(simple_dataframe, ["Group"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        assert "Value1_median" in df_agg.columns

    def test_std_aggregation(self, simple_dataframe):
        """Test std aggregation."""
        aggregations = {"Value1": ["std"]}
        result = aggregate_groups(simple_dataframe, ["Group"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        assert "Value1_std" in df_agg.columns

    def test_var_aggregation(self, simple_dataframe):
        """Test var aggregation."""
        aggregations = {"Value1": ["var"]}
        result = aggregate_groups(simple_dataframe, ["Group"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        assert "Value1_var" in df_agg.columns

    def test_first_aggregation(self, simple_dataframe):
        """Test first aggregation."""
        aggregations = {"Value1": ["first"]}
        result = aggregate_groups(simple_dataframe, ["Group"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        assert "Value1_first" in df_agg.columns

    def test_last_aggregation(self, simple_dataframe):
        """Test last aggregation."""
        aggregations = {"Value1": ["last"]}
        result = aggregate_groups(simple_dataframe, ["Group"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        assert "Value1_last" in df_agg.columns

    def test_preserves_group_columns(self, simple_dataframe):
        """Test that group columns are preserved."""
        aggregations = {"Value1": ["sum"]}
        result = aggregate_groups(simple_dataframe, ["Group"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        assert "Group" in df_agg.columns

    def test_single_group(self):
        """Test aggregation with single group."""
        df = pd.DataFrame({
            'Group': ['A', 'A', 'A', 'B', 'B'],
            'Value': [10, 20, 30, 40, 50]
        })
        aggregations = {"Value": ["sum"]}
        result = aggregate_groups(df, ["Group"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        assert len(df_agg) == 2
        assert df_agg[df_agg['Group'] == 'A']['Value_sum'].iloc[0] == 60
        assert df_agg[df_agg['Group'] == 'B']['Value_sum'].iloc[0] == 90

    def test_aggregation_with_nan_values(self):
        """Test aggregation with NaN in group column."""
        df = pd.DataFrame({
            'Group': ['A', 'A', None, 'B', 'B'],
            'Value': [10, 20, 30, 40, 50]
        })
        aggregations = {"Value": ["sum"]}
        result = aggregate_groups(df, ["Group"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        # dropna=False means NaN is treated as its own group
        assert len(df_agg) >= 2  # At least A and B groups

    def test_complex_aggregation(self, sales_dataframe):
        """Test complex aggregation with multiple groups and functions."""
        aggregations = {
            "Sales": ["sum", "mean", "count"],
            "Quantity": ["sum"],
            "Profit": ["mean", "max"]
        }
        result = aggregate_groups(sales_dataframe, ["Region", "Category"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        assert "Sales_sum" in df_agg.columns
        assert "Sales_mean" in df_agg.columns
        assert "Sales_count" in df_agg.columns
        assert "Quantity_sum" in df_agg.columns
        assert "Profit_mean" in df_agg.columns
        assert "Profit_max" in df_agg.columns


# =============================================================================
# Integration Tests
# =============================================================================

class TestAggregatingIntegration:
    """Integration tests for aggregating operations."""

    def test_full_aggregation_workflow(self, simple_dataframe):
        """Test complete workflow: parse, validate, aggregate."""
        specs = "Value1:sum,mean"

        # Parse specs
        parse_result = parse_aggregation_specs(specs)
        assert is_ok(parse_result)
        aggregations = unwrap(parse_result)

        # Validate columns
        validation_result = validate_aggregation_columns(
            simple_dataframe,
            group_columns=["Group"],
            agg_columns=list(aggregations.keys())
        )
        assert is_ok(validation_result)

        # Aggregate
        agg_result = aggregate_groups(simple_dataframe, ["Group"], aggregations)
        assert is_ok(agg_result)

        df_agg = unwrap(agg_result)
        assert len(df_agg) == 3

    def test_complex_workflow(self, sales_dataframe):
        """Test complex aggregation with multiple options."""
        aggregations = {
            "Sales": ["sum", "mean"],
            "Quantity": ["count"]
        }

        result = aggregate_groups(sales_dataframe, ["Region"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        assert len(df_agg) == 4  # 4 regions

    def test_parse_and_aggregate_directly(self, simple_dataframe):
        """Test parsing and aggregating in one step."""
        specs = "Value1:sum,Value2:mean"

        # Parse
        parse_result = parse_aggregation_specs(specs)
        assert is_ok(parse_result)
        aggregations = unwrap(parse_result)

        # Aggregate
        result = aggregate_groups(simple_dataframe, ["Group"], aggregations)

        assert is_ok(result)
        df_agg = unwrap(result)
        assert "Value1_sum" in df_agg.columns
        assert "Value2_mean" in df_agg.columns

    def test_aggregate_all_functions(self, simple_dataframe):
        """Test aggregation with all supported functions."""
        # Test each function individually
        functions = ["sum", "mean", "median", "min", "max", "count", "std", "var", "first", "last"]

        for func in functions:
            aggregations = {"Value1": [func]}
            result = aggregate_groups(simple_dataframe, ["Group"], aggregations)
            assert is_ok(result), f"Failed for function: {func}"
