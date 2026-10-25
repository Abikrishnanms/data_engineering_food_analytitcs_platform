import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

STATEMENT_TIMEOUT_MS = 10_000  # stop any query that runs longer than 10 seconds
MAX_ROWS = 500                 # never return more than 500 rows


def _connect():
    return psycopg2.connect(
        host=os.getenv("FOODFLOW_DB_HOST") or os.getenv("DB_HOST", "localhost"),
        port=os.getenv("FOODFLOW_DB_PORT") or os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("FOODFLOW_DB_NAME") or os.getenv("DB_NAME", "foodflow"),
        user=os.getenv("FOODFLOW_DB_USER") or os.getenv("DB_USER", "foodflow_analytics"),
        password=os.getenv("FOODFLOW_DB_PASSWORD") or os.getenv("DB_PASSWORD", ""),
        connect_timeout=5,
        options=f"-c statement_timeout={STATEMENT_TIMEOUT_MS}",
    )


def run_query(sql: str):
    """Run one validated SELECT. Returns (columns, rows, truncated)."""
    conn = _connect()
    try:
        conn.set_session(readonly=True, autocommit=True)
        with conn.cursor() as cur:
            cur.execute(sql)
            columns = [d[0] for d in cur.description]
            rows = cur.fetchmany(MAX_ROWS + 1)
        truncated = len(rows) > MAX_ROWS
        return columns, rows[:MAX_ROWS], truncated
    finally:
        conn.close()