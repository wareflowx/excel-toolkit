"""Sort command implementation.

Sorts rows from data files by column values.
"""

from pathlib import Path
from typing import Any

import typer
import pandas as pd

from excel_toolkit.core import HandlerFactory, ExcelHandler, CSVHandler
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err, ok, err
from excel_toolkit.fp._result import Result
from excel_toolkit.commands.common import (
    display_table,
    display_csv,
    display_json,
    format_file_info,
)


def sort(
    file_path: str = typer.Argument(..., help="Path to input file"),
    columns: str = typer.Option(..., "--columns", "-c", help="Column(s) to sort by (comma-separated)"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    rows: int | None = typer.Option(None, "--rows", "-n", help="Limit number of results"),
    desc: bool = typer.Option(False, "--desc", "-d", help="Sort in descending order"),
    where: str | None = typer.Option(None, "--where", "-w", help="Filter condition before sorting"),
    na_placement: str = typer.Option("last", "--na-placement", help="Where to place NaN values ('first' or 'last')"),
    format: str = typer.Option("table", "--format", "-f", help="Output format (table, csv, json)"),
    sheet: str | None = typer.Option(None, "--sheet", "-s", help="Sheet name for Excel files"),
) -> None:
    """Sort rows from a data file by column values.

    Sorts data by one or more columns in ascending or descending order.
    Optionally filter rows before sorting.

    Examples:
        xl sort data.xlsx --columns salary
        xl sort data.xlsx --columns city,age --rows 10
        xl sort data.csv --columns price --desc --output sorted.csv
        xl sort data.xlsx --columns name --where "age > 30"
        xl sort data.csv --columns date --na-placement first
    """
    path = Path(file_path)
    factory = HandlerFactory()

    # Step 1: Validate file exists
    if not path.exists():
        typer.echo(f"File not found: {file_path}", err=True)
        raise typer.Exit(1)

    # Step 2: Validate na_placement
    if na_placement not in ["first", "last"]:
        typer.echo(f"Invalid na_placement: {na_placement}. Must be 'first' or 'last'", err=True)
        raise typer.Exit(1)

    # Step 3: Parse column list
    column_list = [c.strip() for c in columns.split(",")]
    if not column_list:
        typer.echo("Error: At least one column must be specified", err=True)
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

    # Step 7: Validate column names
    missing_cols = [c for c in column_list if c not in df.columns]
    if missing_cols:
        typer.echo(f"Error: Columns not found: {', '.join(missing_cols)}", err=True)
        typer.echo(f"Available columns: {', '.join(df.columns)}")
        raise typer.Exit(1)

    # Step 8: Apply filter if specified
    if where:
        # Import validation from filter command
        from excel_toolkit.commands.filter import _validate_condition, _normalize_condition

        validation_result = _validate_condition(where)
        if is_err(validation_result):
            error_msg = unwrap_err(validation_result)
            typer.echo(f"Invalid filter condition: {error_msg}", err=True)
            raise typer.Exit(1)

        normalized_condition = _normalize_condition(where)

        try:
            df = df.query(normalized_condition)
        except pd.errors.UndefinedVariableError as e:
            import re
            error_str = str(e)
            col_match = re.search(r"'([^']+)'", error_str)
            if col_match:
                col = col_match.group(1)
                typer.echo(f"Error: Column '{col}' not found", err=True)
                typer.echo(f"Available columns: {', '.join(df.columns)}")
            else:
                typer.echo(f"Error: {error_str}", err=True)
            raise typer.Exit(1)
        except Exception as e:
            error_msg = str(e)
            typer.echo(f"Error filtering data: {error_msg}", err=True)
            typer.echo(f"\nCondition: {where}", err=True)
            raise typer.Exit(1)

        filtered_count = len(df)
        if filtered_count == 0:
            typer.echo("No rows match the filter condition")
            typer.echo(f"Condition: {where}")
            raise typer.Exit(0)
    else:
        filtered_count = original_count

    # Step 9: Sort data
    try:
        # Convert single column to list for consistency
        df_sorted = df.sort_values(
            by=column_list,
            ascending=not desc,
            na_position=na_placement,
        )
    except TypeError as e:
        error_msg = str(e)
        if "not comparable" in error_msg or "unorderable types" in error_msg:
            typer.echo("Error: Cannot sort mixed data types in column", err=True)
            typer.echo("Ensure all values in the column are of the same type", err=True)
        else:
            typer.echo(f"Error sorting data: {error_msg}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error sorting data: {str(e)}", err=True)
        raise typer.Exit(1)

    # Step 10: Limit rows if specified
    if rows is not None:
        df_sorted = df_sorted.head(rows)

    # Step 11: Display summary
    final_count = len(df_sorted)
    typer.echo(f"Sorted {final_count} rows")
    typer.echo(f"Columns: {columns}")
    typer.echo(f"Order: {'descending' if desc else 'ascending'}")
    if where:
        typer.echo(f"Filter: {where} ({filtered_count} of {original_count} rows matched)")
    if na_placement:
        typer.echo(f"NaN placement: {na_placement}")
    typer.echo("")

    # Step 12: Write output or display
    if output:
        output_path = Path(output)
        write_result = factory.write_file(df_sorted, output_path)
        if is_err(write_result):
            error = unwrap_err(write_result)
            typer.echo(f"Error writing file: {error}", err=True)
            raise typer.Exit(1)
        typer.echo(f"Written to: {output}")
    else:
        # Display data
        if format == "table":
            display_table(df_sorted)
        elif format == "csv":
            display_csv(df_sorted)
        elif format == "json":
            display_json(df_sorted)
        else:
            typer.echo(f"Unknown format: {format}", err=True)
            typer.echo("Supported formats: table, csv, json")
            raise typer.Exit(1)


# Create CLI app for this command
app = typer.Typer(help="Sort rows from data files")

# Register the command
app.command()(sort)
