import os
import re

from dotenv import load_dotenv

from nlq.executor import run_query
from nlq.prompt import build_system_prompt
from nlq.rules import rule_based_sql
from nlq.validator import validate_sql

load_dotenv()

MODEL = "claude-sonnet-4-6"

HELP_TEXT = (
    "CLARIFY: I did not understand. Try: top 5 restaurants in June 2025, "
    "weekly orders, monthly revenue, cancellation rate, or repeat customers."
)

UNSUPPORTED_PATTERNS = [
    (r"\b(driver|drivers|rider|courier)\b", "FoodFlow has no driver data."),
    (r"(how (long|many minutes)|delivery (time|duration)|minutes to deliver)",
     "FoodFlow does not record delivery duration. delivery_time is only a clock time."),
    (r"\b(delete|drop|truncate|update|insert|alter)\b",
     "This assistant is read-only and cannot change data."),
]


def _response(status, answer, sql=None, columns=None, rows=None, warning=None):
    return {
        "status": status,        # ok, unsupported, clarify, blocked, error
        "answer": answer,
        "sql": sql,
        "columns": columns or [],
        "rows": rows or [],
        "warning": warning,
    }


def _ask_llm(question: str) -> str:
    """Use Claude when ANTHROPIC_API_KEY is set."""
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    msg = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system=build_system_prompt(),
        messages=[{"role": "user", "content": question}],
    )
    return msg.content[0].text.strip()


def _ask_rules(question: str) -> str:
    """Free fallback: translate the question with built-in rules."""
    return rule_based_sql(question) or HELP_TEXT


def _clean(text: str) -> str:
    return re.sub(r"^```(?:sql)?|```$", "", text.strip(), flags=re.MULTILINE).strip()


def ask(question: str, llm=None, runner=run_query):
    question = (question or "").strip()
    if not question:
        return _response("clarify", "Please type a question.")

    for pattern, message in UNSUPPORTED_PATTERNS:
        if re.search(pattern, question, re.IGNORECASE):
            return _response("unsupported", message)

    # Choose the translator: a custom one (tests), Claude (if key), or rules.
    if llm is None:
        llm = _ask_llm if os.getenv("ANTHROPIC_API_KEY") else _ask_rules

    try:
        reply = _clean(llm(question))
    except Exception:
        return _response("error", "Sorry, the question could not be translated.")

    if reply.upper().startswith("UNSUPPORTED:"):
        return _response("unsupported", reply.split(":", 1)[1].strip())
    if reply.upper().startswith("CLARIFY:"):
        return _response("clarify", reply.split(":", 1)[1].strip())

    ok, result = validate_sql(reply)
    if not ok:
        return _response("blocked", "That question could not be answered safely.",
                         sql=reply, warning=result)

    try:
        columns, rows, truncated = runner(result)
    except Exception:
        return _response("error", "The database could not run this query.", sql=result)

    warning = "Showing the first 500 rows only." if truncated else None
    return _response("ok", f"Found {len(rows)} row(s).", sql=result,
                     columns=columns, rows=rows, warning=warning)