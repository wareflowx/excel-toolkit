# Title: Decouple operations layer from CLI commands to enable reuse as a library

## Problem Description

The operations layer is **tightly coupled** to the CLI command interface, making it impossible to reuse the core data processing logic in other contexts (web APIs, Python libraries, Jupyter notebooks, etc.). All operations depend on CLI-specific constructs.

### Current Architecture Problem

```
User → CLI Commands (commands/) → Operations (operations/) → File Handlers (core/)
        ↑                           ↑
    Typer-specific              Should be CLI-agnostic
```

**The Issue**: Operations are designed specifically for CLI usage, not as a general-purpose library.

### Concrete Examples of Coupling

**1. Operations return CLI-friendly messages**
```python
# operations/filtering.py
def apply_filter(df: pd.DataFrame, condition: str) -> Result[pd.DataFrame, FilterError]:
    # Operation is tied to how CLI will use it
    # No clean separation of concerns
```

**2. File I/O mixed with operations**
```python
# commands/filter.py
def filter(file_path: str, condition: str, output: str | None = None):
    # File I/O, filtering, and output all in one function
    # Can't reuse filtering logic without file handling
```

**3. Error messages CLI-specific**
```python
# Error types contain CLI-focused messages
class FilterError(Exception):
    """Error message designed for terminal output"""
```

### Real-World Impact

**Scenario 1: Wanting to use as Python library**
```python
# User wants to do this:
from excel_toolkit import filter_data

df = pd.read_csv('data.csv')
filtered = filter_data(df, 'age > 30')

# But can't! Operations expect file paths, not DataFrames
# No clean API for programmatic usage
```

**Scenario 2: Wanting to build web API**
```python
# Flask/FastAPI endpoint
@app.post("/filter")
def filter_endpoint(request: FilterRequest):
    # Want to reuse filtering logic
    # But operations are CLI-specific
    # Must re-implement everything
```

**Scenario 3: Wanting to use in Jupyter notebook**
```python
# Data scientist wants:
import excel_toolkit as et

df = et.load('data.xlsx')
df_filtered = et.filter(df, 'Amount > 1000')
df_grouped = et.group(df_filtered, 'Region')

# But no such API exists!
```

## Affected Architecture

**Current State** (bad):
- Operations layer designed for CLI
- File I/O mixed with business logic
- Error handling CLI-specific
- No public library API

**Desired State** (good):
- Operations layer CLI-agnostic
- Separate library API
- File I/O in separate layer
- Reusable in multiple contexts

## Proposed Solution

### 1. Create Library-Facing API

```python
# excel_toolkit/api/__init__.py

"""
Public library API for excel-toolkit.

Provides programmatic access to all operations without CLI dependencies.
"""

from excel_toolkit.api.dataframe import filter_rows, sort_rows, group_rows
from excel_toolkit.api.io import read_file, write_file
from excel_toolkit.api.types import FilterResult, GroupResult

__all__ = [
    'filter_rows',
    'sort_rows',
    'group_rows',
    'read_file',
    'write_file',
]
```

### 2. Implement Pure DataFrame Operations

```python
# excel_toolkit/api/dataframe.py

"""Pure DataFrame operations (no file I/O, no CLI dependencies)."""

import pandas as pd
from excel_toolkit.fp import Result
from excel_toolkit.models.error_types import FilterError

def filter_rows(
    df: pd.DataFrame,
    condition: str
) -> Result[pd.DataFrame, FilterError]:
    """
    Filter DataFrame rows based on condition.

    Pure function - no file I/O, no CLI dependencies.

    Args:
        df: Input DataFrame
        condition: Filter condition (pandas query syntax)

    Returns:
        Filtered DataFrame or error

    Examples:
        >>> df = pd.DataFrame({'age': [25, 30, 35]})
        >>> result = filter_rows(df, 'age > 30')
        >>> filtered = unwrap(result)
        >>> len(filtered)
        1
    """
    from excel_toolkit.operations.filtering import normalize_condition, apply_filter

    # Use existing operations but don't handle files
    normalized = normalize_condition(condition, df)
    if normalized.is_err():
        return normalized  # type: ignore

    return apply_filter(df, condition)

def sort_rows(
    df: pd.DataFrame,
    by: str | list[str],
    ascending: bool = True
) -> Result[pd.DataFrame, ValidationError]:
    """Sort DataFrame by column(s)."""
    # Implementation...

def group_rows(
    df: pd.DataFrame,
    by: str | list[str],
    aggregations: dict[str, list[str]]
) -> Result[pd.DataFrame, AggregationError]:
    """Group and aggregate DataFrame."""
    # Implementation...
```

### 3. Separate File I/O Layer

```python
# excel_toolkit/api/io.py

"""File I/O operations (separate from business logic)."""

from pathlib import Path
from excel_toolkit.fp import Result
from excel_toolkit.models.error_types import FileHandlerError
from excel_toolkit.core import HandlerFactory

def read_file(
    path: str | Path,
    sheet: str | int = 0,
    **kwargs
) -> Result[pd.DataFrame, FileHandlerError]:
    """
    Read Excel/CSV file into DataFrame.

    Args:
        path: File path
        sheet: Sheet name or index (for Excel)
        **kwargs: Additional pandas parameters

    Returns:
        DataFrame or error

    Examples:
        >>> result = read_file('data.xlsx')
        >>> df = unwrap(result)
    """
    factory = HandlerFactory()
    return factory.read_file(Path(path), sheet_name=sheet, **kwargs)

def write_file(
    df: pd.DataFrame,
    path: str | Path,
    **kwargs
) -> Result[None, FileHandlerError]:
    """Write DataFrame to file."""
    factory = HandlerFactory()
    return factory.write_file(df, Path(path), **kwargs)
```

### 4. Keep CLI as Thin Wrapper

```python
# commands/filter.py (refactored)

from excel_toolkit.api import read_file, write_file, filter_rows

def filter(
    file_path: str = typer.Argument(...),
    condition: str = typer.Argument(...),
    output: str | None = typer.Option(None),
    ...
):
    """CLI command for filtering (thin wrapper)."""

    # Use library API
    df_result = read_file(file_path)
    if is_err(df_result):
        print_error(unwrap_err(df_result))
        raise typer.Exit(1)

    df = unwrap(df_result)

    # Filter using library API
    filtered_result = filter_rows(df, condition)
    if is_err(filtered_result):
        print_error(unwrap_err(filtered_result))
        raise typer.Exit(1)

    filtered = unwrap(filtered_result)

    # Write output
    if output:
        write_result = write_file(filtered, output)
        if is_err(write_result):
            print_error(unwrap_err(write_result))
            raise typer.Exit(1)
    else:
        display_table(filtered)
```

### 5. Usage Examples

```python
# As Python library
import pandas as pd
from excel_toolkit import filter_rows, group_rows, read_file

# Load and filter
df = pd.read_csv('sales.csv')
filtered = filter_rows(df, 'Amount > 1000')
grouped = group_rows(filtered.unwrap(), 'Region', {'Amount': ['sum']})

# Or use file I/O helpers
result = read_file('sales.xlsx')
df = result.unwrap()
# ... process ...

# In Jupyter notebook
%pip install excel-toolkit
import excel_toolkit as et

df = et.read('data.xlsx')
df_filtered = et.filter(df, 'age > 30')
df_filtered.plot()

# In FastAPI web service
from fastapi import FastAPI, UploadFile
from excel_toolkit import filter_rows

app = FastAPI()

@app.post("/analyze")
async def analyze(file: UploadFile, condition: str):
    df = pd.read_excel(file.file)
    result = filter_rows(df, condition)

    if result.is_ok():
        return {"data": result.unwrap().to_dict()}
    else:
        return {"error": str(result.unwrap_err())}
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     Public API Layer                     │
│         (excel_toolkit/api/__init__.py)                  │
│  - filter_rows(df, condition)                            │
│  - sort_rows(df, by)                                     │
│  - group_rows(df, by, agg)                               │
└────────────┬──────────────────────────────┬──────────────┘
             │                              │
    ┌────────▼─────────┐           ┌────────▼─────────┐
    │  CLI Layer       │           │  Library Layer   │
    │  (commands/)     │           │  (api/)          │
    │  - Thin wrappers │           │  - Pure functions│
    └────────┬─────────┘           └────────┬─────────┘
             │                              │
             └──────────┬───────────────────┘
                        │
             ┌──────────▼──────────┐
             │  Operations Layer   │
             │  (operations/)      │
             │  - Business logic   │
             └──────────┬──────────┘
                        │
             ┌──────────▼──────────┐
             │  File Handlers      │
             │  (core/file_handlers)│
             └─────────────────────┘
```

## Implementation Plan

1. **Phase 1**: Create `excel_toolkit/api/` with pure DataFrame functions
2. **Phase 2**: Refactor operations to be CLI-agnostic
3. **Phase 3**: Update CLI commands to use API layer
4. **Phase 4**: Add library documentation and examples
5. **Phase 5**: Test API independently from CLI

## Benefits

1. **Reusable as library**: Can be imported in Python code
2. **Web API ready**: Business logic separate from CLI
3. **Better testing**: Test operations without CLI dependencies
4. **Jupyter-friendly**: Data scientists can use programmatically
5. **Multiple interfaces**: Same core, different frontends

## Related Issues

- Violation of separation of concerns (#017)
- Circular import risks (#018)
