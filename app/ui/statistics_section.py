"""Basic statistics UI section, powered by `pandas.DataFrame.describe()`."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_statistics_section(statistics: pd.DataFrame) -> None:
    """Render descriptive statistics for the dataset.

    Args:
        statistics: Output of `analyzer.build_statistics`, i.e. a
            transposed `describe(include="all")` table.
    """
    st.subheader("📈 Basic Statistics")

    with st.container(border=True):
        st.caption("Generated with pandas `describe(include='all')`")
        st.dataframe(statistics, use_container_width=True)
