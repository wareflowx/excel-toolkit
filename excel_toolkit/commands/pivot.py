"""Pivot command implementation.

Creates pivot tables from data files.
"""

from pathlib import Path
import typer

from excel_toolkit.core import HandlerFactory
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err
from excel_toolkit.operations.pivoting import (
    validate_aggregation_function,
    validate_pivot_columns,
    parse_fill_value,
    create_pivot_table,
)
from excel_toolkit.commands.common import (
    read_data_file,
    write_or_display,
)


def pivot(
    file_path: str = typer.Argument(..., help="Path to input file"),
    rows: str = typer.Option(..., "--rows", "-r", help="Column(s) for pivot table rows"),
    columns: str | None = typer.Option(None, "--columns", "-c", help="Column(s) for pivot table columns"),
    values: str = typer.Option(..., "--values", "-v", help="Column(s) for pivot table values"),
    aggfunc: str = typer.Option("sum", "--aggfunc", "-a", help="Aggregation function (sum, mean, count, etc.)"),
    fill_value: str | None = typer.Option(None, "--fill", "-f", help="Fill value for missing cells"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("table", "--format", help="Output format (table, csv, json)"),
    sheet: str | None = typer.Option(None, "--sheet", "-s", help="Sheet name for Excel files"),
) -> None:
    """Create a pivot table from data.

    Creates multi-dimensional pivot tables with customizable aggregations.

    Examples:
        xl pivot data.xlsx --rows Category --columns Year --values Sales
        xl pivot data.csv --rows Region --columns Product --values Quantity --aggfunc sum
        xl pivot data.xlsx --rows Date --values Price --aggfunc mean
        xl pivot data.csv --rows City --columns Month --values Revenue --fill 0
    """
    # 1. Read file
    df = read_data_file(file_path, sheet)

    # 2. Parse parameters
    row_cols = [c.strip() for c in rows.split(",")]
    col_cols = [c.strip() for c in columns.split(",")] if columns else None
    value_cols = [c.strip() for c in values.split(",")]

    # 3. Validate aggregation function
    agg_result = validate_aggregation_function(aggfunc)
    if is_err(agg_result):
        error = unwrap_err(agg_result)
        typer.echo(f"Invalid aggregation function: {error}", err=True)
        raise typer.Exit(1)

    agg_func_normalized = unwrap(agg_result)

    # 4. Parse fill value
    fill_val = None
    if fill_value:
        fill_result = parse_fill_value(fill_value)
        if is_err(fill_result):
            error = unwrap_err(fill_result)
            typer.echo(f"Invalid fill value: {error}", err=True)
            raise typer.Exit(1)
        fill_val = unwrap(fill_result)

    # 5. Validate columns
    validation = validate_pivot_columns(df, row_cols, col_cols, value_cols)
    if is_err(validation):
        error = unwrap_err(validation)
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1)

    # 6. Create pivot table
    result = create_pivot_table(
        df,
        rows=row_cols,
        columns=col_cols,
        values=value_cols,
        aggfunc=agg_func_normalized,
        fill_value=fill_val
    )
    if is_err(result):
        error = unwrap_err(result)
        typer.echo(f"Error creating pivot table: {error}", err=True)
        raise typer.Exit(1)

    df_pivot = unwrap(result)

    # 7. Display summary
    typer.echo(f"Created pivot table with {len(df_pivot)} rows x {len(df_pivot.columns)} columns")
    typer.echo(f"Rows: {rows}")
    if columns:
        typer.echo(f"Columns: {columns}")
    typer.echo(f"Values: {values}")
    typer.echo(f"Aggregation: {aggfunc}")
    if fill_value:
        typer.echo(f"Fill value: {fill_value}")
    typer.echo("")

    # 8. Write or display
    factory = HandlerFactory()
    write_or_display(df_pivot, factory, output, format)


# Create CLI app for this command
app = typer.Typer(help="Create pivot tables from data")

# Register the command
app.command()(pivot)
