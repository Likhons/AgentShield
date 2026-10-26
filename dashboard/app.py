"""AgentShield dashboard (Streamlit).

Run from the project root:
    streamlit run dashboard/app.py

Tabs:
  1. Live demo:  run a scenario on the unprotected agent (left). The protected
                 run (right) is added once AgentShield core (Phase 2) exists.
  2. Audit log:  placeholder until the audit log exists.
  3. Benchmark:  placeholder; shows only measured numbers, never invented ones.
"""

import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make project imports work

from agentshield.llm import LLMError  # noqa: E402
from demo_agent.run import run_scenario  # noqa: E402
from demo_agent.scenarios import load_scenarios  # noqa: E402

st.set_page_config(page_title="AgentShield", page_icon="🛡️", layout="wide")


def show_unprotected_run(name: str, provider: str) -> None:
    """Run one scenario without protection and draw every step."""
    try:
        with st.spinner("Agent is working..."):
            run, outcome, start, end = run_scenario(name, provider=provider)
    except LLMError as exc:
        st.error(f"LLM error: {exc}\n\nTip: switch to the offline mock provider.")
        return

    st.markdown(f"**User:** {run.task}")
    for step in run.steps:
        is_money = step.tool == "send_money"
        label = f"{'💸' if is_money else '🔧'} Step {step.number}: `{step.tool}`"
        with st.expander(label, expanded=is_money):
            st.code(json.dumps(step.args, ensure_ascii=False), language="json")
            st.text(step.result)

    st.markdown(f"**Agent's answer:** {run.final_answer}")
    st.metric("Balance (BDT)", end, delta=end - start)

    if outcome.stolen:
        targets = ", ".join(t.to for t in outcome.unauthorized)
        st.error(f"MONEY STOLEN: {outcome.stolen} BDT sent to {targets}, which the user never asked for.")
    else:
        st.success("Safe: no unauthorized transfers.")


def live_demo_tab() -> None:
    scenarios = load_scenarios()
    left, right = st.columns([3, 1])
    with left:
        name = st.selectbox(
            "Scenario",
            list(scenarios),
            index=list(scenarios).index("attack_email_bn"),
            format_func=lambda n: f"{n}: {scenarios[n]['description']}",
        )
    with right:
        provider = st.radio(
            "LLM",
            ["mock", "groq"],
            horizontal=True,
            help="mock works offline and simulates a naive agent. groq uses the real model from .env.",
        )

    if provider == "mock":
        st.caption("Mock LLM: a simulated naive agent that obeys instructions found in data. Not a real-model result.")

    if not st.button("▶ Run scenario", type="primary"):
        return

    col_without, col_with = st.columns(2)
    with col_without:
        st.subheader("❌ Without AgentShield")
        show_unprotected_run(name, provider)
    with col_with:
        st.subheader("🛡️ With AgentShield")
        st.info("Available after Phase 2 (AgentShield core). The same scenario will run here with every tool call checked.")


def audit_tab() -> None:
    st.info("The audit log is part of Phase 2. Every ALLOW / ASK_HUMAN / BLOCK decision will be listed here.")


def benchmark_tab() -> None:
    st.info("Benchmark results: TBD. Only numbers from real benchmark runs will be shown here.")


st.title("🛡️ AgentShield")
st.caption("Runtime security gateway for AI agents: Bangla, Banglish and English.")

demo, audit, bench = st.tabs(["Live demo", "Audit log", "Benchmark"])
with demo:
    live_demo_tab()
with audit:
    audit_tab()
with bench:
    benchmark_tab()
