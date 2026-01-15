"""File handlers for reading and writing data files.

This module provides handlers for different file formats (Excel, CSV).
All handlers follow the same interface and return Result types for
explicit error handling.
"""

from pathlib import Path
from typing import Any, Callable
import sys

from excel_toolkit.fp import ok, err, is_ok, unwrap, is_err
from excel_toolkit.fp._result import Result
from excel_toolkit.core.const import (
    SUPPORTED_READ_FORMATS,
    SUPPORTED_WRITE_FORMATS,
    DEFAULT_SHEET_NAME,
    DEFAULT_CSV_ENCODING,
    DEFAULT_CSV_DELIMITER,
    DEFAULT_EXCEL_ENGINE,
    MAX_FILE_SIZE_MB,
    WARNING_FILE_SIZE_MB,
    ENCODING_DETECTION_ORDER,
    DELIMITER_CANDIDATES,
)
from excel_toolkit.core.exceptions import (
    FileHandlerError,
    FileNotFoundError,
    FileAccessError,
    UnsupportedFormatError,
    InvalidFileError,
    FileSizeError,
    EncodingError,
)

# Import pandas with lazy loading pattern
try:
    import pandas as pd
except ImportError:
    pd = None  # type: ignore


class ExcelHandler:
    """Handle Excel file I/O operations (.xlsx, .xls).

    Provides methods for reading and writing Excel files with proper
    error handling using Result types.
    """

    def can_handle(self, path: Path) -> bool:
        """Check if this handler can process the given file.

        Args:
            path: Path to file

        Returns:
            True if file has .xlsx or .xls extension
        """
        return path.suffix.lower() in [".xlsx", ".xls"]

    def read(
        self,
        path: Path,
        sheet_name: str | int | None = 0,
        header: int | None = 0,
        **kwargs: Any,
    ) -> Result["pd.DataFrame", FileHandlerError]:
        """Read Excel file into DataFrame.

        Args:
            path: Path to Excel file
            sheet_name: Sheet name (str), index (int), or None for all sheets
            header: Row number for column headers (0 for first row)
            **kwargs: Additional pandas read_excel parameters

        Returns:
            Result[DataFrame, FileHandlerError]
            Ok(DataFrame) if successful, Err(FileHandlerError) if failed

        Examples:
            >>> handler = ExcelHandler()
            >>> result = handler.read(Path("data.xlsx"))
            >>> if is_ok(result):
            ...     df = unwrap(result)
        """
        if pd is None:
            return err(FileHandlerError("pandas is not installed"))

        # Validate file exists
        if not path.exists():
            return err(FileNotFoundError(f"File not found: {path}"))

        # Validate format
        if not self.can_handle(path):
            return err(UnsupportedFormatError(f"Unsupported format: {path.suffix}"))

        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            return err(FileSizeError(f"File too large: {file_size_mb:.1f}MB (max: {MAX_FILE_SIZE_MB}MB)"))

        if file_size_mb > WARNING_FILE_SIZE_MB:
            print(f"Warning: Large file ({file_size_mb:.1f}MB)", file=sys.stderr)

        # Select engine based on extension
        engine = "xlrd" if path.suffix.lower() == ".xls" else DEFAULT_EXCEL_ENGINE

        # Try reading
        try:
            df = pd.read_excel(path, sheet_name=sheet_name, header=header, engine=engine, **kwargs)
            return ok(df)
        except PermissionError as e:
            return err(FileAccessError(f"Permission denied: {path} - {str(e)}"))
        except Exception as e:
            error_msg = str(e)
            if "Permission" in error_msg or "locked" in error_msg.lower():
                return err(FileAccessError(f"File access error: {error_msg}"))
            return err(InvalidFileError(f"Failed to read Excel file: {error_msg}"))

    def read_all_sheets(self, path: Path, **kwargs: Any) -> Result[dict[str, "pd.DataFrame"], FileHandlerError]:
        """Read all sheets from Excel file.

        Args:
            path: Path to Excel file
            **kwargs: Additional pandas read_excel parameters

        Returns:
            Result[dict[str, DataFrame], FileHandlerError]
            Dictionary mapping sheet names to DataFrames
        """
        if pd is None:
            return err(FileHandlerError("pandas is not installed"))

        # Validate file exists
        if not path.exists():
            return err(FileNotFoundError(f"File not found: {path}"))

        # Validate format
        if not self.can_handle(path):
            return err(UnsupportedFormatError(f"Unsupported format: {path.suffix}"))

        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            return err(FileSizeError(f"File too large: {file_size_mb:.1f}MB (max: {MAX_FILE_SIZE_MB}MB)"))

        # Try reading all sheets
        try:
            sheets_dict = pd.read_excel(path, sheet_name=None, engine=DEFAULT_EXCEL_ENGINE, **kwargs)
            return ok(sheets_dict)  # type: ignore
        except PermissionError as e:
            return err(FileAccessError(f"Permission denied: {path} - {str(e)}"))
        except Exception as e:
            return err(InvalidFileError(f"Failed to read Excel file: {str(e)}"))

    def write(
        self,
        df: "pd.DataFrame",
        path: Path,
        sheet_name: str = DEFAULT_SHEET_NAME,
        index: bool = False,
        **kwargs: Any,
    ) -> Result[None, FileHandlerError]:
        """Write DataFrame to Excel file.

        Args:
            df: DataFrame to write
            path: Output file path
            sheet_name: Name of sheet to create
            index: Whether to write row indices
            **kwargs: Additional pandas to_excel parameters

        Returns:
            Result[None, FileHandlerError]
            Ok(None) if successful, Err(FileHandlerError) if failed
        """
        if pd is None:
            return err(FileHandlerError("pandas is not installed"))

        # Validate format
        if not self.can_handle(path):
            return err(UnsupportedFormatError(f"Unsupported format: {path.suffix}"))

        # Check if parent directory exists
        if path.parent != Path(".") and not path.parent.exists():
            return err(FileNotFoundError(f"Directory not found: {path.parent}"))

        # Try writing
        try:
            df.to_excel(path, sheet_name=sheet_name, index=index, engine=DEFAULT_EXCEL_ENGINE, **kwargs)
            return ok(None)
        except PermissionError as e:
            return err(FileAccessError(f"Permission denied: {path} - {str(e)}"))
        except Exception as e:
            return err(FileHandlerError(f"Failed to write Excel file: {str(e)}"))

    def get_sheet_names(self, path: Path) -> Result[list[str], FileHandlerError]:
        """Get list of sheet names in Excel file.

        Args:
            path: Path to Excel file

        Returns:
            Result[list[str], FileHandlerError]
            List of sheet names if successful
        """
        if pd is None:
            return err(FileHandlerError("pandas is not installed"))

        # Validate file exists
        if not path.exists():
            return err(FileNotFoundError(f"File not found: {path}"))

        # Validate format
        if not self.can_handle(path):
            return err(UnsupportedFormatError(f"Unsupported format: {path.suffix}"))

        # Try reading sheet names
        try:
            xl_file = pd.ExcelFile(path, engine=DEFAULT_EXCEL_ENGINE)
            return ok(xl_file.sheet_names)
        except PermissionError as e:
            return err(FileAccessError(f"Permission denied: {path} - {str(e)}"))
        except Exception as e:
            return err(InvalidFileError(f"Failed to read sheet names: {str(e)}"))

    def get_sheet_info(self, path: Path) -> Result[dict[str, dict[str, int]], FileHandlerError]:
        """Get metadata about all sheets in Excel file.

        Args:
            path: Path to Excel file

        Returns:
            Result[dict, FileHandlerError]
            Dictionary mapping sheet names to metadata (rows, columns)
            Example: {"Sheet1": {"rows": 100, "columns": 5}}
        """
        sheets_result = self.read_all_sheets(path)
        if is_err(sheets_result):
            return sheets_result  # type: ignore

        sheets_dict = unwrap(sheets_result)
        info = {}
        for sheet_name, df in sheets_dict.items():
            info[sheet_name] = {"rows": len(df), "columns": len(df.columns)}

        return ok(info)


class CSVHandler:
    """Handle CSV file I/O operations.

    Provides methods for reading and writing CSV files with automatic
    encoding and delimiter detection.
    """

    def can_handle(self, path: Path) -> bool:
        """Check if this handler can process the given file.

        Args:
            path: Path to file

        Returns:
            True if file has .csv extension
        """
        return path.suffix.lower() == ".csv"

    def read(
        self,
        path: Path,
        encoding: str = DEFAULT_CSV_ENCODING,
        delimiter: str = DEFAULT_CSV_DELIMITER,
        header: int | None = 0,
        **kwargs: Any,
    ) -> Result["pd.DataFrame", FileHandlerError]:
        """Read CSV file into DataFrame.

        Args:
            path: Path to CSV file
            encoding: File encoding (default: utf-8)
            delimiter: Column delimiter (default: comma)
            header: Row number for column headers (0 for first row)
            **kwargs: Additional pandas read_csv parameters

        Returns:
            Result[DataFrame, FileHandlerError]
            Ok(DataFrame) if successful, Err(FileHandlerError) if failed

        Examples:
            >>> handler = CSVHandler()
            >>> result = handler.read(Path("data.csv"))
            >>> result = handler.read(Path("data.csv"), delimiter=";")
            >>> result = handler.read(Path("data.csv"), encoding="latin-1")
        """
        if pd is None:
            return err(FileHandlerError("pandas is not installed"))

        # Validate file exists
        if not path.exists():
            return err(FileNotFoundError(f"File not found: {path}"))

        # Validate format
        if not self.can_handle(path):
            return err(UnsupportedFormatError(f"Unsupported format: {path.suffix}"))

        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            return err(FileSizeError(f"File too large: {file_size_mb:.1f}MB (max: {MAX_FILE_SIZE_MB}MB)"))

        # Try reading
        try:
            df = pd.read_csv(path, encoding=encoding, delimiter=delimiter, header=header, **kwargs)
            return ok(df)
        except PermissionError as e:
            return err(FileAccessError(f"Permission denied: {path} - {str(e)}"))
        except UnicodeDecodeError as e:
            return err(EncodingError(f"Encoding error: {str(e)}"))
        except Exception as e:
            return err(InvalidFileError(f"Failed to read CSV file: {str(e)}"))

    def write(
        self,
        df: "pd.DataFrame",
        path: Path,
        encoding: str = DEFAULT_CSV_ENCODING,
        delimiter: str = DEFAULT_CSV_DELIMITER,
        index: bool = False,
        **kwargs: Any,
    ) -> Result[None, FileHandlerError]:
        """Write DataFrame to CSV file.

        Args:
            df: DataFrame to write
            path: Output file path
            encoding: File encoding
            delimiter: Column delimiter
            index: Whether to write row indices
            **kwargs: Additional pandas to_csv parameters

        Returns:
            Result[None, FileHandlerError]
            Ok(None) if successful, Err(FileHandlerError) if failed
        """
        if pd is None:
            return err(FileHandlerError("pandas is not installed"))

        # Validate format
        if not self.can_handle(path):
            return err(UnsupportedFormatError(f"Unsupported format: {path.suffix}"))

        # Check if parent directory exists
        if path.parent != Path(".") and not path.parent.exists():
            return err(FileNotFoundError(f"Directory not found: {path.parent}"))

        # Try writing
        try:
            df.to_csv(path, encoding=encoding, sep=delimiter, index=index, **kwargs)
            return ok(None)
        except PermissionError as e:
            return err(FileAccessError(f"Permission denied: {path} - {str(e)}"))
        except Exception as e:
            return err(FileHandlerError(f"Failed to write CSV file: {str(e)}"))

    def detect_encoding(self, path: Path) -> Result[str, FileHandlerError]:
        """Auto-detect file encoding.

        Tries common encodings in order and returns the first one that succeeds.

        Args:
            path: Path to file

        Returns:
            Result[str, FileHandlerError]
            Detected encoding if successful
        """
        # Validate file exists
        if not path.exists():
            return err(FileNotFoundError(f"File not found: {path}"))

        # Try each encoding
        for encoding in ENCODING_DETECTION_ORDER:
            try:
                with open(path, "r", encoding=encoding) as f:
                    f.read(1024)  # Try reading first 1KB
                return ok(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
            except Exception as e:
                return err(FileAccessError(f"Cannot read file: {str(e)}"))

        return err(EncodingError("Could not detect file encoding"))

    def detect_delimiter(self, path: Path, encoding: str = DEFAULT_CSV_ENCODING) -> Result[str, FileHandlerError]:
        """Auto-detect CSV delimiter.

        Analyzes the first line to determine the most likely delimiter.

        Args:
            path: Path to CSV file
            encoding: File encoding to use when reading

        Returns:
            Result[str, FileHandlerError]
            Detected delimiter if successful
        """
        # Validate file exists
        if not path.exists():
            return err(FileNotFoundError(f"File not found: {path}"))

        # Read first line
        try:
            with open(path, "r", encoding=encoding) as f:
                first_line = f.readline()
        except Exception as e:
            return err(FileAccessError(f"Cannot read file: {str(e)}"))

        # Count occurrences of each delimiter candidate
        counts = {delim: first_line.count(delim) for delim in DELIMITER_CANDIDATES}

        # Return delimiter with highest count
        best_delimiter = max(counts, key=counts.get)

        # If all counts are 0, default to comma
        if counts[best_delimiter] == 0:
            return ok(DEFAULT_CSV_DELIMITER)

        return ok(best_delimiter)


class HandlerFactory:
    """Factory for creating appropriate file handlers.

    Automatically selects the correct handler based on file extension.
    """

    def __init__(self) -> None:
        """Initialize factory with available handlers."""
        self._handlers = [
            ExcelHandler(),
            CSVHandler(),
        ]

    def get_handler(self, path: Path) -> Result[Any, FileHandlerError]:
        """Get appropriate handler for file path.

        Args:
            path: Path to file

        Returns:
            Result[FileHandler, UnsupportedFormatError]
            Ok(handler) if format is supported, Err otherwise
        """
        for handler in self._handlers:
            if handler.can_handle(path):
                return ok(handler)

        supported = ", ".join(SUPPORTED_READ_FORMATS.keys())
        return err(UnsupportedFormatError(f"No handler for {path.suffix}. Supported: {supported}"))

    def read_file(self, path: Path, **kwargs: Any) -> Result["pd.DataFrame", FileHandlerError]:
        """Read file using appropriate handler.

        Convenience method that combines handler selection and reading.

        Args:
            path: Path to file
            **kwargs: Handler-specific parameters

        Returns:
            Result[DataFrame, FileHandlerError]
        """
        handler_result = self.get_handler(path)
        if is_err(handler_result):
            return handler_result  # type: ignore

        handler = unwrap(handler_result)
        return handler.read(path, **kwargs)

    def write_file(self, df: "pd.DataFrame", path: Path, **kwargs: Any) -> Result[None, FileHandlerError]:
        """Write file using appropriate handler.

        Convenience method that combines handler selection and writing.

        Args:
            df: DataFrame to write
            path: Output file path
            **kwargs: Handler-specific parameters

        Returns:
            Result[None, FileHandlerError]
        """
        handler_result = self.get_handler(path)
        if is_err(handler_result):
            return handler_result  # type: ignore

        handler = unwrap(handler_result)
        return handler.write(df, path, **kwargs)

    def get_supported_read_formats(self) -> set[str]:
        """Get set of supported file formats for reading.

        Returns:
            Set of file extensions (e.g., {".xlsx", ".csv"})
        """
        return set(SUPPORTED_READ_FORMATS.keys())

    def get_supported_write_formats(self) -> set[str]:
        """Get set of supported file formats for writing.

        Returns:
            Set of file extensions (e.g., {".xlsx", ".csv"})
        """
        return set(SUPPORTED_WRITE_FORMATS.keys())
