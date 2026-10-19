"""
FoodFlow Database Test Runner
File: tests/run_tests.py
Role: Lekshmi Priya - Database Engineer

Description:
    Runs tests/test_database.sql queries directly against the PostgreSQL database
    using Python and psycopg2, and displays formatted results in the terminal.
"""

import os
import sys
from pathlib import Path
import psycopg2

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Read .env if present
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


def main():
    test_sql_path = PROJECT_ROOT / "tests" / "test_database.sql"
    if not test_sql_path.exists():
        print(f"Error: Could not find {test_sql_path}")
        sys.exit(1)

    print("=" * 70)
    print("FOODFLOW DATABASE VALIDATION TEST SUITE")
    print(f"Connecting to {DB_NAME} on {DB_HOST}:{DB_PORT} as {DB_USER}...")
    print("=" * 70)

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
    except Exception as e:
        print(f"[ERROR] Could not connect to database: {e}")
        sys.exit(1)

    with open(test_sql_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split statements by semicolon
    statements = [stmt.strip() for stmt in content.split(";") if stmt.strip()]

    all_passed = True

    with conn.cursor() as cur:
        for idx, stmt in enumerate(statements, 1):
            # Skip pure comment blocks
            code_lines = [l for l in stmt.splitlines() if not l.strip().startswith("--")]
            if not "".join(code_lines).strip():
                continue

            first_meaningful_line = next((l.strip() for l in stmt.splitlines() if l.strip().startswith("--") and not l.strip().startswith("----")), f"Test Block {idx}")
            title = first_meaningful_line.replace("--", "").strip()

            print(f"\n--> Running: {title}")
            try:
                cur.execute(stmt)
                if cur.description:
                    col_names = [desc[0] for desc in cur.description]
                    rows = cur.fetchall()

                    # Print header
                    header = " | ".join(f"{col:25}" for col in col_names)
                    print("-" * len(header))
                    print(header)
                    print("-" * len(header))

                    for row in rows:
                        row_str = " | ".join(f"{str(val):25}" for val in row)
                        print(row_str)

                        # Check if this row is a failure check
                        if "is_valid" in col_names:
                            val_idx = col_names.index("is_valid")
                            if not row[val_idx]:
                                all_passed = False
                        if "orphan_count" in col_names:
                            val_idx = col_names.index("orphan_count")
                            if row[val_idx] != 0:
                                all_passed = False
                        if "invalid_count" in col_names:
                            val_idx = col_names.index("invalid_count")
                            if row[val_idx] != 0:
                                all_passed = False
                        if "dup_count" in col_names:
                            val_idx = col_names.index("dup_count")
                            if row[val_idx] != 0:
                                all_passed = False

            except Exception as e:
                print(f"[FAIL] Error executing query: {e}")
                all_passed = False

    conn.close()

    print("\n" + "=" * 70)
    if all_passed:
        print("ALL DATABASE CHECKS PASSED SUCCESSFULLY! (0 failures)")
    else:
        print("SOME CHECKS REPORTED DISCREPANCIES - Review details above.")
    print("=" * 70)


if __name__ == "__main__":
    main()
