from __future__ import annotations

import streamlit as st


def metric_card(
    title: str,
    value: str,
    color: str = "#3B82F6",
    subtitle: str = "",
    icon: str = "📊",
    progress: float | None = None,
    status: str = "",
) -> None:

    with st.container(border=True):

        st.markdown(
            f"""
### {icon} {title}

<span style="font-size:40px;font-weight:700;color:{color};">{value}</span>

<div style="color:#9CA3AF;font-size:14px;">
{subtitle}
</div>
""",
            unsafe_allow_html=True,
        )

        if progress is not None:
            st.progress(progress)

        if status:
            st.caption(status)