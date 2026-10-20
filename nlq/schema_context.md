# FoodFlow schema context (approved objects only)

Database: PostgreSQL. Use ONLY the views and functions below. "Qualifying" means order_status = 'Delivered'. "Revenue" means qualifying revenue.

## Base views
- v_orders_enriched (one row per order): order_id, user_id, restaurant_id, restaurant_name, city, cuisine, order_date, order_week, order_month, recorded_hour, order_status, is_qualifying, payment_method, total_amount, qualifying_revenue, item_lines, total_units
- v_order_items_enriched (one row per order line): order_item_id, order_id, order_date, order_month, order_status, is_qualifying, restaurant_id, restaurant_name, city, cuisine, menu_id, item_name, category, is_veg, quantity, unit_price, line_revenue

## KPI views and functions
- v_kpi_daily: order_date, total_orders, qualifying_orders, cancelled_orders, qualifying_revenue, avg_order_value, cancellation_rate
- v_kpi_monthly: order_month, total_orders, qualifying_orders, cancelled_orders, qualifying_revenue, avg_order_value, cancellation_rate, active_restaurants, active_customers
- v_kpi_overall (1 row): total_orders, qualifying_orders, cancelled_orders, qualifying_revenue, avg_order_value, cancellation_rate, active_restaurants, active_customers, first_order_date, last_order_date
- fn_kpi_summary(start_date, end_date): KPIs for any date range (one row)

## Business question views and functions
- v_q01_weekly_orders_trend: week_start, total_orders, qualifying_orders, qualifying_revenue, prev_week_orders, wow_change_pct
- v_q02_restaurant_monthly_ranking: order_month, restaurant_id, restaurant_name, city, cuisine, qualifying_orders, qualifying_revenue, revenue_rank
- fn_top_restaurants(start_date, end_date, limit): revenue_rank, restaurant_id, restaurant_name, city, cuisine, qualifying_orders, qualifying_revenue
- v_q03_item_monthly_performance: order_month, menu_id, item_name, category, is_veg, restaurant_id, restaurant_name, units_sold, qualifying_revenue, qualifying_orders
- fn_top_items(start_date, end_date, limit): units_rank, menu_id, item_name, category, restaurant_name, units_sold, qualifying_revenue
- v_q04_status_mix_monthly: order_month, order_status, orders, share_of_orders
- v_q05_customer_orders: user_id, qualifying_orders, qualifying_revenue, first_order_date, last_order_date, is_repeat_customer
- v_q05_repeat_customer_summary (1 row): customers, repeat_customers, repeat_rate, avg_orders_per_customer
- v_q06_basket_size_monthly: order_month, qualifying_orders, avg_item_lines_per_order, avg_units_per_order, avg_order_value
- v_q07_cuisine_mix_monthly: order_month, cuisine, qualifying_orders, qualifying_revenue, revenue_share
- v_q08_payment_mix_monthly: order_month, payment_method, total_orders, qualifying_orders, share_of_orders
- v_q09_orders_by_recorded_hour: recorded_hour, total_orders, qualifying_orders
- v_q10_city_revenue_monthly: order_month, city, qualifying_orders, qualifying_revenue

## Rules
- Write ONE read-only SELECT (or WITH ... SELECT). No comments, no semicolons inside.
- Prefer the v_q and v_kpi views. For a custom date range use fn_kpi_summary, fn_top_restaurants or fn_top_items.
- Never average daily or monthly ratios (avg_order_value, cancellation_rate) over a range. Use fn_kpi_summary instead.
- Never COUNT(*) on v_order_items_enriched to count orders. Use COUNT(DISTINCT order_id).
- Months are the first day of the month, for example '2025-06-01'.

## Limitations (answer politely, do not write SQL)
- There is NO driver data (no driver speed, distance or availability).
- recorded_hour is a clock hour of delivery_time. It is NOT a delivery duration, so questions about minutes taken to deliver are unsupported.
- There are no ratings, so "best restaurant" is ambiguous: ask whether it means revenue or order count.