"""Dataset loading logic.

Supports CSV and Excel (.xlsx) files.

Isolated from Streamlit and from validation so each module has a single
responsibility (clean architecture: validators validate, loaders load,
analyzers analyze, UI renders).
"""

from __future__ import annotations

from typing import Protocol

import pandas as pd

from app.core.exceptions import EmptyFileError, FileReadError


class UploadedFileLike(Protocol):
    """Structural type for a file-like object."""

    name: str
    size: int


def load_csv(
    uploaded_file: UploadedFileLike,
) -> pd.DataFrame:
    """Parse an uploaded CSV or XLSX file into a DataFrame.

    Args:
        uploaded_file: File object returned by Streamlit's uploader.

    Returns:
        A pandas DataFrame.

    Raises:
        EmptyFileError: If the file contains no data.
        FileReadError: If the file cannot be parsed.
    """

    filename = uploaded_file.name.lower()

    try:

        # ==================================================
        # CSV
        # ==================================================

        if filename.endswith(".csv"):

            dataframe = pd.read_csv(
                uploaded_file
            )

        # ==================================================
        # Excel
        # ==================================================

        elif filename.endswith(".xlsx"):

            dataframe = pd.read_excel(
                uploaded_file,
                engine="openpyxl",
            )

        # ==================================================
        # Unsupported File
        # ==================================================

        else:

            raise FileReadError(
                "Unsupported file format. "
                "Please upload a CSV or XLSX file."
            )

    except pd.errors.EmptyDataError as exc:

        raise EmptyFileError(
            "The uploaded file contains no data to read."
        ) from exc

    except pd.errors.ParserError as exc:

        raise FileReadError(
            f"Could not parse the file. Details: {exc}"
        ) from exc

    except UnicodeDecodeError as exc:

        raise FileReadError(
            "Could not read the file encoding. "
            "Please save the CSV as UTF-8 and try again."
        ) from exc

    except FileReadError:

        raise

    except Exception as exc:

        raise FileReadError(
            f"Unexpected error while reading the file: {exc}"
        ) from exc

    # ==================================================
    # Empty Dataset Check
    # ==================================================

    if dataframe.empty:

        raise EmptyFileError(
            "The file was read but contains no rows of data."
        )

    return dataframe