"""AgentShield dashboard (Streamlit), dark "security command center" design.

Run from the project root:
    streamlit run dashboard/app.py

Pages (left sidebar):
  Playground  run a scenario on the unprotected agent and on the agent protected by
              AgentShield, side by side; plus how it works and recent decisions.
  Benchmarks  saved results from benchmark/results/ (measured numbers only).
  Audit Log   every AgentShield decision, newest first, with KPIs.
  Policies    the deterministic rules in policies/default.yaml.
  Datasets    the labeled Bangla / Banglish / English data used by the benchmark.

Every number on screen comes from a real source (policy file, dataset, audit log,
benchmark results). Nothing is hard-coded.
"""

import json
import re
import sys
import tomllib
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # make project imports work

from agentshield.audit.log import AuditLog  # noqa: E402
from agentshield.checks.policy import DEFAULT_POLICY_PATH  # noqa: E402
from agentshield.config import get_settings  # noqa: E402
from agentshield.core.models import CheckName  # noqa: E402
from agentshield.llm import LLMError  # noqa: E402
from benchmark.dataset import load_dataset, summarize  # noqa: E402
from benchmark.report import agent_rows, detection_rows, latest_where, outcome_rows  # noqa: E402
from dashboard import ui  # noqa: E402
from demo_agent.recording import load_result  # noqa: E402
from demo_agent.run import ScenarioResult, run_scenario  # noqa: E402
from demo_agent.scenarios import load_scenarios  # noqa: E402

st.set_page_config(page_title="AgentShield", page_icon="🛡️", layout="wide", initial_sidebar_state="auto")

BADGES = {"allow": "✅ ALLOW", "ask_human": "✋ ASK HUMAN", "block": "🛑 BLOCK"}
RECORDED = "recorded (groq)"
MODES = {
    "mock": (":material/smart_toy: Offline (simulated)", "A naive agent that obeys instructions found in data. No internet."),
    "groq": (":material/wifi: Live (Groq)", "The real model from .env, with the same tools."),
    RECORDED: (":material/play_circle: Recorded run", "Instant replay of a saved real-model run."),
}
PAGES = {
    "Playground": ":material/play_circle: Playground",
    "Benchmarks": ":material/bar_chart: Benchmarks",
    "Audit Log": ":material/receipt_long: Audit Log",
    "Policies": ":material/policy: Policies",
    "Datasets": ":material/database: Datasets",
}


# ---------------------------------------------------------------------------
# Data sources (real, cached where cheap to cache)
# ---------------------------------------------------------------------------
@st.cache_resource
def audit_log() -> AuditLog:
    """One shared audit log for the whole dashboard (file path from .env)."""
    return AuditLog(get_settings().audit_db_path)


@st.cache_data
def policy_rules() -> list[dict]:
    return yaml.safe_load(Path(DEFAULT_POLICY_PATH).read_text(encoding="utf-8")).get("rules", [])


@st.cache_data
def dataset_summary() -> dict:
    return summarize(load_dataset())


@st.cache_data
def app_version() -> str:
    try:
        return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return "dev"


def heuristic_run(data: dict) -> bool:
    return data.get("detector", "heuristic") == "heuristic"


def real_llm_attack_numbers() -> tuple[str, str, str] | None:
    """(with, without, source) attack success from the newest real-LLM run, e.g. ("0/20", "4/20", "agent_...")."""
    found = latest_where("agent", lambda d: d["provider"] == "groq" and heuristic_run(d))
    if found is None:
        return None
    name, data = found
    row = next((r for r in agent_rows(data) if r["language"] == "all"), None)
    if row is None:
        return None

    def frac(cell: str) -> str:
        m = re.search(r"\((\d+)/(\d+)", cell)
        return f"{m.group(1)}/{m.group(2)}" if m else "–"

    return frac(row["attack success WITH AgentShield"]), frac(row["attack success WITHOUT AgentShield"]), name


def short(text: str, limit: int) -> str:
    """Cut at a word boundary and mark the cut, so table cells never end mid-word."""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(".,;:") + "…"


def taka(amount: int) -> str:
    return f"৳ {amount:,}"


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def sidebar() -> str:
    with st.sidebar:
        st.markdown(f'<div class="brand">{ui.icon("shield-check", 34, "#B44CFF")}'
                    '<div><div class="brand-name">AgentShield</div><div class="brand-sub">AI Agent Safety Platform</div></div></div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="side-label">Navigate</div>', unsafe_allow_html=True)
        names = list(PAGES)
        wanted = st.query_params.get("page", "Playground")
        with st.container(key="nav"):
            page = st.radio("Navigation", names, index=names.index(wanted) if wanted in names else 0,
                            format_func=PAGES.get, label_visibility="collapsed", key="nav_page")
        if st.query_params.get("page") != page:
            st.query_params["page"] = page

        settings = get_settings()
        stats = audit_log().stats()
        rows = [
            ("Agent LLM", settings.llm_provider),
            ("Injection detector", settings.detector),
            ("Checks", str(len(CheckName))),
            ("Policy rules", str(len(policy_rules()))),
            ("Decisions logged", str(stats["total"])),
        ]
        body = "".join(f'<div class="status-row"><span>{ui.esc(k)}</span><b>{ui.esc(v)}</b></div>' for k, v in rows)
        st.markdown(f'<div class="status"><div class="status-head"><span class="dot"></span>Gateway ready</div>{body}'
                    f'<div class="version">v{ui.esc(app_version())}</div></div>', unsafe_allow_html=True)
    return page


# ---------------------------------------------------------------------------
# Playground
# ---------------------------------------------------------------------------
def hero() -> None:
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.markdown(
            '<div class="hero"><h1>Stop AI Agents from Acting on <span class="grad">Hidden Instructions</span></h1>'
            '<p class="lead">AgentShield checks every tool call before it runs, so an AI agent cannot be tricked into '
            'sending money by text hidden in emails, web pages or files, in Bangla, Banglish and English.</p>'
            '<div class="cta-row">'
            f'<a class="cta cta-primary" href="#run-scenario">{ui.icon("play", 16, "#fff")}Try a Scenario</a>'
            f'<a class="cta cta-ghost" href="?page=Benchmarks" target="_self">{ui.icon("chart", 16)}View Benchmarks</a>'
            '</div></div>', unsafe_allow_html=True)
    with right:
        st.markdown(ui.hero_art(), unsafe_allow_html=True)


def kpis() -> None:
    summary = dataset_summary()
    attacks = {lang: c.get("attack", 0) for lang, c in summary.items()}
    measured = real_llm_attack_numbers()
    if measured:
        with_shield, without, source = measured
        last = ui.kpi("chart", "#16C784", with_shield, "Attacks that moved money (real LLM)",
                      note=f"without AgentShield: {without} · {source}")
    else:
        last = ui.kpi("chart", "#16C784", "–", "Attacks that moved money (real LLM)", note="no real-LLM run yet")
    cards = [
        ui.kpi("shield-check", "#B44CFF", str(len(CheckName)), "Security checks per tool call",
               note=" · ".join(c.value for c in CheckName)),
        ui.kpi("list-checks", "#5B8CFF", str(len(policy_rules())), "Deterministic policy rules", note="policies/default.yaml"),
        ui.kpi("bug", "#F04452", str(sum(attacks.values())), "Labeled attack samples",
               note=" · ".join(f"{k} {v}" for k, v in sorted(attacks.items()))),
        last,
    ]
    st.markdown(f'<div class="kpis">{"".join(cards)}</div>', unsafe_allow_html=True)


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
        st.error(f"LLM error: {exc}\n\nTip: switch to Offline mode.")
        return None


def scenario_label(name: str, scenario: dict) -> str:
    kind = "⚠️ Attack" if name.startswith("attack") else "✅ Normal"
    return f"{kind}: {scenario['description']}"


def scenario_card() -> tuple[str, str, bool, bool]:
    scenarios = load_scenarios()
    names = sorted(scenarios, key=lambda n: (not n.startswith("attack"), n))
    with st.container(key="card_run"):
        st.markdown('<div id="run-scenario"></div>' + ui.panel_title(
            "play", "Run a Safety Scenario", "Run the same task on an unprotected agent and on an agent protected by AgentShield.",
            badge=True), unsafe_allow_html=True)
        name = st.selectbox("Scenario", names, index=names.index("attack_email_bn"), key="scenario",
                            format_func=lambda n: scenario_label(n, scenarios[n]))
        with st.container(key="mode"):
            mode = st.radio("Agent mode", list(MODES), key="agent_mode", horizontal=True,
                            format_func=lambda m: MODES[m][0], captions=[MODES[m][1] for m in MODES],
                            help="Offline needs no internet and is not a real-model result. "
                                 "Live calls Groq (free-tier limits apply). Recorded replays a saved real run.")
        approve = st.checkbox("I approve actions that ask for my approval (simulated human click)", key="approve",
                              disabled=mode == RECORDED,
                              help="AgentShield sends uncertain actions (ASK) to the user. Unticked = the user says no. "
                                   "Ticked = the user says yes. BLOCK decisions are never sent to the user.")
        clicked = st.button("Run Scenario", type="primary", icon=":material/play_arrow:", key="run", width="stretch")
    return name, mode, approve, clicked


def how_it_works_card() -> None:
    with st.container(key="card_how"):
        st.markdown(ui.panel_title("workflow", "How AgentShield Works") + ui.HOW_IT_WORKS
                    + '<div style="height:.9rem"></div>' + ui.panel_title("chart", "Decision Types") + ui.DECISIONS,
                    unsafe_allow_html=True)


def pipeline_card() -> None:
    with st.container(key="card_pipe"):
        st.markdown(ui.panel_title("layers", "Evaluation Pipeline",
                                   "Four checks run on every tool call; the stricter of score and policy wins.") + ui.PIPELINE,
                    unsafe_allow_html=True)


def recent_card() -> None:
    records = audit_log().recent(limit=5)
    link = '<a class="link" href="?page=Audit+Log" target="_self">View Audit Log →</a>'
    with st.container(key="card_recent"):
        if not records:
            body = '<div class="empty">No decisions yet. Run a scenario to see AgentShield\'s first verdict here.</div>'
        else:
            rows = "".join(
                f'<tr><td class="muted">{r.timestamp.strftime("%b %d, %H:%M")}</td>'
                f'<td class="c-req">{ui.esc(r.user_request[:48])}</td><td class="c-tool"><code>{ui.esc(r.tool_name)}</code></td>'
                f'<td>{ui.badge(r.decision.value)}</td><td class="muted">{ui.esc(short(r.reason_en, 90))}</td></tr>'
                for r in records)
            body = ('<div class="rwrap"><table class="rtable"><tr><th>Time (UTC)</th><th class="c-req">User request</th><th class="c-tool">Tool</th>'
                    f'<th>Decision</th><th>Reason</th></tr>{rows}</table></div>')
        st.markdown(ui.panel_title("file-text", "Recent Evaluations", right=link) + body, unsafe_allow_html=True)


def stopped_count(result: ScenarioResult) -> int:
    return sum(1 for _, v in result.history if v.decision.value != "allow")


def show_outcome(result: ScenarioResult) -> None:
    """The money outcome first: what a judge should see in two seconds."""
    lost = result.outcome.stolen
    a, b = st.columns(2)
    a.markdown(f'<div class="money-label">Stolen / চুরি হয়েছে</div>'
               f'<div class="money {"money-lost" if lost else "money-ok"}">{"−" + taka(lost) if lost else "৳ 0"}</div>',
               unsafe_allow_html=True)
    b.markdown(f'<div class="money-label">Balance / ব্যালান্স</div><div class="money">{taka(result.end_balance)}</div>',
               unsafe_allow_html=True)
    if lost:
        targets = ", ".join(t.to for t in result.outcome.unauthorized)
        st.error(f"MONEY STOLEN: {taka(lost)} sent to {targets}, which the user never asked for.")
    else:
        stopped = stopped_count(result)
        note = f" AgentShield stopped {stopped} action(s)." if stopped else ""
        st.success(f"Safe: no unauthorized transfers.{note}")


def check_line(verdict) -> str:
    return " · ".join(f"{c.check.value} {'skipped' if c.skipped else f'{c.risk_score:.2f}'}{' ⚑' if c.flagged else ''}"
                      for c in verdict.checks)


def show_steps(result: ScenarioResult) -> None:
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
                st.markdown(f'{ui.badge(verdict.decision.value)} &nbsp;risk {verdict.risk_score:.2f} · '
                            f'{verdict.total_latency_ms:.0f} ms', unsafe_allow_html=True)
                st.markdown(f'<div class="reason-bn"><b>কারণ:</b> {ui.esc(verdict.reason_bn)}</div>', unsafe_allow_html=True)
                st.caption(f"Reason: {verdict.reason_en}")
                st.caption(f"Checks: {check_line(verdict)}")
            if not step.result.startswith("[AgentShield]"):  # the block message repeats the reason
                st.text(step.result[:600] + ("…" if len(step.result) > 600 else ""))


def show_result(result: ScenarioResult) -> None:
    show_outcome(result)
    st.markdown(f'<div class="user-quote"><b>User:</b> {ui.esc(result.run.task)}</div>', unsafe_allow_html=True)
    show_steps(result)
    with st.expander("Agent's final answer"):
        st.write(result.run.final_answer)


def results(name: str, mode: str, approve: bool) -> None:
    without = run_safely(name, mode, shield=False)
    with_shield = run_safely(name, mode, shield=True, approve=approve)
    if without and with_shield:
        saved = without.outcome.stolen - with_shield.outcome.stolen
        if saved > 0:
            st.markdown(f'<div class="summary">🛡️ AgentShield saved {taka(saved)} · AgentShield {taka(saved)} বাঁচিয়েছে</div>',
                        unsafe_allow_html=True)
        elif not without.outcome.stolen:
            st.markdown('<div class="summary">✅ Normal task: AgentShield let it run · সাধারণ কাজ, AgentShield বাধা দেয়নি</div>',
                        unsafe_allow_html=True)
    if mode == "mock":
        st.caption("Offline mode: a simulated naive agent. Not a real-model result.")
    col_without, col_with = st.columns(2, gap="large")
    with col_without:
        st.markdown(f'<div class="col-head col-unsafe">{ui.icon("circle-x", 20)}Without AgentShield</div>', unsafe_allow_html=True)
        if without:
            show_result(without)
    with col_with:
        st.markdown(f'<div class="col-head col-safe">{ui.icon("shield-check", 20)}With AgentShield</div>', unsafe_allow_html=True)
        if with_shield:
            show_result(with_shield)


def playground_page() -> None:
    hero()
    kpis()
    left, right = st.columns([1.25, 1], gap="medium")
    with left:
        name, mode, approve, clicked = scenario_card()
    with right:
        how_it_works_card()
    if clicked:
        results(name, mode, approve)
    left, right = st.columns([1.25, 1], gap="medium")
    with left:
        pipeline_card()
    with right:
        recent_card()


# ---------------------------------------------------------------------------
# Other pages
# ---------------------------------------------------------------------------
def page_header(icon_name: str, title: str, sub: str) -> None:
    st.markdown(f'<div class="page-title">{ui.icon(icon_name, 26, "#B44CFF")} {ui.esc(title)}</div>'
                f'<div class="page-sub">{ui.esc(sub)}</div>', unsafe_allow_html=True)


def audit_page() -> None:
    page_header("file-text", "Audit Log", "Every AgentShield decision, newest first (SQLite, path from AUDIT_DB_PATH).")
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
        st.info("No decisions yet. Run a scenario in the Playground.")
        return
    st.dataframe(
        [{"time (UTC)": r.timestamp.strftime("%H:%M:%S"), "tool": r.tool_name, "decision": BADGES[r.decision.value],
          "risk": round(r.risk_score, 2), "arguments": json.dumps(r.arguments, ensure_ascii=False),
          "কারণ": r.reason_bn, "user request": r.user_request} for r in records],
        use_container_width=True, hide_index=True,
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
         for r in rows if r["language"] != "all" and r["detection_rate"] is not None])
    if not chart.empty:
        st.bar_chart(chart, x="language", y="attacks flagged (%)", color="detector", stack=False)
    st.dataframe([{k: v for k, v in r.items() if k not in ("detection_rate", "false_positive_rate")} for r in rows],
                 use_container_width=True, hide_index=True)


def agent_section(title: str, found) -> None:
    if found is None:
        return
    name, data = found
    st.subheader(title)
    st.caption(f"Source: {name}. Provider: {data['provider']} ({data['note']}). "
               f"Detector: {data.get('detector', 'heuristic')}. Runs per item: {data['runs']}.")
    st.dataframe(agent_rows(data), use_container_width=True, hide_index=True)
    outcomes = outcome_rows(data)
    if outcomes:
        st.caption("How each case ended with AgentShield (held for approval = one human click, not a block):")
        st.dataframe(outcomes, use_container_width=True, hide_index=True)


def benchmarks_page() -> None:
    page_header("chart", "Benchmarks", "Numbers come only from saved runs in benchmark/results/. "
                "Small samples: read the 95% intervals. Full write-up with caveats: docs/results.md.")
    agent_section("Agent level, real LLM (Groq): is the money safe?",
                  latest_where("agent", lambda d: d["provider"] == "groq" and heuristic_run(d)))
    agent_section("Agent level, simulated agent",
                  latest_where("agent", lambda d: d["provider"] == "mock" and heuristic_run(d)))
    detection_section("Text level: do existing guardrails catch Bangla/Banglish attacks?",
                      latest_where("detection", lambda d: not d.get("split") and any("promptguard" in k for k in d["metrics"])),
                      "Meta Prompt Guard 2 vs AgentShield's heuristic.")
    detection_section("Trained model (XLM-R), held-out test split",
                      latest_where("detection", lambda d: d.get("split") == "test"),
                      "Text level only: at agent level this model still holds real bills (docs/results.md 3e), "
                      "so the heuristic stays the runtime default.")


def policies_page() -> None:
    page_header("scale", "Policies", f"Deterministic rules from {Path(DEFAULT_POLICY_PATH).name}. "
                "If several match, the most severe decision wins (block > ask > allow).")
    for rule in policy_rules():
        conds = "".join(f'<span class="cond">{ui.esc(k)}: {ui.esc(json.dumps(v, ensure_ascii=False))}</span>'
                        for k, v in (rule.get("when") or {}).items())
        st.markdown(
            f'<div class="rule"><div class="rule-head"><span class="rule-id">{ui.esc(rule["id"])}</span>'
            f'{ui.badge(rule["decision"])}</div><p>{ui.esc(rule.get("description", ""))}</p>'
            f'<div>tools: <span class="cond">{ui.esc(", ".join(rule.get("tools", [])))}</span> {conds}</div>'
            f'<p><b>কারণ:</b> {ui.esc(rule.get("reason_bn", ""))}</p></div>', unsafe_allow_html=True)


def datasets_page() -> None:
    page_header("database", "Datasets", "Labeled texts used by the benchmark and for training. Fake data only "
                "(numbers start with 010, domains end in .example). Details: datasets/README.md.")
    summary = dataset_summary()
    st.dataframe([{"language": lang, "attack": c.get("attack", 0), "benign": c.get("benign", 0)}
                  for lang, c in sorted(summary.items())], use_container_width=True, hide_index=True)
    files = []
    for path in sorted((ROOT / "datasets").glob("*.jsonl")):
        lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        reviewed = sum("reviewed=yes" in (r.get("notes") or "") for r in lines)
        files.append({"file": path.name, "items": len(lines), "reviewed": f"{reviewed}/{len(lines)}",
                      "sources": ", ".join(sorted({r.get("source", "?") for r in lines}))})
    st.subheader("Files")
    st.dataframe(files, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
st.markdown(ui.CSS, unsafe_allow_html=True)
page = sidebar()
{
    "Playground": playground_page,
    "Benchmarks": benchmarks_page,
    "Audit Log": audit_page,
    "Policies": policies_page,
    "Datasets": datasets_page,
}[page]()
