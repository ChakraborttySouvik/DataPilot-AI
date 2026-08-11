"""DataPilot AI - Settings page."""

import streamlit as st


def render_settings_section() -> None:
    """Render application settings and preferences."""

    st.title("⚙️ Settings")
    st.caption(
        "Customize DataPilot AI preferences for your dashboard and reports."
    )

    st.markdown("---")

    # ============================================================
    # Appearance
    # ============================================================
    st.subheader("🎨 Appearance")

    col1, col2 = st.columns(2)

    with col1:
        current_theme = st.session_state.get("app_theme", "Dark")

        theme = st.selectbox(
            "Interface Theme",
            ["Dark", "Light"],
            index=["Dark", "Light"].index(current_theme),
            key="settings_theme",
        )

    with col2:
        density = st.selectbox(
            "Dashboard Density",
            ["Comfortable", "Compact"],
            index=0,
            key="settings_density",
        )

    st.markdown("---")

    # ============================================================
    # Dashboard Preferences
    # ============================================================
    st.subheader("📊 Dashboard Preferences")

    col1, col2 = st.columns(2)

    with col1:
        show_kpis = st.checkbox(
            "Show KPI cards",
            value=True,
            key="settings_show_kpis",
        )

        show_charts = st.checkbox(
            "Show analytical charts",
            value=True,
            key="settings_show_charts",
        )

    with col2:
        show_insights = st.checkbox(
            "Show business insights",
            value=True,
            key="settings_show_insights",
        )

        show_data_quality = st.checkbox(
            "Show data-quality indicators",
            value=True,
            key="settings_show_quality",
        )

    st.markdown("---")

    # ============================================================
    # Report Preferences
    # ============================================================
    st.subheader("📄 Report Preferences")

    report_title = st.text_input(
        "Report Title",
        value="DataPilot AI Business Intelligence Report",
        key="settings_report_title",
    )

    col1, col2 = st.columns(2)

    with col1:
        include_dashboard = st.checkbox(
            "Include dashboard overview",
            value=True,
            key="settings_report_dashboard",
        )

        include_visuals = st.checkbox(
            "Include charts & visualizations",
            value=True,
            key="settings_report_visuals",
        )

        include_tables = st.checkbox(
            "Include analytical tables",
            value=True,
            key="settings_report_tables",
        )

    with col2:
        include_insights = st.checkbox(
            "Include automated insights",
            value=True,
            key="settings_report_insights",
        )

        include_quality = st.checkbox(
            "Include data-quality analysis",
            value=True,
            key="settings_report_quality",
        )

        include_recommendations = st.checkbox(
            "Include recommendations",
            value=True,
            key="settings_report_recommendations",
        )

    st.markdown("---")

    # ============================================================
    # Session / Dataset
    # ============================================================
    st.subheader("🔄 Session")

    st.write(
        "Reset the current application session if you want to start "
        "with a fresh dataset."
    )

    if st.button(
        "🗑️ Reset Current Session",
        use_container_width=False,
        type="secondary",
        key="reset_session_button",
    ):
        keys_to_remove = [
            "uploaded_df",
            "dataset_id",
            "api_overview",
            "report_pdf",
        ]

        for key in keys_to_remove:
            st.session_state.pop(key, None)

        st.success("✅ Current session has been reset.")
        st.rerun()

    st.markdown("---")

    # ============================================================
    # Save Settings
    # ============================================================
    if st.button(
        "💾 Save Preferences",
        type="primary",
        use_container_width=True,
        key="save_settings_button",
    ):
        st.session_state["app_theme"] = theme

        st.session_state["app_settings"] = {
            "theme": theme,
            "density": density,
            "show_kpis": show_kpis,
            "show_charts": show_charts,
            "show_insights": show_insights,
            "show_data_quality": show_data_quality,
            "report_title": report_title,
            "include_dashboard": include_dashboard,
            "include_visuals": include_visuals,
            "include_tables": include_tables,
            "include_insights": include_insights,
            "include_quality": include_quality,
            "include_recommendations": include_recommendations,
        }

        st.success("✅ Preferences saved successfully.")

        st.rerun()
    # ============================================================
    # About
    # ============================================================
    st.markdown("---")

    st.subheader("ℹ️ About DataPilot AI")

    st.markdown(
        """
        **DataPilot AI**

        An AI-powered Business Intelligence platform for exploring,
        analyzing, visualizing, cleaning, and reporting structured datasets.

        **Core capabilities**
        - 📊 Interactive business dashboards
        - 🔍 Dataset exploration
        - ❤️ Data-quality analysis
        - 📈 Statistical analysis
        - 📊 Visual analytics
        - 🧹 Data cleaning
        - 🤖 AI-powered analysis
        - 📄 Automated PDF business reports
        """
    )

    st.caption("DataPilot AI • Business Intelligence Platform")