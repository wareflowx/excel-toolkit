"""Info command implementation.

Displays metadata and information about data files (Excel, CSV).
"""

from pathlib import Path
import sys

import typer

from excel_toolkit.core import (
    HandlerFactory,
    ExcelHandler,
    CSVHandler,
    FileNotFoundError,
    UnsupportedFormatError,
    InvalidFileError,
    FileAccessError,
)
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err


def info(file_path: str, verbose: bool = False) -> None:
    """Display information about a data file.

    Shows metadata including:
    - File type and size
    - Sheet information (for Excel)
    - Encoding and delimiter (for CSV)
    - Row and column counts

    Args:
        file_path: Path to the file to analyze
        verbose: Show detailed information (default: False)

    Raises:
        typer.Exit: If file cannot be read or accessed
    """
    path = Path(file_path)
    factory = HandlerFactory()

    # Step 1: Validate file exists
    if not path.exists():
        typer.echo(f"File not found: {file_path}", err=True)
        raise typer.Exit(1)

    # Step 2: Get appropriate handler
    handler_result = factory.get_handler(path)
    if is_err(handler_result):
        error = unwrap_err(handler_result)
        typer.echo(f"{error}", err=True)
        typer.echo("\nSupported formats: .xlsx, .xls, .csv")
        raise typer.Exit(1)

    handler = unwrap(handler_result)

    # Step 3: Display basic file information
    typer.echo(f"File: {path.name}")
    typer.echo(f"Type: {_get_file_type(path)}")
    typer.echo(f"Size: {_format_size(path.stat().st_size)}")

    # Step 4: Display type-specific information
    if isinstance(handler, ExcelHandler):
        _display_excel_info(handler, path, verbose)
    elif isinstance(handler, CSVHandler):
        _display_csv_info(handler, path, verbose)


def _get_file_type(path: Path) -> str:
    """Get human-readable file type.

    Args:
        path: Path to file

    Returns:
        Human-readable file type string
    """
    suffix = path.suffix.lower()
    types = {
        ".xlsx": "Excel (modern)",
        ".xls": "Excel (legacy)",
        ".csv": "CSV",
    }
    return types.get(suffix, "Unknown")


def _format_size(bytes_size: int) -> str:
    """Format file size in human-readable format.

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted size string (e.g., "2.3 MB", "450 KB")
    """
    mb = bytes_size / (1024 * 1024)
    if mb < 1:
        kb = bytes_size / 1024
        return f"{kb:.1f} KB"
    return f"{mb:.1f} MB"


def _display_excel_info(handler: ExcelHandler, path: Path, verbose: bool) -> None:
    """Display Excel-specific information.

    Args:
        handler: ExcelHandler instance
        path: Path to Excel file
        verbose: Show detailed information
    """
    # Get sheet names
    names_result = handler.get_sheet_names(path)

    if is_err(names_result):
        error = unwrap_err(names_result)
        typer.echo(f"\nError reading sheets: {error}", err=True)
        return

    sheets = unwrap(names_result)
    typer.echo(f"\nSheets ({len(sheets)}):")

    # Get detailed info for each sheet
    info_result = handler.get_sheet_info(path)

    if is_ok(info_result):
        sheet_info = unwrap(info_result)
        for sheet_name in sheets:
            rows = sheet_info[sheet_name]["rows"]
            cols = sheet_info[sheet_name]["columns"]
            typer.echo(f"  - {sheet_name}: {rows:,} rows x {cols} columns")

            if verbose:
                # Show column names
                data_result = handler.read(path, sheet_name=sheet_name)
                if is_ok(data_result):
                    df = unwrap(data_result)
                    columns = ", ".join(df.columns.tolist())
                    typer.echo(f"    Columns: {columns}")
    else:
        # Fallback: just show sheet names
        for sheet_name in sheets:
            typer.echo(f"  - {sheet_name}")


def _display_csv_info(handler: CSVHandler, path: Path, verbose: bool) -> None:
    """Display CSV-specific information.

    Args:
        handler: CSVHandler instance
        path: Path to CSV file
        verbose: Show detailed information
    """
    # Detect encoding
    encoding_result = handler.detect_encoding(path)
    if is_ok(encoding_result):
        encoding = unwrap(encoding_result)
        typer.echo(f"\nEncoding: {encoding}")
    else:
        encoding = "Unknown"

    # Detect delimiter
    delimiter_result = handler.detect_delimiter(path, encoding if encoding != "Unknown" else "utf-8")
    if is_ok(delimiter_result):
        delimiter = unwrap(delimiter_result)
        typer.echo(f"Delimiter: {_delimiter_name(delimiter)}")
    else:
        typer.echo(f"Delimiter: comma (,)")  # Default

    # Read to get row/column count if verbose
    if verbose:
        data_result = handler.read(path, encoding=encoding if encoding != "Unknown" else "utf-8")
        if is_ok(data_result):
            df = unwrap(data_result)
            typer.echo(f"\nRows: {len(df):,}")
            typer.echo(f"Columns: {len(df.columns)}")
            typer.echo(f"Column names: {', '.join(df.columns.tolist())}")
        else:
            error = unwrap_err(data_result)
            typer.echo(f"\nError reading CSV: {error}", err=True)


def _delimiter_name(delimiter: str) -> str:
    """Get human-readable delimiter name.

    Args:
        delimiter: Delimiter character

    Returns:
        Human-readable delimiter name
    """
    names = {
        ",": "comma (,)",
        ";": "semicolon (;)",
        "\t": "tab",
        "|": "pipe (|)",
    }
    return names.get(delimiter, delimiter)


# Create CLI app for this command (can be used standalone or imported)
app = typer.Typer(help="Display information about data files")

# Register the command
app.command()(info)
