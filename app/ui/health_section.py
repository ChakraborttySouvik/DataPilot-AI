from __future__ import annotations

import pandas as pd
import streamlit as st

from app.core.analyzer import DatasetOverview
from app.ui.components.metric_cards import metric_card
from app.utils.formatting import format_bytes


def render_health_section(
    dataframe: pd.DataFrame,
    overview: DatasetOverview,
) -> None:

    st.subheader("❤️ Dataset Health")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            title="Rows",
            value=f"{overview.row_count:,}",
            subtitle="Dataset Records",
            icon="📊",
        )

    with c2:
        metric_card(
            title="Columns",
            value=f"{overview.column_count:,}",
            subtitle="Features",
            icon="🧩",
        )

    with c3:
        metric_card(
            title="Dataset Size",
            value=format_bytes(overview.size_bytes),
            subtitle="Storage",
            icon="💾",
        )

    with c4:
        metric_card(
            title="Duplicates",
            value=f"{overview.duplicate_row_count:,}",
            subtitle="Duplicate Rows",
            icon="⚠️",
            color="#EF4444",
        )

    missing_pct = (
        overview.total_missing_values
        / (overview.row_count * overview.column_count)
        * 100
        if overview.row_count and overview.column_count
        else 0
    )

    duplicate_pct = (
        overview.duplicate_row_count
        / overview.row_count
        * 100
        if overview.row_count
        else 0
    )

    health_score = max(0, round(100 - missing_pct - duplicate_pct))

    st.markdown("### Dataset Health Score")

    if health_score >= 95:
        st.success(f"✅ Health Score: **{health_score}%** — Excellent")
    elif health_score >= 80:
        st.warning(f"🟡 Health Score: **{health_score}%** — Good")
    else:
        st.error(f"🔴 Health Score: **{health_score}%** — Needs Cleaning")