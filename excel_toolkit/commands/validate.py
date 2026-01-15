"""Validate command implementation.

Validates data against rules and constraints.
"""

from pathlib import Path
from typing import Any
import json
import re
from datetime import datetime

import typer
import pandas as pd
import numpy as np

from excel_toolkit.core import HandlerFactory, ExcelHandler, CSVHandler
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err, ok, err
from excel_toolkit.fp._result import Result
from excel_toolkit.commands.common import display_table


def validate(
    file_path: str = typer.Argument(..., help="Path to input file"),
    rules: str | None = typer.Option(None, "--rules", "-r", help="Validation rules (comma-separated)"),
    rules_file: str | None = typer.Option(None, "--rules-file", help="Path to JSON rules file"),
    columns: str | None = typer.Option(None, "--columns", "-c", help="Specific columns to validate"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output report file"),
    fail_fast: bool = typer.Option(False, "--fail-fast", help="Stop on first validation error"),
    sheet: str | None = typer.Option(None, "--sheet", "-s", help="Sheet name for Excel files"),
) -> None:
    """Validate data against rules and constraints.

    Supports various validation types:
    - Type checking: int, float, str, bool, datetime
    - Range validation: min:max (e.g., age:int:0-120)
    - Pattern matching: email, url, phone, regex
    - Null checking: required, optional
    - Uniqueness: unique, duplicate

    Examples:
        xl validate data.csv --rules "age:int:0-120,email:email"
        xl validate sales.xlsx --rules-file validation.json
        xl validate data.csv --columns "email,phone" --rules "email:email,phone:phone"
        xl validate data.xlsx --rules "*" --output report.json --fail-fast
    """
    path = Path(file_path)
    factory = HandlerFactory()

    # Step 1: Validate file exists
    if not path.exists():
        typer.echo(f"File not found: {file_path}", err=True)
        raise typer.Exit(1)

    # Step 2: Parse validation rules
    if not rules and not rules_file:
        typer.echo("Error: Either --rules or --rules-file must be specified", err=True)
        typer.echo("Use --rules '*' to validate all columns with basic type checking", err=True)
        raise typer.Exit(1)

    if rules and rules_file:
        typer.echo("Error: Cannot specify both --rules and --rules-file", err=True)
        raise typer.Exit(1)

    # Parse rules
    if rules:
        rules_result = _parse_rules_string(rules)
    else:
        rules_result = _parse_rules_file(rules_file)

    if is_err(rules_result):
        error_msg = unwrap_err(rules_result)
        typer.echo(f"Error parsing rules: {error_msg}", err=True)
        raise typer.Exit(1)

    validation_rules = unwrap(rules_result)

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

    # Step 5: Handle empty file
    if df.empty:
        typer.echo("File is empty (no data rows)")
        raise typer.Exit(0)

    # Step 6: Determine columns to validate
    if columns:
        column_list = [c.strip() for c in columns.split(",")]
        # Validate column names exist
        missing_cols = [c for c in column_list if c not in df.columns]
        if missing_cols:
            typer.echo(f"Error: Columns not found: {', '.join(missing_cols)}", err=True)
            typer.echo(f"Available columns: {', '.join(df.columns)}")
            raise typer.Exit(1)
    elif "*" in validation_rules:
        # Validate all columns
        column_list = list(df.columns)
    else:
        # Use columns from rules
        column_list = [col for col in validation_rules.keys() if col in df.columns]

    if not column_list:
        typer.echo("No columns to validate")
        raise typer.Exit(0)

    # Step 7: Perform validation
    all_errors = []
    all_warnings = []
    total_checked = 0

    for col in column_list:
        col_rules = validation_rules.get("*", {}) if "*" in validation_rules else validation_rules.get(col, {})

        if not col_rules:
            # Basic validation only
            col_errors, col_warnings = _validate_column_basic(df[col], col)
        else:
            col_errors, col_warnings = _validate_column_with_rules(df[col], col, col_rules)

        all_errors.extend(col_errors)
        all_warnings.extend(col_warnings)
        total_checked += 1

        # Fail fast if requested
        if fail_fast and col_errors:
            break

    # Step 8: Generate report
    total_errors = len(all_errors)
    total_warnings = len(all_warnings)

    report = {
        "file": str(path),
        "total_rows": len(df),
        "columns_checked": total_checked,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "errors": all_errors[:100],  # Limit to first 100
        "warnings": all_warnings[:100],
        "has_errors": total_errors > 0,
        "has_warnings": total_warnings > 0,
    }

    # Step 9: Display results
    if total_errors == 0 and total_warnings == 0:
        typer.echo("Validation passed!")
        typer.echo(f"Checked {total_checked} columns across {len(df)} rows")
    else:
        typer.echo(f"Validation completed with {total_errors} error(s) and {total_warnings} warning(s)")
        typer.echo(f"Checked {total_checked} columns across {len(df)} rows")
        typer.echo("")

        if total_errors > 0:
            typer.echo(f"Errors ({min(total_errors, 100)} shown):")
            for i, error in enumerate(all_errors[:20], 1):
                typer.echo(f"  {i}. {error}")
            if total_errors > 20:
                typer.echo(f"  ... and {total_errors - 20} more errors")
            typer.echo("")

        if total_warnings > 0:
            typer.echo(f"Warnings ({min(total_warnings, 100)} shown):")
            for i, warning in enumerate(all_warnings[:10], 1):
                typer.echo(f"  {i}. {warning}")
            if total_warnings > 10:
                typer.echo(f"  ... and {total_warnings - 10} more warnings")

    # Step 10: Write output if specified
    if output:
        output_path = Path(output)
        try:
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
            typer.echo(f"Report written to: {output}")
        except Exception as e:
            typer.echo(f"Error writing report: {str(e)}", err=True)
            raise typer.Exit(1)

    # Exit with error code if validation failed
    if total_errors > 0:
        raise typer.Exit(1)


def _parse_rules_string(rules_str: str) -> Result[dict, str]:
    """Parse rules from command-line string.

    Format: "column1:rule1,rule2;column2:rule3"
    Examples:
        "age:int:0-120,email:email"
        "name:required,email:email:optional"
        "*"  # Wildcard for all columns with basic validation
    """
    rules = {}

    # Handle wildcard
    if rules_str.strip() == "*":
        return ok({"*": {}})

    try:
        # Split by semicolon for multiple columns
        col_rules_list = rules_str.split(";")

        for col_rule in col_rules_list:
            # Split by first colon to get column name and its rules
            if ":" not in col_rule:
                return err(f"Invalid rule format: {col_rule}. Expected 'column:rule'")

            parts = col_rule.split(":")
            col_name = parts[0].strip()
            rule_specs = parts[1:]

            if col_name == "*":
                # Wildcard rule applies to all columns
                rules["*"] = _parse_rule_specs(rule_specs)
            else:
                rules[col_name] = _parse_rule_specs(rule_specs)

        return ok(rules)

    except Exception as e:
        return err(f"Error parsing rules: {str(e)}")


def _parse_rule_specs(rule_specs: list[str]) -> dict:
    """Parse rule specifications into a dictionary.

    Examples:
        ["int", "0-120"] -> {"type": "int", "min": 0, "max": 120}
        ["email"] -> {"type": "str", "pattern": "email"}
    """
    rule_dict = {}

    for spec in rule_specs:
        spec = spec.strip().lower()

        # Type specification
        if spec in ["int", "float", "str", "bool", "datetime"]:
            rule_dict["type"] = spec

        # Range specification
        elif "-" in spec and spec.replace("-", "").replace(".", "").isdigit():
            parts = spec.split("-")
            if len(parts) == 2:
                try:
                    rule_dict["min"] = float(parts[0])
                    rule_dict["max"] = float(parts[1])
                except ValueError:
                    pass

        # Pattern specification
        elif spec in ["email", "url", "phone"]:
            rule_dict["pattern"] = spec

        # Null specification
        elif spec in ["required", "optional"]:
            rule_dict["nullable"] = (spec == "optional")

        # Uniqueness specification
        elif spec in ["unique", "duplicate"]:
            rule_dict["unique"] = (spec == "unique")

        # Regex pattern
        elif spec.startswith("regex:"):
            rule_dict["pattern"] = spec[6:]
            rule_dict["pattern_type"] = "regex"

    return rule_dict


def _parse_rules_file(file_path: str) -> Result[dict, str]:
    """Parse rules from JSON file."""
    try:
        path = Path(file_path)
        if not path.exists():
            return err(f"Rules file not found: {file_path}")

        with open(path, "r") as f:
            rules = json.load(f)

        # Basic validation of rules structure
        if not isinstance(rules, dict):
            return err("Rules file must contain a JSON object")

        return ok(rules)

    except json.JSONDecodeError as e:
        return err(f"Invalid JSON in rules file: {str(e)}")
    except Exception as e:
        return err(f"Error reading rules file: {str(e)}")


def _validate_column_basic(series: pd.Series, col_name: str) -> tuple[list[str], list[str]]:
    """Perform basic validation on a column."""
    errors = []
    warnings = []

    # Check for null values
    null_count = series.isna().sum()
    if null_count > 0:
        warnings.append(f"Column '{col_name}': {null_count} null values ({null_count / len(series) * 100:.1f}%)")

    # Check data type consistency
    if len(series) > 0:
        # Get the dtype of non-null values
        non_null = series.dropna()
        if len(non_null) > 0:
            dtype = non_null.dtype
            # Check if string column has mixed types
            if dtype == "object":
                try:
                    # Try to convert to numeric
                    pd.to_numeric(non_null, errors="coerce")
                except:
                    pass

    return errors, warnings


def _validate_column_with_rules(series: pd.Series, col_name: str, rules: dict) -> tuple[list[str], list[str]]:
    """Validate a column against specific rules."""
    errors = []
    warnings = []

    # Null validation
    nullable = rules.get("nullable", True)  # Default: nullable

    null_count = series.isna().sum()
    if not nullable and null_count > 0:
        errors.append(f"Column '{col_name}': {null_count} null values found (column is required)")
    elif null_count > 0:
        warnings.append(f"Column '{col_name}': {null_count} null values ({null_count / len(series) * 100:.1f}%)")

    # Get non-null values for further validation
    non_null = series.dropna()

    if len(non_null) == 0:
        return errors, warnings

    # Type validation
    expected_type = rules.get("type")
    if expected_type:
        type_errors = _validate_type(non_null, col_name, expected_type)
        errors.extend(type_errors)
        # If type validation failed, skip further validations
        if type_errors:
            return errors, warnings

    # Range validation
    if "min" in rules or "max" in rules:
        range_errors = _validate_range(non_null, col_name, rules.get("min"), rules.get("max"))
        errors.extend(range_errors)

    # Pattern validation
    pattern = rules.get("pattern")
    if pattern:
        pattern_errors, pattern_warnings = _validate_pattern(non_null, col_name, pattern, rules.get("pattern_type", "name"))
        errors.extend(pattern_errors)
        warnings.extend(pattern_warnings)

    # Uniqueness validation
    if rules.get("unique"):
        unique_errors, unique_warnings = _validate_uniqueness(series, col_name)
        errors.extend(unique_errors)
        warnings.extend(unique_warnings)

    return errors, warnings


def _validate_type(series: pd.Series, col_name: str, expected_type: str) -> list[str]:
    """Validate data type of a series."""
    errors = []

    try:
        if expected_type == "int":
            # Check if all values can be converted to int
            pd.to_numeric(series, errors="coerce")
        elif expected_type == "float":
            pd.to_numeric(series, errors="coerce")
        elif expected_type == "bool":
            # Check if values are boolean-like
            for val in series.head(100):  # Sample first 100
                if val not in [True, False, 1, 0, "True", "False", "true", "false", "1", "0"]:
                    return [f"Column '{col_name}': Contains non-boolean values"]
        elif expected_type == "datetime":
            pd.to_datetime(series, errors="coerce")
    except Exception:
        errors.append(f"Column '{col_name}': Cannot validate as {expected_type} type")

    return errors


def _validate_range(series: pd.Series, col_name: str, min_val: float | None, max_val: float | None) -> list[str]:
    """Validate numeric range."""
    errors = []

    try:
        numeric_series = pd.to_numeric(series, errors="coerce")

        if min_val is not None:
            below_min = (numeric_series < min_val).sum()
            if below_min > 0:
                errors.append(f"Column '{col_name}': {below_min} values below minimum {min_val}")

        if max_val is not None:
            above_max = (numeric_series > max_val).sum()
            if above_max > 0:
                errors.append(f"Column '{col_name}': {above_max} values above maximum {max_val}")

    except Exception:
        pass  # Range validation only applies to numeric values

    return errors


def _validate_pattern(series: pd.Series, col_name: str, pattern: str, pattern_type: str) -> tuple[list[str], list[str]]:
    """Validate pattern matching."""
    errors = []
    warnings = []

    # Convert to string for pattern matching
    str_series = series.astype(str)

    if pattern_type == "regex":
        regex = pattern
    elif pattern == "email":
        regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    elif pattern == "url":
        regex = r'^https?://[^\s/$.?#].[^\s]*$'
    elif pattern == "phone":
        regex = r'^\+?[\d\s\-\(\)]+$'
    else:
        return errors, warnings

    try:
        compiled_regex = re.compile(regex)
        matches = str_series.apply(lambda x: bool(compiled_regex.match(x)))
        non_matches = (~matches).sum()

        if non_matches > 0:
            errors.append(f"Column '{col_name}': {non_matches} values don't match pattern '{pattern}'")

    except Exception:
        warnings.append(f"Column '{col_name}': Invalid regex pattern '{pattern}'")

    return errors, warnings


def _validate_uniqueness(series: pd.Series, col_name: str) -> tuple[list[str], list[str]]:
    """Validate uniqueness constraint."""
    errors = []
    warnings = []

    total_count = len(series)
    unique_count = series.nunique()
    duplicate_count = total_count - unique_count

    if duplicate_count > 0:
        errors.append(f"Column '{col_name}': {duplicate_count} duplicate values found ({unique_count} unique out of {total_count})")

    return errors, warnings


# Create CLI app for this command
app = typer.Typer(help="Validate data against rules and constraints")

# Register the command
app.command()(validate)
