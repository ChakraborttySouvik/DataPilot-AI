"""File upload UI section.

Handles rendering the uploader widget and translating validation /
loading errors into user-friendly Streamlit messages.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.core.data_loader import load_csv
from app.core.exceptions import DataPilotError
from app.core.validators import validate_uploaded_file


def render_upload_section() -> pd.DataFrame | None:
    """Render the CSV upload widget, validate, and load the file.

    Returns:
        A pandas DataFrame if a valid CSV was uploaded and loaded
        successfully; otherwise None (no file yet, or an error was
        shown to the user).
    """
    st.subheader("📤 Upload Your Dataset")
    uploaded_file = st.file_uploader(
        "Upload a CSV file to get started",
        type=["csv"],
        help="Only .csv files are supported for this feature.",
    )

    if uploaded_file is None:
        st.info("👆 Upload a CSV file above to see your data overview.")
        return None

    try:
        validate_uploaded_file(uploaded_file)
        dataframe = load_csv(uploaded_file)
    except DataPilotError as error:
        st.error(f"⚠️ {error}")
        return None
    except Exception as error:  # noqa: BLE001 - last-resort UI safety net
        st.error(f"⚠️ Something went wrong while processing the file: {error}")
        return None

    st.success(f"✅ '{uploaded_file.name}' uploaded and validated successfully.")
    return dataframe
