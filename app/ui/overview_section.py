"""Dataset overview UI section.

Displays: first 10 rows, row/column counts, dataset size, column
names, data types, missing values, and duplicate rows.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.core.analyzer import DatasetOverview
from app.utils.formatting import format_bytes


def render_overview_section(
    dataframe: pd.DataFrame,
    overview: DatasetOverview,
    section: str | None = None,
) -> None:
    """Render the dataset overview: preview, key metrics, and quality checks."""

    st.subheader("🔍 Data Overview")

    st.caption(
        f"Showing first **10** rows of **{overview.row_count:,}** records."
    )

    # -----------------------------
    # Dataset Preview
    # -----------------------------
    with st.container(border=True):
        st.markdown("### 📋 Dataset Preview")
        st.dataframe(dataframe.head(10), use_container_width=True)

    st.markdown("")

   # -----------------------------
# KPI Cards
# -----------------------------
    from app.ui.components.metric_cards import metric_card

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            title="Rows",
            value=f"{overview.row_count:,}",
            subtitle="Dataset Records",
            icon="📊",
        )

    with c2:
        metric_card(
            title="Columns",
            value=f"{overview.column_count:,}",
            subtitle="Features",
            icon="🧩",
        )

    with c3:
        metric_card(
            title="Dataset Size",
            value=format_bytes(overview.size_bytes),
            subtitle="Storage",
            icon="💾",
        )

    with c4:
        metric_card(
            title="Duplicates",
            value=f"{overview.duplicate_row_count:,}",
            color="#EF4444",
            subtitle="Duplicate Rows",
            icon="⚠️",
        )

    # -----------------------------
    # Dataset Health Score
    # -----------------------------
    missing_pct = (
        overview.total_missing_values
        / (overview.row_count * overview.column_count)
        * 100
        if overview.row_count and overview.column_count
        else 0
    )

    duplicate_pct = (
        overview.duplicate_row_count / overview.row_count * 100
        if overview.row_count
        else 0
    )

    health_score = max(0, round(100 - missing_pct - duplicate_pct))

    st.markdown("### 📈 Dataset Health")

    if health_score >= 95:
        st.success(f"✅ Health Score: **{health_score}%** — Excellent")
    elif health_score >= 80:
        st.warning(f"🟡 Health Score: **{health_score}%** — Good")
    else:
        st.error(f"🔴 Health Score: **{health_score}%** — Needs Cleaning")

    # -----------------------------
    # Column Summary
    # -----------------------------
    st.markdown("### 📊 Schema Overview")

    s1, s2, s3 = st.columns(3)

    with s1:
        st.metric(
            "Numeric Columns",
            len(dataframe.select_dtypes(include="number").columns),
        )

    with s2:
        st.metric(
            "Categorical Columns",
            len(dataframe.select_dtypes(include="object").columns),
        )

    with s3:
        st.metric(
            "Date Columns",
            len(dataframe.select_dtypes(include="datetime").columns),
        )

    # -----------------------------
    # Data Types
    # -----------------------------
    with st.expander("📋 Column Names & Data Types"):

        dtype_table = pd.DataFrame(
            {
                "Column": overview.column_names,
                "Data Type": [
                    overview.dtypes[col]
                    for col in overview.column_names
                ],
            }
        )

        st.dataframe(
            dtype_table,
            use_container_width=True,
            hide_index=True,
        )

    # -----------------------------
    # Missing Values
    # -----------------------------
    with st.expander("🧩 Missing Values"):

        if overview.total_missing_values == 0:
            st.success("No missing values detected in this dataset.")

        else:
            missing_table = pd.DataFrame(
                {
                    "Column": list(overview.missing_values.keys()),
                    "Missing Count": list(
                        overview.missing_values.values()
                    ),
                }
            )

            missing_table["Missing %"] = (
                missing_table["Missing Count"]
                / overview.row_count
                * 100
            ).round(2)

            missing_table = missing_table[
                missing_table["Missing Count"] > 0
            ].sort_values(
                "Missing Count",
                ascending=False,
            )

            st.warning(
                f"Total missing values: {overview.total_missing_values:,}"
            )

            st.dataframe(
                missing_table,
                use_container_width=True,
                hide_index=True,
            )

    # -----------------------------
    # Duplicate Rows
    # -----------------------------
    with st.expander("🧬 Duplicate Rows"):

        if overview.duplicate_row_count == 0:
            st.success("No duplicate rows detected in this dataset.")

        else:
            st.warning(
                f"Found {overview.duplicate_row_count:,} duplicate row(s) "
                f"out of {overview.row_count:,} total rows."
            )