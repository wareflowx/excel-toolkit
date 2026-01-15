"""Transform command implementation.

Apply transformations to columns.
"""

from pathlib import Path
from typing import Any

import typer
import pandas as pd

from excel_toolkit.core import HandlerFactory, ExcelHandler, CSVHandler
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err
from excel_toolkit.commands.common import display_table


def transform(
    file_path: str = typer.Argument(..., help="Path to input file"),
    columns: str = typer.Option(..., "--columns", "-c", help="Columns to transform (comma-separated)"),
    operation: str | None = typer.Option(None, "--operation", "-op", help="String operation: uppercase, lowercase, titlecase, strip, replace, length"),
    multiply: str | None = typer.Option(None, "--multiply", help="Multiply by value"),
    add: str | None = typer.Option(None, "--add", help="Add value"),
    subtract: str | None = typer.Option(None, "--subtract", help="Subtract value"),
    divide: str | None = typer.Option(None, "--divide", help="Divide by value"),
    power: str | None = typer.Option(None, "--power", help="Raise to power"),
    mod: str | None = typer.Option(None, "--mod", help="Modulo value"),
    replace: str | None = typer.Option(None, "--replace", help="Replace pattern: old,new"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show preview without writing"),
    sheet: str | None = typer.Option(None, "--sheet", "-s", help="Sheet name for Excel files"),
) -> None:
    """Apply transformations to columns in a data file.

    Apply mathematical or string operations to transform column values.

    Examples:
        xl transform data.xlsx --columns "Price" --multiply "1.1" --output with-tax.xlsx
        xl transform data.csv --columns "Name" --operation "uppercase" --output upper.xlsx
        xl transform data.xlsx --columns "Description" --operation "strip" --output clean.xlsx
        xl transform sales.xlsx --columns "Amount" --add "100" --output adjusted.xlsx
    """
    path = Path(file_path)
    factory = HandlerFactory()

    # Step 1: Validate file exists
    if not path.exists():
        typer.echo(f"File not found: {file_path}", err=True)
        raise typer.Exit(1)

    # Step 2: Validate transformation options
    math_operations = {
        'multiply': multiply,
        'add': add,
        'subtract': subtract,
        'divide': divide,
        'power': power,
        'mod': mod
    }

    has_math_op = any(v is not None for v in math_operations.values())
    has_string_op = operation is not None

    if not has_math_op and not has_string_op:
        typer.echo("Error: Must specify a transformation", err=True)
        typer.echo("Math operations: --multiply, --add, --subtract, --divide, --power, --mod")
        typer.echo("String operations: --operation (uppercase, lowercase, titlecase, strip, replace, length)")
        raise typer.Exit(1)

    if has_math_op and has_string_op:
        typer.echo("Error: Cannot combine math and string operations", err=True)
        raise typer.Exit(1)

    # Validate only one math operation
    if has_math_op:
        active_math_ops = [k for k, v in math_operations.items() if v is not None]
        if len(active_math_ops) > 1:
            typer.echo(f"Error: Cannot use multiple math operations: {', '.join(active_math_ops)}", err=True)
            raise typer.Exit(1)

        math_op = active_math_ops[0]
        math_value = math_operations[math_op]

        # Validate numeric value
        try:
            numeric_value = float(math_value)
        except ValueError:
            typer.echo(f"Error: Invalid numeric value '{math_value}' for --{math_op}", err=True)
            raise typer.Exit(1)

    # Step 3: Validate string operation
    valid_string_ops = ["uppercase", "lowercase", "titlecase", "strip", "replace", "length"]
    if operation and operation not in valid_string_ops:
        typer.echo(f"Error: Invalid operation '{operation}'", err=True)
        typer.echo(f"Valid operations: {', '.join(valid_string_ops)}")
        raise typer.Exit(1)

    # Special validation for replace
    if operation == "replace" and not replace:
        typer.echo("Error: --replace is required when operation is 'replace'", err=True)
        typer.echo("Format: --replace \"old_pattern,new_pattern\"")
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

    # Step 7: Parse columns
    column_list = [c.strip() for c in columns.split(",")]
    # Validate columns exist
    missing_cols = [c for c in column_list if c not in df.columns]
    if missing_cols:
        typer.echo(f"Error: Columns not found: {', '.join(missing_cols)}", err=True)
        typer.echo(f"Available columns: {', '.join(df.columns)}")
        raise typer.Exit(1)

    # Step 8: Apply transformation
    df_transformed = df.copy()

    for col in column_list:
        if has_math_op:
            # Apply math operation
            if not pd.api.types.is_numeric_dtype(df_transformed[col]):
                typer.echo(f"Warning: Column '{col}' is not numeric, skipping math transformation", err=True)
                continue

            if math_op == "multiply":
                df_transformed[col] = df_transformed[col] * numeric_value
            elif math_op == "add":
                df_transformed[col] = df_transformed[col] + numeric_value
            elif math_op == "subtract":
                df_transformed[col] = df_transformed[col] - numeric_value
            elif math_op == "divide":
                df_transformed[col] = df_transformed[col] / numeric_value
            elif math_op == "power":
                df_transformed[col] = df_transformed[col] ** numeric_value
            elif math_op == "mod":
                df_transformed[col] = df_transformed[col] % numeric_value

        elif operation == "uppercase":
            df_transformed[col] = df_transformed[col].astype(str).str.upper()
        elif operation == "lowercase":
            df_transformed[col] = df_transformed[col].astype(str).str.lower()
        elif operation == "titlecase":
            df_transformed[col] = df_transformed[col].astype(str).str.title()
        elif operation == "strip":
            df_transformed[col] = df_transformed[col].astype(str).str.strip()
        elif operation == "replace":
            # Parse replace pattern
            if "," in replace:
                old_pattern, new_pattern = replace.split(",", 1)
                df_transformed[col] = df_transformed[col].astype(str).str.replace(old_pattern, new_pattern)
            else:
                typer.echo(f"Warning: Invalid replace pattern '{replace}', expected 'old,new'", err=True)
        elif operation == "length":
            df_transformed[col] = df_transformed[col].astype(str).str.len()

    # Step 9: Display summary
    typer.echo(f"Transformed {len(column_list)} column(s)")
    typer.echo(f"Columns: {', '.join(column_list)}")
    if has_math_op:
        typer.echo(f"Operation: {math_op} {numeric_value}")
    elif operation:
        typer.echo(f"Operation: {operation}")
    typer.echo(f"Rows: {original_count}")
    typer.echo("")

    # Step 10: Handle dry-run mode
    if dry_run:
        typer.echo("Preview of transformed data:")
        preview_rows = min(5, original_count)
        display_table(df_transformed.head(preview_rows))
        raise typer.Exit(0)

    # Step 11: Write output or display
    if output:
        output_path = Path(output)
        write_result = factory.write_file(df_transformed, output_path)
        if is_err(write_result):
            error = unwrap_err(write_result)
            typer.echo(f"Error writing file: {error}", err=True)
            raise typer.Exit(1)
        typer.echo(f"Written to: {output}")
    else:
        # Display data
        display_table(df_transformed)


# Create CLI app for this command
app = typer.Typer(help="Apply transformations to columns in a data file")

# Register the command
app.command()(transform)
