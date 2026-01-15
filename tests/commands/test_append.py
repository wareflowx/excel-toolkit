"""Unit tests for append command.

Tests for the append command that concatenates datasets vertically.
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
def main_file(tmp_path: Path) -> Path:
    """Create main file for appending."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "value": [100, 200, 300],
        }
    )
    file_path = tmp_path / "main.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def additional_file_1(tmp_path: Path) -> Path:
    """Create first additional file."""
    df = pd.DataFrame(
        {
            "id": [4, 5],
            "name": ["David", "Eve"],
            "value": [400, 500],
        }
    )
    file_path = tmp_path / "additional1.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def additional_file_2(tmp_path: Path) -> Path:
    """Create second additional file."""
    df = pd.DataFrame(
        {
            "id": [6, 7],
            "name": ["Frank", "Grace"],
            "value": [600, 700],
        }
    )
    file_path = tmp_path / "additional2.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def csv_main_file(tmp_path: Path) -> Path:
    """Create CSV main file."""
    df = pd.DataFrame(
        {
            "product": ["A", "B"],
            "price": [10, 20],
        }
    )
    file_path = tmp_path / "main.csv"
    df.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def csv_additional_file(tmp_path: Path) -> Path:
    """Create CSV additional file."""
    df = pd.DataFrame(
        {
            "product": ["C", "D"],
            "price": [30, 40],
        }
    )
    file_path = tmp_path / "additional.csv"
    df.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def mismatched_columns_file(tmp_path: Path) -> Path:
    """Create file with mismatched columns."""
    df = pd.DataFrame(
        {
            "id": [8, 9],
            "name": ["Henry", "Ivy"],
            "value": [800, 900],
            "extra": ["x", "y"],  # Extra column
        }
    )
    file_path = tmp_path / "mismatched.xlsx"
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
# Append Command Tests
# =============================================================================


class TestAppendCommand:
    """Tests for the append command."""

    def test_append_single_file(self, main_file: Path, additional_file_1: Path, tmp_path: Path):
        """Test appending a single file."""
        output_path = tmp_path / "output.xlsx"
        result = runner.invoke(app, [
            "append", str(main_file), str(additional_file_1),
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Main file rows: 3" in result.stdout
        assert "Appended rows: 2" in result.stdout
        assert "Total rows: 5" in result.stdout
        assert output_path.exists()

    def test_append_multiple_files(self, main_file: Path, additional_file_1: Path, additional_file_2: Path, tmp_path: Path):
        """Test appending multiple files."""
        output_path = tmp_path / "output.xlsx"
        result = runner.invoke(app, [
            "append", str(main_file), str(additional_file_1), str(additional_file_2),
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Main file rows: 3" in result.stdout
        assert "Appended rows: 4" in result.stdout
        assert "Total rows: 7" in result.stdout
        assert output_path.exists()

    def test_append_with_ignore_index(self, main_file: Path, additional_file_1: Path, tmp_path: Path):
        """Test append with index reset."""
        output_path = tmp_path / "output.xlsx"
        result = runner.invoke(app, [
            "append", str(main_file), str(additional_file_1),
            "--ignore-index",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert output_path.exists()

    def test_append_with_sort(self, main_file: Path, additional_file_1: Path, tmp_path: Path):
        """Test append with sorting."""
        output_path = tmp_path / "output.xlsx"
        result = runner.invoke(app, [
            "append", str(main_file), str(additional_file_1),
            "--sort",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert output_path.exists()

    def test_append_csv_files(self, csv_main_file: Path, csv_additional_file: Path, tmp_path: Path):
        """Test appending CSV files."""
        output_path = tmp_path / "output.csv"
        result = runner.invoke(app, [
            "append", str(csv_main_file), str(csv_additional_file),
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Total rows: 4" in result.stdout
        assert output_path.exists()

    def test_append_mismatched_columns(self, main_file: Path, mismatched_columns_file: Path, tmp_path: Path):
        """Test append with mismatched columns."""
        output_path = tmp_path / "output.xlsx"
        result = runner.invoke(app, [
            "append", str(main_file), str(mismatched_columns_file),
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Column mismatch" in result.stdout or "mismatch" in result.stdout.lower() or output_path.exists()

    def test_append_empty_main_file(self, empty_file: Path, additional_file_1: Path):
        """Test append with empty main file."""
        result = runner.invoke(app, [
            "append", str(empty_file), str(additional_file_1)
        ])

        assert result.exit_code == 0
        assert "empty" in result.stdout.lower()

    def test_append_nonexistent_main_file(self, additional_file_1: Path):
        """Test append with non-existent main file."""
        result = runner.invoke(app, [
            "append", "missing.xlsx", str(additional_file_1)
        ])

        assert result.exit_code == 1
        assert "Main file not found" in result.stdout or "File not found" in result.stdout or "not found" in result.stderr

    def test_append_nonexistent_additional_file(self, main_file: Path):
        """Test append with non-existent additional file."""
        result = runner.invoke(app, [
            "append", str(main_file), "missing.xlsx"
        ])

        assert result.exit_code == 1
        assert "File not found" in result.stdout or "not found" in result.stderr

    def test_append_specific_sheets(self, main_file: Path, additional_file_1: Path, tmp_path: Path):
        """Test append with specific sheets."""
        output_path = tmp_path / "output.xlsx"
        result = runner.invoke(app, [
            "append", str(main_file), str(additional_file_1),
            "--sheet", "Sheet1",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0

    def test_append_help(self):
        """Test append command help."""
        result = runner.invoke(app, ["append", "--help"])

        assert result.exit_code == 0
        assert "Append" in result.stdout or "append" in result.stdout
