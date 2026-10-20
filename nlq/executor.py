import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

STATEMENT_TIMEOUT_MS = 10_000  # stop any query that runs longer than 10 seconds
MAX_ROWS = 500                 # never return more than 500 rows


def _connect():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "foodflow"),
        user=os.getenv("DB_USER", "foodflow_analytics"),
        password=os.getenv("DB_PASSWORD", ""),
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