"""
FoodFlow Metric Cards Component
File: app/components/metric_cards.py
"""

import streamlit as st


def render_kpi_cards(kpi_row):
    """
    Render modern KPI metric cards from a single row of fn_kpi_summary.
    Expected keys: total_orders, qualifying_orders, cancelled_orders,
                   qualifying_revenue, avg_order_value, cancellation_rate,
                   active_restaurants, active_customers.
    """
    total_orders = int(kpi_row.get("total_orders", 0) or 0)
    qualifying_orders = int(kpi_row.get("qualifying_orders", 0) or 0)
    cancelled_orders = int(kpi_row.get("cancelled_orders", 0) or 0)
    qualifying_revenue = float(kpi_row.get("qualifying_revenue", 0.0) or 0.0)
    avg_order_value = float(kpi_row.get("avg_order_value", 0.0) or 0.0)
    cancellation_rate = float(kpi_row.get("cancellation_rate", 0.0) or 0.0) * 100
    active_restaurants = int(kpi_row.get("active_restaurants", 0) or 0)
    active_customers = int(kpi_row.get("active_customers", 0) or 0)

    # First row: Core business volumes
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Orders Placed",
            value=f"{total_orders:,}",
            help="All orders placed within selected timeframe, any status."
        )

    with col2:
        st.metric(
            label="Delivered Orders",
            value=f"{qualifying_orders:,}",
            delta=f"{((qualifying_orders/total_orders)*100):.1f}% fulfilled" if total_orders > 0 else None,
            help="Qualifying orders successfully delivered to customers."
        )

    with col3:
        st.metric(
            label="Qualifying Revenue",
            value=f"₹{qualifying_revenue:,.2f}" if qualifying_revenue < 1e7 else f"₹{qualifying_revenue/1e6:.2f}M",
            help="Total invoice sum for Delivered orders only. Cancelled orders contribute ₹0."
        )

    with col4:
        st.metric(
            label="Average Order Value (AOV)",
            value=f"₹{avg_order_value:,.2f}",
            help="Qualifying revenue divided by delivered orders."
        )

    # Second row: Operational quality & platform reach
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.metric(
            label="Cancellation Rate",
            value=f"{cancellation_rate:.2f}%",
            delta=f"-{cancelled_orders:,} orders" if cancelled_orders > 0 else None,
            delta_color="inverse",
            help="Share of orders cancelled."
        )

    with col6:
        st.metric(
            label="Active Restaurants",
            value=f"{active_restaurants:,}",
            help="Unique restaurants fulfilling at least 1 delivered order."
        )

    with col7:
        st.metric(
            label="Active Customers",
            value=f"{active_customers:,}",
            help="Unique customers placing at least 1 delivered order."
        )

    with col8:
        completion_rate = 100 - cancellation_rate if total_orders > 0 else 0
        st.metric(
            label="Fulfillment Success",
            value=f"{completion_rate:.1f}%",
            help="Percentage of placed orders successfully delivered without cancellation."
        )
