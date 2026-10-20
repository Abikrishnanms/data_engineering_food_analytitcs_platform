import re

# The only views/functions the AI is allowed to use.
ALLOWED_VIEWS = {
    "v_orders_enriched",
    "v_order_items_enriched",
    "v_kpi_daily",
    "v_kpi_monthly",
    "v_kpi_overall",
    "fn_kpi_summary",
    # Add the v_q... view names from 20_business_questions.sql here later.
}

# Words that must never appear in a read-only query.
FORBIDDEN = (
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|"
    r"copy|call|execute|into|vacuum|pg_sleep|pg_read_file)\b"
)


def validate_sql(sql: str):
    """Return (True, clean_sql) if safe, otherwise (False, reason)."""
    if not sql or not sql.strip():
        return False, "Empty query."

    s = sql.strip()
    if s.endswith(";"):
        s = s[:-1].strip()

    if ";" in s:
        return False, "Only one statement is allowed."
    if "--" in s or "/*" in s:
        return False, "Comments are not allowed."
    if not re.match(r"^(select|with)\b", s, re.IGNORECASE):
        return False, "Query must start with SELECT or WITH."
    if re.search(FORBIDDEN, s, re.IGNORECASE):
        return False, "Query contains a forbidden keyword."

    # Names created by WITH ... AS (...) are temporary, so they are allowed.
    ctes = {c.lower() for c in re.findall(r"(?:with|,)\s*(\w+)\s+as\s*\(", s, re.IGNORECASE)}

    # EXTRACT(HOUR FROM col) contains "FROM", so remove it before checking tables.
    s_check = re.sub(r"extract\s*\([^()]*\)", "", s, flags=re.IGNORECASE)

    tables = re.findall(r"\b(?:from|join)\s+([a-zA-Z_][\w.]*)", s_check, re.IGNORECASE)
    if not tables:
        return False, "Query must read from an approved view."

    for t in tables:
        name = t.lower()
        if name not in ALLOWED_VIEWS and name not in ctes:
            return False, f"'{t}' is not an approved view."

    return True, s


if __name__ == "__main__":
    tests = [
        "SELECT restaurant_name, SUM(qualifying_revenue) FROM v_orders_enriched GROUP BY 1",
        "SELECT * FROM fn_kpi_summary('2025-06-01', '2025-06-30')",
        "SELECT * FROM v_kpi_monthly ORDER BY order_month",
        "DELETE FROM orders",
        "SELECT 1; DROP TABLE orders",
        "SELECT * FROM orders",
        "SELECT * FROM v_orders_enriched -- hi",
        "SELECT * FROM pg_roles",
    ]
    for q in tests:
        print(validate_sql(q), "<-", q)