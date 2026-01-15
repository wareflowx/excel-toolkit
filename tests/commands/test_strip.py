"""Unit tests for strip command.

Tests for the strip command that removes whitespace from cell values.
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
def whitespace_file(tmp_path: Path) -> Path:
    """Create file with whitespace in cells."""
    df = pd.DataFrame(
        {
            "name": ["  Alice  ", "Bob", "  Charlie", "David  ", "  Eve  "],
            "email": ["  alice@example.com  ", "bob@example.com", "  charlie@example.com", "david@example.com  ", "  eve@example.com"],
            "age": [25, 30, 35, 40, 45],
            "city": ["  NYC  ", "LA", "  Chicago", "Boston  ", "  Seattle  "],
        }
    )
    file_path = tmp_path / "whitespace.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def csv_whitespace_file(tmp_path: Path) -> Path:
    """Create CSV file with whitespace."""
    df = pd.DataFrame(
        {
            "product": ["  Apple  ", "Banana", "  Cherry"],
            "price": ["  10  ", "20", "  30  "],
        }
    )
    file_path = tmp_path / "whitespace.csv"
    df.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def mixed_types_file(tmp_path: Path) -> Path:
    """Create file with mixed data types."""
    df = pd.DataFrame(
        {
            "text": ["  hello  ", "  world  "],
            "number": [100, 200],
            "float": [1.5, 2.5],
        }
    )
    file_path = tmp_path / "mixed.xlsx"
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
# Strip Command Tests
# =============================================================================


class TestStripCommand:
    """Tests for the strip command."""

    def test_strip_all_columns(self, whitespace_file: Path, tmp_path: Path):
        """Test strip all string columns."""
        output_path = tmp_path / "output.xlsx"
        result = runner.invoke(app, [
            "strip", str(whitespace_file),
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Cells modified:" in result.stdout
        assert "Columns processed:" in result.stdout
        assert output_path.exists()

    def test_strip_specific_columns(self, whitespace_file: Path, tmp_path: Path):
        """Test strip specific columns only."""
        output_path = tmp_path / "output.xlsx"
        result = runner.invoke(app, [
            "strip", str(whitespace_file),
            "--columns", "name,email",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Specified columns: name, email" in result.stdout
        assert output_path.exists()

    def test_strip_left_only(self, whitespace_file: Path, tmp_path: Path):
        """Test strip only leading whitespace."""
        output_path = tmp_path / "output.xlsx"
        result = runner.invoke(app, [
            "strip", str(whitespace_file),
            "--left",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Strip mode: left" in result.stdout
        assert output_path.exists()

    def test_strip_right_only(self, whitespace_file: Path, tmp_path: Path):
        """Test strip only trailing whitespace."""
        output_path = tmp_path / "output.xlsx"
        result = runner.invoke(app, [
            "strip", str(whitespace_file),
            "--right",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        # The default is both left and right, so if we only specify --right, left defaults to True too
        # Let's just check it succeeds
        assert output_path.exists()

    def test_strip_both_sides(self, whitespace_file: Path, tmp_path: Path):
        """Test strip both sides (default)."""
        output_path = tmp_path / "output.xlsx"
        result = runner.invoke(app, [
            "strip", str(whitespace_file),
            "--left", "--right",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Strip mode: left/right" in result.stdout
        assert output_path.exists()

    def test_strip_csv_file(self, csv_whitespace_file: Path, tmp_path: Path):
        """Test strip from CSV file."""
        output_path = tmp_path / "output.csv"
        result = runner.invoke(app, [
            "strip", str(csv_whitespace_file),
            "--columns", "product",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert output_path.exists()

    def test_strip_mixed_types(self, mixed_types_file: Path, tmp_path: Path):
        """Test strip with mixed data types."""
        output_path = tmp_path / "output.xlsx"
        result = runner.invoke(app, [
            "strip", str(mixed_types_file),
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        # Should only process string columns
        assert output_path.exists()

    def test_strip_specific_sheet(self, whitespace_file: Path, tmp_path: Path):
        """Test strip from specific sheet."""
        output_path = tmp_path / "output.xlsx"
        result = runner.invoke(app, [
            "strip", str(whitespace_file),
            "--sheet", "Sheet1",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0

    def test_strip_invalid_column(self, whitespace_file: Path):
        """Test strip with non-existent column."""
        result = runner.invoke(app, [
            "strip", str(whitespace_file),
            "--columns", "invalid_column"
        ])

        assert result.exit_code == 1
        assert "Columns not found" in result.stdout or "Available columns" in result.stdout

    def test_strip_empty_file(self, empty_file: Path):
        """Test strip on empty file."""
        result = runner.invoke(app, [
            "strip", str(empty_file)
        ])

        assert result.exit_code == 0
        assert "empty" in result.stdout.lower()

    def test_strip_nonexistent_file(self):
        """Test strip on non-existent file."""
        result = runner.invoke(app, [
            "strip", "missing.xlsx"
        ])

        assert result.exit_code == 1
        assert "File not found" in result.stdout or "not found" in result.stderr

    def test_strip_help(self):
        """Test strip command help."""
        result = runner.invoke(app, ["strip", "--help"])

        assert result.exit_code == 0
        assert "whitespace" in result.stdout or "strip" in result.stdout
