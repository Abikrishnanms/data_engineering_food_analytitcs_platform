-- =============================================================================
-- FoodFlow Database Validation & Test Queries
-- File: tests/test_database.sql
-- Role: Lekshmi Priya - Database Engineer
-- Description: Verification queries for table row counts, foreign key integrity,
--              constraint compliance, and read-only testing.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. ROW COUNT RECONCILIATION
-- Expected counts based on raw Swiggy dataset profiling:
-- users: 10,000 | restaurants: 1,000 | menu: 15,658 | orders: 600,000 | order_items: 1,667,399
-- -----------------------------------------------------------------------------
SELECT 'users' AS table_name, COUNT(*) AS row_count, 10000 AS expected_count, (COUNT(*) = 10000) AS is_valid FROM users
UNION ALL
SELECT 'restaurants', COUNT(*), 1000, (COUNT(*) = 1000) FROM restaurants
UNION ALL
SELECT 'menu', COUNT(*), 15658, (COUNT(*) = 15658) FROM menu
UNION ALL
SELECT 'orders', COUNT(*), 600000, (COUNT(*) = 600000) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*), 1667399, (COUNT(*) = 1667399) FROM order_items;


-- -----------------------------------------------------------------------------
-- 2. ORPHAN RECORD & REFERENTIAL INTEGRITY CHECKS
-- Every check must return 0 orphan records.
-- -----------------------------------------------------------------------------

-- Check 1: Menu items pointing to non-existent restaurants
SELECT 'orphan_menu_restaurants' AS check_name, COUNT(*) AS orphan_count
FROM menu m
LEFT JOIN restaurants r ON m.restaurant_id = r.restaurant_id
WHERE r.restaurant_id IS NULL;

-- Check 2: Orders pointing to non-existent users
SELECT 'orphan_orders_users' AS check_name, COUNT(*) AS orphan_count
FROM orders o
LEFT JOIN users u ON o.user_id = u.user_id
WHERE u.user_id IS NULL;

-- Check 3: Orders pointing to non-existent restaurants
SELECT 'orphan_orders_restaurants' AS check_name, COUNT(*) AS orphan_count
FROM orders o
LEFT JOIN restaurants r ON o.restaurant_id = r.restaurant_id
WHERE r.restaurant_id IS NULL;

-- Check 4: Order items pointing to non-existent orders
SELECT 'orphan_order_items_orders' AS check_name, COUNT(*) AS orphan_count
FROM order_items oi
LEFT JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_id IS NULL;

-- Check 5: Order items pointing to non-existent menu items
SELECT 'orphan_order_items_menu' AS check_name, COUNT(*) AS orphan_count
FROM order_items oi
LEFT JOIN menu m ON oi.menu_id = m.menu_id
WHERE m.menu_id IS NULL;


-- -----------------------------------------------------------------------------
-- 3. CONSTRAINT & BOUNDARY VALUE VALIDATION
-- All invalid rows should return 0 count.
-- -----------------------------------------------------------------------------

-- Check 6: Check for invalid restaurant ratings (outside [0.0, 5.0])
SELECT 'invalid_ratings' AS check_name, COUNT(*) AS invalid_count
FROM restaurants
WHERE rating < 0.0 OR rating > 5.0 OR rating IS NULL;

-- Check 7: Check for negative prices in menu or order items
SELECT 'invalid_prices' AS check_name, COUNT(*) AS invalid_count
FROM (
    SELECT price FROM menu WHERE price < 0
    UNION ALL
    SELECT price FROM order_items WHERE price < 0
    UNION ALL
    SELECT total_amount FROM orders WHERE total_amount < 0
) p;

-- Check 8: Check for zero or negative quantities in order items
SELECT 'invalid_quantities' AS check_name, COUNT(*) AS invalid_count
FROM order_items
WHERE quantity <= 0;

-- Check 9: Check for unexpected order statuses
SELECT 'unexpected_order_statuses' AS check_name, COUNT(*) AS invalid_count
FROM orders
WHERE order_status NOT IN ('Delivered', 'Cancelled');

-- Check 10: Check for unexpected payment methods
SELECT 'unexpected_payment_methods' AS check_name, COUNT(*) AS invalid_count
FROM orders
WHERE payment_method NOT IN ('UPI', 'Credit Card', 'Debit Card', 'Cash on Delivery', 'Wallet');


-- -----------------------------------------------------------------------------
-- 4. NULL / PRIMARY KEY UNIQUENESS CHECKS
-- Verifies no null primary keys or duplicate keys exist.
-- -----------------------------------------------------------------------------
SELECT 'users_pk_duplicates' AS check_name, COUNT(*) - COUNT(DISTINCT user_id) AS dup_count FROM users
UNION ALL
SELECT 'restaurants_pk_duplicates', COUNT(*) - COUNT(DISTINCT restaurant_id) FROM restaurants
UNION ALL
SELECT 'menu_pk_duplicates', COUNT(*) - COUNT(DISTINCT menu_id) FROM menu
UNION ALL
SELECT 'orders_pk_duplicates', COUNT(*) - COUNT(DISTINCT order_id) FROM orders
UNION ALL
SELECT 'order_items_pk_duplicates', COUNT(*) - COUNT(DISTINCT order_item_id) FROM order_items;
