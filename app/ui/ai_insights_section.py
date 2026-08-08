from __future__ import annotations

import streamlit as st

from app.core.insights import DatasetInsights
from app.ui.components.metric_cards import metric_card


def render_ai_insights(insights: DatasetInsights) -> None:
    """Render AI Insights dashboard."""

    st.title("🤖 AI Insights")
    st.caption("Automatically generated business insights from your dataset.")

    # ==================================================
    # Dataset Quality
    # ==================================================
    st.subheader("🟡 Dataset Quality")

    if insights.quality == "Excellent":
        st.success("🟢 Excellent Dataset")

    elif insights.quality == "Good":
        st.info("🟡 Good Dataset")

    else:
        st.warning("🟠 Needs Cleaning")

    st.divider()
    # ==================================================
    # AI Confidence
    # ==================================================

    confidence = 100

    if insights.missing_values > 0:
        confidence -= 5

    if insights.duplicate_rows > 0:
        confidence -= 5

    if insights.strongest_value < 0.50:
        confidence -= 5

    confidence = max(0, confidence)

    

    metric_card(
        "AI Confidence",
        f"{confidence}%",
        subtitle="Analysis Reliability",
        icon="🧠",
    )

    st.progress(confidence / 100)

    if confidence >= 90:
        st.success("🟢 High Confidence")

    elif confidence >= 70:
        st.info("🟡 Medium Confidence")

    else:
        st.warning("🔴 Low Confidence")

    # ==================================================
    # Dataset Overview
    # ==================================================
    st.subheader("📊 Dataset Overview")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "Rows",
            f"{insights.row_count:,}",
            icon="📄",
        )

    with c2:
        metric_card(
            "Columns",
            insights.column_count,
            icon="📚",
        )

    with c3:
        metric_card(
            "Missing",
            insights.missing_values,
            icon="⚠️",
        )

    with c4:
        metric_card(
            "Duplicates",
            insights.duplicate_rows,
            icon="📑",
        )

    st.divider()

   # ==================================================
    # Missing Columns
    # ==================================================
   

    st.subheader("⚠️ Missing Values")

    if insights.missing_columns:

        for col_name in insights.missing_columns:
            st.markdown(
                f"""
        <div style="
        display:inline-block;
        padding:10px 18px;
        margin:6px;
        border-radius:25px;
        background:#1E293B;
        border:1px solid #334155;
        font-weight:600;">
        ⚠️ {col_name}
        </div>
        """,
                unsafe_allow_html=True,
            )

    else:
        st.success("✅ No missing values detected.")
    st.divider()

    # ==================================================
    # Correlation + Average
    # ==================================================
    left, right = st.columns(2)

    with left:

        

        metric_card(
            "Strongest Correlation",
            f"{insights.strongest_value:.2f}",
            subtitle=insights.strongest_correlation,
            icon="📈",
        )

    with right:

        
        metric_card(
            "Average Value",
            f"{insights.average_value:.2f}",
            subtitle=insights.average_column,
            icon="💰",
        )

    st.divider()

    # ==================================================
    # Recommendations
    # ==================================================
    st.subheader("💡 AI Recommendations")

    for rec in insights.recommendations:
        st.success(rec)
    
    st.divider()

    st.subheader("📝 Executive Summary")

    summary = f"""
    This dataset contains **{insights.row_count:,} records** and
    **{insights.column_count} columns**.

    There are **{insights.missing_values} missing values**
    and **{insights.duplicate_rows} duplicate rows**.

    The strongest relationship is between
    **{insights.strongest_correlation}**
    with a correlation coefficient of
    **{insights.strongest_value:.2f}**.

    Overall, the dataset quality is
    **{insights.quality}** and is suitable
    for further analysis after applying the
    recommended preprocessing steps.
    """

    with st.container(border=True):
        st.markdown(summary)