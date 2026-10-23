import calendar
import re

MONTHS = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
ALL_TIME = ("2000-01-01", "2100-01-01")


def _date_range(q):
    """Return (start, end), or None if a month is given without a year."""
    month = re.search(r"\b(" + "|".join(MONTHS) + r")\b", q)
    year = re.search(r"\b(20\d\d)\b", q)
    if month and year:
        m, y = MONTHS[month.group(1)], int(year.group(1))
        last = calendar.monthrange(y, m)[1]
        return f"{y}-{m:02d}-01", f"{y}-{m:02d}-{last}"
    if month:
        return None
    return ALL_TIME


def _number(q, default):
    n = re.search(r"\b(\d{1,2})\b", q)
    return int(n.group(1)) if n else default


def rule_based_sql(question: str):
    q = question.lower()
    has = lambda *words: any(w in q for w in words)

    if has("best", "worst") and has("restaurant"):
        return "CLARIFY: Do you mean the highest revenue or the most orders?"

    if has("restaurant") and has("top", "highest", "most"):
        rng = _date_range(q)
        if rng is None:
            return "CLARIFY: Which year do you mean?"
        return f"SELECT * FROM fn_top_restaurants('{rng[0]}', '{rng[1]}', {_number(q, 5)})"

    if has("item", "dish", "menu") and has("top", "most", "best", "popular", "quantity"):
        rng = _date_range(q)
        if rng is None:
            return "CLARIFY: Which year do you mean?"
        return f"SELECT * FROM fn_top_items('{rng[0]}', '{rng[1]}', {_number(q, 10)})"

    if has("veg"):
        return ("SELECT is_veg, SUM(line_revenue) AS revenue FROM v_order_items_enriched "
                "WHERE is_qualifying GROUP BY is_veg")

    if has("cancel"):
        rng = _date_range(q)
        if rng is None:
            return "CLARIFY: Which year do you mean?"
        if rng == ALL_TIME:
            return "SELECT cancelled_orders, cancellation_rate FROM v_kpi_overall"
        return f"SELECT cancelled_orders, cancellation_rate FROM fn_kpi_summary('{rng[0]}', '{rng[1]}')"

    if has("repeat"):
        return "SELECT * FROM v_q05_repeat_customer_summary"
    if has("payment"):
        return ("SELECT order_month, payment_method, share_of_orders FROM v_q08_payment_mix_monthly "
                "ORDER BY order_month DESC, share_of_orders DESC LIMIT 50")
    if has("cuisine"):
        return ("SELECT cuisine, SUM(qualifying_revenue) AS qualifying_revenue FROM v_q07_cuisine_mix_monthly "
                "GROUP BY cuisine ORDER BY 2 DESC LIMIT 10")
    if has("city", "cities"):
        return ("SELECT city, SUM(qualifying_revenue) AS qualifying_revenue FROM v_q10_city_revenue_monthly "
                "GROUP BY city ORDER BY 2 DESC LIMIT 10")
    if has("hour", "time of day"):
        return "SELECT recorded_hour, total_orders FROM v_q09_orders_by_recorded_hour ORDER BY recorded_hour"
    if has("basket"):
        return "SELECT * FROM v_q06_basket_size_monthly ORDER BY order_month"
    if has("week"):
        return "SELECT week_start, total_orders, wow_change_pct FROM v_q01_weekly_orders_trend ORDER BY week_start"
    if has("daily", "per day", "each day"):
        return "SELECT order_date, total_orders, qualifying_revenue FROM v_kpi_daily ORDER BY order_date DESC LIMIT 30"
    if has("month"):
        return "SELECT order_month, total_orders, qualifying_revenue FROM v_kpi_monthly ORDER BY order_month"
    if has("kpi", "overall", "total", "revenue", "orders", "average order"):
        return "SELECT * FROM v_kpi_overall"

    return None