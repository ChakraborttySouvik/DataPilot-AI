from __future__ import annotations

import pandas as pd
import streamlit as st


def render_preview_section(dataframe: pd.DataFrame) -> None:
    """Render dataset preview."""

    st.subheader("👀 Dataset Preview")

    st.caption(
        f"Showing first **10** rows of **{len(dataframe):,}** records."
    )

    with st.container(border=True):
        st.dataframe(
            dataframe.head(10),
            use_container_width=True,
        )