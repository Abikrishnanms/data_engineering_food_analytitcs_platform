"""
FoodFlow Cloud Lakehouse — 01 Bronze Ingestion
File: src/lakehouse/ingest_bronze.py

Description:
    Uploads raw, immutable source CSV datasets into the Supabase
    'foodflow-bronze' storage bucket.
    Automatically compresses files > 45MB with gzip (e.g. order_items.csv.gz)
    to respect Supabase Storage's 50MB single-object limit on the free tier.
"""

import gzip
import os
import sys
import time
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.lakehouse.supabase_client import upload_bytes, BUCKETS

RAW_DIR = PROJECT_ROOT / "data" / "raw"
ZIP_PATH = RAW_DIR / "Swiggy_Data.zip"

TABLE_FILES = [
    "users.csv",
    "restaurants.csv",
    "menu.csv",
    "orders.csv",
    "order_items.csv",
]


def ensure_raw_files_available():
    """Ensure raw CSVs are available on disk or extract from Swiggy_Data.zip."""
    missing = [f for f in TABLE_FILES if not (RAW_DIR / f).exists()]
    if missing and ZIP_PATH.exists():
        print(f"Extracting missing raw CSVs from {ZIP_PATH.name}...")
        with zipfile.ZipFile(ZIP_PATH, "r") as z:
            z.extractall(RAW_DIR)


def ingest_bronze():
    """Upload all raw CSV tables into the Bronze bucket."""
    print("=" * 70)
    print("STAGE 1: BRONZE LAYER INGESTION (Supabase Storage)")
    print(f"Target Bucket: {BUCKETS['bronze']}")
    print("=" * 70)

    ensure_raw_files_available()
    bucket_name = BUCKETS["bronze"]
    start_total = time.time()

    for filename in TABLE_FILES:
        filepath = RAW_DIR / filename
        if not filepath.exists():
            print(f"[!] Warning: {filename} not found in {RAW_DIR}. Skipping.")
            continue

        file_size_mb = filepath.stat().st_size / (1024 * 1024)

        with open(filepath, "rb") as f:
            data = f.read()

        # If file exceeds 45 MB (Supabase free limit is 50 MB), compress as gzip
        if file_size_mb > 45:
            print(f"Compressing {filename} ({file_size_mb:.2f} MB > 45MB limit)... ", end="", flush=True)
            t_comp = time.time()
            data = gzip.compress(data, compresslevel=6)
            gz_size_mb = len(data) / (1024 * 1024)
            print(f"Compressed to {gz_size_mb:.2f} MB in {time.time() - t_comp:.2f}s")
            remote_path = f"raw/{filename}.gz"
            content_type = "application/gzip"
            display_mb = gz_size_mb
        else:
            remote_path = f"raw/{filename}"
            content_type = "text/csv"
            display_mb = file_size_mb

        print(f"Uploading {remote_path:<24} ({display_mb:6.2f} MB)... ", end="", flush=True)
        t0 = time.time()
        upload_bytes(bucket_name, data, remote_path, content_type=content_type)
        elapsed = time.time() - t0
        print(f"Done in {elapsed:5.2f}s ({display_mb / max(elapsed, 0.01):5.2f} MB/s)")

    total_time = time.time() - start_total
    print("=" * 70)
    print(f"Bronze Ingestion Completed Successfully in {total_time:.2f} seconds!")
    print("=" * 70)


if __name__ == "__main__":
    ingest_bronze()
