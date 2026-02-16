"""Head command implementation.

Displays the first N rows of a data file in various formats.
"""

from pathlib import Path

import typer

from excel_toolkit.commands.common import (
    display_column_types,
    display_csv,
    display_json,
    display_table,
    format_file_info,
    read_data_file,
)


def head(
    file_path: str,
    rows: int = typer.Option(5, "--rows", "-n", help="Number of rows to display"),
    sheet: str | None = typer.Option(None, "--sheet", "-s", help="Sheet name for Excel files"),
    show_columns: bool = typer.Option(
        False, "--show-columns", "-c", help="Show column information"
    ),
    max_columns: int | None = typer.Option(None, "--max-columns", help="Limit columns displayed"),
    format: str = typer.Option("table", "--format", "-f", help="Output format (table, csv, json)"),
) -> None:
    """Display the first N rows of a data file.

    Shows the beginning of a file to quickly inspect its contents.
    Supports Excel and CSV files with multiple output formats.

    Args:
        file_path: Path to the file
        rows: Number of rows to display (default: 5)
        sheet: Sheet name for Excel files (default: first sheet)
        show_columns: Show column names and types
        max_columns: Maximum number of columns to display
        format: Output format: table, csv, or json

    Raises:
        typer.Exit: If file cannot be read or invalid format
    """
    # 0. Validate format
    valid_formats = ["table", "csv", "json"]
    if format not in valid_formats:
        typer.echo(f"Unknown format: {format}", err=True)
        typer.echo(f"Supported formats: {', '.join(valid_formats)}", err=True)
        raise typer.Exit(1)

    # 1. Read file
    df = read_data_file(file_path, sheet)

    # 2. Handle empty file
    if df.empty:
        typer.echo("File is empty (no data rows)")
        raise typer.Exit(0)

    # 3. Limit columns if requested
    if max_columns and len(df.columns) > max_columns:
        df = df.iloc[:, :max_columns]

    # 4. Get first N rows
    df_head = df.head(rows)

    # 5. Display file info
    path = Path(file_path)
    typer.echo(format_file_info(str(path), sheet=sheet, total_rows=len(df), total_cols=len(df.columns)))

    # 6. Show column information if requested
    if show_columns:
        display_column_types(df)

    # 7. Display data based on format
    if format == "table":
        display_table(df_head)
    elif format == "csv":
        display_csv(df_head)
    elif format == "json":
        display_json(df_head)


# Create CLI app for this command
app = typer.Typer(help="Display the first N rows of a data file")

# Register the command
app.command()(head)
