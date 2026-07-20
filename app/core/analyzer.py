"""Data analysis logic for Feature 1 (CSV Upload & Data Overview).

All functions here are pure: they take a pandas DataFrame and return
plain data (dataclasses / DataFrames), with no Streamlit calls. This
keeps analysis logic independently testable and reusable.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class DatasetOverview:
    """Basic shape and quality metrics for an uploaded dataset.

    Attributes:
        row_count: Number of rows in the dataset.
        column_count: Number of columns in the dataset.
        size_bytes: Total in-memory size of the dataset, in bytes.
        column_names: List of column names.
        dtypes: Mapping of column name -> dtype (as string).
        missing_values: Mapping of column name -> count of missing values.
        total_missing_values: Total missing values across the dataset.
        duplicate_row_count: Number of fully duplicated rows.
    """

    row_count: int
    column_count: int
    size_bytes: int
    column_names: list[str]
    dtypes: dict[str, str]
    missing_values: dict[str, int]
    total_missing_values: int
    duplicate_row_count: int


@dataclass(frozen=True)
class DatasetSummary:
    """Column-type breakdown and memory usage for an uploaded dataset.

    Attributes:
        numeric_columns: Column names with numeric dtypes.
        categorical_columns: Column names with object/category dtypes.
        date_columns: Column names detected (or convertible) to dates.
        memory_usage_bytes: Deep memory usage of the DataFrame, in bytes.
    """

    numeric_columns: list[str] = field(default_factory=list)
    categorical_columns: list[str] = field(default_factory=list)
    date_columns: list[str] = field(default_factory=list)
    memory_usage_bytes: int = 0


def build_overview(dataframe: pd.DataFrame) -> DatasetOverview:
    """Compute basic shape and data-quality metrics for a DataFrame.

    Args:
        dataframe: The dataset to analyze.

    Returns:
        A `DatasetOverview` with row/column counts, dtypes, missing
        values, and duplicate row count.
    """
    missing_per_column = dataframe.isna().sum()

    return DatasetOverview(
        row_count=int(dataframe.shape[0]),
        column_count=int(dataframe.shape[1]),
        size_bytes=int(dataframe.memory_usage(deep=True).sum()),
        column_names=list(dataframe.columns.astype(str)),
        dtypes={col: str(dtype) for col, dtype in dataframe.dtypes.items()},
        missing_values={col: int(count) for col, count in missing_per_column.items()},
        total_missing_values=int(missing_per_column.sum()),
        duplicate_row_count=int(dataframe.duplicated().sum()),
    )


def _is_probable_date_column(series: pd.Series, sample_size: int = 50) -> bool:
    """Heuristically detect whether an object-typed column holds dates.

    Only object/string columns are checked (numeric columns are never
    treated as dates, to avoid false positives on plain integers). A
    sample is parsed with `pd.to_datetime`; the column is considered a
    date column if parsing succeeds for the whole sample without error.

    Args:
        series: The column to test.
        sample_size: Number of non-null values to sample for the check.

    Returns:
        True if the sampled values parse as dates, False otherwise.
    """
    if not (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)):
        return False

    non_null = series.dropna()
    if non_null.empty:
        return False

    sample = non_null.sample(min(sample_size, len(non_null)), random_state=0)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            pd.to_datetime(sample, errors="raise")
    except (ValueError, TypeError):
        return False
    return True


def build_summary(dataframe: pd.DataFrame) -> DatasetSummary:
    """Classify columns by type and compute memory usage.

    Detects numeric columns (via pandas dtype), native datetime columns,
    object columns that look like dates (via heuristic parsing), and
    treats all remaining object/category columns as categorical.

    Args:
        dataframe: The dataset to analyze.

    Returns:
        A `DatasetSummary` describing column types and memory usage.
    """
    numeric_columns = list(dataframe.select_dtypes(include="number").columns)
    native_date_columns = list(dataframe.select_dtypes(include="datetime").columns)

    candidate_columns = [
        col
        for col in dataframe.select_dtypes(include=["object", "category"]).columns
    ]
    detected_date_columns = [
        col for col in candidate_columns if _is_probable_date_column(dataframe[col])
    ]
    categorical_columns = [
        col for col in candidate_columns if col not in detected_date_columns
    ]

    date_columns = native_date_columns + detected_date_columns

    return DatasetSummary(
        numeric_columns=[str(c) for c in numeric_columns],
        categorical_columns=[str(c) for c in categorical_columns],
        date_columns=[str(c) for c in date_columns],
        memory_usage_bytes=int(dataframe.memory_usage(deep=True).sum()),
    )


def build_statistics(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive statistics for the dataset using pandas.

    Uses `DataFrame.describe(include="all")` so both numeric and
    non-numeric columns are represented in a single summary table.

    Args:
        dataframe: The dataset to analyze.

    Returns:
        A DataFrame produced by `describe(include="all")`, transposed
        so each row corresponds to one column of the original dataset.
    """
    return dataframe.describe(include="all").transpose()
