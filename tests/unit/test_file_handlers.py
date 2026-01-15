"""Unit tests for file handlers.

Tests for ExcelHandler, CSVHandler, and HandlerFactory including:
- Reading valid files
- Error handling for missing/corrupted files
- Encoding and delimiter detection
- Factory handler selection
"""

import pytest
from pathlib import Path
import pandas as pd

from excel_toolkit.core import (
    ExcelHandler,
    CSVHandler,
    HandlerFactory,
    FileNotFoundError,
    FileAccessError,
    UnsupportedFormatError,
    InvalidFileError,
    FileSizeError,
    EncodingError,
)
from excel_toolkit.fp import is_ok, is_err, unwrap, unwrap_err


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_excel_file(tmp_path: Path) -> Path:
    """Create a sample Excel file for testing."""
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "city": ["Paris", "London", "Berlin"],
        }
    )
    file_path = tmp_path / "test.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def multi_sheet_excel_file(tmp_path: Path) -> Path:
    """Create an Excel file with multiple sheets."""
    df1 = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    df2 = pd.DataFrame({"x": [10, 20], "y": [30, 40]})

    file_path = tmp_path / "multi.xlsx"
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df1.to_excel(writer, sheet_name="Sheet1", index=False)
        df2.to_excel(writer, sheet_name="Sheet2", index=False)
    return file_path


@pytest.fixture
def sample_csv_file(tmp_path: Path) -> Path:
    """Create a sample CSV file for testing."""
    df = pd.DataFrame({"product": ["A", "B", "C"], "price": [10.5, 20.0, 15.3], "stock": [100, 50, 75]})
    file_path = tmp_path / "test.csv"
    df.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def csv_with_semicolon(tmp_path: Path) -> Path:
    """Create a CSV file with semicolon delimiter."""
    file_path = tmp_path / "semicolon.csv"
    file_path.write_text("product;price;stock\nA;10.5;100\nB;20.0;50", encoding="utf-8")
    return file_path


@pytest.fixture
def csv_with_latin1(tmp_path: Path) -> Path:
    """Create a CSV file with Latin-1 encoding."""
    df = pd.DataFrame({"nom": ["François", "José"], "âge": [25, 30]})
    file_path = tmp_path / "latin1.csv"
    df.to_csv(file_path, index=False, encoding="latin-1")
    return file_path


@pytest.fixture
def empty_excel_file(tmp_path: Path) -> Path:
    """Create an empty Excel file."""
    df = pd.DataFrame()
    file_path = tmp_path / "empty.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def corrupted_excel_file(tmp_path: Path) -> Path:
    """Create a corrupted Excel file."""
    file_path = tmp_path / "corrupted.xlsx"
    file_path.write_text("This is not a valid Excel file")
    return file_path


@pytest.fixture
def corrupted_csv_file(tmp_path: Path) -> Path:
    """Create a corrupted CSV file."""
    file_path = tmp_path / "corrupted.csv"
    file_path.write_bytes(b"\x00\x01\x02\x03 Invalid binary data")
    return file_path


# =============================================================================
# ExcelHandler Tests
# =============================================================================


class TestExcelHandler:
    """Tests for ExcelHandler."""

    def test_can_handle_xlsx(self):
        """Handler accepts .xlsx files."""
        handler = ExcelHandler()
        assert handler.can_handle(Path("data.xlsx"))

    def test_can_handle_xls(self):
        """Handler accepts .xls files."""
        handler = ExcelHandler()
        assert handler.can_handle(Path("data.xls"))

    def test_cannot_handle_csv(self):
        """Handler rejects .csv files."""
        handler = ExcelHandler()
        assert not handler.can_handle(Path("data.csv"))

    def test_read_valid_file(self, sample_excel_file: Path):
        """Reading valid Excel file returns DataFrame."""
        handler = ExcelHandler()
        result = handler.read(sample_excel_file)

        assert is_ok(result)
        df = unwrap(result)
        assert len(df) == 3
        assert list(df.columns) == ["name", "age", "city"]
        assert df["name"].tolist() == ["Alice", "Bob", "Charlie"]

    def test_read_nonexistent_file(self):
        """Reading non-existent file returns FileNotFoundError."""
        handler = ExcelHandler()
        result = handler.read(Path("nonexistent.xlsx"))

        assert is_err(result)
        error = unwrap_err(result)
        assert isinstance(error, FileNotFoundError)

    def test_read_unsupported_format(self, tmp_path: Path):
        """Reading unsupported format returns UnsupportedFormatError."""
        handler = ExcelHandler()
        invalid_file = tmp_path / "data.txt"
        invalid_file.write_text("Some text")

        result = handler.read(invalid_file)
        assert is_err(result)
        assert isinstance(unwrap_err(result), UnsupportedFormatError)

    def test_read_corrupted_file(self, corrupted_excel_file: Path):
        """Reading corrupted file returns InvalidFileError."""
        handler = ExcelHandler()
        result = handler.read(corrupted_excel_file)

        assert is_err(result)
        assert isinstance(unwrap_err(result), InvalidFileError)

    def test_read_empty_file(self, empty_excel_file: Path):
        """Reading empty file returns empty DataFrame."""
        handler = ExcelHandler()
        result = handler.read(empty_excel_file)

        assert is_ok(result)
        df = unwrap(result)
        assert df.empty

    def test_read_specific_sheet(self, multi_sheet_excel_file: Path):
        """Reading specific sheet works correctly."""
        handler = ExcelHandler()
        result = handler.read(multi_sheet_excel_file, sheet_name="Sheet2")

        assert is_ok(result)
        df = unwrap(result)
        assert list(df.columns) == ["x", "y"]
        assert len(df) == 2

    def test_read_all_sheets(self, multi_sheet_excel_file: Path):
        """Reading all sheets returns dictionary."""
        handler = ExcelHandler()
        result = handler.read_all_sheets(multi_sheet_excel_file)

        assert is_ok(result)
        sheets = unwrap(result)
        assert isinstance(sheets, dict)
        assert "Sheet1" in sheets
        assert "Sheet2" in sheets
        assert len(sheets["Sheet1"]) == 3
        assert len(sheets["Sheet2"]) == 2

    def test_read_all_sheets_nonexistent_file(self):
        """Reading all sheets from non-existent file returns error."""
        handler = ExcelHandler()
        result = handler.read_all_sheets(Path("nonexistent.xlsx"))

        assert is_err(result)
        assert isinstance(unwrap_err(result), FileNotFoundError)

    def test_get_sheet_names(self, multi_sheet_excel_file: Path):
        """Getting sheet names returns list."""
        handler = ExcelHandler()
        result = handler.get_sheet_names(multi_sheet_excel_file)

        assert is_ok(result)
        sheets = unwrap(result)
        assert isinstance(sheets, list)
        assert "Sheet1" in sheets
        assert "Sheet2" in sheets

    def test_get_sheet_names_nonexistent_file(self):
        """Getting sheet names from non-existent file returns error."""
        handler = ExcelHandler()
        result = handler.get_sheet_names(Path("nonexistent.xlsx"))

        assert is_err(result)
        assert isinstance(unwrap_err(result), FileNotFoundError)

    def test_get_sheet_info(self, multi_sheet_excel_file: Path):
        """Getting sheet info returns metadata."""
        handler = ExcelHandler()
        result = handler.get_sheet_info(multi_sheet_excel_file)

        assert is_ok(result)
        info = unwrap(result)
        assert isinstance(info, dict)
        assert "Sheet1" in info
        assert info["Sheet1"]["rows"] == 3
        assert info["Sheet1"]["columns"] == 2

    def test_write_dataframe(self, tmp_path: Path):
        """Writing DataFrame to Excel succeeds."""
        handler = ExcelHandler()
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        output_path = tmp_path / "output.xlsx"

        result = handler.write(df, output_path)

        assert is_ok(result)
        assert output_path.exists()

        # Verify written data
        read_result = handler.read(output_path)
        assert is_ok(read_result)
        read_df = unwrap(read_result)
        pd.testing.assert_frame_equal(df, read_df)

    def test_write_to_nonexistent_directory(self, tmp_path: Path):
        """Writing to non-existent directory returns FileNotFoundError."""
        handler = ExcelHandler()
        df = pd.DataFrame({"a": [1, 2, 3]})
        output_path = tmp_path / "nonexistent" / "output.xlsx"

        result = handler.write(df, output_path)

        assert is_err(result)
        assert isinstance(unwrap_err(result), FileNotFoundError)

    def test_write_with_custom_sheet_name(self, tmp_path: Path):
        """Writing with custom sheet name works."""
        handler = ExcelHandler()
        df = pd.DataFrame({"a": [1, 2, 3]})
        output_path = tmp_path / "custom.xlsx"

        result = handler.write(df, output_path, sheet_name="MyData")

        assert is_ok(result)

        # Verify sheet name
        names_result = handler.get_sheet_names(output_path)
        assert is_ok(names_result)
        assert unwrap(names_result) == ["MyData"]


# =============================================================================
# CSVHandler Tests
# =============================================================================


class TestCSVHandler:
    """Tests for CSVHandler."""

    def test_can_handle_csv(self):
        """Handler accepts .csv files."""
        handler = CSVHandler()
        assert handler.can_handle(Path("data.csv"))

    def test_cannot_handle_xlsx(self):
        """Handler rejects .xlsx files."""
        handler = CSVHandler()
        assert not handler.can_handle(Path("data.xlsx"))

    def test_read_valid_csv(self, sample_csv_file: Path):
        """Reading valid CSV returns DataFrame."""
        handler = CSVHandler()
        result = handler.read(sample_csv_file)

        assert is_ok(result)
        df = unwrap(result)
        assert len(df) == 3
        assert list(df.columns) == ["product", "price", "stock"]

    def test_read_nonexistent_file(self):
        """Reading non-existent file returns FileNotFoundError."""
        handler = CSVHandler()
        result = handler.read(Path("nonexistent.csv"))

        assert is_err(result)
        assert isinstance(unwrap_err(result), FileNotFoundError)

    def test_read_unsupported_format(self, tmp_path: Path):
        """Reading unsupported format returns UnsupportedFormatError."""
        handler = CSVHandler()
        invalid_file = tmp_path / "data.txt"
        invalid_file.write_text("Some text")

        result = handler.read(invalid_file)
        assert is_err(result)
        assert isinstance(unwrap_err(result), UnsupportedFormatError)

    def test_read_with_different_delimiter(self, csv_with_semicolon: Path):
        """Reading CSV with semicolon delimiter."""
        handler = CSVHandler()
        result = handler.read(csv_with_semicolon, delimiter=";")

        assert is_ok(result)
        df = unwrap(result)
        assert list(df.columns) == ["product", "price", "stock"]
        assert len(df) == 2

    def test_write_dataframe(self, tmp_path: Path):
        """Writing DataFrame to CSV succeeds."""
        handler = CSVHandler()
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        output_path = tmp_path / "output.csv"

        result = handler.write(df, output_path)

        assert is_ok(result)
        assert output_path.exists()

        # Verify written data
        read_result = handler.read(output_path)
        assert is_ok(read_result)
        read_df = unwrap(read_result)
        pd.testing.assert_frame_equal(df, read_df)

    def test_write_with_different_delimiter(self, tmp_path: Path):
        """Writing with semicolon delimiter works."""
        handler = CSVHandler()
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        output_path = tmp_path / "semicolon.csv"

        result = handler.write(df, output_path, delimiter=";")

        assert is_ok(result)

        # Verify delimiter
        content = output_path.read_text()
        assert ";" in content

    def test_detect_encoding_utf8(self, sample_csv_file: Path):
        """Auto-detect UTF-8 encoding."""
        handler = CSVHandler()
        result = handler.detect_encoding(sample_csv_file)

        assert is_ok(result)
        encoding = unwrap(result)
        assert encoding == "utf-8"

    def test_detect_encoding_latin1(self, csv_with_latin1: Path):
        """Auto-detect Latin-1 encoding."""
        handler = CSVHandler()
        result = handler.detect_encoding(csv_with_latin1)

        assert is_ok(result)
        encoding = unwrap(result)
        # Should detect latin-1 or utf-8 (both work)
        assert encoding in ["utf-8", "latin-1", "iso-8859-1", "cp1252"]

    def test_detect_encoding_nonexistent_file(self):
        """Detect encoding on non-existent file returns error."""
        handler = CSVHandler()
        result = handler.detect_encoding(Path("nonexistent.csv"))

        assert is_err(result)
        assert isinstance(unwrap_err(result), FileNotFoundError)

    def test_detect_delimiter_comma(self, sample_csv_file: Path):
        """Auto-detect comma delimiter."""
        handler = CSVHandler()
        result = handler.detect_delimiter(sample_csv_file)

        assert is_ok(result)
        delimiter = unwrap(result)
        assert delimiter == ","

    def test_detect_delimiter_semicolon(self, csv_with_semicolon: Path):
        """Auto-detect semicolon delimiter."""
        handler = CSVHandler()
        result = handler.detect_delimiter(csv_with_semicolon)

        assert is_ok(result)
        delimiter = unwrap(result)
        assert delimiter == ";"

    def test_detect_delimiter_nonexistent_file(self):
        """Detect delimiter on non-existent file returns error."""
        handler = CSVHandler()
        result = handler.detect_delimiter(Path("nonexistent.csv"))

        assert is_err(result)
        assert isinstance(unwrap_err(result), FileNotFoundError)


# =============================================================================
# HandlerFactory Tests
# =============================================================================


class TestHandlerFactory:
    """Tests for HandlerFactory."""

    def test_get_excel_handler(self):
        """Factory returns ExcelHandler for .xlsx files."""
        factory = HandlerFactory()
        result = factory.get_handler(Path("data.xlsx"))

        assert is_ok(result)
        handler = unwrap(result)
        assert isinstance(handler, ExcelHandler)

    def test_get_xls_handler(self):
        """Factory returns ExcelHandler for .xls files."""
        factory = HandlerFactory()
        result = factory.get_handler(Path("data.xls"))

        assert is_ok(result)
        handler = unwrap(result)
        assert isinstance(handler, ExcelHandler)

    def test_get_csv_handler(self):
        """Factory returns CSVHandler for .csv files."""
        factory = HandlerFactory()
        result = factory.get_handler(Path("data.csv"))

        assert is_ok(result)
        handler = unwrap(result)
        assert isinstance(handler, CSVHandler)

    def test_unsupported_format(self):
        """Factory returns error for unsupported format."""
        factory = HandlerFactory()
        result = factory.get_handler(Path("data.json"))

        assert is_err(result)
        assert isinstance(unwrap_err(result), UnsupportedFormatError)

    def test_read_excel_file_convenience(self, sample_excel_file: Path):
        """read_file() selects correct handler and reads Excel."""
        factory = HandlerFactory()
        result = factory.read_file(sample_excel_file)

        assert is_ok(result)
        df = unwrap(result)
        assert len(df) == 3

    def test_read_csv_file_convenience(self, sample_csv_file: Path):
        """read_file() selects correct handler and reads CSV."""
        factory = HandlerFactory()
        result = factory.read_file(sample_csv_file)

        assert is_ok(result)
        df = unwrap(result)
        assert len(df) == 3

    def test_read_unsupported_format_convenience(self):
        """read_file() returns error for unsupported format."""
        factory = HandlerFactory()
        result = factory.read_file(Path("data.json"))

        assert is_err(result)
        assert isinstance(unwrap_err(result), UnsupportedFormatError)

    def test_write_excel_file_convenience(self, tmp_path: Path):
        """write_file() selects correct handler and writes Excel."""
        factory = HandlerFactory()
        df = pd.DataFrame({"a": [1, 2, 3]})
        output_path = tmp_path / "output.xlsx"

        result = factory.write_file(df, output_path)

        assert is_ok(result)
        assert output_path.exists()

    def test_write_csv_file_convenience(self, tmp_path: Path):
        """write_file() selects correct handler and writes CSV."""
        factory = HandlerFactory()
        df = pd.DataFrame({"a": [1, 2, 3]})
        output_path = tmp_path / "output.csv"

        result = factory.write_file(df, output_path)

        assert is_ok(result)
        assert output_path.exists()

    def test_get_supported_read_formats(self):
        """Get supported read formats."""
        factory = HandlerFactory()
        formats = factory.get_supported_read_formats()

        assert ".xlsx" in formats
        assert ".xls" in formats
        assert ".csv" in formats

    def test_get_supported_write_formats(self):
        """Get supported write formats."""
        factory = HandlerFactory()
        formats = factory.get_supported_write_formats()

        assert ".xlsx" in formats
        assert ".csv" in formats
