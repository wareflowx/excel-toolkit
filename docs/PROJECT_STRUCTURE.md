# Excel CLI Toolkit - Project Structure

## Overview

This document outlines the project structure for the Excel CLI Toolkit using Typer. The structure follows Python best practices with clear separation between CLI interface, business logic, and data handling.

## Project Directory Structure

```
excel-toolkit/
├── pyproject.toml                 # Project metadata, dependencies, build config (uv-managed)
├── uv.lock                        # Dependency lock file (uv-managed)
├── README.md                      # Project documentation
├── LICENSE                        # License file
├── .gitignore                     # Git ignore patterns
│
├── docs/                          # Documentation
│   ├── FEATURES.md                # Feature documentation
│   ├── PROJECT_STRUCTURE.md       # This file
│   └── API.md                     # API documentation (future)
│
├── excel_toolkit/                 # Main package directory
│   ├── __init__.py                # Package initialization
│   ├── __main__.py                # Entry point for module execution
│   ├── cli.py                     # Main CLI application (Typer app)
│   ├── const.py                   # Constants (exit codes, defaults)
│   └── exceptions.py              # Custom exception classes
│
│   ├── core/                      # File I/O abstraction
│   │   ├── __init__.py
│   │   ├── excel_handler.py       # Excel file operations
│   │   ├── csv_handler.py         # CSV file operations
│   │   ├── json_handler.py        # JSON file operations
│   │   ├── parquet_handler.py     # Parquet file operations
│   │   └── file_manager.py        # Format detection and handler factory
│
│   ├── commands/                  # CLI command implementations
│   │   ├── __init__.py
│   │   ├── base.py                # Base command class and shared utilities
│   │   ├── filter.py              # Filter command
│   │   ├── select.py              # Select command
│   │   ├── sort.py                # Sort command
│   │   ├── group.py               # Group and aggregate commands
│   │   ├── join.py                # Join command
│   │   ├── clean.py               # Clean command
│   │   ├── dedupe.py              # Deduplicate command
│   │   ├── transform.py           # Transform command
│   │   ├── convert.py             # Convert command
│   │   ├── merge.py               # Merge command
│   │   ├── stats.py               # Stats command
│   │   ├── info.py                # Info command
│   │   ├── validate.py            # Validate command
│   │   └── export.py              # Export command
│
│   ├── operations/                # Business logic (data operations)
│   │   ├── __init__.py
│   │   ├── filtering.py           # Filtering logic
│   │   ├── sorting.py             # Sorting logic
│   │   ├── grouping.py            # Grouping and aggregation
│   │   ├── cleaning.py            # Data cleaning operations
│   │   ├── transforming.py        # Data transformations
│   │   ├── joining.py             # Join operations
│   │   └── validation.py          # Data validation logic
│
│   ├── models/                    # Type definitions and data models
│   │   ├── __init__.py
│   │   ├── file_types.py          # File type enums and constants
│   │   ├── operation_config.py    # Operation configuration models
│   │   └── error_types.py         # Error type definitions (ADTs)
│
│   ├── fp/                        # Functional programming primitives
│   │   ├── __init__.py
│   │   ├── result.py              # Result type (Either/Success-Failure)
│   │   ├── maybe.py               # Maybe type (Option/Some-None)
│   │   ├── pipeline.py            # Pipe and composition utilities
│   │   ├── functor.py             # Functor implementations
│   │   ├── monad.py               # Monad utilities (and_then, or_else)
│   │   ├── immutable.py           # Immutable dataclass helpers
│   │   └── curry.py               # Currying and partial application helpers
│
│   ├── utils/                     # Utility functions
│   │   ├── __init__.py
│   │   ├── path_utils.py          # File path utilities
│   │   ├── output.py              # Output formatting
│   │   ├── logging.py             # Logging configuration
│   │   └── validators.py          # Input validation helpers
│
│   └── templates/                 # Predefined operation templates
│       ├── __init__.py
│       ├── clean_csv.py           # Clean CSV template
│       ├── sales_report.py        # Sales report template
│       └── base.py                # Template base class
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── conftest.py                # Pytest configuration and fixtures
│   ├── unit/                      # Unit tests
│   │   ├── test_filtering.py
│   │   ├── test_sorting.py
│   │   ├── test_cleaning.py
│   │   └── ...
│   ├── integration/               # Integration tests
│   │   ├── test_commands.py
│   │   ├── test_workflows.py
│   │   └── test_pipelines.py
│   ├── properties/                # Property-based tests
│   │   ├── test_functor_laws.py   # Functor law verification
│   │   ├── test_monad_laws.py     # Monad law verification
│   │   └── test_round_trip.py     # Round-trip conversion tests
│   └── fixtures/                  # Test data files
│       ├── sample.xlsx
│       ├── sample.csv
│       └── large_dataset.xlsx
│
└── scripts/                       # Development and utility scripts
    └── generate_fixtures.py       # Generate test fixtures
```

## Component Responsibilities

### Root Level

**pyproject.toml**: Central configuration file containing project metadata, dependencies, build system configuration, and tool settings (pytest, ruff, mypy).

**README.md**: User-facing documentation with installation, quick start, usage examples, and contributing guidelines.

### Main Package (excel_toolkit/)

**cli.py**: Main Typer application entry point. Registers all commands, defines global options, handles version display, and manages top-level error handling.

**const.py**: Application-wide constants including exit codes, default values, configuration defaults, and error message templates.

**exceptions.py**: Custom exception hierarchy for specific error scenarios (file operations, validation errors, format support).

### Core Module (core/)

Responsibility: Abstract file I/O operations across different formats.

**file_manager.py**: Format detection from file extensions and handler factory. Provides unified read/write interface regardless of file format.

**format handlers** (excel_handler.py, csv_handler.py, etc.): Format-specific read/write operations, encoding handling, format-specific options.

### Commands Module (commands/)

Responsibility: Typer command implementations. Each file corresponds to one CLI command.

**base.py**: Shared command functionality including common option definitions, output formatting utilities, and validation decorators.

**command files** (filter.py, sort.py, etc.): Define Typer command functions with parameter definitions, argument parsing, and delegation to operations layer. Handle user input validation and display results.

### Operations Module (operations/)

Responsibility: Pure business logic separated from CLI concerns.

Each file contains functions that perform actual data manipulations on pandas DataFrames. These functions have no knowledge of Typer or CLI - they take parameters and return results.

This separation enables:
- Unit testing without CLI dependencies
- Reuse in pipelines and templates
- Import by external packages
- Clear separation of concerns

### Models Module (models/)

Responsibility: Type definitions and data structures.

**file_types.py**: Enums for supported file types and format constants.

**operation_config.py**: Configuration dataclasses for operations, providing type-safe parameter containers.

**error_types.py**: Algebraic Data Types for structured error representation. Defines error hierarchy as ADTs for pattern matching and exhaustive error handling.

### FP Module (fp/)

Responsibility: Functional programming primitives and utilities.

**result.py**: Result type (Either/Success-Failure) for explicit error handling. Represents operations that can succeed (Ok) or fail (Err). Used throughout the codebase for fallible operations.

**maybe.py**: Maybe type (Option/Some-None) for optional values. Represents values that may or may not exist. Eliminates None-related errors.

**pipeline.py**: Pipe and composition utilities. Provides operators for chaining operations in readable pipelines. Enables data transformation workflows.

**functor.py**: Functor implementations for mapping over computational contexts. Provides map operations for Result and Maybe types.

**monad.py**: Monad utilities including and_then (bind), or_else, and composition. Enables chaining operations that may fail with short-circuit evaluation.

**immutable.py**: Immutable dataclass helpers. Provides decorators and utilities for creating immutable data structures. Ensures configuration and models cannot be modified after creation.

**curry.py**: Currying and partial application helpers. Enables creation of specialized functions from general ones. Used for operation factories and validator builders.

### Utils Module (utils/)

Responsibility: Cross-cutting utility functions.

**path_utils.py**: File path validation, normalization, and directory creation utilities.

**output.py**: Terminal output formatting, JSON output generation, progress bars.

**logging.py**: Logging configuration and log level management.

**validators.py**: Input validation functions including condition parsing, column name validation, and data type checking.

### Templates Module (templates/)

Responsibility: Predefined workflow templates for common operations.

Templates chain multiple operations together into single commands. Each template defines a complete workflow (e.g., "clean CSV" = trim + dedupe + validate).

## CLI Architecture

### Command Structure

Two possible organizational approaches:

**Flat Structure** (recommended): All commands registered at root level, enabling direct invocation like `xl filter`, `xl sort`.

**Grouped Structure**: Commands organized under sub-groups. More hierarchical but requires different invocation patterns.

Given the feature set and AI/human usage, flat structure provides simpler, more direct command invocation.

### Command Implementation Pattern

Each command file follows this pattern:
1. Define Typer command function with parameters
2. Validate inputs
3. Call corresponding operation function
4. Handle output formatting
5. Manage exit codes

Operations are called from commands, not the reverse. Operations layer has no Typer dependencies.

### Entry Points

Two execution methods supported:
1. **Installed command**: `xl` command via pyproject.toml entry points
2. **Module execution**: `python -m excel_toolkit` via __main__.py

## Dependencies

### Package Management

**uv** is used as the package and project manager, providing fast dependency resolution, virtual environment management, and building.

### Core Runtime Dependencies

- **typer**: CLI framework and command parsing
- **pandas**: Data manipulation and analysis
- **openpyxl**: Excel XLSX read/write
- **xlrd**: Legacy Excel format support

### Optional Dependencies

- **pyarrow**: Parquet format support
- **fastparquet**: Alternative Parquet engine
- **chardet**: CSV encoding detection

### Development Dependencies

- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **ruff**: Fast linting and formatting
- **mypy**: Static type checking
- **hypothesis**: Property-based testing for functor/monad laws

## Testing Strategy

### Unit Tests (tests/unit/)

Test individual operations and functions in isolation. Mock file I/O operations. Fast execution focused on business logic correctness.

**FP-specific unit tests**:
- Result type operations (map, and_then, or_else)
- Maybe type operations (unwrap_or, map, and_then)
- Pipeline composition
- Immutable dataclass behavior

### Integration Tests (tests/integration/)

Test complete command workflows with actual file operations. Verify file I/O, format conversion, and error handling. Use file fixtures.

**FP integration tests**:
- Error propagation through pipelines
- Result chaining across multiple operations
- Maybe type usage in file operations
- Pipeline execution with failures

### Property-Based Tests (tests/properties/)

Test that FP abstractions satisfy mathematical laws using hypothesis.

**test_functor_laws.py**: Verify functor laws for Result and Maybe
- Identity: map(id) == id
- Composition: map(f . g) == map(f) . map(g)

**test_monad_laws.py**: Verify monad laws for Result
- Left identity: return(x).and_then(f) == f(x)
- Right identity: m.and_then(return) == m
- Associativity: m.and_then(f).and_then(g) == m.and_then(lambda x: f(x).and_then(g))

**test_round_trip.py**: Verify round-trip properties
- Convert XLSX -> CSV -> XLSX preserves data
- Format conversions are lossless
- Operations preserve data invariants

### Fixtures (tests/fixtures/)

Test data files including:
- Small datasets for quick tests
- Large datasets for performance testing
- Edge cases (empty files, malformed data, special characters)

### conftest.py

Centralized pytest configuration including fixtures for sample DataFrames, temporary files, test data generation, and FP type fixtures.

## Configuration

### Environment Variables

Optional environment variables for defaults:
- Default output directory
- Log level
- Maximum file size
- Chunk size for large files
- Temporary directory location

### Future: Configuration File

Potential support for `.xlrc.yml` configuration file for user preferences, default values, and format-specific options.

## Functional Programming Patterns

### Error Handling Pattern

All fallible operations return `Result[T, E]` instead of raising exceptions:

```python
# File operations
def read_file(path: Path) -> Result[DataFrame, FileError]

# Data operations
def filter_data(df: DataFrame, condition: str) -> Result[DataFrame, FilterError]

# Validation
def validate_column_name(name: str) -> Result[ColumnName, ValidationError]
```

### Optional Value Pattern

Operations that may not find a value return `Maybe[T]`:

```python
# Sheet lookup
def get_sheet(workbook: Workbook, name: str) -> Maybe[Sheet]

# Column lookup
def find_column(df: DataFrame, name: str) -> Maybe[Series]
```

### Pipeline Composition Pattern

Complex workflows compose operations using pipes:

```python
# In operations/pipeline.py
def process_sales_data(df: DataFrame) -> Result[DataFrame, Error]:
    return (
        pipe(df)
        .then(filter_valid_rows)
        .then(remove_duplicates)
        .then(group_by_region)
        .then(calculate_totals)
    )
```

### Configuration Pattern

All configuration models are immutable dataclasses:

```python
@immutable
@dataclass
class FilterConfig:
    condition: str
    column: str
    case_sensitive: bool = False
```

### Operation Factory Pattern

Create specialized operations using currying:

```python
# In operations/filtering.py
def create_filter(column: str) -> Callable[[str], FilterOperation]:
    return lambda condition: FilterOperation(column, condition)

filter_by_price = create_filter("Price")
expensive_filter = filter_by_price(" > 1000")
```

### Validation Chain Pattern

Combine multiple validators using monadic composition:

```python
def validate_column(name: str) -> Result[ColumnName, ValidationError]:
    return (
        validate_not_empty(name)
        .and_then(validate_not_reserved)
        .and_then(validate_length)
        .and_then(validate_characters)
    )
```

## Import Conventions

### Import Order

1. Standard library imports
2. Third-party imports
3. Local imports

### Module Boundaries

- **commands/** may import from operations, core, utils, models, fp
- **operations/** may import from core, utils, models, fp, but NOT commands
- **core/** may import from models, utils, fp, but NOT commands or operations
- **utils/** may import from models, fp
- **fp/** must remain independent, only importing from standard library

This prevents circular dependencies and maintains clear layer separation.

### Functional Programming Module Access

The fp/ module is a foundational layer available to all other modules except CLI-specific code:

- **Result types** used in: operations/, core/, utils/
- **Maybe types** used in: core/, models/, utils/
- **Pipeline utilities** used in: operations/, templates/
- **Immutable helpers** used in: models/, operations/
- **Curry helpers** used in: utils/validators.py, operations/

The commands/ layer primarily handles Result propagation but does not create new Result instances.

## Development Workflow

### Project Initialization

```bash
uv init excel-toolkit
cd excel-toolkit
```

### Dependency Management

```bash
# Add core dependencies
uv add typer pandas openpyxl

# Add development dependencies
uv add --dev pytest pytest-cov ruff mypy hypothesis

# Add optional dependencies (extras)
uv add --optional parquet pyarrow
```

### Virtual Environment

uv automatically creates and manages a virtual environment in `.venv/`.

```bash
# Activate environment (standard Python venv)
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Or use uv run to execute commands in the venv
uv run python -m excel_toolkit
uv run pytest
```

### Local Development

Use `uv run python -m excel_toolkit` for testing without installation.

### Editable Installation

```bash
# Install in editable mode with uv
uv pip install -e .

# Or synchronize the environment
uv sync
```

This creates an editable install enabling `xl` command while keeping code changes reflected immediately.

### Code Quality

- **uv run ruff check**: Linting
- **uv run ruff format**: Formatting
- **uv run mypy**: Type checking
- **uv run pytest**: Run tests

## Packaging

### Build System

Modern Python packaging using `pyproject.toml` with uv as the build backend.

### Building Packages

```bash
# Build wheel and source distribution
uv build

# Output: dist/excel_toolkit-0.1.0-py3-none-any.whl
#         dist/excel_toolkit-0.1.0.tar.gz
```

### Entry Points Configuration

Define CLI command in pyproject.toml to create `xl` executable after installation. uv handles entry point installation automatically.

### Publishing

```bash
# Publish to PyPI
uv publish

# Or use twine
uv pip install twine
python -m twine upload dist/*
```

### Distribution

Support standard PyPI distribution with optional dependencies (e.g., `[parquet]` extra for Parquet support).

## Extension Points

### Future Plugin System

Architecture allows for:
- Custom command plugins
- User-defined operation templates
- Custom file format handlers

### Async Operations

Current structure supports future async refactor for parallel processing of large files.

### Caching Layer

Hook points exist for future caching of parsed DataFrames to speed up repeated operations.

## Summary

This architecture provides:

1. **Clear separation**: CLI, business logic, and I/O are isolated
2. **Testability**: Operations can be tested independently
3. **Maintainability**: Each module has single responsibility
4. **Extensibility**: New commands and operations follow established patterns
5. **Performance**: Structure supports future optimization (async, caching)
6. **AI-friendly**: Simple, predictable commands with clear interfaces
7. **Human-usable**: Clear CLI patterns and helpful error messages
8. **Type-safe error handling**: Result types make fallible operations explicit
9. **Composable operations**: Pipeline utilities enable clean workflow composition
10. **Immutable state**: Configuration and models cannot be modified after creation
11. **Mathematical correctness**: Property-based tests verify functor/monad laws
