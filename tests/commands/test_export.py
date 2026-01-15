"""Unit tests for export command.

Tests for the export command that converts data to various formats.
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
    """Create a sample data file for export testing."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "value": [100.5, 200.75, 300.25],
            "active": [True, False, True],
        }
    )
    file_path = tmp_path / "data.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def csv_file_for_export(tmp_path: Path) -> Path:
    """Create a CSV file for export testing."""
    df = pd.DataFrame(
        {
            "product": ["Apple", "Banana", "Cherry"],
            "price": [1.5, 2.0, 3.5],
            "stock": [10, 20, 15],
        }
    )
    file_path = tmp_path / "data.csv"
    df.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def empty_file(tmp_path: Path) -> Path:
    """Create an empty DataFrame file."""
    df = pd.DataFrame()
    file_path = tmp_path / "empty.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


# =============================================================================
# Export Command Tests
# =============================================================================


class TestExportCommand:
    """Tests for the export command."""

    def test_export_to_csv(self, sample_data_file: Path, tmp_path: Path):
        """Test export to CSV format."""
        output_path = tmp_path / "output.csv"
        result = runner.invoke(app, [
            "export", str(sample_data_file),
            "--format", "csv",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Exported 3 rows to" in result.stdout
        assert "Format: csv" in result.stdout
        assert output_path.exists()

    def test_export_to_json(self, sample_data_file: Path, tmp_path: Path):
        """Test export to JSON format."""
        output_path = tmp_path / "output.json"
        result = runner.invoke(app, [
            "export", str(sample_data_file),
            "--format", "json",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Exported 3 rows to" in result.stdout
        assert "Format: json" in result.stdout
        assert output_path.exists()

    def test_export_to_tsv(self, sample_data_file: Path, tmp_path: Path):
        """Test export to TSV format."""
        output_path = tmp_path / "output.tsv"
        result = runner.invoke(app, [
            "export", str(sample_data_file),
            "--format", "tsv",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Exported 3 rows to" in result.stdout
        assert "Format: tsv" in result.stdout
        assert output_path.exists()

    def test_export_to_html(self, sample_data_file: Path, tmp_path: Path):
        """Test export to HTML format."""
        output_path = tmp_path / "output.html"
        result = runner.invoke(app, [
            "export", str(sample_data_file),
            "--format", "html",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Exported 3 rows to" in result.stdout
        assert "Format: html" in result.stdout
        assert output_path.exists()

    def test_export_to_markdown(self, sample_data_file: Path, tmp_path: Path):
        """Test export to Markdown format."""
        output_path = tmp_path / "output.md"
        result = runner.invoke(app, [
            "export", str(sample_data_file),
            "--format", "markdown",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Exported 3 rows to" in result.stdout
        assert "Format: markdown" in result.stdout
        assert output_path.exists()

    def test_export_with_custom_delimiter(self, sample_data_file: Path, tmp_path: Path):
        """Test export with custom delimiter."""
        output_path = tmp_path / "output.csv"
        result = runner.invoke(app, [
            "export", str(sample_data_file),
            "--format", "csv",
            "--delimiter", ";",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Delimiter: ';'" in result.stdout
        assert output_path.exists()

    def test_export_with_index(self, sample_data_file: Path, tmp_path: Path):
        """Test export with index included."""
        output_path = tmp_path / "output.csv"
        result = runner.invoke(app, [
            "export", str(sample_data_file),
            "--format", "csv",
            "--index",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert output_path.exists()

    def test_export_with_float_format(self, sample_data_file: Path, tmp_path: Path):
        """Test export with float formatting."""
        output_path = tmp_path / "output.csv"
        result = runner.invoke(app, [
            "export", str(sample_data_file),
            "--format", "csv",
            "--float-format", "%.1f",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert output_path.exists()

    def test_export_with_encoding(self, sample_data_file: Path, tmp_path: Path):
        """Test export with custom encoding."""
        output_path = tmp_path / "output.csv"
        result = runner.invoke(app, [
            "export", str(sample_data_file),
            "--format", "csv",
            "--encoding", "utf-8",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Encoding: utf-8" in result.stdout
        assert output_path.exists()

    def test_export_from_csv(self, csv_file_for_export: Path, tmp_path: Path):
        """Test export from CSV file."""
        output_path = tmp_path / "output.json"
        result = runner.invoke(app, [
            "export", str(csv_file_for_export),
            "--format", "json",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert output_path.exists()

    def test_export_specific_sheet(self, sample_data_file: Path, tmp_path: Path):
        """Test export from specific sheet."""
        output_path = tmp_path / "output.csv"
        result = runner.invoke(app, [
            "export", str(sample_data_file),
            "--format", "csv",
            "--sheet", "Sheet1",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0

    def test_export_invalid_format(self, sample_data_file: Path):
        """Test export with invalid format."""
        output_path = "output.xml"
        result = runner.invoke(app, [
            "export", str(sample_data_file),
            "--format", "xml",
            "--output", output_path
        ])

        assert result.exit_code == 1
        assert "Invalid format" in result.stdout or "Valid formats" in result.stdout

    def test_export_invalid_json_orient(self, sample_data_file: Path, tmp_path: Path):
        """Test export with invalid JSON orientation."""
        output_path = tmp_path / "output.json"
        result = runner.invoke(app, [
            "export", str(sample_data_file),
            "--format", "json",
            "--orient", "invalid",
            "--output", str(output_path)
        ])

        assert result.exit_code == 1
        assert "Invalid orient" in result.stdout or "Valid orients" in result.stdout

    def test_export_empty_file(self, empty_file: Path):
        """Test export on empty file."""
        result = runner.invoke(app, [
            "export", str(empty_file),
            "--format", "csv",
            "--output", "output.csv"
        ])

        assert result.exit_code == 0
        assert "empty" in result.stdout.lower()

    def test_export_nonexistent_file(self):
        """Test export on non-existent file."""
        result = runner.invoke(app, [
            "export", "missing.xlsx",
            "--format", "csv",
            "--output", "output.csv"
        ])

        assert result.exit_code == 1
        assert "File not found" in result.stdout or "not found" in result.stderr

    def test_export_help(self):
        """Test export command help."""
        result = runner.invoke(app, ["export", "--help"])

        assert result.exit_code == 0
        assert "Export" in result.stdout or "export" in result.stdout
