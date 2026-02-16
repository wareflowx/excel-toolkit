"""Functional programming primitives for Excel CLI Toolkit.

All types are implemented in-house with zero external dependencies.
Public API is purely functional - classes are internal implementation details.

Example:
    from excel_toolkit.fp import ok, err, is_ok, unwrap

    result = ok(42)
    if is_ok(result):
        value = unwrap(result)
"""

# Result API - functions only
# Result type for type hints
from excel_toolkit.fp._result import Result

# Immutable utilities
from excel_toolkit.fp.immutable import immutable

# Maybe API - functions only
from excel_toolkit.fp.maybe import (
    is_nothing,
    is_some,
    nothing,
    some,
    to_maybe,
)
from excel_toolkit.fp.maybe import (
    unwrap as unwrap_maybe,
)
from excel_toolkit.fp.maybe import (
    unwrap_or as unwrap_or_maybe,
)
from excel_toolkit.fp.maybe import (
    unwrap_or_else as unwrap_or_else_maybe,
)
from excel_toolkit.fp.result import (
    UnwrapError,
    err,
    is_err,
    is_ok,
    ok,
    unwrap,
    unwrap_err,
    unwrap_or,
    unwrap_or_else,
)
from excel_toolkit.fp.result import (
    to_result as result_to_result,
)

__all__ = [
    # Result
    "ok",
    "err",
    "is_ok",
    "is_err",
    "unwrap",
    "unwrap_or",
    "unwrap_or_else",
    "unwrap_err",
    "result_to_result",
    "UnwrapError",
    "Result",
    # Maybe
    "some",
    "nothing",
    "is_some",
    "is_nothing",
    "unwrap_maybe",
    "unwrap_or_maybe",
    "unwrap_or_else_maybe",
    "to_maybe",
    # Utilities
    "immutable",
]
