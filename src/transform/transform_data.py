"""
FoodFlow Data Transformation Pipeline
File: src/transform/transform_data.py

Description:
    Reads raw CSVs, standardizes types, strips whitespace, validates values,
    and exports canonical, clean CSVs to data/processed/.
"""

import json
import zipfile
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def ensure_raw_files():
    """Ensure raw CSVs exist, extracting from zip if needed."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    required = ["users.csv", "restaurants.csv", "menu.csv", "orders.csv", "order_items.csv"]
    missing = [f for f in required if not (RAW_DIR / f).exists()]
    if missing:
        zip_path = RAW_DIR / "Swiggy_Data.zip"
        if zip_path.exists():
            print(f"Extracting {zip_path.name}...")
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(RAW_DIR)
        else:
            raise FileNotFoundError(f"Missing raw files: {missing} and {zip_path} not found.")


def transform_users():
    print("Transforming users.csv...")
    df = pd.read_csv(RAW_DIR / "users.csv")
    initial_rows = len(df)

    # Standardize whitespace and casing
    df["user_id"] = df["user_id"].astype(str).str.strip()
    df["user_name"] = df["user_name"].astype(str).str.strip()
    df["age"] = pd.to_numeric(df["age"], errors="coerce").fillna(0).astype(int)
    df["gender"] = df["gender"].astype(str).str.strip().str.title()
    df["marital_status"] = df["marital_status"].astype(str).str.strip().str.title()
    df["occupation"] = df["occupation"].astype(str).str.strip().str.title()

    df = df.drop_duplicates(subset=["user_id"])
    df.to_csv(PROCESSED_DIR / "users.csv", index=False)
    print(f"  [OK] Users: {initial_rows:,} -> {len(df):,} rows.")
    return len(df)


def transform_restaurants():
    print("Transforming restaurants.csv...")
    df = pd.read_csv(RAW_DIR / "restaurants.csv")
    initial_rows = len(df)

    df["restaurant_id"] = df["restaurant_id"].astype(str).str.strip()
    df["restaurant_name"] = df["restaurant_name"].astype(str).str.strip()
    df["city"] = df["city"].astype(str).str.strip().str.title()
    df["cuisine"] = df["cuisine"].astype(str).str.strip().str.title()
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").round(2)
    df["is_cloud_kitchen"] = pd.to_numeric(df["is_cloud_kitchen"], errors="coerce").fillna(0).astype(int)

    df = df.drop_duplicates(subset=["restaurant_id"])
    df.to_csv(PROCESSED_DIR / "restaurants.csv", index=False)
    print(f"  [OK] Restaurants: {initial_rows:,} -> {len(df):,} rows.")
    return len(df)


def transform_menu():
    print("Transforming menu.csv...")
    df = pd.read_csv(RAW_DIR / "menu.csv")
    initial_rows = len(df)

    df["menu_id"] = df["menu_id"].astype(str).str.strip()
    df["restaurant_id"] = df["restaurant_id"].astype(str).str.strip()
    df["item_name"] = df["item_name"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip().str.title()
    df["price"] = pd.to_numeric(df["price"], errors="coerce").round(2)
    df["is_veg"] = pd.to_numeric(df["is_veg"], errors="coerce").fillna(0).astype(int)

    df = df.drop_duplicates(subset=["menu_id"])
    df.to_csv(PROCESSED_DIR / "menu.csv", index=False)
    print(f"  [OK] Menu: {initial_rows:,} -> {len(df):,} rows.")
    return len(df)


def transform_orders():
    print("Transforming orders.csv...")
    df = pd.read_csv(RAW_DIR / "orders.csv")
    initial_rows = len(df)

    df["order_id"] = df["order_id"].astype(str).str.strip()
    df["user_id"] = df["user_id"].astype(str).str.strip()
    df["restaurant_id"] = df["restaurant_id"].astype(str).str.strip()
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["delivery_time"] = df["delivery_time"].astype(str).str.strip()
    df["order_status"] = df["order_status"].astype(str).str.strip().str.title()
    df["payment_method"] = df["payment_method"].astype(str).str.strip()
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce").round(2)

    df = df.drop_duplicates(subset=["order_id"])
    df.to_csv(PROCESSED_DIR / "orders.csv", index=False)
    print(f"  [OK] Orders: {initial_rows:,} -> {len(df):,} rows.")
    return len(df)


def transform_order_items():
    print("Transforming order_items.csv...")
    df = pd.read_csv(RAW_DIR / "order_items.csv")
    initial_rows = len(df)

    df["order_item_id"] = df["order_item_id"].astype(str).str.strip()
    df["order_id"] = df["order_id"].astype(str).str.strip()
    df["menu_id"] = df["menu_id"].astype(str).str.strip()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int)
    df["price"] = pd.to_numeric(df["price"], errors="coerce").round(2)

    df = df.drop_duplicates(subset=["order_item_id"])
    df.to_csv(PROCESSED_DIR / "order_items.csv", index=False)
    print(f"  [OK] Order Items: {initial_rows:,} -> {len(df):,} rows.")
    return len(df)


def main():
    print("=" * 70)
    print("FOODFLOW DATA TRANSFORMATION PIPELINE")
    print("=" * 70)

    ensure_raw_files()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    summary = {
        "users": transform_users(),
        "restaurants": transform_restaurants(),
        "menu": transform_menu(),
        "orders": transform_orders(),
        "order_items": transform_order_items(),
    }

    report_path = PROCESSED_DIR / "transformation_summary.json"
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\n[SUCCESS] All datasets transformed and saved to {PROCESSED_DIR}")
    print(f"Summary report written to {report_path}")


if __name__ == "__main__":
    main()
