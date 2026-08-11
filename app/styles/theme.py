import streamlit as st


def load_theme(theme: str = "Dark") -> None:
    """Load DataPilot AI application theme."""

    if theme == "Light":
        st.markdown(
            """
            <style>

            /* Main application */
            .stApp {
                background-color: #F5F7FA;
                color: #172033;
            }

            /* Main content */
            .main {
                background-color: #F5F7FA;
            }

            /* Sidebar */
            section[data-testid="stSidebar"] {
                background-color: #FFFFFF;
                border-right: 1px solid #D9E0EA;
            }

            section[data-testid="stSidebar"] * {
                color: #172033 !important;
            }

            /* Headings */
            h1, h2, h3, h4 {
                color: #172033 !important;
            }

            /* Normal text */
            p, label, span {
                color: #344054;
            }

            /* Cards */
            div[data-testid="stMetric"] {
                background-color: #FFFFFF;
                border: 1px solid #D9E0EA;
                border-radius: 14px;
                padding: 18px;
            }

            /* Inputs */
            div[data-baseweb="select"] > div,
            div[data-baseweb="input"] > div {
                background-color: #FFFFFF;
                color: #172033;
                border-color: #CBD5E1;
            }

            /* Buttons */
            .stButton > button {
                background-color: #2563EB;
                color: white !important;
                border: none;
                border-radius: 10px;
            }

            /* Dataframes */
            div[data-testid="stDataFrame"] {
                background-color: #FFFFFF;
            }

            </style>
            """,
            unsafe_allow_html=True,
        )

    else:
        st.markdown(
            """
            <style>

            .stApp {
                background-color: #0B1220;
                color: #F8FAFC;
            }

            .main {
                background-color: #0B1220;
            }

            section[data-testid="stSidebar"] {
                background-color: #111827;
                border-right: 1px solid #263244;
            }

            section[data-testid="stSidebar"] * {
                color: #F8FAFC !important;
            }

            h1, h2, h3, h4 {
                color: #F8FAFC !important;
            }

            p, label, span {
                color: #CBD5E1;
            }

            div[data-testid="stMetric"] {
                background-color: #111827;
                border: 1px solid #263244;
                border-radius: 14px;
                padding: 18px;
            }

            div[data-baseweb="select"] > div,
            div[data-baseweb="input"] > div {
                background-color: #1F2937;
                color: #F8FAFC;
                border-color: #374151;
            }

            .stButton > button {
                background-color: #2563EB;
                color: white !important;
                border: none;
                border-radius: 10px;
            }

            </style>
            """,
            unsafe_allow_html=True,
        )