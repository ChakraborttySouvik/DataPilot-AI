"""Dataset overview UI section.

Displays: first 10 rows, row/column counts, dataset size, column
names, data types, missing values, and duplicate rows.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.core.analyzer import DatasetOverview
from app.utils.formatting import format_bytes


def render_overview_section(dataframe: pd.DataFrame, overview: DatasetOverview) -> None:
    """Render the dataset overview: preview, key metrics, and quality checks.

    Args:
        dataframe: The loaded dataset.
        overview: Precomputed overview metrics for the dataset.
    """
    st.subheader("🔍 Data Overview")

    with st.container(border=True):
        st.markdown("**Preview: First 10 Rows**")
        st.dataframe(dataframe.head(10), use_container_width=True)

    st.markdown("")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Rows", f"{overview.row_count:,}")
    metric_cols[1].metric("Columns", f"{overview.column_count:,}")
    metric_cols[2].metric("Dataset Size", format_bytes(overview.size_bytes))
    metric_cols[3].metric("Duplicate Rows", f"{overview.duplicate_row_count:,}")

    with st.expander("📋 Column Names & Data Types", expanded=False):
        dtype_table = pd.DataFrame(
            {
                "Column": overview.column_names,
                "Data Type": [overview.dtypes[col] for col in overview.column_names],
            }
        )
        st.dataframe(dtype_table, use_container_width=True, hide_index=True)

    with st.expander("🧩 Missing Values", expanded=False):
        if overview.total_missing_values == 0:
            st.success("No missing values detected in this dataset.")
        else:
            missing_table = pd.DataFrame(
                {
                    "Column": list(overview.missing_values.keys()),
                    "Missing Count": list(overview.missing_values.values()),
                }
            )
            missing_table["Missing %"] = (
                missing_table["Missing Count"] / overview.row_count * 100
            ).round(2)
            missing_table = missing_table[missing_table["Missing Count"] > 0].sort_values(
                "Missing Count", ascending=False
            )
            st.warning(f"Total missing values: {overview.total_missing_values:,}")
            st.dataframe(missing_table, use_container_width=True, hide_index=True)

    with st.expander("🧬 Duplicate Rows", expanded=False):
        if overview.duplicate_row_count == 0:
            st.success("No duplicate rows detected in this dataset.")
        else:
            st.warning(
                f"Found {overview.duplicate_row_count:,} duplicate row(s) "
                f"out of {overview.row_count:,} total rows."
            )
