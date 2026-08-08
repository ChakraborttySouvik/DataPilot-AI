from __future__ import annotations

from io import StringIO

import plotly.graph_objects as go
import streamlit as st


def render_chart_download(fig: go.Figure) -> None:
    """Render chart download buttons."""

    col1, col2 = st.columns(2)

    # HTML
    html_buffer = StringIO()
    fig.write_html(html_buffer)

    with col1:
        st.download_button(
            "📥 Download HTML",
            html_buffer.getvalue(),
            file_name="chart.html",
            mime="text/html",
            use_container_width=True,
        )

    # PNG
    try:
        png = fig.to_image(format="png")

        with col2:
            st.download_button(
                "🖼 Download PNG",
                png,
                file_name="chart.png",
                mime="image/png",
                use_container_width=True,
            )

    except Exception:
        with col2:
            st.warning("Install Kaleido to enable PNG export.")