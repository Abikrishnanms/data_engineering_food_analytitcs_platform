"""
FoodFlow Analytics Views Deployer
File: db/deploy_views.py

Description:
    Connects to Supabase PostgreSQL and deploys the analytical views,
    KPI summary functions, and business question models in topological order:
    1. sql/analytics/01_base_views.sql
    2. sql/analytics/10_kpis.sql
    3. sql/analytics/20_business_questions.sql
    4. sql/analytics/90_grants.sql
"""

import os
import sys
import time
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

ANALYTICS_DIR = PROJECT_ROOT / "sql" / "analytics"

SCRIPTS = [
    "01_base_views.sql",
    "10_kpis.sql",
    "20_business_questions.sql",
    "90_grants.sql",
]


def deploy_views():
    host = os.getenv("FOODFLOW_DB_HOST")
    port = os.getenv("FOODFLOW_DB_PORT")
    dbname = os.getenv("FOODFLOW_DB_NAME")
    user = os.getenv("FOODFLOW_DB_USER")
    password = os.getenv("FOODFLOW_DB_PASSWORD")

    print("=" * 70)
    print("DEPLOYING ANALYTICAL VIEWS & FUNCTIONS TO SUPABASE POSTGRESQL")
    print(f"Target: {user}@{host}:{port}/{dbname}")
    print("=" * 70)

    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
    )
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            # Disable statement timeout for view creation
            cur.execute("SET statement_timeout = 0;")

            for script_name in SCRIPTS:
                script_path = ANALYTICS_DIR / script_name
                print(f"Executing {script_name}... ", end="", flush=True)
                t0 = time.time()
                sql_content = script_path.read_text(encoding="utf-8")
                cur.execute(sql_content)
                print(f"[OK] in {time.time() - t0:.2f}s")

        print("=" * 70)
        print("ALL ANALYTICAL VIEWS AND FUNCTIONS SUCCESSFULLY DEPLOYED!")
        print("=" * 70)

    finally:
        conn.close()


if __name__ == "__main__":
    deploy_views()
