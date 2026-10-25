"""
FoodFlow Analytics Dashboard — Main Portal
File: app/Home.py

Description:
    Executive homepage for the FoodFlow analytics platform. Connects strictly
    to approved SQL views and functions, honoring the team analytics contract.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path so 'app' and 'nlq' can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from app.data_access import fetch_kpi_summary, fetch_daily_kpis
from app.components.metric_cards import render_kpi_cards
from app.components.charts import plot_daily_trend
from app.components.nlq_container import render_nlq_interface

st.set_page_config(
    page_title="FoodFlow — Food Delivery Analytics & AI Platform",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main-hero {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: white;
        padding: 2.2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 1.8rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }
    .main-hero h1 {
        color: #FFFFFF;
        font-size: 2.3rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }
    .main-hero p {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-bottom: 0;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        background: rgba(255, 82, 0, 0.15);
        color: #FF5200;
        margin-bottom: 0.6rem;
    }
</style>
<div class="main-hero">
    <span class="badge">FOODFLOW ANALYTICS PLATFORM v1.0</span>
    <h1>FoodFlow Intelligence Dashboard</h1>
    <p>Turning 2.3M+ raw food delivery records into trustworthy analytics, verified KPIs, and safe Natural Language Queries.</p>
</div>
""", unsafe_allow_html=True)

# Global Date Filter
col_f1, col_f2, col_info = st.columns([2, 2, 3])
with col_f1:
    start_date = st.date_input(
        "Start Date",
        value=pd.to_datetime("2025-01-01").date(),
        min_value=pd.to_datetime("2022-01-01").date(),
        max_value=pd.to_datetime("2025-12-31").date(),
        key="home_start_date",
    )
with col_f2:
    end_date = st.date_input(
        "End Date",
        value=pd.to_datetime("2025-12-31").date(),
        min_value=pd.to_datetime("2022-01-01").date(),
        max_value=pd.to_datetime("2025-12-31").date(),
        key="home_end_date",
    )

if start_date > end_date:
    st.error("Invalid range: Start date must be before or equal to End date.")
    st.stop()

str_start = start_date.strftime("%Y-%m-%d")
str_end = end_date.strftime("%Y-%m-%d")

# Fetch data via contract data access
kpi_df = None
daily_df = None
try:
    kpi_df = fetch_kpi_summary(str_start, str_end)
    daily_df = fetch_daily_kpis(str_start, str_end)
except Exception as e:
    st.error(f"Could not connect to database or read analytics views: {e}")
    st.info("Ensure PostgreSQL is running and you have executed the schema and analytical view scripts (see README.md).")
    st.stop()

if kpi_df is None or kpi_df.empty or kpi_df.iloc[0]["total_orders"] == 0:
    st.warning(f"No records found between {str_start} and {str_end}.")
    st.stop()

# 1. KPI Cards
st.subheader("📌 Key Business Metrics")
render_kpi_cards(kpi_df.iloc[0])

st.divider()

# 2. Daily Trends
st.subheader("📈 Order Volume & Revenue Trend")
fig = plot_daily_trend(daily_df)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# 3. Interactive Natural Language Query (NLQ) Component
render_nlq_interface()

st.divider()

# 4. Data Lineage and Governance Section
with st.expander("🔍 End-to-End Lineage & Analytics Contract Summary", expanded=False):
    st.markdown("""
    - **Contract Compliance:** All numbers above originate from `fn_kpi_summary(:start, :end)` and `v_kpi_daily`. No queries touch raw tables directly.
    - **Revenue Rule:** Qualifying Revenue is strictly calculated from orders with `order_status = 'Delivered'`. Cancelled orders (4.95%) contribute ₹0.
    - **Reconciliation:** Order `total_amount` matches `SUM(quantity * unit_price)` with 0 discrepancies across all 600,000 orders.
    - **Honesty Guarantee:** Delivery times are recorded clock hours (0-23); elapsed delivery duration and driver metrics are deliberately excluded.
    """)