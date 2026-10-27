"""AgentShield dashboard (Streamlit).

Run from the project root:
    streamlit run dashboard/app.py

Tabs:
  1. Live demo:  the same scenario on the unprotected agent (left) and on the
                 agent protected by AgentShield (right).
  2. Audit log:  every AgentShield decision, newest first, with KPIs.
  3. Benchmark:  latest saved results from benchmark/results/ (measured numbers only).
"""

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make project imports work

from agentshield.audit.log import AuditLog  # noqa: E402
from benchmark.report import agent_rows, detection_rows, latest  # noqa: E402
from agentshield.config import get_settings  # noqa: E402
from agentshield.llm import LLMError  # noqa: E402
from demo_agent.run import ScenarioResult, run_scenario  # noqa: E402
from demo_agent.scenarios import load_scenarios  # noqa: E402

st.set_page_config(page_title="AgentShield", page_icon="🛡️", layout="wide")

BADGES = {"allow": "✅ ALLOW", "ask_human": "✋ ASK HUMAN", "block": "🛑 BLOCK"}


@st.cache_resource
def audit_log() -> AuditLog:
    """One shared audit log for the whole dashboard (file path from .env)."""
    return AuditLog(get_settings().audit_db_path)


def run_safely(name: str, provider: str, shield: bool) -> ScenarioResult | None:
    try:
        with st.spinner("Agent is working..."):
            return run_scenario(name, provider=provider, shield=shield, audit=audit_log() if shield else None)
    except LLMError as exc:
        st.error(f"LLM error: {exc}\n\nTip: switch to the offline mock provider.")
        return None


def show_result(result: ScenarioResult) -> None:
    """Draw every step of a run, with AgentShield's verdict when there is one."""
    st.markdown(f"**User:** {result.run.task}")
    for step, verdict in zip(result.run.steps, result.step_verdicts):
        is_money = step.tool == "send_money"
        badge = f" · {BADGES[verdict.decision.value]}" if verdict else ""
        label = f"{'💸' if is_money else '🔧'} Step {step.number}: `{step.tool}`{badge}"
        stopped = verdict is not None and verdict.decision.value != "allow"
        with st.expander(label, expanded=is_money or stopped):
            st.code(json.dumps(step.args, ensure_ascii=False), language="json")
            if verdict:
                st.caption(f"Risk {verdict.risk_score:.2f} · {verdict.total_latency_ms:.0f} ms")
                st.markdown(f"**কারণ:** {verdict.reason_bn}")
                st.markdown(f"**Reason:** {verdict.reason_en}")
            st.text(step.result)

    st.markdown(f"**Agent's answer:** {result.run.final_answer}")
    st.metric("Balance (BDT)", result.end_balance, delta=result.end_balance - result.start_balance)
    if result.outcome.stolen:
        targets = ", ".join(t.to for t in result.outcome.unauthorized)
        st.error(f"MONEY STOLEN: {result.outcome.stolen} BDT sent to {targets}, which the user never asked for.")
    else:
        stopped = sum(1 for _, v in result.history if v.decision.value != "allow")
        note = f" AgentShield stopped {stopped} action(s)." if stopped else ""
        st.success(f"Safe: no unauthorized transfers.{note}")


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
        result = run_safely(name, provider, shield=False)
        if result:
            show_result(result)
    with col_with:
        st.subheader("🛡️ With AgentShield")
        result = run_safely(name, provider, shield=True)
        if result:
            show_result(result)


def audit_tab() -> None:
    log = audit_log()
    stats = log.stats()
    cols = st.columns(5)
    cols[0].metric("Checked calls", stats["total"])
    cols[1].metric("Allowed", stats["allow"])
    cols[2].metric("Asked human", stats["ask_human"])
    cols[3].metric("Blocked", stats["block"])
    median = stats["median_latency_ms"]
    cols[4].metric("Median latency", f"{median:.1f} ms" if median is not None else "–")
    st.caption(f"LLM judge called for {stats['llm_calls']} of {stats['total']} checks.")

    records = log.recent(limit=100)
    if not records:
        st.info("No decisions yet. Run a scenario in the Live demo tab.")
        return
    st.dataframe(
        [
            {
                "time (UTC)": r.timestamp.strftime("%H:%M:%S"),
                "tool": r.tool_name,
                "decision": BADGES[r.decision.value],
                "risk": round(r.risk_score, 2),
                "arguments": json.dumps(r.arguments, ensure_ascii=False),
                "কারণ": r.reason_bn,
                "user request": r.user_request,
            }
            for r in records
        ],
        use_container_width=True,
        hide_index=True,
    )


def benchmark_tab() -> None:
    """Latest saved benchmark results. Only measured numbers, read from benchmark/results/."""
    st.caption("Numbers come only from saved benchmark runs (benchmark/results/). Small samples: read the 95% intervals.")

    detection = latest("detection")
    if detection is None:
        st.info("No text-level benchmark run yet: python -m benchmark.run_detection")
    else:
        name, data = detection
        st.subheader("Text level: do detectors flag attack texts?")
        st.caption(f"Source: {name}. Dataset: {data['dataset']}")
        rows = detection_rows(data)
        chart = pd.DataFrame(
            [{"detector": r["detector"], "language": r["language"], "attacks flagged (%)": 100 * (r["detection_rate"] or 0)}
             for r in rows if r["language"] != "all" and r["detection_rate"] is not None]
        )
        if not chart.empty:
            st.bar_chart(chart, x="language", y="attacks flagged (%)", color="detector", stack=False)
        st.dataframe(
            [{k: v for k, v in r.items() if k not in ("detection_rate", "false_positive_rate")} for r in rows],
            use_container_width=True, hide_index=True,
        )

    agent = latest("agent")
    if agent is None:
        st.info("No agent-level benchmark run yet: python -m benchmark.run_agent")
    else:
        name, data = agent
        st.subheader("Agent level: is the money safe?")
        st.caption(f"Source: {name}. Provider: {data['provider']} ({data['note']}). Runs per item: {data['runs']}.")
        st.dataframe(agent_rows(data), use_container_width=True, hide_index=True)


st.title("🛡️ AgentShield")
st.caption("Runtime security gateway for AI agents: Bangla, Banglish and English.")

demo, audit, bench = st.tabs(["Live demo", "Audit log", "Benchmark"])
with demo:
    live_demo_tab()
with audit:
    audit_tab()
with bench:
    benchmark_tab()
