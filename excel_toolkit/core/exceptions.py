"""Custom exceptions for file handlers.

This module defines exception types used throughout the file handling layer.
All exceptions inherit from FileHandlerError for consistent error handling.
"""


class FileHandlerError(Exception):
    """Base exception for all file handler errors.

    All file handler exceptions inherit from this class, allowing
    users to catch all file-related errors with a single except clause.
    """

    pass


class FileNotFoundError(FileHandlerError):
    """Raised when a file does not exist at the specified path."""

    pass


class FileAccessError(FileHandlerError):
    """Raised when a file cannot be read or written due to permissions or locks.

    This includes:
    - Permission denied errors
    - File locked by another process
    - Read-only filesystem when writing
    """

    pass


class UnsupportedFormatError(FileHandlerError):
    """Raised when a file format is not supported.

    This occurs when:
    - File extension is not recognized
    - No handler is available for the file type
    """

    pass


class InvalidFileError(FileHandlerError):
    """Raised when a file exists but is invalid or corrupted.

    This includes:
    - Corrupted file structure
    - Empty file when data is expected
    - Invalid file format for the extension
    - Cannot parse file contents
    """

    pass


class FileSizeError(FileHandlerError):
    """Raised when a file exceeds size limits.

    This occurs when:
    - File is larger than MAX_FILE_SIZE_MB
    - Processing would require excessive memory
    """

    pass


class EncodingError(FileHandlerError):
    """Raised when file encoding cannot be detected or is invalid.

    This occurs when:
    - All encoding attempts fail
    - File contains invalid byte sequences
    """

    pass
