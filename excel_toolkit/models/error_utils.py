"""Utility functions and mixins for error serialization and handling.

This module provides helper functions and a base mixin class for converting
error types to JSON-serializable dictionaries, making them suitable for AI
agent consumption.
"""

from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any
import pandas as pd


class ErrorSerializable:
    """Mixin class that adds to_dict() method to error types.

    This mixin provides a consistent serialization interface for all error
    types. It should be inherited by all error dataclasses.

    Example:
        @dataclass
        @immutable
        class MyError(ErrorSerializable):
            error_code: int = 1001
            message: str

        error = MyError(message="Something went wrong")
        error_dict = error.to_dict()
    """

    def to_dict(self) -> dict:
        """Convert the error to a JSON-serializable dictionary.

        Returns:
            Dictionary representation of the error with all values serializable

        Example:
            >>> error = ColumnNotFoundError(column="Age", available=["Name", "Email"])
            >>> error.to_dict()
            {
                'error_type': 'ColumnNotFoundError',
                'error_code': 1011,
                'column': 'Age',
                'available': ['Name', 'Email']
            }
        """
        if not is_dataclass(self):
            return {
                "error_type": type(self).__name__,
                "error_code": getattr(self, "error_code", None),
                "message": str(self)
            }

        # Get the dataclass as a dict
        result = asdict(self)

        # Add error_type
        result["error_type"] = type(self).__name__

        # Ensure all values are JSON-serializable
        result = _make_json_serializable(result)

        return result


def error_to_dict(error: Any) -> dict:
    """Convert an error object to a JSON-serializable dictionary.

    This function handles the conversion of error dataclasses to dictionaries,
    ensuring that all values are JSON-serializable. It handles special cases
    like pandas dtypes, datetime objects, and converts them to strings.

    Args:
        error: Error object (typically a dataclass error type)

    Returns:
        Dictionary representation of the error with all values serializable

    Example:
        >>> error = ColumnNotFoundError(column="Age", available=["Name", "Email"])
        >>> error_dict = error_to_dict(error)
        >>> print(error_dict)
        {
            'error_type': 'ColumnNotFoundError',
            'error_code': 1011,
            'column': 'Age',
            'available': ['Name', 'Email']
        }
    """
    if not is_dataclass(error):
        return {
            "error_type": type(error).__name__,
            "error_code": getattr(error, "error_code", None),
            "message": str(error)
        }

    # Get the dataclass as a dict
    result = asdict(error)

    # Add error_type
    result["error_type"] = type(error).__name__

    # Ensure all values are JSON-serializable
    result = _make_json_serializable(result)

    return result


def _make_json_serializable(obj: Any) -> Any:
    """Convert an object to a JSON-serializable format.

    Args:
        obj: Object to convert

    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_json_serializable(item) for item in obj]
    elif isinstance(obj, pd.DataFrame):
        # Convert DataFrame to dict representation
        return obj.to_dict(orient="records")
    elif hasattr(obj, "dtype"):  # numpy dtype, pandas dtype, etc.
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif callable(obj):
        return str(obj)
    elif pd.isna(obj):
        return None
    else:
        return obj


def get_error_type_name(error: Any) -> str:
    """Get the type name of an error.

    Args:
        error: Error object

    Returns:
        Name of the error type

    Example:
        >>> error = ColumnNotFoundError(column="Age", available=[])
        >>> get_error_type_name(error)
        'ColumnNotFoundError'
    """
    return type(error).__name__


def get_error_code_value(error: Any) -> int | None:
    """Get the error code value from an error object.

    Args:
        error: Error object

    Returns:
        Error code value or None if not present

    Example:
        >>> error = ColumnNotFoundError(column="Age", available=[])
        >>> get_error_code_value(error)
        1011
    """
    # Try ERROR_CODE (class attribute) first, then error_code (instance attribute)
    return getattr(error, "ERROR_CODE", None) or getattr(error, "error_code", None)
