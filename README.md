# FoodFlow — Enterprise Food Delivery Lakehouse & Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![Supabase](https://img.shields.io/badge/Supabase-Cloud%20Postgres%20%26%20Storage-3ECF8E.svg?logo=supabase&logoColor=white)](https://supabase.com/)
[![DuckDB](https://img.shields.io/badge/DuckDB-Data%20Marts-FFF000.svg?logo=duckdb&logoColor=black)](https://duckdb.org/)
[![Tests](https://img.shields.io/badge/Tests-46%20Passed-success.svg)](tests/)
[![Data Scale](https://img.shields.io/badge/Data%20Scale-2.29M%2B%20Records-blue.svg)](#relational-data-scale)

---

## 1. Project Description — What is FoodFlow?

**FoodFlow** is an end-to-end cloud data engineering, lakehouse, and conversational business intelligence platform built to process, model, and analyze **2,294,057 real-world food delivery transactions** spanning 2022 to 2025.

FoodFlow eliminates common data engineering failure modes—such as data drift, row-multiplying joins, unindexed slow aggregations, and unsafe text-to-SQL generation. The platform features:

* **Production Data Scale:** 2.29M+ rows across 5 normalized relational entities (`users`, `restaurants`, `menu`, `orders`, `order_items`).
* **Automated 3-Stage ETL Pipeline:** Raw ingestion, 16 automated quality gates, and canonical data standardization.
* **Medallion Cloud Lakehouse on Supabase Storage:** Multi-tier object storage architecture (Bronze &rarr; Silver &rarr; Gold) achieving a **73.1% storage reduction**.
* **Supabase Cloud PostgreSQL Warehouse:** Relational database optimized with 14 B-Tree performance indexes and analytical views.
* **Strict Analytics Contract:** Prevents invalid metrics (such as "averaging averages") by calculating non-additive ratios dynamically via stored procedures (`fn_kpi_summary`).
* **Safe Natural Language Query (NLQ) Engine:** Plain-English queries compiled into read-only SQL validated against an Abstract Syntax Tree (AST) parser.
* **Executive React 19 Dashboard:** High-performance, clean UI styled exclusively in a professional **Blue & White** theme.

---

## 2. The Automated ETL Pipeline (`src/`)

Raw multi-table CSV files undergo an automated, three-phase data engineering workflow:

```
[ Raw CSV Files (2.29M Rows) ]
              │
              ▼
[ Phase 1: Ingestion & Schema Profiling (src/ingestion/profile_data.py) ]
  • Analyzes column types, null percentages, cardinality & primary key uniqueness
              │
              ▼
[ Phase 2: Data Quality Gates (src/quality/validate_data.py) ]
  • Executes 16 automated validation checks (FK integrity, price >= 0, status enums)
              │
              ▼
[ Phase 3: Normalization & Transformation (src/transform/transform_data.py) ]
  • Standardizes ISO timestamps, trims whitespace, casts boolean flags & generates clean CSVs
```

---

## 3. Cloud Lakehouse & Supabase Infrastructure

```
┌────────────────────────────────────────────────────────────────────────┐
│             MEDALLION DATA LAKE (Supabase Cloud Storage)               │
│                                                                        │
│  • Bronze Tier (foodflow-bronze) : Raw immutable CSVs with transparent │
│    gzip compression for payloads > 45MB (e.g., order_items.csv.gz)     │
│                                                                        │
│  • Silver Tier (foodflow-silver) : Snappy-compressed Apache Parquet    │
│    tables (reduces storage by 73.1%: 98.24 MB CSV ➔ 26.46 MB Parquet)  │
│                                                                        │
│  • Gold Tier (foodflow-gold)     : Vectorized DuckDB data marts        │
│    (kpi_daily.parquet, restaurant_monthly.parquet, cuisine_perf.parquet│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│           CLOUD POSTGRESQL SERVING LAYER (Supabase AWS Tokyo)          │
│  • 2,294,057 verified records loaded via streaming bulk COPY           │
│  • 14 B-Tree composite performance indexes on foreign keys & dates     │
│  • Pre-aggregated analytical views (v_kpi_daily, v_orders_enriched)    │
│  • Non-additive stored procedures (fn_kpi_summary, fn_top_restaurants) │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│              FASTAPI REST BACKEND SERVICE (backend/main.py)            │
│  • High-throughput endpoints: /api/kpis, /api/trends, /api/nlq         │
│  • Enforces SQL statement timeouts & read-only execution roles         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Analytics Contract & Safe NLQ Engine

1. **Analytics Contract (Non-Additive Ratios):**
   Cancellation rates and Average Order Values (AOV) are mathematically non-additive across time windows. The backend prohibits averaging daily rates; all window aggregations invoke `fn_kpi_summary(start_date, end_date)`.
2. **Zero Direct Table Scans:** Downstream consumers never query raw tables (`orders`, `order_items`) directly. All requests pass through pre-aggregated views.
3. **5-Tier Safe NLQ Pipeline:**
   ```
   User Question: "Top 3 restaurants in June 2025"
         │
         ▼
   [ Tier 1: Regex Guardrail ] ──> Blocks DDL/DML (DROP, DELETE, UPDATE)
         │
         ▼
   [ Tier 2: Translation ]     ──> Compiles intent into single SELECT statement
         │
         ▼
   [ Tier 3: AST Validator ]   ──> Rejects multi-statements & enforces View Allowlist
         │
         ▼
   [ Tier 4: DB Execution ]    ──> Executes under read-only role with 10s timeout cap
         │
         ▼
   [ Tier 5: Auditable UI ]    ──> Clean tabular output + transparent "Inspect SQL"
   ```

---

## 5. Executive Dashboard Showcase

The user interface is an executive, high-performance single-page application built with **React 19**, **Vite**, and **Lucide React**, styled with a curated, distraction-free **Blue and White** theme.

### View 1: Executive Dashboard & Multi-Year Toolbar
![Executive KPI Cards & Toolbar](docs/screenshots/01_executive_kpis.png)
* **1-Click Multi-Year Switcher:** Instantly filter across `2025`, `2024`, `2023`, `2022`, or `All Years (2022–2025)`.
* **Dynamic Period Presets:** Responsive buttons for `Full Year`, `Q1`, `Q2`, `Q3`, `Q4`, and individual months.
* **8 Core Business KPI Cards:** Live calculations via `fn_kpi_summary`: Gross Orders, Delivered Orders, Cancelled Orders, Cancellation Rate (%), Total Revenue (₹), AOV, Active Restaurants, and Active Customers.

---

### View 2: Daily Operational Trends (365-Day Time Series)
![Daily Operational Trends](docs/screenshots/02_daily_trends.png)
* **Interactive SVG Visualization:** Smooth gradient area and line graph tracking day-by-day operations across all 365 calendar days.
* **Dual Metric Toggle:** Switch between **Order Volume** and **Qualifying Revenue (₹)** with hover crosshair tooltips displaying exact day-level volume, revenue, and cancellation rates.
* **Summary Highlights:** Displays daily average volume, peak volume dates, and active calendar days.

---

### View 3: Natural Language Query (NLQ) Laboratory
![Ask FoodFlow NLQ Laboratory](docs/screenshots/03_nlq_query_engine.png)
* **Conversational AI Analytics:** Plain-English questions (*e.g., "Top 3 restaurants in June 2025"*) compiled into audited SQL in ~1.1 seconds.
* **Transparent SQL Inspection:** Monospace code container with one-click copy-to-clipboard.
* **Formatted Output Table:** Displays query records with clean integer ranks (`1`, `2`, `3`) and formatted monetary amounts (`₹22,306.18`).

---

### View 4: Channel Distributions & 24-Hour Traffic Pattern
![Channel Distributions and 24h Traffic Pattern](docs/screenshots/04_distributions_traffic.png)
* **Cuisine Revenue Share:** Top 8 cuisine contributions (Seafood, Beverages, Italian, Continental, Desserts, Thai, Chinese, Cafe) with percentage progress bars.
* **Payment Methods Breakdown:** Distribution across UPI (40.1%), Credit Card (25.0%), Debit Card (15.0%), Cash on Delivery (10.0%), and Wallets (10.0%).
* **24-Hour Traffic Pattern:** Hourly volume distribution highlighting lunch (12:00–14:00) and dinner (19:00–22:00) order peaks.

---

## 6. Relational Data Scale

| Entity | Exact Records | Primary Key | Key Attributes |
|:---|---:|:---|:---|
| **`users`** | 10,000 | `user_id` | `age`, `gender`, `occupation`, `marital_status` |
| **`restaurants`** | 1,000 | `restaurant_id` | `restaurant_name`, `city`, `cuisine`, `rating` (0.0–5.0) |
| **`menu`** | 15,658 | `menu_id` | `item_name`, `category`, `price`, `is_veg` |
| **`orders`** | 600,000 | `order_id` | `order_date` (2022–2025), `order_status`, `total_amount`, `payment_method` |
| **`order_items`** | 1,667,399 | `order_item_id` | `quantity`, `price` |
| **Total Scale** | **2,294,057** | — | **100% referential integrity across all relationships** |

---

## 7. Quick Start Guide

### Step 1: Configure Environment Variables
Copy `.env.example` to `.env` and provide your Supabase PostgreSQL credentials:
```ini
FOODFLOW_DB_HOST=aws-0-ap-northeast-1.pooler.supabase.com
FOODFLOW_DB_PORT=6543
FOODFLOW_DB_NAME=postgres
FOODFLOW_DB_USER=postgres.your_project_ref
FOODFLOW_DB_PASSWORD=your_supabase_password
SUPABASE_URL=https://your_project_ref.supabase.co
SUPABASE_KEY=your_supabase_service_role_key
```

### Step 2: Start the FastAPI Backend API
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
API Swagger documentation is live at `http://127.0.0.1:8000/docs`.

### Step 3: Start the React Frontend
```powershell
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser to access the executive dashboard.

---

## 8. Repository Structure

```
data_engineering_food_analytics_platform/
├── backend/                         # FastAPI REST Service Layer
│   ├── main.py                      # Endpoints (/api/kpis, /api/trends, /api/nlq)
│   └── data_access.py               # SQLAlchemy queries over Supabase analytical views
│
├── frontend/                        # React 19 Executive UI (Blue & White Theme)
│   ├── src/components/              # Header, KpiCards, DailyTrendChart, TopRankings, NlqSection
│   ├── src/App.jsx                  # Main dashboard assembly and parallel data fetching
│   └── vite.config.js               # Reverse-proxy configuration to FastAPI (/api)
│
├── src/lakehouse/                   # Medallion Data Lake on Supabase Storage
│   ├── ingest_bronze.py             # Raw CSV ingestion with auto-gzip (>45MB)
│   ├── build_silver.py              # Snappy Parquet conversion (73.1% size reduction)
│   ├── build_gold.py                # DuckDB analytical data mart creation
│   └── run_lakehouse.py             # Unified medallion orchestration runner
│
├── db/                              # Supabase PostgreSQL Database Layer
│   ├── schema/                      # DDL: Tables, constraints, and 14 B-Tree indexes
│   ├── load/load_data.py            # High-speed binary streaming COPY bulk loader
│   └── deploy_views.py              # Analytical views and stored procedure deployer
│
├── nlq/                             # Safe Natural Language Query Engine
│   ├── service.py                   # Central query coordinator
│   ├── validator.py                 # AST safety validator & view allowlist gate
│   └── rules.py                     # Deterministic offline SQL translation rules
│
└── tests/                           # Automated Quality & Reconciliation Suites
    ├── run_tests.py                 # 16 database constraint verifications (all pass)
    └── test_nlq.py                  # 30 automated NLQ behavior and safety tests
```
