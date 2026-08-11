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
from app.ui.settings_section import render_settings_section
from app.styles.theme import load_theme
from app.ui.components.hero import render_hero
from app.ui.forecast_section import render_forecast_section
from app.core.analyzer import  build_statistics, build_summary
from app.ui.sidebar import render_sidebar
from app.ui.overview_section import render_overview_section
from app.ui.statistics_section import render_statistics_section
from app.ui.summary_section import render_summary_section
from app.ui.preview_section import render_preview_section
from app.ui.reports_section import render_report_section
from app.ui.health_section import render_health_section
from app.ui.schema_section import render_schema_section
from app.ui.dashboard_section import render_dashboard
from app.ui.visualizations_section import render_visualizations_section
from app.core.api_client import get_dataset_overview
from app.ui.data_cleaning_section import render_data_cleaning


def configure_page() -> None:
    """Apply global Streamlit page configuration."""
    st.set_page_config(
        page_title="DataPilot AI",
        page_icon="🧭",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def main():
    configure_page()

    # Apply saved application theme
    current_theme = st.session_state.get("app_theme", "Dark")
    load_theme(current_theme)

    # Sidebar Navigation
    page = render_sidebar()

    # Show Hero only on Dashboard
    if page == "🏠 Dashboard":
        render_hero()

    # Get uploaded dataset from sidebar
    dataframe = st.session_state.get("uploaded_df")

    if dataframe is None:
        st.info("👈 Upload a CSV file from the sidebar to continue.")
        return

    # Build Analytics
    dataset_id = st.session_state.get("dataset_id")

    if not dataset_id:
        st.error(
            "❌ Dataset ID not found. Please upload the dataset again."
        )
        return

    try:

        overview = get_dataset_overview(
            dataset_id
        )

        st.session_state["api_overview"] = overview

    except Exception as error:

        st.error(
            f"❌ FastAPI analysis failed: {error}"
        )
        return

    # Keep these local for now.
    # We will migrate them next.
    summary = build_summary(dataframe)
    statistics = build_statistics(dataframe)

   # ==============================
    # Dashboard
    # ==============================
    if page == "🏠 Dashboard":

        render_dashboard(
            dataframe=dataframe,
            overview=overview,
            summary=summary,
            statistics=statistics,
        )
    # ==============================
    # Preview
    # ==============================
    elif page == "👀 Preview":

       render_preview_section(dataframe)
    # ==============================
    # Health
    # ==============================
    elif page == "❤️ Health":

        render_health_section(
            dataframe,
            overview,
        )
    # ==============================
    # Schema
    # ==============================
    elif page == "🧩 Schema":

        render_schema_section(
            dataframe,
            overview,
        )
    # ==============================
    # Summary
    # ==============================
    elif page == "📋 Summary":

        st.subheader("📋 Dataset Summary")

        render_summary_section(summary)

    # ==============================
    # Statistics
    # ==============================
    elif page == "📈 Statistics":

        st.subheader("📈 Statistical Summary")

        render_statistics_section(statistics)
    #================================
    # Visualizations
    #================================
    
    elif page == "📊 Visualizations":

        render_visualizations_section(dataframe)
    #====================
    #Data cleaning
    #===================
    elif page == "🧹 Data Cleaning":
        render_data_cleaning(dataframe)

    # ==============================
    # Future Features
    # ==============================
    elif page == "🤖 AI Data Analyst":
        from app.ui.ai_chat_section import render_ai_chat
        render_ai_chat(dataframe)

    elif page == "🔮 Forecast":

        render_forecast_section(dataframe)

    elif page == "📄 Reports":
        render_report_section(dataframe)

    elif page == "⚙️ Settings":

        render_settings_section()


if __name__ == "__main__":
    main()