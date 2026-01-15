"""Join command implementation.

Join two datasets based on common columns.
"""

from pathlib import Path
from typing import Any

import typer
import pandas as pd

from excel_toolkit.core import HandlerFactory, ExcelHandler, CSVHandler
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err
from excel_toolkit.commands.common import display_table


def join(
    left_file: str = typer.Argument(..., help="Path to left input file"),
    right_file: str = typer.Argument(..., help="Path to right input file"),
    on: str | None = typer.Option(None, "--on", help="Column name to join on (must exist in both files)"),
    left_on: str | None = typer.Option(None, "--left-on", help="Column name in left file"),
    right_on: str | None = typer.Option(None, "--right-on", help="Column name in right file"),
    how: str = typer.Option("inner", "--how", "-h", help="Join type: inner, left, right, outer"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    left_sheet: str | None = typer.Option(None, "--left-sheet", help="Sheet name for left file"),
    right_sheet: str | None = typer.Option(None, "--right-sheet", help="Sheet name for right file"),
) -> None:
    """Join two datasets based on common columns.

    Perform SQL-like joins between two files.
    Supports inner, left, right, and outer joins.

    Examples:
        xl join customers.xlsx orders.xlsx --on "customer_id" --output merged.xlsx
        xl join left.xlsx right.xlsx --left-on "id" --right-on "user_id" --output joined.xlsx
        xl join data1.xlsx data2.xlsx --on "key" --how left --output left_join.xlsx
    """
    left_path = Path(left_file)
    right_path = Path(right_file)
    factory = HandlerFactory()

    # Step 1: Validate files exist
    if not left_path.exists():
        typer.echo(f"File not found: {left_file}", err=True)
        raise typer.Exit(1)

    if not right_path.exists():
        typer.echo(f"File not found: {right_file}", err=True)
        raise typer.Exit(1)

    # Step 2: Validate join type
    valid_join_types = ["inner", "left", "right", "outer"]
    if how not in valid_join_types:
        typer.echo(f"Error: Invalid join type '{how}'", err=True)
        typer.echo(f"Valid types: {', '.join(valid_join_types)}")
        raise typer.Exit(1)

    # Step 3: Validate join columns
    if on:
        if left_on or right_on:
            typer.echo("Error: Cannot use --on with --left-on/--right-on", err=True)
            raise typer.Exit(1)

    if (left_on and not right_on) or (right_on and not left_on):
        typer.echo("Error: Must specify both --left-on and --right-on", err=True)
        raise typer.Exit(1)

    if not on and not (left_on and right_on):
        typer.echo("Error: Must specify either --on or both --left-on and --right-on", err=True)
        raise typer.Exit(1)

    # Step 4: Read left file
    left_handler_result = factory.get_handler(left_path)
    if is_err(left_handler_result):
        error = unwrap_err(left_handler_result)
        typer.echo(f"{error}", err=True)
        raise typer.Exit(1)

    left_handler = unwrap(left_handler_result)

    if isinstance(left_handler, ExcelHandler):
        kwargs = {"sheet_name": left_sheet} if left_sheet else {}
        left_read_result = left_handler.read(left_path, **kwargs)
    elif isinstance(left_handler, CSVHandler):
        encoding_result = left_handler.detect_encoding(left_path)
        encoding = unwrap(encoding_result) if is_ok(encoding_result) else "utf-8"

        delimiter_result = left_handler.detect_delimiter(left_path, encoding)
        delimiter = unwrap(delimiter_result) if is_ok(delimiter_result) else ","

        left_read_result = left_handler.read(left_path, encoding=encoding, delimiter=delimiter)
    else:
        typer.echo("Unsupported handler type", err=True)
        raise typer.Exit(1)

    if is_err(left_read_result):
        error = unwrap_err(left_read_result)
        typer.echo(f"Error reading left file: {error}", err=True)
        raise typer.Exit(1)

    df_left = unwrap(left_read_result)

    # Step 5: Read right file
    right_handler_result = factory.get_handler(right_path)
    if is_err(right_handler_result):
        error = unwrap_err(right_handler_result)
        typer.echo(f"{error}", err=True)
        raise typer.Exit(1)

    right_handler = unwrap(right_handler_result)

    if isinstance(right_handler, ExcelHandler):
        kwargs = {"sheet_name": right_sheet} if right_sheet else {}
        right_read_result = right_handler.read(right_path, **kwargs)
    elif isinstance(right_handler, CSVHandler):
        encoding_result = right_handler.detect_encoding(right_path)
        encoding = unwrap(encoding_result) if is_ok(encoding_result) else "utf-8"

        delimiter_result = right_handler.detect_delimiter(right_path, encoding)
        delimiter = unwrap(delimiter_result) if is_ok(delimiter_result) else ","

        right_read_result = right_handler.read(right_path, encoding=encoding, delimiter=delimiter)
    else:
        typer.echo("Unsupported handler type", err=True)
        raise typer.Exit(1)

    if is_err(right_read_result):
        error = unwrap_err(right_read_result)
        typer.echo(f"Error reading right file: {error}", err=True)
        raise typer.Exit(1)

    df_right = unwrap(right_read_result)

    # Step 6: Handle empty files
    if df_left.empty:
        typer.echo("Left file is empty (no data rows)")
        raise typer.Exit(0)

    if df_right.empty:
        typer.echo("Right file is empty (no data rows)")
        raise typer.Exit(0)

    # Step 7: Validate join columns exist
    if on:
        left_on_cols = [on]
        right_on_cols = [on]
    else:
        left_on_cols = [c.strip() for c in left_on.split(",")]
        right_on_cols = [c.strip() for c in right_on.split(",")]

        if len(left_on_cols) != len(right_on_cols):
            typer.echo("Error: --left-on and --right-on must have the same number of columns", err=True)
            raise typer.Exit(1)

    missing_left = [c for c in left_on_cols if c not in df_left.columns]
    if missing_left:
        typer.echo(f"Error: Columns not found in left file: {', '.join(missing_left)}", err=True)
        typer.echo(f"Available columns: {', '.join(df_left.columns)}")
        raise typer.Exit(1)

    missing_right = [c for c in right_on_cols if c not in df_right.columns]
    if missing_right:
        typer.echo(f"Error: Columns not found in right file: {', '.join(missing_right)}", err=True)
        typer.echo(f"Available columns: {', '.join(df_right.columns)}")
        raise typer.Exit(1)

    # Step 8: Perform join
    try:
        if on:
            df_joined = pd.merge(
                df_left,
                df_right,
                on=on,
                how=how,
                suffixes=("_left", "_right")
            )
        else:
            df_joined = pd.merge(
                df_left,
                df_right,
                left_on=left_on_cols,
                right_on=right_on_cols,
                how=how,
                suffixes=("_left", "_right")
            )
    except Exception as e:
        typer.echo(f"Error performing join: {str(e)}", err=True)
        raise typer.Exit(1)

    joined_rows = len(df_joined)
    left_rows = len(df_left)
    right_rows = len(df_right)

    # Step 9: Display summary
    typer.echo(f"Join type: {how}")
    if on:
        typer.echo(f"On column: {on}")
    else:
        typer.echo(f"Left on: {', '.join(left_on_cols)}")
        typer.echo(f"Right on: {', '.join(right_on_cols)}")
    typer.echo(f"Left rows: {left_rows}")
    typer.echo(f"Right rows: {right_rows}")
    typer.echo(f"Joined rows: {joined_rows}")
    typer.echo("")

    # Step 10: Write output or display
    if output:
        output_path = Path(output)
        write_result = factory.write_file(df_joined, output_path)
        if is_err(write_result):
            error = unwrap_err(write_result)
            typer.echo(f"Error writing file: {error}", err=True)
            raise typer.Exit(1)
        typer.echo(f"Written to: {output}")
    else:
        # Display data
        display_table(df_joined)


# Create CLI app for this command
app = typer.Typer(help="Join two datasets based on common columns")

# Register the command
app.command()(join)
