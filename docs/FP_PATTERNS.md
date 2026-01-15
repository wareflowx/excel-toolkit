# Functional Programming Patterns - Implementation Guide

## Overview

This document defines the specific functional programming patterns to be implemented in the Excel CLI Toolkit. All FP primitives are implemented in-house in the `fp/` module with zero external dependencies.

## Implementation Philosophy

All functional programming types are custom implementations with a **pure functional API**:

- **No external FP libraries**: No `returns`, `attrs`, `toolz`, or `pandera`
- **Custom implementations**: Result, Maybe, Pipeline, Immutable, Curry all built from scratch
- **Function-based API**: All constructors are functions, not classes
- **Classes are internal**: Implementation uses classes, but users only interact with functions
- **Type-safe**: Full type hints with mypy compatibility
- **Well-tested**: Unit tests + property-based tests with hypothesis
- **Documentation focused**: Clear usage patterns and examples

**Key Principle**: The public API is purely functional. Users call `ok(value)` not `Result.ok(value)` or `Ok(value)`. The classes exist internally, but the abstraction is complete.

## Public API Structure

### Functions as Constructors

Instead of class constructors:
```python
# NOT: Result.ok(value) or Ok(value)
# NOT: Maybe.some(value) or Some(value)

# YES: Functional constructors
from excel_toolkit.fp import ok, err, some, nothing

ok_value = ok(dataframe)
error_value = err(FileError("not found"))
some_value = some(sheet)
empty_value = nothing()
```

### Functions as Predicates

Instead of methods:
```python
# NOT: result.is_ok()
# NOT: result.is_some()

# YES: Functional predicates
from excel_toolkit.fp import is_ok, is_err, is_some, is_nothing

if is_ok(result):
    ...
```

### Functions as Operations

Instead of methods for some operations:
```python
# NOT: result.unwrap()
# NOT: result.unwrap_or(default)

# YES: Functional operations
from excel_toolkit.fp import unwrap, unwrap_or

value = unwrap(result)
value = unwrap_or(result, default)
```

### Method Chaining Preserved

Transformation methods remain as methods for fluent API:
```python
# Methods for chaining (returns object with methods)
result.map(lambda df: df.transform("Price"))
result.and_then(lambda df: filter_data(df, "Amount > 1000"))
maybe.map(lambda sheet: sheet.name)
maybe.and_then(lambda sheet: find_column(sheet, "Price"))
```

## Core Types

### Result Type

**Type Signature**: `Result[T, E] = Ok[T] | Err[E]`

**Purpose**: Represent operations that can fail

**Functional API**:

```python
# Import constructors and predicates
from excel_toolkit.fp import ok, err, is_ok, is_err, unwrap, unwrap_or

# Creation
ok_value = ok(dataframe)
error_value = err(FileError("File not found"))

# Predicates
if is_ok(ok_value):
    print("Success!")

if is_err(error_value):
    print("Error!")

# Transformation (method chaining - returns object)
result.map(lambda df: df.transform_column("Price", multiply=1.1))

# Chaining (method chaining - returns object)
result.and_then(lambda df: filter_data(df, "Amount > 1000"))

# Unwrapping (functions)
value = unwrap(result)
value = unwrap_or(result, default_dataframe)

# Fallback (method chaining)
result.or_else_try(lambda: read_csv_backup())
```

**Where to use**:
- All file I/O operations (core/)
- All data operations (operations/)
- All validation (utils/validators.py)
- Not in commands/ (only unwrap there)

### Maybe Type

**Type Signature**: `Maybe[T] = Some[T] | Nothing`

**Purpose**: Represent optional values

**Functional API**:

```python
# Import constructors and predicates
from excel_toolkit.fp import some, nothing, is_some, is_nothing
from excel_toolkit.fp import unwrap_or as unwrap_or_maybe

# Creation
some_value = some(sheet)
empty_value = nothing()

# Predicates
if is_some(some_value):
    print("Has value!")

if is_nothing(empty_value):
    print("Empty!")

# Transformation (method chaining)
maybe.map(lambda sheet: sheet.name)

# Chaining (method chaining)
maybe.and_then(lambda sheet: find_column(sheet, "Price"))

# Unwrapping (functions)
value = unwrap_or_maybe(maybe, default_sheet)
value = unwrap_or_else(maybe, lambda: create_default_sheet())
```

**Where to use**:
- Sheet/column lookups that may not exist
- Optional configuration values
- Template variable resolution

## Complete Functional API Reference

### Result Functions

```python
# Constructors
ok(value: T) -> Result[T, E]
err(error: E) -> Result[T, E]

# Predicates
is_ok(result: Result[T, E]) -> bool
is_err(result: Result[T, E]) -> bool

# Unwrapping
unwrap(result: Result[T, E]) -> T  # Raises if Err
unwrap_or(result: Result[T, E], default: T) -> T
unwrap_or_else(result: Result[T, E], fn: Callable[[], T]) -> T

# Conversion
to_result(value: Maybe[T], error: E) -> Result[T, E]
```

### Result Methods (Method Chaining)

```python
result.map(fn: Callable[[T], U]) -> Result[U, E]
result.and_then(fn: Callable[[T], Result[U, E]]) -> Result[U, E]
result.or_else(result: Result[T, E]) -> Result[T, E]
result.or_else_try(fn: Callable[[], Result[T, E]]) -> Result[T, E]
```

### Maybe Functions

```python
# Constructors
some(value: T) -> Maybe[T]
nothing() -> Maybe[T]

# Predicates
is_some(maybe: Maybe[T]) -> bool
is_nothing(maybe: Maybe[T]) -> bool

# Unwrapping
unwrap(maybe: Maybe[T]) -> T  # Raises if Nothing
unwrap_or(maybe: Maybe[T], default: T) -> T
unwrap_or_else(maybe: Maybe[T], fn: Callable[[], T]) -> T

# Conversion
to_maybe(result: Result[T, E]) -> Maybe[T]
```

### Maybe Methods (Method Chaining)

```python
maybe.map(fn: Callable[[T], U]) -> Maybe[U]
maybe.and_then(fn: Callable[[T], Maybe[U]]) -> Maybe[U]
maybe.or_else(value: T) -> T
```

## Composition Patterns

### Pipeline Pattern

**Purpose**: Compose operations in readable sequences

**Functional API**:

```python
# Import functional constructors
from excel_toolkit.fp import pipe

# Single operation
result = pipe(dataframe).then(filter_rows).finalize()

# Chained operations
result = (
    pipe(dataframe)
    .then(filter_valid_rows)
    .then(remove_duplicates)
    .then(group_by_region)
    .finalize()
)

# With Result types - use functional constructor
from excel_toolkit.fp import ok, pipe

result = (
    pipe(ok(dataframe))
    .then(lambda r: r.and_then(filter_valid_rows))
    .then(lambda r: r.and_then(remove_duplicates))
    .finalize()
)
```

**Where to use**:
- Template workflows (templates/)
- Complex data operations (operations/)
- File processing pipelines (core/file_manager.py)

### Function Composition

**Purpose**: Combine functions into new functions

**Functional API**:

```python
# Import functional composition
from excel_toolkit.fp import compose, compose_many

# Create composed function
clean_and_validate = compose(validate_schema, clean_data)

# Use composed function
result = clean_and_validate(dataframe)

# Multiple compositions
process_sales = compose_many(
    calculate_totals,
    group_by_region,
    remove_duplicates,
    filter_valid_rows
)
```

## Error Handling Patterns

### Error Accumulation

**Purpose**: Collect multiple errors instead of stopping at first

**Functional API**:

```python
from excel_toolkit.fp import ok, err, is_err

@dataclass(frozen=True)
class ValidationErrors:
    errors: List[ValidationError]

    def combine(self, other: ValidationErrors) -> ValidationErrors:
        return ValidationErrors(self.errors + other.errors)

    @staticmethod
    def empty() -> ValidationErrors:
        return ValidationErrors([])

# Usage - functional constructors
def validate_all_columns(df: DataFrame, columns: List[str]):
    results = [validate_column(col) for col in columns]

    errors = [unwrap_err(r) for r in results if is_err(r)]
    if errors:
        return err(ValidationErrors(errors))

    return ok(None)
```

### Fallback Chain

**Purpose**: Try multiple alternatives in sequence

**Functional API**:

```python
from excel_toolkit.fp import ok, pipe

# Method chaining on returned object
result = (
    try_read_excel(path)
    .or_else_try(lambda: try_read_csv(path))
    .or_else_try(lambda: try_read_json(path))
)
```

### Early Exit Pattern

**Purpose**: Stop processing on first error

**Functional API**:

```python
from excel_toolkit.fp import ok

# Using functional constructor + method chaining
def process_pipeline(df: DataFrame):
    return (
        ok(df)
        .and_then(validate_data)
        .and_then(clean_data)
        .and_then(transform_data)
        .and_then(write_output)
    )
    # Stops at first Err, returns that error
```

## Validation Patterns

### Validator Composition

**Purpose**: Build complex validators from simple ones

**Functional API**:

```python
from excel_toolkit.fp import ok
from typing import Callable

Validator = Callable[[T], Result[T, ValidationError]]

def compose_validators(*validators: Validator[T]) -> Validator[T]:
    """Compose multiple validators that all must pass"""
    def validate(value: T) -> Result[T, ValidationError]:
        result = ok(value)
        for validator in validators:
            result = result.and_then(lambda v: validator(v))
        return result
    return validate

# Usage
validate_price = compose_validators(
    validate_not_empty,
    validate_is_numeric,
    validate_is_positive,
    validate_max_decimal_places(2)
)
```

### Conditional Validation

**Purpose**: Validate based on conditions

**Functional API**:

```python
from excel_toolkit.fp import ok

def validate_if(
    condition: Callable[[T], bool],
    validator: Validator[T]
) -> Validator[T]:
    """Apply validator only if condition is true"""
    def validate(value: T) -> Result[T, ValidationError]:
        if condition(value):
            return validator(value)
        return ok(value)
    return validate

# Usage
validate_age = validate_if(
    lambda x: x is not None,
    compose_validators(
        validate_is_numeric,
        validate_range(0, 120)
    )
)
```

## Operation Factory Patterns

### Curried Operations

**Purpose**: Create specialized operations from general ones

**Functional API**:

```python
from excel_toolkit.fp import curry

# Curried function factory
@curry
def filter_by_column(df: DataFrame, column: str, condition: str):
    """Curried filter function"""
    ...

# Create specialized versions
filter_by_price = filter_by_column(column="Price")
filter_expensive = filter_by_price(condition="> 1000")

# Use specialized versions
result = filter_expensive(dataframe)
```

### Partial Application

**Purpose**: Fix some parameters, leave others variable

**Functional API**:

```python
from excel_toolkit.fp import partial_apply

# Partial application function
read_csv_with_comma = partial_apply(read_csv, delimiter=",")
read_csv_with_semicolon = partial_apply(read_csv, delimiter=";")
```

## Immutable Data Patterns

### Immutable Configuration

**Purpose**: Prevent modification of configuration after creation

**Functional API**:

```python
from excel_toolkit.fp import frozen_dataclass

# Functional decorator
@frozen_dataclass
class FilterConfig:
    condition: str
    column: str
    case_sensitive: bool = False

config = FilterConfig(condition="> 100", column="Price")
# config.condition = "new value"  # Raises AttributeError
```

### Immutable DataFrame Wrapper

**Purpose**: Prevent accidental DataFrame mutation

**Functional API**:

```python
from excel_toolkit.fp import immutable_df

# Functional constructor
df_immutable = immutable_df(dataframe)

# Functional operations
df_transformed = transform_df(df_immutable, lambda df: df.query("Price > 100"))
df_final = to_pandas(df_immutable)
```

## Testing Patterns

### Property-Based Testing

**Functional API**:

```python
from hypothesis import given, strategies as st
from excel_toolkit.fp import ok

@given(st.dataframes(min_size=0, max_size=100))
def test_result_functor_identity(df):
    """map(id) == id"""
    result = ok(df)
    assert result.map(lambda x: x) == result

@given(st.dataframes(), st.functions(), st.functions())
def test_result_functor_composition(df, f, g):
    """map(f . g) == map(f) . map(g)"""
    result = ok(df)

    compose_f_g = lambda x: f(g(x))

    left = result.map(compose_f_g)
    right = result.map(g).map(f)

    assert left == right
```

### Round-Trip Testing

**Functional API**:

```python
from hypothesis import given, strategies as st

@given(st.dataframes())
def test_excel_csv_round_trip(df):
    """Converting Excel -> CSV -> Excel preserves data"""
    excel_path = write_temp_excel(df)
    csv_path = convert_to_csv(excel_path)
    final_path = convert_to_excel(csv_path)
    result_df = read_excel(final_path)
    assert dataframes_equal(df, result_df)
```

## Module-Specific Patterns

### core/file_manager.py

**Functional API throughout**:

```python
from excel_toolkit.fp import ok, err, some, nothing, is_nothing, unwrap_or_else

def read_file(path: Path):
    """Read file, auto-detect format"""
    format_detected = detect_format(path)  # Returns Maybe[FileFormat]

    if is_nothing(format_detected):
        return err(UnknownFormatError(path))

    fmt = unwrap(format_detected)
    return get_handler(fmt).read(path)

def detect_format(path: Path):
    """Detect format from extension"""
    ext = path.suffix.lower()
    return FORMAT_MAP.get(ext, nothing())
```

### utils/validators.py

**Functional API throughout**:

```python
from excel_toolkit.fp import ok

def validate_condition(condition: str):
    """Parse and validate filter condition"""
    return (
        ok(condition)
        .and_then(parse_condition)
        .and_then(validate_syntax)
        .and_then(validate_columns_exist)
        .and_then(validate_types_match)
    )
```

### templates/clean_csv.py

**Functional API throughout**:

```python
from excel_toolkit.fp import ok, pipe

def clean_csv_template(df: DataFrame):
    """Apply standard CSV cleaning pipeline"""
    return (
        pipe(ok(df))
        .then(lambda r: r.and_then(trim_whitespace))
        .then(lambda r: r.and_then(remove_duplicates))
        .then(lambda r: r.and_then(validate_schema))
        .then(lambda r: r.and_then(standardize_formats))
        .finalize()
    )
```

### commands/base.py

**Functional API for unwrapping only**:

```python
from excel_toolkit.fp import is_ok, unwrap, unwrap_err

def handle_result(result):
    """Unwrap Result in commands layer only"""
    if is_ok(result):
        return unwrap(result)
    else:
        error = unwrap_err(result)
        typer.echo(f"Error: {error.message}", err=True)
        raise typer.Exit(code=error.exit_code)
```

## Implementation Checklist

### Phase 1: Foundation (Functional API)

- [ ] Implement Result type (fp/result.py) - classes internal
- [ ] Implement functional constructors: ok(), err()
- [ ] Implement functional predicates: is_ok(), is_err()
- [ ] Implement functional unwrappers: unwrap(), unwrap_or()
- [ ] Implement Maybe type (fp/maybe.py) - classes internal
- [ ] Implement functional constructors: some(), nothing()
- [ ] Implement functional predicates: is_some(), is_nothing()
- [ ] Add basic tests for functional API
- [ ] Add property-based tests for functor laws

### Phase 2: Integration

- [ ] Refactor file operations to use functional Result API
- [ ] Refactor validation to use functional Result API
- [ ] Add functional Maybe API to lookups (sheets, columns)
- [ ] Update tests for refactored code
- [ ] Ensure no class constructors are exposed publicly

### Phase 3: Composition

- [ ] Implement Pipeline class (fp/pipeline.py)
- [ ] Implement functional pipe() constructor
- [ ] Add functional compose(), compose_many()
- [ ] Create validator composition helpers
- [ ] Add operation factory patterns with functional API

### Phase 4: Advanced

- [ ] Add frozen_dataclass functional decorator
- [ ] Implement immutable_df functional constructor
- [ ] Implement error accumulation with functional API
- [ ] Add comprehensive property tests
- [ ] Document all functional patterns

## Best Practices

### DO

- Use functional constructors: ok(), err(), some(), nothing()
- Use functional predicates: is_ok(), is_some()
- Use functional unwrappers: unwrap(), unwrap_or()
- Return Result from all fallible operations
- Use Maybe for optional values
- Compose operations with and_then/map
- Make configuration models immutable with @frozen_dataclass
- Test functor/monad laws with property tests
- Unwrap Results only in commands layer
- Keep classes internal to fp/ module

### DON'T

- Use class constructors: Result.ok(), Ok(), Some()
- Use class methods: result.is_ok(), maybe.is_some()
- Expose classes in public API
- Raise exceptions from operations
- Return None (use Maybe instead)
- Mutate configuration after creation
- Ignore Result types in operations
- Wrap exceptions in Result (return Err directly)
- Create cyclic dependencies between fp/ and other modules

## Common Mistakes

### Mistake 1: Using Class Constructors

```python
# BAD - using class constructors
result = Result.ok(dataframe)
error = Result.err(FileError("not found"))
maybe = Maybe.some(sheet)

# GOOD - using functional constructors
result = ok(dataframe)
error = err(FileError("not found"))
maybe = some(sheet)
```

### Mistake 2: Using Method Predicates

```python
# BAD - using method predicates
if result.is_ok():
    ...

if maybe.is_some():
    ...

# GOOD - using functional predicates
if is_ok(result):
    ...

if is_some(maybe):
    ...
```

### Mistake 3: Using Method Unwrappers

```python
# BAD - using method unwrappers
value = result.unwrap()
value = result.unwrap_or(default)

# GOOD - using functional unwrappers
value = unwrap(result)
value = unwrap_or(result, default)
```

### Mistake 4: Wrapping Exceptions

```python
# BAD
def read_file(path: Path):
    try:
        df = pandas.read_excel(path)
        return ok(df)
    except Exception as e:
        return err(FileError(str(e)))

# GOOD
def read_file(path: Path):
    if not path.exists():
        return err(FileNotFound(path))
    if not path.is_readable():
        return err(PermissionError(path))
    df = pandas.read_excel(path)
    return ok(df)
```

### Mistake 5: Ignoring Result Types

```python
# BAD
def filter_data(df: DataFrame, condition: str) -> DataFrame:
    result = parse_condition(condition)
    parsed = unwrap(result)  # Crashes if err!
    return df.query(parsed)

# GOOD
def filter_data(df: DataFrame, condition: str):
    return (
        parse_condition(condition)
        .and_then(lambda parsed: ok(df.query(parsed)))
    )
```

### Mistake 6: Exposing Classes

```python
# BAD - exposing classes in __init__.py
from excel_toolkit.fp import Result, Ok, Err, Maybe, Some, Nothing

# GOOD - only exposing functions
from excel_toolkit.fp import ok, err, some, nothing, is_ok, is_some
```

## Public API Summary

### What Users Import

```python
# Result API
from excel_toolkit.fp import (
    ok, err,
    is_ok, is_err,
    unwrap, unwrap_or, unwrap_or_else,
    to_result, to_maybe
)

# Maybe API
from excel_toolkit.fp import (
    some, nothing,
    is_some, is_nothing,
    unwrap as unwrap_maybe,
    unwrap_or as unwrap_or_maybe
)

# Pipeline API
from excel_toolkit.fp import (
    pipe, compose, compose_many
)

# Immutable API
from excel_toolkit.fp import (
    frozen_dataclass,
    immutable, immutable_df
)

# Curry API
from excel_toolkit.fp import (
    curry, partial_apply, flip
)
```

### What Users Never Import

```python
# NEVER exposed in public API
from excel_toolkit.fp import Result  # NO
from excel_toolkit.fp import Ok, Err  # NO
from excel_toolkit.fp import Maybe, Some, Nothing  # NO
from excel_toolkit.fp import Pipeline  # NO (use pipe())
```

## Migration Strategy

When migrating existing code to use functional FP patterns:

1. **Start with functional constructors**: Replace class constructors with ok(), err(), some(), nothing()
2. **Replace method predicates**: Convert result.is_ok() to is_ok(result)
3. **Replace method unwrappers**: Convert result.unwrap() to unwrap(result)
4. **Keep method chaining**: Preserve result.map(), result.and_then() for fluent API
5. **Start with leaf functions**: Begin with functions that don't depend on other operations
6. **Work backwards**: Migrate from operations -> core -> commands
7. **Keep tests passing**: Migrate incrementally, maintaining test coverage
8. **Update type hints**: Ensure signatures reflect Result/Maybe usage
9. **Document patterns**: Add examples to this doc as you discover new patterns

## Module Organization (fp/)

```
fp/
├── __init__.py              # Public API: only functions
├── _result.py               # Internal: Result class (private)
├── _maybe.py                # Internal: Maybe class (private)
├── _pipeline.py             # Internal: Pipeline class (private)
├── result.py                # Public: ok, err, is_ok, unwrap, etc.
├── maybe.py                 # Public: some, nothing, is_some, etc.
├── pipeline.py              # Public: pipe, compose, etc.
├── immutable.py             # Public: frozen_dataclass, immutable, etc.
└── curry.py                 # Public: curry, partial_apply, etc.
```

**Convention**: Files starting with `_` are internal implementation details. Public API files contain only functions.
