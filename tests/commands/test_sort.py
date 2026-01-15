"""Unit tests for sort command.

Tests for the sort command that sorts rows based on column values.
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner
import pandas as pd

from excel_toolkit.cli import app

# Initialize CLI test runner
runner = CliRunner()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_excel_file(tmp_path: Path) -> Path:
    """Create a sample Excel file for testing."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Charlie", "Alice", "Eve", "Bob", "Diana"],
            "age": [35, 25, 32, 30, 28],
            "city": ["Berlin", "Paris", "Rome", "London", "Madrid"],
            "salary": [70000, 50000, 65000, 60000, 55000],
        }
    )
    file_path = tmp_path / "test.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def sample_csv_file(tmp_path: Path) -> Path:
    """Create a sample CSV file for testing."""
    df = pd.DataFrame(
        {
            "product": ["C", "A", "E", "B", "D"],
            "category": ["Electronics", "Clothing", "Home", "Electronics", "Clothing"],
            "price": [49.99, 19.99, 39.99, 29.99, 14.99],
        }
    )
    file_path = tmp_path / "test.csv"
    df.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def file_with_nulls(tmp_path: Path) -> Path:
    """Create a file with null values."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", None, "Diana", "Eve"],
            "value": [100, None, 300, 400, None],
        }
    )
    file_path = tmp_path / "nulls.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def file_with_dates(tmp_path: Path) -> Path:
    """Create a file with dates."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "date": pd.to_datetime(["2023-01-15", "2023-03-20", "2023-02-10"]),
        }
    )
    file_path = tmp_path / "dates.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def empty_file(tmp_path: Path) -> Path:
    """Create an empty DataFrame file."""
    df = pd.DataFrame()
    file_path = tmp_path / "empty.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


# =============================================================================
# Sort Command Tests
# =============================================================================


class TestSortCommand:
    """Tests for the sort command."""

    def test_sort_single_column_ascending(self, sample_excel_file: Path):
        """Test sorting by single column in ascending order."""
        result = runner.invoke(app, ["sort", str(sample_excel_file), "--columns", "name"])

        assert result.exit_code == 0
        assert "Sorted 5 rows" in result.stdout

    def test_sort_single_column_descending(self, sample_excel_file: Path):
        """Test sorting by single column in descending order."""
        result = runner.invoke(app, ["sort", str(sample_excel_file), "--columns", "salary", "--desc"])

        assert result.exit_code == 0
        assert "Sorted 5 rows" in result.stdout
        assert "descending" in result.stdout

    def test_sort_multiple_columns(self, sample_excel_file: Path):
        """Test sorting by multiple columns."""
        result = runner.invoke(app, ["sort", str(sample_excel_file), "--columns", "city,age"])

        assert result.exit_code == 0
        assert "Sorted 5 rows" in result.stdout
        assert "Columns: city,age" in result.stdout

    def test_sort_with_output(self, sample_excel_file: Path, tmp_path: Path):
        """Test sorting with output file."""
        output_path = tmp_path / "sorted.xlsx"
        result = runner.invoke(
            app, ["sort", str(sample_excel_file), "--columns", "age", "--output", str(output_path)]
        )

        assert result.exit_code == 0
        assert "Written to:" in result.stdout
        assert output_path.exists()

    def test_sort_limited_rows(self, sample_excel_file: Path):
        """Test limiting results."""
        result = runner.invoke(app, ["sort", str(sample_excel_file), "--columns", "name", "--rows", "3"])

        assert result.exit_code == 0
        assert "Sorted" in result.stdout

    def test_sort_csv_format(self, sample_excel_file: Path):
        """Test CSV output format."""
        result = runner.invoke(app, ["sort", str(sample_excel_file), "--columns", "age", "--format", "csv"])

        assert result.exit_code == 0
        assert "," in result.stdout or "name,age" in result.stdout

    def test_sort_json_format(self, sample_excel_file: Path):
        """Test JSON output format."""
        result = runner.invoke(app, ["sort", str(sample_excel_file), "--columns", "name", "--format", "json"])

        assert result.exit_code == 0
        assert "[" in result.stdout or "{" in result.stdout

    def test_sort_with_filter(self, sample_excel_file: Path):
        """Test sorting with filter condition."""
        result = runner.invoke(app, ["sort", str(sample_excel_file), "--columns", "age", "--where", "age > 25"])

        assert result.exit_code == 0
        assert "Sorted" in result.stdout
        assert "Filter:" in result.stdout

    def test_sort_with_filter_no_matches(self, sample_excel_file: Path):
        """Test sort with filter that matches no rows."""
        result = runner.invoke(app, ["sort", str(sample_excel_file), "--columns", "age", "--where", "age > 100"])

        assert result.exit_code == 0
        assert "No rows match" in result.stdout

    def test_sort_na_placement_first(self, file_with_nulls: Path):
        """Test sorting with NaN values placed first."""
        result = runner.invoke(app, ["sort", str(file_with_nulls), "--columns", "value", "--na-placement", "first"])

        assert result.exit_code == 0
        assert "Sorted" in result.stdout
        assert "NaN placement: first" in result.stdout

    def test_sort_na_placement_last(self, file_with_nulls: Path):
        """Test sorting with NaN values placed last (default)."""
        result = runner.invoke(app, ["sort", str(file_with_nulls), "--columns", "value", "--na-placement", "last"])

        assert result.exit_code == 0
        assert "Sorted" in result.stdout
        assert "NaN placement: last" in result.stdout

    def test_sort_invalid_na_placement(self, sample_excel_file: Path):
        """Test invalid na_placement value."""
        result = runner.invoke(app, ["sort", str(sample_excel_file), "--columns", "age", "--na-placement", "invalid"])

        assert result.exit_code == 1

    def test_sort_invalid_column(self, sample_excel_file: Path):
        """Test invalid column name."""
        result = runner.invoke(app, ["sort", str(sample_excel_file), "--columns", "invalid_col"])

        assert result.exit_code == 1

    def test_sort_invalid_columns_in_list(self, sample_excel_file: Path):
        """Test invalid column name in multi-column sort."""
        result = runner.invoke(app, ["sort", str(sample_excel_file), "--columns", "name,invalid"])

        assert result.exit_code == 1

    def test_sort_csv_input(self, sample_csv_file: Path):
        """Test sorting CSV file."""
        result = runner.invoke(app, ["sort", str(sample_csv_file), "--columns", "product"])

        assert result.exit_code == 0
        assert "Sorted" in result.stdout

    def test_sort_nonexistent_file(self):
        """Test sort on non-existent file."""
        result = runner.invoke(app, ["sort", "missing.xlsx", "--columns", "age"])

        assert result.exit_code == 1

    def test_sort_empty_file(self, empty_file: Path):
        """Test sort on empty file."""
        result = runner.invoke(app, ["sort", str(empty_file), "--columns", "age"])

        assert result.exit_code == 0
        assert "File is empty" in result.stdout

    def test_sort_with_dates(self, file_with_dates: Path):
        """Test sorting by date column."""
        result = runner.invoke(app, ["sort", str(file_with_dates), "--columns", "date"])

        assert result.exit_code == 0
        assert "Sorted" in result.stdout

    def test_sort_invalid_filter_condition(self, sample_excel_file: Path):
        """Test sort with invalid filter condition."""
        result = runner.invoke(app, ["sort", str(sample_excel_file), "--columns", "age", "--where", "invalid > 30"])

        assert result.exit_code == 1

    def test_sort_help(self):
        """Test sort command help."""
        result = runner.invoke(app, ["sort", "--help"])

        assert result.exit_code == 0
        assert "Sort rows" in result.stdout
        assert "--columns" in result.stdout
