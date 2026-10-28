"""
FoodFlow Analytics — Backend Data Access Layer
File: backend/data_access.py

Description:
    Queries Supabase PostgreSQL analytical views and stored procedures
    using SQLAlchemy. Enforces the Analytics Contract (never queries raw tables).
"""

import os
from pathlib import Path
from functools import lru_cache
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@lru_cache(maxsize=1)
def get_engine():
    """Create and cache SQLAlchemy connection engine to Supabase."""
    user = os.getenv("FOODFLOW_DB_USER", "postgres")
    password = os.getenv("FOODFLOW_DB_PASSWORD", "")
    host = os.getenv("FOODFLOW_DB_HOST", "localhost")
    port = int(os.getenv("FOODFLOW_DB_PORT", "5432"))
    database = os.getenv("FOODFLOW_DB_NAME", "postgres")

    url = URL.create(
        "postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=10)


def fetch_kpi_summary(start_date: str = "2025-01-01", end_date: str = "2025-12-31") -> dict:
    """Fetch aggregated KPIs for arbitrary date range via fn_kpi_summary."""
    query = "SELECT * FROM fn_kpi_summary(CAST(:start AS date), CAST(:end AS date));"
    with get_engine().connect() as conn:
        df = pd.read_sql(text(query), conn, params={"start": str(start_date), "end": str(end_date)})
        if df.empty:
            return {}
        record = df.iloc[0].to_dict()
        # Clean numeric nulls
        for k, v in record.items():
            if pd.isna(v):
                record[k] = 0
            elif isinstance(v, (int, float)):
                record[k] = float(v) if isinstance(v, float) else int(v)
        return record


def fetch_daily_kpis(start_date: str = "2025-01-01", end_date: str = "2025-12-31") -> list:
    """Fetch daily time-series metrics from v_kpi_daily."""
    query = """
        SELECT order_date, total_orders, qualifying_orders, cancelled_orders,
               qualifying_revenue, avg_order_value, cancellation_rate
        FROM v_kpi_daily
        WHERE order_date BETWEEN CAST(:start AS date) AND CAST(:end AS date)
        ORDER BY order_date ASC;
    """
    with get_engine().connect() as conn:
        df = pd.read_sql(text(query), conn, params={"start": str(start_date), "end": str(end_date)})
        df["order_date"] = df["order_date"].astype(str)
        return df.fillna(0).to_dict(orient="records")


def fetch_top_restaurants(start_date: str = "2025-01-01", end_date: str = "2025-12-31", limit: int = 5) -> list:
    """Fetch top restaurants by qualifying revenue via fn_top_restaurants."""
    query = "SELECT * FROM fn_top_restaurants(CAST(:start AS date), CAST(:end AS date), CAST(:limit AS int));"
    with get_engine().connect() as conn:
        df = pd.read_sql(text(query), conn, params={"start": str(start_date), "end": str(end_date), "limit": int(limit)})
        return df.fillna(0).to_dict(orient="records")


def fetch_top_items(start_date: str = "2025-01-01", end_date: str = "2025-12-31", limit: int = 10) -> list:
    """Fetch top menu items by units sold via v_q03_item_monthly_performance."""
    query = """
        SELECT menu_id, item_name, category, restaurant_name,
               SUM(units_sold) AS units_sold,
               ROUND(SUM(qualifying_revenue), 2) AS qualifying_revenue
        FROM v_q03_item_monthly_performance
        WHERE order_month BETWEEN DATE_TRUNC('month', CAST(:start AS date)) AND CAST(:end AS date)
        GROUP BY menu_id, item_name, category, restaurant_name
        ORDER BY units_sold DESC
        LIMIT CAST(:limit AS int);
    """
    with get_engine().connect() as conn:
        df = pd.read_sql(text(query), conn, params={"start": str(start_date), "end": str(end_date), "limit": int(limit)})
        return df.fillna(0).to_dict(orient="records")


def fetch_cuisine_mix() -> list:
    """Fetch cuisine revenue share from v_q07_cuisine_mix_monthly."""
    query = """
        SELECT cuisine,
               ROUND(SUM(qualifying_revenue), 2) AS total_revenue,
               SUM(qualifying_orders) AS total_orders
        FROM v_q07_cuisine_mix_monthly
        GROUP BY cuisine
        ORDER BY total_revenue DESC
        LIMIT 8;
    """
    with get_engine().connect() as conn:
        df = pd.read_sql(text(query), conn)
        return df.fillna(0).to_dict(orient="records")


def fetch_payment_mix() -> list:
    """Fetch payment method distribution from v_q08_payment_mix_monthly."""
    query = """
        SELECT payment_method, SUM(total_orders) AS total_orders
        FROM v_q08_payment_mix_monthly
        GROUP BY payment_method
        ORDER BY total_orders DESC;
    """
    with get_engine().connect() as conn:
        df = pd.read_sql(text(query), conn)
        return df.fillna(0).to_dict(orient="records")


def fetch_hourly_orders() -> list:
    """Fetch order volume by recorded clock hour from v_q09_orders_by_recorded_hour."""
    query = """
        SELECT recorded_hour, total_orders, qualifying_orders
        FROM v_q09_orders_by_recorded_hour
        ORDER BY recorded_hour ASC;
    """
    with get_engine().connect() as conn:
        df = pd.read_sql(text(query), conn)
        return df.fillna(0).to_dict(orient="records")
