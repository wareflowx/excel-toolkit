"""Fill command implementation.

Fill missing values in a dataset.
"""

from pathlib import Path
from typing import Any

import typer
import pandas as pd

from excel_toolkit.core import HandlerFactory, ExcelHandler, CSVHandler
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err
from excel_toolkit.commands.common import display_table


def fill(
    file_path: str = typer.Argument(..., help="Path to input file"),
    columns: str | None = typer.Option(None, "--columns", "-c", help="Columns to fill (comma-separated)"),
    value: str | None = typer.Option(None, "--value", "-v", help="Constant value to fill with"),
    strategy: str | None = typer.Option(None, "--strategy", "-s", help="Statistical strategy: mean, median, mode, min, max, ffill, bfill"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show preview without writing"),
    sheet: str | None = typer.Option(None, "--sheet", help="Sheet name for Excel files"),
) -> None:
    """Fill missing values in a data file.

    Fill NaN/None values with constants, statistical measures, or forward/backward fill.

    Examples:
        xl fill data.xlsx --columns "Age" --value "0" --output filled.xlsx
        xl fill data.csv --strategy "mean" --output filled.xlsx
        xl fill data.xlsx --columns "Price" --strategy "median" --output filled.xlsx
        xl fill sales.xlsx --strategy "ffill" --output filled.xlsx
    """
    path = Path(file_path)
    factory = HandlerFactory()

    # Step 1: Validate file exists
    if not path.exists():
        typer.echo(f"File not found: {file_path}", err=True)
        raise typer.Exit(1)

    # Step 2: Validate fill options
    if value is None and strategy is None:
        typer.echo("Error: Must specify either --value or --strategy", err=True)
        typer.echo("Available strategies: mean, median, mode, min, max, ffill, bfill")
        raise typer.Exit(1)

    if value is not None and strategy is not None:
        typer.echo("Error: Cannot use both --value and --strategy", err=True)
        raise typer.Exit(1)

    # Step 3: Validate strategy
    valid_strategies = ["mean", "median", "mode", "min", "max", "ffill", "bfill"]
    if strategy and strategy not in valid_strategies:
        typer.echo(f"Error: Invalid strategy '{strategy}'", err=True)
        typer.echo(f"Valid strategies: {', '.join(valid_strategies)}")
        raise typer.Exit(1)

    # Step 4: Get handler
    handler_result = factory.get_handler(path)
    if is_err(handler_result):
        error = unwrap_err(handler_result)
        typer.echo(f"{error}", err=True)
        raise typer.Exit(1)

    handler = unwrap(handler_result)

    # Step 5: Read file
    if isinstance(handler, ExcelHandler):
        sheet_name = sheet
        kwargs = {"sheet_name": sheet_name} if sheet_name else {}
        read_result = handler.read(path, **kwargs)
    elif isinstance(handler, CSVHandler):
        # Auto-detect encoding and delimiter
        encoding_result = handler.detect_encoding(path)
        encoding = unwrap(encoding_result) if is_ok(encoding_result) else "utf-8"

        delimiter_result = handler.detect_delimiter(path, encoding)
        delimiter = unwrap(delimiter_result) if is_ok(delimiter_result) else ","

        read_result = handler.read(path, encoding=encoding, delimiter=delimiter)
    else:
        typer.echo("Unsupported handler type", err=True)
        raise typer.Exit(1)

    if is_err(read_result):
        error = unwrap_err(read_result)
        typer.echo(f"Error reading file: {error}", err=True)
        raise typer.Exit(1)

    df = unwrap(read_result)
    original_count = len(df)

    # Step 6: Handle empty file
    if df.empty:
        typer.echo("File is empty (no data rows)")
        raise typer.Exit(0)

    # Step 7: Determine columns to fill
    if columns:
        column_list = [c.strip() for c in columns.split(",")]
        # Validate columns exist
        missing_cols = [c for c in column_list if c not in df.columns]
        if missing_cols:
            typer.echo(f"Error: Columns not found: {', '.join(missing_cols)}", err=True)
            typer.echo(f"Available columns: {', '.join(df.columns)}")
            raise typer.Exit(1)
        target_columns = column_list
    else:
        # Fill all columns with missing values
        target_columns = df.columns[df.isnull().any()].tolist()

    if not target_columns:
        typer.echo("No columns with missing values found")
        raise typer.Exit(0)

    # Step 8: Count missing values before filling
    missing_before = df[target_columns].isnull().sum().sum()

    # Step 9: Apply fill strategy
    df_filled = df.copy()

    for col in target_columns:
        if strategy == "mean":
            # Only for numeric columns
            if pd.api.types.is_numeric_dtype(df_filled[col]):
                df_filled[col].fillna(df_filled[col].mean(), inplace=True)
            else:
                typer.echo(f"Warning: Cannot apply 'mean' to non-numeric column '{col}', skipping", err=True)
        elif strategy == "median":
            # Only for numeric columns
            if pd.api.types.is_numeric_dtype(df_filled[col]):
                df_filled[col].fillna(df_filled[col].median(), inplace=True)
            else:
                typer.echo(f"Warning: Cannot apply 'median' to non-numeric column '{col}', skipping", err=True)
        elif strategy == "mode":
            # Mode can be applied to any column type
            mode_values = df_filled[col].mode()
            if len(mode_values) > 0:
                df_filled[col].fillna(mode_values[0], inplace=True)
            else:
                typer.echo(f"Warning: No mode found for column '{col}', skipping", err=True)
        elif strategy == "min":
            # Only for numeric columns
            if pd.api.types.is_numeric_dtype(df_filled[col]):
                df_filled[col].fillna(df_filled[col].min(), inplace=True)
            else:
                typer.echo(f"Warning: Cannot apply 'min' to non-numeric column '{col}', skipping", err=True)
        elif strategy == "max":
            # Only for numeric columns
            if pd.api.types.is_numeric_dtype(df_filled[col]):
                df_filled[col].fillna(df_filled[col].max(), inplace=True)
            else:
                typer.echo(f"Warning: Cannot apply 'max' to non-numeric column '{col}', skipping", err=True)
        elif strategy == "ffill":
            # Forward fill (propagate last valid value)
            df_filled[col].fillna(method='ffill', inplace=True)
            # If still NaN at the beginning, backward fill
            df_filled[col].fillna(method='bfill', inplace=True)
        elif strategy == "bfill":
            # Backward fill (propagate next valid value)
            df_filled[col].fillna(method='bfill', inplace=True)
            # If still NaN at the end, forward fill
            df_filled[col].fillna(method='ffill', inplace=True)
        elif value is not None:
            # Fill with constant value
            # Try to convert to appropriate type
            try:
                # Try numeric conversion
                numeric_value = float(value)
                if pd.api.types.is_numeric_dtype(df_filled[col]):
                    df_filled[col].fillna(numeric_value, inplace=True)
                else:
                    df_filled[col].fillna(value, inplace=True)
            except ValueError:
                # Use as string
                df_filled[col].fillna(value, inplace=True)

    # Step 10: Count missing values after filling
    missing_after = df_filled[target_columns].isnull().sum().sum()
    filled_count = missing_before - missing_after

    if filled_count == 0:
        typer.echo("No missing values were filled")
        if not dry_run and not output:
            display_table(df)
        raise typer.Exit(0)

    # Step 11: Display summary
    typer.echo(f"Missing values before: {missing_before}")
    typer.echo(f"Missing values after: {missing_after}")
    typer.echo(f"Values filled: {filled_count}")
    if strategy:
        typer.echo(f"Strategy: {strategy}")
    else:
        typer.echo(f"Value: {value}")
    if columns:
        typer.echo(f"Columns: {', '.join(target_columns)}")
    else:
        typer.echo(f"Columns: all columns with missing values")
    typer.echo("")

    # Step 12: Handle dry-run mode
    if dry_run:
        typer.echo("Preview of filled data:")
        preview_rows = min(5, original_count)
        display_table(df_filled.head(preview_rows))
        raise typer.Exit(0)

    # Step 13: Write output or display
    if output:
        output_path = Path(output)
        write_result = factory.write_file(df_filled, output_path)
        if is_err(write_result):
            error = unwrap_err(write_result)
            typer.echo(f"Error writing file: {error}", err=True)
            raise typer.Exit(1)
        typer.echo(f"Written to: {output}")
    else:
        # Display data
        display_table(df_filled)


# Create CLI app for this command
app = typer.Typer(help="Fill missing values in a data file")

# Register the command
app.command()(fill)
