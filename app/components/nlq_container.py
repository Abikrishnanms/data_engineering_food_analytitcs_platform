"""
FoodFlow Natural Language Query (NLQ) Component
File: app/components/nlq_container.py
Description:
    Interactive Streamlit component enabling users to ask business questions
    in plain English, view generated safe SQL, and inspect tabular results.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
from nlq.service import ask


SAMPLE_QUESTIONS = [
    "Top 5 restaurants by revenue in June 2025",
    "Monthly revenue",
    "What was the cancellation rate in June 2025?",
    "Payment method split in June 2025",
    "Which cuisines earn the most revenue?",
    "How many repeat customers do we have?",
    "Which driver is fastest?",            # Demonstrates honest unsupported question
    "Delete all orders from database",    # Demonstrates adversarial query rejection
]


def render_nlq_interface():
    """Render the full interactive Natural Language Query section."""
    st.subheader("💬 Ask FoodFlow in Natural Language")
    st.markdown(
        "Ask analytical questions in English. FoodFlow translates your question into **safe, "
        "read-only SQL** executed against pre-approved analytics views."
    )

    # Preset quick-question pills
    st.caption("Quick example questions:")
    cols = st.columns(4)
    preset_clicked = None
    for idx, sample in enumerate(SAMPLE_QUESTIONS[:4]):
        with cols[idx]:
            if st.button(f"📌 {sample[:26]}...", key=f"sample_{idx}", help=sample):
                preset_clicked = sample

    col_more1, col_more2, col_more3, col_more4 = st.columns(4)
    for idx, sample in enumerate(SAMPLE_QUESTIONS[4:], start=4):
        with [col_more1, col_more2, col_more3, col_more4][idx - 4]:
            if st.button(f"📌 {sample[:26]}...", key=f"sample_{idx}", help=sample):
                preset_clicked = sample

    user_query = st.text_input(
        "Enter your question:",
        value=preset_clicked if preset_clicked else "",
        placeholder="e.g. Top 5 restaurants in June 2025, or monthly cancellation rate",
        key="nlq_user_input",
    )

    if st.button("🚀 Run Question", type="primary") or (preset_clicked and user_query):
        if not user_query.strip():
            st.warning("Please type a question or select an example above.")
            return

        with st.spinner("Analyzing question and generating verified SQL..."):
            response = ask(user_query)

        status = response.get("status")
        answer = response.get("answer")
        sql = response.get("sql")
        columns = response.get("columns", [])
        rows = response.get("rows", [])
        warning = response.get("warning")

        if status == "ok":
            st.success(f"✅ {answer}")
            if warning:
                st.info(f"ℹ️ {warning}")

            # Tabular results
            if columns and rows:
                df = pd.DataFrame(rows, columns=columns)
                st.dataframe(df, use_container_width=True)

            # Show SQL expandable container
            with st.expander("🔍 Show SQL (Validated Read-Only Query)", expanded=True):
                st.code(sql, language="sql")
                st.caption("Executed using read-only role with a 10s statement timeout.")

        elif status == "clarify":
            st.info(f"🤔 **Clarification Needed:** {answer}")
            st.caption("Tip: Specify year (e.g., 'June 2025') or specify whether 'best' means highest revenue or most orders.")

        elif status == "unsupported":
            st.warning(f"⚠️ **Dataset Limitation:** {answer}")
            st.caption(
                "FoodFlow maintains strict honesty about dataset limitations: "
                "no driver tracking exists, and delivery_time is a clock time rather than a duration."
            )

        elif status == "blocked":
            st.error(f"🛑 **Safety Guardrail Blocked:** {answer}")
            if warning:
                st.caption(f"Reason: {warning}")
            if sql:
                with st.expander("Blocked Statement"):
                    st.code(sql, language="sql")

        else:
            st.error(f"❌ **Error:** {answer}")
            if sql:
                with st.expander("Attempted Query"):
                    st.code(sql, language="sql")
