"""
FoodFlow Cloud Lakehouse — 02 Silver Pipeline
File: src/lakehouse/build_silver.py

Description:
    Processes raw Bronze data into the Silver tier:
    - Cleans strings, strips whitespace, standardizes ISO dates.
    - Enforces strongly-typed schemas (integers, floats, dates).
    - Converts datasets into columnar Apache Parquet with Snappy compression.
    - Uploads Parquet datasets to Supabase 'foodflow-silver' bucket.
    - Demonstrates 70-80% storage reduction and faster columnar scan speeds.
"""

import gzip
import io
import os
import sys
import time
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.lakehouse.supabase_client import upload_bytes, download_bytes, BUCKETS

SILVER_DIR = PROJECT_ROOT / "data" / "processed" / "silver"
SILVER_DIR.mkdir(parents=True, exist_ok=True)


def clean_users(df: pd.DataFrame) -> pd.DataFrame:
    df["user_id"] = df["user_id"].astype(str).str.strip()
    df["age"] = pd.to_numeric(df["age"], errors="coerce").fillna(0).astype("int16")
    df["gender"] = df["gender"].astype(str).str.strip().str.title()
    df["occupation"] = df["occupation"].astype(str).str.strip()
    df["marital_status"] = df["marital_status"].astype(str).str.strip()
    return df


def clean_restaurants(df: pd.DataFrame) -> pd.DataFrame:
    df["restaurant_id"] = df["restaurant_id"].astype(str).str.strip()
    df["restaurant_name"] = df["restaurant_name"].astype(str).str.strip()
    df["city"] = df["city"].astype(str).str.strip().str.title()
    df["cuisine"] = df["cuisine"].astype(str).str.strip().str.title()
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").round(2).astype("float32")
    df["is_cloud_kitchen"] = pd.to_numeric(df["is_cloud_kitchen"], errors="coerce").fillna(0).astype("int8")
    return df


def clean_menu(df: pd.DataFrame) -> pd.DataFrame:
    df["menu_id"] = df["menu_id"].astype(str).str.strip()
    df["restaurant_id"] = df["restaurant_id"].astype(str).str.strip()
    df["item_name"] = df["item_name"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip().str.title()
    df["price"] = pd.to_numeric(df["price"], errors="coerce").round(2).astype("float32")
    df["is_veg"] = pd.to_numeric(df["is_veg"], errors="coerce").fillna(0).astype("int8")
    return df


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    df["order_id"] = df["order_id"].astype(str).str.strip()
    df["user_id"] = df["user_id"].astype(str).str.strip()
    df["restaurant_id"] = df["restaurant_id"].astype(str).str.strip()
    df["order_date"] = pd.to_datetime(df["order_date"]).dt.date
    df["delivery_time"] = df["delivery_time"].astype(str).str.strip()
    df["order_status"] = df["order_status"].astype(str).str.strip().str.title()
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce").round(2).astype("float32")
    df["payment_method"] = df["payment_method"].astype(str).str.strip()
    return df


def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:
    df["order_item_id"] = df["order_item_id"].astype(str).str.strip()
    df["order_id"] = df["order_id"].astype(str).str.strip()
    df["menu_id"] = df["menu_id"].astype(str).str.strip()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype("int16")
    df["price"] = pd.to_numeric(df["price"], errors="coerce").round(2).astype("float32")
    return df


CLEANERS = {
    "users": clean_users,
    "restaurants": clean_restaurants,
    "menu": clean_menu,
    "orders": clean_orders,
    "order_items": clean_order_items,
}


def build_silver():
    """Download Bronze CSVs, clean & type them, and convert to Parquet in Silver bucket."""
    print("=" * 70)
    print("STAGE 2: SILVER LAYER PROCESSING (Cleaned Apache Parquet)")
    print(f"Target Bucket: {BUCKETS['silver']}")
    print("=" * 70)

    start_total = time.time()
    total_raw_bytes = 0
    total_parquet_bytes = 0

    for table_name, cleaner_fn in CLEANERS.items():
        csv_filename = f"{table_name}.csv"
        parquet_filename = f"{table_name}.parquet"
        print(f"\nProcessing {table_name}...")

        # 1. Download CSV or CSV.GZ from Bronze
        t0 = time.time()
        try:
            csv_bytes = download_bytes(BUCKETS["bronze"], f"raw/{csv_filename}")
        except Exception:
            # Fallback to .gz if compressed
            csv_bytes = download_bytes(BUCKETS["bronze"], f"raw/{csv_filename}.gz")
            csv_bytes = gzip.decompress(csv_bytes)

        raw_size = len(csv_bytes)
        total_raw_bytes += raw_size
        print(f"  - Downloaded {raw_size / (1024*1024):.2f} MB from Bronze in {time.time() - t0:.2f}s")

        # 2. Parse & Clean
        t1 = time.time()
        df = pd.read_csv(io.BytesIO(csv_bytes))
        df = cleaner_fn(df)
        print(f"  - Cleaned {len(df):,} records with schema types in {time.time() - t1:.2f}s")

        # 3. Convert to Apache Arrow & Parquet (Snappy compression)
        arrow_table = pa.Table.from_pandas(df, preserve_index=False)
        parquet_buffer = io.BytesIO()
        pq.write_table(arrow_table, parquet_buffer, compression="snappy")
        parquet_bytes = parquet_buffer.getvalue()
        pq_size = len(parquet_bytes)
        total_parquet_bytes += pq_size

        compression_ratio = (1 - (pq_size / max(raw_size, 1))) * 100
        print(f"  - Compressed: {raw_size / (1024*1024):.2f} MB CSV -> {pq_size / (1024*1024):.2f} MB Parquet ({compression_ratio:.1f}% reduction!)")

        # 4. Save local copy for fast DuckDB queries
        local_pq_path = SILVER_DIR / parquet_filename
        with open(local_pq_path, "wb") as f:
            f.write(parquet_bytes)

        # 5. Upload to Silver Bucket in Supabase
        t2 = time.time()
        upload_bytes(
            BUCKETS["silver"],
            parquet_bytes,
            f"{table_name}/{parquet_filename}",
            content_type="application/octet-stream",
        )
        print(f"  - Uploaded to {BUCKETS['silver']}/{table_name}/{parquet_filename} in {time.time() - t2:.2f}s")

    total_time = time.time() - start_total
    overall_reduction = (1 - (total_parquet_bytes / max(total_raw_bytes, 1))) * 100
    print("\n" + "=" * 70)
    print(f"Silver Pipeline Complete in {total_time:.2f} seconds!")
    print(f"Total Storage: {total_raw_bytes / (1024*1024):.2f} MB (CSV) -> {total_parquet_bytes / (1024*1024):.2f} MB (Parquet)")
    print(f"Overall Space Saved: {overall_reduction:.1f}%")
    print("=" * 70)


if __name__ == "__main__":
    build_silver()
