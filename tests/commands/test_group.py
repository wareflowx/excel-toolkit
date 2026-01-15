"""Unit tests for group command.

Tests for the group command that groups and aggregates data.
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
def sales_data_file(tmp_path: Path) -> Path:
    """Create a sales data file for grouping."""
    df = pd.DataFrame(
        {
            "region": ["North", "South", "North", "East", "South", "West", "North", "East"],
            "product": ["A", "B", "A", "C", "B", "A", "C", "A"],
            "amount": [100, 200, 150, 300, 250, 180, 220, 170],
            "quantity": [10, 20, 15, 30, 25, 18, 22, 17],
            "discount": [5, 10, 5, 15, 10, 5, 10, 5],
        }
    )
    file_path = tmp_path / "sales.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def multi_column_group_file(tmp_path: Path) -> Path:
    """Create a file suitable for multi-column grouping."""
    df = pd.DataFrame(
        {
            "year": [2023, 2023, 2023, 2024, 2024, 2024],
            "quarter": ["Q1", "Q2", "Q3", "Q1", "Q2", "Q3"],
            "region": ["North", "South", "North", "South", "North", "South"],
            "sales": [1000, 1500, 1200, 1800, 2000, 1700],
            "profit": [200, 300, 250, 400, 450, 380],
        }
    )
    file_path = tmp_path / "multi_group.xlsx"
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
def csv_file_for_group(tmp_path: Path) -> Path:
    """Create a CSV file for grouping."""
    df = pd.DataFrame(
        {
            "category": ["A", "B", "A", "C", "B", "A"],
            "value": [10, 20, 15, 30, 25, 18],
        }
    )
    file_path = tmp_path / "group_data.csv"
    df.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def file_with_nulls(tmp_path: Path) -> Path:
    """Create a file with null values for grouping."""
    df = pd.DataFrame(
        {
            "group": ["A", "B", "A", None, "B", "A"],
            "value": [10, 20, 15, 25, 30, 18],
        }
    )
    file_path = tmp_path / "nulls.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


# =============================================================================
# Group Command Tests
# =============================================================================


class TestGroupCommand:
    """Tests for the group command."""

    def test_group_single_column_sum(self, sales_data_file: Path):
        """Test grouping by single column with sum aggregation."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "region",
            "--aggregate", "amount:sum"
        ])

        assert result.exit_code == 0
        assert "Grouped by: region" in result.stdout
        assert "Aggregations: amount:sum" in result.stdout

    def test_group_single_column_mean(self, sales_data_file: Path):
        """Test grouping with mean aggregation."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "product",
            "--aggregate", "amount:mean"
        ])

        assert result.exit_code == 0
        assert "Grouped by: product" in result.stdout

    def test_group_avg_synonym(self, sales_data_file: Path):
        """Test that avg is treated as mean."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "region",
            "--aggregate", "amount:avg"
        ])

        assert result.exit_code == 0

    def test_group_multiple_aggregations(self, sales_data_file: Path):
        """Test grouping with multiple aggregations."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "region",
            "--aggregate", "amount:sum,quantity:mean,discount:min"
        ])

        assert result.exit_code == 0
        assert "Aggregations: amount:sum,quantity:mean,discount:min" in result.stdout

    def test_group_median_aggregation(self, sales_data_file: Path):
        """Test median aggregation."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "region",
            "--aggregate", "amount:median"
        ])

        assert result.exit_code == 0

    def test_group_count_aggregation(self, sales_data_file: Path):
        """Test count aggregation."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "product",
            "--aggregate", "amount:count"
        ])

        assert result.exit_code == 0

    def test_group_std_aggregation(self, sales_data_file: Path):
        """Test standard deviation aggregation."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "region",
            "--aggregate", "amount:std"
        ])

        assert result.exit_code == 0

    def test_group_var_aggregation(self, sales_data_file: Path):
        """Test variance aggregation."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "region",
            "--aggregate", "amount:var"
        ])

        assert result.exit_code == 0

    def test_group_multiple_columns(self, multi_column_group_file: Path):
        """Test grouping by multiple columns."""
        result = runner.invoke(app, [
            "group", str(multi_column_group_file),
            "--by", "year,quarter",
            "--aggregate", "sales:sum,profit:mean"
        ])

        assert result.exit_code == 0
        assert "Grouped by: year, quarter" in result.stdout

    def test_group_with_output(self, sales_data_file: Path, tmp_path: Path):
        """Test grouping with output file."""
        output_path = tmp_path / "grouped.xlsx"
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "region",
            "--aggregate", "amount:sum",
            "--output", str(output_path)
        ])

        assert result.exit_code == 0
        assert "Written to:" in result.stdout
        assert output_path.exists()

    def test_group_dry_run(self, sales_data_file: Path):
        """Test dry-run mode."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "region",
            "--aggregate", "amount:sum",
            "--dry-run"
        ])

        assert result.exit_code == 0
        assert "Preview" in result.stdout

    def test_group_csv_input(self, csv_file_for_group: Path):
        """Test grouping from CSV file."""
        result = runner.invoke(app, [
            "group", str(csv_file_for_group),
            "--by", "category",
            "--aggregate", "value:sum"
        ])

        assert result.exit_code == 0

    def test_group_specific_sheet(self, sales_data_file: Path):
        """Test grouping from specific sheet."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "region",
            "--aggregate", "amount:sum",
            "--sheet", "Sheet1"
        ])

        assert result.exit_code == 0

    def test_group_invalid_group_column(self, sales_data_file: Path):
        """Test grouping with non-existent group column."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "invalid_column",
            "--aggregate", "amount:sum"
        ])

        assert result.exit_code == 1

    def test_group_invalid_aggregate_column(self, sales_data_file: Path):
        """Test grouping with non-existent aggregate column."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "region",
            "--aggregate", "invalid_column:sum"
        ])

        assert result.exit_code == 1

    def test_group_invalid_function(self, sales_data_file: Path):
        """Test grouping with invalid aggregation function."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "region",
            "--aggregate", "amount:invalid"
        ])

        assert result.exit_code == 1

    def test_group_missing_by_parameter(self, sales_data_file: Path):
        """Test group without --by parameter."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--aggregate", "amount:sum"
        ])

        assert result.exit_code == 1

    def test_group_missing_aggregate_parameter(self, sales_data_file: Path):
        """Test group without --aggregate parameter."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "region"
        ])

        assert result.exit_code == 1

    def test_group_same_column_for_by_and_aggregate(self, sales_data_file: Path):
        """Test that same column cannot be used for grouping and aggregation."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "region",
            "--aggregate", "region:sum"
        ])

        assert result.exit_code == 1

    def test_group_empty_file(self, empty_file: Path):
        """Test group on empty file."""
        result = runner.invoke(app, [
            "group", str(empty_file),
            "--by", "column",
            "--aggregate", "value:sum"
        ])

        assert result.exit_code == 0
        assert "empty" in result.stdout.lower()

    def test_group_nonexistent_file(self):
        """Test group on non-existent file."""
        result = runner.invoke(app, [
            "group", "missing.xlsx",
            "--by", "region",
            "--aggregate", "amount:sum"
        ])

        assert result.exit_code == 1

    def test_group_help(self):
        """Test group command help."""
        result = runner.invoke(app, ["group", "--help"])

        assert result.exit_code == 0
        assert "Group data" in result.stdout
        assert "--by" in result.stdout
        assert "--aggregate" in result.stdout

    def test_group_invalid_aggregate_format(self, sales_data_file: Path):
        """Test invalid aggregate format (missing colon)."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "region",
            "--aggregate", "amount"
        ])

        assert result.exit_code == 1

    def test_group_duplicate_aggregate_column(self, sales_data_file: Path):
        """Test duplicate column in aggregations."""
        result = runner.invoke(app, [
            "group", str(sales_data_file),
            "--by", "region",
            "--aggregate", "amount:sum,amount:mean"
        ])

        assert result.exit_code == 1

    def test_group_with_nulls(self, file_with_nulls: Path):
        """Test grouping with null values."""
        result = runner.invoke(app, [
            "group", str(file_with_nulls),
            "--by", "group",
            "--aggregate", "value:sum"
        ])

        assert result.exit_code == 0
