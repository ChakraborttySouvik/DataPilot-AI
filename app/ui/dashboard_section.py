from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from app.core.charts import (
    correlation_heatmap,
)

from app.core.analyzer import DatasetOverview, DatasetSummary
from app.ui.components.metric_cards import metric_card


def format_size(size_bytes: int) -> str:
    """Convert bytes to KB/MB."""

    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.2f} KB"

    return f"{size_bytes / (1024 ** 2):.2f} MB"


def render_dashboard(
    dataframe: pd.DataFrame,
    overview: DatasetOverview,
    summary: DatasetSummary,
    statistics: pd.DataFrame,
) -> None:

    st.title("🏠 Dashboard")
    st.caption("Quick overview of your uploaded dataset.")

    # ======================
    # KPI Cards
    # ======================

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "Rows",
            overview.row_count,
            icon="📄",
        )

    with c2:
        metric_card(
            "Columns",
            overview.column_count,
            icon="📊",
        )

    with c3:
        metric_card(
            "Dataset Size",
            format_size(overview.size_bytes),
            icon="💾",
        )

    with c4:

        score = 100

        missing_ratio= (
            overview.total_missing_values/
            (overview.row_count * overview.column_count)
        )
        score -= int(missing_ratio * 100)
        
        if overview.duplicate_row_count > 0:
            score -= min(20, overview.duplicate_row_count)
        score = max(0, min(score, 100))

    

        if score >= 90:
            status = "🟢 Excellent Dataset"
        elif score >= 70:
            status = "🟡 Good Dataset"
        elif score >= 50:
            status = "🟠 Needs Cleaning"
        else:
            status = "🔴 Poor Dataset"

        metric_card(
            title="Health Score",
            value=f"{score}%",
            icon="❤️",
            progress=score / 100,
            status=status,
        )

    # ======================
    # Dataset Summary
    # ======================

    st.subheader("📋 Dataset Summary")

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Numeric Columns",
            len(summary.numeric_columns),
        )

        st.metric(
            "Categorical Columns",
            len(summary.categorical_columns),
        )

    with col2:

        st.metric(
            "Date Columns",
            len(summary.date_columns),
        )

        st.metric(
            "Memory Usage",
            format_size(summary.memory_usage_bytes),
        )

    st.divider()
    # ======================
    # Dashboard Analytics
    # ======================

    st.subheader("📈 Dashboard Analytics")

    numeric = dataframe.select_dtypes(include="number").columns.tolist()
    ignore = ["id", "customer id", "customer_id", "index"]
    numeric = [
        col for col in numeric
        if col.lower() not in ignore
    ]
    categorical = dataframe.select_dtypes(
        include=["object", "category"]
    ).columns
    # ======================
    # Dashboard Filters
    # ======================

    category_col = st.selectbox(
        "Category Column",
        categorical,
        key="dashboard_category",
    )


    # ----------------------
    # First Row
    # ----------------------

    left, right = st.columns(2)
    with left:
        x_col = st.selectbox(
            "X-Axis",
            dataframe.columns,
            key="dashboard_x"
        )
    with right:
        y_col = st.selectbox(
            "Y-Axis",
            numeric,
            key="dashboard_y"
        )

    # Trend
    with left:

        if numeric:

            fig = px.line(
                dataframe,
                x=x_col,
                y=y_col,
                template="plotly_dark",
                title=f"{y_col} Trend",
                color_discrete_sequence=["#3B82F6"],
            )
            fig.update_traces(
                line=dict(width=4)
            )
            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title=y_col,
                hovermode="x unified",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    # Pie
    with right:

        if len(categorical):

            counts = (
                dataframe[category_col]
                .value_counts()
                .head(6)
            )

            fig = px.pie(
                names=counts.index,
                values=counts.values,
                hole=0.45,
                template="plotly_dark",
                title=f"{category_col} Distribution",
                color_discrete_sequence=[
                    "#3B82F6",
                    "#06B6D4",
                    "#8B5CF6",
                    "#10B981",
                    "#F59E0B",
                    "#EF4444",
                ],
            )
            fig.update_traces(
                textposition="inside",
                textinfo="percent+label",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    # ----------------------
    # Second Row
    # ----------------------

    left, right = st.columns(2)

    # Top Categories
    with left:

        if len(categorical):

            counts = (
                dataframe[category_col]
                .value_counts()
                .head(10)
            )

            fig = px.bar(
                x=counts.index,
                y=counts.values,
                template="plotly_dark",
                title=f"Top 10 {category_col}",
                color_discrete_sequence=["#8B5CF6"],
            )
            fig.update_layout(
                xaxis_title="",
                yaxis_title="Count",
            )

            fig.update_traces(
                marker_line_width=0
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    # Heatmap
    with right:

        if len(numeric) >= 2:

            fig = correlation_heatmap(dataframe)
            

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    st.divider()

    # ======================
    # Preview
    # ======================

    st.subheader("👀 Dataset Preview")

    st.dataframe(
        dataframe.head(10),
        use_container_width=True,
        hide_index=True,
        height=350,
    )

    st.divider()

    # ======================
    # Quick Statistics
    # ======================

    st.subheader("📈 Quick Statistics")

    st.dataframe(
        statistics.head(),
        use_container_width=True,
    )