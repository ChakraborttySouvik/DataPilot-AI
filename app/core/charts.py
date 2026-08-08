"""Chart generation utilities for DataPilot AI.

All functions return Plotly Figure objects.
No Streamlit code belongs here.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
DATAPILOT_COLORS = [
    "#3B82F6",  # Blue
    "#06B6D4",  # Cyan
    "#8B5CF6",  # Purple
    "#10B981",  # Green
    "#F59E0B",  # Amber
    "#EF4444",  # Red
]


def histogram(dataframe: pd.DataFrame, column: str):
    """Create a histogram for a numeric column."""
    fig = px.histogram(
        dataframe,
        x=column,
        template="plotly_dark",
        title=f"{column} Distribution",
        color_discrete_sequence=[DATAPILOT_COLORS[0]],
    )

    fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        height=500,
    )

    return fig


def bar_chart(dataframe: pd.DataFrame, column: str):
    """Create a bar chart for a categorical column."""

    counts = dataframe[column].value_counts().reset_index()
    counts.columns = [column, "Count"]

    fig = px.bar(
        counts,
        x=column,
        y="Count",
        template="plotly_dark",
        title=f"{column} Count",
        color_discrete_sequence=[DATAPILOT_COLORS[2]],
    )

    fig.update_layout(height=500)

    return fig


def pie_chart(dataframe: pd.DataFrame, column: str):
    """Create a pie chart."""

    counts = dataframe[column].value_counts().reset_index()
    counts.columns = [column, "Count"]

    fig = px.pie(
        counts,
        names=column,
        values="Count",
        hole=0.45,
        template="plotly_dark",
        color_discrete_sequence=DATAPILOT_COLORS,
    )

    fig.update_layout(height=500)

    return fig


def box_plot(dataframe: pd.DataFrame, column: str):
    """Create a box plot."""

    fig = px.box(
        dataframe,
        y=column,
        template="plotly_dark",
        title=f"{column} Box Plot",
        color_discrete_sequence=[DATAPILOT_COLORS[3]],
    )

    fig.update_layout(height=500)

    return fig


def scatter_plot(
    dataframe: pd.DataFrame,
    x_column: str,
    y_column: str,
):
    """Create a scatter plot."""

    fig = px.scatter(
        dataframe,
        x=x_column,
        y=y_column,
        template="plotly_dark",
        title=f"{x_column} vs {y_column}",
        color_discrete_sequence=[DATAPILOT_COLORS[1]],
    )

    fig.update_layout(height=500)

    return fig


def correlation_heatmap(dataframe: pd.DataFrame):
    """Create a correlation heatmap."""

    numeric_df = dataframe.select_dtypes(include="number")

    corr = numeric_df.corr(numeric_only=True)

    fig = px.imshow(
        corr,
        text_auto=True,
        aspect="auto",
        template="plotly_dark",
        title="Correlation Heatmap",
        color_continuous_scale="Tealgrn",
    )

    fig.update_layout(height=450)

    return fig