"""Unit tests for unique command.

Tests for the unique command that extracts unique values.
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
def sample_data_file(tmp_path: Path) -> Path:
    """Create a sample data file with duplicate values."""
    df = pd.DataFrame(
        {
            "category": ["A", "B", "A", "C", "B", "A", "D", "C"],
            "product": ["X", "Y", "X", "Z", "Y", "W", "V", "Z"],
            "value": [10, 20, 15, 30, 25, 18, 22, 35],
        }
    )
    file_path = tmp_path / "data.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def file_with_nulls(tmp_path: Path) -> Path:
    """Create a file with null values."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 1, 2, 4],
            "status": ["active", None, "active", "active", None, "inactive"],
        }
    )
    file_path = tmp_path / "nulls.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def empty_file(tmp_path: Path) -> Path:
    """Create an empty DataFrame file."""
    df = pd.DataFrame()
    file_path = tmp_path / "empty.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def csv_file_for_unique(tmp_path: Path) -> Path:
    """Create a CSV file for unique extraction."""
    df = pd.DataFrame(
        {
            "region": ["North", "South", "North", "East", "South", "West"],
            "sales": [100, 200, 150, 300, 250, 180],
        }
    )
    file_path = tmp_path / "unique.csv"
    df.to_csv(file_path, index=False)
    return file_path


# =============================================================================
# Unique Command Tests
# =============================================================================


class TestUniqueCommand:
    """Tests for the unique command."""

    def test_unique_single_column(self, sample_data_file: Path):
        """Test extracting unique values from single column."""
        result = runner.invoke(app, [
            "unique", str(sample_data_file),
            "--columns", "category"
        ])

        assert result.exit_code == 0
        assert "Unique rows: 4" in result.stdout  # A, B, C, D

    def test_unique_multiple_columns(self, sample_data_file: Path):
        """Test extracting unique rows from multiple columns."""
        result = runner.invoke(app, [
            "unique", str(sample_data_file),
            "--columns", "category,product"
        ])

        assert result.exit_code == 0
        assert "Unique rows:" in result.stdout

    def test_unique_with_count(self, sample_data_file: Path):
        """Test unique values with count."""
        result = runner.invoke(app, [
            "unique", str(sample_data_file),
            "--columns", "category",
            "--count"
        ])

        assert result.exit_code == 0
        # Should show count for each category

    def test_unique_with_output(self, sample_data_file: Path, tmp_path: Path):
        """Test unique with output file."""
        output_path = tmp_path / "unique.xlsx"
        result = runner.invoke(app, [
            "unique", str(sample_data_file),
            "--columns", "category",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Written to:" in result.stdout
        assert output_path.exists()

    def test_unique_dry_run(self, sample_data_file: Path):
        """Test dry-run mode."""
        result = runner.invoke(app, [
            "unique", str(sample_data_file),
            "--columns", "category",
            "--dry-run"
        ])

        assert result.exit_code == 0
        assert "Preview" in result.stdout

    def test_unique_csv_input(self, csv_file_for_unique: Path):
        """Test unique from CSV file."""
        result = runner.invoke(app, [
            "unique", str(csv_file_for_unique),
            "--columns", "region"
        ])

        assert result.exit_code == 0
        assert "Unique rows:" in result.stdout

    def test_unique_specific_sheet(self, sample_data_file: Path):
        """Test unique from specific sheet."""
        result = runner.invoke(app, [
            "unique", str(sample_data_file),
            "--columns", "category",
            "--sheet", "Sheet1"
        ])

        assert result.exit_code == 0

    def test_unique_invalid_column(self, sample_data_file: Path):
        """Test unique with non-existent column."""
        result = runner.invoke(app, [
            "unique", str(sample_data_file),
            "--columns", "invalid_column"
        ])

        assert result.exit_code == 1

    def test_unique_no_columns_specified(self, sample_data_file: Path):
        """Test unique without specifying columns."""
        result = runner.invoke(app, ["unique", str(sample_data_file)])

        assert result.exit_code == 1

    def test_unique_empty_file(self, empty_file: Path):
        """Test unique on empty file."""
        result = runner.invoke(app, [
            "unique", str(empty_file),
            "--columns", "category"
        ])

        assert result.exit_code == 0
        assert "empty" in result.stdout.lower()

    def test_unique_with_nulls(self, file_with_nulls: Path):
        """Test unique with null values."""
        result = runner.invoke(app, [
            "unique", str(file_with_nulls),
            "--columns", "id"
        ])

        assert result.exit_code == 0
        assert "Unique rows:" in result.stdout

    def test_unique_multiple_columns_with_count(self, sample_data_file: Path):
        """Test unique rows from multiple columns with count."""
        result = runner.invoke(app, [
            "unique", str(sample_data_file),
            "--columns", "category,product",
            "--count"
        ])

        assert result.exit_code == 0

    def test_unique_nonexistent_file(self):
        """Test unique on non-existent file."""
        result = runner.invoke(app, [
            "unique", "missing.xlsx",
            "--columns", "category"
        ])

        assert result.exit_code == 1

    def test_unique_help(self):
        """Test unique command help."""
        result = runner.invoke(app, ["unique", "--help"])

        assert result.exit_code == 0
        assert "Extract unique values" in result.stdout
        assert "--columns" in result.stdout

    def test_unique_all_unique_values(self, sample_data_file: Path):
        """Test when all values are already unique."""
        result = runner.invoke(app, [
            "unique", str(sample_data_file),
            "--columns", "value"
        ])

        assert result.exit_code == 0
        assert "Unique rows: 8" in result.stdout  # All 8 values are unique
