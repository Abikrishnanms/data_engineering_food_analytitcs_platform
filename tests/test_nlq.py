import pytest

from nlq.prompt import build_system_prompt
from nlq.service import ask
from nlq.validator import validate_sql


@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    # Tests must never call Claude or need a key.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def fake_runner(sql):
    return ["value"], [(1,), (2,)], False


# ---------- validator ----------

def test_valid_select_passes():
    ok, _ = validate_sql("SELECT * FROM v_kpi_overall")
    assert ok


def test_trailing_semicolon_allowed():
    ok, _ = validate_sql("SELECT * FROM v_kpi_overall;")
    assert ok


def test_function_allowed():
    ok, _ = validate_sql("SELECT * FROM fn_kpi_summary('2025-06-01', '2025-06-30')")
    assert ok


def test_cte_allowed():
    ok, _ = validate_sql("WITH t AS (SELECT * FROM v_kpi_monthly) SELECT * FROM t")
    assert ok


def test_delete_rejected():
    ok, _ = validate_sql("DELETE FROM orders")
    assert not ok


def test_update_rejected():
    ok, _ = validate_sql("UPDATE v_orders_enriched SET total_amount = 0")
    assert not ok


def test_multi_statement_rejected():
    ok, reason = validate_sql("SELECT 1; DROP TABLE orders")
    assert not ok and "one statement" in reason.lower()


def test_comment_rejected():
    ok, _ = validate_sql("SELECT * FROM v_kpi_overall -- hi")
    assert not ok


def test_raw_table_rejected():
    ok, _ = validate_sql("SELECT * FROM orders")
    assert not ok


def test_system_table_rejected():
    ok, _ = validate_sql("SELECT * FROM pg_roles")
    assert not ok


def test_select_into_rejected():
    ok, _ = validate_sql("SELECT * INTO copy_table FROM v_orders_enriched")
    assert not ok


def test_sleep_rejected():
    ok, _ = validate_sql("SELECT pg_sleep(5) FROM v_kpi_overall")
    assert not ok


def test_empty_rejected():
    ok, _ = validate_sql("   ")
    assert not ok


def test_query_without_from_rejected():
    ok, _ = validate_sql("SELECT 1")
    assert not ok


# ---------- service: unsupported and unsafe questions ----------

def test_driver_question_unsupported():
    r = ask("Which driver is fastest?", runner=fake_runner)
    assert r["status"] == "unsupported" and "driver" in r["answer"].lower()


def test_delivery_minutes_unsupported():
    r = ask("How many minutes does delivery take?", runner=fake_runner)
    assert r["status"] == "unsupported"


def test_delete_request_unsupported():
    r = ask("delete all orders", runner=fake_runner)
    assert r["status"] == "unsupported"


def test_empty_question_clarify():
    assert ask("", runner=fake_runner)["status"] == "clarify"


# ---------- service: translation (rules) ----------

def test_ambiguous_best_restaurant_clarify():
    r = ask("best restaurant", runner=fake_runner)
    assert r["status"] == "clarify" and "revenue" in r["answer"].lower()


def test_month_without_year_clarify():
    r = ask("top restaurants in June", runner=fake_runner)
    assert r["status"] == "clarify"


def test_unknown_question_clarify():
    assert ask("hello there", runner=fake_runner)["status"] == "clarify"


def test_top_restaurants_success_and_show_sql():
    r = ask("top 5 restaurants in June 2025", runner=fake_runner)
    assert r["status"] == "ok"
    assert r["sql"] == "SELECT * FROM fn_top_restaurants('2025-06-01', '2025-06-30', 5)"
    assert r["rows"] == [(1,), (2,)]


# ---------- service: safety with a fake AI ----------

def test_model_write_sql_is_blocked():
    r = ask("anything", llm=lambda q: "DROP TABLE orders", runner=fake_runner)
    assert r["status"] == "blocked" and r["rows"] == []


def test_model_raw_table_is_blocked():
    r = ask("anything", llm=lambda q: "SELECT * FROM users", runner=fake_runner)
    assert r["status"] == "blocked"


def test_model_markdown_fence_is_cleaned():
    fenced = "```sql\nSELECT * FROM v_kpi_overall\n```"
    r = ask("overall", llm=lambda q: fenced, runner=fake_runner)
    assert r["status"] == "ok" and r["sql"] == "SELECT * FROM v_kpi_overall"


def test_model_unsupported_reply_passed_on():
    r = ask("anything", llm=lambda q: "UNSUPPORTED: no ratings", runner=fake_runner)
    assert r["status"] == "unsupported" and r["answer"] == "no ratings"


def test_llm_failure_is_handled():
    def broken(q):
        raise RuntimeError("boom")
    assert ask("anything", llm=broken, runner=fake_runner)["status"] == "error"


def test_database_failure_is_handled():
    def broken_runner(sql):
        raise RuntimeError("db down")
    r = ask("overall", llm=lambda q: "SELECT * FROM v_kpi_overall", runner=broken_runner)
    assert r["status"] == "error" and r["sql"] == "SELECT * FROM v_kpi_overall"


def test_truncated_result_warns():
    r = ask("overall", llm=lambda q: "SELECT * FROM v_kpi_overall",
            runner=lambda sql: (["a"], [(1,)], True))
    assert r["status"] == "ok" and "500" in r["warning"]


# ---------- prompt ----------

def test_prompt_contains_schema_and_limits():
    p = build_system_prompt()
    assert "v_orders_enriched" in p and "driver" in p.lower()