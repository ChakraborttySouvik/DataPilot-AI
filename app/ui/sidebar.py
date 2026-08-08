from __future__ import annotations
import pandas as pd
import streamlit as st
from app.core.data_loader import load_csv
from app.core.validators import validate_uploaded_file
from app.core.exceptions import DataPilotError


def render_sidebar():
    with st.sidebar:
        
        st.markdown(
            """
<div class="sidebar-brand">
    <h2>🧭 DataPilot AI</h2>
    <p>Business Intelligence Platform</p>
</div>
""",
            unsafe_allow_html=True,
        )

        st.divider()

        st.subheader("📂 Dataset")

        uploaded_file = st.file_uploader(
            "Upload Dataset",
            type=["csv", "xlsx"],
            label_visibility="collapsed",
            help="CSV and Excel (.xlsx) files are supported.",
        )

        if uploaded_file is not None:

            try:
                validate_uploaded_file(uploaded_file)

                dataframe = load_csv(uploaded_file)

                st.session_state["uploaded_df"] = dataframe
                st.session_state["uploaded_filename"] = uploaded_file.name

                st.success("✅ Dataset Loaded")

                st.caption(uploaded_file.name)
                st.caption(
                    f"{dataframe.shape[0]:,} rows • "
                    f"{dataframe.shape[1]} columns"
                )

            except DataPilotError as error:
                st.error(str(error))

            except Exception as error:
                st.error(f"Unexpected error: {error}")

        st.divider()

        page = st.radio(
            "Navigation",
            (
                "🏠 Dashboard",
                "👀 Preview",
                "❤️ Health",
                "🧩 Schema",
                "📋 Summary",
                "📈 Statistics",
                "📊 Visualizations",
                "🧹 Data Cleaning",
                "🤖 AI Data Analyst",
                "🔮 Forecast",
                "📄 Reports (Coming Soon)",
                "⚙️ Settings (Coming Soon)",
            ),
            index=0,
            key="navigation",
        )

        st.divider()

        return page