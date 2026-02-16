"""Data models and type definitions."""

# Export error codes
from excel_toolkit.models.error_codes import ErrorCode, get_error_category

# Export all error types
from excel_toolkit.models.error_types import (
    AggColumnsNotFoundError,
    AggregationError,
    AggregationFailedError,
    AggregationValidationError,
    CastFailedError,
    # Phase 2: Support operations
    CleaningError,
    ColumnColumnsNotFoundError,
    ColumnMismatchError,
    ColumnNotFoundError,
    ColumnsNotFoundError,
    CompareError,
    ComparisonFailedError,
    ComparisonValidationError,
    ConditionTooLongError,
    # Validation errors
    DangerousPatternError,
    FillFailedError,
    FilterError,
    # Aggregation errors
    GroupColumnsNotFoundError,
    InsufficientDataFramesError,
    InvalidExpressionError,
    InvalidFillStrategyError,
    # Parse errors
    InvalidFormatError,
    InvalidFunctionError,
    InvalidJoinParametersError,
    InvalidJoinTypeError,
    InvalidRuleError,
    InvalidTransformationError,
    InvalidTypeError,
    JoinColumnsNotFoundError,
    JoiningError,
    # Compare errors
    KeyColumnsNotFoundError,
    KeyColumnsNotFoundError2,
    MergeColumnsNotFoundError,
    NoColumnsError,
    NoRowsError,
    # Sort errors
    NotComparableError,
    NoValidSpecsError,
    NoValuesError,
    NullValueThresholdExceededError,
    OverlappingColumnsError,
    ParseError,
    PivotError,
    PivotFailedError,
    PivotValidationError,
    # Filter errors
    QueryFailedError,
    # Pivot errors
    RowColumnsNotFoundError,
    SortError,
    SortFailedError,
    SortValidationError,
    TransformingError,
    TypeMismatchError,
    UnbalancedBracketsError,
    UnbalancedParenthesesError,
    UnbalancedQuotesError,
    UniquenessViolationError,
    # Type aliases
    ValidationError,
    ValueColumnsNotFoundError,
    ValueOutOfRangeError,
)

# Export error utilities and serialization
from excel_toolkit.models.error_utils import (
    ErrorSerializable,
    error_to_dict,
    get_error_code_value,
    get_error_type_name,
)

__all__ = [
    # Validation errors
    "DangerousPatternError",
    "ConditionTooLongError",
    "UnbalancedParenthesesError",
    "UnbalancedBracketsError",
    "UnbalancedQuotesError",
    "InvalidFunctionError",
    "NoColumnsError",
    "NoRowsError",
    "NoValuesError",
    "ColumnNotFoundError",
    "ColumnsNotFoundError",
    "OverlappingColumnsError",
    # Filter errors
    "QueryFailedError",
    "ColumnMismatchError",
    # Sort errors
    "NotComparableError",
    "SortFailedError",
    # Pivot errors
    "RowColumnsNotFoundError",
    "ColumnColumnsNotFoundError",
    "ValueColumnsNotFoundError",
    "PivotFailedError",
    # Parse errors
    "InvalidFormatError",
    "NoValidSpecsError",
    # Aggregation errors
    "GroupColumnsNotFoundError",
    "AggColumnsNotFoundError",
    "AggregationFailedError",
    # Compare errors
    "KeyColumnsNotFoundError",
    "KeyColumnsNotFoundError2",
    "ComparisonFailedError",
    # Phase 2 errors
    "CleaningError",
    "InvalidFillStrategyError",
    "FillFailedError",
    "InvalidExpressionError",
    "InvalidTypeError",
    "CastFailedError",
    "TransformingError",
    "InvalidTransformationError",
    "InvalidJoinTypeError",
    "InvalidJoinParametersError",
    "JoinColumnsNotFoundError",
    "MergeColumnsNotFoundError",
    "InsufficientDataFramesError",
    "JoiningError",
    "ValueOutOfRangeError",
    "NullValueThresholdExceededError",
    "UniquenessViolationError",
    "InvalidRuleError",
    "TypeMismatchError",
    # Type aliases
    "ValidationError",
    "FilterError",
    "SortValidationError",
    "SortError",
    "PivotValidationError",
    "PivotError",
    "ParseError",
    "AggregationValidationError",
    "AggregationError",
    "ComparisonValidationError",
    "CompareError",
    # Error utilities
    "ErrorCode",
    "get_error_category",
    "ErrorSerializable",
    "error_to_dict",
    "get_error_type_name",
    "get_error_code_value",
]
