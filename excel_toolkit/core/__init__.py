"""Core layer for file I/O operations.

This module provides the foundation for reading and writing data files.
It uses Result types for explicit error handling and supports multiple
file formats (Excel, CSV).

Example:
    >>> from excel_toolkit.core import HandlerFactory
    >>> from pathlib import Path
    >>> from excel_toolkit.fp import is_ok, unwrap
    >>>
    >>> factory = HandlerFactory()
    >>> result = factory.read_file(Path("data.xlsx"))
    >>>
    >>> if is_ok(result):
    ...     df = unwrap(result)
    ...     print(f"Read {len(df)} rows")
"""

# Public API - Handlers
# Public API - Constants
from excel_toolkit.core.const import (
    DEFAULT_CSV_DELIMITER,
    DEFAULT_CSV_ENCODING,
    DEFAULT_SHEET_NAME,
    MAX_FILE_SIZE_MB,
    SUPPORTED_READ_FORMATS,
    SUPPORTED_WRITE_FORMATS,
    WARNING_FILE_SIZE_MB,
)

# Public API - Exceptions
from excel_toolkit.core.exceptions import (
    EncodingError,
    FileAccessError,
    FileHandlerError,
    FileNotFoundError,
    FileSizeError,
    InvalidFileError,
    UnsupportedFormatError,
)
from excel_toolkit.core.file_handlers import (
    CSVHandler,
    ExcelHandler,
    HandlerFactory,
)

__all__ = [
    # Handlers
    "ExcelHandler",
    "CSVHandler",
    "HandlerFactory",
    # Exceptions
    "FileHandlerError",
    "FileNotFoundError",
    "FileAccessError",
    "UnsupportedFormatError",
    "InvalidFileError",
    "FileSizeError",
    "EncodingError",
    # Constants
    "SUPPORTED_READ_FORMATS",
    "SUPPORTED_WRITE_FORMATS",
    "DEFAULT_SHEET_NAME",
    "DEFAULT_CSV_ENCODING",
    "DEFAULT_CSV_DELIMITER",
    "MAX_FILE_SIZE_MB",
    "WARNING_FILE_SIZE_MB",
]
