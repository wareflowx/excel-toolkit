# Excel CLI Toolkit

Command-line toolkit for Excel data manipulation and analysis.

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

Excel CLI Toolkit (`xl`) is a powerful command-line interface for performing data wrangling and analysis operations on Excel files. Designed for both human users and AI systems, it provides fast, predictable operations without requiring scripts or programming.

## Features

- **Filter & Search**: Filter rows by conditions, search for values
- **Sort & Group**: Sort by columns, group and aggregate data
- **Transform**: Apply transformations, clean data, deduplicate
- **Multi-format**: Support for XLSX, CSV, JSON, and Parquet
- **Functional Programming**: Built with Result/Maybe types for robust error handling
- **AI-Friendly**: Simple, composable commands perfect for AI automation
- **Fast**: Efficient processing of large files

## Installation

### Using pip

```bash
pip install excel-toolkit
```

### Using uv (recommended)

```bash
uv pip install excel-toolkit
```

### Development installation

```bash
git clone https://github.com/wareflowx/excel-toolkit.git
cd excel-toolkit
uv pip install -e ".[dev]"
```

### With Parquet support

```bash
pip install "excel-toolkit[parquet]"
```

## Quick Start

### Basic filtering

```bash
# Filter rows where Amount > 1000
xl filter sales.xlsx --where "Amount > 1000" --output filtered.xlsx

# Filter by multiple conditions
xl filter data.xlsx --where "Region == 'North' and Price > 100" -o result.xlsx
```

### Sorting and aggregation

```bash
# Sort by column
xl sort data.xlsx --by "Date" --descending --output sorted.xlsx

# Group and aggregate
xl group sales.xlsx --by "Region" --aggregate "Amount:sum" --output grouped.xlsx
```

### Data cleaning

```bash
# Remove duplicates
xl dedupe data.xlsx --by "Email" --output unique.xlsx

# Clean whitespace and standardize
xl clean data.xlsx --trim --lowercase --columns "Name,Email" --output clean.xlsx
```

### File conversion

```bash
# Convert Excel to CSV
xl convert data.xlsx --output data.csv

# Convert CSV to Excel
xl convert data.csv --output data.xlsx
```

### Pipeline operations

```bash
# Chain operations
xl filter sales.xlsx --where "Amount > 1000" | \
  xl sort --by "Date" --descending | \
  xl group --by "Region" --aggregate "Amount:sum" \
  --output final.xlsx
```

## Documentation

For detailed documentation, see the [docs/](docs/) directory:

- [FEATURES.md](docs/FEATURES.md) - Complete feature list
- [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) - Architecture overview
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contributing guidelines

## Development

### Setup development environment

```bash
# Clone repository
git clone https://github.com/wareflowx/excel-toolkit.git
cd excel-toolkit

# Install dependencies
uv sync --all-extras

# Install pre-commit hooks
pre-commit install
```

### Running tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=excel_toolkit

# Run specific test file
uv run pytest tests/unit/test_filtering.py
```

### Code quality

```bash
# Linting
uv run ruff check .

# Formatting
uv run ruff format .

# Type checking
uv run mypy excel_toolkit/
```

## Command Reference

### Core Commands

- `xl filter` - Filter rows based on conditions
- `xl select` - Select specific columns
- `xl sort` - Sort by column(s)
- `xl group` - Group and aggregate data
- `xl join` - Join multiple files
- `xl clean` - Clean data (trim, case, etc.)
- `xl dedupe` - Remove duplicates
- `xl transform` - Apply transformations
- `xl convert` - Convert between formats
- `xl merge` - Merge multiple files
- `xl stats` - Calculate statistics
- `xl info` - Display file information
- `xl validate` - Validate data

### Getting help

```bash
# General help
xl --help

# Command-specific help
xl filter --help
```

## Examples

### Data Analysis Workflow

```bash
# Extract sales data for Q1, filter high-value orders, group by region
xl filter sales.xlsx --where "Date >= '2024-01-01' and Date <= '2024-03-31'" | \
  xl filter --where "Amount > 1000" | \
  xl group --by "Region" --aggregate "Amount:sum,Orders:count" \
  --output q1_high_value_by_region.xlsx
```

### Data Cleaning Pipeline

```bash
# Clean messy CSV file
xl clean messy_data.csv \
  --trim \
  --lowercase \
  --columns "email,name" \
  --output cleaned.csv

# Remove duplicates and validate
xl dedupe cleaned.csv --by "email" --output unique.csv
xl validate unique.csv --columns "email:email,age:int:0-120" --output final.csv
```

## Architecture

Built with a functional programming approach:

- **Result types**: Explicit error handling without exceptions
- **Maybe types**: Safe handling of optional values
- **Immutable configuration**: Predictable behavior
- **Composable operations**: Chain commands efficiently

For more details, see [FUNCTIONAL_ANALYSIS.md](docs/FUNCTIONAL_ANALYSIS.md).

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Built with:
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Pandas](https://pandas.pydata.org/) - Data manipulation
- [OpenPyXL](https://openpyxl.readthedocs.io/) - Excel file handling
