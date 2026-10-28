-- =============================================================================
-- FoodFlow Database Schema
-- File: db/schema/001_create_tables.sql
-- Description: DDL table definitions, data types, primary keys,
--              and validation constraints for the FoodFlow platform.
--              Foreign keys are added in 002_indexes.sql for high-speed bulk loading.
-- =============================================================================

-- Drop tables in reverse order of dependencies if they already exist
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS menu CASCADE;
DROP TABLE IF EXISTS restaurants CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- -----------------------------------------------------------------------------
-- 1. USERS TABLE
-- Stores registered customer profiles and demographic details.
-- -----------------------------------------------------------------------------
CREATE TABLE users (
    user_id         VARCHAR(50) PRIMARY KEY,
    user_name       VARCHAR(150) NOT NULL,
    age             INTEGER CHECK (age >= 0 AND age <= 120),
    gender          VARCHAR(50),
    marital_status  VARCHAR(50),
    occupation      VARCHAR(100),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE users IS 'Registered customer profile information';
COMMENT ON COLUMN users.user_id IS 'Unique identifier for the customer (e.g. U00001)';
COMMENT ON COLUMN users.age IS 'Customer age in years';

-- -----------------------------------------------------------------------------
-- 2. RESTAURANTS TABLE
-- Stores partner restaurant metadata, locations, and ratings.
-- -----------------------------------------------------------------------------
CREATE TABLE restaurants (
    restaurant_id      VARCHAR(50) PRIMARY KEY,
    restaurant_name    VARCHAR(200) NOT NULL,
    city               VARCHAR(100) NOT NULL,
    cuisine            VARCHAR(100),
    rating             NUMERIC(3, 2) CHECK (rating >= 0.0 AND rating <= 5.0),
    is_cloud_kitchen   SMALLINT NOT NULL CHECK (is_cloud_kitchen IN (0, 1)),
    created_at         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE restaurants IS 'Partner restaurant profiles and operational characteristics';
COMMENT ON COLUMN restaurants.restaurant_id IS 'Unique identifier for the restaurant (e.g. R0001)';
COMMENT ON COLUMN restaurants.rating IS 'Customer rating between 0.0 and 5.0';
COMMENT ON COLUMN restaurants.is_cloud_kitchen IS 'Binary flag: 1 for cloud kitchen / delivery-only, 0 otherwise';

-- -----------------------------------------------------------------------------
-- 3. MENU TABLE
-- Stores individual food items offered by restaurants.
-- -----------------------------------------------------------------------------
CREATE TABLE menu (
    menu_id        VARCHAR(50) PRIMARY KEY,
    restaurant_id  VARCHAR(50) NOT NULL,
    item_name      VARCHAR(200) NOT NULL,
    category       VARCHAR(100),
    price          NUMERIC(10, 2) NOT NULL CHECK (price >= 0.00),
    is_veg         SMALLINT NOT NULL CHECK (is_veg IN (0, 1)),
    created_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE menu IS 'Catalog of food items offered by partner restaurants';
COMMENT ON COLUMN menu.menu_id IS 'Unique identifier for the menu item (e.g. M000001)';
COMMENT ON COLUMN menu.price IS 'Base catalog price of the item';
COMMENT ON COLUMN menu.is_veg IS 'Binary flag: 1 for vegetarian, 0 otherwise';

-- -----------------------------------------------------------------------------
-- 4. ORDERS TABLE
-- Stores order header transactions placed by users at restaurants.
-- Note: delivery_time is a clock time (e.g. 14:30:00), not delivery duration.
-- -----------------------------------------------------------------------------
CREATE TABLE orders (
    order_id        VARCHAR(50) PRIMARY KEY,
    user_id         VARCHAR(50) NOT NULL,
    restaurant_id   VARCHAR(50) NOT NULL,
    order_date      DATE NOT NULL,
    delivery_time   TIME,
    order_status    VARCHAR(50) NOT NULL CHECK (order_status IN ('Delivered', 'Cancelled')),
    payment_method  VARCHAR(50) NOT NULL CHECK (payment_method IN ('UPI', 'Credit Card', 'Debit Card', 'Cash on Delivery', 'Wallet')),
    total_amount    NUMERIC(10, 2) NOT NULL CHECK (total_amount >= 0.00),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE orders IS 'Order transactions placed by customers';
COMMENT ON COLUMN orders.order_id IS 'Unique identifier for the order (e.g. O0000001)';
COMMENT ON COLUMN orders.delivery_time IS 'Clock time when order was recorded/delivered; not duration';
COMMENT ON COLUMN orders.total_amount IS 'Total recorded invoice amount for the order';

-- -----------------------------------------------------------------------------
-- 5. ORDER_ITEMS TABLE
-- Stores the line items belonging to each order.
-- -----------------------------------------------------------------------------
CREATE TABLE order_items (
    order_item_id  VARCHAR(50) PRIMARY KEY,
    order_id       VARCHAR(50) NOT NULL,
    menu_id        VARCHAR(50) NOT NULL,
    quantity       INTEGER NOT NULL CHECK (quantity > 0),
    price          NUMERIC(10, 2) NOT NULL CHECK (price >= 0.00),
    created_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE order_items IS 'Itemized line items belonging to orders';
COMMENT ON COLUMN order_items.order_item_id IS 'Unique line item identifier (e.g. OI00000001)';
COMMENT ON COLUMN order_items.quantity IS 'Number of units ordered; strictly positive integer';
COMMENT ON COLUMN order_items.price IS 'Price recorded on the order item line';
