"""Clean command implementation.

Cleans data by removing whitespace, standardizing case, and fixing formatting issues.
"""

from pathlib import Path

import typer
import pandas as pd

from excel_toolkit.core import HandlerFactory
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err
from excel_toolkit.operations.cleaning import trim_whitespace
from excel_toolkit.commands.common import (
    read_data_file,
    write_or_display,
    display_table,
)


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
    # 1. Validate operations
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

    # 2. Read file
    df = read_data_file(file_path, sheet)
    original_count = len(df)

    # 3. Handle empty file
    if df.empty:
        typer.echo("File is empty (no data rows)")
        raise typer.Exit(0)

    # 4. Determine columns to clean
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
        column_list = [col for col in df.columns if df[col].dtype == "object"]

    if not column_list:
        typer.echo("No string columns to clean")
        typer.echo("Use --columns to specify which columns to clean")
        raise typer.Exit(0)

    # 5. Apply cleaning operations
    df_cleaned = df.copy()

    # Use trim_whitespace operation if --trim specified
    if trim:
        result = trim_whitespace(df_cleaned, columns=column_list, side="both")
        if is_err(result):
            error = unwrap_err(result)
            typer.echo(f"Error trimming whitespace: {error}", err=True)
            raise typer.Exit(1)
        df_cleaned = unwrap(result)

    # Apply other operations
    for col in column_list:
        # Only clean string columns
        if df_cleaned[col].dtype != "object":
            continue

        series = df_cleaned[col].copy()

        # Apply operations in order
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

    # 6. Display summary
    typer.echo(f"Cleaned {len(column_list)} column(s)")
    typer.echo(f"Operations: {', '.join(operations)}")
    if columns:
        typer.echo(f"Columns: {columns}")
    typer.echo(f"Rows: {original_count}")
    typer.echo("")

    # 7. Handle dry-run mode
    if dry_run:
        typer.echo("Preview of cleaned data:")
        preview_rows = min(5, original_count)
        display_table(df_cleaned.head(preview_rows))
        raise typer.Exit(0)

    # 8. Write or display
    factory = HandlerFactory()
    write_or_display(df_cleaned, factory, output, "table")


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
