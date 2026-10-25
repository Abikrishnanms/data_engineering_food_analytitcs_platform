"""
FoodFlow Dashboard — Executive Overview Page
File: app/pages/1_📊_Overview.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
from app.data_access import fetch_kpi_summary, fetch_daily_kpis, fetch_payment_mix, fetch_status_mix
from app.components.metric_cards import render_kpi_cards
from app.components.charts import plot_daily_trend, plot_payment_mix

st.set_page_config(page_title="Executive Overview — FoodFlow", page_icon="📊", layout="wide")

st.title("📊 Executive Overview & Order Trends")
st.markdown("Monitor high-level business performance, qualifying revenue, and order trends across selected periods.")

# Date filter
col_date1, col_date2, col_preset = st.columns([2, 2, 3])
with col_date1:
    start_date = st.date_input("Start date", value=pd.to_datetime("2025-01-01").date(),
                               min_value=pd.to_datetime("2022-01-01").date(),
                               max_value=pd.to_datetime("2025-12-31").date())
with col_date2:
    end_date = st.date_input("End date", value=pd.to_datetime("2025-12-31").date(),
                             min_value=pd.to_datetime("2022-01-01").date(),
                             max_value=pd.to_datetime("2025-12-31").date())

if start_date > end_date:
    st.error("Error: Start date cannot be after end date.")
    st.stop()

str_start = start_date.strftime("%Y-%m-%d")
str_end = end_date.strftime("%Y-%m-%d")

try:
    kpi_df = fetch_kpi_summary(str_start, str_end)
    daily_df = fetch_daily_kpis(str_start, str_end)
    payment_df = fetch_payment_mix()
except Exception as e:
    st.error(f"Could not connect to PostgreSQL analytics views. Please verify database is loaded. Details: {e}")
    st.stop()

if kpi_df.empty or kpi_df.iloc[0]["total_orders"] == 0:
    st.warning(f"No order records found between {str_start} and {str_end}.")
    st.stop()

# Render KPI cards
st.markdown("### Key Performance Indicators")
render_kpi_cards(kpi_df.iloc[0])

st.divider()

# Daily trend
st.markdown("### Daily Delivery & Revenue Performance")
trend_fig = plot_daily_trend(daily_df)
st.plotly_chart(trend_fig, use_container_width=True)

st.divider()

# Breakdown columns
col_c1, col_c2 = st.columns(2)
with col_c1:
    st.markdown("### Payment Methods Breakdown")
    pay_fig = plot_payment_mix(payment_df)
    st.plotly_chart(pay_fig, use_container_width=True)

with col_c2:
    st.markdown("### Delivery vs Cancellation Ratio")
    status_df = fetch_status_mix()
    if not status_df.empty:
        status_summary = status_df.groupby("order_status")["orders"].sum().reset_index()
        delivered = int(status_summary.loc[status_summary["order_status"] == "Delivered", "orders"].sum())
        cancelled = int(status_summary.loc[status_summary["order_status"] == "Cancelled", "orders"].sum())
        total = delivered + cancelled

        display_df = status_summary.rename(columns={"order_status": "Status", "orders": "Total Orders"})
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )
        if total > 0:
            st.info(f"Across the full dataset: **{delivered:,}** Delivered ({delivered/total*100:.2f}%) vs **{cancelled:,}** Cancelled ({cancelled/total*100:.2f}%).")
