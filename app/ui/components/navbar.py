from __future__ import annotations

import streamlit as st


def render_navbar() -> None:
    """Render the top navigation bar."""

    st.markdown(
        """
<div class="navbar">

<div class="nav-logo">
🧭 <span>DataPilot AI</span>
</div>

<div class="nav-links">
<span>Dashboard</span>
<span>Upload</span>
<span>Insights</span>
<span>Reports</span>
</div>

</div>
""",
        unsafe_allow_html=True,
    )