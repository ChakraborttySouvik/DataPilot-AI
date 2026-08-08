from __future__ import annotations

import pandas as pd
import streamlit as st

from app.core.gemini_client import ask_gemini


def render_ai_chat(
    dataframe: pd.DataFrame,
) -> None:
    """Render the AI Data Analyst page."""

    # ======================================================
    # Page Header
    # ======================================================

    header_col1, header_col2 = st.columns([5, 1])

    with header_col1:
        st.title("🤖 AI Data Analyst")
        st.caption(
            "Ask questions about your uploaded dataset using Gemini AI."
        )

    with header_col2:
        st.write("")

        if st.button(
            "🗑 Clear Chat",
            key="clear_ai_chat_btn",
            use_container_width=True,
        ):
            st.session_state.messages = []
            st.rerun()

    # ======================================================
    # Dataset Context
    # ======================================================

    filename = st.session_state.get(
        "uploaded_filename",
        "Uploaded Dataset",
    )

    st.markdown(
        f"""
        <div style="
            padding: 12px 18px;
            margin: 8px 0 20px 0;
            border: 1px solid #334155;
            border-radius: 10px;
            background: #111827;
        ">
            <span style="font-size: 15px;">
                📂 <strong>{filename}</strong>
            </span>
            <span style="
                margin-left: 20px;
                color: #94a3b8;
            ">
                {dataframe.shape[0]:,} rows
                •
                {dataframe.shape[1]} columns
            </span>
            <span style="
                margin-left: 20px;
                color: #60a5fa;
            ">
                🟢 Gemini AI Connected
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ======================================================
    # Chat History Initialization
    # ======================================================

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ======================================================
    # Suggested Questions
    # ======================================================

    selected_question = None

    if not st.session_state.messages:

        st.subheader("💡 Try asking")

        q1, q2, q3 = st.columns(3)

        with q1:
            if st.button(
                "📊 Dataset Summary\nSummarize this dataset.",
                key="suggest_summary",
                use_container_width=True,
            ):
                selected_question = (
                    "Summarize this dataset."
                )

        with q2:
            if st.button(
                "🔍 Data Quality\nWhat are the main data quality issues?",
                key="suggest_quality",
                use_container_width=True,
            ):
                selected_question = (
                    "What are the main data quality issues?"
                )

        with q3:
            if st.button(
                "📈 Business Insight\nWhat are the most important insights?",
                key="suggest_insight",
                use_container_width=True,
            ):
                selected_question = (
                    "What are the most important insights?"
                )

        st.write("")

    # ======================================================
    # Display Chat History
    # ======================================================

    for message in st.session_state.messages:

        if message["role"] == "user":

            with st.chat_message("user"):

                st.markdown(
                    message["content"]
                )

        else:

            with st.chat_message("assistant"):

                with st.container(
                    border=True
                ):

                    st.markdown(
                        message["content"]
                    )

    # ======================================================
    # Chat Input
    # ======================================================

    question = st.chat_input(
        "Ask anything about your dataset..."
    )

    # Use suggested question if one was clicked
    if selected_question:
        question = selected_question

    if not question:
        return

    # ======================================================
    # Store User Message
    # ======================================================

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):

        st.markdown(
            question
        )
    # ==========================================
    # Prepare Full Dataset Context
    # ==========================================

    prompt = f"""
    You are DataPilot AI, an expert Business Intelligence Analyst.

    You are analyzing the user's uploaded dataset.

    DATASET INFORMATION
    -------------------
    Rows: {dataframe.shape[0]:,}
    Columns: {dataframe.shape[1]}

    Column Names:
    {', '.join(str(col) for col in dataframe.columns)}

    DATA TYPES
    ----------
    {dataframe.dtypes.to_string()}

    MISSING VALUES
    --------------
    {dataframe.isnull().sum().to_string()}

    DUPLICATE ROWS
    --------------
    {dataframe.duplicated().sum():,}

    STATISTICAL SUMMARY
    -------------------
    {dataframe.describe(include="all").to_string()}

    FULL DATASET
    ------------
    {dataframe.to_csv(index=False)}

    USER QUESTION
    -------------
    {question}

    INSTRUCTIONS
    ------------
    1. Answer the user's question using the uploaded dataset.
    2. Use the FULL dataset, not just a preview.
    3. Perform calculations when necessary.
    4. Give exact numbers whenever the dataset allows it.
    5. Do not invent information.
    6. If the requested information does not exist in the dataset, clearly say so.
    7. Explain the result in simple business language.
    8. Use bullet points or tables when useful.
    """
        

    # ==========================================
    # Gemini Response
    # ==========================================

    with st.chat_message("assistant"):

        with st.spinner("Analyzing your dataset..."):

            try:

                answer = ask_gemini(prompt)

                st.markdown(answer)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                )

            except Exception as e:

                st.error(
                    f"Gemini Error:\n\n{e}"
                )