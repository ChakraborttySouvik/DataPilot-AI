from __future__ import annotations

import pandas as pd
import streamlit as st

from app.core.analyzer import DatasetOverview


def render_schema_section(
    dataframe: pd.DataFrame,
    overview: DatasetOverview,
) -> None:

    st.subheader("🧩 Schema Overview")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Numeric Columns",
            len(dataframe.select_dtypes(include="number").columns),
        )

    with c2:
        st.metric(
            "Categorical Columns",
            len(dataframe.select_dtypes(include="object").columns),
        )

    with c3:
        st.metric(
            "Date Columns",
            len(dataframe.select_dtypes(include="datetime").columns),
        )

    with st.expander("📋 Column Names & Data Types", expanded=True):

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

    with st.expander("🧩 Missing Values"):

        if overview.total_missing_values == 0:
            st.success("No missing values detected.")

        else:

            missing_table = pd.DataFrame(
                {
                    "Column": list(overview.missing_values.keys()),
                    "Missing Count": list(overview.missing_values.values()),
                }
            )

            missing_table["Missing %"] = (
                missing_table["Missing Count"]
                / overview.row_count
                * 100
            ).round(2)

            missing_table = missing_table[
                missing_table["Missing Count"] > 0
            ]

            st.dataframe(
                missing_table,
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("🧬 Duplicate Rows"):

        if overview.duplicate_row_count == 0:
            st.success("No duplicate rows detected.")

        else:
            st.warning(
                f"Found {overview.duplicate_row_count:,} duplicate rows."
            )