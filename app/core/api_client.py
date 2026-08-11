"""Client for DataPilot AI backend services.

Supports two modes:

1. Local development:
   Streamlit communicates with the FastAPI backend running on
   http://127.0.0.1:8000

2. Streamlit Cloud:
   If the FastAPI backend is unavailable, the client automatically
   falls back to in-process pandas analysis.

This keeps the application deployable without requiring a separate
FastAPI server.
"""

from __future__ import annotations

import os
import uuid

import pandas as pd
import requests

from app.core.analyzer import DatasetOverview


# -------------------------------------------------------------------
# API CONFIGURATION
# -------------------------------------------------------------------

API_BASE_URL = os.getenv(
    "DATAPILOT_API_URL",
    "http://127.0.0.1:8000",
)


# -------------------------------------------------------------------
# LOCAL FALLBACK STORAGE
# -------------------------------------------------------------------

_LOCAL_DATASETS: dict[str, pd.DataFrame] = {}


# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

def _build_local_overview(
    dataframe: pd.DataFrame,
) -> DatasetOverview:
    """Build DatasetOverview without FastAPI."""

    missing_per_column = dataframe.isna().sum()

    return DatasetOverview(
        row_count=int(dataframe.shape[0]),

        column_count=int(dataframe.shape[1]),

        size_bytes=int(
            dataframe.memory_usage(
                deep=True
            ).sum()
        ),

        column_names=[
            str(column)
            for column in dataframe.columns
        ],

        dtypes={
            str(column): str(dtype)
            for column, dtype
            in dataframe.dtypes.items()
        },

        missing_values={
            str(column): int(count)
            for column, count
            in missing_per_column.items()
        },

        total_missing_values=int(
            missing_per_column.sum()
        ),

        duplicate_row_count=int(
            dataframe.duplicated().sum()
        ),
    )


def _read_uploaded_file(file) -> pd.DataFrame:
    """Read CSV or Excel uploaded through Streamlit."""

    file_bytes = file.getvalue()

    filename = file.name.lower()

    if filename.endswith(".csv"):
        from io import BytesIO

        return pd.read_csv(
            BytesIO(file_bytes)
        )

    if filename.endswith(".xlsx"):
        from io import BytesIO

        return pd.read_excel(
            BytesIO(file_bytes),
            engine="openpyxl",
        )

    if filename.endswith(".xls"):
        from io import BytesIO

        return pd.read_excel(
            BytesIO(file_bytes)
        )

    raise ValueError(
        "Unsupported file format. "
        "Please upload CSV or Excel files."
    )


# -------------------------------------------------------------------
# UPLOAD DATASET
# -------------------------------------------------------------------

def upload_dataset(file) -> dict:
    """Upload a dataset to FastAPI.

    If FastAPI is unavailable, automatically use local pandas
    processing so the Streamlit Cloud deployment still works.
    """

    files = {
        "file": (
            file.name,
            file.getvalue(),
            file.type or "application/octet-stream",
        )
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/dataset/upload",
            files=files,
            timeout=120,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:
        # -----------------------------------------------------------
        # FASTAPI NOT AVAILABLE
        # Use local fallback
        # -----------------------------------------------------------

        dataframe = _read_uploaded_file(file)

        dataset_id = str(uuid.uuid4())

        _LOCAL_DATASETS[dataset_id] = dataframe

        return {
            "dataset_id": dataset_id,
            "filename": file.name,

            # Existing UI compatibility
            "rows": int(dataframe.shape[0]),
            "columns": int(dataframe.shape[1]),

            # Existing API-style names
            "row_count": int(dataframe.shape[0]),
            "column_count": int(dataframe.shape[1]),

            "size_bytes": int(
                dataframe.memory_usage(deep=True).sum()
            ),

            "storage": "local",
        }
# -------------------------------------------------------------------
# DATASET OVERVIEW
# -------------------------------------------------------------------

def get_dataset_overview(
    dataset_id: str,
) -> DatasetOverview:
    """Get dataset overview from FastAPI.

    Falls back to local pandas analysis if FastAPI is unavailable.
    """

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/analysis/overview",
            json={
                "dataset_id": dataset_id,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        return DatasetOverview(
            row_count=int(
                data["row_count"]
            ),

            column_count=int(
                data["column_count"]
            ),

            size_bytes=int(
                data["size_bytes"]
            ),

            column_names=[
                str(column)
                for column in data["column_names"]
            ],

            dtypes={
                str(key): str(value)
                for key, value
                in data["dtypes"].items()
            },

            missing_values={
                str(key): int(value)
                for key, value
                in data["missing_values"].items()
            },

            total_missing_values=int(
                data["total_missing_values"]
            ),

            duplicate_row_count=int(
                data["duplicate_row_count"]
            ),
        )

    except requests.exceptions.ConnectionError:
        # -----------------------------------------------------------
        # FASTAPI NOT AVAILABLE
        # Use local fallback
        # -----------------------------------------------------------

        dataframe = _LOCAL_DATASETS.get(
            dataset_id
        )

        if dataframe is None:
            raise RuntimeError(
                "Dataset is not available. "
                "Please upload the dataset again."
            )

        return _build_local_overview(
            dataframe
        )