# Title: Add integration tests for command pipelines and end-to-end workflows

## Problem Description

The test suite has **good unit test coverage** but **zero integration tests** for real-world usage scenarios like command pipelines, multi-step workflows, and end-to-end operations. This means bugs in integration scenarios go undetected until they affect users in production.

### Current Test Coverage

**Unit Tests** (good coverage):
- 40+ test files covering individual functions
- Unit tests for operations (filtering, sorting, aggregating, etc.)
- Unit tests for file handlers
- Unit tests for functional programming primitives

**Missing Integration Tests**:
- No tests for piped commands
- No tests for multi-step workflows
- No tests for error scenarios across operations
- No tests for file format conversions
- No tests for real-world data scenarios

### Real-World Scenarios Not Tested

**Scenario 1: Pipeline operations**
```bash
# This is NEVER tested:
xl filter data.xlsx --where "Amount > 1000" | \
  xl sort --by Date --descending | \
  xl group --by Region --aggregate "Amount:sum" \
  --output final.xlsx
```

**Scenario 2: Multi-format workflow**
```bash
# Never tested:
xl convert data.csv --output temp.xlsx
xl transform temp.xlsx --col "Amount" --expr "Amount * 1.1" --output transformed.xlsx
xl validate transformed.xlsx --columns "Amount:numeric" --output final.xlsx
```

**Scenario 3: Error recovery**
```bash
# Never tested:
xl filter corrupt_file.xlsx --where "age > 30"  # What happens?
```

**Scenario 4: Large file handling**
```bash
# Never tested with real large files:
xl filter large_500k_rows.xlsx --where "Amount > 1000"
```

### Impact

1. **Bugs in production**: Integration issues only discovered by users
2. **Regression risk**: Changes break real workflows without detection
3. **False confidence**: 90% unit test coverage doesn't mean system works
4. **Missing edge cases**: File format issues, encoding problems not caught

## Affected Areas

All command combinations and workflows:
- Pipeline operations (using `|`)
- Multi-step data transformations
- File format conversions
- Error handling across operations
- Integration with external tools

## Proposed Solution

### 1. Add Integration Test Suite

```python
# tests/integration/test_pipelines.py

"""Integration tests for command pipelines."""

import subprocess
import tempfile
from pathlib import Path
import pandas as pd

class TestCommandPipelines:
    """Test actual command-line pipelines."""

    def test_filter_sort_group_pipeline(self, tmp_path):
        """Test realistic pipeline: filter → sort → group."""

        # Create test data
        input_file = tmp_path / "input.xlsx"
        df = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=1000),
            'Region': ['North', 'South', 'East', 'West'] * 250,
            'Amount': [100 + i % 500 for i in range(1000)]
        })
        df.to_excel(input_file, index=False)

        output_file = tmp_path / "output.xlsx"

        # Run pipeline
        result = subprocess.run([
            'xl', 'filter', str(input_file), 'Amount > 300',
            '|',
            'xl', 'sort', '--by', 'Date', '--descending',
            '|',
            'xl', 'group', '--by', 'Region', '--aggregate', 'Amount:sum',
            '--output', str(output_file)
        ], capture_output=True, text=True, shell=True)

        assert result.returncode == 0
        assert output_file.exists()

        # Verify output
        result_df = pd.read_excel(output_file)
        assert len(result_df) == 4  # 4 regions
        assert 'Amount' in result_df.columns

    def test_csv_to_excel_workflow(self, tmp_path):
        """Test CSV to Excel conversion with validation."""

        # Create CSV
        csv_file = tmp_path / "input.csv"
        df = pd.DataFrame({
            'id': range(100),
            'name': [f'User{i}' for i in range(100)],
            'age': [20 + (i % 50) for i in range(100)]
        })
        df.to_csv(csv_file, index=False)

        xlsx_file = tmp_path / "output.xlsx"
        validated_file = tmp_path / "validated.xlsx"

        # Convert
        subprocess.run([
            'xl', 'convert', str(csv_file),
            '--output', str(xlsx_file)
        ], check=True)

        # Validate
        subprocess.run([
            'xl', 'validate', str(xlsx_file),
            '--columns', 'age:int:0-120',
            '--output', str(validated_file)
        ], check=True)

        assert validated_file.exists()

    def test_error_handling_in_pipeline(self, tmp_path):
        """Test error handling when pipeline step fails."""

        input_file = tmp_path / "input.xlsx"
        df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        df.to_excel(input_file, index=False)

        # Invalid filter should fail pipeline
        result = subprocess.run([
            'xl', 'filter', str(input_file), 'invalid_column == 1',
            '|',
            'xl', 'sort', '--by', 'A'
        ], capture_output=True, text=True, shell=True)

        assert result.returncode != 0
        assert 'ColumnNotFoundError' in result.stderr or 'Invalid condition' in result.stderr
```

### 2. Add End-to-End Workflow Tests

```python
# tests/integration/test_workflows.py

"""End-to-end workflow tests."""

class TestRealWorldWorkflows:
    """Test realistic data processing workflows."""

    def test_sales_data_analysis_workflow(self, tmp_path):
        """Test complete sales data analysis workflow."""

        # Create realistic test data
        input_file = tmp_path / "sales.xlsx"
        df = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=10000),
            'Product': [f'P{i%100}' for i in range(10000)],
            'Region': ['North', 'South', 'East', 'West'] * 2500,
            'Salesperson': [f'SP{i%50}' for i in range(10000)],
            'Amount': [100 + (i % 1000) for i in range(10000)],
            'Quantity': [1 + (i % 10) for i in range(10000)]
        })
        df.to_excel(input_file, index=False)

        output_dir = tmp_path / "outputs"
        output_dir.mkdir()

        # Workflow: Clean → Filter → Aggregate → Export
        # Step 1: Clean (remove duplicates)
        clean_file = output_dir / "cleaned.xlsx"
        subprocess.run([
            'xl', 'dedupe', str(input_file),
            '--by', 'Date,Product,Region,Salesperson',
            '--output', str(clean_file)
        ], check=True)

        # Step 2: Filter (high-value orders)
        filtered_file = output_dir / "filtered.xlsx"
        subprocess.run([
            'xl', 'filter', str(clean_file),
            'Amount > 500',
            '--output', str(filtered_file)
        ], check=True)

        # Step 3: Aggregate by region
        aggregated_file = output_dir / "by_region.xlsx"
        subprocess.run([
            'xl', 'group', str(filtered_file),
            '--by', 'Region',
            '--aggregate', 'Amount:sum,Quantity:sum',
            '--output', str(aggregated_file)
        ], check=True)

        # Verify final output
        result = pd.read_excel(aggregated_file)
        assert len(result) == 4  # 4 regions
        assert result['Amount'].sum() > 0

    def test_data_quality_workflow(self, tmp_path):
        """Test data quality checking and fixing workflow."""

        # Create data with quality issues
        input_file = tmp_path / "messy.xlsx"
        df = pd.DataFrame({
            'name': ['  Alice  ', 'bob', '  CHARLIE', '  David  '],
            'email': ['alice@example.com', 'BOB@EXAMPLE.COM', 'charlie@test.com', 'david@test.com'],
            'age': [25, 30, 35, 150],  # Invalid age
            'country': ['USA', 'uk', 'FRANCE', '  us  ']  # Inconsistent
        })
        df.to_excel(input_file, index=False)

        output_dir = tmp_path / "outputs"
        output_dir.mkdir()

        # Step 1: Clean (trim, lowercase)
        cleaned_file = output_dir / "cleaned.xlsx"
        subprocess.run([
            'xl', 'clean', str(input_file),
            '--trim', '--lowercase',
            '--columns', 'name,country',
            '--output', str(cleaned_file)
        ], check=True)

        # Step 2: Validate
        validated_file = output_dir / "validated.xlsx"
        result = subprocess.run([
            'xl', 'validate', str(cleaned_file),
            '--columns', 'age:int:0-120',
            '--output', str(validated_file)
        ])

        # Should fail validation due to age=150
        assert result.returncode != 0
```

### 3. Add File Format Integration Tests

```python
# tests/integration/test_file_formats.py

"""Test file format conversions and edge cases."""

class TestFileFormats:
    """Test various file formats and conversions."""

    def test_csv_with_special_encoding(self, tmp_path):
        """Test CSV with non-UTF8 encoding."""

        # Create CSV with Latin-1 encoding
        csv_file = tmp_path / "latin1.csv"
        with open(csv_file, 'w', encoding='latin-1') as f:
            f.write("name,city\n")
            f.write("José,São Paulo\n")
            f.write("François,Montréal\n")

        # Should auto-detect encoding
        result = subprocess.run([
            'xl', 'filter', str(csv_file),
            'name == "José"',
            '--output', str(tmp_path / 'output.xlsx')
        ])

        assert result.returncode == 0

    def test_excel_with_multiple_sheets(self, tmp_path):
        """Test Excel file with multiple sheets."""

        excel_file = tmp_path / "multi.xlsx"
        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame({'A': [1, 2, 3]}).to_excel(writer, sheet_name='Sheet1', index=False)
            pd.DataFrame({'B': [4, 5, 6]}).to_excel(writer, sheet_name='Sheet2', index=False)
            pd.DataFrame({'C': [7, 8, 9]}).to_excel(writer, sheet_name='Sheet3', index=False)

        # Process specific sheet
        output = tmp_path / "output.xlsx"
        subprocess.run([
            'xl', 'filter', str(excel_file),
            'A > 1',
            '--sheet', 'Sheet1',
            '--output', str(output)
        ], check=True)

        result = pd.read_excel(output)
        assert len(result) == 2

    def test_corrupt_file_handling(self, tmp_path):
        """Test handling of corrupt files."""

        # Create invalid Excel file
        corrupt_file = tmp_path / "corrupt.xlsx"
        with open(corrupt_file, 'wb') as f:
            f.write(b'This is not a valid Excel file')

        result = subprocess.run([
            'xl', 'info', str(corrupt_file)
        ], capture_output=True, text=True)

        assert result.returncode != 0
        assert 'Invalid file' in result.stderr or 'corrupt' in result.stderr.lower()
```

### 4. Add Performance Regression Tests

```python
# tests/integration/test_performance.py

"""Performance regression tests for large files."""

class TestPerformance:
    """Test that performance doesn't degrade."""

    def test_large_file_filter_performance(self, tmp_path, benchmark=False):
        """Test filtering on large file doesn't exceed time limit."""

        # Create 100k row file
        input_file = tmp_path / "large.xlsx"
        df = pd.DataFrame({
            'id': range(100000),
            'value': [i % 1000 for i in range(100000)]
        })
        df.to_excel(input_file, index=False)

        output_file = tmp_path / "output.xlsx"

        import time
        start = time.time()

        subprocess.run([
            'xl', 'filter', str(input_file),
            'value > 500',
            '--output', str(output_file)
        ], check=True)

        elapsed = time.time() - start

        # Should complete in less than 30 seconds
        assert elapsed < 30, f"Too slow: {elapsed:.1f}s"
```

## Test Infrastructure

```python
# tests/integration/conftest.py

"""Fixtures for integration tests."""

import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def sample_data_dir():
    """Provide directory with sample test data."""
    return Path(__file__).parent / 'fixtures' / 'sample_data'

@pytest.fixture
def temp_workspace(tmp_path):
    """Provide temporary workspace directory."""
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    return workspace
```

## Implementation Priority

1. **High Priority**: Pipeline tests (most common usage)
2. **High Priority**: Error handling tests (critical for UX)
3. **Medium Priority**: End-to-end workflow tests
4. **Medium Priority**: File format edge cases
5. **Low Priority**: Performance regression tests

## Related Issues

- Tests using dangerous patterns (#015)
- Insufficient property tests (#016)
