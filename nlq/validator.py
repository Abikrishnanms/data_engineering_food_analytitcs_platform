import re

ALLOWED_VIEWS = {"v_orders_enriched", "v_order_items_enriched"}

FORBIDDEN = (
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|"
    r"copy|call|execute|into|vacuum|pg_sleep|pg_read_file)\b"
)


def validate_sql(sql: str):
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

    ctes = set(re.findall(r"(?:with|,)\s*(\w+)\s+as\s*\(", s, re.IGNORECASE))
    s_check = re.sub(r"extract\s*\([^()]*\)", "", s, flags=re.IGNORECASE)

    tables = re.findall(r"\b(?:from|join)\s+([a-zA-Z_][\w.]*)", s_check, re.IGNORECASE)
    for t in tables:
        name = t.lower()
        if name not in ALLOWED_VIEWS and name not in {c.lower() for c in ctes}:
            return False, f"'{t}' is not an approved view."

    return True, s


if __name__ == "__main__":
    tests = [
        "SELECT restaurant_name, SUM(qualifying_revenue) FROM v_orders_enriched GROUP BY 1",
        "DELETE FROM orders",
        "SELECT 1; DROP TABLE orders",
        "SELECT * FROM orders",
        "SELECT * FROM v_orders_enriched -- hi",
    ]
    for q in tests:
        print(validate_sql(q), "<-", q)