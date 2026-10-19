
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# 1. Define project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"
REPORT_PATH = PROJECT_ROOT / "data" / "processed"

REPORT_PATH.mkdir(parents=True, exist_ok=True)

# Expected primary key for each dataset
PRIMARY_KEYS = {
    "users.csv": "user_id",
    "restaurants.csv": "restaurant_id",
    "menu.csv": "menu_id",
    "orders.csv": "order_id",
    "order_items.csv": "order_item_id",
}


def profile_dataset(file_path):
    """Profile one CSV and return table and column summaries."""

    print("\n" + "=" * 70)
    print(f"DATASET: {file_path.name}")
    print("=" * 70)

    # Load one dataset at a time
    df = pd.read_csv(file_path, low_memory=False)

    rows, columns = df.shape
    missing_cells = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    print(f"Rows: {rows:,}")
    print(f"Columns: {columns}")
    print(f"Missing cells: {missing_cells:,}")
    print(f"Duplicate rows: {duplicate_rows:,}")

    print("\nColumn names:")
    print(df.columns.tolist())

    print("\nData types:")
    print(df.dtypes.to_string())

    print("\nMissing values by column:")
    print(df.isna().sum().to_string())

    # Check the expected primary key
    key = PRIMARY_KEYS.get(file_path.name)

    if key and key in df.columns:
        unique_keys = int(df[key].nunique(dropna=True))
        missing_keys = int(df[key].isna().sum())
        duplicate_keys = int(df[key].duplicated().sum())

        print(f"\nPrimary key candidate: {key}")
        print(f"Unique key values: {unique_keys:,}")
        print(f"Missing key values: {missing_keys:,}")
        print(f"Duplicate key values: {duplicate_keys:,}")
    else:
        unique_keys = None
        missing_keys = None
        duplicate_keys = None
        print("\nWARNING: Expected primary key column was not found.")

    # Numerical summary
    numeric_columns = df.select_dtypes(include="number").columns

    if len(numeric_columns) > 0:
        print("\nNumerical statistics:")
        print(df[numeric_columns].describe().round(2).to_string())

    # Build a column-level profile
    column_profile = pd.DataFrame({
        "table": file_path.name,
        "column": df.columns,
        "data_type": [
            str(dtype) for dtype in df.dtypes
        ],
        "missing_count": [
            int(value) for value in df.isna().sum()
        ],
        "missing_percent": [
            round(float(value), 2)
            for value in df.isna().mean() * 100
        ],
        "unique_values": [
            int(value) for value in df.nunique(dropna=True)
        ],
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
    """Profile every CSV in the raw data directory."""

    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Raw data directory not found: {RAW_DATA_PATH}"
        )

    csv_files = sorted(RAW_DATA_PATH.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {RAW_DATA_PATH}"
        )

    print(f"Found {len(csv_files)} CSV files.")
    print(f"Reading data from: {RAW_DATA_PATH}")

    table_summaries = []
    column_profiles = []

    for file_path in csv_files:
        summary, columns = profile_dataset(file_path)
        table_summaries.append(summary)
        column_profiles.append(columns)

    # Save reports
    summary_df = pd.DataFrame(table_summaries)
    columns_df = pd.concat(column_profiles, ignore_index=True)

    summary_file = REPORT_PATH / "profiling_summary.csv"
    columns_file = REPORT_PATH / "column_profile.csv"

    summary_df.to_csv(summary_file, index=False)
    columns_df.to_csv(columns_file, index=False)

    print("\n" + "=" * 70)
    print("PROFILING COMPLETED")
    print("=" * 70)
    print(summary_df.to_string(index=False))
    print(f"\nTable summary saved to: {summary_file}")
    print(f"Column profile saved to: {columns_file}")


if __name__ == "__main__":
    main()
