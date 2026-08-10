from __future__ import annotations

from io import BytesIO

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.storage import save_dataset


router = APIRouter(
    prefix="/api/dataset",
    tags=["Dataset"],
)


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
):
    """Upload a CSV or XLSX dataset."""

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file was provided.",
        )

    filename = file.filename.lower()

    if not filename.endswith(
        (".csv", ".xlsx")
    ):
        raise HTTPException(
            status_code=400,
            detail="Only CSV and XLSX files are supported.",
        )

    try:

        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        if filename.endswith(".csv"):

            dataframe = pd.read_csv(
                BytesIO(file_bytes)
            )

        else:

            dataframe = pd.read_excel(
                BytesIO(file_bytes),
                engine="openpyxl",
            )

        if dataframe.empty:
            raise HTTPException(
                status_code=400,
                detail="The uploaded dataset contains no rows.",
            )

        dataset_id = save_dataset(
            dataframe
        )

        return {
            "dataset_id": dataset_id,
            "filename": file.filename,
            "rows": int(
                dataframe.shape[0]
            ),
            "columns": int(
                dataframe.shape[1]
            ),
            "column_names": [
                str(column)
                for column in dataframe.columns
            ],
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=400,
            detail=f"Could not read dataset: {error}",
        )