
# FoodFlow — Data Dictionary

## 1. Purpose

This document describes the five source datasets used in FoodFlow,
their columns, expected meanings, and relationships.

The raw CSV files are stored in `data/raw/`.
They must remain unchanged. Cleaning and transformations will be
performed separately.

## 2. Dataset Overview

| Dataset | Rows | Columns |
|---|---:|---:|
| users.csv | 10,000 | 6 |
| restaurants.csv | 1,000 | 6 |
| menu.csv | 15,658 | 6 |
| orders.csv | 600,000 | 8 |
| order_items.csv | 1,667,399 | 5 |

## 3. users.csv

Purpose: Stores customer information.

| Column | Meaning | Expected type |
|---|---|---|
| user_id | Unique customer identifier | String |
| user_name | Customer name | String |
| age | Customer age | Integer |
| gender | Customer gender category | String |
| marital_status | Customer marital-status category | String |
| occupation | Customer occupation | String |

Primary key: user_id

Relationship:
users.user_id -> orders.user_id

## 4. restaurants.csv

Purpose: Stores restaurant information.

| Column | Meaning | Expected type |
|---|---|---|
| restaurant_id | Unique restaurant identifier | String |
| restaurant_name | Restaurant name | String |
| city | Restaurant city | String |
| cuisine | Cuisine offered by the restaurant | String |
| rating | Restaurant rating | Numeric |
| is_cloud_kitchen | Indicator for cloud kitchen | Boolean or integer flag |

Primary key: restaurant_id

Relationship:
restaurants.restaurant_id -> orders.restaurant_id
restaurants.restaurant_id -> menu.restaurant_id

## 5. menu.csv

Purpose: Stores the menu items offered by restaurants.

| Column | Meaning | Expected type |
|---|---|---|
| menu_id | Unique menu-item identifier | String |
| restaurant_id | Restaurant offering the item | String |
| item_name | Name of the food item | String |
| category | Food category | String |
| price | Listed menu-item price | Numeric |
| is_veg | Indicator for vegetarian item | Boolean or integer flag |

Primary key: menu_id

Foreign key: restaurant_id -> restaurants.restaurant_id

## 6. orders.csv

Purpose: Stores order-level information.

| Column | Meaning | Expected type |
|---|---|---|
| order_id | Unique order identifier | String |
| user_id | Customer who placed the order | String |
| restaurant_id | Restaurant receiving the order | String |
| order_date | Date associated with the order | Date |
| delivery_time | Recorded time of day | Time or string |
| order_status | Status of the order | String |
| payment_method | Payment method used | String |
| total_amount | Recorded total order amount | Numeric |

Primary key: order_id

Foreign keys:
- user_id -> users.user_id
- restaurant_id -> restaurants.restaurant_id

Important:
delivery_time represents a clock time, not elapsed delivery
duration. Actual delivery-duration analysis requires additional data.

## 7. order_items.csv

Purpose: Stores individual items within orders.

| Column | Meaning | Expected type |
|---|---|---|
| order_item_id | Unique order-item record identifier | String |
| order_id | Order containing the item | String |
| menu_id | Menu item ordered | String |
| quantity | Number of units ordered | Integer |
| price | Recorded price for the order-item record | Numeric |

Primary key: order_item_id

Foreign keys:
- order_id -> orders.order_id
- menu_id -> menu.menu_id

## 8. Relationship Summary

users
  -> orders
  -> order_items
  -> menu
  -> restaurants

Additional relationships:
- orders.restaurant_id -> restaurants.restaurant_id
- menu.restaurant_id -> restaurants.restaurant_id

## 9. Initial Data Quality Findings

The first profiling run reported:
- No missing cells in the five source datasets.
- No completely duplicated rows.
- All five expected primary-key columns had unique values.
- Numerical summaries were generated for numeric columns.

The first validation run passed all nine implemented checks:
- Five foreign-key relationship checks.
- Three non-negative price/amount checks.
- One positive-quantity check.

Additional checks are still required for dates, ratings, flags,
allowed categories, order statuses and business-rule consistency.

## 10. Dataset Limitations

1. There is no driver table or driver identifier.
   Driver-performance analysis is unsupported.

2. delivery_time is a clock time, not a delivery-duration field.
   We can analyze ordering-time patterns but cannot calculate actual
   delivery duration from this field alone.

3. The meaning of total_amount and order_items.price must be confirmed
   before defining revenue metrics. Do not assume they reconcile
   without checking the dataset's business rules.


