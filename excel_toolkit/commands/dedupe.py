"""Dedupe command implementation.

Remove duplicate rows from a dataset.
"""

from pathlib import Path

import typer
import pandas as pd

from excel_toolkit.core import HandlerFactory
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err
from excel_toolkit.operations.cleaning import remove_duplicates
from excel_toolkit.commands.common import (
    read_data_file,
    write_or_display,
    display_table,
)


def dedupe(
    file_path: str = typer.Argument(..., help="Path to input file"),
    by: str | None = typer.Option(None, "--by", "-b", help="Columns to use for deduplication (comma-separated)"),
    keep: str = typer.Option("first", "--keep", "-k", help="Which duplicate to keep: first, last, or none"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show preview without writing"),
    sheet: str | None = typer.Option(None, "--sheet", "-s", help="Sheet name for Excel files"),
) -> None:
    """Remove duplicate rows from a data file.

    Remove duplicates based on all columns or specific key columns.
    Control which occurrence to keep (first, last) or remove all duplicates.

    Examples:
        xl dedupe data.xlsx --by "email" --keep first --output unique.xlsx
        xl dedupe data.csv --keep last --output latest.xlsx
        xl dedupe contacts.xlsx --output clean.xlsx
    """
    # 1. Validate keep option
    valid_keep_values = ["first", "last", "none"]
    if keep not in valid_keep_values:
        typer.echo(f"Error: Invalid keep value '{keep}'", err=True)
        typer.echo(f"Valid values: {', '.join(valid_keep_values)}")
        raise typer.Exit(1)

    # 2. Map "none" to False for pandas
    keep_param = False if keep == "none" else keep

    # 3. Read file
    df = read_data_file(file_path, sheet)
    original_count = len(df)

    # 4. Handle empty file
    if df.empty:
        typer.echo("File is empty (no data rows)")
        raise typer.Exit(0)

    # 5. Parse columns for deduplication
    subset = None
    if by:
        subset = [c.strip() for c in by.split(",")]
        # Validate columns exist
        missing_cols = [c for c in subset if c not in df.columns]
        if missing_cols:
            typer.echo(f"Error: Columns not found: {', '.join(missing_cols)}", err=True)
            typer.echo(f"Available columns: {', '.join(df.columns)}")
            raise typer.Exit(1)

    # 6. Count duplicates before removal
    duplicated_mask = df.duplicated(subset=subset, keep=keep_param)
    duplicate_count = duplicated_mask.sum()

    if duplicate_count == 0:
        typer.echo("No duplicates found")
        if not dry_run and not output:
            display_table(df)
        raise typer.Exit(0)

    # 7. Remove duplicates using operation
    result = remove_duplicates(df, subset=subset, keep=keep_param)

    if is_err(result):
        error = unwrap_err(result)
        typer.echo(f"Error removing duplicates: {error}", err=True)
        raise typer.Exit(1)

    df_dedupe = unwrap(result)
    deduped_count = len(df_dedupe)
    removed_count = original_count - deduped_count

    # 8. Display summary
    typer.echo(f"Original rows: {original_count}")
    typer.echo(f"Duplicate rows found: {duplicate_count}")
    typer.echo(f"Rows removed: {removed_count}")
    typer.echo(f"Remaining rows: {deduped_count}")
    if subset:
        typer.echo(f"Key columns: {', '.join(subset)}")
    else:
        typer.echo("Key columns: all columns")
    typer.echo(f"Keep strategy: {keep}")
    typer.echo("")

    # 9. Handle dry-run mode
    if dry_run:
        typer.echo("Preview of deduplicated data:")
        preview_rows = min(5, deduped_count)
        display_table(df_dedupe.head(preview_rows))

        if removed_count > 0:
            typer.echo("")
            typer.echo("Preview of removed duplicate rows:")
            removed_rows = min(5, removed_count)
            if keep == "none":
                # Show all duplicate rows (both first and subsequent occurrences)
                all_dupes = df[df.duplicated(subset=subset, keep=False)]
                display_table(all_dupes.head(removed_rows))
            else:
                # Show only the rows that were removed
                display_table(df[duplicated_mask].head(removed_rows))
        raise typer.Exit(0)

    # 10. Write or display
    factory = HandlerFactory()
    write_or_display(df_dedupe, factory, output, "table")


# Create CLI app for this command
app = typer.Typer(help="Remove duplicate rows from a data file")

# Register the command
app.command()(dedupe)
