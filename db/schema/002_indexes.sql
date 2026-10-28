-- =============================================================================
-- FoodFlow Database Indexes & Foreign Key Constraints
-- File: db/schema/002_indexes.sql
-- Description: Applied after bulk data load to achieve sub-minute ingestion speed.
--              Enforces foreign keys, builds B-Tree indexes for joins,
--              status filtering, and analytical aggregations.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. FOREIGN KEY CONSTRAINTS
-- Added in bulk after data loading for 100x faster validation.
-- -----------------------------------------------------------------------------

ALTER TABLE menu 
    ADD CONSTRAINT fk_menu_restaurant 
    FOREIGN KEY (restaurant_id) REFERENCES restaurants (restaurant_id) 
    ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE orders 
    ADD CONSTRAINT fk_orders_user 
    FOREIGN KEY (user_id) REFERENCES users (user_id) 
    ON DELETE RESTRICT ON UPDATE CASCADE,
    ADD CONSTRAINT fk_orders_restaurant 
    FOREIGN KEY (restaurant_id) REFERENCES restaurants (restaurant_id) 
    ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE order_items 
    ADD CONSTRAINT fk_order_items_order 
    FOREIGN KEY (order_id) REFERENCES orders (order_id) 
    ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT fk_order_items_menu 
    FOREIGN KEY (menu_id) REFERENCES menu (menu_id) 
    ON DELETE RESTRICT ON UPDATE CASCADE;

-- -----------------------------------------------------------------------------
-- 2. FOREIGN KEY INDEXES
-- PostgreSQL does not automatically create indexes on foreign key columns.
-- These eliminate sequential scans on child tables during joins & cascade checks.
-- -----------------------------------------------------------------------------

-- menu foreign key
CREATE INDEX IF NOT EXISTS idx_menu_restaurant_id
    ON menu (restaurant_id);

-- orders foreign keys
CREATE INDEX IF NOT EXISTS idx_orders_user_id
    ON orders (user_id);

CREATE INDEX IF NOT EXISTS idx_orders_restaurant_id
    ON orders (restaurant_id);

-- order_items foreign keys
CREATE INDEX IF NOT EXISTS idx_order_items_order_id
    ON order_items (order_id);

CREATE INDEX IF NOT EXISTS idx_order_items_menu_id
    ON order_items (menu_id);

-- -----------------------------------------------------------------------------
-- 3. DASHBOARD & ANALYTICS FILTER INDEXES
-- Supports time-series queries, KPI calculations, and restaurant performance.
-- -----------------------------------------------------------------------------

-- Filter orders by date range (used in date pickers)
CREATE INDEX IF NOT EXISTS idx_orders_order_date
    ON orders (order_date);

-- Filter orders by status (e.g. Delivered vs Cancelled for revenue)
CREATE INDEX IF NOT EXISTS idx_orders_order_status
    ON orders (order_status);

-- Composite index: Filter by date range for delivered orders
CREATE INDEX IF NOT EXISTS idx_orders_status_date
    ON orders (order_status, order_date);

-- Composite index: Filter orders by restaurant and date range (restaurant performance)
CREATE INDEX IF NOT EXISTS idx_orders_restaurant_date
    ON orders (restaurant_id, order_date);

-- Restaurant filtering by city and rating
CREATE INDEX IF NOT EXISTS idx_restaurants_city
    ON restaurants (city);

CREATE INDEX IF NOT EXISTS idx_restaurants_rating
    ON restaurants (rating DESC);
