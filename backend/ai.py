from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.gemini_client import ask_gemini
from backend.storage import get_dataset


router = APIRouter(
    prefix="/api/ai",
    tags=["AI"],
)


class AIRequest(BaseModel):
    dataset_id: str
    question: str


@router.post("/chat")
async def ai_chat(request: AIRequest):
    """Answer a question using a stored dataset and Gemini AI."""

    # ============================================================
    # Validate Question
    # ============================================================

    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    # ============================================================
    # Retrieve Dataset
    # ============================================================

    dataframe = get_dataset(
        request.dataset_id
    )

    if dataframe is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found. Please upload the dataset again.",
        )

    # ============================================================
    # Prepare Gemini Context
    # ============================================================

    try:

        dataset_context = f"""
You are DataPilot AI, an expert Business Intelligence Analyst.

You are analyzing the user's uploaded dataset.

DATASET INFORMATION
-------------------
Rows: {dataframe.shape[0]:,}
Columns: {dataframe.shape[1]}

COLUMN NAMES
------------
{', '.join(str(column) for column in dataframe.columns)}

DATA TYPES
----------
{dataframe.dtypes.to_string()}

MISSING VALUES
--------------
{dataframe.isnull().sum().to_string()}

DUPLICATE ROWS
--------------
{dataframe.duplicated().sum():,}

STATISTICAL SUMMARY
-------------------
{dataframe.describe(include="all").to_string()}

FULL DATASET
------------
{dataframe.to_csv(index=False)}

USER QUESTION
-------------
{request.question}

INSTRUCTIONS
------------
1. Answer using the uploaded dataset.
2. Use the full dataset provided.
3. Perform calculations when necessary.
4. Give exact numbers whenever possible.
5. Do not invent information.
6. If the answer cannot be determined from the dataset, clearly say so.
7. Explain the result in simple business language.
8. Use bullet points or tables when useful.
"""

        # ========================================================
        # Gemini
        # ========================================================

        answer = ask_gemini(
            dataset_context
        )

        return {
            "dataset_id": request.dataset_id,
            "question": request.question,
            "answer": answer,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Gemini analysis failed: {error}",
        )