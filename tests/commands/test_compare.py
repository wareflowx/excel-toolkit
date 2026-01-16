"""Unit tests for compare command.

Tests for the compare command that compares two files or sheets.
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
def baseline_file(tmp_path: Path) -> Path:
    """Create a baseline file for comparison."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "value": [100, 200, 150, 300, 250],
            "status": ["active", "inactive", "active", "active", "inactive"],
        }
    )
    file_path = tmp_path / "baseline.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def modified_file(tmp_path: Path) -> Path:
    """Create a modified file for comparison."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 6],
            "name": ["Alice", "Bob", "Charles", "David", "Frank"],
            "value": [100, 250, 150, 300, 180],
            "status": ["active", "active", "active", "active", "active"],
        }
    )
    file_path = tmp_path / "modified.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def identical_file(tmp_path: Path) -> Path:
    """Create an identical file to baseline."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "value": [100, 200, 150, 300, 250],
            "status": ["active", "inactive", "active", "active", "inactive"],
        }
    )
    file_path = tmp_path / "identical.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def csv_file1(tmp_path: Path) -> Path:
    """Create a CSV file for comparison."""
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["A", "B", "C"], "value": [10, 20, 30]})
    file_path = tmp_path / "file1.csv"
    df.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def csv_file2(tmp_path: Path) -> Path:
    """Create a CSV file for comparison."""
    df = pd.DataFrame({"id": [1, 2, 4], "name": ["A", "B", "D"], "value": [10, 25, 30]})
    file_path = tmp_path / "file2.csv"
    df.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def empty_file1(tmp_path: Path) -> Path:
    """Create an empty file."""
    df = pd.DataFrame()
    file_path = tmp_path / "empty1.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def empty_file2(tmp_path: Path) -> Path:
    """Create another empty file."""
    df = pd.DataFrame()
    file_path = tmp_path / "empty2.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def data_with_nulls1(tmp_path: Path) -> Path:
    """Create a file with null values."""
    df = pd.DataFrame({"id": [1, 2, 3], "value": [100, None, 150], "name": ["A", "B", "C"]})
    file_path = tmp_path / "nulls1.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def data_with_nulls2(tmp_path: Path) -> Path:
    """Create a file with different null values."""
    df = pd.DataFrame({"id": [1, 2, 3], "value": [100, 200, None], "name": ["A", "B", "C"]})
    file_path = tmp_path / "nulls2.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


# =============================================================================
# Compare Command Tests
# =============================================================================


class TestCompareCommand:
    """Tests for the compare command."""

    def test_compare_with_differences(self, baseline_file: Path, modified_file: Path):
        """Test comparing two files with differences."""
        result = runner.invoke(app, ["compare", str(baseline_file), str(modified_file)])

        assert result.exit_code == 0
        assert "Added rows:" in result.stdout
        assert "Deleted rows:" in result.stdout
        assert "Modified rows:" in result.stdout
        assert "Total differences:" in result.stdout

    def test_compare_identical_files(self, baseline_file: Path, identical_file: Path):
        """Test comparing identical files."""
        result = runner.invoke(app, ["compare", str(baseline_file), str(identical_file)])

        assert result.exit_code == 0
        assert "No differences found" in result.stdout
        assert "files are identical" in result.stdout

    def test_compare_with_key_column(self, baseline_file: Path, modified_file: Path):
        """Test comparing files with key column."""
        result = runner.invoke(
            app, ["compare", str(baseline_file), str(modified_file), "--key-columns", "id"]
        )

        assert result.exit_code == 0
        assert "Added rows:" in result.stdout
        assert "Deleted rows:" in result.stdout

    def test_compare_with_multiple_key_columns(self, tmp_path: Path):
        """Test comparing files with multiple key columns."""
        df1 = pd.DataFrame(
            {
                "year": [2023, 2023, 2024],
                "quarter": ["Q1", "Q2", "Q1"],
                "value": [100, 200, 150],
            }
        )
        df2 = pd.DataFrame(
            {
                "year": [2023, 2023, 2024],
                "quarter": ["Q1", "Q2", "Q2"],
                "value": [100, 200, 180],
            }
        )
        file1 = tmp_path / "data1.xlsx"
        file2 = tmp_path / "data2.xlsx"
        df1.to_excel(file1, index=False)
        df2.to_excel(file2, index=False)

        result = runner.invoke(
            app, ["compare", str(file1), str(file2), "--key-columns", "year,quarter"]
        )

        assert result.exit_code == 0

    def test_compare_with_output(self, baseline_file: Path, modified_file: Path, tmp_path: Path):
        """Test comparing files with output."""
        output_path = tmp_path / "differences.xlsx"
        result = runner.invoke(
            app, ["compare", str(baseline_file), str(modified_file), "--output", str(output_path)]
        )

        assert result.exit_code == 0
        assert "Written to:" in result.stdout
        assert output_path.exists()

    def test_compare_diffs_only(self, baseline_file: Path, modified_file: Path):
        """Test comparing files with diffs-only flag."""
        result = runner.invoke(
            app, ["compare", str(baseline_file), str(modified_file), "--diffs-only"]
        )

        assert result.exit_code == 0

    def test_compare_csv_files(self, csv_file1: Path, csv_file2: Path):
        """Test comparing CSV files."""
        result = runner.invoke(app, ["compare", str(csv_file1), str(csv_file2)])

        assert result.exit_code == 0
        assert "Total differences:" in result.stdout

    def test_compare_csv_with_key(self, csv_file1: Path, csv_file2: Path):
        """Test comparing CSV files with key column."""
        result = runner.invoke(
            app, ["compare", str(csv_file1), str(csv_file2), "--key-columns", "id"]
        )

        assert result.exit_code == 0

    def test_compare_excel_specific_sheets(self, baseline_file: Path, modified_file: Path):
        """Test comparing specific sheets."""
        result = runner.invoke(
            app,
            [
                "compare",
                str(baseline_file),
                str(modified_file),
                "--sheet1", "Sheet1",
                "--sheet2", "Sheet1",
            ],
        )

        assert result.exit_code == 0

    def test_compare_both_empty_files(self, empty_file1: Path, empty_file2: Path):
        """Test comparing two empty files."""
        result = runner.invoke(app, ["compare", str(empty_file1), str(empty_file2)])

        assert result.exit_code == 0
        assert "empty" in result.stdout.lower()

    def test_compare_first_file_empty(self, empty_file1: Path, baseline_file: Path):
        """Test comparing when first file is empty."""
        result = runner.invoke(app, ["compare", str(empty_file1), str(baseline_file)])

        assert result.exit_code == 0
        assert "File1 is empty" in result.stdout

    def test_compare_second_file_empty(self, baseline_file: Path, empty_file1: Path):
        """Test comparing when second file is empty."""
        result = runner.invoke(app, ["compare", str(baseline_file), str(empty_file1)])

        assert result.exit_code == 0
        assert "File2 is empty" in result.stdout

    def test_compare_with_nulls(self, data_with_nulls1: Path, data_with_nulls2: Path):
        """Test comparing files with null values."""
        result = runner.invoke(
            app, ["compare", str(data_with_nulls1), str(data_with_nulls2), "--key-columns", "id"]
        )

        assert result.exit_code == 0

    def test_compare_nonexistent_file1(self, baseline_file: Path):
        """Test comparing with non-existent first file."""
        result = runner.invoke(app, ["compare", "missing1.xlsx", str(baseline_file)])

        assert result.exit_code == 1

    def test_compare_nonexistent_file2(self, baseline_file: Path):
        """Test comparing with non-existent second file."""
        result = runner.invoke(app, ["compare", str(baseline_file), "missing2.xlsx"])

        assert result.exit_code == 1

    def test_compare_invalid_key_column_file1(self, baseline_file: Path, modified_file: Path):
        """Test comparing with invalid key column in file1."""
        result = runner.invoke(
            app, ["compare", str(baseline_file), str(modified_file), "--key-columns", "invalid_column"]
        )

        assert result.exit_code == 1

    def test_compare_help(self):
        """Test compare command help."""
        result = runner.invoke(app, ["compare", "--help"])

        assert result.exit_code == 0
        assert "Compare two files" in result.stdout
        assert "--key-columns" in result.stdout
        assert "--output" in result.stdout

    def test_compare_shows_diff_status(self, baseline_file: Path, modified_file: Path):
        """Test that result shows diff status column."""
        result = runner.invoke(app, ["compare", str(baseline_file), str(modified_file), "--key-columns", "id"])

        assert result.exit_code == 0
        # Should have some differences
        assert "Total differences:" in result.stdout

    def test_compare_without_key_column(self, baseline_file: Path, modified_file: Path):
        """Test comparing files without key column (row by row)."""
        result = runner.invoke(app, ["compare", str(baseline_file), str(modified_file)])

        assert result.exit_code == 0

    def test_compare_missing_file1(self):
        """Test compare with missing first file argument."""
        result = runner.invoke(app, ["compare", str(modified_file)])

        assert result.exit_code != 0

    def test_compare_missing_file2(self):
        """Test compare with missing second file argument."""
        result = runner.invoke(app, ["compare", str(baseline_file)])

        assert result.exit_code != 0
