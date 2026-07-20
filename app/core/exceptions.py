"""Custom exceptions for DataPilot AI - Feature 1 (CSV Upload & Overview).

Using dedicated exception types (instead of generic Exception) lets the
UI layer catch specific failure modes and show tailored, user-friendly
messages instead of raw tracebacks.
"""


class DataPilotError(Exception):
    """Base class for all DataPilot AI application errors."""


class InvalidFileTypeError(DataPilotError):
    """Raised when the uploaded file is not a CSV file."""


class EmptyFileError(DataPilotError):
    """Raised when the uploaded CSV file has no data."""


class FileReadError(DataPilotError):
    """Raised when the CSV file cannot be parsed by pandas."""
