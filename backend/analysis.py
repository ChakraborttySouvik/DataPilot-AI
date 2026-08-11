from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.storage import get_dataset


router = APIRouter(
    prefix="/api/analysis",
    tags=["Analysis"],
)


class DatasetRequest(BaseModel):
    dataset_id: str


@router.post("/overview")
async def dataset_overview(
    request: DatasetRequest,
):
    """Return basic overview information for a stored dataset."""

    dataframe = get_dataset(
        request.dataset_id
    )

    if dataframe is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Dataset not found. "
                "Please upload the dataset again."
            ),
        )

    try:

        missing_values = dataframe.isna().sum()

        return {
            "dataset_id": request.dataset_id,

            "row_count": int(
                dataframe.shape[0]
            ),

            "column_count": int(
                dataframe.shape[1]
            ),

            "size_bytes": int(
                dataframe.memory_usage(
                    deep=True
                ).sum()
            ),

            "column_names": [
                str(column)
                for column in dataframe.columns
            ],

            "dtypes": {
                str(column): str(dtype)
                for column, dtype
                in dataframe.dtypes.items()
            },

            "missing_values": {
                str(column): int(count)
                for column, count
                in missing_values.items()
            },

            "total_missing_values": int(
                missing_values.sum()
            ),

            "duplicate_row_count": int(
                dataframe.duplicated().sum()
            ),
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not analyze dataset: {error}"
            ),
        ) from error