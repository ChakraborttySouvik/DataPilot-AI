from __future__ import annotations

import streamlit as st


def render_hero() -> None:
    st.markdown(
        """
<div class="hero">

<div class="hero-badge">
AI-Powered Business Intelligence
</div>

<h1>DataPilot AI</h1>

<p>
Upload • Analyze • Visualize • Generate Insights
</p>

</div>
""",
        unsafe_allow_html=True,
    )