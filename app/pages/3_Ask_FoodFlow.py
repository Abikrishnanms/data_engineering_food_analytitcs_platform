"""
FoodFlow Dashboard — Natural Language Query Page
File: app/pages/3_Ask_FoodFlow.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from app.components.nlq_container import render_nlq_interface
from nlq.prompt import build_system_prompt

st.set_page_config(page_title="Ask FoodFlow — Natural Language Query", page_icon="💬", layout="wide")

render_nlq_interface()

st.divider()

# Educational & Architecture Details
with st.expander("🛡️ How NLQ Safety and Guardrails Work in FoodFlow", expanded=False):
    st.markdown("""
    ### 5-Layer Security & Safety Architecture
    1. **Pre-execution Keyword Block:** Prohibits write requests (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `GRANT`, `COPY`).
    2. **Single Statement Enforcement:** Rejects multi-statements (`SELECT ...; DROP TABLE`).
    3. **Strict View Allowlist:** Generated SQL can query **only approved analytical views** (e.g. `v_kpi_*`, `fn_top_*`), never raw base tables.
    4. **Read-Only Database Role:** The database connection uses a PostgreSQL account with `SELECT`-only permissions and strict `statement_timeout = 10s`.
    5. **Row Limit Cap:** Queries automatically truncate output at 500 rows to prevent memory exhaustion.
    6. **Honest Limitations:** Questions regarding drivers or delivery durations are politely rejected with explicit explanations of data limitations.
    """)

with st.expander("📋 View Approved Schema Context Given to the AI", expanded=False):
    prompt_context = build_system_prompt()
    st.text(prompt_context)
