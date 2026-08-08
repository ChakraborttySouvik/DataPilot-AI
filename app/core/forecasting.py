"""Forecasting utilities for DataPilot AI.

This module contains the business logic required to prepare
time-series data and generate simple forecasts.

The UI layer should only call these functions and display
the returned results.
"""

from __future__ import annotations

import pandas as pd
import numpy as np


# ============================================================
# Date Column Detection
# ============================================================
def detect_date_columns(dataframe: pd.DataFrame) -> list[str]:
    """Automatically detect genuine date/time columns."""

    date_columns = []

    # Strong hints that a column is intended to contain dates
    date_keywords = (
        "date",
        "time",
        "timestamp",
        "datetime",
        "month",
        "year",
    )

    for column in dataframe.columns:

        series = dataframe[column]

        # ------------------------------------------
        # Already datetime
        # ------------------------------------------
        if pd.api.types.is_datetime64_any_dtype(series):
            date_columns.append(column)
            continue

        # ------------------------------------------
        # Never treat numeric columns as dates
        # ------------------------------------------
        if pd.api.types.is_numeric_dtype(series):
            continue

        # ------------------------------------------
        # Column-name hint
        # ------------------------------------------
        column_name = str(column).strip().lower()

        has_date_name = any(
            keyword in column_name
            for keyword in date_keywords
        )

        # ------------------------------------------
        # Try converting text to datetime
        # ------------------------------------------
        converted = pd.to_datetime(
            series,
            errors="coerce",
        )

        valid_ratio = converted.notna().mean()

        # Require a high percentage of valid dates
        if valid_ratio >= 0.80:

            # Prefer columns whose names suggest dates
            if has_date_name:
                date_columns.append(column)

            # Also allow clearly date-like text columns
            elif converted.notna().sum() >= 10:
                date_columns.append(column)

    return date_columns

# ============================================================
# Numeric Column Detection
# ============================================================

def detect_numeric_columns(
    dataframe: pd.DataFrame,
) -> list[str]:
    """Return numeric columns suitable for forecasting."""

    return dataframe.select_dtypes(
        include="number"
    ).columns.tolist()


# ============================================================
# Prepare Time Series
# ============================================================

def prepare_time_series(
    dataframe: pd.DataFrame,
    date_column: str,
    target_column: str,
) -> pd.DataFrame:
    """Prepare a clean time-series DataFrame."""

    if date_column not in dataframe.columns:
        raise ValueError(
            f"Date column '{date_column}' was not found."
        )

    if target_column not in dataframe.columns:
        raise ValueError(
            f"Target column '{target_column}' was not found."
        )

    data = dataframe[
        [date_column, target_column]
    ].copy()

    # Convert date column
    data[date_column] = pd.to_datetime(
        data[date_column],
        errors="coerce",
    )

    # Convert target to numeric
    data[target_column] = pd.to_numeric(
        data[target_column],
        errors="coerce",
    )

    # Remove invalid rows
    data = data.dropna(
        subset=[
            date_column,
            target_column,
        ]
    )

    # Sort chronologically
    data = data.sort_values(
        date_column
    )

    # Remove duplicate dates by summing values
    data = (
        data.groupby(
            date_column,
            as_index=False,
        )[target_column]
        .sum()
    )

    return data.reset_index(
        drop=True
    )


# ============================================================
# Linear Trend Forecast
# ============================================================

def forecast_linear_trend(
    time_series: pd.DataFrame,
    date_column: str,
    target_column: str,
    periods: int,
) -> pd.DataFrame:
    """Generate a simple linear-trend forecast."""

    if len(time_series) < 2:
        raise ValueError(
            "At least 2 historical observations are required."
        )

    if periods < 1:
        raise ValueError(
            "Forecast horizon must be at least 1."
        )

    data = time_series.copy()

    # Convert dates into integer positions
    x = np.arange(
        len(data),
        dtype=float,
    )

    y = data[target_column].astype(float).to_numpy()

    # Linear regression using NumPy
    slope, intercept = np.polyfit(
        x,
        y,
        1,
    )

    future_x = np.arange(
        len(data),
        len(data) + periods,
        dtype=float,
    )

    forecast_values = (
        slope * future_x
        + intercept
    )

    # Determine typical time interval
    date_differences = (
        data[date_column]
        .sort_values()
        .diff()
        .dropna()
    )

    if date_differences.empty:
        frequency = pd.Timedelta(days=1)
    else:
        frequency = date_differences.median()

    last_date = data[date_column].max()

    future_dates = [
        last_date + frequency * (i + 1)
        for i in range(periods)
    ]

    forecast = pd.DataFrame(
        {
            date_column: future_dates,
            target_column: forecast_values,
        }
    )

    return forecast


# ============================================================
# Moving Average Forecast
# ============================================================

def forecast_moving_average(
    time_series: pd.DataFrame,
    date_column: str,
    target_column: str,
    periods: int,
    window: int = 3,
) -> pd.DataFrame:
    """Generate a moving-average forecast."""

    if len(time_series) < window:
        raise ValueError(
            f"At least {window} historical observations "
            "are required."
        )

    if periods < 1:
        raise ValueError(
            "Forecast horizon must be at least 1."
        )

    data = time_series.copy()

    values = (
        data[target_column]
        .astype(float)
        .tolist()
    )

    predictions = []

    for _ in range(periods):

        recent_values = values[-window:]

        prediction = float(
            np.mean(recent_values)
        )

        predictions.append(
            prediction
        )

        values.append(
            prediction
        )

    date_differences = (
        data[date_column]
        .sort_values()
        .diff()
        .dropna()
    )

    if date_differences.empty:
        frequency = pd.Timedelta(days=1)
    else:
        frequency = date_differences.median()

    last_date = data[date_column].max()

    future_dates = [
        last_date + frequency * (i + 1)
        for i in range(periods)
    ]

    forecast = pd.DataFrame(
        {
            date_column: future_dates,
            target_column: predictions,
        }
    )

    return forecast


# ============================================================
# Forecast Dispatcher
# ============================================================

def generate_forecast(
    dataframe: pd.DataFrame,
    date_column: str,
    target_column: str,
    periods: int,
    method: str = "Linear Trend",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare historical data and generate forecast."""

    historical = prepare_time_series(
        dataframe=dataframe,
        date_column=date_column,
        target_column=target_column,
    )

    if method == "Linear Trend":

        forecast = forecast_linear_trend(
            time_series=historical,
            date_column=date_column,
            target_column=target_column,
            periods=periods,
        )

    elif method == "Moving Average":

        forecast = forecast_moving_average(
            time_series=historical,
            date_column=date_column,
            target_column=target_column,
            periods=periods,
        )

    else:

        raise ValueError(
            f"Unsupported forecasting method: {method}"
        )

    return historical, forecast