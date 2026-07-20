"""Validation utilities for uploaded files.

This module is intentionally decoupled from Streamlit. It only knows
about an "uploaded file"-like object (anything exposing `.name` and
`.size`, which is what `st.file_uploader` returns) so it can be unit
tested without spinning up a Streamlit app.
"""

from __future__ import annotations

from typing import Protocol

from app.core.exceptions import EmptyFileError, InvalidFileTypeError

ALLOWED_EXTENSION: str = ".csv"


class UploadedFileLike(Protocol):
    """Structural type describing the subset of Streamlit's UploadedFile
    interface that this module depends on.
    """

    name: str
    size: int


def validate_file_extension(uploaded_file: UploadedFileLike) -> None:
    """Ensure the uploaded file has a `.csv` extension.

    Args:
        uploaded_file: The file object returned by `st.file_uploader`.

    Raises:
        InvalidFileTypeError: If the file name does not end in `.csv`.
    """
    file_name = getattr(uploaded_file, "name", "")
    if not file_name.lower().endswith(ALLOWED_EXTENSION):
        raise InvalidFileTypeError(
            f"Invalid file type: '{file_name}'. Please upload a "
            f"CSV file (.csv extension)."
        )


def validate_file_not_empty(uploaded_file: UploadedFileLike) -> None:
    """Ensure the uploaded file is not zero bytes.

    Args:
        uploaded_file: The file object returned by `st.file_uploader`.

    Raises:
        EmptyFileError: If the file size is 0 bytes.
    """
    file_size = getattr(uploaded_file, "size", 0)
    if file_size == 0:
        raise EmptyFileError(
            "The uploaded file is empty (0 bytes). Please upload a "
            "CSV file that contains data."
        )


def validate_uploaded_file(uploaded_file: UploadedFileLike) -> None:
    """Run all upload-time validations on a file.

    Args:
        uploaded_file: The file object returned by `st.file_uploader`.

    Raises:
        InvalidFileTypeError: If the file is not a `.csv` file.
        EmptyFileError: If the file has zero bytes.
    """
    validate_file_extension(uploaded_file)
    validate_file_not_empty(uploaded_file)
