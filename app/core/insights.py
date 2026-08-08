"""AI-style dataset insights (rule-based).

Generates business insights from a dataset without requiring an LLM.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DatasetInsights:
    quality: str

    row_count: int
    column_count: int
    missing_values: int
    duplicate_rows: int

    missing_columns: list[str]

    strongest_correlation: str
    strongest_value: float

    average_column: str
    average_value: float

    recommendations: list[str]


def build_insights(dataframe: pd.DataFrame) -> DatasetInsights:
    """Generate structured insights for the dataset."""

    # ---------------------------------
    # Basic Dataset Info
    # ---------------------------------
    row_count = len(dataframe)
    column_count = dataframe.shape[1]

    # ---------------------------------
    # Missing Values
    # ---------------------------------
    missing = dataframe.isna().sum()
    missing_values = int(missing.sum())

    missing_columns = missing[missing > 0].index.tolist()

    # ---------------------------------
    # Duplicate Rows
    # ---------------------------------
    duplicate_rows = int(dataframe.duplicated().sum())

    # ---------------------------------
    # Numeric Summary
    # ---------------------------------
    numeric = dataframe.select_dtypes(include="number")

    average_column = "N/A"
    average_value = 0.0

    if not numeric.empty:
        means = numeric.mean().round(2)

        average_column = str(means.index[0])
        average_value = float(means.iloc[0])

    # ---------------------------------
    # Correlation
    # ---------------------------------
    strongest_correlation = "N/A"
    strongest_value = 0.0

    recommendations: list[str] = []

    if numeric.shape[1] >= 2:

        corr = numeric.corr().abs()

        corr = corr.mask(np.eye(len(corr), dtype=bool), 0)

        if not corr.stack().empty:

            strongest = corr.stack().idxmax()

            strongest_correlation = (
                f"{strongest[0]} ↔ {strongest[1]}"
            )

            strongest_value = float(corr.stack().max())

            if strongest_value > 0.90:
                recommendations.append(
                    "Highly correlated features detected. Consider feature selection."
                )

    # ---------------------------------
    # Recommendations
    # ---------------------------------
    if missing_values > 0:
        recommendations.append(
            "Fill missing values using median or mode before training ML models."
        )

    if duplicate_rows > 0:
        recommendations.append(
            "Remove duplicate rows to improve data quality."
        )

    if missing_values == 0 and duplicate_rows == 0:
        recommendations.append(
            "Dataset is clean and suitable for machine learning."
        )

    # ---------------------------------
    # Dataset Quality
    # ---------------------------------
    if missing_values == 0 and duplicate_rows == 0:
        quality = "Excellent"

    elif missing_values < row_count * 0.05:
        quality = "Good"

    else:
        quality = "Needs Cleaning"

    # ---------------------------------
    # Return
    # ---------------------------------
    return DatasetInsights(
        quality=quality,

        row_count=row_count,
        column_count=column_count,

        missing_values=missing_values,
        duplicate_rows=duplicate_rows,

        missing_columns=missing_columns,

        strongest_correlation=strongest_correlation,
        strongest_value=round(strongest_value, 2),

        average_column=average_column,
        average_value=round(average_value, 2),

        recommendations=recommendations,
    )