"""Sorting operations for DataFrames.

This module provides sorting operations that can be applied to pandas DataFrames.
All functions return Result types for explicit error handling.
"""

from typing import Any

import pandas as pd

from excel_toolkit.fp import ok, err, is_ok, is_err, unwrap, unwrap_err, Result
from excel_toolkit.models.error_types import (
    NoColumnsError,
    ColumnNotFoundError,
    NotComparableError,
    SortFailedError,
    SortValidationError,
    SortError,
)


# =============================================================================
# Validation Functions
# =============================================================================


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
    if not columns:
        return err(NoColumnsError())

    missing = [c for c in columns if c not in df.columns]
    if missing:
        return err(ColumnNotFoundError(
            column=missing[0],
            available=list(df.columns)
        ))

    return ok(None)


# =============================================================================
# Main Operations
# =============================================================================


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
    # Validate na_position
    if na_position not in ("first", "last"):
        return err(SortFailedError(
            message=f"Invalid na_position: {na_position}. Must be 'first' or 'last'"
        ))

    # Validate columns exist
    validation_result = validate_sort_columns(df, columns)
    if is_err(validation_result):
        # Convert SortValidationError to SortError
        error = unwrap_err(validation_result)
        if isinstance(error, NoColumnsError):
            return err(SortFailedError("No columns specified for sorting"))
        elif isinstance(error, ColumnNotFoundError):
            return err(SortFailedError(
                f"Column '{error.column}' not found. Available: {', '.join(error.available)}"
            ))

    # Sort
    try:
        df_sorted = df.sort_values(
            by=columns,
            ascending=ascending,
            na_position=na_position,
        )
    except TypeError as e:
        error_msg = str(e)
        if "not comparable" in error_msg or "unorderable types" in error_msg or "mixed types" in error_msg or "not supported between instances" in error_msg:
            # Find the problematic column
            for col in columns:
                if df[col].dtype == "object":
                    return err(NotComparableError(
                        column=col,
                        message=error_msg
                    ))
            return err(NotComparableError(
                column=columns[0],
                message=error_msg
            ))
        return err(SortFailedError(error_msg))
    except Exception as e:
        return err(SortFailedError(str(e)))

    # Limit rows if specified
    if limit is not None:
        df_sorted = df_sorted.head(limit)

    return ok(df_sorted)
