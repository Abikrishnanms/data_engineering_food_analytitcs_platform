"""
FoodFlow Cloud Lakehouse — End-to-End Orchestrator
File: src/lakehouse/run_lakehouse.py

Description:
    Runs the complete 3-tier Medallion Data Lake pipeline:
    1. Bronze Ingestion (Raw CSVs -> Supabase 'foodflow-bronze')
    2. Silver Processing (Schema typing + Parquet compression -> Supabase 'foodflow-silver')
    3. Gold Marts (DuckDB analytical aggregations -> Supabase 'foodflow-gold')
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.lakehouse.ingest_bronze import ingest_bronze
from src.lakehouse.build_silver import build_silver
from src.lakehouse.build_gold import build_gold


def main():
    print("#" * 70)
    print("FOODFLOW CLOUD DATA LAKE (MEDALLION ARCHITECTURE)")
    print("Storage Engine: Supabase Storage + Apache Parquet + DuckDB")
    print("#" * 70)

    t_start = time.time()

    # Step 1: Bronze
    ingest_bronze()

    # Step 2: Silver
    build_silver()

    # Step 3: Gold
    build_gold()

    total_duration = time.time() - t_start
    print("\n" + "#" * 70)
    print(f"MEDALLION PIPELINE COMPLETED IN {total_duration:.2f}s!")
    print("Raw CSVs (Bronze) -> Clean Parquet (Silver) -> Curated Marts (Gold)")
    print("#" * 70)


if __name__ == "__main__":
    main()
