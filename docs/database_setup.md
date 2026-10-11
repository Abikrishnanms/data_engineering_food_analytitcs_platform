# FoodFlow — Database Setup & Operational Guide
**Owner:** Lekshmi Priya — Database Engineer  
**Role:** PostgreSQL Architecture, Schema DDL, Constraints, Indexes, and Repeatable Loading

---

## 1. Overview
The database layer serves as the single source of truth for the FoodFlow analytical platform. It models raw entities into strongly typed, relational tables with strict foreign key constraints and validation rules.

Downstream consumers:
- **Swetha (Analytics Engineer):** Builds SQL views, KPIs, and metric models.
- **Athulya (AI / NLQ Engineer):** Translates natural language into safe, read-only analytical queries.
- **Meera (Dashboard Engineer):** Queries views for Streamlit and Plotly charts.

---

## 2. Relational Architecture & Tables

| Table Name | Description | Primary Key | Key Relationships | Row Count |
|---|---|---|---|---:|
| `users` | Customer profiles and demographics | `user_id` | 1-to-many with `orders` | 10,000 |
| `restaurants` | Restaurant details, cuisine, ratings | `restaurant_id` | 1-to-many with `menu`, `orders` | 1,000 |
| `menu` | Food item catalog per restaurant | `menu_id` | Foreign Key to `restaurants` | 15,658 |
| `orders` | Transactional order headers | `order_id` | Foreign Keys to `users`, `restaurants` | 600,000 |
| `order_items` | Individual line items per order | `order_item_id` | Foreign Keys to `orders`, `menu` | 1,667,399 |

---

## 3. Prerequisites & Installation

### Option A: Local PostgreSQL
Make sure PostgreSQL 14+ is installed and the service is running:
- **Windows:** Ensure the PostgreSQL service is started in `services.msc`.
- **macOS / Linux:** `brew services start postgresql` or `systemctl start postgresql`.

### Option B: Docker Container (Recommended for Team)
```bash
docker run --name foodflow-postgres \
  -e POSTGRES_DB=foodflow \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 -d postgres:16-alpine
```

---

## 4. Configuration (`.env`)
Create a `.env` file in the project root (or set OS environment variables):
```env
FOODFLOW_DB_HOST=localhost
FOODFLOW_DB_PORT=5432
FOODFLOW_DB_NAME=foodflow
FOODFLOW_DB_USER=postgres
FOODFLOW_DB_PASSWORD=postgres
```

Ensure Python dependencies are installed:
```bash
pip install psycopg2-binary pandas
```

---

## 5. Execution Order

### Step 1: Create Database
Connect to your PostgreSQL server via `psql` or pgAdmin and create the database if it doesn't already exist:
```sql
CREATE DATABASE foodflow;
```

### Step 2: Run the Automated Loader
You can run the all-in-one loader script which creates the tables, streams the data from `data/raw/` or `Swiggy_Data.zip`, and sets up the indexes:
```bash
python db/load/load_data.py
```

*Note:* Loading ~2.3 million records using the optimized PostgreSQL `COPY` mechanism takes under 30 seconds!

### Step 3: Run Database Verification & Tests
Verify data integrity and constraints using the test script:
```bash
psql -h localhost -U postgres -d foodflow -f tests/test_database.sql
```
All row counts must match expected counts, and orphan/invalid counts must return `0`.

---

## 6. Read-Only Analytics Role Setup
For security and safety, the AI/NLQ engine (Athulya) and reporting queries (Swetha/Meera) should use a dedicated read-only role:

```sql
-- Create read-only role
CREATE ROLE foodflow_analytics WITH LOGIN PASSWORD 'analytics_secure_pass';

-- Grant connection and usage
GRANT CONNECT ON DATABASE foodflow TO foodflow_analytics;
GRANT USAGE ON SCHEMA public TO foodflow_analytics;

-- Grant SELECT only on current and future tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO foodflow_analytics;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO foodflow_analytics;
```
This guarantees that generated natural language queries can never execute `DROP`, `DELETE`, `UPDATE`, or `INSERT` commands.
