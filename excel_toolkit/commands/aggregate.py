"""Aggregate command implementation.

Perform custom aggregations on grouped data.
"""

from pathlib import Path
import typer

from excel_toolkit.core import HandlerFactory
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err
from excel_toolkit.operations.aggregating import (
    parse_aggregation_specs,
    validate_aggregation_columns,
    aggregate_groups,
)
from excel_toolkit.commands.common import (
    read_data_file,
    write_or_display,
)


def aggregate(
    file_path: str = typer.Argument(..., help="Path to input file"),
    group: str | None = typer.Option(None, "--group", "-g", help="Columns to group by (comma-separated)"),
    functions: str | None = typer.Option(None, "--functions", "-f", help="Aggregations: column:func1,func2 (comma-separated)"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show preview without writing"),
    sheet: str | None = typer.Option(None, "--sheet", "-s", help="Sheet name for Excel files"),
) -> None:
    """Perform custom aggregations on grouped data.

    Group by specified columns and apply multiple aggregation functions to value columns.
    Multiple functions can be applied to the same column by specifying the column multiple times.
    Supported functions: sum, mean, avg, median, min, max, count, std, var, first, last.

    Examples:
        xl aggregate sales.xlsx --group "Region" --functions "Revenue:sum,Revenue:mean" --output summary.xlsx
        xl aggregate data.csv --group "Category" --functions "Sales:sum,Sales:min,Sales:max,Profit:mean" --output stats.xlsx
        xl aggregate transactions.xlsx --group "Date,Type" --functions "Amount:sum,Amount:count,Quantity:mean" --output daily.xlsx
    """
    # 1. Validate parameters
    if not group:
        typer.echo("Error: Must specify --group columns", err=True)
        raise typer.Exit(1)

    if not functions:
        typer.echo("Error: Must specify --functions", err=True)
        typer.echo("Format: column:func1,func2 (e.g., 'Amount:sum,mean')", err=True)
        typer.echo("Supported functions: sum, mean, avg, median, min, max, count, std, var, first, last")
        raise typer.Exit(1)

    # 2. Read file
    df = read_data_file(file_path, sheet)

    # 3. Parse aggregation specifications
    parse_result = parse_aggregation_specs(functions)
    if is_err(parse_result):
        error = unwrap_err(parse_result)
        typer.echo(f"Error parsing aggregation specifications: {error}", err=True)
        raise typer.Exit(1)

    agg_specs = unwrap(parse_result)

    # 4. Parse group columns
    group_cols = [c.strip() for c in group.split(",")]

    # 5. Validate columns
    validation = validate_aggregation_columns(df, group_cols, list(agg_specs.keys()))
    if is_err(validation):
        error = unwrap_err(validation)
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1)

    # 6. Aggregate
    result = aggregate_groups(df, group_cols, agg_specs)
    if is_err(result):
        error = unwrap_err(result)
        typer.echo(f"Error aggregating data: {error}", err=True)
        raise typer.Exit(1)

    df_agg = unwrap(result)

    # 7. Handle dry-run
    if dry_run:
        typer.echo(f"Would aggregate {len(df)} rows into {len(df_agg)} groups")
        typer.echo(f"Group by: {group}")
        typer.echo(f"Aggregations: {functions}")
        typer.echo("")
        if len(df_agg) > 0:
            from excel_toolkit.commands.common import display_table
            preview_rows = min(5, len(df_agg))
            typer.echo("Preview of aggregated data:")
            display_table(df_agg.head(preview_rows))
        raise typer.Exit(0)

    # 8. Display summary
    typer.echo(f"Aggregated {len(df)} rows into {len(df_agg)} groups")
    typer.echo(f"Group by: {group}")
    typer.echo(f"Aggregations: {functions}")
    typer.echo("")

    # 9. Write or display
    factory = HandlerFactory()
    write_or_display(df_agg, factory, output, "table")


# Create CLI app for this command
app = typer.Typer(help="Perform custom aggregations on grouped data")

# Register the command
app.command()(aggregate)
