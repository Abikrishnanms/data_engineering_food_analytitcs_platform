"""
FoodFlow Analytics — FastAPI Backend Service
File: backend/main.py

Description:
    Production FastAPI application providing REST API endpoints for the
    FoodFlow React frontend. Bridges the React UI to Supabase PostgreSQL
    and executes the safe Natural Language Query (NLQ) engine.
"""

import sys
import time
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.data_access import (
    fetch_kpi_summary,
    fetch_daily_kpis,
    fetch_top_restaurants,
    fetch_top_items,
    fetch_cuisine_mix,
    fetch_payment_mix,
    fetch_hourly_orders,
)
from nlq.service import ask

app = FastAPI(
    title="FoodFlow Analytics & NLQ API",
    description="High-performance analytical API serving Supabase cloud data & safe Natural Language Queries.",
    version="2.0.0",
)

# Enable CORS for React development and preview servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NLQRequest(BaseModel):
    question: str


@app.get("/api/health")
def health_check():
    """Verify backend and database connection status."""
    return {
        "status": "healthy",
        "service": "FoodFlow Analytics API",
        "database": "Supabase PostgreSQL Cloud",
        "version": "2.0.0",
    }


@app.get("/api/kpis")
def get_kpis(
    start_date: str = Query("2025-01-01", description="Start date YYYY-MM-DD"),
    end_date: str = Query("2025-12-31", description="End date YYYY-MM-DD"),
):
    """Fetch non-additive business KPI summary for specified date window."""
    try:
        return fetch_kpi_summary(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trends/daily")
def get_daily_trends(
    start_date: str = Query("2025-01-01", description="Start date YYYY-MM-DD"),
    end_date: str = Query("2025-12-31", description="End date YYYY-MM-DD"),
):
    """Fetch daily time-series of total orders, qualifying revenue, and cancellation rates."""
    try:
        return fetch_daily_kpis(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/restaurants/top")
def get_top_restaurants(
    start_date: str = Query("2025-01-01", description="Start date YYYY-MM-DD"),
    end_date: str = Query("2025-12-31", description="End date YYYY-MM-DD"),
    limit: int = Query(5, ge=1, le=50, description="Top N restaurants"),
):
    """Fetch top grossing partner restaurants."""
    try:
        return fetch_top_restaurants(start_date, end_date, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/menu/top")
def get_top_menu_items(
    start_date: str = Query("2025-01-01", description="Start date YYYY-MM-DD"),
    end_date: str = Query("2025-12-31", description="End date YYYY-MM-DD"),
    limit: int = Query(8, ge=1, le=50, description="Top N items"),
):
    """Fetch best selling menu items by volume."""
    try:
        return fetch_top_items(start_date, end_date, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cuisines/mix")
def get_cuisine_mix():
    """Fetch revenue distribution by cuisine."""
    try:
        return fetch_cuisine_mix()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/payments/mix")
def get_payment_mix():
    """Fetch distribution of payment methods."""
    try:
        return fetch_payment_mix()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hourly")
def get_hourly_orders():
    """Fetch 24-hour order traffic patterns."""
    try:
        return fetch_hourly_orders()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/nlq")
def handle_natural_language_query(payload: NLQRequest):
    """
    Translates plain-English business questions into safe, read-only SQL,
    validates against AST and allowlist rules, and executes against Supabase.
    """
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    t0 = time.time()
    try:
        res = ask(payload.question.strip())
        duration_ms = round((time.time() - t0) * 1000, 2)

        status = res.get("status", "ok")
        answer = res.get("answer", "")
        sql_query = res.get("sql")
        columns = res.get("columns", [])
        raw_rows = res.get("rows", [])
        warning = res.get("warning")

        # Clean decimals and tuples into JSON dictionaries
        clean_data = []
        for row in raw_rows:
            item_dict = {}
            for col, val in zip(columns, row):
                if isinstance(val, Decimal):
                    item_dict[col] = float(val)
                else:
                    item_dict[col] = val
            clean_data.append(item_dict)

        return {
            "status": status,
            "answer": answer,
            "sql": sql_query,
            "columns": columns,
            "data": clean_data,
            "warning": warning,
            "duration_ms": duration_ms,
        }
    except Exception as e:
        return {
            "status": "error",
            "answer": f"Execution error: {str(e)}",
            "sql": None,
            "columns": [],
            "data": [],
            "duration_ms": round((time.time() - t0) * 1000, 2),
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
