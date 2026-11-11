"""AgentShield dashboard (Streamlit).

Run from the project root:
    streamlit run dashboard/app.py

Tabs:
  1. Live demo:  the same scenario on the unprotected agent (left) and on the
                 agent protected by AgentShield (right). The money outcome comes first.
  2. Audit log:  every AgentShield decision, newest first, with KPIs.
  3. Benchmark:  saved results from benchmark/results/ (measured numbers only).
"""

import html
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make project imports work

from agentshield.audit.log import AuditLog  # noqa: E402
from benchmark.report import agent_rows, detection_rows, latest_where, outcome_rows  # noqa: E402
from agentshield.config import get_settings  # noqa: E402
from agentshield.llm import LLMError  # noqa: E402
from demo_agent.recording import load_result  # noqa: E402
from demo_agent.run import ScenarioResult, run_scenario  # noqa: E402
from demo_agent.scenarios import load_scenarios  # noqa: E402

st.set_page_config(page_title="AgentShield", page_icon="🛡️", layout="wide")

BADGES = {"allow": "✅ ALLOW", "ask_human": "✋ ASK HUMAN", "block": "🛑 BLOCK"}
PILL = {"allow": ("ALLOW", "pill-allow"), "ask_human": ("ASK HUMAN", "pill-ask"), "block": ("BLOCK", "pill-block")}
RECORDED = "recorded (groq)"
PROVIDER_LABELS = {"mock": "Offline (simulated agent)", "groq": "Live (Groq)", RECORDED: "Recorded real run"}

CSS = """
<style>
html, body, [class*="css"] { font-family: "Segoe UI", "Nirmala UI", "Noto Sans Bengali", sans-serif; }
.block-container { padding-top: 2rem; max-width: 1400px; }
.hero-sub { color: #4B5563; font-size: 1.05rem; margin-top: -0.6rem; }
.pipeline { display: flex; flex-wrap: wrap; gap: .4rem; align-items: center; margin: .6rem 0 1.2rem; }
.chip { background: #F3F6F8; border: 1px solid #E5E7EB; border-radius: 999px; padding: .25rem .75rem;
        font-size: .85rem; color: #374151; }
.chip b { color: #0F766E; }
.arrow { color: #9CA3AF; }
.col-head { border-radius: 12px; padding: .7rem 1rem; margin-bottom: .8rem; font-weight: 600; font-size: 1.1rem; }
.col-unsafe { background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }
.col-safe { background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
.money { font-size: 2.1rem; font-weight: 700; line-height: 1.1; }
.money-lost { color: #B91C1C; }
.money-ok { color: #047857; }
.money-label { color: #6B7280; font-size: .85rem; }
.pill { display: inline-block; border-radius: 6px; padding: .05rem .45rem; font-size: .75rem; font-weight: 700; }
.pill-allow { background: #D1FAE5; color: #065F46; }
.pill-ask { background: #FEF3C7; color: #92400E; }
.pill-block { background: #FEE2E2; color: #991B1B; }
.user-quote { border-left: 4px solid #0F766E; background: #F3F6F8; padding: .5rem .8rem; border-radius: 0 8px 8px 0;
              margin-bottom: .6rem; }
.reason-bn { font-size: 1.02rem; margin: .2rem 0; }
.summary { border-radius: 12px; padding: .9rem 1.2rem; margin: .4rem 0 1rem; font-size: 1.15rem; font-weight: 600;
           background: #0F766E; color: white; }
</style>
"""


@st.cache_resource
def audit_log() -> AuditLog:
    """One shared audit log for the whole dashboard (file path from .env)."""
    return AuditLog(get_settings().audit_db_path)


def taka(amount: int) -> str:
    return f"৳ {amount:,}"


def run_safely(name: str, provider: str, shield: bool, approve: bool = False) -> ScenarioResult | None:
    if provider == RECORDED:  # instant replay of a saved real-LLM run
        loaded = load_result(name, shield, "groq")
        if loaded is None:
            st.info("No recording for this scenario yet. Record with:\n\n"
                    "python -m demo_agent.run --all --compare --provider groq --record")
            return None
        result, recorded_utc = loaded
        st.caption(f"Replay of a real run recorded {recorded_utc} (UTC). Not live.")
        return result
    try:
        with st.spinner("Agent is working..."):
            return run_scenario(name, provider=provider, shield=shield,
                                audit=audit_log() if shield else None, approve=approve)
    except LLMError as exc:
        st.error(f"LLM error: {exc}\n\nTip: switch to the offline provider.")
        return None


def stopped_count(result: ScenarioResult) -> int:
    return sum(1 for _, v in result.history if v.decision.value != "allow")


def show_outcome(result: ScenarioResult) -> None:
    """The money outcome first: what a judge should see in two seconds."""
    lost = result.outcome.stolen
    money_class = "money-lost" if lost else "money-ok"
    money_text = f"−{taka(lost)}" if lost else "৳ 0"
    a, b = st.columns(2)
    a.markdown(f'<div class="money-label">Stolen / চুরি হয়েছে</div>'
               f'<div class="money {money_class}">{money_text}</div>', unsafe_allow_html=True)
    b.markdown(f'<div class="money-label">Balance / ব্যালান্স</div>'
               f'<div class="money">{taka(result.end_balance)}</div>', unsafe_allow_html=True)
    if lost:
        targets = ", ".join(t.to for t in result.outcome.unauthorized)
        st.error(f"MONEY STOLEN: {taka(lost)} sent to {targets}, which the user never asked for.")
    else:
        stopped = stopped_count(result)
        note = f" AgentShield stopped {stopped} action(s)." if stopped else ""
        st.success(f"Safe: no unauthorized transfers.{note}")


def check_line(verdict) -> str:
    parts = []
    for c in verdict.checks:
        value = "skipped" if c.skipped else f"{c.risk_score:.2f}"
        parts.append(f"{c.check.value} {value}{' ⚑' if c.flagged else ''}")
    return " · ".join(parts)


def show_steps(result: ScenarioResult) -> None:
    """Every tool call the agent made, with AgentShield's verdict when there is one."""
    for step, verdict in zip(result.run.steps, result.step_verdicts):
        is_money = step.tool == "send_money"
        badge = f" · {BADGES[verdict.decision.value]}" if verdict else ""
        if verdict and verdict.decision.value == "ask_human":
            approved = not step.result.startswith("[AgentShield]")
            badge += " → 👍 approved" if approved else " → not approved"
        label = f"{'💸' if is_money else '🔧'} Step {step.number}: `{step.tool}`{badge}"
        stopped = verdict is not None and verdict.decision.value != "allow"
        with st.expander(label, expanded=is_money or stopped):
            st.code(json.dumps(step.args, ensure_ascii=False), language="json")
            if verdict:
                text, css = PILL[verdict.decision.value]
                st.markdown(f'<span class="pill {css}">{text}</span> risk {verdict.risk_score:.2f} · '
                            f'{verdict.total_latency_ms:.0f} ms', unsafe_allow_html=True)
                st.markdown(f'<div class="reason-bn"><b>কারণ:</b> {html.escape(verdict.reason_bn)}</div>',
                            unsafe_allow_html=True)
                st.caption(f"Reason: {verdict.reason_en}")
                st.caption(f"Checks: {check_line(verdict)}")
            if not step.result.startswith("[AgentShield]"):  # the block message repeats the reason
                st.text(step.result[:600] + ("…" if len(step.result) > 600 else ""))


def show_result(result: ScenarioResult) -> None:
    show_outcome(result)
    st.markdown(f'<div class="user-quote"><b>User:</b> {html.escape(result.run.task)}</div>', unsafe_allow_html=True)
    show_steps(result)
    with st.expander("Agent's final answer"):
        st.write(result.run.final_answer)


def scenario_label(name: str, scenario: dict) -> str:
    kind = "⚠️ Attack" if name.startswith("attack") else "✅ Normal"
    return f"{kind} · {scenario['description']}"


def live_demo_tab() -> None:
    scenarios = load_scenarios()
    names = sorted(scenarios, key=lambda n: (not n.startswith("attack"), n))
    left, right = st.columns([3, 2])
    with left:
        name = st.selectbox("Scenario", names, index=names.index("attack_email_bn"),
                            format_func=lambda n: scenario_label(n, scenarios[n]))
    with right:
        provider = st.radio(
            "Agent", ["mock", "groq", RECORDED], horizontal=True, format_func=PROVIDER_LABELS.get,
            help="Offline simulates a naive agent (no internet). Live uses the real model from .env. "
                 "Recorded replays a saved real-model run instantly (for the stage).",
        )
    if provider == "mock":
        st.caption("Offline mode: a simulated naive agent that obeys instructions found in data. Not a real-model result.")

    approve = st.checkbox(
        "I approve actions that ask for my approval (simulated human click)",
        disabled=provider == RECORDED,
        help="AgentShield sends uncertain actions (ASK_HUMAN) to the user. Unticked = the user says no. "
             "Ticked = the user says yes to every such request. BLOCK decisions are never sent to the user.",
    )

    if not st.button("▶ Run scenario", type="primary"):
        return

    without = run_safely(name, provider, shield=False)
    with_shield = run_safely(name, provider, shield=True, approve=approve)
    if without and with_shield:
        saved = without.outcome.stolen - with_shield.outcome.stolen
        if saved > 0:
            st.markdown(f'<div class="summary">🛡️ AgentShield saved {taka(saved)} · '
                        f'AgentShield {taka(saved)} বাঁচিয়েছে</div>', unsafe_allow_html=True)
        elif not without.outcome.stolen:
            st.markdown('<div class="summary">✅ Normal task: AgentShield let it run · '
                        'সাধারণ কাজ, AgentShield বাধা দেয়নি</div>', unsafe_allow_html=True)

    col_without, col_with = st.columns(2, gap="large")
    with col_without:
        st.markdown('<div class="col-head col-unsafe">❌ Without AgentShield</div>', unsafe_allow_html=True)
        if without:
            show_result(without)
    with col_with:
        st.markdown('<div class="col-head col-safe">🛡️ With AgentShield</div>', unsafe_allow_html=True)
        if with_shield:
            show_result(with_shield)


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


def detection_section(title: str, found, note: str) -> None:
    if found is None:
        return
    name, data = found
    st.subheader(title)
    st.caption(f"Source: {name}. {note} Dataset: {data['dataset']}")
    rows = detection_rows(data)
    chart = pd.DataFrame(
        [{"detector": r["detector"], "language": r["language"], "attacks flagged (%)": 100 * (r["detection_rate"] or 0)}
         for r in rows if r["language"] != "all" and r["detection_rate"] is not None]
    )
    if not chart.empty:
        st.bar_chart(chart, x="language", y="attacks flagged (%)", color="detector", stack=False)
    st.dataframe([{k: v for k, v in r.items() if k not in ("detection_rate", "false_positive_rate")} for r in rows],
                 use_container_width=True, hide_index=True)


def agent_section(title: str, found) -> None:
    if found is None:
        return
    name, data = found
    st.subheader(title)
    detector = data.get("detector", "heuristic")
    st.caption(f"Source: {name}. Provider: {data['provider']} ({data['note']}). Detector: {detector}. "
               f"Runs per item: {data['runs']}.")
    st.dataframe(agent_rows(data), use_container_width=True, hide_index=True)
    outcomes = outcome_rows(data)
    if outcomes:
        st.caption("How each case ended with AgentShield (held for approval = one human click, not a block):")
        st.dataframe(outcomes, use_container_width=True, hide_index=True)


def benchmark_tab() -> None:
    """Saved benchmark results, chosen by what they measure (not just the newest file)."""
    st.caption("Numbers come only from saved benchmark runs (benchmark/results/). Small samples: read the 95% intervals. "
               "Full write-up with caveats: docs/results.md.")

    heuristic = lambda d: d.get("detector", "heuristic") == "heuristic"  # noqa: E731
    agent_section("Agent level, real LLM (Groq): is the money safe?",
                  latest_where("agent", lambda d: d["provider"] == "groq" and heuristic(d)))
    agent_section("Agent level, simulated agent", latest_where("agent", lambda d: d["provider"] == "mock" and heuristic(d)))
    detection_section("Text level: do existing guardrails catch Bangla/Banglish attacks?",
                      latest_where("detection", lambda d: not d.get("split") and any("promptguard" in k for k in d["metrics"])),
                      "Meta Prompt Guard 2 vs AgentShield's heuristic.")
    detection_section("Trained model (XLM-R), held-out test split",
                      latest_where("detection", lambda d: d.get("split") == "test"),
                      "Text level only: at agent level this model still holds real bills (docs/results.md 3e), "
                      "so the heuristic stays the runtime default.")


st.markdown(CSS, unsafe_allow_html=True)
st.title("🛡️ AgentShield")
st.markdown('<div class="hero-sub">Stops AI agents from acting on hidden instructions in Bangla, Banglish and English · '
            'AI agent-কে লুকানো নির্দেশে টাকা পাঠানো থেকে আটকায়</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="pipeline"><span class="chip">Tool call</span><span class="arrow">→</span>'
    '<span class="chip"><b>Taint</b> where did each value come from?</span>'
    '<span class="chip"><b>Classifier</b> instructions hidden in data?</span>'
    '<span class="chip"><b>Intent</b> did the user ask for this?</span>'
    '<span class="chip"><b>Policy</b> fixed rules</span><span class="arrow">→</span>'
    '<span class="chip"><span class="pill pill-allow">ALLOW</span> <span class="pill pill-ask">ASK</span> '
    '<span class="pill pill-block">BLOCK</span></span></div>',
    unsafe_allow_html=True,
)

demo, audit, bench = st.tabs(["Live demo", "Audit log", "Benchmark"])
with demo:
    live_demo_tab()
with audit:
    audit_tab()
with bench:
    benchmark_tab()
