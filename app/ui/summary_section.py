"""Dataset summary UI section.

Displays: numeric columns, categorical columns, date columns
(auto-detected), and memory usage.
"""

from __future__ import annotations

import streamlit as st

from app.core.analyzer import DatasetSummary
from app.utils.formatting import format_bytes


def render_summary_section(summary: DatasetSummary) -> None:
    """Render the dataset summary: column-type breakdown and memory usage.

    Args:
        summary: Precomputed column-type classification and memory usage.
    """
    st.subheader("📊 Dataset Summary")

    with st.container(border=True):
        metric_cols = st.columns(4)
        metric_cols[0].metric("Numeric Columns", len(summary.numeric_columns))
        metric_cols[1].metric("Categorical Columns", len(summary.categorical_columns))
        metric_cols[2].metric("Date Columns", len(summary.date_columns))
        metric_cols[3].metric("Memory Usage", format_bytes(summary.memory_usage_bytes))

        with st.expander("🔢 Numeric Columns", expanded=False):
            _render_column_list(summary.numeric_columns)

        with st.expander("🏷️ Categorical Columns", expanded=False):
            _render_column_list(summary.categorical_columns)

        with st.expander("📅 Date Columns (auto-detected)", expanded=False):
            _render_column_list(summary.date_columns)


def _render_column_list(columns: list[str]) -> None:
    """Render a bullet list of column names, or a fallback message.

    Args:
        columns: Column names to display.
    """
    if not columns:
        st.caption("None detected.")
        return
    st.markdown("\n".join(f"- {col}" for col in columns))
