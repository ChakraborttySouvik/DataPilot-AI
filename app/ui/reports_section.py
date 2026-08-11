"""
DataPilot AI - Automated Business Intelligence PDF Report.

This module generates a professional, dataset-independent PDF report
from the DataFrame already loaded by DataPilot AI.

The report is designed to work with many structured datasets, including:
- Sales
- Employees / HR
- Students / Education
- Customers
- Finance
- Marketing
- Banking
- Inventory
- Operations
- General business datasets

It does NOT assume specific column names.

Architecture:
    Streamlit
        -> render_report_section(dataframe)
        -> generate_report_pdf(dataframe)
        -> dynamic analysis
        -> charts + tables
        -> 12-page PDF
"""

from __future__ import annotations

import io
import math
import re
import warnings
from datetime import datetime
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image as RLImage,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ============================================================
# PAGE / DESIGN CONSTANTS
# ============================================================

PAGE_SIZE = landscape(A4)

PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE

MARGIN_LEFT = 14 * mm
MARGIN_RIGHT = 14 * mm
MARGIN_TOP = 13 * mm
MARGIN_BOTTOM = 13 * mm

# Professional BI palette.
NAVY = colors.HexColor("#172554")
BLUE = colors.HexColor("#2563EB")
CYAN = colors.HexColor("#0891B2")
TEAL = colors.HexColor("#0F766E")
PURPLE = colors.HexColor("#7C3AED")
ORANGE = colors.HexColor("#EA580C")
GREEN = colors.HexColor("#16A34A")
RED = colors.HexColor("#DC2626")
AMBER = colors.HexColor("#D97706")

LIGHT_BLUE = colors.HexColor("#EFF6FF")
LIGHT_CYAN = colors.HexColor("#ECFEFF")
LIGHT_PURPLE = colors.HexColor("#F5F3FF")
LIGHT_GREEN = colors.HexColor("#F0FDF4")
LIGHT_ORANGE = colors.HexColor("#FFF7ED")

LIGHT_GRAY = colors.HexColor("#F8FAFC")
MID_GRAY = colors.HexColor("#E2E8F0")
TEXT = colors.HexColor("#1E293B")
MUTED = colors.HexColor("#64748B")
WHITE = colors.white


# ============================================================
# GENERAL HELPERS
# ============================================================

def _safe_string(value: Any) -> str:
    """Convert a value safely to readable text."""
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value)


def _clean_column_name(column: Any) -> str:
    """Convert a column name to a readable label."""
    text = _safe_string(column)

    text = re.sub(r"[_\-]+", " ", text)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)

    return text.strip().title()


def _short_text(text: Any, max_length: int = 32) -> str:
    """Shorten long labels."""
    value = _safe_string(text)

    if len(value) <= max_length:
        return value

    return value[: max_length - 3] + "..."


def _format_number(value: Any) -> str:
    """Format numbers compactly for KPI cards and report text."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return _safe_string(value)

    if math.isnan(value) or math.isinf(value):
        return "N/A"

    absolute = abs(value)

    if absolute >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"

    if absolute >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"

    if absolute >= 1_000:
        return f"{value / 1_000:.2f}K"

    if value.is_integer():
        return f"{int(value):,}"

    return f"{value:,.2f}"


def _format_percent(value: float) -> str:
    """Format percentage."""
    return f"{value:.1f}%"


def _format_memory(bytes_value: int) -> str:
    """Format memory size."""
    if bytes_value < 1024:
        return f"{bytes_value} B"

    if bytes_value < 1024**2:
        return f"{bytes_value / 1024:.1f} KB"

    if bytes_value < 1024**3:
        return f"{bytes_value / 1024**2:.2f} MB"

    return f"{bytes_value / 1024**3:.2f} GB"


def _is_numeric(series: pd.Series) -> bool:
    """Return True when a Series is numeric."""
    return pd.api.types.is_numeric_dtype(series)


def _is_datetime(series: pd.Series) -> bool:
    """Return True when a Series is already datetime."""
    return pd.api.types.is_datetime64_any_dtype(series)


def _try_datetime_column(series: pd.Series) -> bool:
    """
    Detect whether an object/string column is probably a date.

    Only a sample is parsed so large datasets remain reasonably fast.
    """
    if _is_datetime(series):
        return True

    if not (
        pd.api.types.is_object_dtype(series)
        or pd.api.types.is_string_dtype(series)
    ):
        return False

    values = series.dropna()

    if values.empty:
        return False

    sample = values.head(100)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        parsed = pd.to_datetime(
            sample,
            errors="coerce",
        )

    success_rate = parsed.notna().mean()

    return bool(success_rate >= 0.90)


def _detect_date_columns(dataframe: pd.DataFrame) -> list[str]:
    """Return probable date columns."""
    result: list[str] = []

    for column in dataframe.columns:
        try:
            if _try_datetime_column(dataframe[column]):
                result.append(column)
        except Exception:
            continue

    return result


def _detect_numeric_columns(dataframe: pd.DataFrame) -> list[str]:
    """Return numeric columns."""
    return [
        column
        for column in dataframe.columns
        if _is_numeric(dataframe[column])
    ]


def _detect_categorical_columns(dataframe: pd.DataFrame) -> list[str]:
    """
    Return useful categorical columns.

    Extremely high-cardinality columns are excluded because they are
    usually IDs or free text rather than useful categories.
    """
    result: list[str] = []

    row_count = max(len(dataframe), 1)

    for column in dataframe.columns:
        series = dataframe[column]

        if _is_numeric(series):
            continue

        if _try_datetime_column(series):
            continue

        unique_count = series.nunique(dropna=True)

        if unique_count < 2:
            continue

        # Ignore near-unique identifier columns.
        if unique_count > 100 and unique_count / row_count > 0.30:
            continue

        if unique_count <= 30:
            result.append(column)

    return result


def _detect_id_like_columns(dataframe: pd.DataFrame) -> list[str]:
    """Detect columns that appear to be identifiers."""
    result: list[str] = []

    row_count = max(len(dataframe), 1)

    for column in dataframe.columns:
        series = dataframe[column]

        unique_count = series.nunique(dropna=True)

        name = _safe_string(column).lower()

        looks_like_name = any(
            token in name
            for token in (
                "id",
                "identifier",
                "code",
                "uuid",
            )
        )

        high_cardinality = (
            unique_count / row_count >= 0.90
            and unique_count > 20
        )

        if looks_like_name and high_cardinality:
            result.append(column)

    return result


def _choose_primary_numeric_column(
    dataframe: pd.DataFrame,
) -> str | None:
    """
    Select a meaningful numeric column.

    Business-like names receive priority over arbitrary numeric columns.
    """
    numeric_columns = _detect_numeric_columns(dataframe)

    if not numeric_columns:
        return None

    priority_tokens = (
        "sales",
        "revenue",
        "amount",
        "profit",
        "income",
        "salary",
        "wage",
        "price",
        "value",
        "score",
        "marks",
        "grade",
        "rating",
        "quantity",
        "units",
        "total",
        "balance",
        "cost",
        "expense",
    )

    scored: list[tuple[int, str]] = []

    for column in numeric_columns:
        name = _safe_string(column).lower()

        score = 0

        for token in priority_tokens:
            if token in name:
                score += 10

        # Avoid obvious ID columns.
        if "id" in name:
            score -= 20

        scored.append((score, column))

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return scored[0][1]


def _choose_secondary_numeric_column(
    dataframe: pd.DataFrame,
    primary: str | None,
) -> str | None:
    """Select a second meaningful numeric column."""
    numeric_columns = _detect_numeric_columns(dataframe)

    candidates = [
        column
        for column in numeric_columns
        if column != primary
    ]

    if not candidates:
        return None

    priority_tokens = (
        "profit",
        "salary",
        "score",
        "marks",
        "experience",
        "quantity",
        "amount",
        "revenue",
        "cost",
        "age",
        "rating",
    )

    def score_column(column: str) -> int:
        name = _safe_string(column).lower()

        return sum(
            10
            for token in priority_tokens
            if token in name
        )

    candidates.sort(
        key=score_column,
        reverse=True,
    )

    return candidates[0]


# ============================================================
# DYNAMIC ANALYSIS
# ============================================================

def _calculate_data_health(dataframe: pd.DataFrame) -> float:
    """Calculate a simple completeness/duplicate health score."""
    if dataframe.empty:
        return 0.0

    total_cells = dataframe.shape[0] * dataframe.shape[1]

    missing = int(
        dataframe.isna().sum().sum()
    )

    missing_ratio = (
        missing / total_cells
        if total_cells
        else 0
    )

    duplicate_ratio = (
        dataframe.duplicated().sum()
        / len(dataframe)
        if len(dataframe)
        else 0
    )

    score = 100 * (
        1
        - min(missing_ratio, 1)
        - min(duplicate_ratio, 1)
    )

    return max(0.0, min(100.0, score))


def _get_kpis(dataframe: pd.DataFrame) -> list[tuple[str, str]]:
    """Create four generic KPI values."""
    kpis: list[tuple[str, str]] = []

    # KPI 1: records
    kpis.append(
        (
            "Total Records",
            _format_number(len(dataframe)),
        )
    )

    primary = _choose_primary_numeric_column(dataframe)

    if primary is not None:
        series = pd.to_numeric(
            dataframe[primary],
            errors="coerce",
        ).dropna()

        if not series.empty:
            name = _clean_column_name(primary)

            # Prefer sum when a metric is naturally aggregatable.
            aggregatable_tokens = (
                "sales",
                "revenue",
                "amount",
                "profit",
                "income",
                "salary",
                "wage",
                "cost",
                "expense",
                "quantity",
                "units",
                "value",
                "marks",
            )

            if any(
                token in _safe_string(primary).lower()
                for token in aggregatable_tokens
            ):
                kpis.append(
                    (
                        f"Total {name}",
                        _format_number(series.sum()),
                    )
                )
            else:
                kpis.append(
                    (
                        f"Average {name}",
                        _format_number(series.mean()),
                    )
                )

            kpis.append(
                (
                    f"Median {name}",
                    _format_number(series.median()),
                )
            )
        else:
            kpis.append(
                (
                    "Numeric Fields",
                    str(len(_detect_numeric_columns(dataframe))),
                )
            )
    else:
        kpis.append(
            (
                "Columns",
                str(dataframe.shape[1]),
            )
        )

        kpis.append(
            (
                "Categories",
                str(len(_detect_categorical_columns(dataframe))),
            )
        )

    health = _calculate_data_health(dataframe)

    kpis.append(
        (
            "Data Health",
            _format_percent(health),
        )
    )

    return kpis[:4]


def _grouped_numeric_data(
    dataframe: pd.DataFrame,
    category_column: str,
    numeric_column: str,
) -> pd.DataFrame:
    """Create category-level mean and count data."""
    temp = dataframe[
        [category_column, numeric_column]
    ].copy()

    temp[numeric_column] = pd.to_numeric(
        temp[numeric_column],
        errors="coerce",
    )

    temp = temp.dropna(
        subset=[category_column, numeric_column]
    )

    grouped = (
        temp.groupby(category_column)[numeric_column]
        .agg(["mean", "sum", "count"])
        .sort_values("mean", ascending=False)
    )

    return grouped


def _choose_category_column(
    dataframe: pd.DataFrame,
) -> str | None:
    """Select the most useful categorical column."""
    categories = _detect_categorical_columns(dataframe)

    if not categories:
        return None

    priority_tokens = (
        "department",
        "category",
        "region",
        "segment",
        "course",
        "class",
        "grade",
        "gender",
        "type",
        "status",
        "product",
        "payment",
        "city",
        "country",
    )

    def score_column(column: str) -> int:
        name = _safe_string(column).lower()

        score = 0

        for token in priority_tokens:
            if token in name:
                score += 10

        unique_count = dataframe[column].nunique(
            dropna=True
        )

        if 2 <= unique_count <= 8:
            score += 5

        return score

    categories.sort(
        key=score_column,
        reverse=True,
    )

    return categories[0]


def _choose_second_category_column(
    dataframe: pd.DataFrame,
    primary: str | None,
) -> str | None:
    """Select a second categorical column."""
    categories = [
        column
        for column in _detect_categorical_columns(dataframe)
        if column != primary
    ]

    if not categories:
        return None

    return categories[0]


# ============================================================
# CHART CREATION
# ============================================================

def _chart_to_image(
    figure: plt.Figure,
    width: float = 125,
    height: float = 70,
) -> RLImage:
    """Convert a Matplotlib figure into a ReportLab image."""
    buffer = io.BytesIO()

    figure.savefig(
        buffer,
        format="png",
        dpi=170,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(figure)

    buffer.seek(0)

    image = RLImage(
        buffer,
        width=width * mm,
        height=height * mm,
    )

    return image


def _empty_chart(
    title: str,
    message: str,
) -> RLImage:
    """Create a clean placeholder chart."""
    figure, axis = plt.subplots(
        figsize=(6, 3),
    )

    axis.axis("off")

    axis.text(
        0.5,
        0.58,
        title,
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
    )

    axis.text(
        0.5,
        0.40,
        message,
        ha="center",
        va="center",
        fontsize=10,
        color="#64748B",
    )

    return _chart_to_image(
        figure,
        width=125,
        height=70,
    )


def _create_category_chart(
    dataframe: pd.DataFrame,
) -> RLImage:
    """Create category vs primary metric chart."""
    category = _choose_category_column(dataframe)
    numeric = _choose_primary_numeric_column(dataframe)

    if category is None:
        return _empty_chart(
            "Category Analysis",
            "No suitable categorical field was detected.",
        )

    if numeric is None:
        counts = (
            dataframe[category]
            .value_counts()
            .head(8)
            .sort_values()
        )

        figure, axis = plt.subplots(
            figsize=(7, 3.5)
        )

        counts.plot(
            kind="barh",
            ax=axis,
            color="#2563EB",
        )

        axis.set_title(
            f"Records by {_clean_column_name(category)}",
            fontweight="bold",
        )

        axis.set_xlabel("Records")
        axis.set_ylabel("")

        figure.tight_layout()

        return _chart_to_image(
            figure,
            width=125,
            height=70,
        )

    grouped = _grouped_numeric_data(
        dataframe,
        category,
        numeric,
    )

    grouped = grouped.head(8).sort_values("mean")

    figure, axis = plt.subplots(
        figsize=(7, 3.5)
    )

    axis.barh(
        [
            _short_text(value, 22)
            for value in grouped.index
        ],
        grouped["mean"],
        color="#2563EB",
    )

    axis.set_title(
        f"Average {_clean_column_name(numeric)} by "
        f"{_clean_column_name(category)}",
        fontweight="bold",
    )

    axis.set_xlabel(
        f"Average {_clean_column_name(numeric)}"
    )

    axis.grid(
        axis="x",
        alpha=0.20,
    )

    figure.tight_layout()

    return _chart_to_image(
        figure,
        width=125,
        height=70,
    )


def _create_second_category_chart(
    dataframe: pd.DataFrame,
) -> RLImage:
    """Create a second categorical chart."""
    category = _choose_second_category_column(
        dataframe,
        _choose_category_column(dataframe),
    )

    if category is None:
        return _empty_chart(
            "Categorical Analysis",
            "No additional categorical field was detected.",
        )

    counts = (
        dataframe[category]
        .value_counts()
        .head(8)
        .sort_values()
    )

    figure, axis = plt.subplots(
        figsize=(7, 3.5)
    )

    axis.barh(
        [
            _short_text(value, 22)
            for value in counts.index
        ],
        counts.values,
        color="#7C3AED",
    )

    axis.set_title(
        f"Records by {_clean_column_name(category)}",
        fontweight="bold",
    )

    axis.set_xlabel("Records")
    axis.grid(
        axis="x",
        alpha=0.20,
    )

    figure.tight_layout()

    return _chart_to_image(
        figure,
        width=125,
        height=70,
    )


def _create_distribution_chart(
    dataframe: pd.DataFrame,
) -> RLImage:
    """Create histogram of primary numeric column."""
    numeric = _choose_primary_numeric_column(dataframe)

    if numeric is None:
        return _empty_chart(
            "Numeric Distribution",
            "No numeric field was detected.",
        )

    values = pd.to_numeric(
        dataframe[numeric],
        errors="coerce",
    ).dropna()

    if values.empty:
        return _empty_chart(
            "Numeric Distribution",
            "The selected field contains no usable numeric values.",
        )

    figure, axis = plt.subplots(
        figsize=(7, 3.5)
    )

    axis.hist(
        values,
        bins=25,
        color="#0891B2",
        edgecolor="white",
        alpha=0.90,
    )

    axis.axvline(
        values.mean(),
        linestyle="--",
        linewidth=2,
        color="#EA580C",
        label=f"Mean: {_format_number(values.mean())}",
    )

    axis.axvline(
        values.median(),
        linestyle=":",
        linewidth=2,
        color="#7C3AED",
        label=f"Median: {_format_number(values.median())}",
    )

    axis.set_title(
        f"Distribution of {_clean_column_name(numeric)}",
        fontweight="bold",
    )

    axis.set_xlabel(
        _clean_column_name(numeric)
    )

    axis.set_ylabel("Frequency")

    axis.legend(
        frameon=False,
    )

    axis.grid(
        axis="y",
        alpha=0.18,
    )

    figure.tight_layout()

    return _chart_to_image(
        figure,
        width=125,
        height=70,
    )


def _create_boxplot_chart(
    dataframe: pd.DataFrame,
) -> RLImage:
    """Create a boxplot for the primary numeric column."""
    numeric = _choose_primary_numeric_column(dataframe)

    if numeric is None:
        return _empty_chart(
            "Outlier Analysis",
            "No numeric field was detected.",
        )

    values = pd.to_numeric(
        dataframe[numeric],
        errors="coerce",
    ).dropna()

    if values.empty:
        return _empty_chart(
            "Outlier Analysis",
            "No usable numeric values were detected.",
        )

    figure, axis = plt.subplots(
        figsize=(7, 3.5)
    )

    axis.boxplot(
        values,
        vert=False,
        patch_artist=True,
        boxprops={
            "facecolor": "#F5F3FF",
            "edgecolor": "#7C3AED",
        },
        medianprops={
            "color": "#EA580C",
            "linewidth": 2,
        },
    )

    axis.set_title(
        f"Outlier Review — {_clean_column_name(numeric)}",
        fontweight="bold",
    )

    axis.set_xlabel(
        _clean_column_name(numeric)
    )

    axis.grid(
        axis="x",
        alpha=0.18,
    )

    figure.tight_layout()

    return _chart_to_image(
        figure,
        width=125,
        height=70,
    )


def _create_relationship_chart(
    dataframe: pd.DataFrame,
) -> RLImage:
    """Create scatter chart for two numeric fields."""
    primary = _choose_primary_numeric_column(dataframe)
    secondary = _choose_secondary_numeric_column(
        dataframe,
        primary,
    )

    if primary is None or secondary is None:
        return _empty_chart(
            "Relationship Analysis",
            "At least two numeric fields are required.",
        )

    temp = dataframe[
        [primary, secondary]
    ].copy()

    temp[primary] = pd.to_numeric(
        temp[primary],
        errors="coerce",
    )

    temp[secondary] = pd.to_numeric(
        temp[secondary],
        errors="coerce",
    )

    temp = temp.dropna()

    if len(temp) < 3:
        return _empty_chart(
            "Relationship Analysis",
            "Not enough valid observations.",
        )

    correlation = temp[primary].corr(
        temp[secondary]
    )

    figure, axis = plt.subplots(
        figsize=(7, 3.5)
    )

    axis.scatter(
        temp[primary],
        temp[secondary],
        alpha=0.55,
        color="#2563EB",
        edgecolors="none",
    )

    axis.set_title(
        f"{_clean_column_name(primary)} vs "
        f"{_clean_column_name(secondary)}",
        fontweight="bold",
    )

    axis.set_xlabel(
        _clean_column_name(primary)
    )

    axis.set_ylabel(
        _clean_column_name(secondary)
    )

    axis.text(
        0.03,
        0.94,
        f"Correlation: {correlation:.2f}",
        transform=axis.transAxes,
        fontsize=10,
        fontweight="bold",
        verticalalignment="top",
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "white",
            "edgecolor": "#CBD5E1",
        },
    )

    axis.grid(
        alpha=0.18,
    )

    figure.tight_layout()

    return _chart_to_image(
        figure,
        width=125,
        height=70,
    )


def _create_correlation_chart(
    dataframe: pd.DataFrame,
) -> RLImage:
    """Create correlation matrix for numeric variables."""
    numeric_columns = _detect_numeric_columns(dataframe)

    if len(numeric_columns) < 2:
        return _empty_chart(
            "Correlation Analysis",
            "At least two numeric fields are required.",
        )

    selected = numeric_columns[:8]

    corr = dataframe[selected].corr()

    figure, axis = plt.subplots(
        figsize=(7, 4)
    )

    image = axis.imshow(
        corr.values,
        cmap="Blues",
        vmin=-1,
        vmax=1,
    )

    axis.set_xticks(
        range(len(selected))
    )

    axis.set_yticks(
        range(len(selected))
    )

    axis.set_xticklabels(
        [
            _short_text(
                _clean_column_name(column),
                14,
            )
            for column in selected
        ],
        rotation=45,
        ha="right",
        fontsize=8,
    )

    axis.set_yticklabels(
        [
            _short_text(
                _clean_column_name(column),
                18,
            )
            for column in selected
        ],
        fontsize=8,
    )

    for row in range(len(selected)):
        for col in range(len(selected)):
            axis.text(
                col,
                row,
                f"{corr.iloc[row, col]:.2f}",
                ha="center",
                va="center",
                fontsize=7,
            )

    axis.set_title(
        "Numeric Correlation Matrix",
        fontweight="bold",
    )

    figure.colorbar(
        image,
        ax=axis,
        fraction=0.046,
        pad=0.04,
    )

    figure.tight_layout()

    return _chart_to_image(
        figure,
        width=125,
        height=78,
    )


def _create_time_chart(
    dataframe: pd.DataFrame,
) -> RLImage | None:
    """Create a monthly/yearly trend when a date column exists."""
    date_columns = _detect_date_columns(dataframe)

    numeric = _choose_primary_numeric_column(
        dataframe
    )

    if not date_columns or numeric is None:
        return None

    date_column = date_columns[0]

    temp = dataframe[
        [date_column, numeric]
    ].copy()

    temp[date_column] = pd.to_datetime(
        temp[date_column],
        errors="coerce",
    )

    temp[numeric] = pd.to_numeric(
        temp[numeric],
        errors="coerce",
    )

    temp = temp.dropna()

    if temp.empty:
        return None

    # Aggregate monthly for readability.
    temp["period"] = (
        temp[date_column]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    trend = (
        temp.groupby("period")[numeric]
        .sum()
        .sort_index()
    )

    if len(trend) > 36:
        trend = trend.tail(36)

    figure, axis = plt.subplots(
        figsize=(7, 3.5)
    )

    axis.plot(
        trend.index,
        trend.values,
        linewidth=2.5,
        color="#2563EB",
        marker="o",
        markersize=3,
    )

    axis.fill_between(
        trend.index,
        trend.values,
        alpha=0.08,
        color="#2563EB",
    )

    axis.set_title(
        f"Time Trend of {_clean_column_name(numeric)}",
        fontweight="bold",
    )

    axis.set_xlabel("Period")
    axis.set_ylabel(
        _clean_column_name(numeric)
    )

    axis.grid(
        alpha=0.18,
    )

    figure.autofmt_xdate()

    figure.tight_layout()

    return _chart_to_image(
        figure,
        width=125,
        height=70,
    )


# ============================================================
# REPORT TEXT / INSIGHTS
# ============================================================

def _build_overview_insights(
    dataframe: pd.DataFrame,
) -> list[str]:
    """Create short factual overview statements."""
    insights: list[str] = []

    rows, columns = dataframe.shape

    insights.append(
        f"The dataset contains {rows:,} records across "
        f"{columns:,} columns."
    )

    missing = int(
        dataframe.isna().sum().sum()
    )

    duplicates = int(
        dataframe.duplicated().sum()
    )

    if missing == 0:
        insights.append(
            "No missing values were detected in the uploaded dataset."
        )
    else:
        insights.append(
            f"{missing:,} missing values were detected across "
            "the dataset."
        )

    if duplicates == 0:
        insights.append(
            "No fully duplicated rows were detected."
        )
    else:
        insights.append(
            f"{duplicates:,} duplicated rows were detected."
        )

    return insights


def _build_metric_insight(
    dataframe: pd.DataFrame,
) -> str:
    """Create a short metric interpretation."""
    numeric = _choose_primary_numeric_column(
        dataframe
    )

    if numeric is None:
        return (
            "The dataset does not contain a suitable numeric "
            "field for metric-based interpretation."
        )

    values = pd.to_numeric(
        dataframe[numeric],
        errors="coerce",
    ).dropna()

    if values.empty:
        return (
            f"{_clean_column_name(numeric)} does not contain "
            "enough valid numeric observations."
        )

    mean = values.mean()
    median = values.median()

    if mean > median * 1.10:
        shape = (
            "The mean is noticeably above the median, suggesting "
            "that higher-value observations are influencing the average."
        )
    elif median > mean * 1.10:
        shape = (
            "The median is above the mean, suggesting that lower-value "
            "observations may be pulling the average downward."
        )
    else:
        shape = (
            "The mean and median are relatively close, indicating "
            "a broadly balanced central distribution."
        )

    return (
        f"{_clean_column_name(numeric)} has a mean of "
        f"{_format_number(mean)} and a median of "
        f"{_format_number(median)}. {shape}"
    )


def _build_relationship_insight(
    dataframe: pd.DataFrame,
) -> str:
    """Create relationship explanation."""
    primary = _choose_primary_numeric_column(dataframe)

    secondary = _choose_secondary_numeric_column(
        dataframe,
        primary,
    )

    if primary is None or secondary is None:
        return (
            "A relationship analysis could not be completed because "
            "at least two numeric variables are required."
        )

    temp = dataframe[
        [primary, secondary]
    ].copy()

    temp[primary] = pd.to_numeric(
        temp[primary],
        errors="coerce",
    )

    temp[secondary] = pd.to_numeric(
        temp[secondary],
        errors="coerce",
    )

    temp = temp.dropna()

    if len(temp) < 3:
        return (
            "There are not enough valid observations for a "
            "reliable relationship analysis."
        )

    correlation = temp[primary].corr(
        temp[secondary]
    )

    absolute = abs(correlation)

    if absolute >= 0.70:
        strength = "strong"
    elif absolute >= 0.40:
        strength = "moderate"
    elif absolute >= 0.20:
        strength = "weak"
    else:
        strength = "limited"

    direction = (
        "positive"
        if correlation >= 0
        else "negative"
    )

    return (
        f"{_clean_column_name(primary)} and "
        f"{_clean_column_name(secondary)} show a "
        f"{strength} {direction} relationship "
        f"(correlation {correlation:.2f})."
    )


def _build_distribution_insight(
    dataframe: pd.DataFrame,
) -> str:
    """Create distribution explanation."""
    numeric = _choose_primary_numeric_column(
        dataframe
    )

    if numeric is None:
        return (
            "No suitable numeric variable was detected "
            "for distribution analysis."
        )

    values = pd.to_numeric(
        dataframe[numeric],
        errors="coerce",
    ).dropna()

    if values.empty:
        return "No valid numeric observations were available."

    mean = values.mean()
    median = values.median()

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)

    iqr = q3 - q1

    if iqr == 0:
        outliers = 0
    else:
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers = int(
            ((values < lower) | (values > upper)).sum()
        )

    return (
        f"{_clean_column_name(numeric)} spans from "
        f"{_format_number(values.min())} to "
        f"{_format_number(values.max())}. "
        f"The interquartile range is "
        f"{_format_number(iqr)}, with approximately "
        f"{outliers:,} potential outlier observations based on "
        "the IQR rule."
    )


def _build_category_insight(
    dataframe: pd.DataFrame,
) -> str:
    """Create category comparison insight."""
    category = _choose_category_column(
        dataframe
    )

    numeric = _choose_primary_numeric_column(
        dataframe
    )

    if category is None:
        return (
            "No suitable categorical variable was detected."
        )

    if numeric is None:
        top = (
            dataframe[category]
            .value_counts()
            .head(1)
        )

        if top.empty:
            return "No category distribution was available."

        value = top.index[0]

        return (
            f"{_clean_column_name(category)} is most concentrated "
            f"in the '{_short_text(value)}' category."
        )

    grouped = _grouped_numeric_data(
        dataframe,
        category,
        numeric,
    )

    if grouped.empty:
        return "No valid grouped observations were available."

    highest = grouped.index[0]
    lowest = grouped.index[-1]

    return (
        f"The '{_short_text(highest)}' "
        f"{_clean_column_name(category)} group has the highest "
        f"average {_clean_column_name(numeric)}, while "
        f"'{_short_text(lowest)}' has the lowest among the "
        "largest available groups."
    )


def _build_time_insight(
    dataframe: pd.DataFrame,
) -> str:
    """Create time-trend insight."""
    date_columns = _detect_date_columns(
        dataframe
    )

    numeric = _choose_primary_numeric_column(
        dataframe
    )

    if not date_columns or numeric is None:
        return (
            "No suitable date and numeric combination was detected "
            "for time-based analysis."
        )

    date_column = date_columns[0]

    temp = dataframe[
        [date_column, numeric]
    ].copy()

    temp[date_column] = pd.to_datetime(
        temp[date_column],
        errors="coerce",
    )

    temp[numeric] = pd.to_numeric(
        temp[numeric],
        errors="coerce",
    )

    temp = temp.dropna()

    if temp.empty:
        return "No valid time-series observations were available."

    temp["period"] = (
        temp[date_column]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    trend = (
        temp.groupby("period")[numeric]
        .sum()
        .sort_index()
    )

    if len(trend) < 2:
        return (
            "The dataset does not contain enough time periods "
            "for a meaningful trend comparison."
        )

    first = trend.iloc[0]
    last = trend.iloc[-1]

    if first == 0:
        return (
            f"The time series contains {len(trend)} periods, "
            "but percentage growth could not be calculated "
            "from a zero starting value."
        )

    change = ((last - first) / abs(first)) * 100

    if change > 5:
        direction = "increased"
    elif change < -5:
        direction = "decreased"
    else:
        direction = "remained relatively stable"

    return (
        f"{_clean_column_name(numeric)} {direction} by approximately "
        f"{abs(change):.1f}% between the first and last available "
        "period in the report."
    )


# ============================================================
# REPORT STYLES
# ============================================================

def _styles() -> dict[str, ParagraphStyle]:
    """Create ReportLab styles."""
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=MUTED,
        ),
        "page_title": ParagraphStyle(
            "PageTitle",
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            textColor=NAVY,
            spaceAfter=4,
        ),
        "section": ParagraphStyle(
            "Section",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=TEXT,
            spaceBefore=3,
            spaceAfter=7,
        ),
        "body": ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=TEXT,
        ),
        "small": ParagraphStyle(
            "Small",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=MUTED,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            leftIndent=10,
            firstLineIndent=-7,
            textColor=TEXT,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=WHITE,
            alignment=TA_LEFT,
        ),
        "table_body": ParagraphStyle(
            "TableBody",
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
            textColor=TEXT,
        ),
        "kpi_label": ParagraphStyle(
            "KpiLabel",
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=10,
            textColor=MUTED,
        ),
        "kpi_value": ParagraphStyle(
            "KpiValue",
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=20,
            textColor=NAVY,
        ),
        "insight": ParagraphStyle(
            "Insight",
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=TEXT,
            leftIndent=5,
        ),
    }


# ============================================================
# PDF ELEMENT HELPERS
# ============================================================

def _page_header(
    styles: dict[str, ParagraphStyle],
    title: str,
    subtitle: str = "",
) -> list[Any]:
    """Create a standard report page header."""
    elements: list[Any] = []

    elements.append(
        Paragraph(
            title,
            styles["page_title"],
        )
    )

    if subtitle:
        elements.append(
            Paragraph(
                subtitle,
                styles["subtitle"],
            )
        )

    elements.append(
        Spacer(1, 5 * mm)
    )

    return elements


def _kpi_table(
    kpis: list[tuple[str, str]],
    styles: dict[str, ParagraphStyle],
) -> Table:
    """Create a row of KPI cards."""
    cards = []

    card_colors = [
        LIGHT_BLUE,
        LIGHT_CYAN,
        LIGHT_PURPLE,
        LIGHT_GREEN,
    ]

    for index, (label, value) in enumerate(kpis):
        card = Table(
            [
                [
                    Paragraph(
                        label.upper(),
                        styles["kpi_label"],
                    )
                ],
                [
                    Paragraph(
                        value,
                        styles["kpi_value"],
                    )
                ],
            ],
            colWidths=[60 * mm],
            rowHeights=[10 * mm, 18 * mm],
        )

        card.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        card_colors[
                            index % len(card_colors)
                        ],
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.7,
                        MID_GRAY,
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        5 * mm,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        5 * mm,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        3 * mm,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        3 * mm,
                    ),
                ]
            )
        )

        cards.append(card)

    table = Table(
        [cards],
        colWidths=[
            63 * mm
            for _ in cards
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2 * mm,
                ),
            ]
        )
    )

    return table


def _two_chart_table(
    first: RLImage,
    second: RLImage,
) -> Table:
    """Place two charts side-by-side."""
    table = Table(
        [
            [first, second]
        ],
        colWidths=[
            130 * mm,
            130 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    1 * mm,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    1 * mm,
                ),
            ]
        )
    )

    return table


def _bullet_list(
    items: list[str],
    styles: dict[str, ParagraphStyle],
) -> list[Paragraph]:
    """Create bullet paragraphs."""
    result = []

    for item in items:
        result.append(
            Paragraph(
                f"• {_safe_string(item)}",
                styles["bullet"],
            )
        )

        result.append(
            Spacer(1, 1.5 * mm)
        )

    return result


def _dataframe_table(
    dataframe: pd.DataFrame,
    styles: dict[str, ParagraphStyle],
    max_rows: int = 12,
    max_columns: int = 8,
) -> Table:
    """Convert a DataFrame into a readable PDF table."""
    if dataframe.empty:
        return Table(
            [
                [
                    Paragraph(
                        "No data available.",
                        styles["body"],
                    )
                ]
            ]
        )

    display = dataframe.copy()

    display = display.iloc[
        :max_rows,
        :max_columns,
    ]

    headers = [
        _clean_column_name(column)
        for column in display.columns
    ]

    rows = [
        [
            Paragraph(
                _short_text(header, 25),
                styles["table_header"],
            )
            for header in headers
        ]
    ]

    for _, row in display.iterrows():
        rows.append(
            [
                Paragraph(
                    _short_text(
                        _safe_string(value),
                        28,
                    ),
                    styles["table_body"],
                )
                for value in row
            ]
        )

    available_width = (
        PAGE_WIDTH
        - MARGIN_LEFT
        - MARGIN_RIGHT
    )

    column_width = available_width / max(
        len(headers),
        1,
    )

    table = Table(
        rows,
        colWidths=[
            column_width
            for _ in headers
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    NAVY,
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    WHITE,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    MID_GRAY,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        WHITE,
                        LIGHT_GRAY,
                    ],
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    return table


# ============================================================
# PAGE FOOTER
# ============================================================

def _draw_footer(canvas, document):
    """Draw page number and DataPilot AI footer."""
    canvas.saveState()

    canvas.setStrokeColor(
        MID_GRAY
    )

    canvas.line(
        MARGIN_LEFT,
        9 * mm,
        PAGE_WIDTH - MARGIN_RIGHT,
        9 * mm,
    )

    canvas.setFont(
        "Helvetica",
        7.5,
    )

    canvas.setFillColor(
        MUTED
    )

    canvas.drawString(
        MARGIN_LEFT,
        5.5 * mm,
        "DataPilot AI • Automated Business Intelligence Report",
    )

    canvas.drawRightString(
        PAGE_WIDTH - MARGIN_RIGHT,
        5.5 * mm,
        f"Page {document.page}",
    )

    canvas.restoreState()


# ============================================================
# PDF GENERATION
# ============================================================

def generate_report_pdf(
    dataframe: pd.DataFrame,
    dataset_name: str = "Uploaded Dataset",
) -> bytes:
    """
    Generate the complete 12-page DataPilot AI PDF report.

    Args:
        dataframe: Uploaded pandas DataFrame.
        dataset_name: Optional dataset filename.

    Returns:
        PDF bytes.
    """
    if dataframe is None or dataframe.empty:
        raise ValueError(
            "Cannot generate a report from an empty dataset."
        )

    styles = _styles()

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=PAGE_SIZE,
        leftMargin=MARGIN_LEFT,
        rightMargin=MARGIN_RIGHT,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title="DataPilot AI Business Intelligence Report",
        author="DataPilot AI",
    )

    story: list[Any] = []

    # --------------------------------------------------------
    # PAGE 1 — EXECUTIVE DASHBOARD
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "DataPilot AI",
            styles["title"],
        )
    )

    story.append(
        Paragraph(
            "BUSINESS INTELLIGENCE REPORT",
            styles["subtitle"],
        )
    )

    story.append(
        Spacer(1, 4 * mm)
    )

    story.append(
        Paragraph(
            _short_text(
                dataset_name,
                100,
            ),
            styles["body"],
        )
    )

    story.append(
        Spacer(1, 5 * mm)
    )

    kpis = _get_kpis(dataframe)

    story.append(
        _kpi_table(
            kpis,
            styles,
        )
    )

    story.append(
        Spacer(1, 7 * mm)
    )

    story.append(
        Paragraph(
            "Executive Dashboard",
            styles["section"],
        )
    )

    story.append(
        _two_chart_table(
            _create_category_chart(dataframe),
            _create_second_category_chart(dataframe),
        )
    )

    story.append(
        Spacer(1, 4 * mm)
    )

    story.append(
        _two_chart_table(
            _create_distribution_chart(dataframe),
            _create_relationship_chart(dataframe),
        )
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 2 — DATASET OVERVIEW
    # --------------------------------------------------------

    story.extend(
        _page_header(
            styles,
            "Dataset Overview",
            "A high-level view of structure, completeness and dataset composition.",
        )
    )

    overview_data = [
        ("Records", f"{len(dataframe):,}"),
        ("Columns", f"{dataframe.shape[1]:,}"),
        (
            "Memory Usage",
            _format_memory(
                int(
                    dataframe.memory_usage(
                        deep=True
                    ).sum()
                )
            ),
        ),
        (
            "Missing Values",
            f"{int(dataframe.isna().sum().sum()):,}",
        ),
        (
            "Duplicate Rows",
            f"{int(dataframe.duplicated().sum()):,}",
        ),
        (
            "Numeric Columns",
            f"{len(_detect_numeric_columns(dataframe))}",
        ),
        (
            "Categorical Columns",
            f"{len(_detect_categorical_columns(dataframe))}",
        ),
        (
            "Date Columns",
            f"{len(_detect_date_columns(dataframe))}",
        ),
    ]

    overview_rows = [
        [
            Paragraph("Metric", styles["table_header"]),
            Paragraph("Value", styles["table_header"]),
        ]
    ]

    for label, value in overview_data:
        overview_rows.append(
            [
                Paragraph(label, styles["table_body"]),
                Paragraph(value, styles["table_body"]),
            ]
        )

    overview_table = Table(
        overview_rows,
        colWidths=[
            70 * mm,
            55 * mm,
        ],
    )

    overview_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    NAVY,
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        WHITE,
                        LIGHT_GRAY,
                    ],
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    MID_GRAY,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(
        overview_table
    )

    story.append(
        Spacer(1, 7 * mm)
    )

    story.append(
        Paragraph(
            "Dataset Quality Summary",
            styles["section"],
        )
    )

    story.extend(
        _bullet_list(
            _build_overview_insights(dataframe),
            styles,
        )
    )

    story.append(
        Spacer(1, 4 * mm)
    )

    story.append(
        Paragraph(
            "Detected Data Types",
            styles["section"],
        )
    )

    type_data = []

    for column in dataframe.columns:
        series = dataframe[column]

        if _is_numeric(series):
            dtype = "Numeric"
        elif _try_datetime_column(series):
            dtype = "Date / Time"
        else:
            dtype = "Categorical / Text"

        type_data.append(
            {
                "Column": _clean_column_name(column),
                "Type": dtype,
                "Unique": series.nunique(
                    dropna=True
                ),
            }
        )

    story.append(
        _dataframe_table(
            pd.DataFrame(type_data),
            styles,
            max_rows=12,
            max_columns=3,
        )
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 3 — KEY METRICS
    # --------------------------------------------------------

    story.extend(
        _page_header(
            styles,
            "Key Metrics",
            "Important numeric measures selected dynamically from the uploaded dataset.",
        )
    )

    numeric_columns = _detect_numeric_columns(
        dataframe
    )

    metric_rows = []

    for column in numeric_columns[:8]:
        values = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        ).dropna()

        if values.empty:
            continue

        metric_rows.append(
            {
                "Metric": _clean_column_name(column),
                "Count": f"{len(values):,}",
                "Mean": _format_number(values.mean()),
                "Median": _format_number(values.median()),
                "Minimum": _format_number(values.min()),
                "Maximum": _format_number(values.max()),
            }
        )

    if metric_rows:
        story.append(
            _dataframe_table(
                pd.DataFrame(metric_rows),
                styles,
                max_rows=8,
                max_columns=6,
            )
        )
    else:
        story.append(
            Paragraph(
                "No numeric measures were available for metric analysis.",
                styles["body"],
            )
        )

    story.append(
        Spacer(1, 8 * mm)
    )

    story.append(
        Paragraph(
            "Metric Interpretation",
            styles["section"],
        )
    )

    story.append(
        Paragraph(
            _build_metric_insight(dataframe),
            styles["insight"],
        )
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    story.append(
        _two_chart_table(
            _create_distribution_chart(dataframe),
            _create_boxplot_chart(dataframe),
        )
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 4 — CATEGORICAL ANALYSIS
    # --------------------------------------------------------

    category = _choose_category_column(
        dataframe
    )

    story.extend(
        _page_header(
            styles,
            "Categorical Analysis",
            (
                f"Group-level analysis using "
                f"{_clean_column_name(category)}."
                if category
                else
                "Automatic category-level analysis."
            ),
        )
    )

    story.append(
        _two_chart_table(
            _create_category_chart(dataframe),
            _create_second_category_chart(dataframe),
        )
    )

    story.append(
        Spacer(1, 7 * mm)
    )

    story.append(
        Paragraph(
            "Category Insight",
            styles["section"],
        )
    )

    story.append(
        Paragraph(
            _build_category_insight(dataframe),
            styles["insight"],
        )
    )

    if category is not None:
        counts = (
            dataframe[category]
            .value_counts()
            .head(12)
        )

        category_table = pd.DataFrame(
            {
                _clean_column_name(category): counts.index,
                "Records": counts.values,
                "Share": [
                    _format_percent(
                        value / len(dataframe) * 100
                    )
                    for value in counts.values
                ],
            }
        )

        story.append(
            Spacer(1, 5 * mm)
        )

        story.append(
            _dataframe_table(
                category_table,
                styles,
                max_rows=10,
                max_columns=3,
            )
        )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 5 — DISTRIBUTION & OUTLIERS
    # --------------------------------------------------------

    numeric = _choose_primary_numeric_column(
        dataframe
    )

    story.extend(
        _page_header(
            styles,
            "Distribution & Outlier Analysis",
            (
                f"Statistical distribution of "
                f"{_clean_column_name(numeric)}."
                if numeric
                else
                "Automatic numeric distribution analysis."
            ),
        )
    )

    story.append(
        _two_chart_table(
            _create_distribution_chart(dataframe),
            _create_boxplot_chart(dataframe),
        )
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    story.append(
        Paragraph(
            "Interpretation",
            styles["section"],
        )
    )

    story.append(
        Paragraph(
            _build_distribution_insight(dataframe),
            styles["insight"],
        )
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 6 — RELATIONSHIPS
    # --------------------------------------------------------

    story.extend(
        _page_header(
            styles,
            "Relationship Analysis",
            "Exploring relationships between numeric variables.",
        )
    )

    story.append(
        _two_chart_table(
            _create_relationship_chart(dataframe),
            _create_correlation_chart(dataframe),
        )
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    story.append(
        Paragraph(
            "Relationship Insight",
            styles["section"],
        )
    )

    story.append(
        Paragraph(
            _build_relationship_insight(dataframe),
            styles["insight"],
        )
    )

    story.append(
        Spacer(1, 5 * mm)
    )

    story.append(
        Paragraph(
            "Important Note",
            styles["section"],
        )
    )

    story.append(
        Paragraph(
            "Correlation describes statistical association and does not "
            "by itself establish causation. Derived or directly related "
            "variables should be interpreted carefully.",
            styles["small"],
        )
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 7 — TIME ANALYSIS
    # --------------------------------------------------------

    time_chart = _create_time_chart(
        dataframe
    )

    story.extend(
        _page_header(
            styles,
            "Time-Based Analysis",
            "Trend analysis is included when a valid date/time field is available.",
        )
    )

    if time_chart is not None:
        story.append(
            time_chart
        )

        story.append(
            Spacer(1, 6 * mm)
        )

        story.append(
            Paragraph(
                "Time Trend Interpretation",
                styles["section"],
            )
        )

        story.append(
            Paragraph(
                _build_time_insight(dataframe),
                styles["insight"],
            )
        )

        story.append(
            Spacer(1, 8 * mm)
        )

        date_columns = _detect_date_columns(
            dataframe
        )

        if date_columns:
            story.append(
                Paragraph(
                    f"Detected date field: "
                    f"<b>{_clean_column_name(date_columns[0])}</b>",
                    styles["body"],
                )
            )
    else:
        story.append(
            _empty_chart(
                "Time-Based Analysis",
                "No suitable date/time field was detected.",
            )
        )

        story.append(
            Spacer(1, 7 * mm)
        )

        story.append(
            Paragraph(
                "Alternative Analysis",
                styles["section"],
            )
        )

        story.append(
            Paragraph(
                "Because the dataset does not contain a reliable date/time "
                "field, this report does not invent a time series. The "
                "available categorical and numeric analyses should be used "
                "instead.",
                styles["insight"],
            )
        )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 8 — ADVANCED ANALYSIS
    # --------------------------------------------------------

    story.extend(
        _page_header(
            styles,
            "Advanced Analysis",
            "Additional analytical views selected dynamically from the dataset.",
        )
    )

    story.append(
        _two_chart_table(
            _create_correlation_chart(dataframe),
            _create_boxplot_chart(dataframe),
        )
    )

    story.append(
        Spacer(1, 7 * mm)
    )

    story.append(
        Paragraph(
            "Analytical Observations",
            styles["section"],
        )
    )

    observations = [
        _build_relationship_insight(dataframe),
        _build_distribution_insight(dataframe),
        _build_category_insight(dataframe),
    ]

    story.extend(
        _bullet_list(
            observations,
            styles,
        )
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 9 — DATA QUALITY
    # --------------------------------------------------------

    story.extend(
        _page_header(
            styles,
            "Data Quality",
            "Column-level completeness, uniqueness and type checks.",
        )
    )

    quality_rows = []

    for column in dataframe.columns:
        series = dataframe[column]

        missing = int(series.isna().sum())
        unique = int(series.nunique(dropna=True))

        completeness = (
            (1 - missing / len(series)) * 100
            if len(series)
            else 0
        )

        if _is_numeric(series):
            dtype = "Numeric"
        elif _try_datetime_column(series):
            dtype = "Date / Time"
        else:
            dtype = "Categorical / Text"

        quality = (
            "Excellent"
            if completeness >= 99 and missing == 0
            else "Good"
            if completeness >= 95
            else "Review"
        )

        quality_rows.append(
            {
                "Column": _clean_column_name(column),
                "Type": dtype,
                "Missing": f"{missing:,}",
                "Unique": f"{unique:,}",
                "Completeness": _format_percent(completeness),
                "Quality": quality,
            }
        )

    story.append(
        _dataframe_table(
            pd.DataFrame(quality_rows),
            styles,
            max_rows=14,
            max_columns=6,
        )
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    health = _calculate_data_health(
        dataframe
    )

    story.append(
        Paragraph(
            f"Overall Data Health Score: "
            f"<b>{_format_percent(health)}</b>",
            styles["section"],
        )
    )

    if health >= 99:
        health_text = (
            "The dataset is highly complete with minimal quality concerns."
        )
    elif health >= 95:
        health_text = (
            "The dataset is generally healthy, with some minor quality "
            "issues that may warrant review."
        )
    else:
        health_text = (
            "The dataset contains quality issues that should be reviewed "
            "before relying on all analytical conclusions."
        )

    story.append(
        Paragraph(
            health_text,
            styles["insight"],
        )
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 10 — STATISTICAL SUMMARY
    # --------------------------------------------------------

    story.extend(
        _page_header(
            styles,
            "Statistical Summary",
            "Compact descriptive statistics for the most relevant numeric fields.",
        )
    )

    statistics_rows = []

    for column in numeric_columns[:10]:
        values = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        ).dropna()

        if values.empty:
            continue

        statistics_rows.append(
            {
                "Variable": _clean_column_name(column),
                "Count": f"{len(values):,}",
                "Mean": _format_number(values.mean()),
                "Std Dev": _format_number(values.std()),
                "Min": _format_number(values.min()),
                "25%": _format_number(values.quantile(0.25)),
                "Median": _format_number(values.median()),
                "75%": _format_number(values.quantile(0.75)),
                "Max": _format_number(values.max()),
            }
        )

    if statistics_rows:
        story.append(
            _dataframe_table(
                pd.DataFrame(statistics_rows),
                styles,
                max_rows=10,
                max_columns=9,
            )
        )
    else:
        story.append(
            Paragraph(
                "No numeric variables were available for descriptive statistics.",
                styles["body"],
            )
        )

    story.append(
        Spacer(1, 8 * mm)
    )

    story.append(
        Paragraph(
            "How to Read This Table",
            styles["section"],
        )
    )

    story.append(
        Paragraph(
            "Mean represents the arithmetic average, median represents "
            "the middle observation, standard deviation indicates "
            "dispersion, and quartiles describe the central 50% of "
            "observations.",
            styles["body"],
        )
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 11 — DATA SAMPLE
    # --------------------------------------------------------

    story.extend(
        _page_header(
            styles,
            "Dataset Sample",
            "Representative records from the uploaded dataset.",
        )
    )

    sample_columns = list(
        dataframe.columns[:8]
    )

    sample = dataframe[
        sample_columns
    ].head(10).copy()

    story.append(
        _dataframe_table(
            sample,
            styles,
            max_rows=10,
            max_columns=8,
        )
    )

    story.append(
        Spacer(1, 5 * mm)
    )

    story.append(
        Paragraph(
            f"Showing {len(sample)} sample records and "
            f"{len(sample_columns)} of {dataframe.shape[1]} columns "
            "for readability.",
            styles["small"],
        )
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    id_columns = _detect_id_like_columns(
        dataframe
    )

    if id_columns:
        story.append(
            Paragraph(
                "Potential Identifier Fields",
                styles["section"],
            )
        )

        story.extend(
            _bullet_list(
                [
                    _clean_column_name(column)
                    for column in id_columns[:8]
                ],
                styles,
            )
        )

        story.append(
            Spacer(1, 3 * mm)
        )

    story.append(
        Paragraph(
            "Dataset Handling Note",
            styles["section"],
        )
    )

    story.append(
        Paragraph(
            "The report uses the uploaded DataFrame for analysis. "
            "The sample shown here is intended for readability and "
            "does not represent the complete dataset.",
            styles["body"],
        )
    )

    story.append(PageBreak())

    # --------------------------------------------------------
    # PAGE 12 — KEY INSIGHTS & RECOMMENDATIONS
    # --------------------------------------------------------

    story.extend(
        _page_header(
            styles,
            "Key Insights & Recommendations",
            "Data-driven observations generated from the uploaded dataset.",
        )
    )

    story.append(
        Paragraph(
            "Key Insights",
            styles["section"],
        )
    )

    final_insights = [
        *_build_overview_insights(dataframe),
        _build_metric_insight(dataframe),
        _build_category_insight(dataframe),
        _build_distribution_insight(dataframe),
        _build_relationship_insight(dataframe),
    ]

    time_columns = _detect_date_columns(
        dataframe
    )

    if time_columns:
        final_insights.append(
            _build_time_insight(dataframe)
        )

    story.extend(
        _bullet_list(
            final_insights,
            styles,
        )
    )

    story.append(
        Spacer(1, 7 * mm)
    )

    story.append(
        Paragraph(
            "Recommended Actions",
            styles["section"],
        )
    )

    recommendations = [
        (
            "Review data quality issues before using the dataset "
            "for high-impact decisions."
        ),
        (
            "Investigate the strongest category-level differences "
            "identified in the report."
        ),
        (
            "Review potential outliers where they may influence "
            "averages or business conclusions."
        ),
        (
            "Use the strongest numeric relationships as areas for "
            "further investigation rather than treating correlation "
            "as proof of causation."
        ),
        (
            "Where date information is available, monitor the "
            "identified trends regularly."
        ),
    ]

    story.extend(
        _bullet_list(
            recommendations,
            styles,
        )
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    conclusion_table = Table(
        [
            [
                Paragraph(
                    "<b>DataPilot AI Assessment</b>",
                    styles["body"],
                ),
                Paragraph(
                    (
                        "This report provides an automated analytical "
                        "starting point. Business users should combine "
                        "these findings with domain knowledge before "
                        "making operational or strategic decisions."
                    ),
                    styles["body"],
                ),
            ]
        ],
        colWidths=[
            55 * mm,
            205 * mm,
        ],
    )

    conclusion_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    LIGHT_BLUE,
                ),
                (
                    "BACKGROUND",
                    (1, 0),
                    (1, 0),
                    colors.HexColor("#F8FAFC"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    MID_GRAY,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(
        conclusion_table
    )

    # --------------------------------------------------------
    # BUILD PDF
    # --------------------------------------------------------

    document.build(
        story,
        onFirstPage=_draw_footer,
        onLaterPages=_draw_footer,
    )

    buffer.seek(0)

    return buffer.getvalue()


# ============================================================
# STREAMLIT REPORT PAGE
# ============================================================

def render_report_section(dataframe: pd.DataFrame) -> None:
    """
    Render the DataPilot AI Report Center.

    The PDF generation logic remains completely separate.
    This page only provides a clean UI for:
        - explaining the report
        - showing dataset readiness
        - generating the PDF
        - downloading the generated PDF
    """

    # --------------------------------------------------------
    # PAGE HEADER
    # --------------------------------------------------------

    st.title("📄 Report Center")

    st.caption(
        "Generate a professional, automated PDF report from your uploaded dataset."
    )

    if dataframe is None or dataframe.empty:
        st.warning(
            "👈 Please upload a dataset before generating a report."
        )
        return
    # --------------------------------------------------------
    # DATASET INFORMATION
    # --------------------------------------------------------

    dataset_name = (
        st.session_state.get("uploaded_filename")
        or st.session_state.get("filename")
        or "Uploaded Dataset"
    )

    st.subheader("📊 Report Dataset")

    st.write(f"**Dataset:** `{dataset_name}`")

    st.caption(
        "Your dataset will be automatically analyzed and converted "
        "into a professional multi-page Business Intelligence report."
    )

    
    # --------------------------------------------------------
    # DATASET READINESS
    # --------------------------------------------------------

    numeric_count = len(
        _detect_numeric_columns(dataframe)
    )

    categorical_count = len(
        _detect_categorical_columns(dataframe)
    )

    date_count = len(
        _detect_date_columns(dataframe)
    )

    health = _calculate_data_health(dataframe)

    missing_count = int(
        dataframe.isna().sum().sum()
    )

    duplicate_count = int(
        dataframe.duplicated().sum()
    )

    st.subheader("📊 Dataset Readiness")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Records",
            f"{len(dataframe):,}",
        )

    with c2:
        st.metric(
            "Columns",
            f"{dataframe.shape[1]:,}",
        )

    with c3:
        st.metric(
            "Data Health",
            _format_percent(health),
        )

    with c4:
        st.metric(
            "Missing Values",
            f"{missing_count:,}",
        )

    st.caption(
        f"{numeric_count} numeric fields • "
        f"{categorical_count} categorical fields • "
        f"{date_count} date/time fields • "
        f"{duplicate_count:,} duplicate rows"
    )

    st.divider()

    # --------------------------------------------------------
    # WHAT THE REPORT GENERATES
    # --------------------------------------------------------

    st.subheader("📑 What's inside the PDF?")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            ### 📊 Executive Analysis

            ✓ Executive dashboard  
            ✓ KPI summary  
            ✓ Dataset overview  
            ✓ Key metrics  
            ✓ Business highlights
            """
        )

    with col2:
        st.markdown(
            """
            ### 📈 Visual Analytics

            ✓ Category analysis  
            ✓ Distributions  
            ✓ Outlier analysis  
            ✓ Relationships  
            ✓ Correlation analysis  
            ✓ Time trends when available
            """
        )

    with col3:
        st.markdown(
            """
            ### 🧠 Data Intelligence

            ✓ Data quality  
            ✓ Statistical analysis  
            ✓ Dataset sample  
            ✓ Automated insights  
            ✓ Recommendations  
            ✓ Dataset-specific findings
            """
        )

    st.divider()

    # --------------------------------------------------------
    # DATASET-INDEPENDENT MESSAGE
    # --------------------------------------------------------

    st.subheader("🌐 Designed for Different Datasets")

    st.markdown(
        """
        DataPilot AI automatically adapts the report to the structure
        of the uploaded dataset.

        **Sales • Employees • Students • Customers • Finance • HR •
        Marketing • Banking • Inventory • Operations • General Business**
        """
    )

    st.caption(
        "The report does not require fixed column names. "
        "Available analyses are selected automatically from the dataset."
    )

    st.divider()

    # --------------------------------------------------------
    # GENERATE REPORT
    # --------------------------------------------------------

    st.subheader("🚀 Generate Your Report")

    st.info(
        "Your PDF combines dashboard-style visuals, analytical charts, "
        "tables, data-quality checks and automated insights into a "
        "professional multi-page report."
    )

    if st.button(
        "📄 Generate Professional PDF Report",
        type="primary",
        use_container_width=True,
    ):

        with st.spinner(
            "Analyzing dataset and building your PDF report..."
        ):

            try:

                pdf_bytes = generate_report_pdf(
                    dataframe=dataframe,
                    dataset_name=dataset_name,
                )

                st.session_state[
                    "generated_report_pdf"
                ] = pdf_bytes

                st.success(
                    "✅ Your DataPilot AI report has been generated successfully."
                )

            except Exception as error:

                st.error(
                    f"❌ Report generation failed: {error}"
                )

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    pdf_bytes = st.session_state.get(
        "generated_report_pdf"
    )

    if pdf_bytes:
        st.success("✅ Report Ready")

        st.caption(
            "Your complete Business Intelligence PDF is ready to download."
        )

        st.download_button(
            label="⬇️ Download PDF Report",
            data=pdf_bytes,
            file_name="DataPilot_AI_Business_Intelligence_Report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

