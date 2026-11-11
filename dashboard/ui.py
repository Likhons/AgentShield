"""Design system for the AgentShield dashboard: dark theme CSS, Lucide icons
(inline SVG, ISC license) and small HTML building blocks.

Everything here is presentation only. Numbers shown with these helpers must come
from real sources (audit log, policy file, dataset, benchmark/results).
"""

from __future__ import annotations

import html

# ---------------------------------------------------------------------------
# Lucide icons (https://lucide.dev, ISC license): inner SVG markup, 24x24 grid.
# ---------------------------------------------------------------------------
_ICONS = {
    "shield": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
    "shield-check": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    "play": '<polygon points="6 3 20 12 6 21 6 3"/>',
    "chart": '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    "file-text": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/>',
    "layers": '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "zap": '<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>',
    "mail": '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    "circle-check": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "circle-help": '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    "circle-x": '<circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>',
    "bug": '<path d="m8 2 1.88 1.88"/><path d="M14.12 3.88 16 2"/><path d="M9 7.13v-1a3.003 3.003 0 1 1 6 0v1"/><path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6"/><path d="M12 20v-9"/><path d="M6.53 9C4.6 8.8 3 7.1 3 5"/><path d="M6 13H2"/><path d="M3 21c0-2.1 1.7-3.9 3.8-4"/><path d="M20.97 5c0 2.1-1.6 3.8-3.5 4"/><path d="M22 13h-4"/><path d="M17.2 17c2.1.1 3.8 1.9 3.8 4"/>',
    "list-checks": '<path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "eye-off": '<path d="M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49"/><path d="M14.084 14.158a3 3 0 0 1-4.242-4.242"/><path d="M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143"/><path d="m2 2 20 20"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "scale": '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "activity": '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>',
    "workflow": '<rect width="8" height="8" x="3" y="3" rx="2"/><path d="M7 11v4a2 2 0 0 0 2 2h4"/><rect width="8" height="8" x="13" y="13" rx="2"/>',
}


def icon(name: str, size: int = 18, color: str = "currentColor", stroke: float = 2) -> str:
    return (f'<svg class="ic" xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
            f'fill="none" stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">'
            f'{_ICONS[name]}</svg>')


def esc(text: object) -> str:
    return html.escape(str(text))


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------
CSS = """
<style>
:root {
  --bg: #080D24; --side: #070B1D; --card: #131A38; --card2: #1A2045;
  --accent: #7138FF; --accent2: #B44CFF; --text: #F5F5FF; --muted: #A8B0CE;
  --ok: #16C784; --warn: #F5A623; --bad: #F04452;
  --line: rgba(140, 120, 255, 0.18); --line2: rgba(140, 120, 255, 0.32);
  --radius: 14px;
}
html, body, .stApp, [class*="css"], .stMarkdown, button, input, textarea {
  font-family: "Inter", "Segoe UI", "Nirmala UI", "Noto Sans Bengali", system-ui, sans-serif;
}
.stApp { background: radial-gradient(1200px 500px at 70% -10%, rgba(113,56,255,.18), transparent 60%), var(--bg); }
header[data-testid="stHeader"] { background: transparent; }
@media (max-width: 760px) {
  /* on phones the menu button floats over scrolled content, so the bar gets a solid background */
  header[data-testid="stHeader"] { background: rgba(8,13,36,.88); backdrop-filter: blur(8px); }
}
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"] { display: none; }
.block-container { padding-top: 4rem; max-width: 1480px; }
.ic { vertical-align: middle; flex-shrink: 0; }
h1, h2, h3 { color: var(--text); letter-spacing: -0.01em; }

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] { background: var(--side); border-right: 1px solid var(--line); }
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] { position: absolute; top: 0; right: 0; z-index: 3;
  height: auto; padding: .7rem .7rem 0 0; }
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding-top: 1.4rem; }
.brand { display: flex; gap: .7rem; align-items: center; padding: 0 2.2rem 1.1rem .2rem; }
.brand-name { font-weight: 800; font-size: 1.25rem; color: var(--text); line-height: 1.1; }
.brand-sub { font-size: .78rem; color: var(--muted); }
.side-label { font-size: .7rem; letter-spacing: .08em; color: #6E7699; text-transform: uppercase; margin: .4rem 0 .3rem .2rem; }
.st-key-nav_page, .st-key-nav_page [data-testid="stRadio"], .st-key-nav_page [data-testid="stRadioGroup"] { width: 100% !important; }
.st-key-nav [role="radiogroup"] { gap: .25rem; display: flex; flex-direction: column; align-items: stretch; width: 100%; }
.st-key-nav [role="radiogroup"] > div { width: 100%; border-radius: 10px; border: 1px solid transparent;
  transition: background .15s, border-color .15s; }
.st-key-nav [data-testid="stRadioOption"] { width: 100%; padding: .6rem .8rem; cursor: pointer; box-sizing: border-box; }
.st-key-nav [data-testid="stRadioOption"] > div > div:first-child { display: none; }
.st-key-nav [role="radiogroup"] > div:hover { background: rgba(113,56,255,.10); }
.st-key-nav [role="radiogroup"] > div[data-selected="true"] {
  background: linear-gradient(90deg, rgba(113,56,255,.6), rgba(180,76,255,.35));
  border-color: rgba(180,76,255,.55); box-shadow: 0 0 18px rgba(113,56,255,.35); }
.st-key-nav [data-testid="stRadioOption"] p { font-size: .95rem; font-weight: 500; color: var(--text); }
.st-key-nav [data-testid="stRadioOption"] p span[role="img"] { margin-right: .35rem; color: #C9B6FF; }
.status { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: .9rem 1rem; margin-top: 1.2rem; }
.status-head { display: flex; gap: .5rem; align-items: center; font-weight: 600; color: var(--text); margin-bottom: .55rem; }
.dot { width: 9px; height: 9px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 8px var(--ok); }
.status-row { display: flex; justify-content: space-between; font-size: .82rem; color: var(--muted); padding: .18rem 0; }
.status-row b { color: var(--text); font-weight: 500; }
.version { color: #6E7699; font-size: .75rem; margin-top: .7rem; }

/* ---------- hero ---------- */
.hero-title { font-size: 2.55rem; font-weight: 800; line-height: 1.15; margin: 0 0 .7rem; padding: 0; color: var(--text); letter-spacing: -0.01em; }
[data-testid="stHeaderActionElements"] { display: none; }
.grad { background: linear-gradient(90deg, #B44CFF, #8B5CFF); -webkit-background-clip: text; background-clip: text; color: transparent; }
.hero p.lead { color: var(--muted); font-size: 1.08rem; max-width: 560px; margin-bottom: 1.1rem; }
.cta-row { display: flex; gap: .7rem; flex-wrap: wrap; }
.cta { display: inline-flex; gap: .5rem; align-items: center; padding: .65rem 1.15rem; border-radius: 10px;
  font-weight: 600; font-size: .95rem; text-decoration: none !important; transition: transform .15s, box-shadow .15s; }
.cta:hover { transform: translateY(-1px); }
.cta-primary { background: linear-gradient(90deg, var(--accent), var(--accent2)); color: #fff !important; box-shadow: 0 6px 22px rgba(113,56,255,.35); }
.cta-ghost { border: 1px solid var(--line2); color: var(--text) !important; background: rgba(255,255,255,.02); }
.hero-art { position: relative; height: 270px; }
.hero-art svg.shield-art { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -52%); }
.feat { position: absolute; display: inline-flex; gap: .45rem; align-items: center; padding: .42rem .8rem; border-radius: 999px;
  background: rgba(19,26,56,.88); border: 1px solid var(--line2); color: var(--text); font-size: .8rem; font-weight: 500;
  backdrop-filter: blur(4px); white-space: nowrap; }
.feat .ic { color: #C9B6FF; }

/* ---------- cards ---------- */
.kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .9rem; margin: .6rem 0 1.1rem; }
.kpi { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: 1rem 1.1rem;
  display: flex; gap: .9rem; align-items: center; }
.kpi-icon { width: 46px; height: 46px; border-radius: 12px; display: grid; place-items: center; flex-shrink: 0; }
.kpi-num { font-size: 1.75rem; font-weight: 800; color: var(--text); line-height: 1.05; }
.kpi-label { color: var(--muted); font-size: .85rem; }
.kpi-note { font-size: .72rem; color: #8E96B8; margin-top: .15rem; }
.trend { display: inline-block; font-size: .72rem; font-weight: 600; padding: .05rem .4rem; border-radius: 6px; margin-left: .35rem;
  background: rgba(22,199,132,.14); color: var(--ok); vertical-align: middle; }
.panel-title { display: flex; gap: .6rem; align-items: center; font-size: 1.15rem; font-weight: 700; color: var(--text); margin-bottom: .2rem; }
.panel-sub { color: var(--muted); font-size: .88rem; margin-bottom: .6rem; }
.play-badge { width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center;
  background: linear-gradient(135deg, var(--accent), var(--accent2)); }

/* Streamlit bordered containers become our cards */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) { border-radius: var(--radius); }
.st-key-card_run, .st-key-card_how, .st-key-card_pipe, .st-key-card_recent, .st-key-card_dec {
  background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: 1.1rem 1.2rem; }
.st-key-card_run { border-color: var(--line2); }

/* agent mode cards (radio) */
.st-key-agent_mode, .st-key-agent_mode [data-testid="stRadio"], .st-key-agent_mode [data-testid="stRadioGroup"] { width: 100% !important; }
.st-key-mode [role="radiogroup"] { display: grid !important; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .6rem; align-items: stretch; width: 100%; }
.st-key-mode [role="radiogroup"] > div { margin: 0; padding: .8rem .85rem; border-radius: 12px; background: var(--card2);
  border: 1px solid var(--line); transition: border-color .15s, box-shadow .15s, background .15s; min-height: 96px; cursor: pointer; }
.st-key-mode [role="radiogroup"] > div:hover { border-color: var(--line2); }
.st-key-mode [role="radiogroup"] > div[data-selected="true"] { border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent), 0 0 22px rgba(113,56,255,.35); background: rgba(113,56,255,.13); }
.st-key-mode [data-testid="stRadioOption"] p { font-weight: 600; color: var(--text); }
.st-key-mode [data-testid="stRadioOption"] p span[role="img"] { color: #C9B6FF; margin-right: .2rem; }
.st-key-mode [data-testid="stRadioCaption"] { color: var(--muted); font-size: .8rem; padding-left: 0; margin-top: .2rem; }

/* primary button = refined purple gradient */
.stButton > button[data-testid="stBaseButton-primary"] { background: linear-gradient(90deg, var(--accent), var(--accent2)); border: 0; border-radius: 10px;
  padding: .7rem 1rem; font-weight: 700; font-size: 1rem; box-shadow: 0 6px 22px rgba(113,56,255,.35); }
.stButton > button[data-testid="stBaseButton-primary"]:hover { filter: brightness(1.08); }

/* how it works */
.flow { display: grid; grid-template-columns: 1fr auto 1.15fr auto 1fr; gap: .5rem; align-items: center; margin-top: .4rem; }
.node { border-radius: 12px; padding: .8rem .6rem; text-align: center; border: 1px solid var(--line); background: var(--card2); }
.node b { display: block; color: var(--text); font-size: .9rem; margin-top: .35rem; }
.node span { color: var(--muted); font-size: .76rem; }
.node-user { background: rgba(240,68,82,.10); border-color: rgba(240,68,82,.35); }
.node-shield { background: rgba(113,56,255,.18); border-color: rgba(180,76,255,.6); box-shadow: 0 0 22px rgba(113,56,255,.3); }
.node-dec { background: rgba(22,199,132,.10); border-color: rgba(22,199,132,.35); }
.flow .arrow { color: #8E96B8; }
.decs { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .6rem; margin-top: .5rem; }
.dec { border-radius: 12px; padding: .75rem .85rem; display: flex; flex-direction: column; gap: .45rem; align-items: flex-start; }
.dec b { color: var(--text); display: block; font-size: .95rem; }
.dec span { color: var(--muted); font-size: .78rem; }
.dec-allow { background: rgba(22,199,132,.12); border: 1px solid rgba(22,199,132,.35); }
.dec-ask { background: rgba(245,166,35,.12); border: 1px solid rgba(245,166,35,.35); }
.dec-block { background: rgba(240,68,82,.12); border: 1px solid rgba(240,68,82,.35); }

/* pipeline */
.pipe { display: grid; grid-template-columns: 1fr auto 1fr auto 1fr auto 1fr; gap: .45rem; align-items: stretch; margin-top: .5rem; }
.pnode { background: var(--card2); border: 1px solid var(--line2); border-radius: 12px; padding: .7rem .75rem; display: flex; gap: .6rem; align-items: center; }
.pnode b { color: var(--text); font-size: .86rem; display: block; }
.pnode span { color: var(--muted); font-size: .74rem; }
.pnode .ic { color: #C9B6FF; }
.pipe .arrow { color: #8E96B8; align-self: center; }

/* recent evaluations */
.rtable { width: 100%; border-collapse: collapse; font-size: .84rem; }
.rtable th { text-align: left; color: #8E96B8; font-weight: 500; padding: .45rem .4rem; border-bottom: 1px solid var(--line); }
.rtable td { color: var(--text); padding: .55rem .4rem; border-bottom: 1px solid rgba(140,120,255,.08); vertical-align: top; }
.rtable td.muted { color: var(--muted); }
.link { color: #C9B6FF !important; text-decoration: none !important; font-size: .85rem; font-weight: 500; }
.badge { display: inline-block; padding: .14rem .55rem; border-radius: 7px; font-size: .72rem; font-weight: 700; letter-spacing: .02em; }
.b-allow { background: rgba(22,199,132,.16); color: var(--ok); }
.b-ask { background: rgba(245,166,35,.16); color: var(--warn); }
.b-block { background: rgba(240,68,82,.18); color: #FF6B78; }
.empty { color: var(--muted); font-size: .88rem; padding: .8rem 0; }

/* results */
.summary { border-radius: var(--radius); padding: 1rem 1.3rem; margin: 1rem 0; font-size: 1.15rem; font-weight: 700; color: #fff;
  background: linear-gradient(90deg, rgba(22,199,132,.85), rgba(15,118,110,.85)); border: 1px solid rgba(22,199,132,.6); }
.col-head { border-radius: 12px; padding: .7rem 1rem; margin-bottom: .8rem; font-weight: 700; font-size: 1.05rem; display: flex; gap: .5rem; align-items: center; }
.col-unsafe { background: rgba(240,68,82,.12); color: #FF8A94; border: 1px solid rgba(240,68,82,.4); }
.col-safe { background: rgba(22,199,132,.12); color: #4BE0A8; border: 1px solid rgba(22,199,132,.4); }
.money { font-size: 2.1rem; font-weight: 800; line-height: 1.1; color: var(--text); }
.money-lost { color: #FF6B78; } .money-ok { color: var(--ok); }
.money-label { color: var(--muted); font-size: .8rem; }
.user-quote { border-left: 3px solid var(--accent); background: var(--card2); padding: .55rem .85rem; border-radius: 0 10px 10px 0; margin: .6rem 0; color: var(--text); }
.reason-bn { font-size: 1rem; margin: .3rem 0; color: var(--text); }
[data-testid="stCode"] pre, [data-testid="stCode"] code { white-space: pre-wrap !important; word-break: break-word; }
[data-testid="stExpander"] details { background: var(--card); border: 1px solid var(--line); border-radius: 12px; }
.page-title { font-size: 1.8rem; font-weight: 800; color: var(--text); margin: .2rem 0 .1rem; }
.page-sub { color: var(--muted); margin-bottom: 1rem; }
.rule { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: 1rem 1.1rem; margin-bottom: .8rem; }
.rule-head { display: flex; justify-content: space-between; gap: 1rem; align-items: center; }
.rule-id { font-weight: 700; color: var(--text); font-family: ui-monospace, Consolas, monospace; font-size: .92rem; }
.rule p { color: var(--muted); margin: .4rem 0; font-size: .9rem; }
.cond { display: inline-block; background: var(--card2); border: 1px solid var(--line); border-radius: 7px; padding: .1rem .5rem;
  margin: .15rem .3rem .15rem 0; font-size: .78rem; color: #C9B6FF; font-family: ui-monospace, Consolas, monospace; }

/* ---------- motion: slow, purposeful, never decorative noise ---------- */
:root { --ease: cubic-bezier(.22, .61, .36, 1); }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
@keyframes breathe { 0%, 100% { opacity: .75; } 50% { opacity: 1; } }
@keyframes orbit { to { stroke-dashoffset: -1000; } }
@keyframes rise { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
@keyframes sheen { from { transform: translateX(-120%) skewX(-18deg); } to { transform: translateX(260%) skewX(-18deg); } }
@keyframes scan { 0%, 12%, 100% { border-color: var(--line2); box-shadow: none; }
                  4% { border-color: rgba(180,76,255,.85); box-shadow: 0 0 0 1px rgba(180,76,255,.45), 0 0 22px rgba(113,56,255,.35); } }
@keyframes halo { 0%, 100% { box-shadow: 0 0 18px rgba(113,56,255,.25); } 50% { box-shadow: 0 0 30px rgba(113,56,255,.45); } }

/* hero: the shield floats, a light streak orbits its ring, the aura breathes */
.shield-art .shield-body { animation: float 6s var(--ease) infinite; transform-box: fill-box; transform-origin: center; }
.shield-art .orbit { stroke-dashoffset: 0; animation: orbit 9s linear infinite; opacity: .9; }
.shield-art .aura, .shield-art .pad-glow { animation: breathe 6s var(--ease) infinite; }
.feat { animation: rise .6s var(--ease) backwards; transition: border-color .25s var(--ease), transform .25s var(--ease), background .25s; }
.feat:nth-of-type(1) { animation-delay: .05s; } .feat:nth-of-type(2) { animation-delay: .12s; } .feat:nth-of-type(3) { animation-delay: .19s; }
.feat:nth-of-type(4) { animation-delay: .26s; } .feat:nth-of-type(5) { animation-delay: .33s; } .feat:nth-of-type(6) { animation-delay: .40s; }
.feat:hover { border-color: rgba(180,76,255,.7); background: rgba(40,30,90,.9); transform: translateY(-1px); }

/* cards: a quiet lift and a brighter edge on hover */
.kpi, .node, .dec, .pnode, .rule, .status, .st-key-card_run, .st-key-card_how, .st-key-card_pipe, .st-key-card_recent {
  transition: transform .28s var(--ease), border-color .28s var(--ease), box-shadow .28s var(--ease), background .28s; }
.kpi:hover, .rule:hover { transform: translateY(-2px); border-color: var(--line2);
  box-shadow: 0 10px 30px -12px rgba(0,0,0,.6), 0 0 0 1px rgba(140,120,255,.12); }
.kpi .kpi-icon { transition: transform .28s var(--ease), box-shadow .28s var(--ease); }
.kpi:hover .kpi-icon { transform: scale(1.06); box-shadow: 0 0 18px rgba(113,56,255,.25); }
.kpi { animation: rise .55s var(--ease) backwards; }
.kpis .kpi:nth-child(2) { animation-delay: .06s; } .kpis .kpi:nth-child(3) { animation-delay: .12s; } .kpis .kpi:nth-child(4) { animation-delay: .18s; }
.st-key-card_how:hover, .st-key-card_pipe:hover, .st-key-card_recent:hover { border-color: var(--line2); }
.node:hover, .dec:hover { transform: translateY(-2px); }
.node-shield { animation: halo 4s var(--ease) infinite; }

/* pipeline: each check lights up in turn, like a tool call passing through */
.pipe .pnode { animation: scan 6s var(--ease) infinite; }
.pipe .pnode:nth-child(1) { animation-delay: 0s; } .pipe .pnode:nth-child(3) { animation-delay: .7s; }
.pipe .pnode:nth-child(5) { animation-delay: 1.4s; } .pipe .pnode:nth-child(7) { animation-delay: 2.1s; }
.pnode:hover { border-color: rgba(180,76,255,.8); }

/* buttons */
.cta-primary, .stButton > button[data-testid="stBaseButton-primary"] { position: relative; overflow: hidden; }
.cta-primary::after, .stButton > button[data-testid="stBaseButton-primary"]::after {
  content: ""; position: absolute; top: 0; left: 0; width: 40%; height: 100%; pointer-events: none;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.22), transparent); transform: translateX(-120%) skewX(-18deg); }
.cta-primary:hover::after, .stButton > button[data-testid="stBaseButton-primary"]:hover::after { animation: sheen .9s var(--ease); }
.stButton > button[data-testid="stBaseButton-primary"] { transition: transform .2s var(--ease), box-shadow .2s var(--ease), filter .2s; }
.stButton > button[data-testid="stBaseButton-primary"]:hover { transform: translateY(-1px); box-shadow: 0 10px 28px rgba(113,56,255,.45); }
.stButton > button[data-testid="stBaseButton-primary"]:active { transform: translateY(0); }
.cta-ghost { transition: border-color .2s var(--ease), background .2s var(--ease), transform .15s; }
.cta-ghost:hover { border-color: rgba(180,76,255,.6); background: rgba(113,56,255,.08); }

/* sidebar nav */
.st-key-nav [role="radiogroup"] > div { transition: background .2s var(--ease), border-color .2s var(--ease), transform .2s var(--ease); }
.st-key-nav [role="radiogroup"] > div:not([data-selected="true"]):hover { transform: translateX(2px); }
.dot { animation: breathe 2.4s var(--ease) infinite; }

/* results: the outcome arrives, the saved banner catches the light once */
.summary { position: relative; overflow: hidden; animation: rise .5s var(--ease) both; }
.summary::after { content: ""; position: absolute; top: 0; left: 0; width: 35%; height: 100%; pointer-events: none;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.28), transparent); animation: sheen 1.4s .35s var(--ease) both; }
.money, .col-head { animation: rise .5s var(--ease) both; }
.money { animation-delay: .1s; }
.rtable tr { transition: background .2s; }
.rtable tr:hover td { background: rgba(113,56,255,.06); }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}

/* ---------- responsive ---------- */
@media (max-width: 1100px) {
  /* the big two-column rows stack, so cards never get squeezed (sidebar takes ~300px) */
  [data-testid="stHorizontalBlock"]:has(.st-key-card_run), [data-testid="stHorizontalBlock"]:has(.st-key-card_pipe),
  [data-testid="stHorizontalBlock"]:has(.hero), [data-testid="stHorizontalBlock"]:has(.col-head) { flex-wrap: wrap; }
  [data-testid="stHorizontalBlock"]:has(.st-key-card_run) > [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"]:has(.st-key-card_pipe) > [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"]:has(.hero) > [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"]:has(.col-head) > [data-testid="stColumn"] { flex: 1 1 100% !important; min-width: 100% !important; width: 100% !important; }
}
@media (max-width: 1200px) {
  .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .pipe { grid-template-columns: 1fr 1fr; } .pipe .arrow { display: none; }
}
@media (max-width: 760px) {
  .hero-title { font-size: 1.9rem; }
  .kpis { grid-template-columns: 1fr; }
  .st-key-mode [role="radiogroup"] { grid-template-columns: 1fr; }
  .decs { grid-template-columns: 1fr; }
  .flow { grid-template-columns: 1fr; } .flow .arrow { transform: rotate(90deg); justify-self: center; }
  .pipe { grid-template-columns: 1fr; }
  .hero-art { height: auto; display: flex; flex-wrap: wrap; gap: .4rem; justify-content: center; align-items: center; }
  .hero-art .feat { position: static; }
  .hero-art svg.shield-art { position: static; transform: none; width: 180px; height: 180px; }
  .rwrap { overflow-x: auto; }
  .rtable .c-req, .rtable .c-tool { display: none; }
}
</style>
"""

SHIELD_ART = """
<svg class="shield-art" width="250" height="250" viewBox="0 0 250 250" xmlns="http://www.w3.org/2000/svg" aria-label="AgentShield">
  <defs>
    <linearGradient id="sg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#B44CFF"/><stop offset="1" stop-color="#4A22D6"/></linearGradient>
    <linearGradient id="sg2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2A1C72"/><stop offset="1" stop-color="#140F3F"/></linearGradient>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#7138FF" stop-opacity=".55"/><stop offset="1" stop-color="#7138FF" stop-opacity="0"/></radialGradient>
    <filter id="blur"><feGaussianBlur stdDeviation="6"/></filter>
  </defs>
  <circle class="aura" cx="125" cy="118" r="112" fill="url(#glow)"/>
  <ellipse cx="125" cy="200" rx="92" ry="22" fill="none" stroke="#7138FF" stroke-opacity=".55" stroke-width="2"/>
  <ellipse class="pad-glow" cx="125" cy="200" rx="66" ry="14" fill="#7138FF" fill-opacity=".25" filter="url(#blur)"/>
  <ellipse cx="125" cy="120" rx="118" ry="34" fill="none" stroke="#B44CFF" stroke-opacity=".35" stroke-width="1.2"/>
  <ellipse class="orbit" cx="125" cy="120" rx="118" ry="34" fill="none" stroke="#E2D4FF" stroke-width="2.2"
           stroke-linecap="round" pathLength="1000" stroke-dasharray="70 930"/>
  <g class="shield-body">
  <path d="M125 32 L188 56 C188 120 166 162 125 186 C84 162 62 120 62 56 Z" fill="url(#sg)" stroke="#D7C2FF" stroke-opacity=".7" stroke-width="2"/>
  <path d="M125 50 L172 68 C172 118 155 150 125 168 C95 150 78 118 78 68 Z" fill="url(#sg2)" stroke="#B44CFF" stroke-opacity=".6" stroke-width="1.5"/>
  <path d="M101 110 L118 127 L151 92" fill="none" stroke="#FFFFFF" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
</svg>
"""

FEATURES = [  # (label, icon, css position inside .hero-art)
    ("Prompt Injection", "zap", "left:2%; top:6%"),
    ("Data Tainting", "layers", "left:0%; top:42%"),
    ("Multilingual (BN / Banglish / EN)", "globe", "left:3%; top:78%"),
    ("Instruction Hiding", "eye-off", "right:2%; top:6%"),
    ("Unsafe Action", "alert", "right:0%; top:42%"),
    ("Policy Enforcement", "scale", "right:3%; top:78%"),
]


def hero_art() -> str:
    chips = "".join(f'<span class="feat" style="{pos}">{icon(ic, 15)}{esc(label)}</span>' for label, ic, pos in FEATURES)
    return f'<div class="hero-art">{SHIELD_ART}{chips}</div>'


def kpi(icon_name: str, tint: str, number: str, label: str, note: str = "", trend: str = "") -> str:
    trend_html = f'<span class="trend">{esc(trend)}</span>' if trend else ""
    note_html = f'<div class="kpi-note">{esc(note)}</div>' if note else ""
    return (f'<div class="kpi"><div class="kpi-icon" style="background:{tint}22">{icon(icon_name, 22, tint)}</div>'
            f'<div><div class="kpi-num">{esc(number)}{trend_html}</div><div class="kpi-label">{esc(label)}</div>{note_html}</div></div>')


def panel_title(icon_name: str, title: str, sub: str = "", badge: bool = False, right: str = "") -> str:
    ic = f'<span class="play-badge">{icon(icon_name, 18, "#fff")}</span>' if badge else icon(icon_name, 20, "#C9B6FF")
    right_html = f'<span style="margin-left:auto">{right}</span>' if right else ""
    sub_html = f'<div class="panel-sub">{esc(sub)}</div>' if sub else ""
    return f'<div class="panel-title">{ic}{esc(title)}{right_html}</div>{sub_html}'


BADGE_CLASS = {"allow": ("ALLOW", "b-allow"), "ask_human": ("ASK", "b-ask"), "block": ("BLOCK", "b-block")}


def badge(decision: str) -> str:
    text, css = BADGE_CLASS[decision]
    return f'<span class="badge {css}">{text}</span>'


HOW_IT_WORKS = f"""
<div class="flow">
  <div class="node node-user">{icon("mail", 26, "#FF6B78")}<b>Untrusted input</b><span>email, web page, file (possibly malicious)</span></div>
  <div class="arrow">{icon("arrow-right", 22)}</div>
  <div class="node node-shield">{icon("shield-check", 28, "#C9B6FF")}<b>AgentShield</b><span>checks every tool call before it runs</span></div>
  <div class="arrow">{icon("arrow-right", 22)}</div>
  <div class="node node-dec">{icon("circle-check", 26, "#16C784")}<b>Decision</b><span>allow / ask / block</span></div>
</div>
"""

DECISIONS = f"""
<div class="decs">
  <div class="dec dec-allow">{icon("circle-check", 26, "#16C784")}<div><b>ALLOW</b><span>Action follows from the user's request</span></div></div>
  <div class="dec dec-ask">{icon("circle-help", 26, "#F5A623")}<div><b>ASK</b><span>Uncertain: the user approves or rejects</span></div></div>
  <div class="dec dec-block">{icon("circle-x", 26, "#F04452")}<div><b>BLOCK</b><span>Clear attack or policy violation</span></div></div>
</div>
"""

PIPELINE = f"""
<div class="pipe">
  <div class="pnode">{icon("layers", 22)}<div><b>Taint analysis</b><span>Where did each value come from?</span></div></div>
  <div class="arrow">{icon("arrow-right", 18)}</div>
  <div class="pnode">{icon("target", 22)}<div><b>Injection classifier</b><span>Instructions hidden in data?</span></div></div>
  <div class="arrow">{icon("arrow-right", 18)}</div>
  <div class="pnode">{icon("activity", 22)}<div><b>Intent + policy</b><span>Did the user ask? Fixed rules</span></div></div>
  <div class="arrow">{icon("arrow-right", 18)}</div>
  <div class="pnode">{icon("zap", 22)}<div><b>Agent decision</b><span>Allow / Ask / Block + reason (BN/EN)</span></div></div>
</div>
"""
