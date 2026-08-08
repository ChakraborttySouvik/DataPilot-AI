"""Validation utilities for uploaded files.

This module is intentionally decoupled from Streamlit. It only knows
about an "uploaded file"-like object (anything exposing `.name` and
`.size`, which is what `st.file_uploader` returns) so it can be unit
tested without spinning up a Streamlit app.

Supported file formats:
- CSV (.csv)
- Excel (.xlsx)
"""

from __future__ import annotations

from typing import Protocol

from app.core.exceptions import EmptyFileError, InvalidFileTypeError


ALLOWED_EXTENSIONS: tuple[str, ...] = (
    ".csv",
    ".xlsx",
)


class UploadedFileLike(Protocol):
    """Structural type describing the subset of Streamlit's UploadedFile
    interface that this module depends on.
    """

    name: str
    size: int


def validate_file_extension(
    uploaded_file: UploadedFileLike,
) -> None:
    """Ensure the uploaded file has a supported extension.

    Supported formats:
    - .csv
    - .xlsx

    Raises:
        InvalidFileTypeError: If the file extension is unsupported.
    """

    file_name = getattr(
        uploaded_file,
        "name",
        "",
    )

    file_name_lower = file_name.lower()

    if not file_name_lower.endswith(ALLOWED_EXTENSIONS):

        raise InvalidFileTypeError(
            f"Invalid file type: '{file_name}'. "
            f"Please upload a CSV (.csv) or Excel (.xlsx) file."
        )


def validate_file_not_empty(
    uploaded_file: UploadedFileLike,
) -> None:
    """Ensure the uploaded file is not zero bytes.

    Raises:
        EmptyFileError: If the file size is 0 bytes.
    """

    file_size = getattr(
        uploaded_file,
        "size",
        0,
    )

    if file_size == 0:

        raise EmptyFileError(
            "The uploaded file is empty (0 bytes). "
            "Please upload a CSV or Excel file that contains data."
        )


def validate_uploaded_file(
    uploaded_file: UploadedFileLike,
) -> None:
    """Run all upload-time validations on a file."""

    validate_file_extension(
        uploaded_file
    )

    validate_file_not_empty(
        uploaded_file
    )