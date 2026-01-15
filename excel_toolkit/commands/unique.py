"""Unique command implementation.

Extract unique values from a dataset.
"""

from pathlib import Path
from typing import Any

import typer
import pandas as pd

from excel_toolkit.core import HandlerFactory, ExcelHandler, CSVHandler
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err
from excel_toolkit.commands.common import display_table


def unique(
    file_path: str = typer.Argument(..., help="Path to input file"),
    columns: str | None = typer.Option(None, "--columns", "-c", help="Columns to get unique values from (comma-separated)"),
    count: bool = typer.Option(False, "--count", help="Show count of each unique value"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show preview without writing"),
    sheet: str | None = typer.Option(None, "--sheet", "-s", help="Sheet name for Excel files"),
) -> None:
    """Extract unique values from a data file.

    Get unique values from specified columns or unique rows across all columns.

    Examples:
        xl unique data.xlsx --columns "Category" --output categories.xlsx
        xl unique data.csv --columns "Region,Product" --output unique.xlsx
        xl unique contacts.xlsx --columns "Email" --count --output email-counts.xlsx
    """
    path = Path(file_path)
    factory = HandlerFactory()

    # Step 1: Validate file exists
    if not path.exists():
        typer.echo(f"File not found: {file_path}", err=True)
        raise typer.Exit(1)

    # Step 2: Validate columns specified
    if not columns:
        typer.echo("Error: Must specify --columns", err=True)
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

    # Step 6: Parse columns
    column_list = [c.strip() for c in columns.split(",")]
    # Validate columns exist
    missing_cols = [c for c in column_list if c not in df.columns]
    if missing_cols:
        typer.echo(f"Error: Columns not found: {', '.join(missing_cols)}", err=True)
        typer.echo(f"Available columns: {', '.join(df.columns)}")
        raise typer.Exit(1)

    # Step 7: Get unique values
    if len(column_list) == 1:
        # Single column - get unique values
        col = column_list[0]
        unique_values = df[col].dropna().unique()

        if count:
            # Get value counts
            value_counts = df[col].value_counts().reset_index()
            value_counts.columns = [col, 'count']
            df_unique = value_counts
        else:
            # Just unique values
            df_unique = pd.DataFrame({col: unique_values})
    else:
        # Multiple columns - get unique rows
        df_subset = df[column_list].copy()
        df_unique = df_subset.drop_duplicates().reset_index(drop=True)

        if count:
            # Add count column
            df_unique['count'] = df_subset.groupby(column_list, dropna=False).size().values

    unique_count = len(df_unique)

    # Step 8: Display summary
    typer.echo(f"Original rows: {original_count}")
    typer.echo(f"Unique rows: {unique_count}")
    if len(column_list) == 1:
        typer.echo(f"Column: {column_list[0]}")
    else:
        typer.echo(f"Columns: {', '.join(column_list)}")
    typer.echo("")

    # Step 9: Handle dry-run mode
    if dry_run:
        typer.echo("Preview of unique values:")
        preview_rows = min(5, unique_count)
        display_table(df_unique.head(preview_rows))
        raise typer.Exit(0)

    # Step 10: Write output or display
    if output:
        output_path = Path(output)
        write_result = factory.write_file(df_unique, output_path)
        if is_err(write_result):
            error = unwrap_err(write_result)
            typer.echo(f"Error writing file: {error}", err=True)
            raise typer.Exit(1)
        typer.echo(f"Written to: {output}")
    else:
        # Display data
        display_table(df_unique)


# Create CLI app for this command
app = typer.Typer(help="Extract unique values from a data file")

# Register the command
app.command()(unique)
