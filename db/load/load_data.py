"""
FoodFlow Database Loader
File: db/load/load_data.py

Description:
    Repeatable, high-performance loader for the FoodFlow dataset into PostgreSQL.
    Features:
    - Reads directly from data/raw/ CSVs or extracted files, or streams from Swiggy_Data.zip.
    - Loads tables in strict relational hierarchy:
        1. Parent tables: users, restaurants
        2. Dependent tables: menu, orders
        3. Child table: order_items
    - Uses PostgreSQL COPY via copy_expert() for sub-second to second bulk loading of ~2.3M rows.
    - Idempotent: can truncate and reload cleanly without foreign key deadlock.
    - Supports connection configuration via environment variables or .env file.
"""

import io
import os
import sys
import time
import zipfile
from pathlib import Path
import psycopg2
from psycopg2 import sql

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
ZIP_PATH = RAW_DIR / "Swiggy_Data.zip"
SCHEMA_DIR = PROJECT_ROOT / "db" / "schema"

# Database Configuration (Environment variables with defaults or read from .env)
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

DB_HOST = os.getenv("FOODFLOW_DB_HOST", "localhost")
DB_PORT = os.getenv("FOODFLOW_DB_PORT", "5432")
DB_NAME = os.getenv("FOODFLOW_DB_NAME", "foodflow")
DB_USER = os.getenv("FOODFLOW_DB_USER", "postgres")
DB_PASSWORD = os.getenv("FOODFLOW_DB_PASSWORD", "postgres")

# Loading order honoring foreign key dependencies
TABLE_CSV_MAP = [
    {
        "table": "users",
        "csv_name": "users.csv",
        "columns": ["user_id", "user_name", "age", "gender", "marital_status", "occupation"],
    },
    {
        "table": "restaurants",
        "csv_name": "restaurants.csv",
        "columns": ["restaurant_id", "restaurant_name", "city", "cuisine", "rating", "is_cloud_kitchen"],
    },
    {
        "table": "menu",
        "csv_name": "menu.csv",
        "columns": ["menu_id", "restaurant_id", "item_name", "category", "price", "is_veg"],
    },
    {
        "table": "orders",
        "csv_name": "orders.csv",
        "columns": [
            "order_id",
            "user_id",
            "restaurant_id",
            "order_date",
            "delivery_time",
            "order_status",
            "payment_method",
            "total_amount",
        ],
    },
    {
        "table": "order_items",
        "csv_name": "order_items.csv",
        "columns": ["order_item_id", "order_id", "menu_id", "quantity", "price"],
    },
]


def get_connection():
    """Establish and return a connection to PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        conn.autocommit = False
        return conn
    except Exception as e:
        print(f"\n[ERROR] Could not connect to PostgreSQL ({DB_HOST}:{DB_PORT}/{DB_NAME}) as '{DB_USER}'.")
        print(f"Details: {e}")
        print("\nPlease check your credentials and make sure PostgreSQL is running.")
        sys.exit(1)


def execute_sql_file(conn, file_path):
    """Execute all statements in a SQL script file."""
    print(f"\n--> Executing SQL script: {file_path.name}")
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    with conn.cursor() as cur:
        cur.execute(sql_content)
    conn.commit()
    print(f"[OK] Successfully executed {file_path.name}")


def get_csv_stream(csv_name):
    """
    Open CSV file from extracted data/raw or directly from data/raw/Swiggy_Data.zip.
    Returns a file-like object stream and a closer callback.
    """
    extracted_path = RAW_DIR / csv_name
    if extracted_path.exists():
        print(f"    Reading from extracted file: {extracted_path}")
        f = open(extracted_path, "r", encoding="utf-8")
        return f, f.close

    if ZIP_PATH.exists():
        print(f"    Streaming directly from ZIP: {ZIP_PATH.name} -> {csv_name}")
        zf = zipfile.ZipFile(ZIP_PATH, "r")
        csv_file = zf.open(csv_name, "r")
        text_stream = io.TextIOWrapper(csv_file, encoding="utf-8")

        def cleanup():
            text_stream.close()
            csv_file.close()
            zf.close()

        return text_stream, cleanup

    raise FileNotFoundError(f"Could not find {csv_name} in {RAW_DIR} or inside {ZIP_PATH}")


def load_table(cur, table_info):
    """Bulk load data into a table using PostgreSQL COPY."""
    table = table_info["table"]
    csv_name = table_info["csv_name"]
    columns = table_info["columns"]
    cols_joined = ", ".join(columns)

    start_time = time.time()
    stream, close_cb = get_csv_stream(csv_name)

    try:
        copy_sql = f"""
            COPY {table} ({cols_joined})
            FROM STDIN
            WITH (FORMAT csv, HEADER true, DELIMITER ',');
        """
        cur.copy_expert(sql=copy_sql, file=stream)
        elapsed = time.time() - start_time

        # Check row count
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        row_count = cur.fetchone()[0]
        print(f"[LOADED] Table '{table}': {row_count:,} rows in {elapsed:.2f}s")
    finally:
        close_cb()


def main():
    print("=" * 70)
    print("FOODFLOW DATABASE LOADER")
    print("=" * 70)

    # 1. Connect
    conn = get_connection()
    print(f"[CONNECTED] PostgreSQL connected to {DB_NAME} at {DB_HOST}:{DB_PORT}")

    try:
        # 2. Re-create tables
        tables_file = SCHEMA_DIR / "001_create_tables.sql"
        execute_sql_file(conn, tables_file)

        # 3. Load data in relational order
        print("\n--> Starting bulk data load...")
        total_load_start = time.time()
        with conn.cursor() as cur:
            for item in TABLE_CSV_MAP:
                load_table(cur, item)
        conn.commit()
        total_elapsed = time.time() - total_load_start
        print(f"\n[OK] All tables successfully loaded in {total_elapsed:.2f}s!")

        # 4. Build indexes
        indexes_file = SCHEMA_DIR / "002_indexes.sql"
        execute_sql_file(conn, indexes_file)

        print("\n" + "=" * 70)
        print("DATABASE INITIALIZATION & LOAD COMPLETED SUCCESSFULLY!")
        print("Run 'tests/test_database.sql' to run full validation checks.")
        print("=" * 70)

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Data load failed: {e}")
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    main()
