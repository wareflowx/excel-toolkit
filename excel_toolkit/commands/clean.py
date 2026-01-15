"""Clean command implementation.

Cleans data by removing whitespace, standardizing case, and fixing formatting issues.
"""

from pathlib import Path
from typing import Any

import typer
import pandas as pd
import numpy as np

from excel_toolkit.core import HandlerFactory, ExcelHandler, CSVHandler
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err
from excel_toolkit.commands.common import display_table


def clean(
    file_path: str = typer.Argument(..., help="Path to input file"),
    trim: bool = typer.Option(False, "--trim", help="Remove leading/trailing whitespace"),
    lowercase: bool = typer.Option(False, "--lowercase", help="Convert to lowercase"),
    uppercase: bool = typer.Option(False, "--uppercase", help="Convert to uppercase"),
    titlecase: bool = typer.Option(False, "--titlecase", help="Convert to title case"),
    casefold: bool = typer.Option(False, "--casefold", help="Apply casefold for case-insensitive comparison"),
    whitespace: bool = typer.Option(False, "--whitespace", help="Normalize multiple whitespace to single space"),
    remove_special: bool = typer.Option(False, "--remove-special", help="Remove special characters"),
    keep_alphanumeric: bool = typer.Option(False, "--keep-alphanumeric", help="Keep only alphanumeric characters"),
    columns: str | None = typer.Option(None, "--columns", "-c", help="Specific columns to clean"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show preview without writing"),
    sheet: str | None = typer.Option(None, "--sheet", "-s", help="Sheet name for Excel files"),
) -> None:
    """Clean data by removing whitespace, standardizing case, and fixing formatting issues.

    Various cleaning operations can be applied individually or combined.
    Operations are applied in the order they appear in the command.

    Examples:
        xl clean data.csv --trim --lowercase --columns "name,email"
        xl clean data.xlsx --trim --whitespace --output cleaned.xlsx
        xl clean contacts.csv --keep-alphanumeric --column "phone"
        xl clean data.csv --uppercase --columns "category" --dry-run
    """
    path = Path(file_path)
    factory = HandlerFactory()

    # Step 1: Validate file exists
    if not path.exists():
        typer.echo(f"File not found: {file_path}", err=True)
        raise typer.Exit(1)

    # Step 2: Check if at least one cleaning operation is specified
    operations = []
    if trim:
        operations.append("trim")
    if lowercase:
        operations.append("lowercase")
    if uppercase:
        operations.append("uppercase")
    if titlecase:
        operations.append("titlecase")
    if casefold:
        operations.append("casefold")
    if whitespace:
        operations.append("whitespace")
    if remove_special:
        operations.append("remove_special")
    if keep_alphanumeric:
        operations.append("keep_alphanumeric")

    if not operations:
        typer.echo("Error: At least one cleaning operation must be specified", err=True)
        typer.echo("Available operations: --trim, --lowercase, --uppercase, --titlecase, --casefold, --whitespace, --remove-special, --keep-alphanumeric")
        raise typer.Exit(1)

    # Check for conflicting operations
    if lowercase and uppercase:
        typer.echo("Error: Cannot specify both --lowercase and --uppercase", err=True)
        raise typer.Exit(1)

    if lowercase and titlecase:
        typer.echo("Error: Cannot specify both --lowercase and --titlecase", err=True)
        raise typer.Exit(1)

    if uppercase and titlecase:
        typer.echo("Error: Cannot specify both --uppercase and --titlecase", err=True)
        raise typer.Exit(1)

    if casefold and (lowercase or uppercase or titlecase):
        typer.echo("Warning: --casefold combined with case operation. Case operations will be applied first.", err=False)

    if remove_special and keep_alphanumeric:
        typer.echo("Error: Cannot specify both --remove-special and --keep-alphanumeric", err=True)
        raise typer.Exit(1)

    # Step 3: Get handler
    handler_result = factory.get_handler(path)
    if is_err(handler_result):
        error = unwrap_err(handler_result)
        typer.echo(f"{error}", err=True)
        raise typer.Exit(1)

    handler = unwrap(handler_result)

    # Step 4: Read file
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

    # Step 5: Handle empty file
    if df.empty:
        typer.echo("File is empty (no data rows)")
        raise typer.Exit(0)

    # Step 6: Determine columns to clean
    if columns:
        column_list = [c.strip() for c in columns.split(",")]
        # Validate column names exist
        missing_cols = [c for c in column_list if c not in df.columns]
        if missing_cols:
            typer.echo(f"Error: Columns not found: {', '.join(missing_cols)}", err=True)
            typer.echo(f"Available columns: {', '.join(df.columns)}")
            raise typer.Exit(1)
    else:
        # Clean all string columns
        column_list = []
        for col in df.columns:
            if df[col].dtype == "object":
                column_list.append(col)

    if not column_list:
        typer.echo("No string columns to clean")
        typer.echo("Use --columns to specify which columns to clean")
        raise typer.Exit(0)

    # Step 7: Apply cleaning operations
    df_cleaned = df.copy()

    for col in column_list:
        # Only clean string columns
        if df_cleaned[col].dtype != "object":
            continue

        series = df_cleaned[col].copy()

        # Apply operations in order
        if trim:
            series = _trim_whitespace(series)

        if whitespace:
            series = _normalize_whitespace(series)

        if lowercase:
            series = _apply_case(series, "lower")

        if uppercase:
            series = _apply_case(series, "upper")

        if titlecase:
            series = _apply_case(series, "title")

        if casefold:
            series = _apply_case(series, "casefold")

        if remove_special:
            series = _remove_special_chars(series)

        if keep_alphanumeric:
            series = _keep_alphanumeric(series)

        df_cleaned[col] = series

    # Step 8: Display summary
    typer.echo(f"Cleaned {len(column_list)} column(s)")
    typer.echo(f"Operations: {', '.join(operations)}")
    if columns:
        typer.echo(f"Columns: {columns}")
    typer.echo(f"Rows: {original_count}")
    typer.echo("")

    # Step 9: Handle dry-run mode
    if dry_run:
        typer.echo("Preview of cleaned data:")
        preview_rows = min(5, original_count)
        display_table(df_cleaned.head(preview_rows))
        raise typer.Exit(0)

    # Step 10: Write output or display
    if output:
        output_path = Path(output)
        write_result = factory.write_file(df_cleaned, output_path)
        if is_err(write_result):
            error = unwrap_err(write_result)
            typer.echo(f"Error writing file: {error}", err=True)
            raise typer.Exit(1)
        typer.echo(f"Written to: {output}")
    else:
        # Display data
        display_table(df_cleaned)


def _trim_whitespace(series: pd.Series) -> pd.Series:
    """Remove leading and trailing whitespace from string values."""
    # Convert to string and strip whitespace
    return series.astype(str).str.strip()


def _normalize_whitespace(series: pd.Series) -> pd.Series:
    """Normalize multiple whitespace characters to single space."""
    # Replace multiple whitespace characters with single space
    return series.astype(str).str.replace(r'\s+', ' ', regex=True)


def _apply_case(series: pd.Series, case_type: str) -> pd.Series:
    """Apply case transformation to string values."""
    if case_type == "lower":
        return series.astype(str).str.lower()
    elif case_type == "upper":
        return series.astype(str).str.upper()
    elif case_type == "title":
        return series.astype(str).str.title()
    elif case_type == "casefold":
        return series.astype(str).str.casefold()
    return series


def _remove_special_chars(series: pd.Series) -> pd.Series:
    """Remove special characters, keeping only letters, numbers, and basic punctuation."""
    # Keep alphanumeric, spaces, and basic punctuation (. , - _ @)
    return series.astype(str).str.replace(r'[^\w\s\.\,\-\_@]', '', regex=True)


def _keep_alphanumeric(series: pd.Series) -> pd.Series:
    """Keep only alphanumeric characters (letters and numbers)."""
    # Remove everything except letters and numbers
    return series.astype(str).str.replace(r'[^a-zA-Z0-9]', '', regex=True)


# Create CLI app for this command
app = typer.Typer(help="Clean data by removing whitespace and standardizing case")

# Register the command
app.command()(clean)
