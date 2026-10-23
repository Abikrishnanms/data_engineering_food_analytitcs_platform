-- =============================================================================
-- FoodFlow Analytics - KPI Views and Functions
-- File: sql/analytics/10_kpis.sql
-- Owner: Swetha - Analytics Engineer
-- Depends on: 01_base_views.sql
--
-- Ratios (AOV, cancellation rate) are NOT additive. For any date range, never
-- average the daily/monthly ratios: call fn_kpi_summary(start, end) instead.
-- =============================================================================

DROP FUNCTION IF EXISTS fn_kpi_summary(date, date);
DROP VIEW IF EXISTS v_kpi_overall CASCADE;
DROP VIEW IF EXISTS v_kpi_monthly CASCADE;
DROP VIEW IF EXISTS v_kpi_daily   CASCADE;

-- -----------------------------------------------------------------------------
-- v_kpi_daily : one row per calendar day with orders. Drives the daily trend.
-- -----------------------------------------------------------------------------
CREATE VIEW v_kpi_daily AS
SELECT
    order_date,
    COUNT(*)                                             AS total_orders,
    COUNT(*) FILTER (WHERE is_qualifying)                AS qualifying_orders,
    COUNT(*) FILTER (WHERE NOT is_qualifying)            AS cancelled_orders,
    SUM(qualifying_revenue)                              AS qualifying_revenue,
    ROUND(SUM(qualifying_revenue)
          / NULLIF(COUNT(*) FILTER (WHERE is_qualifying), 0), 2) AS avg_order_value,
    ROUND(COUNT(*) FILTER (WHERE NOT is_qualifying)::numeric
          / NULLIF(COUNT(*), 0), 4)                      AS cancellation_rate
FROM v_orders_enriched
GROUP BY order_date;

-- -----------------------------------------------------------------------------
-- v_kpi_monthly : one row per month.
-- -----------------------------------------------------------------------------
CREATE VIEW v_kpi_monthly AS
SELECT
    order_month,
    COUNT(*)                                             AS total_orders,
    COUNT(*) FILTER (WHERE is_qualifying)                AS qualifying_orders,
    COUNT(*) FILTER (WHERE NOT is_qualifying)            AS cancelled_orders,
    SUM(qualifying_revenue)                              AS qualifying_revenue,
    ROUND(SUM(qualifying_revenue)
          / NULLIF(COUNT(*) FILTER (WHERE is_qualifying), 0), 2) AS avg_order_value,
    ROUND(COUNT(*) FILTER (WHERE NOT is_qualifying)::numeric
          / NULLIF(COUNT(*), 0), 4)                      AS cancellation_rate,
    COUNT(DISTINCT restaurant_id) FILTER (WHERE is_qualifying) AS active_restaurants,
    COUNT(DISTINCT user_id)       FILTER (WHERE is_qualifying) AS active_customers
FROM v_orders_enriched
GROUP BY order_month;

-- -----------------------------------------------------------------------------
-- v_kpi_overall : single row, all dates.
-- -----------------------------------------------------------------------------
CREATE VIEW v_kpi_overall AS
SELECT
    COUNT(*)                                             AS total_orders,
    COUNT(*) FILTER (WHERE is_qualifying)                AS qualifying_orders,
    COUNT(*) FILTER (WHERE NOT is_qualifying)            AS cancelled_orders,
    SUM(qualifying_revenue)                              AS qualifying_revenue,
    ROUND(SUM(qualifying_revenue)
          / NULLIF(COUNT(*) FILTER (WHERE is_qualifying), 0), 2) AS avg_order_value,
    ROUND(COUNT(*) FILTER (WHERE NOT is_qualifying)::numeric
          / NULLIF(COUNT(*), 0), 4)                      AS cancellation_rate,
    COUNT(DISTINCT restaurant_id) FILTER (WHERE is_qualifying) AS active_restaurants,
    COUNT(DISTINCT user_id)       FILTER (WHERE is_qualifying) AS active_customers,
    MIN(order_date)                                      AS first_order_date,
    MAX(order_date)                                      AS last_order_date
FROM v_orders_enriched;

-- -----------------------------------------------------------------------------
-- fn_kpi_summary(start, end) : KPI cards for the dashboard date filter.
-- Inclusive on both dates. Returns exactly one row (zeros/NULLs if no data).
-- Usage: SELECT * FROM fn_kpi_summary('2025-06-01', '2025-06-30');
-- -----------------------------------------------------------------------------
CREATE FUNCTION fn_kpi_summary(p_start date, p_end date)
RETURNS TABLE (
    total_orders        bigint,
    qualifying_orders   bigint,
    cancelled_orders    bigint,
    qualifying_revenue  numeric,
    avg_order_value     numeric,
    cancellation_rate   numeric,
    active_restaurants  bigint,
    active_customers    bigint
)
LANGUAGE sql STABLE AS $$
    SELECT
        COUNT(*),
        COUNT(*) FILTER (WHERE is_qualifying),
        COUNT(*) FILTER (WHERE NOT is_qualifying),
        COALESCE(SUM(qualifying_revenue), 0),
        ROUND(SUM(qualifying_revenue)
              / NULLIF(COUNT(*) FILTER (WHERE is_qualifying), 0), 2),
        ROUND(COUNT(*) FILTER (WHERE NOT is_qualifying)::numeric
              / NULLIF(COUNT(*), 0), 4),
        COUNT(DISTINCT restaurant_id) FILTER (WHERE is_qualifying),
        COUNT(DISTINCT user_id)       FILTER (WHERE is_qualifying)
    FROM v_orders_enriched
    WHERE order_date BETWEEN p_start AND p_end
$$;
