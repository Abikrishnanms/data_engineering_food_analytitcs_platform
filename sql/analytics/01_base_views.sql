-- =============================================================================
-- FoodFlow Analytics - Base Views
-- File: sql/analytics/01_base_views.sql
-- Run order: 01 -> 10 -> 20 -> 90 (re-running 01 drops dependent views; re-run all)
--
-- These two views are the ONLY place where raw tables are joined.
-- Dashboard and NLQ code must read views, never raw tables.
-- Metric definitions: docs/metrics.md
-- =============================================================================

DROP VIEW IF EXISTS v_order_items_enriched CASCADE;
DROP VIEW IF EXISTS v_orders_enriched CASCADE;

-- -----------------------------------------------------------------------------
-- v_orders_enriched
-- GRAIN: one row per order (600,000 rows). Safe to COUNT(*) for orders.
-- Item information is pre-aggregated to order level BEFORE joining, so orders
-- are never multiplied by their item lines.
-- -----------------------------------------------------------------------------
CREATE VIEW v_orders_enriched AS
WITH item_totals AS (
    SELECT order_id,
           COUNT(*)              AS item_lines,
           SUM(quantity)         AS total_units
    FROM order_items
    GROUP BY order_id
)
SELECT
    o.order_id,
    o.user_id,
    o.restaurant_id,
    r.restaurant_name,
    r.city,
    r.cuisine,
    o.order_date,
    DATE_TRUNC('week',  o.order_date)::date           AS order_week,   -- Monday
    DATE_TRUNC('month', o.order_date)::date           AS order_month,  -- 1st of month
    EXTRACT(HOUR FROM o.delivery_time)::int           AS recorded_hour, -- clock hour, NOT duration
    o.order_status,
    (o.order_status = 'Delivered')                    AS is_qualifying,
    o.payment_method,
    o.total_amount,
    CASE WHEN o.order_status = 'Delivered'
         THEN o.total_amount ELSE 0 END               AS qualifying_revenue,
    COALESCE(it.item_lines, 0)                        AS item_lines,
    COALESCE(it.total_units, 0)                       AS total_units
FROM orders o
JOIN restaurants r        ON r.restaurant_id = o.restaurant_id
LEFT JOIN item_totals it  ON it.order_id     = o.order_id;

COMMENT ON VIEW v_orders_enriched IS
'Grain: one row per order. is_qualifying = Delivered. qualifying_revenue = total_amount for Delivered orders, else 0. recorded_hour is the clock hour of delivery_time, not a duration.';

-- -----------------------------------------------------------------------------
-- v_order_items_enriched
-- GRAIN: one row per order line (1,667,399 rows).
-- Use for item / category / veg analysis. Do NOT COUNT(*) this for orders;
-- use COUNT(DISTINCT order_id) or v_orders_enriched.
-- order_items.price is a UNIT price (verified: SUM(quantity*price) = total_amount).
-- -----------------------------------------------------------------------------
CREATE VIEW v_order_items_enriched AS
SELECT
    oi.order_item_id,
    oi.order_id,
    o.order_date,
    DATE_TRUNC('month', o.order_date)::date  AS order_month,
    o.order_status,
    (o.order_status = 'Delivered')           AS is_qualifying,
    o.restaurant_id,
    r.restaurant_name,
    r.city,
    r.cuisine,
    oi.menu_id,
    m.item_name,
    m.category,
    (m.is_veg = 1)                           AS is_veg,
    oi.quantity,
    oi.price                                 AS unit_price,
    (oi.quantity * oi.price)                 AS line_revenue
FROM order_items oi
JOIN orders o       ON o.order_id      = oi.order_id
JOIN restaurants r  ON r.restaurant_id = o.restaurant_id
JOIN menu m         ON m.menu_id       = oi.menu_id;

COMMENT ON VIEW v_order_items_enriched IS
'Grain: one row per order line. line_revenue = quantity * unit_price. Filter is_qualifying for revenue. Do not COUNT(*) for orders.';
