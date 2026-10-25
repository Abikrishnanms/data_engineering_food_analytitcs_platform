"""
FoodFlow Schema Profiler
File: src/ingestion/profile_data.py
"""

import zipfile
import pandas as pd
from pathlib import Path

# Find project root robustly
_curr = Path(__file__).resolve()
PROJECT_ROOT = _curr.parents[2] if "src" in _curr.parts else _curr.parents[1]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"
REPORT_PATH = PROJECT_ROOT / "data" / "processed"
REPORT_PATH.mkdir(parents=True, exist_ok=True)

PRIMARY_KEYS = {
    "users.csv": "user_id",
    "restaurants.csv": "restaurant_id",
    "menu.csv": "menu_id",
    "orders.csv": "order_id",
    "order_items.csv": "order_item_id",
}


def profile_dataset(file_path):
    print("\n" + "=" * 70)
    print(f"DATASET: {file_path.name}")
    print("=" * 70)

    df = pd.read_csv(file_path, low_memory=False)

    rows, columns = df.shape
    missing_cells = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    print(f"Rows: {rows:,}")
    print(f"Columns: {columns}")
    print(f"Missing cells: {missing_cells:,}")
    print(f"Duplicate rows: {duplicate_rows:,}")

    key = PRIMARY_KEYS.get(file_path.name)
    if key and key in df.columns:
        unique_keys = int(df[key].nunique(dropna=True))
        missing_keys = int(df[key].isna().sum())
        duplicate_keys = int(df[key].duplicated().sum())
        print(f"Primary key candidate: {key}")
        print(f"Unique keys: {unique_keys:,} | Missing: {missing_keys:,} | Dups: {duplicate_keys:,}")
    else:
        unique_keys, missing_keys, duplicate_keys = None, None, None

    column_profile = pd.DataFrame({
        "table": file_path.name,
        "column": df.columns,
        "data_type": [str(dtype) for dtype in df.dtypes],
        "missing_count": [int(v) for v in df.isna().sum()],
        "missing_percent": [round(float(v), 2) for v in df.isna().mean() * 100],
        "unique_values": [int(v) for v in df.nunique(dropna=True)],
    })

    table_summary = {
        "table": file_path.name,
        "rows": rows,
        "columns": columns,
        "missing_cells": missing_cells,
        "duplicate_rows": duplicate_rows,
        "primary_key": key,
        "unique_key_values": unique_keys,
        "missing_key_values": missing_keys,
        "duplicate_key_values": duplicate_keys,
    }

    return table_summary, column_profile


def main():
    if not RAW_DATA_PATH.exists():
        RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(RAW_DATA_PATH.glob("*.csv"))
    if not csv_files:
        zip_path = RAW_DATA_PATH / "Swiggy_Data.zip"
        if zip_path.exists():
            print(f"Extracting {zip_path.name} into {RAW_DATA_PATH}...")
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(RAW_DATA_PATH)
            csv_files = sorted(RAW_DATA_PATH.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {RAW_DATA_PATH}")

    print(f"Found {len(csv_files)} CSV files in {RAW_DATA_PATH}.")
    table_summaries = []
    column_profiles = []

    for file_path in csv_files:
        summary, columns = profile_dataset(file_path)
        table_summaries.append(summary)
        column_profiles.append(columns)

    summary_df = pd.DataFrame(table_summaries)
    columns_df = pd.concat(column_profiles, ignore_index=True)

    summary_file = REPORT_PATH / "profiling_summary.csv"
    columns_file = REPORT_PATH / "column_profile.csv"

    summary_df.to_csv(summary_file, index=False)
    columns_df.to_csv(columns_file, index=False)

    print("\n" + "=" * 70)
    print(f"PROFILING COMPLETED. Reports saved to {REPORT_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()
