from __future__ import annotations

import pandas as pd
import streamlit as st


def render_chart_info(
    dataframe: pd.DataFrame,
    column: str,
) -> None:
    """Display information about the selected column."""

    col1, col2, col3 = st.columns([1, 1, 1.4])

    with col1:
        st.metric(
            "Unique Values",
            dataframe[column].nunique(),
        )

    with col2:
        st.metric(
            "Missing Values",
            int(dataframe[column].isna().sum()),
        )

    # Friendly Data Type
    dtype = dataframe[column].dtype
    dtype_str = str(dtype).lower()

    if pd.api.types.is_numeric_dtype(dtype):
        dtype_name = "Numeric"

    elif pd.api.types.is_datetime64_any_dtype(dtype):
        dtype_name = "Date"

    elif pd.api.types.is_bool_dtype(dtype):
        dtype_name = "Boolean"

    elif (
        "object" in dtype_str
        or "string" in dtype_str
        or "str" == dtype_str
        or "category" in dtype_str
    ):
        dtype_name = "Category"

    else:
        dtype_name = str(dtype)

    with col3:
        st.metric(
            "Data Type",
            dtype_name,
        )

    st.divider()