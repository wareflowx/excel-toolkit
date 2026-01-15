"""Unit tests for fill command.

Tests for the fill command that fills missing values.
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner
import pandas as pd
import numpy as np

from excel_toolkit.cli import app

# Initialize CLI test runner
runner = CliRunner()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def file_with_nulls(tmp_path: Path) -> Path:
    """Create a file with null values."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", None, "Diana", "Eve"],
            "age": [25, 30, 35, None, 32],
            "salary": [50000, None, 70000, 55000, None],
            "city": ["Paris", "London", "Berlin", None, "Rome"],
        }
    )
    file_path = tmp_path / "nulls.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def numeric_file_with_nulls(tmp_path: Path) -> Path:
    """Create a file with numeric null values."""
    df = pd.DataFrame(
        {
            "product": ["A", "B", "C", "D", "E"],
            "price": [10.5, None, 15.0, None, 20.0],
            "quantity": [100, 200, None, 150, None],
            "discount": [0.1, 0.15, None, 0.2, None],
        }
    )
    file_path = tmp_path / "numeric_nulls.xlsx"
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
def csv_file_with_nulls(tmp_path: Path) -> Path:
    """Create a CSV file with null values."""
    df = pd.DataFrame(
        {
            "item": ["X", "Y", "Z", "W"],
            "value": [100, None, 300, None],
            "status": ["OK", None, "OK", "OK"],
        }
    )
    file_path = tmp_path / "nulls.csv"
    df.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def file_no_nulls(tmp_path: Path) -> Path:
    """Create a file with no null values."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
        }
    )
    file_path = tmp_path / "no_nulls.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def file_for_ffill_bfill(tmp_path: Path) -> Path:
    """Create a file suitable for forward/backward fill testing."""
    df = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
            "value": [100, None, None, 150, None],
        }
    )
    file_path = tmp_path / "ffill_test.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


# =============================================================================
# Fill Command Tests
# =============================================================================


class TestFillCommand:
    """Tests for the fill command."""

    def test_fill_with_constant_value(self, file_with_nulls: Path):
        """Test filling with constant value."""
        result = runner.invoke(app, [
            "fill", str(file_with_nulls),
            "--columns", "age",
            "--value", "0"
        ])

        assert result.exit_code == 0
        assert "Missing values before:" in result.stdout
        assert "Value: 0" in result.stdout

    def test_fill_mean_strategy(self, numeric_file_with_nulls: Path):
        """Test filling with mean strategy."""
        result = runner.invoke(app, [
            "fill", str(numeric_file_with_nulls),
            "--columns", "price",
            "--strategy", "mean"
        ])

        assert result.exit_code == 0
        assert "Strategy: mean" in result.stdout
        assert "Values filled:" in result.stdout

    def test_fill_median_strategy(self, numeric_file_with_nulls: Path):
        """Test filling with median strategy."""
        result = runner.invoke(app, [
            "fill", str(numeric_file_with_nulls),
            "--columns", "quantity",
            "--strategy", "median"
        ])

        assert result.exit_code == 0
        assert "Strategy: median" in result.stdout

    def test_fill_mode_strategy(self, file_with_nulls: Path):
        """Test filling with mode strategy."""
        result = runner.invoke(app, [
            "fill", str(file_with_nulls),
            "--columns", "name",
            "--strategy", "mode"
        ])

        assert result.exit_code == 0
        assert "Strategy: mode" in result.stdout

    def test_fill_min_strategy(self, numeric_file_with_nulls: Path):
        """Test filling with min strategy."""
        result = runner.invoke(app, [
            "fill", str(numeric_file_with_nulls),
            "--columns", "price",
            "--strategy", "min"
        ])

        assert result.exit_code == 0
        assert "Strategy: min" in result.stdout

    def test_fill_max_strategy(self, numeric_file_with_nulls: Path):
        """Test filling with max strategy."""
        result = runner.invoke(app, [
            "fill", str(numeric_file_with_nulls),
            "--columns", "price",
            "--strategy", "max"
        ])

        assert result.exit_code == 0
        assert "Strategy: max" in result.stdout

    def test_fill_ffill_strategy(self, file_for_ffill_bfill: Path):
        """Test forward fill strategy."""
        result = runner.invoke(app, [
            "fill", str(file_for_ffill_bfill),
            "--columns", "value",
            "--strategy", "ffill"
        ])

        assert result.exit_code == 0
        assert "Strategy: ffill" in result.stdout

    def test_fill_bfill_strategy(self, file_for_ffill_bfill: Path):
        """Test backward fill strategy."""
        result = runner.invoke(app, [
            "fill", str(file_for_ffill_bfill),
            "--columns", "value",
            "--strategy", "bfill"
        ])

        assert result.exit_code == 0
        assert "Strategy: bfill" in result.stdout

    def test_fill_multiple_columns(self, file_with_nulls: Path):
        """Test filling multiple columns."""
        result = runner.invoke(app, [
            "fill", str(file_with_nulls),
            "--columns", "age,salary",
            "--value", "0"
        ])

        assert result.exit_code == 0
        assert "Columns: age, salary" in result.stdout

    def test_fill_all_columns(self, file_with_nulls: Path):
        """Test filling all columns with missing values."""
        result = runner.invoke(app, [
            "fill", str(file_with_nulls),
            "--strategy", "mean"
        ])

        assert result.exit_code == 0
        assert "all columns with missing values" in result.stdout

    def test_fill_with_output(self, file_with_nulls: Path, tmp_path: Path):
        """Test filling with output file."""
        output_path = tmp_path / "filled.xlsx"
        result = runner.invoke(app, [
            "fill", str(file_with_nulls),
            "--columns", "age",
            "--value", "30",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Written to:" in result.stdout
        assert output_path.exists()

    def test_fill_dry_run(self, file_with_nulls: Path):
        """Test dry-run mode."""
        result = runner.invoke(app, [
            "fill", str(file_with_nulls),
            "--columns", "age",
            "--value", "30",
            "--dry-run"
        ])

        assert result.exit_code == 0
        assert "Preview" in result.stdout

    def test_fill_csv_input(self, csv_file_with_nulls: Path):
        """Test filling from CSV file."""
        result = runner.invoke(app, [
            "fill", str(csv_file_with_nulls),
            "--columns", "value",
            "--value", "0"
        ])

        assert result.exit_code == 0
        assert "Values filled:" in result.stdout

    def test_fill_specific_sheet(self, file_with_nulls: Path):
        """Test filling from specific sheet."""
        result = runner.invoke(app, [
            "fill", str(file_with_nulls),
            "--columns", "age",
            "--value", "0",
            "--sheet", "Sheet1"
        ])

        assert result.exit_code == 0

    def test_fill_invalid_column(self, file_with_nulls: Path):
        """Test filling with non-existent column."""
        result = runner.invoke(app, [
            "fill", str(file_with_nulls),
            "--columns", "invalid_column",
            "--value", "0"
        ])

        assert result.exit_code == 1

    def test_fill_invalid_strategy(self, file_with_nulls: Path):
        """Test filling with invalid strategy."""
        result = runner.invoke(app, [
            "fill", str(file_with_nulls),
            "--columns", "age",
            "--strategy", "invalid"
        ])

        assert result.exit_code == 1

    def test_fill_no_options(self, file_with_nulls: Path):
        """Test fill without specifying value or strategy."""
        result = runner.invoke(app, ["fill", str(file_with_nulls)])

        assert result.exit_code == 1

    def test_fill_both_value_and_strategy(self, file_with_nulls: Path):
        """Test fill with both value and strategy specified."""
        result = runner.invoke(app, [
            "fill", str(file_with_nulls),
            "--columns", "age",
            "--value", "0",
            "--strategy", "mean"
        ])

        assert result.exit_code == 1

    def test_fill_empty_file(self, empty_file: Path):
        """Test fill on empty file."""
        result = runner.invoke(app, [
            "fill", str(empty_file),
            "--columns", "age",
            "--value", "0"
        ])

        assert result.exit_code == 0
        assert "empty" in result.stdout.lower()

    def test_fill_no_nulls(self, file_no_nulls: Path):
        """Test fill on file with no missing values."""
        result = runner.invoke(app, [
            "fill", str(file_no_nulls),
            "--columns", "age",
            "--value", "0"
        ])

        assert result.exit_code == 0

    def test_fill_nonexistent_file(self):
        """Test fill on non-existent file."""
        result = runner.invoke(app, [
            "fill", "missing.xlsx",
            "--columns", "age",
            "--value", "0"
        ])

        assert result.exit_code == 1

    def test_fill_help(self):
        """Test fill command help."""
        result = runner.invoke(app, ["fill", "--help"])

        assert result.exit_code == 0
        assert "Fill missing values" in result.stdout
        assert "--value" in result.stdout
        assert "--strategy" in result.stdout

    def test_fill_numeric_string_conversion(self, file_with_nulls: Path):
        """Test that numeric values are properly converted."""
        result = runner.invoke(app, [
            "fill", str(file_with_nulls),
            "--columns", "age",
            "--value", "25"
        ])

        assert result.exit_code == 0
        assert "Values filled:" in result.stdout
