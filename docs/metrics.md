# FoodFlow - Metric Definitions & Analytics Contract

**Owner:** Swetha - Analytics Engineer
**Status:** v1.0 - ready for contract review with Meera (dashboard) and Athulya (NLQ)
**Verified on:** full dataset, 600,000 orders, PostgreSQL 16, 29/29 checks in `tests/test_analytics.sql` pass

Everything downstream (dashboard, NLQ) reads **only** the views and functions listed here, never the raw tables.

---

## 1. Core decisions (please approve in the contract review)

| # | Decision | Reason (verified on the data) |
|---|---|---|
| D1 | **Qualifying order = `order_status = 'Delivered'`** | Only two statuses exist: Delivered (570,281) and Cancelled (29,719). Cancelled orders still carry a `total_amount` (about 20.8M), so they must not count as revenue. |
| D2 | **Revenue = `orders.total_amount`** of qualifying orders | `total_amount` equals `SUM(quantity * price)` of its items for **all 600,000 orders** (0 differences), so order-level and item-level revenue agree exactly. |
| D3 | **`order_items.price` is a unit price** | Proven by D2: `quantity * price` reconciles to the order total. Item revenue = `quantity * unit_price`. |
| D4 | **Date field = `order_date`** | Dates run 2022-01-01 to 2025-12-31. |
| D5 | **Weeks start on Monday** | PostgreSQL `DATE_TRUNC('week')`. First and last weeks are partial. |
| D6 | **Currency is not stated in the data.** Label money as "amount" or use the symbol the team agrees on | The CSVs have no currency column. Do not assume. |

Not available, so never claimed: driver performance, driver distance, delivery duration (`delivery_time` is a clock time).

---

## 2. KPI definitions

| KPI | Plain-language meaning | Formula | Source |
|---|---|---|---|
| Total orders | All orders placed, any status | `COUNT(*)` of orders | `v_kpi_*`, `fn_kpi_summary` |
| Qualifying orders | Orders that were delivered | `COUNT(*) WHERE is_qualifying` | same |
| Cancelled orders | Orders cancelled | `COUNT(*) WHERE NOT is_qualifying` | same |
| **Qualifying revenue** | Money from delivered orders | `SUM(total_amount)` of qualifying orders | same |
| **Average order value (AOV)** | Typical delivered-order size | qualifying revenue / qualifying orders | same |
| Cancellation rate | Share of orders cancelled | cancelled orders / total orders | same |
| Active restaurants | Restaurants with at least 1 qualifying order in the period | `COUNT(DISTINCT restaurant_id)` of qualifying orders | `v_kpi_monthly/overall`, `fn_kpi_summary` |
| Active customers | Customers with at least 1 qualifying order in the period | `COUNT(DISTINCT user_id)` of qualifying orders | same |

**Reference values (whole dataset):** 600,000 orders, 570,281 qualifying, qualifying revenue **396,159,910.39**, AOV **694.67**, cancellation rate **4.95%**.

> **Rule for the dashboard:** ratios (AOV, cancellation rate) and distinct counts are **not additive**. For a user-chosen date range, call `fn_kpi_summary(start, end)`. Do **not** sum or average the daily/monthly rows in Python.

---

## 3. The analytics contract

### 3.1 Base views (the only place raw tables are joined)

**`v_orders_enriched`** - grain: **one row per order** (600,000). Safe to `COUNT(*)` for orders.

| Column | Type | Meaning |
|---|---|---|
| order_id, user_id, restaurant_id | text | keys |
| restaurant_name, city, cuisine | text | restaurant attributes |
| order_date | date | order date |
| order_week | date | Monday of the order's week |
| order_month | date | first day of the order's month |
| recorded_hour | int | clock hour of `delivery_time` (0-23). **Not a duration.** |
| order_status | text | Delivered / Cancelled |
| is_qualifying | boolean | true when Delivered |
| payment_method | text | UPI, Credit Card, Debit Card, Cash on Delivery, Wallet |
| total_amount | numeric | recorded order total, any status |
| qualifying_revenue | numeric | `total_amount` if Delivered, else 0 |
| item_lines | int | number of item lines in the order |
| total_units | int | sum of item quantities |

**`v_order_items_enriched`** - grain: **one row per order line** (1,667,399). Do **not** `COUNT(*)` this for orders; use `COUNT(DISTINCT order_id)`.

| Column | Type | Meaning |
|---|---|---|
| order_item_id, order_id | text | keys |
| order_date, order_month | date | from the order |
| order_status, is_qualifying | text, boolean | from the order |
| restaurant_id, restaurant_name, city, cuisine | text | restaurant attributes |
| menu_id, item_name, category | text | menu item |
| is_veg | boolean | vegetarian item |
| quantity | int | units on the line |
| unit_price | numeric | price per unit |
| line_revenue | numeric | `quantity * unit_price` |

### 3.2 KPI views and function

| Object | Grain / use | Columns |
|---|---|---|
| `v_kpi_daily` | one row per day - daily trend | order_date, total_orders, qualifying_orders, cancelled_orders, qualifying_revenue, avg_order_value, cancellation_rate |
| `v_kpi_monthly` | one row per month | order_month, total_orders, qualifying_orders, cancelled_orders, qualifying_revenue, avg_order_value, cancellation_rate, active_restaurants, active_customers |
| `v_kpi_overall` | single row | the KPIs above plus first_order_date, last_order_date |
| `fn_kpi_summary(start, end)` | **KPI cards for any date range**, inclusive, always returns 1 row | total_orders, qualifying_orders, cancelled_orders, qualifying_revenue, avg_order_value, cancellation_rate, active_restaurants, active_customers |

### 3.3 Business questions

| # | Question | Object | Key columns |
|---|---|---|---|
| Q0 | What is the daily order trend? | `v_kpi_daily` | order_date, total_orders, qualifying_revenue |
| Q1 | Orders per week and week-over-week change? | `v_q01_weekly_orders_trend` | week_start, total_orders, prev_week_orders, wow_change_pct |
| Q2 | Top restaurants by qualifying revenue? | `v_q02_restaurant_monthly_ranking` (per month, filter `revenue_rank <= N`) or **`fn_top_restaurants(start, end, n)`** (any range) | revenue_rank, restaurant_name, city, cuisine, qualifying_orders, qualifying_revenue |
| Q3 | Top menu items by units sold? | `v_q03_item_monthly_performance` or **`fn_top_items(start, end, n)`** | item_name, category, restaurant_name, units_sold, qualifying_revenue |
| Q4 | Delivered vs cancelled share per month? | `v_q04_status_mix_monthly` | order_month, order_status, orders, share_of_orders |
| Q5 | Who are the repeat customers? | `v_q05_customer_orders`, `v_q05_repeat_customer_summary` | qualifying_orders, is_repeat_customer, repeat_rate |
| Q6 | How big is a basket? | `v_q06_basket_size_monthly` | avg_item_lines_per_order, avg_units_per_order, avg_order_value |
| Q7 | Revenue mix by cuisine? | `v_q07_cuisine_mix_monthly` | cuisine, qualifying_revenue, revenue_share |
| Q8 | Payment-method mix? | `v_q08_payment_mix_monthly` | payment_method, total_orders, share_of_orders |
| Q9 | At what time of day are orders recorded? | `v_q09_orders_by_recorded_hour` | recorded_hour, total_orders |
| Q10 | Revenue by city? | `v_q10_city_revenue_monthly` | city, qualifying_orders, qualifying_revenue |

**Example queries**

```sql
-- KPI cards for June 2025
SELECT * FROM fn_kpi_summary('2025-06-01', '2025-06-30');

-- Top 5 restaurants by qualifying revenue in June 2025
SELECT * FROM fn_top_restaurants('2025-06-01', '2025-06-30', 5);

-- Top 10 items by units sold in 2025
SELECT * FROM fn_top_items('2025-01-01', '2025-12-31', 10);

-- Week-over-week order change
SELECT week_start, total_orders, wow_change_pct
FROM v_q01_weekly_orders_trend ORDER BY week_start;
```

---

## 4. Limitations and honest notes

1. **No driver data and no delivery duration.** `recorded_hour` only shows *when* activity is recorded.
2. **Repeat-customer rate is 100%.** Every one of the 10,000 customers has at least 2 qualifying orders (average 57), so "repeat vs one-time" is not informative on this dataset. Use `qualifying_orders` per customer (frequency) instead, or treat Q5 as a data observation, not a business insight.
3. **Item-level monthly numbers are small** (the top item in June 2025 sold 16 units). For item rankings, prefer `fn_top_items` over a wider date range than one month.
4. **Revenue is the recorded `total_amount`.** The data has no separate tax, discount or fee columns, so none are modelled.
5. **Ties:** `RANK()` gives tied rows the same rank, so `fn_top_*` can return the requested number of rows but may show shared ranks.
6. **Performance (local, full data):** `fn_kpi_summary` for one year about 0.2 s; `v_kpi_monthly` about 1.2 s (distinct counts over 600k orders). Meera should cache these queries.

---

## 5. How to run and test

```bash
# from project root, after the database is loaded (docs/database_setup.md)
psql -h localhost -U postgres -d foodflow -f sql/analytics/01_base_views.sql
psql -h localhost -U postgres -d foodflow -f sql/analytics/10_kpis.sql
psql -h localhost -U postgres -d foodflow -f sql/analytics/20_business_questions.sql
psql -h localhost -U postgres -d foodflow -f sql/analytics/90_grants.sql   # needs foodflow_analytics role
psql -h localhost -U postgres -d foodflow -f tests/test_analytics.sql      # every is_pass must be true
```

Run order matters: re-running `01` drops everything that depends on it, so re-run all files in order.
`90_grants.sql` revokes the role's access to the raw tables and grants it only the views/functions above.

---

## 6. Versioning rule

Column names and metric definitions above are a contract. Renaming a column, changing a view's grain, or changing a definition (for example, which statuses qualify) must be announced to Meera, Athulya and Abikrishnan **before** merging, and recorded in the decisions log.

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-10-13 | First published contract |
