"""
FoodFlow Plotly Chart Components
File: app/components/charts.py
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Elegant color palette
PRIMARY_COLOR = "#FF5200"     # Swiggy/FoodFlow orange
SECONDARY_COLOR = "#2B7FFF"   # High contrast blue
ACCENT_GREEN = "#00C48C"
ACCENT_RED = "#FF4560"
CHART_TEMPLATE = "plotly_white"


def plot_daily_trend(df: pd.DataFrame) -> go.Figure:
    """Create dual-axis daily order volume and revenue trend line chart."""
    if df.empty:
        return go.Figure()

    fig = go.Figure()

    # Left Y-axis: Delivered Orders
    fig.add_trace(
        go.Scatter(
            x=df["order_date"],
            y=df["qualifying_orders"],
            name="Delivered Orders",
            mode="lines",
            line=dict(color=PRIMARY_COLOR, width=2.5),
            hovertemplate="Date: %{x}<br>Delivered: %{y:,}<extra></extra>",
        )
    )

    # Right Y-axis: Qualifying Revenue
    fig.add_trace(
        go.Scatter(
            x=df["order_date"],
            y=df["qualifying_revenue"],
            name="Revenue (₹)",
            mode="lines",
            line=dict(color=SECONDARY_COLOR, width=2, dash="dot"),
            yaxis="y2",
            hovertemplate="Date: %{x}<br>Revenue: ₹%{y:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="<b>Daily Order Volume & Revenue Trend</b>",
        template=CHART_TEMPLATE,
        hovermode="x unified",
        xaxis=dict(title="Order Date", showgrid=True),
        yaxis=dict(title="Delivered Orders", showgrid=True),
        yaxis2=dict(
            title="Revenue (₹)",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig


def plot_top_restaurants(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart for top restaurants by qualifying revenue."""
    if df.empty:
        return go.Figure()

    sorted_df = df.sort_values(by="qualifying_revenue", ascending=True)
    fig = px.bar(
        sorted_df,
        x="qualifying_revenue",
        y="restaurant_name",
        orientation="h",
        color="cuisine",
        title="<b>Top Restaurants by Qualifying Revenue</b>",
        labels={"qualifying_revenue": "Revenue (₹)", "restaurant_name": "Restaurant", "cuisine": "Cuisine"},
        template=CHART_TEMPLATE,
        hover_data=["city", "qualifying_orders"],
    )
    fig.update_layout(
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis_title="Qualifying Revenue (₹)",
        yaxis_title="",
    )
    return fig


def plot_top_items(df: pd.DataFrame) -> go.Figure:
    """Bar chart for top menu items by units sold."""
    if df.empty:
        return go.Figure()

    fig = px.bar(
        df,
        x="item_name",
        y="units_sold",
        color="category",
        title="<b>Top Menu Items by Units Sold</b>",
        labels={"units_sold": "Units Sold", "item_name": "Menu Item", "category": "Category"},
        template=CHART_TEMPLATE,
        hover_data=["restaurant_name", "qualifying_revenue"],
    )
    fig.update_layout(
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis_title="",
        xaxis_tickangle=-30,
    )
    return fig


def plot_cuisine_mix(df: pd.DataFrame) -> go.Figure:
    """Donut chart for top cuisine revenue shares."""
    if df.empty:
        return go.Figure()

    fig = px.pie(
        df,
        names="cuisine",
        values="total_revenue",
        hole=0.45,
        title="<b>Revenue Share by Cuisine</b>",
        template=CHART_TEMPLATE,
        color_discrete_sequence=px.colors.qualitative.Prism,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), showlegend=False)
    return fig


def plot_payment_mix(df: pd.DataFrame) -> go.Figure:
    """Donut chart for payment method distribution."""
    if df.empty:
        return go.Figure()

    fig = px.pie(
        df,
        names="payment_method",
        values="total_orders",
        hole=0.45,
        title="<b>Payment Method Distribution</b>",
        template=CHART_TEMPLATE,
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), showlegend=True)
    return fig


def plot_hourly_orders(df: pd.DataFrame) -> go.Figure:
    """Bar chart of order count by recorded clock hour."""
    if df.empty:
        return go.Figure()

    fig = px.bar(
        df,
        x="recorded_hour",
        y="total_orders",
        title="<b>Order Volume by Clock Hour of Day</b>",
        labels={"recorded_hour": "Recorded Clock Hour (0-23)", "total_orders": "Total Orders Placed"},
        template=CHART_TEMPLATE,
        color_discrete_sequence=[SECONDARY_COLOR],
    )
    fig.update_layout(
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(tickmode="linear", tick0=0, dtick=1),
    )
    return fig
