"""Sidebar rendering for DataPilot AI."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.core.analyzer import DatasetOverview
from app.utils.formatting import format_bytes


def render_sidebar(overview: DatasetOverview | None) -> None:
    """Render the sidebar with app info and, if available, a quick
    snapshot of the currently loaded dataset.

    Args:
        overview: The current dataset's overview metrics, or None if
            no file has been uploaded yet.
    """
    with st.sidebar:
        st.title("DataPilot AI")
        st.caption("Feature 1 · CSV Upload & Data Overview")

        st.markdown("---")
        st.markdown(
            "**What this app does:**\n"
            "- Upload a CSV file\n"
            "- Validate the file\n"
            "- Explore rows, columns & types\n"
            "- View missing values & duplicates\n"
            "- See a dataset summary\n"
            "- View basic statistics"
        )

        st.markdown("---")
        if overview is not None:
            st.subheader("Quick Snapshot")
            st.metric("Rows", f"{overview.row_count:,}")
            st.metric("Columns", f"{overview.column_count:,}")
            st.metric("Size", format_bytes(overview.size_bytes))
        else:
            st.info("Upload a CSV file to see a quick snapshot here.")
