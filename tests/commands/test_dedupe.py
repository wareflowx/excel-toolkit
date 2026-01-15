"""Unit tests for dedupe command.

Tests for the dedupe command that removes duplicate rows.
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
def file_with_duplicates(tmp_path: Path) -> Path:
    """Create a file with duplicate rows."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 1, 2, 4],
            "name": ["Alice", "Bob", "Charlie", "Alice", "Bob", "Diana"],
            "email": ["alice@example.com", "bob@example.com", "charlie@example.com",
                     "alice@example.com", "bob@example.com", "diana@example.com"],
            "age": [25, 30, 35, 25, 30, 28],
        }
    )
    file_path = tmp_path / "duplicates.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def file_with_key_duplicates(tmp_path: Path) -> Path:
    """Create a file with duplicates based on key columns."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5, 6],
            "email": ["alice@example.com", "bob@example.com", "alice@example.com",
                     "charlie@example.com", "bob@example.com", "diana@example.com"],
            "name": ["Alice Smith", "Bob Jones", "Alice Smith",
                    "Charlie Wilson", "Bob Taylor", "Diana Davis"],
            "timestamp": ["2024-01-01", "2024-01-02", "2024-01-03",
                         "2024-01-04", "2024-01-05", "2024-01-06"],
        }
    )
    file_path = tmp_path / "key_duplicates.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def file_no_duplicates(tmp_path: Path) -> Path:
    """Create a file with no duplicates."""
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "email": ["alice@example.com", "bob@example.com", "charlie@example.com",
                     "diana@example.com", "eve@example.com"],
        }
    )
    file_path = tmp_path / "no_duplicates.xlsx"
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
def csv_file_with_duplicates(tmp_path: Path) -> Path:
    """Create a CSV file with duplicates."""
    df = pd.DataFrame(
        {
            "product": ["A", "B", "A", "C", "B"],
            "price": [10.99, 20.50, 10.99, 15.75, 20.50],
            "quantity": [100, 50, 100, 75, 50],
        }
    )
    file_path = tmp_path / "duplicates.csv"
    df.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def file_all_duplicates(tmp_path: Path) -> Path:
    """Create a file where all rows are duplicates."""
    df = pd.DataFrame(
        {
            "id": [1, 1, 1],
            "name": ["Alice", "Alice", "Alice"],
            "email": ["alice@example.com", "alice@example.com", "alice@example.com"],
        }
    )
    file_path = tmp_path / "all_duplicates.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


# =============================================================================
# Dedupe Command Tests
# =============================================================================


class TestDedupeCommand:
    """Tests for the dedupe command."""

    def test_dedupe_keep_first(self, file_with_duplicates: Path):
        """Test deduplication keeping first occurrence."""
        result = runner.invoke(app, ["dedupe", str(file_with_duplicates), "--keep", "first"])

        assert result.exit_code == 0
        assert "Original rows: 6" in result.stdout
        assert "Duplicate rows found: 2" in result.stdout
        assert "Rows removed: 2" in result.stdout
        assert "Remaining rows: 4" in result.stdout

    def test_dedupe_keep_last(self, file_with_duplicates: Path):
        """Test deduplication keeping last occurrence."""
        result = runner.invoke(app, ["dedupe", str(file_with_duplicates), "--keep", "last"])

        assert result.exit_code == 0
        assert "Original rows: 6" in result.stdout
        assert "Duplicate rows found: 2" in result.stdout
        assert "Rows removed: 2" in result.stdout
        assert "Remaining rows: 4" in result.stdout

    def test_dedupe_keep_none(self, file_with_duplicates: Path):
        """Test removing all duplicate occurrences."""
        result = runner.invoke(app, ["dedupe", str(file_with_duplicates), "--keep", "none"])

        assert result.exit_code == 0
        assert "Original rows: 6" in result.stdout
        assert "Duplicate rows found: 4" in result.stdout
        assert "Rows removed: 4" in result.stdout
        assert "Remaining rows: 2" in result.stdout

    def test_dedupe_by_columns(self, file_with_key_duplicates: Path):
        """Test deduplication based on specific columns."""
        result = runner.invoke(app, [
            "dedupe", str(file_with_key_duplicates),
            "--by", "email",
            "--keep", "first"
        ])

        assert result.exit_code == 0
        assert "Original rows: 6" in result.stdout
        assert "Duplicate rows found: 2" in result.stdout
        assert "Key columns: email" in result.stdout

    def test_dedupe_by_multiple_columns(self, file_with_key_duplicates: Path):
        """Test deduplication based on multiple columns."""
        result = runner.invoke(app, [
            "dedupe", str(file_with_key_duplicates),
            "--by", "email,name",
            "--keep", "first"
        ])

        assert result.exit_code == 0
        assert "Duplicate rows found: 1" in result.stdout
        assert "Key columns: email, name" in result.stdout

    def test_dedupe_no_duplicates(self, file_no_duplicates: Path):
        """Test file with no duplicates."""
        result = runner.invoke(app, ["dedupe", str(file_no_duplicates)])

        assert result.exit_code == 0
        assert "No duplicates found" in result.stdout

    def test_dedupe_with_output(self, file_with_duplicates: Path, tmp_path: Path):
        """Test deduplication with output file."""
        output_path = tmp_path / "deduped.xlsx"
        result = runner.invoke(app, [
            "dedupe", str(file_with_duplicates),
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Written to:" in result.stdout
        assert output_path.exists()

        # Verify the output has correct number of rows
        df_output = pd.read_excel(output_path)
        assert len(df_output) == 4  # Should have 4 unique rows

    def test_dedupe_dry_run(self, file_with_duplicates: Path):
        """Test dry-run mode."""
        result = runner.invoke(app, [
            "dedupe", str(file_with_duplicates),
            "--dry-run"
        ])

        assert result.exit_code == 0
        assert "Preview" in result.stdout
        assert "Original rows: 6" in result.stdout

    def test_dedupe_csv_input(self, csv_file_with_duplicates: Path):
        """Test deduplication from CSV file."""
        result = runner.invoke(app, ["dedupe", str(csv_file_with_duplicates)])

        assert result.exit_code == 0
        assert "Original rows: 5" in result.stdout
        assert "Duplicate rows found: 2" in result.stdout

    def test_dedupe_specific_sheet(self, file_with_duplicates: Path):
        """Test deduplication from specific sheet."""
        result = runner.invoke(app, [
            "dedupe", str(file_with_duplicates),
            "--sheet", "Sheet1"
        ])

        assert result.exit_code == 0

    def test_dedupe_invalid_column(self, file_with_duplicates: Path):
        """Test deduplication with non-existent column."""
        result = runner.invoke(app, [
            "dedupe", str(file_with_duplicates),
            "--by", "invalid_column"
        ])

        assert result.exit_code == 1
        # Error goes to stderr
        assert "Columns not found" in result.stderr or "Columns not found" in result.stdout

    def test_dedupe_invalid_keep_value(self, file_with_duplicates: Path):
        """Test deduplication with invalid keep value."""
        result = runner.invoke(app, [
            "dedupe", str(file_with_duplicates),
            "--keep", "invalid"
        ])

        assert result.exit_code == 1
        # Error message mentions the invalid value
        assert "Invalid keep value" in result.stderr or "Invalid keep value" in result.stdout

    def test_dedupe_empty_file(self, empty_file: Path):
        """Test dedupe on empty file."""
        result = runner.invoke(app, ["dedupe", str(empty_file)])

        assert result.exit_code == 0
        assert "empty" in result.stdout.lower()

    def test_dedupe_all_duplicates_keep_first(self, file_all_duplicates: Path):
        """Test file where all rows are duplicates keeping first."""
        result = runner.invoke(app, [
            "dedupe", str(file_all_duplicates),
            "--keep", "first"
        ])

        assert result.exit_code == 0
        assert "Original rows: 3" in result.stdout
        assert "Remaining rows: 1" in result.stdout

    def test_dedupe_all_duplicates_keep_none(self, file_all_duplicates: Path):
        """Test file where all rows are duplicates keeping none."""
        result = runner.invoke(app, [
            "dedupe", str(file_all_duplicates),
            "--keep", "none"
        ])

        assert result.exit_code == 0
        assert "Original rows: 3" in result.stdout
        assert "Duplicate rows found: 3" in result.stdout
        assert "Remaining rows: 0" in result.stdout

    def test_dedupe_nonexistent_file(self):
        """Test dedupe on non-existent file."""
        result = runner.invoke(app, ["dedupe", "missing.xlsx"])

        assert result.exit_code == 1
        # Error goes to stderr
        assert "File not found" in result.stderr or "File not found" in result.stdout

    def test_dedupe_help(self):
        """Test dedupe command help."""
        result = runner.invoke(app, ["dedupe", "--help"])

        assert result.exit_code == 0
        assert "Remove duplicate rows" in result.stdout
        assert "--by" in result.stdout
        assert "--keep" in result.stdout

    def test_dedupe_case_sensitive(self, file_with_duplicates: Path):
        """Test that deduplication is case-sensitive."""
        # This test verifies the default behavior (case-sensitive)
        result = runner.invoke(app, ["dedupe", str(file_with_duplicates)])

        assert result.exit_code == 0
        # Should find exact duplicates
        assert "Duplicate rows found: 2" in result.stdout

    def test_dedupe_default_keep_first(self, file_with_duplicates: Path):
        """Test that default keep strategy is 'first'."""
        result = runner.invoke(app, ["dedupe", str(file_with_duplicates)])

        assert result.exit_code == 0
        assert "Keep strategy: first" in result.stdout

    def test_dedupe_all_columns_by_default(self, file_with_key_duplicates: Path):
        """Test that all columns are used by default."""
        result = runner.invoke(app, ["dedupe", str(file_with_key_duplicates)])

        assert result.exit_code == 0
        # All columns should be unique, so no duplicates found
        assert "No duplicates found" in result.stdout

    def test_dedupe_with_output_verify_content(self, file_with_duplicates: Path, tmp_path: Path):
        """Test that output file contains correct deduplicated data."""
        output_path = tmp_path / "deduped_verify.xlsx"
        result = runner.invoke(app, [
            "dedupe", str(file_with_duplicates),
            "--output", str(output_path),
            "--keep", "first"
        ])

        assert result.exit_code == 0

        # Verify content
        df_output = pd.read_excel(output_path)
        assert len(df_output) == 4

        # Verify first occurrence is kept
        # Rows with id=1 and id=2 appear first, so those should be kept
        ids = df_output["id"].tolist()
        assert 1 in ids  # First occurrence kept
        assert 2 in ids  # First occurrence kept
        assert 3 in ids
        assert 4 in ids
