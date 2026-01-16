"""Cleaning operations for DataFrames.

This module provides data cleaning operations that can be applied to pandas DataFrames.
All functions return Result types for explicit error handling.
"""

from typing import Any

import pandas as pd

from excel_toolkit.fp import ok, err, is_ok, is_err, unwrap, unwrap_err, Result
from excel_toolkit.models.error_types import (
    ColumnNotFoundError,
    InvalidParameterError,
    InvalidFillStrategyError,
    FillFailedError,
    CleaningError,
)


# =============================================================================
# Trimming Operations
# =============================================================================


def trim_whitespace(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    side: str = "both"
) -> Result[pd.DataFrame, ColumnNotFoundError | InvalidParameterError | CleaningError]:
    """Trim whitespace from string columns.

    Args:
        df: Source DataFrame
        columns: Columns to trim (None = all string columns)
        side: Which side to trim ("left", "right", "both")

    Returns:
        Result[pd.DataFrame, ColumnNotFoundError | InvalidParameterError] - Cleaned DataFrame or error

    Errors:
        - ColumnNotFoundError: Specified columns don't exist
        - InvalidParameterError: Invalid side parameter

    Implementation:
        - If columns is None, detect all string/object dtype columns
        - Apply str.strip() for "both", str.lstrip() for "left", str.rstrip() for "right"
        - Handle NaN values (preserve them)
        - Return modified copy of DataFrame

    Examples:
        columns=["Name"], side="both" → Trim " John " to "John"
        columns=None, side="left" → Trim all string columns on left
    """
    # Validate side parameter
    if side not in ["left", "right", "both"]:
        return err(InvalidParameterError(
            parameter="side",
            value=side,
            valid_values=["left", "right", "both"]
        ))

    # Determine columns to trim
    if columns is None:
        # Find all string/object dtype columns
        columns = df.select_dtypes(include=['object', 'string']).columns.tolist()

    # Validate columns exist
    missing_columns = [col for col in columns if col not in df.columns]
    if missing_columns:
        return err(ColumnNotFoundError(
            column=missing_columns[0] if len(missing_columns) == 1 else f"{', '.join(missing_columns[:-1])} and {missing_columns[-1]}",
            available=list(df.columns)
        ))

    # Create a copy to avoid modifying original
    df_clean = df.copy()

    try:
        # Apply trimming based on side
        for col in columns:
            if df_clean[col].dtype == 'object' or str(df_clean[col].dtype) == 'string':
                if side == "both":
                    df_clean[col] = df_clean[col].str.strip()
                elif side == "left":
                    df_clean[col] = df_clean[col].str.lstrip()
                elif side == "right":
                    df_clean[col] = df_clean[col].str.rstrip()
    except Exception as e:
        return err(CleaningError(f"Failed to trim whitespace: {str(e)}"))

    return ok(df_clean)


# =============================================================================
# Deduplication Operations
# =============================================================================


def remove_duplicates(
    df: pd.DataFrame,
    subset: list[str] | None = None,
    keep: str = "first"
) -> Result[pd.DataFrame, ColumnNotFoundError | InvalidParameterError | CleaningError]:
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
        - CleaningError: Deduplication failed

    Implementation:
        - Validate keep parameter is "first", "last", or False
        - If subset is provided, validate columns exist
        - Use df.drop_duplicates(subset=subset, keep=keep)
        - Return new DataFrame without duplicates

    Examples:
        subset=["ID"], keep="first" → Keep first occurrence of each ID
        subset=None, keep=False → Remove all duplicates entirely
    """
    # Validate keep parameter
    if keep not in ["first", "last", False]:
        return err(InvalidParameterError(
            parameter="keep",
            value=str(keep),
            valid_values=["first", "last", "False"]
        ))

    # Validate subset columns if provided
    if subset is not None:
        missing_columns = [col for col in subset if col not in df.columns]
        if missing_columns:
            return err(ColumnNotFoundError(
                column=missing_columns[0] if len(missing_columns) == 1 else f"{', '.join(missing_columns[:-1])} and {missing_columns[-1]}",
                available=list(df.columns)
            ))

    try:
        df_dedup = df.drop_duplicates(subset=subset, keep=keep)
    except Exception as e:
        return err(CleaningError(f"Failed to remove duplicates: {str(e)}"))

    return ok(df_dedup)


# =============================================================================
# Missing Value Operations
# =============================================================================


def fill_missing_values(
    df: pd.DataFrame,
    strategy: str | dict = "forward",
    columns: list[str] | None = None,
    value: Any = None
) -> Result[pd.DataFrame, ColumnNotFoundError | InvalidFillStrategyError | FillFailedError]:
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
        - InvalidFillStrategyError: Invalid strategy or parameters
        - FillFailedError: Fill operation failed

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
    valid_strategies = ["forward", "backward", "mean", "median", "constant", "drop"]

    # Create a copy to avoid modifying original
    df_filled = df.copy()

    try:
        if isinstance(strategy, dict):
            # Validate each column exists and apply its strategy
            for col, col_strategy in strategy.items():
                if col not in df.columns:
                    return err(ColumnNotFoundError(
                        column=col,
                        available=list(df.columns)
                    ))

                if col_strategy not in valid_strategies:
                    return err(InvalidFillStrategyError(
                        strategy=col_strategy,
                        valid_strategies=valid_strategies
                    ))

                # Apply strategy to column
                result = _apply_fill_strategy(df_filled, col, col_strategy, value)
                if is_err(result):
                    return result
                df_filled = unwrap(result)

        else:
            # Apply same strategy to specified or all columns
            if strategy not in valid_strategies:
                return err(InvalidFillStrategyError(
                    strategy=strategy,
                    valid_strategies=valid_strategies
                ))

            # Determine columns to fill
            if columns is None:
                # Find all columns with missing values
                columns = df_filled.columns[df_filled.isna().any()].tolist()

            # Validate columns exist
            missing_columns = [col for col in columns if col not in df_filled.columns]
            if missing_columns:
                return err(ColumnNotFoundError(
                    column=missing_columns[0] if len(missing_columns) == 1 else f"{', '.join(missing_columns[:-1])} and {missing_columns[-1]}",
                    available=list(df_filled.columns)
                ))

            # Handle drop strategy at DataFrame level
            if strategy == "drop":
                df_filled = df_filled.dropna(subset=columns)
            else:
                # Apply strategy to each column
                for col in columns:
                    result = _apply_fill_strategy(df_filled, col, strategy, value)
                    if is_err(result):
                        return result
                    df_filled = unwrap(result)

    except Exception as e:
        return err(FillFailedError(
            column="multiple" if columns is None or len(columns) > 1 else (columns[0] if columns else "unknown"),
            reason=str(e)
        ))

    return ok(df_filled)


def _apply_fill_strategy(
    df: pd.DataFrame,
    column: str,
    strategy: str,
    value: Any = None
) -> Result[pd.DataFrame, FillFailedError]:
    """Apply fill strategy to a single column.

    Helper function for fill_missing_values.
    """
    try:
        if strategy == "forward":
            df[column] = df[column].ffill()
        elif strategy == "backward":
            df[column] = df[column].bfill()
        elif strategy == "mean":
            # Only works on numeric columns
            if pd.api.types.is_numeric_dtype(df[column]):
                mean_value = df[column].mean()
                if pd.isna(mean_value):
                    return err(FillFailedError(
                        column=column,
                        reason="Cannot calculate mean (all values are NaN)"
                    ))
                df[column] = df[column].fillna(mean_value)
            else:
                return err(FillFailedError(
                    column=column,
                    reason=f"Cannot apply mean strategy to non-numeric column (dtype: {df[column].dtype})"
                ))
        elif strategy == "median":
            # Only works on numeric columns
            if pd.api.types.is_numeric_dtype(df[column]):
                median_value = df[column].median()
                if pd.isna(median_value):
                    return err(FillFailedError(
                        column=column,
                        reason="Cannot calculate median (all values are NaN)"
                    ))
                df[column] = df[column].fillna(median_value)
            else:
                return err(FillFailedError(
                    column=column,
                    reason=f"Cannot apply median strategy to non-numeric column (dtype: {df[column].dtype})"
                ))
        elif strategy == "constant":
            if value is None and strategy == "constant":
                return err(FillFailedError(
                    column=column,
                    reason="Value parameter required for constant strategy"
                ))
            df[column] = df[column].fillna(value)
        elif strategy == "drop":
            # This is handled at DataFrame level, not per column
            pass

        return ok(df)

    except Exception as e:
        return err(FillFailedError(
            column=column,
            reason=str(e)
        ))


# =============================================================================
# Column Standardization Operations
# =============================================================================


def standardize_columns(
    df: pd.DataFrame,
    case: str = "lower",
    separator: str = "_",
    remove_special: bool = False
) -> Result[pd.DataFrame, InvalidParameterError | CleaningError]:
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
        - CleaningError: Standardization failed

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
    # Validate case parameter
    if case not in ["lower", "upper", "title", "snake"]:
        return err(InvalidParameterError(
            parameter="case",
            value=case,
            valid_values=["lower", "upper", "title", "snake"]
        ))

    try:
        # Create a copy
        df_std = df.copy()

        # Get original column names
        original_columns = list(df_std.columns)
        new_columns = []

        for col in original_columns:
            # Convert to string if not already
            col_str = str(col)

            # Strip leading/trailing whitespace
            col_str = col_str.strip()

            # Apply case conversion
            if case == "lower":
                col_str = col_str.lower()
            elif case == "upper":
                col_str = col_str.upper()
            elif case == "title":
                col_str = col_str.title()
            elif case == "snake":
                # Convert to snake_case
                # Insert separator before capital letters (for CamelCase)
                import re
                col_str = re.sub(r'(?<=[a-z])(?=[A-Z])', separator, col_str)
                # Convert to lowercase and replace spaces with separator
                col_str = col_str.lower().replace(' ', separator)

            # Remove special characters if requested (but preserve separator and spaces)
            if remove_special:
                import re
                # Keep only alphanumeric, separator, and spaces
                col_str = re.sub(rf'[^\w\s{re.escape(separator)}]', '', col_str)

            # Strip again after removing special chars
            col_str = col_str.strip()

            # Ensure not empty
            if not col_str:
                col_str = "column"

            new_columns.append(col_str)

        # Ensure uniqueness
        seen = {}
        final_columns = []
        for i, col in enumerate(new_columns):
            if col in seen:
                # Add suffix to make unique
                suffix = 1
                while f"{col}{separator}{suffix}" in seen:
                    suffix += 1
                col = f"{col}{separator}{suffix}"
            seen[col] = True
            final_columns.append(col)

        # Rename columns
        df_std.columns = final_columns

        return ok(df_std)

    except Exception as e:
        return err(CleaningError(f"Failed to standardize columns: {str(e)}"))


# =============================================================================
# Combined Cleaning Operations
# =============================================================================


def clean_dataframe(
    df: pd.DataFrame,
    trim: bool = False,
    trim_columns: list[str] | None = None,
    trim_side: str = "both",
    remove_dup: bool = False,
    dup_subset: list[str] | None = None,
    dup_keep: str = "first",
    fill_strategy: str | dict | None = None,
    fill_value: Any = None,
    standardize: bool = False,
    standardize_case: str = "lower"
) -> Result[pd.DataFrame, ColumnNotFoundError | InvalidParameterError | InvalidFillStrategyError | FillFailedError | CleaningError]:
    """Apply multiple cleaning operations in sequence.

    Args:
        df: Source DataFrame
        trim: Whether to trim whitespace
        trim_columns: Columns to trim (None = all string columns)
        trim_side: Side to trim ("left", "right", "both")
        remove_dup: Whether to remove duplicates
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
        - Apply operations in order: standardize → trim → fill → remove_dup
        - Stop and return error if any operation fails
        - Return cleaned DataFrame

    Examples:
        Clean with all operations
        Clean with only trim and remove_dup
        Clean with custom parameters for each operation
    """
    result = df

    # Apply in order: standardize → trim → fill → remove_dup

    if standardize:
        std_result = standardize_columns(
            result if isinstance(result, pd.DataFrame) else unwrap(result),
            case=standardize_case
        )
        if is_err(std_result):
            return std_result
        result = unwrap(std_result)

    if trim:
        trim_result = trim_whitespace(
            result if isinstance(result, pd.DataFrame) else unwrap(result),
            columns=trim_columns,
            side=trim_side
        )
        if is_err(trim_result):
            return trim_result
        result = unwrap(trim_result)

    if fill_strategy is not None:
        fill_result = fill_missing_values(
            result if isinstance(result, pd.DataFrame) else unwrap(result),
            strategy=fill_strategy,
            value=fill_value
        )
        if is_err(fill_result):
            return fill_result
        result = unwrap(fill_result)

    if remove_dup:
        dup_result = remove_duplicates(
            result if isinstance(result, pd.DataFrame) else unwrap(result),
            subset=dup_subset,
            keep=dup_keep
        )
        if is_err(dup_result):
            return dup_result
        result = unwrap(dup_result)

    return ok(result)
