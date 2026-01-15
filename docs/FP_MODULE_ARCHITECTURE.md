# FP Module Architecture

## Overview

The `fp/` module contains all custom functional programming primitives for the Excel CLI Toolkit. This document outlines the architecture and implementation details of each component.

## Key Architectural Principle

**Functional Public API, Class-based Internal Implementation**

- **Users interact with functions only**: `ok(value)`, `err(error)`, `some(value)`, `nothing()`
- **Classes are internal implementation**: `_Result`, `_Ok`, `_Err`, `_Maybe`, `_Some`, `_Nothing`
- **Method chaining preserved**: Objects returned by functions have `.map()`, `.and_then()` methods
- **Predicates and operations are functions**: `is_ok(result)`, `unwrap(result)`

This creates a pure functional abstraction while maintaining the benefits of method chaining for transformations.

## Module Structure

```
excel_toolkit/fp/
├── __init__.py              # Public API exports (functions only)
├── _result.py               # Internal: Result, Ok, Err classes (private)
├── _maybe.py                # Internal: Maybe, Some, Nothing classes (private)
├── _pipeline.py             # Internal: Pipeline class (private)
├── result.py                # Public: ok, err, is_ok, unwrap, etc.
├── maybe.py                 # Public: some, nothing, is_some, etc.
├── pipeline.py              # Public: pipe, compose, compose_many
├── functor.py               # Public: map, and_then, or_else helpers
├── monad.py                 # Public: bind, join utilities
├── immutable.py             # Public: frozen_dataclass, immutable_df
└── curry.py                 # Public: curry, partial_apply, flip
```

**Convention**: Files starting with `_` are private implementation details. They contain the actual class definitions.

## Component Specifications

### _result.py - Internal Result Classes

**Purpose**: Internal implementation of Result type using classes

**Class Definitions**:

```python
from typing import TypeVar, Generic
from abc import ABC, abstractmethod
from dataclasses import dataclass

T = TypeVar('T')
E = TypeVar('E')

class Result(ABC, Generic[T, E]):
    """Base class for Result type - internal only"""

    @abstractmethod
    def map(self, fn):
        """Apply function if Ok, pass through if Err"""
        pass

    @abstractmethod
    def and_then(self, fn):
        """Chain Result-returning function"""
        pass

    @abstractmethod
    def or_else(self, default):
        """Provide default value if Err"""
        pass

@dataclass(frozen=True)
class Ok(Result[T, E]):
    """Success variant - internal only"""
    _value: T

    def map(self, fn):
        return Ok(fn(self._value))

    def and_then(self, fn):
        return fn(self._value)

    def or_else(self, default):
        return self  # Ok ignores or_else

@dataclass(frozen=True)
class Err(Result[T, E]):
    """Error variant - internal only"""
    _error: E

    def map(self, fn):
        return self  # Err ignores map

    def and_then(self, fn):
        return self  # Err ignores and_then

    def or_else(self, default):
        return default
```

**Key Methods** (internal, exposed via functions in result.py):
- `map(fn)`: Apply function to Ok value
- `and_then(fn)`: Chain operations that return Result
- `or_else(default)`: Provide fallback Result

**Implementation Notes**:
- Use Generic[T, E] for full type safety
- Use @dataclass(frozen=True) for immutability
- Implement `__eq__` for value comparison
- These classes are NOT exposed in public API

### result.py - Public Result Functions

**Purpose**: Public functional API for Result type

**Function Definitions**:

```python
# Import internal classes
from ._result import Ok, Err

# Constructors
def ok(value: T) -> Result[T, E]:
    """Create Ok result"""
    return Ok(value)

def err(error: E) -> Result[T, E]:
    """Create Err result"""
    return Err(error)

# Predicates
def is_ok(result: Result[T, E]) -> bool:
    """Check if result is Ok"""
    return isinstance(result, Ok)

def is_err(result: Result[T, E]) -> bool:
    """Check if result is Err"""
    return isinstance(result, Err)

# Unwrapping
def unwrap(result: Result[T, E]) -> T:
    """Extract Ok value, raise if Err"""
    if is_ok(result):
        return result._value  # Access internal attribute
    raise UnwrapError("Cannot unwrap Err")

def unwrap_or(result: Result[T, E], default: T) -> T:
    """Extract Ok value or default"""
    if is_ok(result):
        return result._value
    return default

def unwrap_or_else(result: Result[T, E], fn: Callable[[], T]) -> T:
    """Extract Ok value or compute default"""
    if is_ok(result):
        return result._value
    return fn()

def unwrap_err(result: Result[T, E]) -> E:
    """Extract Err error, raise if Ok"""
    if is_err(result):
        return result._error
    raise UnwrapError("Cannot unwrap Ok")

# Conversion
def to_result(maybe: Maybe[T], error: E) -> Result[T, E]:
    """Convert Maybe to Result"""
    if is_some(maybe):
        return ok(maybe._value)
    return err(error)
```

**Public API**:
- `ok(value)`, `err(error)`: Constructors
- `is_ok(result)`, `is_err(result)`: Predicates
- `unwrap(result)`, `unwrap_or(result, default)`: Unwrappers
- `to_result(maybe, error)`: Conversion

### _maybe.py - Internal Maybe Classes

**Purpose**: Internal implementation of Maybe type using classes

**Class Definitions**:

```python
from typing import TypeVar, Generic
from dataclasses import dataclass

T = TypeVar('T')

class Maybe(ABC, Generic[T]):
    """Base class for Maybe type - internal only"""
    pass

@dataclass(frozen=True)
class Some(Maybe[T]):
    """Value present variant - internal only"""
    _value: T

    def map(self, fn):
        return Some(fn(self._value))

    def and_then(self, fn):
        return fn(self._value)

@dataclass(frozen=True)
class Nothing(Maybe[T]):
    """Value absent variant - internal only (singleton)"""
    __slots__ = ()  # Singleton pattern

    def map(self, fn):
        return self  # Nothing ignores map

    def and_then(self, fn):
        return self  # Nothing ignores and_then

# Singleton instance
_NOTHING = Nothing()
```

**Implementation Notes**:
- Nothing is a singleton (only one instance)
- Support conversion between Maybe and Result
- Implement `__eq__` for value comparison
- These classes are NOT exposed in public API

### maybe.py - Public Maybe Functions

**Purpose**: Public functional API for Maybe type

**Function Definitions**:

```python
# Import internal classes
from ._maybe import Some, _NOTHING

# Constructors
def some(value: T) -> Maybe[T]:
    """Create Some with value"""
    return Some(value)

def nothing() -> Maybe[T]:
    """Create Nothing (singleton)"""
    return _NOTHING

# Predicates
def is_some(maybe: Maybe[T]) -> bool:
    """Check if maybe has value"""
    return isinstance(maybe, Some)

def is_nothing(maybe: Maybe[T]) -> bool:
    """Check if maybe is empty"""
    return isinstance(maybe, Nothing)

# Unwrapping
def unwrap(maybe: Maybe[T]) -> T:
    """Extract Some value, raise if Nothing"""
    if is_some(maybe):
        return maybe._value
    raise UnwrapError("Cannot unwrap Nothing")

def unwrap_or(maybe: Maybe[T], default: T) -> T:
    """Extract Some value or default"""
    if is_some(maybe):
        return maybe._value
    return default

def unwrap_or_else(maybe: Maybe[T], fn: Callable[[], T]) -> T:
    """Extract Some value or compute default"""
    if is_some(maybe):
        return maybe._value
    return fn()

# Conversion
def to_maybe(result: Result[T, E]) -> Maybe[T]:
    """Convert Result to Maybe (lose error info)"""
    if is_ok(result):
        return some(result._value)
    return nothing()
```

**Public API**:
- `some(value)`, `nothing()`: Constructors
- `is_some(maybe)`, `is_nothing(maybe)`: Predicates
- `unwrap(maybe)`, `unwrap_or(maybe, default)`: Unwrappers
- `to_maybe(result)`: Conversion

### _pipeline.py - Internal Pipeline Class

**Purpose**: Internal implementation of Pipeline using class

**Class Definition**:

```python
from typing import TypeVar, Callable

T = TypeVar('T')

class Pipeline(Generic[T]):
    """Fluent interface for function composition - internal only"""

    def __init__(self, value: T):
        self._value = value

    def then(self, fn: Callable) -> Pipeline:
        """Apply function to current value"""
        return Pipeline(fn(self._value))

    def finalize(self) -> T:
        """Extract final value from pipeline"""
        return self._value
```

### pipeline.py - Public Pipeline Functions

**Purpose**: Public functional API for Pipeline

**Function Definitions**:

```python
# Import internal class
from ._pipeline import Pipeline

def pipe(value: T) -> Pipeline:
    """Start a pipeline from a value"""
    return Pipeline(value)

def compose(f: Callable, g: Callable) -> Callable:
    """Compose two functions: f(g(x))"""
    return lambda x: f(g(x))

def compose_many(*functions: Callable) -> Callable:
    """Compose multiple functions right-to-left"""
    return reduce(compose, functions)
```

**Public API**:
- `pipe(value)`: Start pipeline
- `compose(f, g)`: Compose two functions
- `compose_many(f1, f2, ...)`: Compose multiple functions

### functor.py - Functor Utilities

**Purpose**: Functional utilities for functor operations

**Function Definitions**:

```python
def map(fn: Callable, *functors):
    """Apply function over multiple functor values"""
    if len(functors) == 1:
        return functors[0].map(fn)
    # Multiple functor support for advanced usage
    ...

def fmap(fn: Callable):
    """Partially applied map for composition"""
    return lambda functor: functor.map(fn)
```

### monad.py - Monad Utilities

**Purpose**: Functional utilities for monad operations

**Function Definitions**:

```python
def bind(fn: Callable, monad):
    """Partially applied and_then for composition"""
    return monad.and_then(fn)

def join(monad):
    """Flatten nested monads"""
    ...

def lift_m2(fn: Callable, m1: Monad, m2: Monad) -> Monad:
    """Lift binary function to work with monads"""
    return m1.and_then(lambda x1: m2.map(lambda x2: fn(x1, x2)))
```

### immutable.py - Immutable Helpers

**Purpose**: Functional API for immutable data structures

**Function Definitions**:

```python
def frozen_dataclass(cls):
    """Decorator to make dataclass immutable"""
    return immutable(dataclass(cls))

def immutable(cls):
    """Class decorator to make class immutable"""
    original_post_init = getattr(cls, '__post_init__', None)

    def __post_init__(self):
        if original_post_init:
            original_post_init(self)
        object.__setattr__(self, '__frozen__', True)

    cls.__post_init__ = __post_init__

    def __setattr__(self, name, value):
        if getattr(self, '__frozen__', False):
            raise AttributeError(f"Cannot modify frozen {cls.__name__}")
        object.__setattr__(self, name, value)

    return cls

def immutable_df(df: DataFrame) -> ImmutableDataFrame:
    """Create immutable DataFrame wrapper"""
    return ImmutableDataFrame(df)

def to_pandas(immutable_df: ImmutableDataFrame) -> DataFrame:
    """Extract pandas DataFrame from immutable wrapper"""
    return immutable_df.to_pandas()

def transform_df(immutable_df: ImmutableDataFrame, fn: Callable) -> ImmutableDataFrame:
    """Apply transformation, return new immutable wrapper"""
    return immutable_df.transform(fn)
```

**Public API**:
- `frozen_dataclass`: Decorator for immutable dataclasses
- `immutable`: Generic immutable decorator
- `immutable_df(df)`: Create immutable DataFrame
- `to_pandas(immutable_df)`: Extract DataFrame
- `transform_df(immutable_df, fn)`: Transform immutably

### curry.py - Currying Helpers

**Purpose**: Functional API for currying and partial application

**Function Definitions**:

```python
import functools

def curry(func: Callable) -> Callable:
    """Convert function to curried form"""
    @functools.wraps(func)
    def curried(*args):
        if len(args) >= func.__code__.co_argcount:
            return func(*args)
        return lambda *more: curried(*(args + more))
    return curried

def partial_apply(func: Callable, **kwargs) -> Callable:
    """Partially apply function with keyword arguments"""
    @functools.wraps(func)
    def partial(*args, **more_kwargs):
        all_kwargs = {**kwargs, **more_kwargs}
        return func(*args, **all_kwargs)
    return partial

def flip(func: Callable) -> Callable:
    """Flip first two arguments of function"""
    @functools.wraps(func)
    def flipped(*args):
        if len(args) < 2:
            return func(*args)
        return func(args[1], args[0], *args[2:])
    return flipped
```

**Public API**:
- `curry(fn)`: Convert to curried form
- `partial_apply(fn, **kwargs)`: Fix some arguments
- `flip(fn)`: Reverse first two arguments

## Public API (fp/__init__.py)

```python
"""
Functional programming primitives for Excel CLI Toolkit.

All types are implemented in-house with zero external dependencies.
Public API is purely functional - classes are internal implementation details.
"""

# Result API - functions only
from .result import (
    ok, err,
    is_ok, is_err,
    unwrap, unwrap_or, unwrap_or_else, unwrap_err,
    to_result
)

# Maybe API - functions only
from .maybe import (
    some, nothing,
    is_some, is_nothing,
    unwrap as unwrap_maybe,
    unwrap_or as unwrap_or_maybe,
    unwrap_or_else as unwrap_or_else_maybe,
    to_maybe
)

# Pipeline API
from .pipeline import pipe, compose, compose_many

# Immutable API
from .immutable import frozen_dataclass, immutable, immutable_df, to_pandas, transform_df

# Curry API
from .curry import curry, partial_apply, flip

# Functor/Monad utilities
from .functor import fmap
from .monad import bind, join, lift_m2

__all__ = [
    # Result
    'ok', 'err',
    'is_ok', 'is_err',
    'unwrap', 'unwrap_or', 'unwrap_or_else', 'unwrap_err',
    'to_result',
    # Maybe
    'some', 'nothing',
    'is_some', 'is_nothing',
    'unwrap_maybe', 'unwrap_or_maybe', 'unwrap_or_else_maybe',
    'to_maybe',
    # Pipeline
    'pipe', 'compose', 'compose_many',
    # Immutable
    'frozen_dataclass', 'immutable', 'immutable_df', 'to_pandas', 'transform_df',
    # Curry
    'curry', 'partial_apply', 'flip',
    # Functor/Monad
    'fmap', 'bind', 'join', 'lift_m2',
]
```

**Important**: No classes (Result, Ok, Err, Maybe, Some, Nothing, Pipeline) are exported.

## Testing Strategy

### Unit Tests (tests/unit/test_fp_*.py)

**test_fp_result.py**:
```python
from excel_toolkit.fp import ok, err, is_ok, is_err, unwrap

def test_ok_creation():
    result = ok(42)
    assert is_ok(result)

def test_err_creation():
    result = err("error")
    assert is_err(result)

def test_unwrap_ok():
    result = ok(42)
    assert unwrap(result) == 42

def test_unwrap_err_raises():
    result = err("error")
    with pytest.raises(UnwrapError):
        unwrap(result)
```

**test_fp_maybe.py**:
```python
from excel_toolkit.fp import some, nothing, is_some, unwrap

def test_some_creation():
    maybe = some(42)
    assert is_some(maybe)

def test_nothing_singleton():
    m1 = nothing()
    m2 = nothing()
    assert m1 is m2  # Same instance
```

**test_fp_pipeline.py**:
```python
from excel_toolkit.fp import pipe, compose

def test_pipe_single():
    result = pipe(5).then(lambda x: x * 2).finalize()
    assert result == 10

def test_compose():
    f = compose(lambda x: x + 1, lambda x: x * 2)
    assert f(5) == 11  # (5 * 2) + 1
```

### Property-Based Tests (tests/properties/test_fp_*.py)

**test_fp_functor_laws.py**:
```python
from hypothesis import given
from excel_toolkit.fp import ok

@given(st.integers())
def test_result_functor_identity(x):
    """map(id) == id"""
    result = ok(x)
    assert result.map(lambda y: y) == result
```

**test_fp_monad_laws.py**:
```python
@given(st.integers())
def test_result_left_identity(x):
    """ok(x).and_then(f) == f(x)"""
    f = lambda n: ok(n + 1)
    result = ok(x)
    left = result.and_then(f)
    right = f(x)
    assert left == right
```

## Implementation Priority

### Phase 1: Core Types (Foundation)

1. **_result.py**: Implement Result, Ok, Err classes
   - Basic construction and internal structure
   - map(), and_then(), or_else() methods
   - Immutability with frozen dataclass

2. **result.py**: Implement public functional API
   - ok(), err() constructors
   - is_ok(), is_err() predicates
   - unwrap(), unwrap_or() functions
   - Unit tests for functional API

3. **_maybe.py**: Implement Maybe, Some, Nothing classes
   - Basic construction and Nothing singleton
   - map(), and_then() methods

4. **maybe.py**: Implement public functional API
   - some(), nothing() constructors
   - is_some(), is_nothing() predicates
   - unwrap(), unwrap_or() functions
   - Unit tests for functional API

### Phase 2: Composition

5. **_pipeline.py**: Implement Pipeline class
   - Basic structure with then(), finalize()

6. **pipeline.py**: Implement public functional API
   - pipe() constructor
   - compose(), compose_many() functions
   - Integration with Result/Maybe

7. **curry.py**: Implement currying helpers
   - curry(), partial_apply(), flip()
   - Type preservation

### Phase 3: Advanced Patterns

8. **immutable.py**: Immutable dataclass decorator
   - frozen_dataclass, immutable decorators
   - immutable_df(), to_pandas(), transform_df()

9. **functor.py** and **monad.py**: Functional utilities
   - fmap, bind, join, lift_m2
   - Property-based tests for laws

## Type Safety Considerations

### Generic Types

All FP types use proper generics:

```python
# Good: Type-safe functions
ok(value: DataFrame) -> Result[DataFrame, FileError]
err(error: FileError) -> Result[DataFrame, FileError]

# Bad: Not type-safe
ok(value)  # What are the types?
```

### Type Hints

All functions must have complete type hints:

```python
def ok(value: T) -> Result[T, Any]:
    """Create Ok result with value"""
    return Ok(value)

def unwrap(result: Result[T, E]) -> T:
    """Extract value from Ok result"""
    ...
```

### Mypy Compatibility

All implementations must pass mypy strict mode:

```bash
uv run mypy --strict excel_toolkit/fp/
```

## Integration Points

### With core/ Module

```python
# core/file_manager.py
from excel_toolkit.fp import ok, err, is_nothing, unwrap

def read_file(path: Path):
    if not path.exists():
        return err(FileNotFound(path))

    df = pandas.read_excel(path)
    return ok(df)
```

### With operations/ Module

```python
# operations/filtering.py
from excel_toolkit.fp import ok

def filter_data(df: DataFrame, condition: str):
    parsed = parse_condition(condition)
    if is_err(parsed):
        return parsed  # Return Err directly

    return ok(df.query(unwrap(parsed)))
```

### With utils/ Module

```python
# utils/validators.py
from excel_toolkit.fp import ok, err

def validate_column_name(name: str):
    if not name:
        return err(ValidationError("Empty column name"))
    return ok(name)
```

## Performance Considerations

### Immutability

- Use @dataclass(frozen=True) for zero-copy immutability
- Defensive copies where necessary
- Consider __slots__ for performance-critical types

### Function Call Overhead

- Minimize wrapper functions
- Direct class method calls for chaining (no wrapper overhead)
- Profile before optimizing

### Memory Usage

- Ok/Err are lightweight (single attribute)
- Some/Nothing are lightweight (Nothing is singleton)
- Pipeline creates intermediate objects (acceptable for typical usage)

## Common Implementation Patterns

### Pattern 1: Function Delegates to Class

```python
# result.py
def ok(value: T) -> Result[T, E]:
    """Public functional constructor"""
    return Ok(value)  # Delegate to internal class

# _result.py
@dataclass(frozen=True)
class Ok(Result[T, E]):
    _value: T
    # Internal implementation
```

### Pattern 2: Predicate Uses isinstance

```python
# result.py
def is_ok(result: Result[T, E]) -> bool:
    """Public functional predicate"""
    return isinstance(result, Ok)  # Check internal class
```

### Pattern 3: Unwrap Accesses Internal Attribute

```python
# result.py
def unwrap(result: Result[T, E]) -> T:
    """Public functional unwrapper"""
    if is_ok(result):
        return result._value  # Access internal attribute
    raise UnwrapError("Cannot unwrap Err")
```

## Documentation Requirements

Each module must have:

1. **Module docstring**: Purpose and usage overview
2. **Function docstrings**: Parameters, returns, examples
3. **Type hints**: Complete type annotations
4. **Usage examples**: In docstrings or separate examples/

## Error Handling

All FP functions should:

- Never raise exceptions (except unwrap on Err/Nothing)
- Return Err or Nothing for failure cases
- Use explicit types for errors
- Provide clear error messages

## Summary

This architecture provides:

1. **Pure functional public API**: Users only interact with functions
2. **Class-based internal implementation**: Clean implementation with classes
3. **Method chaining preserved**: Fluent API for transformations
4. **Type-safe**: Full generic type hints
5. **Zero external dependencies**: All implemented in-house
6. **Well-tested**: Unit + property-based tests
7. **Clear separation**: Internal (_result.py) vs public (result.py)
