"""Validate command implementation.

Validates data quality against various rules.
"""

import pandas as pd
import typer

from excel_toolkit.commands.common import read_data_file
from excel_toolkit.fp import is_err, unwrap, unwrap_err
from excel_toolkit.operations.validation import (
    ValidationReport,
    validate_dataframe,
)


def validate(
    file_path: str = typer.Argument(..., help="Path to input file"),
    rules: str | None = typer.Option(
        None,
        "--rules",
        help="Validation rules (format: col:type or col:type:min-max or col:pattern or col:required or col:unique)",
    ),
    rules_file: str | None = typer.Option(
        None, "--rules-file", help="JSON file with validation rules"
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="Output file for validation report"
    ),
    columns: str | None = typer.Option(
        None, "--columns", "-c", help="Comma-separated columns to check"
    ),
    types: str | None = typer.Option(
        None, "--types", "-t", help="Type checks (format: col:type,col:type)"
    ),
    range: str | None = typer.Option(
        None, "--range", "-r", help="Range check (format: col:min:max)"
    ),
    unique: str | None = typer.Option(None, "--unique", "-u", help="Check uniqueness of column(s)"),
    null_threshold: float | None = typer.Option(
        None, "--null-threshold", help="Max null percentage (0-1)"
    ),
    min_value: float | None = typer.Option(None, "--min", help="Minimum value for range check"),
    max_value: float | None = typer.Option(None, "--max", help="Maximum value for range check"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed validation info"),
    fail_fast: bool = typer.Option(False, "--fail-fast", help="Stop on first validation failure"),
    sheet: str | None = typer.Option(None, "--sheet", "-s", help="Sheet name for Excel files"),
) -> None:
    """Validate data quality against various rules.

    Performs comprehensive validation checks:
    - Column existence: Verify columns exist
    - Type checking: Validate data types (int, float, str, bool, datetime, numeric)
    - Range validation: Ensure values within specified range
    - Uniqueness: Check for duplicate values
    - Null threshold: Verify null values don't exceed threshold

    Examples:
        xl validate data.xlsx --columns id,name,email
        xl validate data.csv --types "age:int,salary:float"
        xl validate data.xlsx --range "age:0:120"
        xl validate data.csv --unique id --null-threshold 0.1
        xl validate data.xlsx --columns id --types "id:int" --unique id --verbose
    """
    # 1. Read file
    df = read_data_file(file_path, sheet)

    # 1.1 Handle empty file
    if df.empty:
        typer.echo("File is empty (no data rows)")
        raise typer.Exit(0)

    # 2. Parse --rules parameter if provided
    email_columns = []  # Track email columns for pattern validation

    if rules:
        for rule_spec in rules.split(","):
            parts = rule_spec.strip().split(":")
            col = parts[0]

            # Handle wildcard "*"
            if col == "*":
                # Apply rule to all columns
                if len(parts) == 1:
                    # Just "*" - validate all columns exist
                    if columns is None:
                        columns = ",".join(df.columns)
                    else:
                        columns += f",{','.join(df.columns)}"
                elif len(parts) == 2:
                    rule_type = parts[1]
                    # Check all columns
                    for column in df.columns:
                        if rule_type == "required":
                            # Required field rule (no nulls allowed)
                            if columns is None:
                                columns = column
                            else:
                                columns += f",{column}"
                            if null_threshold is None:
                                null_threshold = 0.0
                        elif rule_type == "unique":
                            # Uniqueness constraint (can't apply to all columns at once)
                            pass  # Skip
                        elif rule_type == "email":
                            # Email pattern validation
                            email_columns.append(column)
                            if types is None:
                                types = f"{column}:str"
                            else:
                                types += f",{column}:str"
                        else:
                            # Type checking
                            if types is None:
                                types = f"{column}:{rule_type}"
                            else:
                                types += f",{column}:{rule_type}"
                continue

            if len(parts) == 2:
                # Format: col:type or col:required or col:unique
                rule_type = parts[1]

                if rule_type == "required":
                    # Required field rule (no nulls allowed)
                    if columns is None:
                        columns = col
                    else:
                        columns += f",{col}"
                    if null_threshold is None:
                        null_threshold = 0.0
                elif rule_type == "unique":
                    # Uniqueness constraint
                    if unique is None:
                        unique = col
                    else:
                        unique += f",{col}"
                elif rule_type == "email":
                    # Email pattern validation - track for post-processing
                    email_columns.append(col)
                    if types is None:
                        types = f"{col}:str"
                    else:
                        types += f",{col}:str"
                else:
                    # Type checking
                    if types is None:
                        types = f"{col}:{rule_type}"
                    else:
                        types += f",{col}:{rule_type}"

            elif len(parts) == 3:
                # Format: col:type:range or col:min:max
                middle = parts[1]

                # Check if middle is a type or part of range
                try:
                    # Try to parse as number
                    float(middle)
                    # It's a number, so format is col:min:max
                    if range is None:
                        range = f"{col}:{middle}:{parts[2]}"
                except ValueError:
                    # It's not a number, so format is col:type:min-max
                    rule_type = middle
                    range_parts = parts[2].split("-")
                    if len(range_parts) == 2:
                        min_val = range_parts[0]
                        max_val = range_parts[1]
                        # Add type rule
                        if types is None:
                            types = f"{col}:{rule_type}"
                        else:
                            types += f",{col}:{rule_type}"
                        # Add range rule
                        if range is None:
                            range = f"{col}:{min_val}:{max_val}"

    # 2.1 Parse --rules-file parameter if provided
    if rules_file:
        import json
        from pathlib import Path

        rules_path = Path(rules_file)
        if not rules_path.exists():
            typer.echo(f"Error: Rules file not found: {rules_file}", err=True)
            raise typer.Exit(1)

        try:
            with open(rules_path, "r") as f:
                file_rules = json.load(f)

            # Parse rules from JSON file
            for rule in file_rules:
                rule_type = rule.get("type")
                if rule_type == "column_type":
                    column_types = rule.get("column_types", {})
                    for col, col_type in column_types.items():
                        if types is None:
                            types = f"{col}:{col_type}"
                        else:
                            types += f",{col}:{col_type}"
                elif rule_type == "value_range":
                    col = rule.get("column")
                    min_val = rule.get("min")
                    max_val = rule.get("max")
                    if range is None:
                        range = f"{col}:{min_val}:{max_val}"
                elif rule_type == "unique":
                    cols = rule.get("columns", [])
                    if unique is None:
                        unique = ",".join(cols)
                    else:
                        unique += f",{','.join(cols)}"
                elif rule_type == "null_threshold":
                    threshold = rule.get("threshold")
                    cols = rule.get("columns")
                    if null_threshold is None:
                        null_threshold = threshold
                    if cols and columns is None:
                        columns = ",".join(cols)
        except Exception as e:
            typer.echo(f"Error reading rules file: {e}", err=True)
            raise typer.Exit(1)

    # 3. Build validation rules
    rules_list = []

    # Column existence rule
    if columns:
        col_list = [c.strip() for c in columns.split(",")]
        rules_list.append({"type": "column_exists", "columns": col_list})

    # Type validation rule
    if types:
        type_dict = {}
        for spec in types.split(","):
            col, col_type = spec.split(":")
            type_dict[col.strip()] = col_type.strip()
        rules_list.append({"type": "column_type", "column_types": type_dict})

    # Range validation rule
    if range or (min_value is not None or max_value is not None):
        if range:
            # Parse range spec "col:min:max"
            col_name, min_val, max_val = range.split(":")
            range_col = col_name.strip()
            range_min = float(min_val)
            range_max = float(max_val)
        else:
            # Use --min and --max options (need a column)
            if not columns:
                typer.echo("Error: Must specify --columns with --min/--max", err=True)
                raise typer.Exit(1)
            range_col = columns.split(",")[0].strip()
            range_min = min_value
            range_max = max_value

        rules_list.append(
            {"type": "value_range", "column": range_col, "min": range_min, "max": range_max}
        )

    # Uniqueness rule
    if unique:
        unique_cols = [c.strip() for c in unique.split(",")]
        rules_list.append({"type": "unique", "columns": unique_cols})

    # Null threshold rule
    if null_threshold is not None:
        cols_to_check = [c.strip() for c in columns.split(",")] if columns else None
        rules_list.append(
            {"type": "null_threshold", "columns": cols_to_check, "threshold": null_threshold}
        )

    # If no rules specified, check all columns exist and have no nulls
    if not rules_list:
        typer.echo(
            "Error: No validation rules specified. Use --rules, --columns, --types, --range, --unique, or --null-threshold",
            err=True,
        )
        typer.echo("Run 'xl validate --help' for examples")
        raise typer.Exit(1)

    # 4. Run validation
    result = validate_dataframe(df, rules_list)
    if is_err(result):
        error = unwrap_err(result)
        typer.echo(f"Validation error: {error}", err=True)
        raise typer.Exit(1)

    report: ValidationReport = unwrap(result)

    # 4.5 Validate email patterns if specified
    if email_columns:
        import re

        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

        for email_col in email_columns:
            if email_col not in df.columns:
                continue

            invalid_emails = []
            for idx, value in df[email_col].items():
                if pd.notna(value):
                    value_str = str(value).strip()
                    if value_str and not email_pattern.match(value_str):
                        invalid_emails.append({"row": idx, "value": value_str})

            if invalid_emails:
                # Add email pattern errors to the report
                for invalid_email in invalid_emails[:10]:  # Limit to 10 errors
                    error = {
                        "rule": len(report.errors) + len(report.warnings),
                        "type": "pattern_mismatch",
                        "column": email_col,
                        "error": f"Invalid email format at row {invalid_email['row']}: '{invalid_email['value']}'",
                    }
                    report.errors.append(error)

                if len(invalid_emails) > 10:
                    report.errors.append(
                        {
                            "rule": len(report.errors) + len(report.warnings),
                            "type": "pattern_mismatch",
                            "column": email_col,
                            "error": f"... and {len(invalid_emails) - 10} more invalid emails",
                        }
                    )

                # Update failed count
                report.failed += len(invalid_emails)

    # 5. Write to output file if specified
    if output:
        import json
        from pathlib import Path

        output_path = Path(output)
        report_dict = {
            "file": file_path,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "passed": report.passed,
            "failed": report.failed,
            "total_errors": len(report.errors),
            "total_warnings": len(report.warnings),
            "errors": report.errors,
            "warnings": report.warnings,
        }
        try:
            with open(output_path, "w") as f:
                json.dump(report_dict, f, indent=2)
            typer.echo(f"Report written to: {output}")
        except Exception as e:
            typer.echo(f"Error writing report: {e}", err=True)
            raise typer.Exit(1)

    # 6. Display results
    _display_validation_report(report, verbose)

    # 7. Exit with error if failures
    # Only exit with code 1 if there are actual critical errors (not just type mismatches)
    # Type mismatches (column_type) are considered warnings for data quality validation
    critical_errors = [
        e
        for e in report.errors
        if e.get("type") != "column_type"  # Filter out type mismatches, keep pattern errors
    ]
    if critical_errors:
        raise typer.Exit(1)


def _display_validation_report(report: ValidationReport, verbose: bool) -> None:
    """Display validation report in user-friendly format.

    Args:
        report: Validation report from validate_dataframe
        verbose: Whether to show detailed warnings
    """
    # Separate type mismatches (warnings) from critical errors
    type_mismatches = [e for e in report.errors if e.get("type") == "column_type"]
    critical_errors = [e for e in report.errors if e.get("type") != "column_type"]

    # Summary
    typer.echo(f"✅ Passed: {report.passed}")
    if report.failed > 0:
        typer.echo(f"❌ Failed: {report.failed}", err=True)
    else:
        typer.echo("❌ Failed: 0")

    typer.echo("")

    # Critical errors
    if critical_errors:
        typer.echo("Errors:", err=True)
        for i, error in enumerate(critical_errors, 1):
            rule_num = error.get("rule", "?")
            error_type = error.get("type", "unknown")
            error_msg = error.get("error", str(error))
            typer.echo(f"  {i}. Rule #{rule_num} ({error_type}): {error_msg}", err=True)
        typer.echo("")

    # Warnings (type mismatches and other warnings)
    all_warnings = type_mismatches + report.warnings
    if all_warnings:
        typer.echo("Warnings:")
        for i, warning in enumerate(all_warnings, 1):
            if isinstance(warning, dict):
                rule_num = warning.get("rule", "?")
                error_type = warning.get("type", "unknown")
                error_msg = warning.get("error", str(warning))
                typer.echo(f"  {i}. Rule #{rule_num} ({error_type}): {error_msg}")
            else:
                col = warning.get("column", "?")
                null_count = warning.get("null_count", 0)
                null_percent = warning.get("null_percent", 0.0)
                typer.echo(f"  {i}. Column '{col}': {null_count} nulls ({null_percent:.1%})")
        typer.echo("")

    # Legacy warnings (only if verbose and no type mismatches)
    if not type_mismatches and report.warnings and verbose:
        for i, warning in enumerate(report.warnings, 1):
            col = warning.get("column", "?")
            null_count = warning.get("null_count", 0)
            null_percent = warning.get("null_percent", 0.0)
            typer.echo(f"  {i}. Column '{col}': {null_count} nulls ({null_percent:.1%})")
            col = warning.get("column", "?")
            null_count = warning.get("null_count", 0)
            null_percent = warning.get("null_percent", 0.0)
            typer.echo(f"  {i}. Column '{col}': {null_count} nulls ({null_percent:.1%})")
        typer.echo("")


# Create CLI app for this command
app = typer.Typer(help="Validate data quality")

# Register the command
app.command()(validate)
