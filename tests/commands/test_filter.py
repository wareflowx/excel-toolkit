"""Unit tests for filter command.

Tests for the filter command that filters rows based on conditions.
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
            "id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack"],
            "age": [25, 30, 35, 28, 32, 27, 38, 29, 31, 26],
            "city": ["Paris", "London", "Berlin", "Madrid", "Rome", "Vienna", "Athens", "Lisbon", "Dublin", "Prague"],
            "salary": [50000, 60000, 70000, 55000, 65000, 52000, 75000, 58000, 62000, 48000],
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
            "product": ["A", "B", "C", "D", "E"],
            "category": ["Electronics", "Clothing", "Electronics", "Home", "Clothing"],
            "price": [29.99, 19.99, 49.99, 39.99, 14.99],
            "stock": [150, 75, 200, 100, 50],
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
            "name": ["Alice", None, "Charlie", "Diana", None],
            "value": [100, 200, None, 400, 500],
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


# =============================================================================
# Filter Command Tests
# =============================================================================


class TestFilterCommand:
    """Tests for the filter command."""

    def test_filter_simple_numeric(self, sample_excel_file: Path):
        """Test simple numeric filter."""
        result = runner.invoke(app, ["filter", str(sample_excel_file), "age > 30"])

        assert result.exit_code == 0
        assert "Filtered" in result.stdout
        assert "Condition: age > 30" in result.stdout

    def test_filter_string_equality(self, sample_excel_file: Path):
        """Test string equality filter."""
        result = runner.invoke(app, ["filter", str(sample_excel_file), "city == 'Paris'"])

        assert result.exit_code == 0
        assert "Filtered 1 of 10 rows" in result.stdout

    def test_filter_and_condition(self, sample_excel_file: Path):
        """Test AND logical operator."""
        result = runner.invoke(app, ["filter", str(sample_excel_file), "age > 30 and salary > 60000"])

        assert result.exit_code == 0
        assert "Filtered" in result.stdout

    def test_filter_or_condition(self, sample_excel_file: Path):
        """Test OR logical operator."""
        result = runner.invoke(app, ["filter", str(sample_excel_file), "age > 35 or city == 'Paris'"])

        assert result.exit_code == 0
        assert "Filtered" in result.stdout

    def test_filter_with_output(self, sample_excel_file: Path, tmp_path: Path):
        """Test filtering with output file."""
        output_path = tmp_path / "filtered.xlsx"
        result = runner.invoke(
            app, ["filter", str(sample_excel_file), "age > 30", "--output", str(output_path)]
        )

        assert result.exit_code == 0
        assert "Written to:" in result.stdout
        assert output_path.exists()

    def test_filter_limited_rows(self, sample_excel_file: Path):
        """Test limiting results."""
        result = runner.invoke(app, ["filter", str(sample_excel_file), "age > 25", "--rows", "3"])

        assert result.exit_code == 0
        assert "Filtered" in result.stdout

    def test_filter_select_columns(self, sample_excel_file: Path):
        """Test selecting specific columns."""
        result = runner.invoke(app, ["filter", str(sample_excel_file), "age > 25", "--columns", "name,age"])

        assert result.exit_code == 0
        assert "Filtered" in result.stdout

    def test_filter_csv_format(self, sample_excel_file: Path):
        """Test CSV output format."""
        result = runner.invoke(app, ["filter", str(sample_excel_file), "age > 30", "--format", "csv"])

        assert result.exit_code == 0
        assert "," in result.stdout or "name,age" in result.stdout

    def test_filter_json_format(self, sample_excel_file: Path):
        """Test JSON output format."""
        result = runner.invoke(app, ["filter", str(sample_excel_file), "age > 30", "--format", "json"])

        assert result.exit_code == 0
        assert "[" in result.stdout or "{" in result.stdout

    def test_filter_dry_run(self, sample_excel_file: Path):
        """Test dry-run mode."""
        result = runner.invoke(app, ["filter", str(sample_excel_file), "age > 30", "--dry-run"])

        assert result.exit_code == 0
        assert "Would filter" in result.stdout

    def test_filter_no_matches(self, sample_excel_file: Path):
        """Test filter with no matching rows."""
        result = runner.invoke(app, ["filter", str(sample_excel_file), "age > 100"])

        assert result.exit_code == 0
        assert "No rows match" in result.stdout

    def test_filter_all_match(self, sample_excel_file: Path):
        """Test filter where all rows match."""
        result = runner.invoke(app, ["filter", str(sample_excel_file), "age > 0"])

        assert result.exit_code == 0
        assert "Filtered 10 of 10 rows" in result.stdout

    def test_filter_invalid_column(self, sample_excel_file: Path):
        """Test invalid column name."""
        result = runner.invoke(app, ["filter", str(sample_excel_file), "invalid_col > 30"])

        assert result.exit_code == 1

    def test_filter_invalid_columns_param(self, sample_excel_file: Path):
        """Test invalid columns parameter."""
        result = runner.invoke(app, ["filter", str(sample_excel_file), "age > 25", "--columns", "invalid,age"])

        assert result.exit_code == 1

    def test_filter_with_nulls(self, file_with_nulls: Path):
        """Test filtering with NULL values."""
        result = runner.invoke(app, ["filter", str(file_with_nulls), "name.isna()"])

        assert result.exit_code == 0
        assert "Filtered 2 of 5 rows" in result.stdout

    def test_filter_with_not_null(self, file_with_nulls: Path):
        """Test filtering with NOT NULL."""
        result = runner.invoke(app, ["filter", str(file_with_nulls), "name.notna()"])

        assert result.exit_code == 0
        assert "Filtered 3 of 5 rows" in result.stdout

    def test_filter_is_none_syntax(self, file_with_nulls: Path):
        """Test 'is None' syntax conversion."""
        result = runner.invoke(app, ["filter", str(file_with_nulls), "name is None"])

        assert result.exit_code == 0
        assert "Filtered 2 of 5 rows" in result.stdout

    def test_filter_csv_input(self, sample_csv_file: Path):
        """Test filtering CSV file."""
        result = runner.invoke(app, ["filter", str(sample_csv_file), "price > 20"])

        assert result.exit_code == 0
        assert "Filtered" in result.stdout

    def test_filter_complex_nested(self, sample_excel_file: Path):
        """Test complex nested conditions."""
        result = runner.invoke(app, ["filter", str(sample_excel_file), "(age > 30 and city == 'Berlin') or (age > 35 and city == 'Athens')"])

        assert result.exit_code == 0
        assert "Filtered" in result.stdout

    def test_filter_nonexistent_file(self):
        """Test filter on non-existent file."""
        result = runner.invoke(app, ["filter", "missing.xlsx", "age > 30"])

        assert result.exit_code == 1

    def test_filter_empty_file(self, empty_file: Path):
        """Test filter on empty file."""
        result = runner.invoke(app, ["filter", str(empty_file), "age > 30"])

        assert result.exit_code == 0
        assert "File is empty" in result.stdout

    def test_filter_unbalanced_parentheses(self, sample_excel_file: Path):
        """Test unbalanced parentheses."""
        result = runner.invoke(app, ["filter", str(sample_excel_file), "(age > 30"])

        assert result.exit_code == 1

    def test_filter_dangerous_pattern(self, sample_excel_file: Path):
        """Test dangerous pattern rejection."""
        result = runner.invoke(app, ["filter", str(sample_excel_file), "__import__('os')"])

        assert result.exit_code == 1

    def test_filter_help(self):
        """Test filter command help."""
        result = runner.invoke(app, ["filter", "--help"])

        assert result.exit_code == 0
        assert "Filter rows" in result.stdout
        assert "condition" in result.stdout
