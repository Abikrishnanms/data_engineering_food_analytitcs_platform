"""
FoodFlow Dashboard — Restaurants & Menu Performance Page
File: app/pages/2_🍽️_Restaurants_and_Menu.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
from app.data_access import fetch_top_restaurants, fetch_top_items, fetch_cuisine_mix, fetch_hourly_orders
from app.components.charts import plot_top_restaurants, plot_top_items, plot_cuisine_mix, plot_hourly_orders

st.set_page_config(page_title="Restaurants & Menu — FoodFlow", page_icon="🍽️", layout="wide")

st.title("🍽️ Restaurant & Menu Item Performance")
st.markdown("Analyze restaurant rankings, best-selling dishes, cuisine revenue contributions, and ordering patterns.")

# Date filter controls
col_d1, col_d2, col_limit = st.columns([2, 2, 2])
with col_d1:
    start_date = st.date_input("Start date", value=pd.to_datetime("2025-06-01").date(),
                               min_value=pd.to_datetime("2022-01-01").date(),
                               max_value=pd.to_datetime("2025-12-31").date())
with col_d2:
    end_date = st.date_input("End date", value=pd.to_datetime("2025-06-30").date(),
                             min_value=pd.to_datetime("2022-01-01").date(),
                             max_value=pd.to_datetime("2025-12-31").date())
with col_limit:
    top_n = st.slider("Top N Results", min_value=3, max_value=20, value=5)

str_start = start_date.strftime("%Y-%m-%d")
str_end = end_date.strftime("%Y-%m-%d")

try:
    rest_df = fetch_top_restaurants(str_start, str_end, limit=top_n)
    items_df = fetch_top_items(str_start, str_end, limit=top_n)
    cuisine_df = fetch_cuisine_mix()
    hourly_df = fetch_hourly_orders()
except Exception as e:
    st.error(f"Error querying restaurant/menu analytics: {e}")
    st.stop()

# Row 1: Top Restaurants
st.markdown(f"### Top {top_n} Partner Restaurants by Revenue ({str_start} to {str_end})")
col_r1, col_r2 = st.columns([3, 2])
with col_r1:
    st.plotly_chart(plot_top_restaurants(rest_df), use_container_width=True)
with col_r2:
    if not rest_df.empty:
        display_rest = rest_df[["revenue_rank", "restaurant_name", "city", "cuisine", "qualifying_orders", "qualifying_revenue"]].copy()
        display_rest["qualifying_revenue"] = display_rest["qualifying_revenue"].apply(lambda v: f"₹{v:,.2f}")
        st.dataframe(display_rest.rename(columns={
            "revenue_rank": "Rank",
            "restaurant_name": "Restaurant",
            "city": "City",
            "cuisine": "Cuisine",
            "qualifying_orders": "Orders",
            "qualifying_revenue": "Revenue",
        }), use_container_width=True, hide_index=True)

st.divider()

# Row 2: Top Menu Items
st.markdown(f"### Top {top_n} Menu Items by Units Sold ({str_start} to {str_end})")
col_i1, col_i2 = st.columns([3, 2])
with col_i1:
    st.plotly_chart(plot_top_items(items_df), use_container_width=True)
with col_i2:
    if not items_df.empty:
        display_items = items_df[["units_rank", "item_name", "category", "restaurant_name", "units_sold", "qualifying_revenue"]].copy()
        display_items["qualifying_revenue"] = display_items["qualifying_revenue"].apply(lambda v: f"₹{v:,.2f}")
        st.dataframe(display_items.rename(columns={
            "units_rank": "Rank",
            "item_name": "Item",
            "category": "Category",
            "restaurant_name": "Restaurant",
            "units_sold": "Units Sold",
            "qualifying_revenue": "Revenue",
        }), use_container_width=True, hide_index=True)

st.divider()

# Row 3: Cuisine & Order Time Pattern
col_b1, col_b2 = st.columns(2)
with col_b1:
    st.markdown("### Top Cuisines by Revenue Share")
    st.plotly_chart(plot_cuisine_mix(cuisine_df), use_container_width=True)

with col_b2:
    st.markdown("### Order Timing Distribution (Clock Hour)")
    st.plotly_chart(plot_hourly_orders(hourly_df), use_container_width=True)
    st.caption("ℹ️ *Note: `delivery_time` in FoodFlow records the clock time of order activity (0-23), not delivery duration in minutes.*")
