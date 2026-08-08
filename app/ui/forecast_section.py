"""Forecast UI for DataPilot AI.

This module is responsible only for rendering the forecasting page.
Forecasting business logic lives in app.core.forecasting.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from app.core.forecasting import (
    detect_date_columns,
    detect_numeric_columns,
    generate_forecast,
)


def render_forecast_section(dataframe: pd.DataFrame) -> None:
    """Render the Forecast page."""

    # ============================================================
    # Page Header
    # ============================================================

    st.title("🔮 Forecast")

    st.caption(
        "Generate simple time-series forecasts from your uploaded dataset."
    )

    st.divider()

    # ============================================================
    # Detect Columns
    # ============================================================

    date_columns = detect_date_columns(dataframe)
    numeric_columns = detect_numeric_columns(dataframe)

    # ============================================================
    # Dataset Overview
    # ============================================================

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Rows",
            f"{len(dataframe):,}",
        )

    with c2:
        st.metric(
            "Columns",
            f"{len(dataframe.columns):,}",
        )

    with c3:
        st.metric(
            "Date Columns",
            f"{len(date_columns):,}",
        )

    st.divider()

    # ============================================================
    # No Date Column
    # ============================================================

    if not date_columns:

        st.warning(
            "📅 No date/time column was detected in this dataset."
        )

        st.info(
            """
            Forecasting requires a time-based column.

            Examples:

            • Date
            • Order Date
            • Purchase Date
            • Transaction Date
            • Timestamp
            • Month
            • Year
            """
        )

        return

    # ============================================================
    # No Numeric Columns
    # ============================================================

    if not numeric_columns:

        st.warning(
            "📊 No numeric columns were detected for forecasting."
        )

        return

    # ============================================================
    # Forecast Configuration
    # ============================================================

    st.subheader("⚙️ Forecast Configuration")

    config_col1, config_col2 = st.columns(2)

    with config_col1:

        date_column = st.selectbox(
            "📅 Date Column",
            options=date_columns,
            index=0,
            key="forecast_date_column",
        )

    with config_col2:

        # Prefer business-relevant sales columns
        preferred_targets = [
            "TotalAmount",
            "Total Amount",
            "Sales",
            "Revenue",
            "Amount",
            "Profit",
            "Quantity",
            "UnitPrice",
        ]

        default_target = 0

        for preferred in preferred_targets:

            if preferred in numeric_columns:
                default_target = numeric_columns.index(preferred)
                break

        target_column = st.selectbox(
            "📊 Target Column",
            options=numeric_columns,
            index=default_target,
            key="forecast_target_column",
        )

    config_col3, config_col4 = st.columns(2)

    with config_col3:

        periods = st.number_input(
            "🔮 Forecast Periods",
            min_value=1,
            max_value=365,
            value=7,
            step=1,
            help="Number of future time periods to forecast.",
            key="forecast_periods",
        )

    with config_col4:

        method = st.selectbox(
            "🧠 Forecast Method",
            options=[
                "Moving Average",
                "Linear Trend",
            ],
            key="forecast_method",
        )

    st.divider()

    # ============================================================
    # Generate Forecast
    # ============================================================

    if st.button(
        "🚀 Generate Forecast",
        use_container_width=True,
        type="primary",
        key="generate_forecast_btn",
    ):

        with st.spinner("Analyzing historical data and generating forecast..."):

            try:

                historical, forecast = generate_forecast(
                    dataframe=dataframe,
                    date_column=date_column,
                    target_column=target_column,
                    periods=int(periods),
                    method=method,
                )

                # Store results
                st.session_state["forecast_historical"] = historical
                st.session_state["forecast_result"] = forecast
        

            except Exception as error:

                st.error(
                    f"❌ Could not generate forecast:\n\n{error}"
                )

                return

    # ============================================================
    # Read Existing Forecast
    # ============================================================

    historical = st.session_state.get(
        "forecast_historical"
    )

    forecast = st.session_state.get(
        "forecast_result"
    )

    stored_date_column = date_column
    stored_target_column = target_column
    stored_method = method

    if historical is None or forecast is None:
        return

    # ============================================================
    # Forecast Summary
    # ============================================================

    st.divider()

    st.subheader("📊 Forecast Summary")

    s1, s2, s3 = st.columns(3)

    with s1:
        st.metric(
            "Historical Records",
            f"{len(historical):,}",
        )

    with s2:
        st.metric(
            "Forecast Periods",
            f"{len(forecast):,}",
        )

    with s3:

        average_forecast = forecast[
            stored_target_column
        ].mean()

        st.metric(
            "Average Forecast",
            f"{average_forecast:,.2f}",
        )

    # ============================================================
    # Historical vs Forecast Chart
    # ============================================================

    st.subheader("📈 Historical vs Forecast")

    chart_data = historical.copy()

    chart_data[stored_date_column] = pd.to_datetime(
        chart_data[stored_date_column],
        errors="coerce",
    )

    forecast_chart = forecast.copy()

    forecast_chart[stored_date_column] = pd.to_datetime(
        forecast_chart[stored_date_column],
        errors="coerce",
    )

    fig = go.Figure()

    # Historical line
    fig.add_trace(
        go.Scatter(
            x=chart_data[stored_date_column],
            y=chart_data[stored_target_column],
            mode="lines",
            name="Historical",
            line=dict(
                width=2,
            ),
        )
    )

    # Forecast line
    fig.add_trace(
        go.Scatter(
            x=forecast_chart[stored_date_column],
            y=forecast_chart[stored_target_column],
            mode="lines+markers",
            name="Forecast",
            line=dict(
                width=3,
                dash="dash",
            ),
            marker=dict(
                size=7,
            ),
        )
    )

    fig.update_layout(
        height=500,
        margin=dict(
            l=20,
            r=20,
            t=30,
            b=20,
        ),
        xaxis_title="Date",
        yaxis_title=stored_target_column,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    # ============================================================
    # Forecast Results
    # ============================================================

    st.subheader("🔮 Forecast Results")

    display_forecast = forecast.copy()

    display_forecast[stored_date_column] = pd.to_datetime(
        display_forecast[stored_date_column]
    ).dt.strftime("%Y-%m-%d")

    display_forecast[stored_target_column] = (
        display_forecast[stored_target_column]
        .round(2)
    )

    st.dataframe(
        display_forecast,
        use_container_width=True,
        hide_index=True,
    )

    # ============================================================
    # Download
    # ============================================================

    csv_data = forecast.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "⬇️ Download Forecast CSV",
        data=csv_data,
        file_name="datapilot_forecast.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # ============================================================
    # About Forecast
    # ============================================================

    with st.expander(
        "ℹ️ About this forecast"
    ):

        if stored_method == "Moving Average":

            st.markdown(
                """
                **Moving Average**

                The forecast uses recent historical values to
                calculate the expected future value.

                This method is useful for smoothing short-term
                fluctuations and producing a simple baseline forecast.
                """
            )

        else:

            st.markdown(
                """
                **Linear Trend**

                The forecast estimates the overall historical trend
                and extends that trend into future periods.

                This method is useful when the historical data shows
                a relatively consistent upward or downward trend.
                """
            )