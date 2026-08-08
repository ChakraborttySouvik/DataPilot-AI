from __future__ import annotations
from app.ui.components.chart_info import render_chart_info
from app.ui.components.chart_download import render_chart_download
import pandas as pd
import streamlit as st

from app.core.charts import (
    histogram,
    bar_chart,
    pie_chart,
    box_plot,
    scatter_plot,
    correlation_heatmap,
)


def render_visualizations_section(dataframe: pd.DataFrame) -> None:
    """Render interactive visualizations."""

    st.title("📊 Visualizations")
    st.caption("Explore your dataset with interactive charts.")

    numeric_columns = list(dataframe.select_dtypes(include="number").columns)
    categorical_columns = list(
        dataframe.select_dtypes(include=["object", "category"]).columns
    )

    left, right = st.columns(2)

    with left:
        chart = st.selectbox(
            "Select Chart",
            [
                "Histogram",
                "Bar Chart",
                "Pie Chart",
                "Box Plot",
                "Scatter Plot",
                "Correlation Heatmap",
            ],
        )
    

    # -----------------------------
    # Histogram
    # -----------------------------
    if chart == "Histogram":

        if not numeric_columns:
            st.warning("No numeric columns available.")
            return
        with right:
            column = st.selectbox("Select Column", numeric_columns)
            render_chart_info(
                dataframe,
                column,
            )

        fig = histogram(dataframe, column)

        st.plotly_chart(fig, use_container_width=True)
        render_chart_download(fig)

    # -----------------------------
    # Bar Chart
    # -----------------------------
    elif chart == "Bar Chart":

        if not categorical_columns:
            st.warning("No categorical columns available.")
            return
        with right:
            column = st.selectbox("Select Column", categorical_columns)
            render_chart_info(
                dataframe,
                column,
            )

        fig = bar_chart(dataframe, column)

        st.plotly_chart(fig, use_container_width=True)
        render_chart_download(fig)

    # -----------------------------
    # Pie Chart
    # -----------------------------
    elif chart == "Pie Chart":

        if not categorical_columns:
            st.warning("No categorical columns available.")
            return
        with right:
            column = st.selectbox("Select Column", categorical_columns)
            render_chart_info(
                dataframe,
                column,
            )

        fig = pie_chart(dataframe, column)

        st.plotly_chart(fig, use_container_width=True)
        render_chart_download(fig)

    # -----------------------------
    # Box Plot
    # -----------------------------
    elif chart == "Box Plot":

        if not numeric_columns:
            st.warning("No numeric columns available.")
            return
        with right:
            column = st.selectbox("Select Column", numeric_columns)
            render_chart_info(
                dataframe,
                column,
            )

        fig = box_plot(dataframe, column)

        st.plotly_chart(fig, use_container_width=True)
        render_chart_download(fig)

    # -----------------------------
    # Scatter Plot
    # -----------------------------
    elif chart == "Scatter Plot":

        if len(numeric_columns) < 2:
            st.warning("Need at least two numeric columns.")
            return

        left, middle, right = st.columns(3)

        with left:
            st.write("")  # keeps alignment with other charts

        with middle:
            x_column = st.selectbox(
                "X Axis",
                numeric_columns,
            )

        with right:
            y_column = st.selectbox(
                "Y Axis",
                numeric_columns,
                index=1 if len(numeric_columns) > 1 else 0,
            )

        fig = scatter_plot(
            dataframe,
            x_column,
            y_column,
        )

        st.plotly_chart(fig, use_container_width=True)
        render_chart_download(fig)

    # -----------------------------
# Heatmap
# -----------------------------
    elif chart == "Correlation Heatmap":

        if len(numeric_columns) < 2:
            st.warning("Need at least two numeric columns.")
            return

        st.subheader("Correlation Summary")

        st.metric(
            "Numeric Columns",
            len(numeric_columns),
        )

        st.caption(
            "Shows Pearson correlation between all numeric columns."
        )

        st.divider()

        fig = correlation_heatmap(dataframe)

        st.plotly_chart(
            fig,
            use_container_width=True,
        )
        render_chart_download(fig)