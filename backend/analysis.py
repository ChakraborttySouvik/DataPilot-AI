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
            detail="Dataset not found. Please upload the dataset again.",
        )

    try:

        return {
            "dataset_id": request.dataset_id,
            "rows": int(dataframe.shape[0]),
            "columns": int(dataframe.shape[1]),
            "column_names": [
                str(column)
                for column in dataframe.columns
            ],
            "missing_values": int(
                dataframe.isnull().sum().sum()
            ),
            "duplicate_rows": int(
                dataframe.duplicated().sum()
            ),
            "numeric_columns": [
                str(column)
                for column in dataframe.select_dtypes(
                    include="number"
                ).columns
            ],
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Could not analyze dataset: {error}",
        )