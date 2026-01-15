"""Unit tests for stats command.

Tests for the stats command that computes statistical summaries.
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner
import pandas as pd
import json

from excel_toolkit.cli import app

# Initialize CLI test runner
runner = CliRunner()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_numeric_file(tmp_path: Path) -> Path:
    """Create a file with numeric data for testing."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "age": [25, 30, 35, 28, 32, 27, 38, 29, 31, 26],
            "salary": [50000, 60000, 70000, 55000, 65000, 52000, 75000, 58000, 62000, 48000],
            "score": [85.5, 92.3, 78.9, 95.2, 88.7, 91.4, 82.6, 89.3, 94.1, 87.8],
        }
    )
    file_path = tmp_path / "numeric.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def sample_categorical_file(tmp_path: Path) -> Path:
    """Create a file with categorical data for testing."""
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "Alice", "Bob", "Charlie", "Alice"],
            "city": ["Paris", "London", "Berlin", "Paris", "London", "Paris", "Berlin"],
            "status": ["active", "inactive", "active", "active", "inactive", "active", "pending"],
        }
    )
    file_path = tmp_path / "categorical.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def sample_datetime_file(tmp_path: Path) -> Path:
    """Create a file with datetime data for testing."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "date": pd.to_datetime(["2023-01-15", "2023-03-20", "2023-02-10", "2023-04-05", "2023-05-12"]),
            "timestamp": pd.to_datetime([
                "2023-01-15 10:30:00",
                "2023-03-20 14:45:00",
                "2023-02-10 09:15:00",
                "2023-04-05 16:20:00",
                "2023-05-12 11:00:00"
            ]),
        }
    )
    file_path = tmp_path / "datetime.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def file_with_nulls(tmp_path: Path) -> Path:
    """Create a file with null values."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "value": [100.0, None, 300.0, 400.0, None],
            "category": ["A", "B", None, "A", "B"],
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
def single_value_file(tmp_path: Path) -> Path:
    """Create a file with a single value."""
    df = pd.DataFrame({"value": [42.0]})
    file_path = tmp_path / "single.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def identical_values_file(tmp_path: Path) -> Path:
    """Create a file where all values are identical."""
    df = pd.DataFrame({"value": [10.0, 10.0, 10.0, 10.0, 10.0]})
    file_path = tmp_path / "identical.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


# =============================================================================
# Stats Command Tests
# =============================================================================


class TestStatsCommand:
    """Tests for the stats command."""

    def test_stats_single_numeric_column(self, sample_numeric_file: Path):
        """Test statistics for a single numeric column."""
        result = runner.invoke(app, ["stats", str(sample_numeric_file), "--column", "age"])

        assert result.exit_code == 0
        assert "Statistics for column: age" in result.stdout or "age" in result.stdout

    def test_stats_all_numeric_columns(self, sample_numeric_file: Path):
        """Test statistics for all numeric columns."""
        result = runner.invoke(app, ["stats", str(sample_numeric_file), "--all-columns"])

        assert result.exit_code == 0
        assert "Statistical Summary" in result.stdout or "age" in result.stdout

    def test_stats_categorical_column(self, sample_categorical_file: Path):
        """Test statistics for categorical column."""
        result = runner.invoke(app, ["stats", str(sample_categorical_file), "--column", "name"])

        assert result.exit_code == 0
        assert "Unique" in result.stdout or "Top" in result.stdout

    def test_stats_datetime_column(self, sample_datetime_file: Path):
        """Test statistics for datetime column."""
        result = runner.invoke(app, ["stats", str(sample_datetime_file), "--column", "date"])

        assert result.exit_code == 0
        assert "Min" in result.stdout or "Max" in result.stdout or "Range" in result.stdout

    def test_stats_custom_percentiles(self, sample_numeric_file: Path):
        """Test statistics with custom percentiles."""
        result = runner.invoke(app, [
            "stats", str(sample_numeric_file),
            "--column", "salary",
            "--percentiles", "10,25,50,75,90,95,99"
        ])

        assert result.exit_code == 0
        assert "Statistics for column: salary" in result.stdout or "salary" in result.stdout

    def test_stats_with_nulls(self, file_with_nulls: Path):
        """Test statistics with missing values."""
        result = runner.invoke(app, ["stats", str(file_with_nulls), "--column", "value"])

        assert result.exit_code == 0
        assert "Missing" in result.stdout

    def test_stats_json_format(self, sample_numeric_file: Path):
        """Test JSON output format."""
        result = runner.invoke(app, [
            "stats", str(sample_numeric_file),
            "--column", "age",
            "--format", "json"
        ])

        assert result.exit_code == 0
        # Parse JSON to verify it's valid
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pytest.fail("Invalid JSON output")

    def test_stats_csv_format(self, sample_numeric_file: Path):
        """Test CSV output format."""
        result = runner.invoke(app, [
            "stats", str(sample_numeric_file),
            "--column", "age",
            "--format", "csv"
        ])

        assert result.exit_code == 0
        assert "," in result.stdout

    def test_stats_with_output(self, sample_numeric_file: Path, tmp_path: Path):
        """Test statistics with output file."""
        output_path = tmp_path / "stats.json"
        result = runner.invoke(app, [
            "stats", str(sample_numeric_file),
            "--column", "salary",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Written to:" in result.stdout
        assert output_path.exists()

    def test_stats_specific_sheet(self, sample_numeric_file: Path):
        """Test statistics for specific sheet."""
        result = runner.invoke(app, [
            "stats", str(sample_numeric_file),
            "--column", "age",
            "--sheet", "Sheet1"
        ])

        assert result.exit_code == 0

    def test_stats_include_categorical(self, sample_categorical_file: Path):
        """Test including categorical columns."""
        result = runner.invoke(app, [
            "stats", str(sample_categorical_file),
            "--all-columns",
            "--include", "categorical"
        ])

        assert result.exit_code == 0

    def test_stats_include_datetime(self, sample_datetime_file: Path):
        """Test including datetime columns."""
        result = runner.invoke(app, [
            "stats", str(sample_datetime_file),
            "--all-columns",
            "--include", "datetime"
        ])

        assert result.exit_code == 0

    def test_stats_include_all_types(self, sample_numeric_file: Path):
        """Test including all column types."""
        result = runner.invoke(app, [
            "stats", str(sample_numeric_file),
            "--all-columns",
            "--include", "all"
        ])

        assert result.exit_code == 0

    def test_stats_empty_file(self, empty_file: Path):
        """Test statistics on empty file."""
        result = runner.invoke(app, ["stats", str(empty_file), "--column", "value"])

        assert result.exit_code == 0
        assert "File is empty" in result.stdout

    def test_stats_single_value(self, single_value_file: Path):
        """Test statistics with single value."""
        result = runner.invoke(app, ["stats", str(single_value_file), "--column", "value"])

        assert result.exit_code == 0

    def test_stats_identical_values(self, identical_values_file: Path):
        """Test statistics where all values are identical."""
        result = runner.invoke(app, ["stats", str(identical_values_file), "--column", "value"])

        assert result.exit_code == 0

    def test_stats_invalid_column(self, sample_numeric_file: Path):
        """Test statistics on non-existent column."""
        result = runner.invoke(app, ["stats", str(sample_numeric_file), "--column", "invalid"])

        assert result.exit_code == 1

    def test_stats_invalid_percentiles(self, sample_numeric_file: Path):
        """Test statistics with invalid percentiles."""
        result = runner.invoke(app, [
            "stats", str(sample_numeric_file),
            "--column", "age",
            "--percentiles", "invalid"
        ])

        assert result.exit_code == 1

    def test_stats_percentile_out_of_range(self, sample_numeric_file: Path):
        """Test statistics with percentile out of range."""
        result = runner.invoke(app, [
            "stats", str(sample_numeric_file),
            "--column", "age",
            "--percentiles", "150"
        ])

        assert result.exit_code == 1

    def test_stats_invalid_include_type(self, sample_numeric_file: Path):
        """Test statistics with invalid include type."""
        result = runner.invoke(app, [
            "stats", str(sample_numeric_file),
            "--column", "age",
            "--include", "invalid"
        ])

        assert result.exit_code == 1

    def test_stats_nonexistent_file(self):
        """Test statistics on non-existent file."""
        result = runner.invoke(app, ["stats", "missing.xlsx", "--column", "age"])

        assert result.exit_code == 1

    def test_stats_help(self):
        """Test stats command help."""
        result = runner.invoke(app, ["stats", "--help"])

        assert result.exit_code == 0
        assert "Compute statistical" in result.stdout
        assert "--column" in result.stdout
