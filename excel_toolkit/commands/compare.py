"""Compare command implementation.

Compare two files or sheets to identify differences.
"""

from pathlib import Path
from typing import Any

import typer
import pandas as pd

from excel_toolkit.core import HandlerFactory, ExcelHandler, CSVHandler
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err
from excel_toolkit.commands.common import display_table


def compare(
    file1: str = typer.Argument(..., help="Path to first file (baseline)"),
    file2: str = typer.Argument(..., help="Path to second file (comparison)"),
    key_columns: str | None = typer.Option(None, "--key-columns", "-k", help="Columns to use as key for matching rows (comma-separated)"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    show_diffs_only: bool = typer.Option(False, "--diffs-only", "-d", help="Show only differing rows"),
    sheet1: str | None = typer.Option(None, "--sheet1", "-s1", help="Sheet name for first file"),
    sheet2: str | None = typer.Option(None, "--sheet2", "-s2", help="Sheet name for second file"),
) -> None:
    """Compare two files or sheets to identify differences.

    Compare two datasets row by row or by key columns to identify added, deleted, and modified rows.

    Examples:
        xl compare old.xlsx new.xlsx --output differences.xlsx
        xl compare baseline.csv current.csv --key-columns "ID" --output changes.xlsx
        xl compare data1.xlsx data2.xlsx --key-columns "ID,Date" --diffs-only --output changes.xlsx
        xl compare old.xlsx new.xlsx --sheet1 "Sheet1" --sheet2 "Sheet2" --output diff.xlsx
    """
    path1 = Path(file1)
    path2 = Path(file2)
    factory = HandlerFactory()

    # Step 1: Validate files exist
    if not path1.exists():
        typer.echo(f"File not found: {file1}", err=True)
        raise typer.Exit(1)

    if not path2.exists():
        typer.echo(f"File not found: {file2}", err=True)
        raise typer.Exit(1)

    # Step 2: Get handlers
    handler1_result = factory.get_handler(path1)
    if is_err(handler1_result):
        error = unwrap_err(handler1_result)
        typer.echo(f"Error with file1: {error}", err=True)
        raise typer.Exit(1)

    handler2_result = factory.get_handler(path2)
    if is_err(handler2_result):
        error = unwrap_err(handler2_result)
        typer.echo(f"Error with file2: {error}", err=True)
        raise typer.Exit(1)

    handler1 = unwrap(handler1_result)
    handler2 = unwrap(handler2_result)

    # Step 3: Read first file
    if isinstance(handler1, ExcelHandler):
        kwargs = {"sheet_name": sheet1} if sheet1 else {}
        read_result1 = handler1.read(path1, **kwargs)
    elif isinstance(handler1, CSVHandler):
        encoding_result = handler1.detect_encoding(path1)
        encoding = unwrap(encoding_result) if is_ok(encoding_result) else "utf-8"

        delimiter_result = handler1.detect_delimiter(path1, encoding)
        delimiter = unwrap(delimiter_result) if is_ok(delimiter_result) else ","

        read_result1 = handler1.read(path1, encoding=encoding, delimiter=delimiter)
    else:
        typer.echo("Unsupported handler type for file1", err=True)
        raise typer.Exit(1)

    if is_err(read_result1):
        error = unwrap_err(read_result1)
        typer.echo(f"Error reading file1: {error}", err=True)
        raise typer.Exit(1)

    df1 = unwrap(read_result1)

    # Step 4: Read second file
    if isinstance(handler2, ExcelHandler):
        kwargs = {"sheet_name": sheet2} if sheet2 else {}
        read_result2 = handler2.read(path2, **kwargs)
    elif isinstance(handler2, CSVHandler):
        encoding_result = handler2.detect_encoding(path2)
        encoding = unwrap(encoding_result) if is_ok(encoding_result) else "utf-8"

        delimiter_result = handler2.detect_delimiter(path2, encoding)
        delimiter = unwrap(delimiter_result) if is_ok(delimiter_result) else ","

        read_result2 = handler2.read(path2, encoding=encoding, delimiter=delimiter)
    else:
        typer.echo("Unsupported handler type for file2", err=True)
        raise typer.Exit(1)

    if is_err(read_result2):
        error = unwrap_err(read_result2)
        typer.echo(f"Error reading file2: {error}", err=True)
        raise typer.Exit(1)

    df2 = unwrap(read_result2)

    # Step 5: Handle empty files
    if df1.empty and df2.empty:
        typer.echo("Both files are empty")
        raise typer.Exit(0)

    if df1.empty:
        typer.echo(f"File1 is empty, File2 has {len(df2)} rows")
        if output:
            output_path = Path(output)
            df2['_diff_status'] = 'added'
            write_result = factory.write_file(df2, output_path)
            if is_err(write_result):
                error = unwrap_err(write_result)
                typer.echo(f"Error writing file: {error}", err=True)
                raise typer.Exit(1)
            typer.echo(f"Written to: {output}")
        else:
            display_table(df2)
        raise typer.Exit(0)

    if df2.empty:
        typer.echo(f"File2 is empty, File1 has {len(df1)} rows")
        if output:
            output_path = Path(output)
            df1['_diff_status'] = 'deleted'
            write_result = factory.write_file(df1, output_path)
            if is_err(write_result):
                error = unwrap_err(write_result)
                typer.echo(f"Error writing file: {error}", err=True)
                raise typer.Exit(1)
            typer.echo(f"Written to: {output}")
        else:
            display_table(df1)
        raise typer.Exit(0)

    # Step 6: Parse key columns if specified
    if key_columns:
        key_cols = [c.strip() for c in key_columns.split(",")]

        # Validate key columns exist in both dataframes
        missing_df1 = [c for c in key_cols if c not in df1.columns]
        missing_df2 = [c for c in key_cols if c not in df2.columns]

        if missing_df1:
            typer.echo(f"Error: Key columns not found in file1: {', '.join(missing_df1)}", err=True)
            typer.echo(f"Available columns in file1: {', '.join(df1.columns)}")
            raise typer.Exit(1)

        if missing_df2:
            typer.echo(f"Error: Key columns not found in file2: {', '.join(missing_df2)}", err=True)
            typer.echo(f"Available columns in file2: {', '.join(df2.columns)}")
            raise typer.Exit(1)

        # Set key columns as index for comparison
        df1_indexed = df1.set_index(key_cols)
        df2_indexed = df2.set_index(key_cols)
    else:
        # Compare by row position
        df1_indexed = df1.copy()
        df2_indexed = df2.copy()
        # Add a temporary index column
        df1_indexed['_row_num'] = range(len(df1))
        df2_indexed['_row_num'] = range(len(df2))
        key_cols = ['_row_num']

    # Step 7: Perform comparison
    try:
        # Find rows only in df1 (deleted)
        only_df1 = df1_indexed.index.difference(df2_indexed.index)

        # Find rows only in df2 (added)
        only_df2 = df2_indexed.index.difference(df1_indexed.index)

        # Find rows in both (potentially modified)
        common_index = df1_indexed.index.intersection(df2_indexed.index)

        modified_rows = []
        if len(common_index) > 0:
            df1_common = df1_indexed.loc[common_index].sort_index()
            df2_common = df2_indexed.loc[common_index].sort_index()

            # Compare values
            for idx in common_index:
                row1 = df1_common.loc[idx]
                row2 = df2_common.loc[idx]

                # Check if values are different (ignoring NaN differences)
                values_equal = True
                for col in df1_common.columns:
                    val1 = row1[col] if col in row1 else None
                    val2 = row2[col] if col in row2 else None

                    # Handle NaN comparisons
                    if pd.isna(val1) and pd.isna(val2):
                        continue
                    elif pd.isna(val1) or pd.isna(val2):
                        values_equal = False
                        break
                    elif val1 != val2:
                        values_equal = False
                        break

                if not values_equal:
                    modified_rows.append(idx)

    except Exception as e:
        typer.echo(f"Error comparing data: {str(e)}", err=True)
        raise typer.Exit(1)

    # Step 8: Build comparison result
    result_data = []
    added_count = 0
    deleted_count = 0
    modified_count = 0

    # Added rows
    if len(only_df2) > 0:
        for idx in only_df2:
            row = df2_indexed.loc[idx].to_dict()
            row['_diff_status'] = 'added'
            result_data.append(row)
            added_count += 1

    # Deleted rows
    if len(only_df1) > 0:
        for idx in only_df1:
            row = df1_indexed.loc[idx].to_dict()
            row['_diff_status'] = 'deleted'
            result_data.append(row)
            deleted_count += 1

    # Modified rows (show both versions)
    if len(modified_rows) > 0:
        for idx in modified_rows:
            row1 = df1_indexed.loc[idx]
            row2 = df2_indexed.loc[idx]

            # Show old version
            row_old = row1.to_dict()
            row_old['_diff_status'] = 'modified (old)'
            result_data.append(row_old)

            # Show new version
            row_new = row2.to_dict()
            row_new['_diff_status'] = 'modified (new)'
            result_data.append(row_new)

            modified_count += 1

    # Create result dataframe
    if result_data:
        df_result = pd.DataFrame(result_data)

        # Reset index to make key columns regular columns again
        if key_cols != ['_row_num']:
            df_result.reset_index(inplace=True)
            # Remove the temporary _row_num column if it exists
            if '_row_num' in df_result.columns:
                df_result.drop('_row_num', axis=1, inplace=True)
        else:
            df_result.reset_index(drop=True, inplace=True)
            if '_row_num' in df_result.columns:
                df_result.drop('_row_num', axis=1, inplace=True)

        # Reorder columns to put _diff_status first
        if '_diff_status' in df_result.columns:
            cols = ['_diff_status'] + [c for c in df_result.columns if c != '_diff_status']
            df_result = df_result[cols]
    else:
        # No differences found - create empty dataframe with columns from df1
        df_result = pd.DataFrame(columns=list(df1.columns) + ['_diff_status'])

    # Step 9: Display summary
    typer.echo(f"File1 ({file1}): {len(df1)} rows")
    typer.echo(f"File2 ({file2}): {len(df2)} rows")
    typer.echo("")
    typer.echo(f"Added rows: {added_count}")
    typer.echo(f"Deleted rows: {deleted_count}")
    typer.echo(f"Modified rows: {modified_count}")
    total_diffs = added_count + deleted_count + modified_count
    typer.echo(f"Total differences: {total_diffs}")
    typer.echo("")

    if total_diffs == 0:
        typer.echo("No differences found - files are identical")
        raise typer.Exit(0)

    # Step 10: Filter if diffs only requested
    if show_diffs_only:
        df_result = df_result[df_result['_diff_status'].notna()]
        if df_result.empty:
            typer.echo("No differences to display")
            raise typer.Exit(0)

    # Step 11: Write output or display
    if output:
        output_path = Path(output)
        write_result = factory.write_file(df_result, output_path)
        if is_err(write_result):
            error = unwrap_err(write_result)
            typer.echo(f"Error writing file: {error}", err=True)
            raise typer.Exit(1)
        typer.echo(f"Written to: {output}")
    else:
        # Display data
        display_table(df_result)


# Create CLI app for this command
app = typer.Typer(help="Compare two files or sheets")

# Register the command
app.command()(compare)
