-- =============================================================================
-- FoodFlow Analytics Tests
-- File: tests/test_analytics.sql
-- Owner: Swetha - Analytics Engineer
-- Run:  psql -h localhost -U postgres -d foodflow -f tests/test_analytics.sql
-- Every row must show is_pass = true. "expected" is computed independently
-- from the RAW tables; "actual" comes from the analytics views.
-- =============================================================================
SELECT check_name, expected, actual, (expected = actual) AS is_pass
FROM (
    -- ---- Grain / join safety -------------------------------------------------
    SELECT 1 AS n, 'orders_view_rowcount_equals_orders' AS check_name,
           (SELECT COUNT(*) FROM orders)::numeric AS expected,
           (SELECT COUNT(*) FROM v_orders_enriched)::numeric AS actual
    UNION ALL SELECT 2, 'orders_view_has_no_duplicate_order_id', 0,
           (SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM v_orders_enriched)
    UNION ALL SELECT 3, 'items_view_rowcount_equals_order_items',
           (SELECT COUNT(*) FROM order_items),
           (SELECT COUNT(*) FROM v_order_items_enriched)
    -- ---- Qualifying definition (Delivered) -----------------------------------
    UNION ALL SELECT 4, 'qualifying_order_count',
           (SELECT COUNT(*) FROM orders WHERE order_status = 'Delivered'),
           (SELECT qualifying_orders FROM v_kpi_overall)
    UNION ALL SELECT 5, 'qualifying_revenue_total',
           (SELECT SUM(total_amount) FROM orders WHERE order_status = 'Delivered'),
           (SELECT qualifying_revenue FROM v_kpi_overall)
    UNION ALL SELECT 6, 'cancelled_orders_contribute_zero_revenue', 0,
           (SELECT COALESCE(SUM(qualifying_revenue), 0) FROM v_orders_enriched WHERE NOT is_qualifying)
    -- ---- Reconciliation: orders vs items --------------------------------------
    UNION ALL SELECT 7, 'orders_whose_total_differs_from_item_sum', 0,
           (SELECT COUNT(*) FROM orders o
             JOIN (SELECT order_id, SUM(quantity * price) AS s FROM order_items GROUP BY order_id) i
               ON i.order_id = o.order_id
            WHERE o.total_amount <> i.s)
    UNION ALL SELECT 8, 'item_revenue_equals_order_revenue_all_orders',
           (SELECT SUM(total_amount) FROM orders),
           (SELECT SUM(line_revenue) FROM v_order_items_enriched)
    UNION ALL SELECT 9, 'item_revenue_equals_order_revenue_qualifying',
           (SELECT qualifying_revenue FROM v_kpi_overall),
           (SELECT SUM(line_revenue) FROM v_order_items_enriched WHERE is_qualifying)
    -- ---- KPI views are consistent with each other -----------------------------
    UNION ALL SELECT 10, 'daily_kpi_orders_sum',
           (SELECT COUNT(*) FROM orders), (SELECT SUM(total_orders) FROM v_kpi_daily)
    UNION ALL SELECT 11, 'daily_kpi_revenue_sum',
           (SELECT qualifying_revenue FROM v_kpi_overall), (SELECT SUM(qualifying_revenue) FROM v_kpi_daily)
    UNION ALL SELECT 12, 'monthly_kpi_revenue_sum',
           (SELECT qualifying_revenue FROM v_kpi_overall), (SELECT SUM(qualifying_revenue) FROM v_kpi_monthly)
    UNION ALL SELECT 13, 'fn_kpi_summary_full_range_revenue',
           (SELECT qualifying_revenue FROM v_kpi_overall),
           (SELECT qualifying_revenue FROM fn_kpi_summary('2000-01-01', '2100-01-01'))
    UNION ALL SELECT 14, 'fn_kpi_summary_single_month_orders',
           (SELECT COUNT(*) FROM orders WHERE order_date BETWEEN '2025-06-01' AND '2025-06-30'),
           (SELECT total_orders FROM fn_kpi_summary('2025-06-01', '2025-06-30'))
    UNION ALL SELECT 15, 'fn_kpi_summary_empty_range_returns_one_row_zero_orders', 0,
           (SELECT total_orders FROM fn_kpi_summary('1990-01-01', '1990-01-31'))
    UNION ALL SELECT 16, 'avg_order_value_matches_formula',
           (SELECT ROUND(SUM(total_amount) / COUNT(*), 2) FROM orders WHERE order_status = 'Delivered'),
           (SELECT avg_order_value FROM v_kpi_overall)
    -- ---- Business-question views ----------------------------------------------
    UNION ALL SELECT 17, 'q01_weekly_total_orders_sum',
           (SELECT COUNT(*) FROM orders), (SELECT SUM(total_orders) FROM v_q01_weekly_orders_trend)
    UNION ALL SELECT 18, 'q02_restaurant_revenue_sum',
           (SELECT qualifying_revenue FROM v_kpi_overall),
           (SELECT SUM(qualifying_revenue) FROM v_q02_restaurant_monthly_ranking)
    UNION ALL SELECT 19, 'q02_every_month_has_a_rank_1', 0,
           (SELECT COUNT(*) FROM v_kpi_monthly k
             WHERE NOT EXISTS (SELECT 1 FROM v_q02_restaurant_monthly_ranking q
                                WHERE q.order_month = k.order_month AND q.revenue_rank = 1))
    UNION ALL SELECT 20, 'fn_top_restaurants_returns_requested_rows', 5,
           (SELECT COUNT(*) FROM fn_top_restaurants('2025-06-01', '2025-06-30', 5))
    UNION ALL SELECT 21, 'q03_item_units_sum',
           (SELECT SUM(oi.quantity) FROM order_items oi JOIN orders o USING (order_id) WHERE o.order_status = 'Delivered'),
           (SELECT SUM(units_sold) FROM v_q03_item_monthly_performance)
    UNION ALL SELECT 22, 'q04_status_shares_sum_to_one_every_month', 0,
           (SELECT COUNT(*) FROM (SELECT order_month FROM v_q04_status_mix_monthly
                                   GROUP BY order_month HAVING ABS(SUM(share_of_orders) - 1) > 0.001) x)
    UNION ALL SELECT 23, 'q05_customer_count_with_delivered_orders',
           (SELECT COUNT(DISTINCT user_id) FROM orders WHERE order_status = 'Delivered'),
           (SELECT customers FROM v_q05_repeat_customer_summary)
    UNION ALL SELECT 24, 'q05_customer_orders_sum',
           (SELECT COUNT(*) FROM orders WHERE order_status = 'Delivered'),
           (SELECT SUM(qualifying_orders) FROM v_q05_customer_orders)
    UNION ALL SELECT 25, 'q06_basket_orders_sum',
           (SELECT COUNT(*) FROM orders WHERE order_status = 'Delivered'),
           (SELECT SUM(qualifying_orders) FROM v_q06_basket_size_monthly)
    UNION ALL SELECT 26, 'q07_cuisine_revenue_sum',
           (SELECT qualifying_revenue FROM v_kpi_overall), (SELECT SUM(qualifying_revenue) FROM v_q07_cuisine_mix_monthly)
    UNION ALL SELECT 27, 'q08_payment_orders_sum',
           (SELECT COUNT(*) FROM orders), (SELECT SUM(total_orders) FROM v_q08_payment_mix_monthly)
    UNION ALL SELECT 28, 'q09_hour_orders_sum',
           (SELECT COUNT(*) FROM orders), (SELECT SUM(total_orders) FROM v_q09_orders_by_recorded_hour)
    UNION ALL SELECT 29, 'q10_city_revenue_sum',
           (SELECT qualifying_revenue FROM v_kpi_overall), (SELECT SUM(qualifying_revenue) FROM v_q10_city_revenue_monthly)
) t
ORDER BY n;
