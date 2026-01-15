"""Unit tests for clean command.

Tests for the clean command that removes whitespace and standardizes case.
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
def messy_data_file(tmp_path: Path) -> Path:
    """Create a file with messy data for testing."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["  Alice  ", "BOB", "  Charlie  ", "DIANA", "  Eve  "],
            "email": ["alice@example.com", "  BOB@EXAMPLE.COM  ", "charlie@example.com", "diana@example.com", "eve@example.com"],
            "city": ["New  York", "los  angeles", "  Chicago  ", "Houston", "  Phoenix  "],
            "phone": ["123-456-7890", " (555) 123-4567 ", "555.987.6543", " 444-555-6666", "777 888 9999"],
        }
    )
    file_path = tmp_path / "messy.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def file_with_special_chars(tmp_path: Path) -> Path:
    """Create a file with special characters."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "text": ["Hello!!!", "World@#$", "Test***Data"],
        }
    )
    file_path = tmp_path / "special.xlsx"
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
def numeric_only_file(tmp_path: Path) -> Path:
    """Create a file with only numeric columns."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "value": [100, 200, 300],
        }
    )
    file_path = tmp_path / "numeric.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


# =============================================================================
# Clean Command Tests
# =============================================================================


class TestCleanCommand:
    """Tests for the clean command."""

    def test_clean_trim(self, messy_data_file: Path):
        """Test trimming whitespace."""
        result = runner.invoke(app, ["clean", str(messy_data_file), "--trim", "--columns", "name"])

        assert result.exit_code == 0
        assert "Cleaned" in result.stdout
        assert "trim" in result.stdout

    def test_clean_lowercase(self, messy_data_file: Path):
        """Test converting to lowercase."""
        result = runner.invoke(app, ["clean", str(messy_data_file), "--lowercase", "--columns", "email"])

        assert result.exit_code == 0
        assert "Cleaned" in result.stdout

    def test_clean_uppercase(self, messy_data_file: Path):
        """Test converting to uppercase."""
        result = runner.invoke(app, ["clean", str(messy_data_file), "--uppercase", "--columns", "city"])

        assert result.exit_code == 0
        assert "Cleaned" in result.stdout

    def test_clean_titlecase(self, messy_data_file: Path):
        """Test converting to title case."""
        result = runner.invoke(app, ["clean", str(messy_data_file), "--titlecase", "--columns", "city"])

        assert result.exit_code == 0
        assert "Cleaned" in result.stdout

    def test_clean_whitespace_normalization(self, messy_data_file: Path):
        """Test normalizing multiple whitespace."""
        result = runner.invoke(app, ["clean", str(messy_data_file), "--whitespace", "--columns", "city"])

        assert result.exit_code == 0
        assert "Cleaned" in result.stdout

    def test_clean_remove_special(self, file_with_special_chars: Path):
        """Test removing special characters."""
        result = runner.invoke(app, ["clean", str(file_with_special_chars), "--remove-special"])

        assert result.exit_code == 0
        assert "Cleaned" in result.stdout

    def test_clean_keep_alphanumeric(self, file_with_special_chars: Path):
        """Test keeping only alphanumeric characters."""
        result = runner.invoke(app, ["clean", str(file_with_special_chars), "--keep-alphanumeric"])

        assert result.exit_code == 0
        assert "Cleaned" in result.stdout

    def test_clean_casefold(self, messy_data_file: Path):
        """Test casefold operation."""
        result = runner.invoke(app, ["clean", str(messy_data_file), "--casefold", "--columns", "email"])

        assert result.exit_code == 0
        assert "Cleaned" in result.stdout

    def test_clean_multiple_operations(self, messy_data_file: Path):
        """Test applying multiple operations."""
        result = runner.invoke(app, [
            "clean", str(messy_data_file),
            "--trim",
            "--lowercase",
            "--whitespace",
            "--columns", "name,city"
        ])

        assert result.exit_code == 0
        assert "Cleaned" in result.stdout

    def test_clean_with_output(self, messy_data_file: Path, tmp_path: Path):
        """Test cleaning with output file."""
        output_path = tmp_path / "cleaned.xlsx"
        result = runner.invoke(app, [
            "clean", str(messy_data_file),
            "--trim",
            "--lowercase",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Written to:" in result.stdout
        assert output_path.exists()

    def test_clean_dry_run(self, messy_data_file: Path):
        """Test dry-run mode."""
        result = runner.invoke(app, [
            "clean", str(messy_data_file),
            "--trim",
            "--lowercase",
            "--dry-run"
        ])

        assert result.exit_code == 0
        assert "Preview" in result.stdout

    def test_clean_all_string_columns(self, messy_data_file: Path):
        """Test cleaning all string columns."""
        result = runner.invoke(app, [
            "clean", str(messy_data_file),
            "--trim"
        ])

        assert result.exit_code == 0
        assert "Cleaned" in result.stdout

    def test_clean_specific_columns(self, messy_data_file: Path):
        """Test cleaning specific columns only."""
        result = runner.invoke(app, [
            "clean", str(messy_data_file),
            "--trim",
            "--lowercase",
            "--columns", "name,email"
        ])

        assert result.exit_code == 0
        assert "Columns: name,email" in result.stdout

    def test_clean_conflicting_lowercase_uppercase(self, messy_data_file: Path):
        """Test conflicting lowercase and uppercase."""
        result = runner.invoke(app, [
            "clean", str(messy_data_file),
            "--lowercase",
            "--uppercase"
        ])

        assert result.exit_code == 1

    def test_clean_conflicting_remove_special_keep_alphanumeric(self, messy_data_file: Path):
        """Test conflicting remove-special and keep-alphanumeric."""
        result = runner.invoke(app, [
            "clean", str(messy_data_file),
            "--remove-special",
            "--keep-alphanumeric"
        ])

        assert result.exit_code == 1

    def test_clean_no_operations_specified(self, messy_data_file: Path):
        """Test clean without specifying any operation."""
        result = runner.invoke(app, ["clean", str(messy_data_file)])

        assert result.exit_code == 1

    def test_clean_empty_file(self, empty_file: Path):
        """Test clean on empty file."""
        result = runner.invoke(app, ["clean", str(empty_file), "--trim"])

        assert result.exit_code == 0
        assert "empty" in result.stdout.lower()

    def test_clean_numeric_only_file(self, numeric_only_file: Path):
        """Test clean on file with only numeric columns."""
        result = runner.invoke(app, ["clean", str(numeric_only_file), "--trim"])

        # Should handle gracefully - no string columns to clean
        assert result.exit_code == 0

    def test_clean_invalid_column(self, messy_data_file: Path):
        """Test clean with non-existent column."""
        result = runner.invoke(app, [
            "clean", str(messy_data_file),
            "--trim",
            "--columns", "nonexistent"
        ])

        assert result.exit_code == 1

    def test_clean_nonexistent_file(self):
        """Test clean on non-existent file."""
        result = runner.invoke(app, ["clean", "missing.xlsx", "--trim"])

        assert result.exit_code == 1

    def test_clean_help(self):
        """Test clean command help."""
        result = runner.invoke(app, ["clean", "--help"])

        assert result.exit_code == 0
        assert "Clean data" in result.stdout
        assert "--trim" in result.stdout
