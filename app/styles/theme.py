from pathlib import Path
import streamlit as st


def load_theme():
    """Load custom CSS for DataPilot AI."""
    css_file = Path(__file__).parent / "custom.css"

    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)