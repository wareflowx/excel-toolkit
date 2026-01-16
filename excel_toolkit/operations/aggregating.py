"""Aggregating operations for DataFrames.

This module provides aggregation operations that can be applied to pandas DataFrames.
All functions return Result types for explicit error handling.
"""

from typing import Any

import pandas as pd

from excel_toolkit.fp import ok, err, is_ok, is_err, unwrap, unwrap_err, Result
from excel_toolkit.models.error_types import (
    InvalidFormatError,
    InvalidFunctionError,
    NoValidSpecsError,
    GroupColumnsNotFoundError,
    AggColumnsNotFoundError,
    OverlappingColumnsError,
    AggregationFailedError,
    ParseError,
    AggregationValidationError,
    AggregationError,
)


# =============================================================================
# Constants
# =============================================================================

VALID_AGGREGATION_FUNCTIONS = [
    "sum",
    "mean",
    "avg",
    "median",
    "min",
    "max",
    "count",
    "std",
    "var",
    "first",
    "last",
]


# =============================================================================
# Parsing Functions
# =============================================================================


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
    if not specs:
        return err(NoValidSpecsError())

    agg_specs = {}
    parse_errors = []
    current_column = None
    current_funcs = []

    # Split by comma and process tokens
    for token in specs.split(","):
        token = token.strip()
        if not token:
            continue

        if ":" in token:
            # Save previous column if exists
            if current_column and current_funcs:
                if current_column in agg_specs:
                    agg_specs[current_column].extend(current_funcs)
                else:
                    agg_specs[current_column] = current_funcs

            # Start new column
            col_name, funcs = token.split(":", 1)
            col_name = col_name.strip()
            funcs = funcs.strip()

            if not funcs:
                parse_errors.append(f"No functions specified for column: '{col_name}'")
                current_column = None
                current_funcs = []
                continue

            # Parse functions for this column
            func_list = [f.strip().lower() for f in funcs.split(",")]
            func_list = [f for f in func_list if f]  # Remove empty strings

            # Normalize "avg" to "mean"
            func_list = ["mean" if f == "avg" else f for f in func_list]

            # Validate functions
            invalid_funcs = [f for f in func_list if f not in VALID_AGGREGATION_FUNCTIONS]
            if invalid_funcs:
                parse_errors.append(f"Invalid functions for column '{col_name}': {', '.join(invalid_funcs)}")
                current_column = None
                current_funcs = []
                continue

            current_column = col_name
            current_funcs = func_list
        else:
            # Token without colon - could be a function for current column
            token_lower = token.lower()

            # Normalize "avg" to "mean"
            if token_lower == "avg":
                token_lower = "mean"

            if current_column and token_lower in VALID_AGGREGATION_FUNCTIONS:
                # It's a function for the current column
                current_funcs.append(token_lower)
            else:
                # Not a valid function - error
                if current_column:
                    parse_errors.append(f"Invalid function '{token}' for column '{current_column}'")
                else:
                    parse_errors.append(f"Invalid format: '{token}' (expected column:func1,func2)")

    # Save last column
    if current_column and current_funcs:
        if current_column in agg_specs:
            agg_specs[current_column].extend(current_funcs)
        else:
            agg_specs[current_column] = current_funcs

    if parse_errors:
        return err(InvalidFormatError(
            spec="; ".join(parse_errors),
            expected_format="column:func1,func2"
        ))

    if not agg_specs:
        return err(NoValidSpecsError())

    return ok(agg_specs)


# =============================================================================
# Validation Functions
# =============================================================================


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
    # Check group columns exist
    missing_group = [c for c in group_columns if c not in df.columns]
    if missing_group:
        return err(GroupColumnsNotFoundError(
            missing=missing_group,
            available=list(df.columns)
        ))

    # Check agg columns exist
    missing_agg = [c for c in agg_columns if c not in df.columns]
    if missing_agg:
        return err(AggColumnsNotFoundError(
            missing=missing_agg,
            available=list(df.columns)
        ))

    # Check for overlap
    overlap_cols = set(group_columns) & set(agg_columns)
    if overlap_cols:
        return err(OverlappingColumnsError(
            overlap=list(overlap_cols)
        ))

    return ok(None)


# =============================================================================
# Main Operations
# =============================================================================


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
    # Build aggregation dictionary for pandas
    agg_dict = {}
    for col, func_list in aggregations.items():
        agg_dict[col] = func_list

    # Perform groupby and aggregation
    try:
        df_aggregated = df.groupby(group_columns, as_index=False, dropna=False).agg(agg_dict)

        # Flatten column names (MultiIndex from agg with multiple functions)
        if isinstance(df_aggregated.columns, pd.MultiIndex):
            df_aggregated.columns = ['_'.join(col).strip() for col in df_aggregated.columns.values]
            # Remove trailing underscores from group columns
            new_columns = []
            for col in df_aggregated.columns:
                if col.endswith('_'):
                    # Check if it's a group column (base name without underscore)
                    base_name = col[:-1]
                    if base_name in group_columns:
                        new_columns.append(base_name)
                    else:
                        new_columns.append(col)
                else:
                    new_columns.append(col)
            df_aggregated.columns = new_columns

    except Exception as e:
        return err(AggregationFailedError(str(e)))

    return ok(df_aggregated)
