from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.forecasting import generate_forecast
from backend.storage import get_dataset


router = APIRouter(
    prefix="/api/forecast",
    tags=["Forecast"],
)


class ForecastRequest(BaseModel):
    dataset_id: str
    date_column: str
    target_column: str
    periods: int = 7
    method: str = "Moving Average"


@router.post("")
async def create_forecast(
    request: ForecastRequest,
):
    """Generate a forecast for a stored dataset."""

    dataframe = get_dataset(
        request.dataset_id
    )

    if dataframe is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found. Please upload the dataset again.",
        )

    if request.periods < 1:
        raise HTTPException(
            status_code=400,
            detail="Forecast periods must be at least 1.",
        )

    try:

        historical, forecast = generate_forecast(
            dataframe=dataframe,
            date_column=request.date_column,
            target_column=request.target_column,
            periods=request.periods,
            method=request.method,
        )

        return {
            "dataset_id": request.dataset_id,
            "method": request.method,
            "date_column": request.date_column,
            "target_column": request.target_column,
            "historical_records": len(historical),
            "forecast_periods": len(forecast),
            "forecast": forecast.to_dict(
                orient="records"
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Forecast generation failed: {error}",
        )