"""
FoodFlow Analytics Data Access Layer
File: app/data_access.py

Description:
    Centralized, cached database query interface for the Streamlit dashboard.
    Strictly reads from approved PostgreSQL views and functions (fn_kpi_summary,
    v_kpi_daily, fn_top_restaurants, etc.). Never queries raw tables directly.
"""

import os
from pathlib import Path
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@st.cache_resource
def get_engine():
    """Create and cache SQLAlchemy connection engine."""
    user = os.getenv("FOODFLOW_ANALYTICS_USER") or os.getenv("FOODFLOW_DB_USER", "postgres")
    password = os.getenv("FOODFLOW_ANALYTICS_PASSWORD") or os.getenv("FOODFLOW_DB_PASSWORD", "")
    host = os.getenv("FOODFLOW_DB_HOST") or os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("FOODFLOW_DB_PORT") or os.getenv("DB_PORT", "5432"))
    database = os.getenv("FOODFLOW_DB_NAME") or os.getenv("DB_NAME", "foodflow")

    url = URL.create(
        "postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )
    return create_engine(url, pool_pre_ping=True)


@st.cache_data(ttl=600)
def fetch_kpi_summary(start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch aggregated KPIs for an arbitrary date range via fn_kpi_summary."""
    query = "SELECT * FROM fn_kpi_summary(CAST(:start AS date), CAST(:end AS date));"
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn, params={"start": str(start_date), "end": str(end_date)})


@st.cache_data(ttl=600)
def fetch_daily_kpis(start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch daily time-series metrics from v_kpi_daily."""
    query = """
        SELECT order_date, total_orders, qualifying_orders, cancelled_orders,
               qualifying_revenue, avg_order_value, cancellation_rate
        FROM v_kpi_daily
        WHERE order_date BETWEEN CAST(:start AS date) AND CAST(:end AS date)
        ORDER BY order_date;
    """
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn, params={"start": str(start_date), "end": str(end_date)})


@st.cache_data(ttl=600)
def fetch_top_restaurants(start_date: str, end_date: str, limit: int = 5) -> pd.DataFrame:
    """Fetch top restaurants by qualifying revenue via fn_top_restaurants."""
    query = "SELECT * FROM fn_top_restaurants(CAST(:start AS date), CAST(:end AS date), CAST(:limit AS int));"
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn, params={"start": str(start_date), "end": str(end_date), "limit": int(limit)})


@st.cache_data(ttl=600)
def fetch_top_items(start_date: str, end_date: str, limit: int = 10) -> pd.DataFrame:
    """Fetch top menu items by units sold via fn_top_items."""
    query = "SELECT * FROM fn_top_items(CAST(:start AS date), CAST(:end AS date), CAST(:limit AS int));"
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn, params={"start": str(start_date), "end": str(end_date), "limit": int(limit)})


@st.cache_data(ttl=600)
def fetch_status_mix() -> pd.DataFrame:
    """Fetch monthly order status breakdown from v_q04_status_mix_monthly."""
    query = """
        SELECT order_month, order_status, orders, share_of_orders
        FROM v_q04_status_mix_monthly
        ORDER BY order_month, order_status;
    """
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn)


@st.cache_data(ttl=600)
def fetch_cuisine_mix() -> pd.DataFrame:
    """Fetch cuisine revenue share from v_q07_cuisine_mix_monthly."""
    query = """
        SELECT cuisine, SUM(qualifying_revenue) AS total_revenue,
               SUM(qualifying_orders) AS total_orders
        FROM v_q07_cuisine_mix_monthly
        GROUP BY cuisine
        ORDER BY total_revenue DESC
        LIMIT 10;
    """
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn)


@st.cache_data(ttl=600)
def fetch_payment_mix() -> pd.DataFrame:
    """Fetch payment method distribution from v_q08_payment_mix_monthly."""
    query = """
        SELECT payment_method, SUM(total_orders) AS total_orders
        FROM v_q08_payment_mix_monthly
        GROUP BY payment_method
        ORDER BY total_orders DESC;
    """
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn)


@st.cache_data(ttl=600)
def fetch_hourly_orders() -> pd.DataFrame:
    """Fetch order volume by recorded clock hour from v_q09_orders_by_recorded_hour."""
    query = """
        SELECT recorded_hour, total_orders, qualifying_orders
        FROM v_q09_orders_by_recorded_hour
        ORDER BY recorded_hour;
    """
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn)


@st.cache_data(ttl=600)
def fetch_repeat_customers() -> pd.DataFrame:
    """Fetch repeat customer summary from v_q05_repeat_customer_summary."""
    query = "SELECT * FROM v_q05_repeat_customer_summary;"
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn)
