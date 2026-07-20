"""DataPilot AI - Streamlit entrypoint.

Scope (Feature 1 ONLY):
    CSV upload, validation, data overview, dataset summary, and basic
    statistics.

Explicitly OUT of scope for this file/feature:
    Dashboards, AI chat, forecasting, reports, authentication, and
    database connections. These must not be added here.

This file is intentionally thin: it only wires together the modules
under `app/core` (business logic) and `app/ui` (rendering). No
analysis or validation logic lives directly in this file.
"""

from __future__ import annotations

import streamlit as st

from app.core.analyzer import build_overview, build_statistics, build_summary
from app.ui.overview_section import render_overview_section
from app.ui.sidebar import render_sidebar
from app.ui.statistics_section import render_statistics_section
from app.ui.summary_section import render_summary_section
from app.ui.upload_section import render_upload_section


def configure_page() -> None:
    """Apply global Streamlit page configuration."""
    st.set_page_config(
        page_title="DataPilot AI",
        page_icon="🧭",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def main() -> None:
    """Run the DataPilot AI Streamlit application (Feature 1)."""
    configure_page()

    st.title("🧭 DataPilot AI")
    st.caption("AI-Powered Business Intelligence Platform — Feature 1: CSV Upload & Data Overview")
    st.markdown("---")

    dataframe = render_upload_section()

    if dataframe is None:
        render_sidebar(overview=None)
        return

    overview = build_overview(dataframe)
    summary = build_summary(dataframe)
    statistics = build_statistics(dataframe)

    render_sidebar(overview=overview)

    st.markdown("---")
    render_overview_section(dataframe, overview)

    st.markdown("---")
    render_summary_section(summary)

    st.markdown("---")
    render_statistics_section(statistics)


if __name__ == "__main__":
    main()
