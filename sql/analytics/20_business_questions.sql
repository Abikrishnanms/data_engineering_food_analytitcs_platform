-- =============================================================================
-- FoodFlow Analytics - Business Question Views and Functions
-- File: sql/analytics/20_business_questions.sql
-- Depends on: 01_base_views.sql, 10_kpis.sql
--
-- Every object answers one named business question. "Qualifying" = Delivered.
-- Month-grain views are for charts; use the fn_* functions for arbitrary date
-- ranges (they re-aggregate correctly instead of summing ranks or ratios).
-- =============================================================================

DROP FUNCTION IF EXISTS fn_top_restaurants(date, date, int);
DROP FUNCTION IF EXISTS fn_top_items(date, date, int);
DROP VIEW IF EXISTS v_q01_weekly_orders_trend        CASCADE;
DROP VIEW IF EXISTS v_q02_restaurant_monthly_ranking CASCADE;
DROP VIEW IF EXISTS v_q03_item_monthly_performance   CASCADE;
DROP VIEW IF EXISTS v_q04_status_mix_monthly         CASCADE;
DROP VIEW IF EXISTS v_q05_customer_orders            CASCADE;
DROP VIEW IF EXISTS v_q05_repeat_customer_summary    CASCADE;
DROP VIEW IF EXISTS v_q06_basket_size_monthly        CASCADE;
DROP VIEW IF EXISTS v_q07_cuisine_mix_monthly        CASCADE;
DROP VIEW IF EXISTS v_q08_payment_mix_monthly        CASCADE;
DROP VIEW IF EXISTS v_q09_orders_by_recorded_hour    CASCADE;
DROP VIEW IF EXISTS v_q10_city_revenue_monthly       CASCADE;

-- -----------------------------------------------------------------------------
-- Q1. How many orders were placed each week, and what changed week-over-week?
-- Note: Monday-based weeks. First (2021-12-27) and last weeks are partial.
-- (Daily trend: use v_kpi_daily.)
-- -----------------------------------------------------------------------------
CREATE VIEW v_q01_weekly_orders_trend AS
WITH weekly AS (
    SELECT order_week                                  AS week_start,
           COUNT(*)                                    AS total_orders,
           COUNT(*) FILTER (WHERE is_qualifying)       AS qualifying_orders,
           SUM(qualifying_revenue)                     AS qualifying_revenue
    FROM v_orders_enriched
    GROUP BY order_week
)
SELECT week_start,
       total_orders,
       qualifying_orders,
       qualifying_revenue,
       LAG(total_orders) OVER w                        AS prev_week_orders,
       ROUND(100.0 * (total_orders - LAG(total_orders) OVER w)
             / NULLIF(LAG(total_orders) OVER w, 0), 2) AS wow_change_pct
FROM weekly
WINDOW w AS (ORDER BY week_start);

-- -----------------------------------------------------------------------------
-- Q2. Which restaurants have the highest qualifying revenue in each month?
-- Top 5 for a month: SELECT * FROM v_q02_restaurant_monthly_ranking
--                    WHERE order_month = '2025-06-01' AND revenue_rank <= 5;
-- -----------------------------------------------------------------------------
CREATE VIEW v_q02_restaurant_monthly_ranking AS
SELECT order_month,
       restaurant_id,
       restaurant_name,
       city,
       cuisine,
       COUNT(*)                                        AS qualifying_orders,
       SUM(total_amount)                               AS qualifying_revenue,
       RANK() OVER (PARTITION BY order_month
                    ORDER BY SUM(total_amount) DESC)   AS revenue_rank
FROM v_orders_enriched
WHERE is_qualifying
GROUP BY order_month, restaurant_id, restaurant_name, city, cuisine;

-- fn_top_restaurants: top N restaurants for ANY inclusive date range.
CREATE FUNCTION fn_top_restaurants(p_start date, p_end date, p_limit int DEFAULT 5)
RETURNS TABLE (
    revenue_rank       bigint,
    restaurant_id      varchar,
    restaurant_name    varchar,
    city               varchar,
    cuisine            varchar,
    qualifying_orders  bigint,
    qualifying_revenue numeric
)
LANGUAGE sql STABLE AS $$
    SELECT RANK() OVER (ORDER BY SUM(total_amount) DESC),
           restaurant_id, restaurant_name, city, cuisine,
           COUNT(*), SUM(total_amount)
    FROM v_orders_enriched
    WHERE is_qualifying AND order_date BETWEEN p_start AND p_end
    GROUP BY restaurant_id, restaurant_name, city, cuisine
    ORDER BY 1, restaurant_id
    LIMIT p_limit
$$;

-- -----------------------------------------------------------------------------
-- Q3. Which menu items sell the most (units and revenue) each month?
-- -----------------------------------------------------------------------------
CREATE VIEW v_q03_item_monthly_performance AS
SELECT order_month,
       menu_id,
       item_name,
       category,
       is_veg,
       restaurant_id,
       restaurant_name,
       SUM(quantity)                    AS units_sold,
       SUM(line_revenue)                AS qualifying_revenue,
       COUNT(DISTINCT order_id)         AS qualifying_orders
FROM v_order_items_enriched
WHERE is_qualifying
GROUP BY order_month, menu_id, item_name, category, is_veg, restaurant_id, restaurant_name;

-- fn_top_items: top N items by units sold for ANY inclusive date range.
CREATE FUNCTION fn_top_items(p_start date, p_end date, p_limit int DEFAULT 10)
RETURNS TABLE (
    units_rank         bigint,
    menu_id            varchar,
    item_name          varchar,
    category           varchar,
    restaurant_name    varchar,
    units_sold         bigint,
    qualifying_revenue numeric
)
LANGUAGE sql STABLE AS $$
    SELECT RANK() OVER (ORDER BY SUM(quantity) DESC),
           menu_id, item_name, category, restaurant_name,
           SUM(quantity)::bigint, SUM(line_revenue)
    FROM v_order_items_enriched
    WHERE is_qualifying AND order_date BETWEEN p_start AND p_end
    GROUP BY menu_id, item_name, category, restaurant_name
    ORDER BY 1, menu_id
    LIMIT p_limit
$$;

-- -----------------------------------------------------------------------------
-- Q4. What share of orders is Delivered vs Cancelled each month?
-- -----------------------------------------------------------------------------
CREATE VIEW v_q04_status_mix_monthly AS
SELECT order_month,
       order_status,
       COUNT(*)                                                     AS orders,
       ROUND(COUNT(*)::numeric
             / SUM(COUNT(*)) OVER (PARTITION BY order_month), 4)    AS share_of_orders
FROM v_orders_enriched
GROUP BY order_month, order_status;

-- -----------------------------------------------------------------------------
-- Q5. Who are the repeat customers? (qualifying orders only)
-- Repeat customer = 2 or more qualifying orders.
-- -----------------------------------------------------------------------------
CREATE VIEW v_q05_customer_orders AS
SELECT user_id,
       COUNT(*)                         AS qualifying_orders,
       SUM(total_amount)                AS qualifying_revenue,
       MIN(order_date)                  AS first_order_date,
       MAX(order_date)                  AS last_order_date,
       (COUNT(*) >= 2)                  AS is_repeat_customer
FROM v_orders_enriched
WHERE is_qualifying
GROUP BY user_id;

CREATE VIEW v_q05_repeat_customer_summary AS
SELECT COUNT(*)                                             AS customers,
       COUNT(*) FILTER (WHERE is_repeat_customer)           AS repeat_customers,
       ROUND(COUNT(*) FILTER (WHERE is_repeat_customer)::numeric
             / NULLIF(COUNT(*), 0), 4)                      AS repeat_rate,
       ROUND(AVG(qualifying_orders), 2)                     AS avg_orders_per_customer
FROM v_q05_customer_orders;

-- -----------------------------------------------------------------------------
-- Q6. How large is a typical basket each month? (qualifying orders)
-- -----------------------------------------------------------------------------
CREATE VIEW v_q06_basket_size_monthly AS
SELECT order_month,
       COUNT(*)                                  AS qualifying_orders,
       ROUND(AVG(item_lines), 2)                 AS avg_item_lines_per_order,
       ROUND(AVG(total_units), 2)                AS avg_units_per_order,
       ROUND(AVG(total_amount), 2)               AS avg_order_value
FROM v_orders_enriched
WHERE is_qualifying
GROUP BY order_month;

-- -----------------------------------------------------------------------------
-- Q7. Which cuisines earn the most revenue each month?
-- -----------------------------------------------------------------------------
CREATE VIEW v_q07_cuisine_mix_monthly AS
SELECT order_month,
       cuisine,
       COUNT(*)                                                   AS qualifying_orders,
       SUM(total_amount)                                          AS qualifying_revenue,
       ROUND(SUM(total_amount)
             / SUM(SUM(total_amount)) OVER (PARTITION BY order_month), 4) AS revenue_share
FROM v_orders_enriched
WHERE is_qualifying
GROUP BY order_month, cuisine;

-- -----------------------------------------------------------------------------
-- Q8. How are orders split across payment methods each month? (all orders)
-- -----------------------------------------------------------------------------
CREATE VIEW v_q08_payment_mix_monthly AS
SELECT order_month,
       payment_method,
       COUNT(*)                                                   AS total_orders,
       COUNT(*) FILTER (WHERE is_qualifying)                      AS qualifying_orders,
       ROUND(COUNT(*)::numeric
             / SUM(COUNT(*)) OVER (PARTITION BY order_month), 4)  AS share_of_orders
FROM v_orders_enriched
GROUP BY order_month, payment_method;

-- -----------------------------------------------------------------------------
-- Q9. At what time of day are orders recorded?
-- LIMITATION: recorded_hour comes from delivery_time (a clock time).
-- It shows WHEN activity is recorded, never HOW LONG delivery took.
-- -----------------------------------------------------------------------------
CREATE VIEW v_q09_orders_by_recorded_hour AS
SELECT recorded_hour,
       COUNT(*)                                  AS total_orders,
       COUNT(*) FILTER (WHERE is_qualifying)     AS qualifying_orders
FROM v_orders_enriched
GROUP BY recorded_hour;

-- -----------------------------------------------------------------------------
-- Q10. Which cities earn the most revenue each month?
-- -----------------------------------------------------------------------------
CREATE VIEW v_q10_city_revenue_monthly AS
SELECT order_month,
       city,
       COUNT(*)                          AS qualifying_orders,
       SUM(total_amount)                 AS qualifying_revenue
FROM v_orders_enriched
WHERE is_qualifying
GROUP BY order_month, city;
