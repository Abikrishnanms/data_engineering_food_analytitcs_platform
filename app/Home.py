import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

st.set_page_config(page_title="FoodFlow", layout="wide")
st.title("FoodFlow Dashboard")


@st.cache_resource
def get_engine():
    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("FOODFLOW_DB_USER", "postgres"),
        password=os.getenv("FOODFLOW_DB_PASSWORD", ""),
        host=os.getenv("FOODFLOW_DB_HOST", "localhost"),
        port=int(os.getenv("FOODFLOW_DB_PORT", "5432")),
        database=os.getenv("FOODFLOW_DB_NAME", "foodflow"),
    )
    return create_engine(url)


@st.cache_data(ttl=600)
def run_query(sql, params):
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


KPI_SQL = """
SELECT COUNT(*) AS total_orders,
       COUNT(*) FILTER (WHERE order_status = 'Delivered') AS delivered_orders,
       COALESCE(SUM(total_amount) FILTER (WHERE order_status = 'Delivered'), 0) AS revenue,
       COUNT(DISTINCT restaurant_id) FILTER (WHERE order_status = 'Delivered') AS active_restaurants
FROM orders
WHERE order_date BETWEEN :start AND :end
"""

TREND_SQL = """
SELECT order_date, COUNT(*) AS delivered_orders, SUM(total_amount) AS revenue
FROM orders
WHERE order_status = 'Delivered' AND order_date BETWEEN :start AND :end
GROUP BY order_date
ORDER BY order_date
"""

dates = st.date_input(
    "Date range",
    value=(pd.Timestamp("2025-01-01").date(), pd.Timestamp("2025-12-31").date()),
    min_value=pd.Timestamp("2022-01-01").date(),
    max_value=pd.Timestamp("2025-12-31").date(),
)
if len(dates) != 2:
    st.info("Pick both a start date and an end date.")
    st.stop()
params = {"start": dates[0], "end": dates[1]}

try:
    kpi = run_query(KPI_SQL, params).iloc[0]
    trend = run_query(TREND_SQL, params)
except Exception:
    st.error("Could not read from the database. Check that PostgreSQL is running and your .env settings are correct.")
    st.stop()

if kpi["total_orders"] == 0:
    st.warning(f"No orders between {dates[0]} and {dates[1]}. Try a wider date range.")
    st.stop()

aov = kpi["revenue"] / kpi["delivered_orders"] if kpi["delivered_orders"] else 0
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total orders", f"{int(kpi['total_orders']):,}")
c2.metric("Delivered orders", f"{int(kpi['delivered_orders']):,}",
          help="Orders with status Delivered. Provisional definition of a qualifying order.")
c3.metric("Delivered revenue", f"{kpi['revenue']:,.0f}",
          help="Sum of total_amount for Delivered orders. Meaning of total_amount still to be confirmed.")
c4.metric("Average order value", f"{aov:,.2f}",
          help="Delivered revenue divided by delivered orders.")

fig = px.line(trend, x="order_date", y="delivered_orders",
              title="Delivered orders per day",
              labels={"order_date": "Date", "delivered_orders": "Delivered orders"})
st.plotly_chart(fig, use_container_width=True)