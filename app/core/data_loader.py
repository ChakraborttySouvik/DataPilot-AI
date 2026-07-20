"""CSV loading logic.

Isolated from Streamlit and from validation so each module has a single
responsibility (clean architecture: validators validate, loaders load,
analyzers analyze, UI renders).
"""

from __future__ import annotations

from typing import Protocol

import pandas as pd

from app.core.exceptions import EmptyFileError, FileReadError


class UploadedFileLike(Protocol):
    """Structural type for a file-like object with a `.read()` method,
    matching Streamlit's `UploadedFile`.
    """

    name: str
    size: int


def load_csv(uploaded_file: UploadedFileLike) -> pd.DataFrame:
    """Parse an uploaded CSV file into a pandas DataFrame.

    Args:
        uploaded_file: The file object returned by `st.file_uploader`.
            Assumed to have already passed `validate_uploaded_file`.

    Returns:
        A pandas DataFrame containing the parsed CSV data.

    Raises:
        EmptyFileError: If the CSV has no rows/columns after parsing
            (e.g. a file with only whitespace).
        FileReadError: If pandas cannot parse the file as CSV
            (malformed CSV, wrong encoding, etc.).
    """
    try:
        dataframe = pd.read_csv(uploaded_file)
    except pd.errors.EmptyDataError as exc:
        raise EmptyFileError(
            "The CSV file contains no data to read."
        ) from exc
    except pd.errors.ParserError as exc:
        raise FileReadError(
            f"Could not parse the file as CSV. Details: {exc}"
        ) from exc
    except UnicodeDecodeError as exc:
        raise FileReadError(
            "Could not read the file's encoding. Please save the CSV "
            "as UTF-8 and try again."
        ) from exc
    except Exception as exc:  # noqa: BLE001 - final safety net, re-raised as domain error
        raise FileReadError(f"Unexpected error while reading the file: {exc}") from exc

    if dataframe.empty:
        raise EmptyFileError("The CSV file was read but contains no rows of data.")

    return dataframe
