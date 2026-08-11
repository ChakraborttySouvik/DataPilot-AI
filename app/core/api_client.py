from __future__ import annotations

import requests

from app.core.analyzer import DatasetOverview


API_BASE_URL = "http://127.0.0.1:8000"


def upload_dataset(file) -> dict:
    """Upload a dataset to FastAPI."""

    files = {
        "file": (
            file.name,
            file.getvalue(),
            file.type,
        )
    }

    response = requests.post(
        f"{API_BASE_URL}/api/dataset/upload",
        files=files,
        timeout=120,
    )

    response.raise_for_status()

    return response.json()


def get_dataset_overview(
    dataset_id: str,
) -> DatasetOverview:
    """Get dataset overview from FastAPI."""

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
        row_count=int(data["row_count"]),

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
            for key, value in data["dtypes"].items()
        },

        missing_values={
            str(key): int(value)
            for key, value in data["missing_values"].items()
        },

        total_missing_values=int(
            data["total_missing_values"]
        ),

        duplicate_row_count=int(
            data["duplicate_row_count"]
        ),
    )