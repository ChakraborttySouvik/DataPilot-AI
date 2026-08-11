from __future__ import annotations
import pandas as pd
import streamlit as st
from app.core.data_loader import load_csv
from app.core.validators import validate_uploaded_file
from app.core.exceptions import DataPilotError
from app.core.api_client import upload_dataset


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

                # ==========================================
                # Upload through FastAPI
                # ==========================================

                result = upload_dataset(
                    uploaded_file
                )

                # ==========================================
                # Store backend dataset information
                # ==========================================

                st.session_state["dataset_id"] = (
                    result["dataset_id"]
                )

                st.session_state["uploaded_filename"] = (
                    result["filename"]
                )

                # ==========================================
                # Load local DataFrame for existing UI
                # ==========================================

                uploaded_file.seek(0)

                if uploaded_file.name.lower().endswith(".csv"):

                    dataframe = pd.read_csv(
                        uploaded_file
                    )

                else:

                    dataframe = pd.read_excel(
                        uploaded_file,
                        engine="openpyxl",
                    )

                st.session_state["uploaded_df"] = dataframe

                # ==========================================
                # Success UI
                # ==========================================

                st.success(
                    "✅ Dataset loaded successfully"
                )

                st.caption(
                    result["filename"]
                )

                st.caption(
                    f"{result['rows']:,} rows • "
                    f"{result['columns']} columns"
                )

                st.caption(
                    f"Dataset ID: {result['dataset_id']}"
                )

            except Exception as error:

                st.error(
                    f"❌ Upload failed: {error}"
                )

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
                "📄 Reports",
                "⚙️ Settings",
            ),
            index=0,
            key="navigation",
        )

        st.divider()

        return page