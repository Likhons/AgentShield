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

import csv
import importlib
import io
import json
import math
import re
import sys
import tomllib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

import altair as alt
import pandas as pd
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # make project imports work

def _reload_if_modified(mod) -> None:
    path = getattr(mod, "__file__", None)
    if not path:
        return
    try:
        mtime = Path(path).stat().st_mtime_ns
    except OSError:
        return
    if getattr(mod, "_last_mtime_ns", None) != mtime:
        sys.modules[mod.__name__] = mod
        importlib.reload(mod)
        mod._last_mtime_ns = mtime


import agentshield.audit.log as _audit_log_mod  # noqa: E402
_reload_if_modified(_audit_log_mod)
from agentshield.audit.log import AuditLog  # noqa: E402
from agentshield.checks.policy import DEFAULT_POLICY_PATH, PolicyRule  # noqa: E402
from agentshield.config import get_settings  # noqa: E402
from agentshield.core.models import AuditRecord, CheckName, DecisionThresholds  # noqa: E402
from agentshield.llm import LLMError  # noqa: E402
from benchmark.dataset import load_dataset, summarize  # noqa: E402
from benchmark.report import agent_rows, detection_rows, latest_where, outcome_rows  # noqa: E402
from dashboard import ui  # noqa: E402
_reload_if_modified(ui)
from demo_agent.recording import load_result  # noqa: E402
from demo_agent.run import ScenarioResult, run_scenario  # noqa: E402
from demo_agent.scenarios import load_scenarios  # noqa: E402

st.set_page_config(page_title="AgentShield", page_icon="🛡️", layout="wide", initial_sidebar_state="auto")

BADGES = {"allow": "✅ ALLOW", "ask_human": "✋ ASK HUMAN", "block": "🛑 BLOCK"}
RECORDED = "recorded (groq)"
MODES = {
    "mock": (":material/smart_toy: Offline (simulated)", "Simulated naive agent. Works offline."),
    "groq": (":material/wifi: Live (Groq)", "Real model via Groq, same tools."),
    RECORDED: (":material/play_circle: Recorded Run", "Instant replay of a saved real run."),
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
def _cached_audit_log(db_path: str) -> AuditLog:
    """One shared audit log for the whole dashboard (file path from .env)."""
    return AuditLog(db_path)


def audit_log() -> AuditLog:
    db_path = str(get_settings().audit_db_path)
    inst = _cached_audit_log(db_path)
    if not hasattr(inst, "query"):
        _cached_audit_log.clear()
        inst = _cached_audit_log(db_path)
    return inst


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
        st.markdown(f'<div class="brand"><span class="brand-badge">{ui.icon("shield-check", 22, "#D8B4FE")}</span>'
                    '<div><div class="brand-name">AgentShield</div><div class="brand-sub">AI Agent Safety Platform</div></div></div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="side-label">Workspace</div>', unsafe_allow_html=True)
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
        st.markdown(f'<div class="status"><div class="status-head"><span class="dot"></span>Gateway Ready</div>{body}'
                    f'<div class="version">v{ui.esc(app_version())}</div></div>', unsafe_allow_html=True)
    return page


# ---------------------------------------------------------------------------
# Playground
# ---------------------------------------------------------------------------
def hero() -> None:
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.markdown(
            f'<div class="hero"><div class="hero-pill">{ui.icon("play-fill", 10, "#C084FC")}<span>Playground</span></div>'
            '<div class="hero-title" role="heading" aria-level="1">'
            '<span class="l1">Stop AI Agents from Acting&nbsp;on</span> <span class="grad l2">Hidden Instructions</span></div>'
            '<p class="lead">AgentShield checks every tool call before it runs, so an AI agent cannot be tricked into '
            'sending money by text hidden in emails, web pages or files, in Bangla, Banglish and English.</p>'
            '<div class="cta-row">'
            f'<a class="cta cta-primary" href="#run-scenario">{ui.icon("play-fill", 14, "#fff")}Try a Scenario</a>'
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
        last = ui.kpi("chart", "#16C784", with_shield, "Attacks that Moved Money",
                      note=f"Real LLM · {without} without AgentShield")
    else:
        last = ui.kpi("chart", "#16C784", "–", "Attacks that Moved Money", note="No real-LLM run yet")
    cards = [
        ui.kpi("shield-check", "#B44CFF", str(len(CheckName)), "Checks per Tool Call",
               note=" · ".join(c.value.capitalize() for c in CheckName)),
        ui.kpi("list-checks", "#5B8CFF", str(len(policy_rules())), "Policy Rules", note="Deterministic · default.yaml"),
        ui.kpi("bug", "#F04452", str(sum(attacks.values())), "Attack Samples",
               note=" · ".join(f"{k.upper() if len(k) <= 2 else k.capitalize()} {v}" for k, v in sorted(attacks.items()))),
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
    ready = '<span class="ready-pill"><span class="ready-dot"></span>Ready</span>'
    with st.container(key="card_run"):
        st.markdown('<div id="run-scenario"></div>' + ui.panel_title(
            "play-fill", "Run a Safety Scenario",
            "Test the same task on an unprotected agent and on an agent protected by AgentShield.",
            badge=True, right=ready), unsafe_allow_html=True)
        name = st.selectbox("Scenario", names, index=names.index("attack_email_bn"), key="scenario",
                            format_func=lambda n: scenario_label(n, scenarios[n]))
        with st.container(key="mode"):
            mode = st.radio("Agent Mode", list(MODES), key="agent_mode", horizontal=True,
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
    controls = (f'<span class="search-pill">{ui.icon("search", 14, "#8690B5")}<span>Search requests, tools...</span></span>'
                '<a class="audit-btn" href="?page=Audit+Log" target="_self">View Audit Log →</a>')
    with st.container(key="card_recent"):
        if not records:
            body = '<div class="empty">No decisions yet. Run a scenario to see AgentShield\'s first verdict here.</div>'
        else:
            rows = "".join(
                f'<tr><td class="muted">{r.timestamp.strftime("%b %d, %H:%M")}</td>'
                f'<td class="c-req">{ui.esc(r.user_request[:48])}</td>'
                f'<td class="c-tool"><code class="tool-pill tool-{r.decision.value}">{ui.esc(r.tool_name)}</code></td>'
                f'<td>{ui.badge(r.decision.value)}</td><td class="muted">{ui.esc(short(r.reason_en, 90))}</td>'
                f'<td><a class="row-link" href="?page=Audit+Log" target="_self" title="Open in Audit Log">{ui.icon("external-link", 13)}</a></td></tr>'
                for r in records)
            body = ('<div class="rwrap"><table class="rtable"><tr><th>Time (UTC)</th><th class="c-req">User Request</th><th class="c-tool">Tool</th>'
                    f'<th>Decision</th><th>Reason</th><th>•••</th></tr>{rows}</table></div>')
        st.markdown(ui.panel_title("file-text", "Recent Evaluations", right=controls) + body, unsafe_allow_html=True)


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
            # plain styled block: st.code lazy-loads a highlighter that showed only a skeleton online
            st.markdown(f'<div class="args">{ui.esc(json.dumps(step.args, ensure_ascii=False))}</div>',
                        unsafe_allow_html=True)
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
        banner = ui.summary_banner(name, without.outcome.stolen, with_shield.outcome.stolen)
        if banner:
            css, text = banner
            st.markdown(f'<div class="summary {css}">{text}</div>', unsafe_allow_html=True)
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
    pipeline_card()
    recent_card()


# ---------------------------------------------------------------------------
# Other pages
# ---------------------------------------------------------------------------
def page_header(icon_name: str, title: str, sub: str) -> None:
    st.markdown(f'<div class="page-title">{ui.icon(icon_name, 26, "#B44CFF")} {ui.esc(title)}</div>'
                f'<div class="page-sub">{ui.esc(sub)}</div>', unsafe_allow_html=True)


AUDIT_DATE_RANGES = {
    "All time": None,
    "Last 24 hours": timedelta(hours=24),
    "Last 7 days": timedelta(days=7),
    "Last 30 days": timedelta(days=30),
}


def build_audit_csv(records: list[AuditRecord]) -> bytes:
    """Export AuditRecords as UTF-8 CSV (with BOM so Excel preserves Bangla Unicode)."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id", "timestamp_utc", "session_id", "request_id", "tool", "decision",
        "risk_score", "tainted", "latency_ms", "arguments", "user_request",
        "reason_bn", "reason_en",
    ])
    for r in records:
        writer.writerow([
            r.id,
            r.timestamp.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            r.session_id,
            r.request_id,
            r.tool_name,
            r.decision.value,
            round(r.risk_score, 4),
            r.tainted,
            round(r.total_latency_ms, 2),
            json.dumps(r.arguments, ensure_ascii=False),
            r.user_request,
            r.reason_bn,
            r.reason_en,
        ])
    return buf.getvalue().encode("utf-8-sig")


def _audit_since_iso(date_range_label: str, newest_ts: datetime | None = None) -> str | None:
    delta = AUDIT_DATE_RANGES.get(date_range_label)
    if delta is None:
        return None
    anchor = newest_ts.astimezone(timezone.utc) if newest_ts is not None else datetime.now(timezone.utc)
    return (anchor - delta).isoformat(timespec="microseconds")


def _clear_audit_filters() -> None:
    st.session_state["audit_decision_filter"] = "all"
    st.session_state["audit_search"] = ""
    st.session_state["audit_date_range"] = "All time"
    st.session_state["audit_tool_filter"] = "All tools"
    st.session_state["audit_taint_filter"] = "All"
    st.session_state["audit_min_risk"] = 0.0
    st.session_state["audit_page_num"] = 1


def _audit_url(**extra: str | int) -> str:
    params: dict[str, str | int] = {"page": "Audit Log"}
    params.update(extra)
    return "?" + urlencode(params)


def _render_audit_kpis(stats: dict) -> None:
    total = stats["total"]
    allow_pct = f"{(stats['allow'] / total * 100):.0f}% of total" if total else "0% of total"
    ask_pct = f"{(stats['ask_human'] / total * 100):.1f}% of total" if total else "0% of total"
    block_pct = f"{(stats['block'] / total * 100):.0f}% of total" if total else "0% of total"
    median = stats["median_latency_ms"]
    median_str = f"{median:.1f} ms" if median is not None else "–"
    cards = [
        ui.audit_kpi_card("layers", "#9147FF", "Checked Calls", str(total), "100% SQLite logged"),
        ui.audit_kpi_card("circle-check", "#00D6A0", "Allowed", str(stats["allow"]), allow_pct),
        ui.audit_kpi_card("circle-help", "#FFB547", "Asked Human", str(stats["ask_human"]), ask_pct),
        ui.audit_kpi_card("circle-x", "#FF526F", "Blocked", str(stats["block"]), block_pct),
        ui.audit_kpi_card("zap", "#C044FF", "Median Latency", median_str, f"LLM judge: {stats['llm_calls']}/{total}"),
    ]
    st.markdown(
        f'<div class="audit-kpis">{"".join(cards)}</div>'
        f'<div class="audit-llm-line">{ui.icon("activity", 14, "#9147FF")}'
        f'<span>LLM judge called for <b>{stats["llm_calls"]}</b> of <b>{total}</b> checks.</span></div>',
        unsafe_allow_html=True,
    )


def _render_audit_table(
    page_records: list[AuditRecord],
    selected_id: str | None,
    current_page: int,
    page_size: int,
    filtered_total: int,
    thresholds: DecisionThresholds,
) -> None:
    total_pages = max(1, math.ceil(filtered_total / page_size))
    start_idx = (current_page - 1) * page_size + 1 if filtered_total > 0 else 0
    end_idx = min(current_page * page_size, filtered_total)

    radios_html = ['<input type="checkbox" id="adrawer-close-chk" class="asel-radio">']
    css_rules = []
    rows_html = []
    chk_svg = ui.icon("check", 12, "currentColor", stroke=3)

    for r in page_records:
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "", r.id)
        is_sel = r.id == selected_id
        checked_attr = " checked" if is_sel else ""
        radios_html.append(
            f'<input type="radio" name="audit_sel_p{current_page}" id="asel-{safe_id}" '
            f'class="asel-radio"{checked_attr}>'
        )
        css_rules.append(
            f'[data-testid="stHorizontalBlock"]:has(#asel-{safe_id}:checked) tr.arow-{safe_id} td,'
            f'.audit-table-card:has(#asel-{safe_id}:checked) tr.arow-{safe_id} td {{'
            f'background:linear-gradient(90deg,rgba(145,71,255,.20),rgba(192,68,255,.10));'
            f'border-top-color:#9147FF;border-bottom-color:#9147FF;}}'
            f'[data-testid="stHorizontalBlock"]:has(#asel-{safe_id}:checked) tr.arow-{safe_id} td:first-child,'
            f'.audit-table-card:has(#asel-{safe_id}:checked) tr.arow-{safe_id} td:first-child {{'
            f'border-left-color:#9147FF;box-shadow:-4px 0 14px -4px rgba(145,71,255,.55);}}'
            f'[data-testid="stHorizontalBlock"]:has(#asel-{safe_id}:checked) tr.arow-{safe_id} td:last-child,'
            f'.audit-table-card:has(#asel-{safe_id}:checked) tr.arow-{safe_id} td:last-child {{'
            f'border-right-color:#9147FF;box-shadow:4px 0 14px -4px rgba(145,71,255,.55);}}'
            f'[data-testid="stHorizontalBlock"]:has(#asel-{safe_id}:checked) tr.arow-{safe_id} .achk,'
            f'.audit-table-card:has(#asel-{safe_id}:checked) tr.arow-{safe_id} .achk {{'
            f'background:linear-gradient(135deg,#9147FF,#C044FF);border-color:#E2B8FF;color:#FFFFFF;'
            f'box-shadow:0 0 10px rgba(145,71,255,.55);}}'
            f'[data-testid="stHorizontalBlock"]:has(#asel-{safe_id}:checked) .adrawer-pane-{safe_id} {{'
            f'display:block;}}'
        )

        tool_ic = ui.icon(ui.audit_tool_icon(r.tool_name), 13, "#C9A6FF")
        risk_str, risk_cls, _ = ui.audit_risk_level(r.risk_score, thresholds.ask_human_at, thresholds.block_at)
        args_json = json.dumps(r.arguments, ensure_ascii=False)
        args_preview = short(args_json, 56)
        lbl = f'for="asel-{safe_id}"'
        rows_html.append(
            f'<tr class="arow arow-{safe_id}">'
            f'<td><label class="arow-link" {lbl} title="Select event {ui.esc(r.id)}">'
            f'<span class="achk">{chk_svg}</span></label></td>'
            f'<td class="atime"><label class="arow-link" {lbl} '
            f'title="{ui.esc(r.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"))}">{r.timestamp.strftime("%H:%M:%S")}</label></td>'
            f'<td><label class="arow-link" {lbl}>'
            f'<span class="atool-ic">{tool_ic}</span><span class="atool-name">{ui.esc(r.tool_name)}</span></label></td>'
            f'<td><label class="arow-link" {lbl}>{ui.audit_badge(r.decision.value)}</label></td>'
            f'<td><label class="arow-link" {lbl}>'
            f'<span class="arisk arisk-{risk_cls}">{ui.esc(risk_str)}</span></label></td>'
            f'<td><label class="arow-link" {lbl}>'
            f'<span class="aargs" title="{ui.esc(args_json)}">{ui.esc(args_preview)}</span></label></td>'
            f'<td><label class="amore" {lbl} title="Inspect details">'
            f'{ui.icon("more-horizontal", 16)}</label></td>'
            f'</tr>'
        )

    page_links = []
    for item in ui.audit_page_items(current_page, total_pages):
        if item == "…":
            page_links.append('<span class="apage-dots">…</span>')
        else:
            active_cls = " apage-active" if item == current_page else ""
            page_links.append(f'<span class="apage-btn{active_cls}">{item}</span>')

    table_html = (
        f'<style>{"".join(css_rules)}</style>'
        f'<div class="audit-table-card">{"".join(radios_html)}'
        f'<div class="audit-table-wrap"><table class="atable">'
        '<thead><tr><th class="col-chk"></th><th>Time (UTC)</th><th>Tool</th><th>Decision</th>'
        '<th>Risk</th><th>Arguments (Preview)</th><th class="col-more">Details</th></tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody></table></div>'
        f'<div class="audit-foot"><span>Showing {start_idx}–{end_idx} of {filtered_total}</span>'
        f'<div class="apager">{"".join(page_links)}</div></div></div>'
    )
    st.markdown(table_html, unsafe_allow_html=True)


def _build_drawer_pane_html(record: AuditRecord, thresholds: DecisionThresholds) -> str:
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "", record.id)
    dec_val = record.decision.value
    dec_meta = {
        "block": ("shield-x", "#FF526F", "BLOCK", "Blocked policy or untrusted injection attempt"),
        "ask_human": ("circle-help", "#FFB547", "ASK HUMAN", "Held for explicit human approval"),
        "allow": ("circle-check", "#00D6A0", "ALLOW", "Verified safe to execute"),
    }[dec_val]
    b_icon, b_color, b_title, b_sub = dec_meta
    _, risk_cls, risk_label = ui.audit_risk_level(
        record.risk_score, thresholds.ask_human_at, thresholds.block_at
    )
    pretty_args = json.dumps(record.arguments, ensure_ascii=False, indent=2)

    chk_chips = []
    for c in record.checks:
        flag_cls = " adrawer-chk-flagged" if c.flagged else ""
        status = "skipped" if c.skipped else f"{c.risk_score:.2f}"
        flag_mark = " ⚑" if c.flagged else ""
        chk_chips.append(
            f'<span class="adrawer-chk-chip{flag_cls}">{ui.esc(c.check.value)}: {status}{flag_mark}</span>'
        )
    checks_html = f'<div class="adrawer-checks">{"".join(chk_chips)}</div>' if chk_chips else ""

    return (
        f'<div class="adrawer-pane adrawer-pane-{safe_id}">'
        f'<div class="adrawer-head">'
        f'<div class="adrawer-title">{ui.icon("file-text", 18, "#9147FF")}<span>Audit Details</span></div>'
        f'<label class="adrawer-close" for="adrawer-close-chk" title="Close drawer">{ui.icon("x", 16)}</label>'
        f'</div>'
        f'<div class="adrawer-banner adrawer-banner-{dec_val}">'
        f'<div class="adrawer-banner-ic">{ui.icon(b_icon, 19, b_color)}</div>'
        f'<div class="adrawer-banner-body"><b>{ui.esc(b_title)}</b><span class="adrawer-banner-sub">{ui.esc(b_sub)}</span></div>'
        f'</div>'
        f'<div class="adrawer-kv"><span class="adrawer-k">{ui.icon("clock", 14, "#A8B3D3")}Time (UTC)</span>'
        f'<span class="adrawer-v">{ui.esc(record.timestamp.strftime("%b %d, %H:%M:%S"))}</span></div>'
        f'<div class="adrawer-kv"><span class="adrawer-k">{ui.icon("terminal", 14, "#A8B3D3")}Tool</span>'
        f'<span class="adrawer-v"><code>{ui.esc(record.tool_name)}</code></span></div>'
        f'<div class="adrawer-kv"><span class="adrawer-k">{ui.icon("alert", 14, "#A8B3D3")}Risk Score</span>'
        f'<span class="adrawer-v"><span class="arisk-pill arisk-pill-{risk_cls}">'
        f'{ui.esc(f"{record.risk_score:.2f}")} · {ui.esc(risk_label)}</span></span></div>'
        f'<div class="adrawer-kv"><span class="adrawer-k">{ui.icon("shield", 14, "#A8B3D3")}Event ID</span>'
        f'<span class="adrawer-v"><code>{ui.esc(record.id)}</code></span></div>'
        f'<div class="adrawer-kv"><span class="adrawer-k">{ui.icon("layers", 14, "#A8B3D3")}Taint / Latency</span>'
        f'<span class="adrawer-v">{"Tainted" if record.tainted else "Untainted"} · '
        f'{record.total_latency_ms:.2f} ms</span></div>'
        f'<div class="adrawer-kv"><span class="adrawer-k">{ui.icon("mail", 14, "#A8B3D3")}User Request</span>'
        f'<span class="adrawer-v">{ui.esc(record.user_request)}</span></div>'
        f'<div class="adrawer-sec">'
        f'<div class="adrawer-sec-title">{ui.icon("terminal", 14, "#9147FF")}<span>Arguments</span></div>'
        f'<pre class="adrawer-json">{ui.esc(pretty_args)}</pre>'
        f'</div>'
        f'<div class="adrawer-sec">'
        f'<div class="adrawer-sec-title">{ui.icon("file-text", 14, "#9147FF")}<span>Reason</span></div>'
        f'<div class="adrawer-reason">{ui.esc(record.reason_bn)}'
        f'<div class="adrawer-reason-en">{ui.esc(record.reason_en)}</div>'
        f'{checks_html}</div>'
        f'</div></div>'
    )


def _render_audit_drawer(
    page_records: list[AuditRecord],
    selected_record: AuditRecord,
    thresholds: DecisionThresholds,
) -> None:
    panes_html = "".join(_build_drawer_pane_html(r, thresholds) for r in page_records)
    pretty_args = json.dumps(selected_record.arguments, ensure_ascii=False, indent=2)

    def _on_copy_args() -> None:
        st.session_state["audit_copied_mode"] = "args"

    def _on_copy_id() -> None:
        st.session_state["audit_copied_mode"] = "id"

    def _on_close_drawer() -> None:
        st.session_state["audit_drawer_open"] = False

    with st.container(key="audit_drawer_card"):
        st.markdown(panes_html, unsafe_allow_html=True)
        b1, b2, b3 = st.columns([1.15, 1, 0.85], gap="small", vertical_alignment="center")
        b1.button("Copy Arguments", icon=":material/content_copy:", key="audit_copy_args", on_click=_on_copy_args, width="stretch")
        b2.button("Copy ID", icon=":material/tag:", key="audit_copy_id", on_click=_on_copy_id, width="stretch")
        b3.button("Close", icon=":material/close:", key="audit_close_drawer", on_click=_on_close_drawer, width="stretch")

        copied_mode = st.session_state.get("audit_copied_mode")
        if copied_mode == "args":
            st.caption("Copy structured JSON arguments:")
            st.code(pretty_args, language="json")
        elif copied_mode == "id":
            st.caption("Copy Event ID:")
            st.code(selected_record.id, language=None)


@st.fragment
def _audit_interactive_console(
    log: AuditLog,
    newest_ts: datetime | None,
    thresholds: DecisionThresholds,
) -> None:
    """Fragment-isolated interactive Audit Table, Filter Toolbar, Pagination, and Details Drawer."""
    since_iso = _audit_since_iso(st.session_state["audit_date_range"], newest_ts)
    cur_tool = None if st.session_state["audit_tool_filter"] == "All tools" else st.session_state["audit_tool_filter"]
    cur_taint = (
        True if st.session_state["audit_taint_filter"] == "Tainted only"
        else (False if st.session_state["audit_taint_filter"] == "Untainted only" else None)
    )
    cur_min_risk = float(st.session_state["audit_min_risk"])
    _, _, chip_counts = log.query(
        decision=None,
        search=st.session_state["audit_search"],
        tool_name=cur_tool,
        tainted=cur_taint,
        min_risk=cur_min_risk,
        since_iso=since_iso,
        limit=1,
    )

    adv_active = sum([
        st.session_state["audit_tool_filter"] != "All tools",
        st.session_state["audit_taint_filter"] != "All",
        float(st.session_state["audit_min_risk"]) > 0,
        st.session_state["audit_date_range"] != "All time",
    ])
    any_filter_active = (
        adv_active > 0
        or st.session_state["audit_decision_filter"] != "all"
        or bool(st.session_state["audit_search"].strip())
    )

    chip_labels = {
        "all": f"All ({chip_counts['total']})",
        "allow": f"Allow ({chip_counts['allow']})",
        "ask_human": f"Ask ({chip_counts['ask_human']})",
        "block": f"Block ({chip_counts['block']})",
    }
    with st.container(key="audit_toolbar"):
        tb_chips, tb_search, tb_flt = st.columns([1.85, 1.15, 0.72], gap="small", vertical_alignment="center")
        with tb_chips:
            with st.container(key="audit_decision_wrap"):
                decision_choice = st.radio(
                    "Decision filter",
                    list(chip_labels),
                    format_func=chip_labels.get,
                    horizontal=True,
                    label_visibility="collapsed",
                    key="audit_decision_filter",
                )
        with tb_search:
            search_query = st.text_input(
                "Search audit log",
                placeholder="Search tool, arguments, or decision...",
                label_visibility="collapsed",
                key="audit_search",
            )
        with tb_flt:
            fcol1, fcol2 = st.columns([1.2, 1] if any_filter_active else [1, 0.01], gap="small", vertical_alignment="center")
            with fcol1:
                pop_label = f"Filters ({adv_active})" if adv_active else "Filters"
                with st.popover(pop_label, icon=":material/filter_alt:", width="stretch"):
                    st.selectbox("Tool", ["All tools"] + log.distinct_tools(), key="audit_tool_filter")
                    st.selectbox("Taint status", ["All", "Tainted only", "Untainted only"], key="audit_taint_filter")
                    st.slider("Minimum risk score", 0.0, 1.0, step=0.05, key="audit_min_risk")
                    st.selectbox("Rows per page", [8, 15, 25, 50], key="audit_page_size")
                    st.button(
                        "Clear all filters",
                        key="audit_clear_filters_popover",
                        on_click=_clear_audit_filters,
                        width="stretch",
                    )
            if any_filter_active:
                with fcol2:
                    st.button(
                        "Reset",
                        key="audit_clear_filters",
                        on_click=_clear_audit_filters,
                        width="stretch",
                        help="Clear all active filters",
                    )

    # Reset to page 1 when filter signature changes
    filter_sig = (
        decision_choice,
        search_query.strip(),
        st.session_state["audit_date_range"],
        st.session_state["audit_tool_filter"],
        st.session_state["audit_taint_filter"],
        float(st.session_state["audit_min_risk"]),
        int(st.session_state["audit_page_size"]),
    )
    if st.session_state.get("_audit_filter_sig") != filter_sig:
        if st.session_state.get("_audit_filter_sig") is not None:
            st.session_state["audit_page_num"] = 1
        st.session_state["_audit_filter_sig"] = filter_sig

    page_size = int(st.session_state["audit_page_size"])
    cur_tool = None if st.session_state["audit_tool_filter"] == "All tools" else st.session_state["audit_tool_filter"]
    cur_taint = (
        True if st.session_state["audit_taint_filter"] == "Tainted only"
        else (False if st.session_state["audit_taint_filter"] == "Untainted only" else None)
    )
    cur_min_risk = float(st.session_state["audit_min_risk"])

    _, filtered_total, _ = log.query(
        decision=None if decision_choice == "all" else decision_choice,
        search=search_query,
        tool_name=cur_tool,
        tainted=cur_taint,
        min_risk=cur_min_risk,
        since_iso=since_iso,
        limit=1,
        offset=0,
    )
    total_pages = max(1, math.ceil(filtered_total / page_size))
    current_page = min(max(1, int(st.session_state["audit_page_num"])), total_pages)
    st.session_state["audit_page_num"] = current_page

    page_records, filtered_total, _ = log.query(
        decision=None if decision_choice == "all" else decision_choice,
        search=search_query,
        tool_name=cur_tool,
        tainted=cur_taint,
        min_risk=cur_min_risk,
        since_iso=since_iso,
        limit=page_size,
        offset=(current_page - 1) * page_size,
    )

    if not page_records:
        st.info("No audit records match your current filters.")
        st.button("Clear all filters", key="audit_clear_empty", on_click=_clear_audit_filters)
        return

    # Preserve selection when available on current page; otherwise select default record on page
    selected_id = st.session_state.get("audit_selected_id")
    page_ids = [r.id for r in page_records]
    if selected_id in page_ids:
        selected_record = next(r for r in page_records if r.id == selected_id)
    else:
        default_rec = next((r for r in page_records if r.decision.value == "block"), page_records[0])
        selected_record = default_rec
        selected_id = default_rec.id
        st.session_state["audit_selected_id"] = selected_id

    drawer_open = bool(st.session_state.get("audit_drawer_open", True))

    if drawer_open and selected_record is not None:
        col_table, col_drawer = st.columns([1.85, 1], gap="medium")
    else:
        col_table = st.container()
        col_drawer = None

    def _go_prev_page() -> None:
        st.session_state["audit_page_num"] = max(1, current_page - 1)

    def _go_next_page() -> None:
        st.session_state["audit_page_num"] = min(total_pages, current_page + 1)

    def _on_select_record() -> None:
        chosen = st.session_state.get("audit_select_record")
        if chosen:
            st.session_state["audit_selected_id"] = chosen
            st.session_state["audit_drawer_open"] = True

    def _on_open_drawer() -> None:
        st.session_state["audit_drawer_open"] = True

    with col_table:
        _render_audit_table(
            page_records,
            selected_id if drawer_open else None,
            current_page,
            page_size,
            filtered_total,
            thresholds,
        )
        with st.container(key="audit_pager_bar"):
            nav_c1, nav_c2, nav_c3, nav_c4 = st.columns([0.7, 0.7, 1.8, 0.9], gap="small", vertical_alignment="center")
            nav_c1.button(
                "‹ Previous",
                key="audit_prev_page",
                disabled=current_page <= 1,
                on_click=_go_prev_page,
                width="stretch",
            )
            nav_c2.button(
                "Next ›",
                key="audit_next_page",
                disabled=current_page >= total_pages,
                on_click=_go_next_page,
                width="stretch",
            )
            rec_labels = {
                r.id: f"{r.timestamp.strftime('%H:%M:%S')} · {r.tool_name} · {r.decision.value.upper()} ({r.id[:6]})"
                for r in page_records
            }
            nav_c3.selectbox(
                "Inspect record",
                page_ids,
                index=page_ids.index(selected_id) if selected_id in page_ids else 0,
                format_func=rec_labels.get,
                key="audit_select_record",
                on_change=_on_select_record,
                label_visibility="collapsed",
            )
            if not drawer_open:
                nav_c4.button(
                    "Open Details",
                    icon=":material/side_navigation:",
                    key="audit_open_drawer",
                    on_click=_on_open_drawer,
                    width="stretch",
                )
            else:
                nav_c4.caption(f"Page {current_page} of {total_pages}")

    if col_drawer is not None and selected_record is not None:
        with col_drawer:
            _render_audit_drawer(page_records, selected_record, thresholds)


def audit_page() -> None:
    log = audit_log()
    stats = log.stats()
    thresholds = DecisionThresholds()
    newest = log.recent(limit=1)
    newest_ts = newest[0].timestamp if newest else None

    st.session_state.setdefault("audit_decision_filter", "all")
    st.session_state.setdefault("audit_search", "")
    st.session_state.setdefault("audit_date_range", "All time")
    st.session_state.setdefault("audit_tool_filter", "All tools")
    st.session_state.setdefault("audit_taint_filter", "All")
    st.session_state.setdefault("audit_min_risk", 0.0)
    st.session_state.setdefault("audit_page_size", 8)
    st.session_state.setdefault("audit_page_num", 1)
    st.session_state.setdefault("audit_drawer_open", True)

    cur_dec = st.session_state["audit_decision_filter"]
    cur_search = st.session_state["audit_search"]
    cur_date = st.session_state["audit_date_range"]
    cur_tool = None if st.session_state["audit_tool_filter"] == "All tools" else st.session_state["audit_tool_filter"]
    cur_taint = (
        True if st.session_state["audit_taint_filter"] == "Tainted only"
        else (False if st.session_state["audit_taint_filter"] == "Untainted only" else None)
    )
    cur_min_risk = float(st.session_state["audit_min_risk"])
    since_iso = _audit_since_iso(cur_date, newest_ts)

    export_records, _, _ = log.query(
        decision=None if cur_dec == "all" else cur_dec,
        search=cur_search,
        tool_name=cur_tool,
        tainted=cur_taint,
        min_risk=cur_min_risk,
        since_iso=since_iso,
        limit=None,
    )

    # Region A: Static Header & KPI Cards
    head_left, head_right = st.columns([2.85, 1.05], gap="small", vertical_alignment="center")
    with head_left:
        st.markdown(
            f'<div class="audit-header" style="margin-bottom:0">'
            f'<span class="audit-header-icon">{ui.icon("file-text", 24, "#D8B4FE")}</span>'
            f'<div class="audit-header-text">'
            f'<div class="audit-h1" role="heading" aria-level="1">Audit Log</div>'
            f'<div class="audit-sub">Every AgentShield decision, newest first (SQLite, path from AUDIT_DB_PATH).</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
    with head_right:
        hr1, hr2 = st.columns([1, 1.15], gap="small", vertical_alignment="center")
        hr1.download_button(
            "Export (CSV)",
            data=build_audit_csv(export_records),
            file_name="agentshield_audit_log.csv",
            mime="text/csv",
            icon=":material/upload:",
            key="audit_export_csv",
            width="stretch",
        )
        hr2.selectbox(
            "Date range",
            list(AUDIT_DATE_RANGES),
            key="audit_date_range",
            label_visibility="collapsed",
        )

    _render_audit_kpis(stats)

    if stats["total"] == 0:
        st.info("No decisions yet. Run a scenario in the Playground.")
        return

    # Region B & C: Fragment-scoped Interactive Table + Right-Side Details Drawer
    _audit_interactive_console(log, newest_ts, thresholds)


_DETECTOR_META = {
    "agentshield-heuristic": ("AgentShield Heuristic", "#A855F7", 0),
    "promptguard-22m": ("PromptGuard-22m", "#38BDF8", 1),
    "promptguard-86m": ("PromptGuard-86m", "#FB7185", 2),
    "agentshield-model": ("AgentShield XLM-R", "#10B981", 3),
}
_LANG_LABELS = {"banglish": "Banglish", "bn": "BN", "en": "EN"}


def _build_detection_chart(rows: list[dict]) -> tuple[alt.LayerChart, list[tuple[str, str]]] | None:
    records = []
    for r in rows:
        if r["language"] == "all" or r["detection_rate"] is None:
            continue
        raw_det = str(r["detector"])
        det_label, det_color, det_ord = _DETECTOR_META.get(raw_det, (raw_det, "#C084FC", 9))
        raw_lang = str(r["language"])
        lang_label = _LANG_LABELS.get(raw_lang, raw_lang.upper())
        pct = round(100.0 * float(r["detection_rate"] or 0.0), 1)
        pct_label = f"{int(pct)}%" if pct.is_integer() else f"{pct:.1f}%"

        cell_str = str(r.get("attacks flagged", ""))
        m = re.search(r"\((\d+/\d+)(?:,\s*95%\s*CI\s*([^)]+))?\)", cell_str)
        samples_str = m.group(1) if m else "–"
        ci_str = m.group(2) if (m and m.group(2)) else "–"

        records.append({
            "detector_raw": raw_det,
            "Detector": det_label,
            "det_color": det_color,
            "det_ord": det_ord,
            "Language": lang_label,
            "pct": pct,
            "pct_label": pct_label,
            "Flagged / Total": samples_str,
            "95% CI": ci_str,
            "Benign Flagged (FP)": str(r.get("benign flagged", "–")),
        })

    if not records:
        return None

    max_pct = max(item["pct"] for item in records)
    if max_pct <= 45.0:
        domain_max = float(max(40, int(math.ceil((max_pct + 6.0) / 10.0) * 10)))
        tick_step = 10
    else:
        domain_max = 112.0
        tick_step = 20
    tick_vals = [float(v) for v in range(0, int(min(100.0, domain_max)) + 1, tick_step)]

    # Give 0% bars a tiny visual stub so zero-value detector categories stay clearly visible
    zero_stub = round(domain_max * 0.0085, 3)
    for item in records:
        item["bar_pct"] = item["pct"] if item["pct"] > 0 else zero_stub

    df = pd.DataFrame(records)
    det_pairs = sorted({(r["Detector"], r["det_color"], r["det_ord"]) for r in records}, key=lambda x: x[2])
    ordered_dets = [d for d, _, _ in det_pairs]
    ordered_colors = [c for _, c, _ in det_pairs]
    legend_items = [(d, c) for d, c, _ in det_pairs]
    lang_order = [lg for lg in ("Banglish", "BN", "EN") if lg in set(df["Language"])] + [
        lg for lg in sorted(set(df["Language"])) if lg not in {"Banglish", "BN", "EN"}
    ]

    base = alt.Chart(df).encode(
        y=alt.Y(
            "Language:N",
            sort=lang_order,
            title=None,
            scale=alt.Scale(paddingInner=0.26, paddingOuter=0.14),
            axis=alt.Axis(
                labelAngle=0,
                labelColor="#F5F6FF",
                labelFontSize=12.5,
                labelFontWeight="bold",
                labelPadding=12,
                ticks=False,
                domain=False,
                grid=False,
            ),
        ),
        yOffset=alt.YOffset(
            "Detector:N",
            sort=ordered_dets,
            scale=alt.Scale(paddingInner=0.12),
        ),
    )

    bars = base.mark_bar(
        cornerRadiusTopRight=5,
        cornerRadiusBottomRight=5,
        height=16 if len(ordered_dets) >= 3 else 20,
    ).encode(
        x=alt.X(
            "bar_pct:Q",
            scale=alt.Scale(domain=[0, domain_max], nice=False),
            title="Attacks Flagged (%)",
            axis=alt.Axis(
                values=tick_vals,
                labelExpr="datum.value + '%'",
                labelColor="#A8B3D3",
                labelFontSize=11,
                titleColor="#A8B3D3",
                titleFontSize=11.5,
                titleFontWeight=600,
                titlePadding=10,
                grid=True,
                gridColor="rgba(145, 71, 255, 0.14)",
                gridDash=[3, 3],
                domainColor="rgba(145, 71, 255, 0.28)",
                tickColor="rgba(145, 71, 255, 0.28)",
            ),
        ),
        color=alt.Color(
            "Detector:N",
            scale=alt.Scale(domain=ordered_dets, range=ordered_colors),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("Detector:N", title="Detector"),
            alt.Tooltip("Language:N", title="Language"),
            alt.Tooltip("pct_label:N", title="Attacks Flagged"),
            alt.Tooltip("Flagged / Total:N", title="Flagged / Total"),
            alt.Tooltip("95% CI:N", title="95% Confidence Interval"),
            alt.Tooltip("Benign Flagged (FP):N", title="Benign False Positive"),
        ],
    )

    labels = base.mark_text(
        align="left",
        baseline="middle",
        dx=7,
        fontSize=11.5,
        fontWeight=600,
        color="#E2E8FF",
    ).encode(
        x=alt.X("bar_pct:Q"),
        text=alt.Text("pct_label:N"),
    )

    chart_height = max(215, 78 * len(lang_order))
    chart = (
        alt.layer(bars, labels)
        .properties(height=chart_height, padding={"top": 8, "right": 32, "bottom": 6, "left": 6})
        .configure(background="transparent", font="Inter, Segoe UI, system-ui, sans-serif")
        .configure_view(stroke=None, fill="transparent")
    )
    return chart, legend_items


def detection_section(title: str, found, note: str) -> None:
    if found is None:
        return
    name, data = found
    rows = detection_rows(data)
    st.markdown(
        ui.benchmark_detection_section_html(title, name, note, str(data.get("dataset", "")), rows),
        unsafe_allow_html=True,
    )
    built = _build_detection_chart(rows)
    if built is not None:
        alt_chart, legend_items = built
        safe_key = re.sub(r"[^a-zA-Z0-9_]", "_", name)
        with st.container(key=f"bm_chart_{safe_key}"):
            st.markdown(ui.benchmark_chart_header_html(legend_items), unsafe_allow_html=True)
            st.altair_chart(alt_chart, width="stretch")


def agent_section(title: str, found) -> None:
    if found is None:
        return
    name, data = found
    rows = agent_rows(data)
    outcomes = outcome_rows(data)
    st.markdown(
        ui.benchmark_agent_section_html(title, name, data, rows, outcomes),
        unsafe_allow_html=True,
    )


def benchmarks_page() -> None:
    head_left, head_right = st.columns([3.65, 0.78], gap="small", vertical_alignment="center")
    with head_left:
        st.markdown(
            f'<div class="audit-header" style="margin-bottom:0">'
            f'<span class="audit-header-icon">{ui.icon("chart", 24, "#D8B4FE")}</span>'
            f'<div class="audit-header-text">'
            f'<div class="audit-h1" role="heading" aria-level="1">Benchmarks</div>'
            f'<div class="audit-sub">Numbers come only from saved runs in benchmark/results/. '
            f'Small samples: read the 95% intervals. Full write-up with caveats: docs/results.md.</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
    with head_right:
        results_doc = ROOT / "docs" / "results.md"
        if results_doc.exists():
            with st.popover("docs/results.md", icon=":material/description:", width="stretch"):
                st.markdown(results_doc.read_text(encoding="utf-8"))

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


def _policy_matches_search(rule: dict, query: str) -> bool:
    if not query or not query.strip():
        return True
    q = query.strip().lower()
    haystack = " ".join([
        str(rule.get("id", "")),
        str(rule.get("description", "")),
        " ".join(str(t) for t in rule.get("tools", [])),
        json.dumps(rule.get("when") or {}, ensure_ascii=False),
        str(rule.get("decision", "")),
        str(rule.get("reason_en", "")),
        str(rule.get("reason_bn", "")),
    ]).lower()
    return q in haystack


def policies_page() -> None:
    rules = policy_rules()
    policy_file = Path(DEFAULT_POLICY_PATH).name

    # Header
    st.markdown(
        f'<div class="audit-header">'
        f'<span class="audit-header-icon">{ui.icon("scale", 24, "#D8B4FE")}</span>'
        f'<div class="audit-header-text">'
        f'<div class="audit-h1" role="heading" aria-level="1">Policies</div>'
        f'<div class="audit-sub">Deterministic rules from {ui.esc(policy_file)}. '
        f'If several match, the most severe decision wins (block &gt; ask &gt; allow).</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # 3 KPI Summary Cards (matched against search if active, or full ruleset)
    st.session_state.setdefault("policy_decision_filter", "all")
    st.session_state.setdefault("policy_search", "")

    total_count = len(rules)
    block_count = sum(1 for r in rules if r.get("decision") == "block")
    ask_count = sum(1 for r in rules if r.get("decision") == "ask_human")

    kpis_html = "".join([
        ui.policy_kpi_card("layers", "#9147FF", total_count, "Total Policies"),
        ui.policy_kpi_card("shield-x", "#FF526F", block_count, "Block Policies"),
        ui.policy_kpi_card("circle-help", "#FFB547", ask_count, "Ask Policies"),
    ])
    st.markdown(f'<div class="policy-kpis">{kpis_html}</div>', unsafe_allow_html=True)

    # Filter & Search Toolbar + Add Policy action
    search_val = st.session_state.get("policy_search", "")
    search_matched = [r for r in rules if _policy_matches_search(r, search_val)]
    chip_counts = {
        "all": len(search_matched),
        "block": sum(1 for r in search_matched if r.get("decision") == "block"),
        "ask_human": sum(1 for r in search_matched if r.get("decision") == "ask_human"),
    }
    chip_labels = {
        "all": f"All ({chip_counts['all']})",
        "block": f"Block ({chip_counts['block']})",
        "ask_human": f"Ask ({chip_counts['ask_human']})",
    }

    with st.container(key="policy_toolbar"):
        c_chips, c_search, c_add = st.columns([1.35, 1.85, 0.58], gap="small", vertical_alignment="center")
        with c_chips:
            with st.container(key="policy_decision_wrap"):
                dec_filter = st.radio(
                    "Policy decision filter",
                    list(chip_labels),
                    format_func=chip_labels.get,
                    horizontal=True,
                    label_visibility="collapsed",
                    key="policy_decision_filter",
                )
        with c_search:
            search_query = st.text_input(
                "Search policies",
                placeholder="Search policies, tools, or description...",
                label_visibility="collapsed",
                key="policy_search",
            )
        with c_add:
            with st.container(key="policy_add_wrap"):
                with st.popover("+ Add Policy", width="stretch"):
                    st.markdown("**Validate & Generate Policy Rule (YAML)**")
                    st.caption(
                        f"`{policy_file}` is preserved read-only at runtime. "
                        "Validate a rule against `PolicyRule` and copy the YAML snippet."
                    )
                    new_id = st.text_input("Rule ID", value="custom_transfer_rule", key="p_new_id")
                    new_desc = st.text_input(
                        "Description",
                        value="Require approval for transfers above threshold.",
                        key="p_new_desc",
                    )
                    new_tools = st.text_input("Tools (comma-separated)", value="send_money", key="p_new_tools")
                    new_dec = st.selectbox("Decision", ["ask_human", "block"], key="p_new_dec")
                    new_risk = st.slider("Risk score", 0.1, 1.0, 0.7, 0.05, key="p_new_risk")
                    new_tainted = st.checkbox("Require tainted context (tainted: true)", value=False, key="p_new_taint")
                    new_gt = st.number_input("Amount greater than (0 = none)", min_value=0, value=10000, step=1000, key="p_new_gt")
                    new_bn = st.text_input(
                        "Reason (Bangla)",
                        value="{limit} টাকার বেশি ট্রান্সফারে আপনার অনুমতি লাগবে।",
                        key="p_new_bn",
                    )
                    new_en = st.text_input(
                        "Reason (English)",
                        value="Transfers above {limit} BDT need your approval.",
                        key="p_new_en",
                    )
                    when_dict: dict = {}
                    if new_tainted:
                        when_dict["tainted"] = True
                    if new_gt > 0:
                        when_dict["argument_gt"] = {"argument": "amount", "value": int(new_gt)}
                    candidate = {
                        "id": new_id.strip() or "custom_rule",
                        "description": new_desc.strip(),
                        "tools": [t.strip() for t in new_tools.split(",") if t.strip()] or ["send_money"],
                        "when": when_dict,
                        "decision": new_dec,
                        "risk": round(float(new_risk), 2),
                        "reason_en": new_en,
                        "reason_bn": new_bn,
                    }
                    try:
                        validated = PolicyRule.model_validate(candidate)
                        yaml_snippet = yaml.safe_dump(
                            [validated.model_dump(mode="json", exclude_none=True)],
                            allow_unicode=True,
                            sort_keys=False,
                        )
                        st.success("Valid `PolicyRule` schema.")
                        st.code(yaml_snippet, language="yaml")
                    except Exception as exc:
                        st.error(f"Validation error: {exc}")

    # Filter rules by search + decision chip
    filtered_rules = [
        r for r in rules
        if _policy_matches_search(r, search_query)
        and (dec_filter == "all" or r.get("decision") == dec_filter)
    ]

    if not filtered_rules:
        st.info("No policy rules match your current search or filter.")
        return

    # Render Policy Cards
    cards_html = []
    for rule in filtered_rules:
        rid = rule["id"]
        inspect_href = f"?page=Policies&prule={rid}&pmode=inspect"
        copy_href = f"?page=Policies&prule={rid}&pmode=yaml"
        detail_href = f"?page=Policies&prule={rid}&pmode=details"
        cards_html.append(ui.policy_card_html(rule, inspect_href, copy_href, detail_href))
    st.markdown("".join(cards_html), unsafe_allow_html=True)

    # Handle card action links (Inspect / Copy YAML / Rule Details)
    selected_rule_id = st.query_params.get("prule")
    selected_mode = st.query_params.get("pmode", "yaml")
    target_rule = next((r for r in rules if r.get("id") == selected_rule_id), None)
    if target_rule is not None:
        with st.container(key="audit_drawer_card"):
            h1, h2 = st.columns([4, 0.6], vertical_alignment="center")
            h1.markdown(f"**Rule `{target_rule['id']}` — {selected_mode.upper()}**")
            if h2.button("Close", key="policy_close_action", width="stretch"):
                del st.query_params["prule"]
                if "pmode" in st.query_params:
                    del st.query_params["pmode"]
                st.rerun()
            if selected_mode == "yaml":
                st.code(yaml.safe_dump([target_rule], allow_unicode=True, sort_keys=False), language="yaml")
            elif selected_mode == "inspect":
                st.code(json.dumps(target_rule, ensure_ascii=False, indent=2), language="json")
            else:
                st.markdown(
                    f"- **Decision:** `{target_rule['decision']}` (risk `{target_rule.get('risk', 0)}`)\n"
                    f"- **Tools:** `{', '.join(target_rule.get('tools', []))}`\n"
                    f"- **English template:** {target_rule.get('reason_en', '')}\n"
                    f"- **Bangla template:** {target_rule.get('reason_bn', '')}"
                )


def _load_dataset_files() -> tuple[list[dict], list[str]]:
    files: list[dict] = []
    all_sources: set[str] = set()
    for path in sorted((ROOT / "datasets").glob("*.jsonl")):
        lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        reviewed = sum("reviewed=yes" in (r.get("notes") or "") for r in lines)
        file_sources = sorted({str(r.get("source", "?")) for r in lines})
        all_sources.update(file_sources)
        files.append({
            "file": path.name,
            "path": path,
            "items": len(lines),
            "reviewed_count": reviewed,
            "reviewed": f"{reviewed} / {len(lines)}",
            "sources_set": set(file_sources),
            "sources": ", ".join(file_sources),
            "records": lines,
        })
    return files, sorted(all_sources)


def datasets_page() -> None:
    st.session_state.setdefault("dataset_search", "")
    st.session_state.setdefault("dataset_source_filter", "All Sources")

    # Header (Left: icon + title + subtitle; Right: Refresh + View README)
    head_left, head_right = st.columns([3.2, 1.05], gap="small", vertical_alignment="center")
    with head_left:
        st.markdown(
            f'<div class="audit-header" style="margin-bottom:0">'
            f'<span class="audit-header-icon">{ui.icon("database", 24, "#D8B4FE")}</span>'
            f'<div class="audit-header-text">'
            f'<div class="audit-h1" role="heading" aria-level="1">Datasets</div>'
            f'<div class="audit-sub">Labeled texts used by the benchmark and for training. '
            f'Fake data only (numbers start with 010, domains end in .example).</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
    with head_right:
        hr1, hr2 = st.columns([0.88, 1.15], gap="small", vertical_alignment="center")
        if hr1.button("Refresh", icon=":material/refresh:", key="dataset_refresh", width="stretch"):
            dataset_summary.clear()
            st.rerun()
        with hr2:
            with st.popover("View README", icon=":material/description:", width="stretch"):
                readme_path = ROOT / "datasets" / "README.md"
                if readme_path.exists():
                    st.markdown(readme_path.read_text(encoding="utf-8"))
                else:
                    st.info("datasets/README.md not found.")

    summary = dataset_summary()
    total_attack = sum(c.get("attack", 0) for c in summary.values())
    total_benign = sum(c.get("benign", 0) for c in summary.values())

    # 1 & 2. Language Distribution (Left) + Dataset Overview Donut Chart (Right)
    col_lang, col_donut = st.columns([1.48, 1], gap="medium")
    with col_lang:
        st.markdown(ui.dataset_lang_card_html(summary), unsafe_allow_html=True)
    with col_donut:
        st.markdown(ui.dataset_donut_card_html(total_attack, total_benign), unsafe_allow_html=True)

    # 3 & 4. Dataset Files Card with Search + Source Filter
    files, distinct_sources = _load_dataset_files()
    with st.container(key="ds_files_card"):
        fh_left, fh_search, fh_src = st.columns([1.55, 1.05, 0.65], gap="small", vertical_alignment="center")
        with fh_left:
            st.markdown(
                f'<div class="ds-card-head" style="margin-bottom:.25rem">'
                f'<div class="ds-card-ic">{ui.icon("file-text", 19, "#D8B4FE")}</div>'
                f'<div><div class="ds-card-title">Dataset Files</div>'
                f'<div class="ds-card-sub">Dataset files, sizes and usage across the platform.</div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with fh_search:
            ds_query = st.text_input(
                "Search dataset files",
                placeholder="Search file (e.g., attacks.jsonl)...",
                label_visibility="collapsed",
                key="dataset_search",
            )
        with fh_src:
            ds_source = st.selectbox(
                "Filter by source",
                ["All Sources"] + distinct_sources,
                label_visibility="collapsed",
                key="dataset_source_filter",
            )

        q_lower = ds_query.strip().lower()
        filtered_files = [
            f for f in files
            if (not q_lower or q_lower in f["file"].lower() or q_lower in f["sources"].lower())
            and (ds_source == "All Sources" or ds_source in f["sources_set"])
        ]

        if not filtered_files:
            st.info("No dataset files match your current search or source filter.")
        else:
            st.markdown(ui.dataset_files_table_html(filtered_files), unsafe_allow_html=True)

    # 5. Functional File Preview / Open Action Drawer
    selected_dfile = st.query_params.get("dfile")
    selected_daction = st.query_params.get("daction", "preview")
    target_file = next((f for f in files if f["file"] == selected_dfile), None)
    if target_file is not None:
        with st.container(key="audit_drawer_card"):
            dh1, dh2, dh3 = st.columns([3.2, 1.1, 0.6], gap="small", vertical_alignment="center")
            dh1.markdown(
                f"**`{target_file['file']}`** — {target_file['items']} items · "
                f"Reviewed `{target_file['reviewed']}` · Sources: `{target_file['sources']}`"
            )
            dh2.download_button(
                "Download JSONL",
                data=target_file["path"].read_bytes(),
                file_name=target_file["file"],
                mime="application/jsonl",
                icon=":material/download:",
                key="dataset_download_jsonl",
                width="stretch",
            )
            if dh3.button("Close", key="dataset_close_preview", width="stretch"):
                del st.query_params["dfile"]
                if "daction" in st.query_params:
                    del st.query_params["daction"]
                st.rerun()

            recs = target_file["records"]
            if selected_daction == "open":
                by_lang: dict[str, dict[str, int]] = {}
                for r in recs:
                    lg = str(r.get("language", "?"))
                    lb = str(r.get("label", "?"))
                    row = by_lang.setdefault(lg, {"attack": 0, "benign": 0, "reviewed": 0})
                    row[lb] = row.get(lb, 0) + 1
                    if "reviewed=yes" in (r.get("notes") or ""):
                        row["reviewed"] += 1
                st.caption("Per-language breakdown in this file:")
                st.dataframe(
                    [{"language": lg, **vals} for lg, vals in sorted(by_lang.items())],
                    width="stretch",
                    hide_index=True,
                )
            st.caption(f"Sample records from `{target_file['file']}` (showing first 15 of {len(recs)}):")
            st.dataframe(
                [
                    {
                        "id": r.get("id", ""),
                        "language": r.get("language", ""),
                        "label": r.get("label", ""),
                        "attack_type": r.get("attack_type") or "–",
                        "source": r.get("source", ""),
                        "notes": r.get("notes", ""),
                        "text": r.get("text", ""),
                    }
                    for r in recs[:15]
                ],
                width="stretch",
                hide_index=True,
            )


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
