"""
FoodFlow Cloud Lakehouse — 03 Gold Aggregations
File: src/lakehouse/build_gold.py

Description:
    Computes curated analytical business data marts from Silver Parquet files
    using DuckDB's in-memory columnar engine.
    Uploads aggregated Parquet marts into Supabase 'foodflow-gold' bucket:
    1. kpi_daily.parquet
    2. restaurant_monthly.parquet
    3. cuisine_performance.parquet
"""

import os
import sys
import time
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.lakehouse.supabase_client import upload_bytes, BUCKETS

SILVER_DIR = PROJECT_ROOT / "data" / "processed" / "silver"
GOLD_DIR = PROJECT_ROOT / "data" / "processed" / "gold"
GOLD_DIR.mkdir(parents=True, exist_ok=True)


def build_gold():
    """Build Gold business marts with DuckDB and upload to foodflow-gold bucket."""
    print("=" * 70)
    print("STAGE 3: GOLD LAYER AGGREGATION (DuckDB -> Curated Parquet Marts)")
    print(f"Target Bucket: {BUCKETS['gold']}")
    print("=" * 70)

    start_total = time.time()

    # Connect to DuckDB and register local Silver Parquet files
    con = duckdb.connect()
    orders_path = (SILVER_DIR / "orders.parquet").as_posix()
    items_path = (SILVER_DIR / "order_items.parquet").as_posix()
    rest_path = (SILVER_DIR / "restaurants.parquet").as_posix()
    menu_path = (SILVER_DIR / "menu.parquet").as_posix()

    con.execute(f"CREATE VIEW orders AS SELECT * FROM read_parquet('{orders_path}')")
    con.execute(f"CREATE VIEW order_items AS SELECT * FROM read_parquet('{items_path}')")
    con.execute(f"CREATE VIEW restaurants AS SELECT * FROM read_parquet('{rest_path}')")
    con.execute(f"CREATE VIEW menu AS SELECT * FROM read_parquet('{menu_path}')")

    # -------------------------------------------------------------------------
    # Mart 1: Daily KPI Timeline
    # -------------------------------------------------------------------------
    print("\nComputing Mart 1: Daily KPI Timeline (kpi_daily.parquet)...")
    t0 = time.time()
    pq_path1 = GOLD_DIR / "kpi_daily.parquet"
    con.execute(f"""
        COPY (
            SELECT 
                order_date,
                COUNT(*) AS total_orders,
                COUNT(*) FILTER (WHERE order_status = 'Delivered') AS qualifying_orders,
                COUNT(*) FILTER (WHERE order_status = 'Cancelled') AS cancelled_orders,
                ROUND(SUM(total_amount) FILTER (WHERE order_status = 'Delivered'), 2) AS qualifying_revenue,
                ROUND(
                    SUM(total_amount) FILTER (WHERE order_status = 'Delivered') / 
                    NULLIF(COUNT(*) FILTER (WHERE order_status = 'Delivered'), 0), 
                    2
                ) AS avg_order_value,
                ROUND(
                    COUNT(*) FILTER (WHERE order_status = 'Cancelled')::DOUBLE / 
                    COUNT(*) * 100, 
                    2
                ) AS cancellation_rate
            FROM orders
            GROUP BY order_date
            ORDER BY order_date
        ) TO '{pq_path1.as_posix()}' (FORMAT PARQUET, COMPRESSION SNAPPY)
    """)
    upload_bytes(BUCKETS["gold"], pq_path1.read_bytes(), "kpi_daily.parquet")
    print(f"  - Completed in {time.time() - t0:.2f}s ({pq_path1.stat().st_size / 1024:.1f} KB)")

    # -------------------------------------------------------------------------
    # Mart 2: Restaurant Monthly Rankings
    # -------------------------------------------------------------------------
    print("\nComputing Mart 2: Monthly Restaurant Rankings (restaurant_monthly.parquet)...")
    t1 = time.time()
    pq_path2 = GOLD_DIR / "restaurant_monthly.parquet"
    con.execute(f"""
        COPY (
            WITH monthly_rest AS (
                SELECT 
                    DATE_TRUNC('month', order_date::DATE)::DATE AS order_month,
                    r.restaurant_id,
                    r.restaurant_name,
                    r.city,
                    r.cuisine,
                    COUNT(*) FILTER (WHERE o.order_status = 'Delivered') AS qualifying_orders,
                    ROUND(SUM(o.total_amount) FILTER (WHERE o.order_status = 'Delivered'), 2) AS qualifying_revenue
                FROM orders o
                JOIN restaurants r ON o.restaurant_id = r.restaurant_id
                GROUP BY 1, 2, 3, 4, 5
            )
            SELECT 
                *,
                DENSE_RANK() OVER (PARTITION BY order_month ORDER BY qualifying_revenue DESC) AS revenue_rank
            FROM monthly_rest
            ORDER BY order_month, revenue_rank
        ) TO '{pq_path2.as_posix()}' (FORMAT PARQUET, COMPRESSION SNAPPY)
    """)
    upload_bytes(BUCKETS["gold"], pq_path2.read_bytes(), "restaurant_monthly.parquet")
    print(f"  - Completed in {time.time() - t1:.2f}s ({pq_path2.stat().st_size / 1024:.1f} KB)")

    # -------------------------------------------------------------------------
    # Mart 3: Cuisine Performance
    # -------------------------------------------------------------------------
    print("\nComputing Mart 3: Overall Cuisine Performance (cuisine_performance.parquet)...")
    t2 = time.time()
    pq_path3 = GOLD_DIR / "cuisine_performance.parquet"
    con.execute(f"""
        COPY (
            WITH cuisine_stats AS (
                SELECT 
                    r.cuisine,
                    COUNT(*) AS total_orders,
                    COUNT(*) FILTER (WHERE o.order_status = 'Delivered') AS qualifying_orders,
                    ROUND(SUM(o.total_amount) FILTER (WHERE o.order_status = 'Delivered'), 2) AS qualifying_revenue
                FROM orders o
                JOIN restaurants r ON o.restaurant_id = r.restaurant_id
                GROUP BY r.cuisine
            )
            SELECT 
                cuisine,
                total_orders,
                qualifying_orders,
                qualifying_revenue,
                ROUND(qualifying_revenue / NULLIF(qualifying_orders, 0), 2) AS avg_order_value,
                ROUND(qualifying_revenue / SUM(qualifying_revenue) OVER () * 100, 2) AS share_of_revenue
            FROM cuisine_stats
            ORDER BY qualifying_revenue DESC
        ) TO '{pq_path3.as_posix()}' (FORMAT PARQUET, COMPRESSION SNAPPY)
    """)
    upload_bytes(BUCKETS["gold"], pq_path3.read_bytes(), "cuisine_performance.parquet")
    print(f"  - Completed in {time.time() - t2:.2f}s ({pq_path3.stat().st_size / 1024:.1f} KB)")

    total_time = time.time() - start_total
    print("\n" + "=" * 70)
    print(f"Gold Marts Successfully Created and Uploaded in {total_time:.2f} seconds!")
    print(f"All 3 Marts stored in Supabase Bucket: {BUCKETS['gold']}")
    print("=" * 70)


if __name__ == "__main__":
    build_gold()
