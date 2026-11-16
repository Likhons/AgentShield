"""Design system for the AgentShield dashboard: dark theme CSS, Lucide icons
(inline SVG, ISC license) and small HTML building blocks.

Everything here is presentation only. Numbers shown with these helpers must come
from real sources (audit log, policy file, dataset, benchmark/results).
"""

from __future__ import annotations

import html
import json

# ---------------------------------------------------------------------------
# Lucide icons (https://lucide.dev, ISC license): inner SVG markup, 24x24 grid.
# ---------------------------------------------------------------------------
_ICONS = {
    "shield": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
    "shield-check": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    "play": '<polygon points="6 3 20 12 6 21 6 3"/>',
    "play-fill": '<polygon points="6 3 20 12 6 21 6 3" fill="currentColor"/>',
    "chart": '<path d="M3 3v18h18"/><path d="M18 17V8"/><path d="M13 17V5"/><path d="M8 17v-6"/>',
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
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "external-link": '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>',
    "calendar": '<rect width="18" height="18" x="3" y="4" rx="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/>',
    "filter": '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "terminal": '<polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/>',
    "copy": '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "shield-x": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m14.5 9.5-5 5"/><path d="m9.5 9.5 5 5"/>',
    "wallet": '<rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "more-horizontal": '<circle cx="12" cy="12" r="1.5" fill="currentColor"/><circle cx="19" cy="12" r="1.5" fill="currentColor"/><circle cx="5" cy="12" r="1.5" fill="currentColor"/>',
    "chevron-left": '<path d="m15 18-6-6 6-6"/>',
    "chevron-right": '<path d="m9 18 6-6-6-6"/>',
    "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
    "edit": '<path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/>',
    "more-vertical": '<circle cx="12" cy="12" r="1.5" fill="currentColor"/><circle cx="12" cy="5" r="1.5" fill="currentColor"/><circle cx="12" cy="19" r="1.5" fill="currentColor"/>',
    "message-square": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "refresh": '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
    "eye": '<path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/>',
    "laptop": '<path d="M20 16V7a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v9m16 0H4m16 0 1.28 2.55a1 1 0 0 1-.9 1.45H3.62a1 1 0 0 1-.9-1.45L4 16"/>',
    "bot": '<path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>',
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
  --bg: #080B1C; --side: #060919; --card: #111733; --card2: #171E40;
  --accent: #9147FF; --accent2: #C044FF; --text: #F5F5FF; --muted: #A2ABD0;
  --ok: #16C784; --warn: #F5A623; --bad: #F04452;
  --line: rgba(145, 71, 255, 0.19); --line2: rgba(192, 68, 255, 0.36);
  --radius: 14px;
}
html, body, .stApp, [class*="css"], .stMarkdown, button, input, textarea {
  font-family: "Inter", "Segoe UI", "Nirmala UI", "Noto Sans Bengali", system-ui, sans-serif;
}
.stApp {
  background:
    radial-gradient(640px 320px at 94% 3%, rgba(192, 68, 255, .17), transparent 68%),
    radial-gradient(960px 460px at 78% -4%, rgba(145, 71, 255, .20), transparent 65%),
    radial-gradient(620px 360px at 24% 0%, rgba(145, 71, 255, .10), transparent 60%),
    radial-gradient(540px 310px at 4% 96%, rgba(145, 71, 255, .15), transparent 66%),
    var(--bg);
}
header[data-testid="stHeader"] { background: transparent; }
.stApp { overflow-x: hidden; }
.block-container, [data-testid="stMainBlockContainer"] {
  padding: 1.5rem 2.2rem 3rem 2.2rem !important;
  max-width: 1480px !important;
  box-sizing: border-box;
}
@media (max-width: 760px) {
  /* on phones the menu button floats over scrolled content, so the bar gets a solid background
     and the content starts below it */
  header[data-testid="stHeader"] { background: rgba(7,11,30,.88); backdrop-filter: blur(8px); }
  .block-container, [data-testid="stMainBlockContainer"] { padding: 4.4rem 1rem 2.2rem 1rem !important; }
}
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"] { display: none; }
.ic { vertical-align: middle; flex-shrink: 0; }
.brand-badge .ic, .play-badge .ic, .sec-badge .ic, .kpi-icon .ic, .node-ic .ic, .feat-ic .ic, .pnode-ic .ic, .row-link .ic {
  display: block; margin: auto; }
h1, h2, h3 { color: var(--text); letter-spacing: -0.01em; }

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {
  background:
    radial-gradient(340px 240px at 20% 98%, rgba(130, 60, 255, .20), transparent 70%),
    var(--side);
  border-right: 1px solid var(--line);
}
@media (min-width: 761px) {
  section[data-testid="stSidebar"][aria-expanded="true"] {
    width: 268px !important;
    min-width: 268px !important;
    max-width: 268px !important;
  }
}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] { position: absolute; top: 0; right: 0; z-index: 3;
  height: auto; padding: .85rem .7rem 0 0; }
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding: 1.15rem 1rem 1.25rem 1rem !important; box-sizing: border-box; }
.brand { display: flex; gap: .75rem; align-items: center; padding: 0 1.85rem 1rem .15rem; border-bottom: 1px solid rgba(140,120,255,.12); margin-bottom: .8rem; }
.brand-badge { width: 38px; height: 38px; border-radius: 11px; display: inline-flex; align-items: center; justify-content: center;
  line-height: 0; flex-shrink: 0;
  background: linear-gradient(135deg, rgba(180,76,255,.26), rgba(113,56,255,.16));
  border: 1px solid rgba(180,76,255,.45); box-shadow: 0 0 18px rgba(140,76,255,.28); }
.brand-name { font-weight: 800; font-size: 1.22rem; color: var(--text); line-height: 1.15; letter-spacing: -0.01em; white-space: nowrap; }
.brand-sub { font-size: .75rem; color: var(--muted); margin-top: .08rem; white-space: nowrap; }
.side-label { font-size: .68rem; font-weight: 700; letter-spacing: .1em; color: #757E9F; text-transform: uppercase; margin: .15rem 0 .42rem .35rem; }
.st-key-nav_page, .st-key-nav_page [data-testid="stRadio"], .st-key-nav_page [data-testid="stRadioGroup"] { width: 100% !important; }
.st-key-nav [role="radiogroup"] { gap: .26rem; display: flex; flex-direction: column; align-items: stretch; width: 100%; }
.st-key-nav [role="radiogroup"] > div { width: 100%; border-radius: 10px; border: 1px solid transparent;
  transition: background .15s, border-color .15s; position: relative; box-sizing: border-box; }
/* Divider + SECURITY section header before the 4th item (Policies) */
.st-key-nav [role="radiogroup"] > div:nth-child(4) { margin-top: 2.15rem; }
.st-key-nav [role="radiogroup"] > div:nth-child(4)::before {
  content: "SECURITY";
  position: absolute;
  top: -1.62rem;
  left: .35rem;
  right: .15rem;
  padding-top: .55rem;
  border-top: 1px solid rgba(140, 120, 255, 0.14);
  font-size: .68rem;
  font-weight: 700;
  letter-spacing: .1em;
  color: #757E9F;
  pointer-events: none;
}
.st-key-nav [data-testid="stRadioOption"] { width: 100%; padding: .56rem .85rem; cursor: pointer; box-sizing: border-box; position: static; }
.st-key-nav [data-testid="stRadioOption"] > div > div:first-child { display: none; }
.st-key-nav [role="radiogroup"] > div:hover { background: rgba(113,56,255,.12); }
.st-key-nav [data-testid="stRadioOption"]::after { content: ""; position: absolute; inset: 0; border-radius: inherit; z-index: 1; cursor: pointer; }
.st-key-nav [role="radiogroup"] > div[data-selected="true"] {
  background: linear-gradient(90deg, #7C3AED 0%, #9333EA 60%, rgba(168,85,247,.75) 100%);
  border-color: rgba(216,180,254,.55);
  box-shadow: 0 4px 20px rgba(124,58,237,.45), inset 0 1px 0 rgba(255,255,255,.22);
}
.st-key-nav [data-testid="stRadioOption"] p {
  font-size: .92rem; font-weight: 500; color: var(--muted); white-space: nowrap;
  display: flex; align-items: center; margin: 0 !important; line-height: 1.25;
}
.st-key-nav [role="radiogroup"] > div[data-selected="true"] [data-testid="stRadioOption"] p { color: #FFFFFF; font-weight: 600; }
.st-key-nav [data-testid="stRadioOption"] p span[role="img"] { margin-right: .45rem; color: #A6B0D4; flex-shrink: 0; }
.st-key-nav [role="radiogroup"] > div[data-selected="true"] [data-testid="stRadioOption"] p span[role="img"] { color: #FFFFFF; }
.status { background: linear-gradient(180deg, rgba(23,30,64,.85), rgba(15,20,46,.92)); border: 1px solid var(--line);
  border-radius: var(--radius); padding: .9rem 1rem; margin-top: 1.15rem; margin-bottom: 0;
  box-sizing: border-box; box-shadow: inset 0 1px 0 rgba(255,255,255,.04); }
.status-head { display: flex; gap: .55rem; align-items: center; font-weight: 700; font-size: .9rem; color: var(--text); margin-bottom: .58rem; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 10px var(--ok); flex-shrink: 0; }
.status-row { display: flex; justify-content: space-between; align-items: center; gap: .5rem; font-size: .8rem; color: var(--muted); padding: .2rem 0; }
.status-row b { color: var(--text); font-weight: 600; text-align: right; }
.version { color: #6E7699; font-size: .74rem; margin-top: .55rem; padding-top: .5rem; border-top: 1px solid rgba(140,120,255,.12); }

/* ---------- hero ---------- */
.hero-pill { display: inline-flex; gap: .4rem; align-items: center; padding: .24rem .72rem; border-radius: 999px;
  background: rgba(113,56,255,.16); border: 1px solid rgba(180,76,255,.38); color: #D8B4FE;
  font-size: .76rem; font-weight: 600; margin-bottom: .75rem; letter-spacing: .01em; }
.hero-title { font-size: clamp(2rem, 2.4vw + .55rem, 2.65rem); font-weight: 800; line-height: 1.14; margin: 0 0 .85rem; padding: 0; color: var(--text); letter-spacing: -0.02em; }
[data-testid="stHeaderActionElements"] { display: none; }
.grad { background: linear-gradient(90deg, #C06CFF, #8B5CFF); -webkit-background-clip: text; background-clip: text; color: transparent; }
[data-testid="stHorizontalBlock"]:has(.hero) { align-items: center; margin-bottom: .35rem; }
.hero p.lead { color: var(--muted); font-size: 1.02rem; line-height: 1.55; max-width: 560px; margin-bottom: 1.25rem; }
.cta-row { display: flex; gap: .75rem; flex-wrap: wrap; align-items: center; }
.cta { display: inline-flex; gap: .5rem; align-items: center; padding: .62rem 1.2rem; border-radius: 10px;
  font-weight: 600; font-size: .92rem; text-decoration: none !important; transition: transform .15s, box-shadow .15s; white-space: nowrap; }
.cta:hover { transform: translateY(-1px); }
.cta-primary { background: linear-gradient(90deg, #7C3AED, #B44CFF); color: #fff !important;
  box-shadow: 0 6px 24px rgba(124,58,237,.45), inset 0 1px 0 rgba(255,255,255,.25); border: 1px solid rgba(216,180,254,.35); }
.cta-ghost { border: 1px solid var(--line2); color: var(--text) !important; background: rgba(23,30,64,.65); }
.hero-art { position: relative; height: 265px; width: 100%; max-width: 590px; margin: 0 auto; }
.hero-art svg.shield-art { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: 100%; height: 100%; pointer-events: none; }
.feat { position: absolute; display: inline-flex; gap: .48rem; align-items: center; padding: .38rem .78rem .38rem .45rem; border-radius: 999px;
  background: rgba(17,23,51,.92); border: 1px solid rgba(160,130,255,.34); color: var(--text); font-size: .78rem; font-weight: 500;
  white-space: nowrap; box-shadow: 0 6px 18px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.06); z-index: 2; }
.feat-ic { width: 22px; height: 22px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
  line-height: 0; background: rgba(140,92,255,.18); border: 1px solid rgba(180,120,255,.32); color: #D8B4FE; flex-shrink: 0; }

/* ---------- cards ---------- */
.kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .9rem; align-items: stretch; margin: 1.15rem 0 1.2rem; }
.kpi { background: linear-gradient(180deg, rgba(23,30,64,.72), rgba(17,23,51,.92)); border: 1px solid var(--line);
  border-radius: var(--radius); padding: 1.05rem 1.15rem; display: flex; gap: .9rem; align-items: center;
  height: 100%; box-sizing: border-box;
  box-shadow: 0 8px 24px -12px rgba(0,0,0,.5), inset 0 1px 0 rgba(255,255,255,.04); }
.kpi-icon { width: 46px; height: 46px; border-radius: 12px; display: inline-flex; align-items: center; justify-content: center;
  line-height: 0; flex-shrink: 0; }
.kpi-num { font-size: 1.7rem; font-weight: 800; color: var(--text); line-height: 1.05; letter-spacing: -0.02em; }
.kpi-label { color: var(--text); font-size: .84rem; font-weight: 600; margin-top: .18rem; }
.kpi-note { font-size: .73rem; color: #8690B5; margin-top: .16rem; line-height: 1.3; }
.trend { display: inline-block; font-size: .72rem; font-weight: 600; padding: .05rem .4rem; border-radius: 6px; margin-left: .35rem;
  background: rgba(22,199,132,.14); color: var(--ok); vertical-align: middle; }
.panel-head { display: flex; justify-content: space-between; align-items: center; gap: .8rem; margin-bottom: .55rem; flex-wrap: wrap; }
.panel-title { display: flex; gap: .6rem; align-items: center; font-size: 1.1rem; font-weight: 700; color: var(--text); line-height: 1.25; }
.panel-sub { color: var(--muted); font-size: .83rem; margin-top: .18rem; font-weight: 400; }
.panel-right { display: flex; gap: .6rem; align-items: center; margin-left: auto; flex-shrink: 0; }
.play-badge { width: 34px; height: 34px; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center;
  line-height: 0; flex-shrink: 0;
  background: linear-gradient(135deg, #7C3AED, #B44CFF); box-shadow: 0 4px 14px rgba(124,58,237,.4); }
.sec-badge { width: 30px; height: 30px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center;
  line-height: 0; flex-shrink: 0;
  background: rgba(140,92,255,.15); border: 1px solid rgba(180,120,255,.28); }
.ready-pill { display: inline-flex; gap: .4rem; align-items: center; padding: .24rem .68rem; border-radius: 999px;
  background: rgba(22,199,132,.12); border: 1px solid rgba(22,199,132,.35); color: #2EE59D; font-size: .75rem; font-weight: 600; white-space: nowrap; }
.ready-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 8px var(--ok); flex-shrink: 0; }

/* Streamlit bordered containers become our cards */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) { border-radius: var(--radius); }
.st-key-card_run, .st-key-card_how, .st-key-card_pipe, .st-key-card_recent, .st-key-card_dec {
  background: linear-gradient(180deg, rgba(21,28,62,.78), rgba(15,20,46,.94));
  border: 1px solid var(--line); border-radius: var(--radius); padding: 1.15rem 1.25rem;
  box-sizing: border-box;
  box-shadow: 0 10px 28px -14px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.04); }
.st-key-card_run { border-color: var(--line2); }

/* agent mode cards (radio) */
.st-key-agent_mode, .st-key-agent_mode [data-testid="stRadio"], .st-key-agent_mode [data-testid="stRadioGroup"] { width: 100% !important; }
.st-key-mode [role="radiogroup"] { display: grid !important; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .65rem; align-items: stretch; width: 100%; }
.st-key-mode [role="radiogroup"] > div { margin: 0; padding: .8rem .85rem; border-radius: 12px; background: rgba(23,30,64,.75);
  border: 1px solid var(--line); transition: border-color .15s, box-shadow .15s, background .15s; min-height: 92px; cursor: pointer; position: relative; box-sizing: border-box; }
.st-key-mode [role="radiogroup"] > div:hover { border-color: var(--line2); }
/* the whole card is clickable: the option's label is stretched over the card */
.st-key-mode [data-testid="stRadioOption"] { position: static; }
.st-key-mode [data-testid="stRadioOption"]::after { content: ""; position: absolute; inset: 0; border-radius: inherit; z-index: 1; cursor: pointer; }
.st-key-mode [role="radiogroup"] > div[data-selected="true"] {
  border-color: #A855F7;
  box-shadow: 0 0 0 1px rgba(168,85,247,.6), 0 6px 22px rgba(113,56,255,.32);
  background: linear-gradient(160deg, rgba(124,58,237,.22), rgba(180,76,255,.10));
}
.st-key-mode [role="radiogroup"] > div[data-selected="true"]::before {
  content: "✓";
  position: absolute;
  top: .6rem;
  right: .6rem;
  width: 19px;
  height: 19px;
  border-radius: 50%;
  background: linear-gradient(135deg, #9333EA, #C084FC);
  color: #fff;
  font-size: .68rem;
  font-weight: 800;
  display: grid;
  place-items: center;
  box-shadow: 0 2px 8px rgba(147,51,234,.5);
}
.st-key-mode [data-testid="stRadioOption"] > div > div:first-child { display: none; }
.st-key-mode [data-testid="stRadioOption"] p { font-weight: 600; font-size: .88rem; color: var(--text); padding-right: 1.2rem; }
.st-key-mode [data-testid="stRadioOption"] p span[role="img"] { color: #C9B6FF; margin-right: .25rem; }
.st-key-mode [data-testid="stRadioCaption"] { color: var(--muted); font-size: .76rem; padding-left: 0; margin-top: .22rem; line-height: 1.35; }

/* primary button = refined purple gradient */
.stButton > button[data-testid="stBaseButton-primary"] {
  background: linear-gradient(90deg, #6D28D9 0%, #9333EA 50%, #C026D3 100%);
  border: 1px solid rgba(216,180,254,.38); border-radius: 10px;
  padding: .68rem 1rem; font-weight: 700; font-size: .96rem;
  box-shadow: 0 6px 24px rgba(147,51,234,.4), inset 0 1px 0 rgba(255,255,255,.22);
}
.stButton > button[data-testid="stBaseButton-primary"]:hover { filter: brightness(1.08); }

/* how it works */
.flow { display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr) auto minmax(0, 1fr); gap: .45rem; align-items: stretch; margin-top: .35rem; }
.flow .arrow { align-self: center; color: #8E96B8; }
.node { border-radius: 12px; padding: .8rem .55rem; text-align: center; border: 1px solid var(--line); background: var(--card2);
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: .14rem; height: 100%; box-sizing: border-box; }
.node-ic { width: 36px; height: 36px; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center;
  line-height: 0; margin-bottom: .2rem; flex-shrink: 0; }
.node b { display: block; color: var(--text); font-size: .88rem; margin-top: .1rem; }
.node-sub { color: var(--muted); font-size: .74rem; display: block; }
.node-user { background: linear-gradient(180deg, rgba(240,68,82,.12), rgba(240,68,82,.05)); border-color: rgba(240,68,82,.38); }
.node-user .node-ic { background: rgba(240,68,82,.16); border: 1px solid rgba(240,68,82,.32); }
.node-shield { background: linear-gradient(180deg, rgba(124,58,237,.24), rgba(113,56,255,.12)); border-color: rgba(180,76,255,.65); box-shadow: 0 0 24px rgba(113,56,255,.28); }
.node-shield .node-ic { background: rgba(180,76,255,.22); border: 1px solid rgba(216,180,254,.4); }
.node-dec { background: linear-gradient(180deg, rgba(22,199,132,.12), rgba(22,199,132,.05)); border-color: rgba(22,199,132,.38); }
.node-dec .node-ic { background: rgba(22,199,132,.16); border: 1px solid rgba(22,199,132,.32); }
.decs { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .6rem; align-items: stretch; margin-top: .45rem; }
.dec { border-radius: 12px; padding: .75rem .85rem; display: flex; flex-direction: column; gap: .38rem; align-items: flex-start; height: 100%; box-sizing: border-box; }
.dec-head { display: flex; gap: .45rem; align-items: center; }
.dec b { color: var(--text); font-size: .9rem; letter-spacing: .02em; }
.dec span { color: var(--muted); font-size: .75rem; line-height: 1.35; }
.dec-allow { background: linear-gradient(180deg, rgba(22,199,132,.13), rgba(22,199,132,.05)); border: 1px solid rgba(22,199,132,.36); }
.dec-ask { background: linear-gradient(180deg, rgba(245,166,35,.13), rgba(245,166,35,.05)); border: 1px solid rgba(245,166,35,.36); }
.dec-block { background: linear-gradient(180deg, rgba(240,68,82,.13), rgba(240,68,82,.05)); border: 1px solid rgba(240,68,82,.36); }

/* pipeline */
.pipe { display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr) auto minmax(0, 1fr) auto minmax(0, 1fr); gap: .5rem; align-items: stretch; margin-top: .35rem; }
.pnode { background: rgba(23,30,64,.82); border: 1px solid var(--line2); border-radius: 12px; padding: .9rem 1rem;
  display: flex; gap: .75rem; align-items: center; height: 100%; box-sizing: border-box; }
.pnode-ic { width: 36px; height: 36px; border-radius: 9px; display: inline-flex; align-items: center; justify-content: center;
  flex-shrink: 0; line-height: 0; background: rgba(140,92,255,.14); border: 1px solid rgba(180,120,255,.25); color: #C9B6FF; }
.pnode-num { display: inline-flex; align-items: center; justify-content: center; min-width: 28px; height: 22px; padding: 0 .42rem;
  border-radius: 6px; background: linear-gradient(135deg, #7C3AED, #9333EA); color: #fff !important; font-size: .72rem;
  font-weight: 800; line-height: 1; letter-spacing: .03em; flex-shrink: 0; box-shadow: 0 2px 8px rgba(124,58,237,.4); }
.pnode-body { display: flex; flex-direction: column; justify-content: center; min-width: 0; }
.pnode-body b { color: var(--text); font-size: .88rem; display: block; line-height: 1.25; }
.pnode-sub { color: var(--muted); font-size: .74rem; display: block; margin-top: .16rem; line-height: 1.3; }
.pipe .arrow { color: #8E96B8; align-self: center; }

/* recent evaluations */
.search-pill { display: inline-flex; gap: .45rem; align-items: center; padding: .34rem .75rem; border-radius: 8px;
  background: rgba(11,16,38,.75); border: 1px solid var(--line); color: #7E88B0; font-size: .78rem; min-width: 210px; white-space: nowrap; }
.audit-btn { display: inline-flex; gap: .35rem; align-items: center; padding: .36rem .8rem; border-radius: 8px;
  background: rgba(124,58,237,.18); border: 1px solid rgba(180,120,255,.38); color: #E2D4FF !important;
  text-decoration: none !important; font-size: .78rem; font-weight: 600; transition: background .15s, border-color .15s; white-space: nowrap; }
.audit-btn:hover { background: rgba(124,58,237,.3); border-color: rgba(216,180,254,.6); }
.rwrap { width: 100%; overflow-x: auto; }
.rtable { width: 100%; border-collapse: collapse; font-size: .83rem; }
.rtable th { text-align: left; color: #8690B5; font-weight: 500; font-size: .78rem; padding: .5rem .55rem; border-bottom: 1px solid var(--line); white-space: nowrap; }
.rtable th:last-child, .rtable td:last-child { text-align: right; width: 42px; }
.rtable td { color: var(--text); font-weight: 400; padding: .62rem .55rem; border-bottom: 1px solid rgba(140,120,255,.08); vertical-align: middle; }
.rtable td.muted:first-child, .rtable th:first-child { white-space: nowrap; }
.rtable td.muted { color: var(--muted); }
.tool-pill { display: inline-block; padding: .16rem .55rem; border-radius: 6px; font-family: ui-monospace, Consolas, monospace;
  font-size: .76rem; font-weight: 600; white-space: nowrap; }
.tool-allow { background: rgba(22,199,132,.12); border: 1px solid rgba(22,199,132,.3); color: #2EE59D; }
.tool-ask_human { background: rgba(245,166,35,.12); border: 1px solid rgba(245,166,35,.3); color: #FBBF24; }
.tool-block { background: rgba(240,68,82,.14); border: 1px solid rgba(240,68,82,.32); color: #FF7A85; }
.row-link { display: inline-flex; align-items: center; justify-content: center; line-height: 0; width: 26px; height: 26px; border-radius: 6px;
  background: rgba(140,120,255,.1); border: 1px solid var(--line); color: #B8C0E0 !important; text-decoration: none !important;
  transition: background .15s, border-color .15s, color .15s; }
.row-link:hover { background: rgba(124,58,237,.25); border-color: rgba(180,120,255,.5); color: #fff !important; }
.link { color: #C9B6FF !important; text-decoration: none !important; font-size: .85rem; font-weight: 500; }
.badge { display: inline-block; padding: .16rem .58rem; border-radius: 6px; font-size: .71rem; font-weight: 700; letter-spacing: .03em; white-space: nowrap; }
.b-allow { background: rgba(22,199,132,.16); border: 1px solid rgba(22,199,132,.32); color: var(--ok); }
.b-ask { background: rgba(245,166,35,.16); border: 1px solid rgba(245,166,35,.32); color: var(--warn); }
.b-block { background: rgba(240,68,82,.18); border: 1px solid rgba(240,68,82,.35); color: #FF6B78; }
.empty { color: var(--muted); font-size: .88rem; padding: .8rem 0; }

/* results */
.summary { border-radius: var(--radius); padding: 1rem 1.3rem; margin: 1rem 0; font-size: 1.15rem; font-weight: 700; color: #fff;
  background: linear-gradient(90deg, rgba(22,199,132,.85), rgba(15,118,110,.85)); border: 1px solid rgba(22,199,132,.6); }
.summary-neutral { background: linear-gradient(90deg, rgba(91,140,255,.55), rgba(113,56,255,.45)); border-color: rgba(140,160,255,.6); }
.col-head { border-radius: 12px; padding: .7rem 1rem; margin-bottom: .8rem; font-weight: 700; font-size: 1.05rem; display: flex; gap: .5rem; align-items: center; }
.col-unsafe { background: rgba(240,68,82,.12); color: #FF8A94; border: 1px solid rgba(240,68,82,.4); }
.col-safe { background: rgba(22,199,132,.12); color: #4BE0A8; border: 1px solid rgba(22,199,132,.4); }
.money { font-size: 2.1rem; font-weight: 800; line-height: 1.1; color: var(--text); }
.money-lost { color: #FF6B78; } .money-ok { color: var(--ok); }
.money-label { color: var(--muted); font-size: .8rem; }
.user-quote { border-left: 3px solid var(--accent); background: var(--card2); padding: .55rem .85rem; border-radius: 0 10px 10px 0; margin: .6rem 0; color: var(--text); }
.reason-bn { font-size: 1rem; margin: .3rem 0; color: var(--text); }
.args { background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: .7rem .9rem; margin: .2rem 0 .6rem;
  color: #C9B6FF; font-family: ui-monospace, Consolas, monospace; font-size: .86rem; white-space: pre-wrap; word-break: break-word; }
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

/* st.metric (Audit Log) styled like the KPI cards */
[data-testid="stMetric"] { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: .9rem 1.1rem;
  transition: border-color .28s, transform .28s; }
[data-testid="stMetric"]:hover { border-color: var(--line2); transform: translateY(-2px); }
[data-testid="stMetricLabel"] p { color: var(--muted); font-size: .85rem; }
[data-testid="stMetricValue"] { font-weight: 800; font-size: 1.8rem; color: var(--text); }

/* inline code (tool names in step labels) readable everywhere */
[data-testid="stExpander"] summary code, [data-testid="stMarkdownContainer"] p code { font-size: .82rem !important; }

/* equal-height cards in a row */
[data-testid="stHorizontalBlock"]:has(.st-key-card_run) { align-items: stretch !important; }
[data-testid="stHorizontalBlock"]:has(.st-key-card_run) > [data-testid="stColumn"] { display: flex; flex-direction: column; }
[data-testid="stHorizontalBlock"]:has(.st-key-card_run) > [data-testid="stColumn"] > div,
[data-testid="stHorizontalBlock"]:has(.st-key-card_run) > [data-testid="stColumn"] [data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(.st-key-card_run) > [data-testid="stColumn"] [data-testid="stLayoutWrapper"] {
  flex: 1 1 auto; display: flex; flex-direction: column; height: 100%;
}
.st-key-card_run, .st-key-card_how { flex: 1 1 auto; height: 100%; box-sizing: border-box; }
.st-key-card_pipe { margin-top: .25rem; margin-bottom: .25rem; }
.st-key-card_pipe, .st-key-card_recent { padding-bottom: 1.35rem !important; }

/* ---------- motion: slow, purposeful, never decorative noise ---------- */
:root { --ease: cubic-bezier(.22, .61, .36, 1); }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
@keyframes breathe { 0%, 100% { opacity: .75; } 50% { opacity: 1; } }
@keyframes orbit { to { stroke-dashoffset: -1000; } }
@keyframes rise { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
@keyframes sheen { from { transform: translateX(-120%) skewX(-18deg); } to { transform: translateX(260%) skewX(-18deg); } }
@keyframes scan { 0%, 12%, 100% { opacity: 0; } 4% { opacity: 1; } }
@keyframes halo { 0%, 100% { opacity: .35; } 50% { opacity: 1; } }

/* hero headline: each line comes into focus once; a slow light crosses the key words */
@keyframes focus-in { from { opacity: 0; filter: blur(10px); transform: translateY(14px); } to { opacity: 1; filter: blur(0); transform: none; } }
@keyframes light-pass { 0% { background-position: 100% 50%; } 55%, 100% { background-position: 0% 50%; } }
.hero-title .l1 { display: block; animation: focus-in .9s var(--ease) backwards; }
.hero-title .grad.l2 {
  display: inline-block;
  background-image: linear-gradient(90deg, #C06CFF 0%, #8B5CFF 33.33%, #8B5CFF 44%, #F3E8FF 50%,
                                    #C06CFF 56%, #C06CFF 66.67%, #8B5CFF 100%);
  background-size: 300% 100%; background-position: 100% 50%;
  animation: focus-in .9s .16s var(--ease) backwards, light-pass 8s 1.6s var(--ease) infinite; }
.hero p.lead { animation: rise .7s .38s var(--ease) backwards; }
.hero .cta-row { animation: rise .7s .5s var(--ease) backwards; }

/* hero: the shield floats, a light streak orbits its ring, the aura breathes */
.shield-art .shield-body { animation: float 6s var(--ease) infinite; transform-box: fill-box; transform-origin: center; will-change: transform; }
.shield-art .orbit { stroke-dashoffset: 0; animation: orbit 9s linear infinite; opacity: .9; }
.shield-art .aura, .shield-art .pad-glow { animation: breathe 6s var(--ease) infinite; }
.feat { animation: rise .6s var(--ease) backwards; transition: border-color .25s var(--ease), transform .25s var(--ease), background .25s; }
.feat:nth-of-type(1) { animation-delay: .05s; } .feat:nth-of-type(2) { animation-delay: .12s; } .feat:nth-of-type(3) { animation-delay: .19s; }
.feat:nth-of-type(4) { animation-delay: .26s; } .feat:nth-of-type(5) { animation-delay: .33s; } .feat:nth-of-type(6) { animation-delay: .40s; }
.feat:hover { border-color: rgba(180,76,255,.75); background: rgba(34,26,80,.95); transform: translateY(-1px); }

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
.node-shield { position: relative; }
.node-shield::after { content: ""; position: absolute; inset: -1px; border-radius: inherit; pointer-events: none;
  box-shadow: 0 0 0 1px rgba(180,76,255,.55), 0 0 28px rgba(113,56,255,.45); animation: halo 4s var(--ease) infinite; will-change: opacity; }

/* pipeline: each check lights up in turn, like a tool call passing through */
.pipe .pnode { position: relative; }
.pipe .pnode::after { content: ""; position: absolute; inset: -1px; border-radius: inherit; pointer-events: none; opacity: 0;
  border: 1px solid rgba(180,76,255,.85); box-shadow: 0 0 22px rgba(113,56,255,.35); animation: scan 6s var(--ease) infinite; will-change: opacity; }
.pipe .pnode:nth-child(1)::after { animation-delay: 0s; } .pipe .pnode:nth-child(3)::after { animation-delay: .7s; }
.pipe .pnode:nth-child(5)::after { animation-delay: 1.4s; } .pipe .pnode:nth-child(7)::after { animation-delay: 2.1s; }
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
.cta-ghost:hover { border-color: rgba(180,76,255,.6); background: rgba(113,56,255,.12); }

/* sidebar nav */
.st-key-nav [role="radiogroup"] > div { transition: background .2s var(--ease), border-color .2s var(--ease), transform .2s var(--ease); }
.st-key-nav [role="radiogroup"] > div:not([data-selected="true"]):hover { transform: translateX(2px); }
.dot, .ready-dot { animation: breathe 2.4s var(--ease) infinite; }

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
  .hero-art svg.shield-art { position: static; transform: none; width: 220px; height: 190px; flex: 0 0 100%; }
  .hero-art svg.shield-art .connectors { display: none; }
  .rwrap { overflow-x: auto; }
  .rtable .c-req, .rtable .c-tool { display: none; }
  .search-pill { display: none; }
  .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; gap: .6rem; margin: 1.2rem 0 1rem; }
  .kpi { flex-direction: column; align-items: flex-start; gap: .55rem; padding: .9rem; }
  .kpi-icon { width: 38px; height: 38px; }
  .kpi-num { font-size: 1.45rem; }
  .kpi-label { font-size: .8rem; }
  .st-key-mode [role="radiogroup"] > div { min-height: 0; }
  [data-testid="stHorizontalBlock"]:has(.money):not(:has(.col-head)) { flex-wrap: nowrap !important; flex-direction: row !important; gap: .8rem; }
  [data-testid="stHorizontalBlock"]:has(.money):not(:has(.col-head)) > [data-testid="stColumn"] { flex: 1 1 0 !important; min-width: 0 !important; width: auto !important; }
  .money { font-size: 1.6rem; }
  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) { flex-wrap: wrap !important; flex-direction: row !important; gap: .6rem; }
  [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="stColumn"] {
    flex: 1 1 calc(50% - .6rem) !important; min-width: calc(50% - .6rem) !important; width: auto !important; }
  [data-testid="stMetricValue"] { font-size: 1.4rem; }
}

/* ---------- Audit Log Premium Console (scoped) ---------- */
.audit-header { display: flex; align-items: center; gap: .9rem; margin: 0 0 .85rem 0; padding: .1rem 0; }
.audit-header-icon {
  width: 46px; height: 46px; border-radius: 12px;
  display: inline-flex !important; align-items: center; justify-content: center; flex-shrink: 0; line-height: 0;
  background: linear-gradient(135deg, rgba(145, 71, 255, .32), rgba(192, 68, 255, .16));
  border: 1px solid rgba(192, 68, 255, .52);
  box-shadow: 0 0 24px rgba(145, 71, 255, .35), inset 0 1px 0 rgba(255, 255, 255, .15);
}
.audit-header-icon .ic { display: block; margin: auto; }
.audit-header-text { display: flex; flex-direction: column; justify-content: center; gap: .18rem; min-width: 0; flex: 1; }
.audit-h1 {
  font-size: 1.7rem !important; font-weight: 800 !important; color: #F5F6FF !important;
  line-height: 1.1 !important; letter-spacing: -0.02em; margin: 0 !important; padding: 0 !important;
}
.audit-sub { font-size: .84rem; color: #A8B3D3; margin: 0 !important; padding: 0 !important; line-height: 1.3; }
[data-testid="stHorizontalBlock"]:has(.audit-header) {
  align-items: center !important;
  margin-bottom: .85rem !important;
}
[data-testid="stHorizontalBlock"]:has(.audit-header) [data-testid="stElementContainer"],
[data-testid="stHorizontalBlock"]:has(.audit-header) .stButton,
[data-testid="stHorizontalBlock"]:has(.audit-header) .stDownloadButton,
[data-testid="stHorizontalBlock"]:has(.audit-header) [data-testid="stPopover"],
[data-testid="stHorizontalBlock"]:has(.audit-header) .stSelectbox {
  margin-bottom: 0 !important;
}
@media (min-width: 1260px) {
  .audit-sub { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
}

/* 5 KPI Cards on Audit Log */
.audit-kpis { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: .85rem; align-items: stretch; margin: .85rem 0 .45rem; }
.audit-kpi {
  background: linear-gradient(180deg, #1B2345 0%, #151D3B 100%);
  border: 1px solid #29345F; border-radius: 14px; padding: .95rem 1.05rem;
  display: flex; gap: .85rem; align-items: center; position: relative; overflow: hidden;
  height: 100%; box-sizing: border-box;
  box-shadow: 0 10px 26px -14px rgba(0, 0, 0, .6), inset 0 1px 0 rgba(255, 255, 255, .05);
  transition: transform .22s var(--ease), border-color .22s var(--ease);
}
.audit-kpi:hover { transform: translateY(-2px); border-color: rgba(145, 71, 255, .55); }
.audit-kpi-ring {
  width: 44px; height: 44px; border-radius: 50%; flex-shrink: 0;
  display: inline-flex; align-items: center; justify-content: center; line-height: 0;
}
.audit-kpi-ring .ic { display: block; margin: auto; }
.audit-kpi-body { min-width: 0; flex: 1; }
.audit-kpi-label { font-size: .78rem; font-weight: 500; color: #A8B3D3; line-height: 1.2; }
.audit-kpi-val { font-size: 1.65rem; font-weight: 800; color: #F5F6FF; line-height: 1.15; letter-spacing: -0.02em; margin-top: .12rem; }
.audit-kpi-meta { display: flex; align-items: center; justify-content: space-between; gap: .4rem; margin-top: .28rem; font-size: .72rem; font-weight: 600; }
.audit-llm-line {
  display: inline-flex; align-items: center; gap: .45rem; font-size: .78rem; color: #A8B3D3;
  margin: .15rem 0 .75rem; padding: .22rem .65rem; border-radius: 8px;
  background: rgba(21, 29, 59, .65); border: 1px solid rgba(41, 52, 95, .75);
}

/* Unified Filter & Search Toolbar (Audit Log + Policies) */
.st-key-audit_toolbar { margin: .2rem 0 .65rem; }
.st-key-audit_toolbar [data-testid="stHorizontalBlock"],
.st-key-policy_toolbar [data-testid="stHorizontalBlock"],
.st-key-audit_pager_bar [data-testid="stHorizontalBlock"],
.st-key-ds_files_card [data-testid="stHorizontalBlock"] {
  align-items: center !important;
}
.st-key-audit_toolbar [data-testid="stElementContainer"],
.st-key-policy_toolbar [data-testid="stElementContainer"],
.st-key-audit_pager_bar [data-testid="stElementContainer"],
.st-key-ds_files_card > [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] [data-testid="stElementContainer"],
.st-key-audit_toolbar .stRadio,
.st-key-policy_toolbar .stRadio,
.st-key-audit_toolbar .stTextInput,
.st-key-policy_toolbar .stTextInput,
.st-key-ds_files_card .stTextInput,
.st-key-ds_files_card .stSelectbox,
.st-key-audit_toolbar .stButton,
.st-key-policy_toolbar .stButton,
.st-key-audit_toolbar [data-testid="stPopover"],
.st-key-policy_toolbar [data-testid="stPopover"] {
  margin-bottom: 0 !important;
}
.st-key-audit_toolbar [data-testid="stTextInputRootElement"],
.st-key-policy_toolbar [data-testid="stTextInputRootElement"],
.st-key-ds_files_card [data-testid="stTextInputRootElement"] {
  min-height: 40px !important;
  height: 40px !important;
  border-radius: 10px !important;
  background: rgba(13, 18, 40, .82) !important;
  border: 1px solid #29345F !important;
}
.st-key-audit_toolbar [data-testid="stPopover"] button,
.st-key-audit_toolbar .stButton > button,
.st-key-policy_toolbar [data-testid="stPopover"] button,
.st-key-policy_toolbar .stButton > button {
  min-height: 40px !important;
  height: 40px !important;
  border-radius: 10px !important;
  margin: 0 !important;
  white-space: nowrap !important;
}
.st-key-audit_decision_wrap [role="radiogroup"] {
  display: inline-flex !important; flex-direction: row !important; flex-wrap: wrap; gap: .4rem;
  background: rgba(13, 18, 40, .82); border: 1px solid #29345F; border-radius: 11px; padding: .24rem;
  min-height: 40px; align-items: center; box-sizing: border-box;
}
.st-key-audit_decision_wrap [role="radiogroup"] > div,
.st-key-audit_decision_wrap [role="radiogroup"] > label {
  border-radius: 8px !important; border: 1px solid transparent; padding: 0 !important; margin: 0 !important;
  transition: background .15s, border-color .15s, box-shadow .15s; position: relative;
}
.st-key-audit_decision_wrap [data-testid="stRadioOption"] { padding: .34rem .78rem !important; cursor: pointer; position: static; }
.st-key-audit_decision_wrap [data-testid="stRadioOption"] > div > div:first-child { display: none; }
.st-key-audit_decision_wrap [data-testid="stRadioOption"]::after {
  content: ""; position: absolute; inset: 0; border-radius: inherit; z-index: 1; cursor: pointer;
}
.st-key-audit_decision_wrap [data-testid="stRadioOption"] p { font-size: .82rem !important; font-weight: 600 !important; color: #A8B3D3; white-space: nowrap; margin: 0 !important; }
.st-key-audit_decision_wrap [role="radiogroup"] > div[data-selected="true"],
.st-key-audit_decision_wrap [role="radiogroup"] > label:has(input:checked) {
  background: linear-gradient(90deg, #9147FF, #C044FF) !important;
  border-color: rgba(233, 213, 255, .55) !important;
  box-shadow: 0 3px 16px rgba(145, 71, 255, .45);
}
.st-key-audit_decision_wrap [role="radiogroup"] > div[data-selected="true"] [data-testid="stRadioOption"] p,
.st-key-audit_decision_wrap [role="radiogroup"] > label:has(input:checked) p { color: #FFFFFF !important; }

/* Audit Table + Drawer Horizontal Alignment */
[data-testid="stHorizontalBlock"]:has(.audit-table-card) {
  align-items: flex-start !important;
}
.st-key-audit_pager_bar { margin-top: .5rem; }

/* Audit Table Card */
.audit-table-card {
  background: linear-gradient(180deg, rgba(21, 29, 59, .92) 0%, rgba(14, 19, 42, .96) 100%);
  border: 1px solid #29345F; border-radius: 14px; overflow: hidden; box-sizing: border-box;
  box-shadow: 0 12px 32px -14px rgba(0, 0, 0, .65), inset 0 1px 0 rgba(255, 255, 255, .04);
}
.audit-table-wrap { width: 100%; overflow-x: auto; }
.atable { width: 100%; border-collapse: separate; border-spacing: 0 3px; padding: .35rem .55rem; font-size: .83rem; }
.atable thead th {
  text-align: left; color: #A8B3D3; font-weight: 600; font-size: .76rem; letter-spacing: .01em;
  padding: .65rem .7rem; border-bottom: 1px solid #29345F; white-space: nowrap;
}
.atable thead th.col-chk { width: 38px; text-align: center; }
.atable thead th.col-more { width: 42px; text-align: right; }
.atable tbody tr.arow td {
  padding: .66rem .7rem; color: #F5F6FF; vertical-align: middle;
  background: rgba(21, 29, 59, .45);
  border-top: 1px solid transparent; border-bottom: 1px solid rgba(41, 52, 95, .48);
  transition: background .15s, border-color .15s;
}
.atable tbody tr.arow td:first-child { border-left: 1px solid transparent; border-radius: 10px 0 0 10px; text-align: center; }
.atable tbody tr.arow td:last-child { border-right: 1px solid transparent; border-radius: 0 10px 10px 0; text-align: right; }
.atable tbody tr.arow:hover td { background: rgba(145, 71, 255, .09); }
.asel-radio { position: absolute; opacity: 0; width: 0; height: 0; pointer-events: none; margin: 0; }
.arow-link {
  cursor: pointer; color: inherit !important; text-decoration: none !important;
  display: flex; align-items: center; gap: .5rem; width: 100%; user-select: none;
}
.achk {
  width: 18px; height: 18px; border-radius: 5px; border: 1.5px solid #3E4C80;
  display: inline-flex; align-items: center; justify-content: center; line-height: 0;
  background: rgba(11, 15, 34, .65); color: transparent; margin: 0 auto;
  transition: background .12s, border-color .12s, color .12s, box-shadow .12s;
}
.achk .ic { display: block; margin: auto; }
.atool-ic {
  width: 24px; height: 24px; border-radius: 6px;
  display: inline-flex; align-items: center; justify-content: center; line-height: 0; flex-shrink: 0;
  background: rgba(145, 71, 255, .16); border: 1px solid rgba(145, 71, 255, .36); color: #C9A6FF;
}
.atool-ic .ic { display: block; margin: auto; }
.atool-name { font-weight: 500; color: #F5F6FF; white-space: nowrap; }
.atime { color: #A8B3D3; font-variant-numeric: tabular-nums; white-space: nowrap; }
.aargs {
  font-family: ui-monospace, "Cascadia Code", Consolas, monospace; font-size: .79rem;
  color: #D5DCF6; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: clamp(140px, 20vw, 270px);
}
.amore {
  cursor: pointer; display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px;
  border-radius: 6px; color: #A8B3D3 !important; text-decoration: none !important; line-height: 0;
}
.amore:hover { background: rgba(145, 71, 255, .2); color: #F5F6FF !important; }
.abadge {
  display: inline-flex; align-items: center; justify-content: center;
  padding: .18rem .62rem; border-radius: 6px; font-size: .7rem; font-weight: 700; letter-spacing: .04em;
  white-space: nowrap;
}
.abadge-allow { background: rgba(0, 214, 160, .15); border: 1px solid rgba(0, 214, 160, .38); color: #00D6A0; }
.abadge-ask_human { background: rgba(255, 181, 71, .16); border: 1px solid rgba(255, 181, 71, .42); color: #FFB547; }
.abadge-block { background: rgba(255, 82, 111, .16); border: 1px solid rgba(255, 82, 111, .42); color: #FF526F; }
.arisk { font-variant-numeric: tabular-nums; font-weight: 600; font-size: .82rem; white-space: nowrap; }
.arisk-low { color: #F5F6FF; }
.arisk-med { color: #FFB547; }
.arisk-high { color: #FF526F; }
.audit-foot {
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: .75rem;
  padding: .75rem 1rem; border-top: 1px solid #29345F; background: rgba(13, 18, 40, .65);
  font-size: .79rem; color: #A8B3D3;
}
.apager { display: inline-flex; align-items: center; gap: .3rem; }
.apage-btn {
  display: inline-flex; align-items: center; justify-content: center; min-width: 28px; height: 28px;
  padding: 0 .45rem; border-radius: 7px; font-size: .78rem; font-weight: 600;
  color: #A8B3D3 !important; text-decoration: none !important; border: 1px solid transparent;
  transition: background .15s, color .15s;
}
.apage-btn:hover { background: rgba(145, 71, 255, .18); color: #F5F6FF !important; }
.apage-btn.apage-active {
  background: linear-gradient(135deg, #9147FF, #C044FF); color: #FFFFFF !important;
  border-color: rgba(233, 213, 255, .5); box-shadow: 0 2px 10px rgba(145, 71, 255, .45);
}
.apage-dots { color: #6E789E; padding: 0 .25rem; }

/* Right-Side Audit Details Drawer */
.st-key-audit_drawer_card {
  background: linear-gradient(180deg, #1B2345 0%, #151D3B 100%);
  border: 1px solid #29345F; border-radius: 14px; padding: 1.05rem 1.15rem; box-sizing: border-box;
  box-shadow: 0 14px 36px -12px rgba(0, 0, 0, .7), inset 0 1px 0 rgba(255, 255, 255, .05);
}
.st-key-audit_drawer_card [data-testid="stHorizontalBlock"] {
  align-items: center !important;
  margin-top: .3rem;
}
.st-key-audit_drawer_card .stButton > button {
  min-height: 36px !important;
  padding: .35rem .55rem !important;
  font-size: .78rem !important;
  white-space: nowrap !important;
  border-radius: 9px !important;
}
.adrawer-head {
  display: flex; justify-content: space-between; align-items: center;
  padding-bottom: .75rem; margin-bottom: .8rem; border-bottom: 1px solid #29345F;
}
.adrawer-title { display: inline-flex; align-items: center; gap: .5rem; font-size: 1.02rem; font-weight: 700; color: #F5F6FF; line-height: 1; }
.adrawer-title .ic { display: block; flex-shrink: 0; }
.adrawer-close {
  cursor: pointer; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px;
  border-radius: 7px; color: #A8B3D3 !important; text-decoration: none !important;
  border: 1px solid transparent; transition: background .15s, color .15s; line-height: 0;
}
.adrawer-close .ic { display: block; margin: auto; }
.adrawer-close:hover { background: rgba(255, 82, 111, .16); border-color: rgba(255, 82, 111, .35); color: #FF526F !important; }
.adrawer-pane { display: none; animation: adrawer-fade .14s ease-out; }
@keyframes adrawer-fade {
  from { opacity: .72; transform: translateY(2px); }
  to { opacity: 1; transform: none; }
}
[data-testid="stHorizontalBlock"]:has(#adrawer-close-chk:checked) > [data-testid="stColumn"]:last-child {
  display: none !important;
}
[data-testid="stHorizontalBlock"]:has(#adrawer-close-chk:checked) > [data-testid="stColumn"]:first-child {
  flex: 1 1 100% !important; max-width: 100% !important; width: 100% !important;
}
.adrawer-banner {
  display: flex; align-items: center; gap: .8rem; padding: .8rem .95rem; border-radius: 11px; margin-bottom: .85rem;
}
.adrawer-banner-ic {
  width: 36px; height: 36px; border-radius: 9px; flex-shrink: 0;
  display: inline-flex !important; align-items: center; justify-content: center; line-height: 0;
}
.adrawer-banner-ic .ic { display: block; margin: auto; }
.adrawer-banner-body { display: flex; flex-direction: column; justify-content: center; min-width: 0; }
.adrawer-banner-body b { display: block; font-size: .88rem; letter-spacing: .03em; line-height: 1.2; }
.adrawer-banner-sub { display: block; font-size: .76rem; color: #D5DCF6; margin-top: .16rem; line-height: 1.35; }
.adrawer-banner-block { background: rgba(255, 82, 111, .13); border: 1px solid rgba(255, 82, 111, .38); }
.adrawer-banner-block b { color: #FF526F; }
.adrawer-banner-block .adrawer-banner-ic { background: rgba(255, 82, 111, .18); border: 1px solid rgba(255, 82, 111, .38); }
.adrawer-banner-ask_human { background: rgba(255, 181, 71, .13); border: 1px solid rgba(255, 181, 71, .38); }
.adrawer-banner-ask_human b { color: #FFB547; }
.adrawer-banner-ask_human .adrawer-banner-ic { background: rgba(255, 181, 71, .18); border: 1px solid rgba(255, 181, 71, .38); }
.adrawer-banner-allow { background: rgba(0, 214, 160, .12); border: 1px solid rgba(0, 214, 160, .36); }
.adrawer-banner-allow b { color: #00D6A0; }
.adrawer-banner-allow .adrawer-banner-ic { background: rgba(0, 214, 160, .18); border: 1px solid rgba(0, 214, 160, .36); }

.adrawer-kv {
  display: flex; justify-content: space-between; align-items: center; gap: .75rem;
  padding: .5rem 0; border-bottom: 1px solid rgba(41, 52, 95, .6); font-size: .81rem;
}
.adrawer-k { display: inline-flex; align-items: center; gap: .5rem; color: #A8B3D3; font-weight: 500; line-height: 1.2; flex-shrink: 0; }
.adrawer-k .ic { display: block; flex-shrink: 0; }
.adrawer-v { color: #F5F6FF; font-weight: 600; text-align: right; word-break: break-word; min-width: 0; }
.arisk-pill {
  display: inline-block; padding: .12rem .5rem; border-radius: 6px; font-size: .76rem; font-weight: 700;
  font-variant-numeric: tabular-nums; white-space: nowrap;
}
.arisk-pill-low { background: rgba(0, 214, 160, .15); border: 1px solid rgba(0, 214, 160, .38); color: #00D6A0; }
.arisk-pill-med { background: rgba(255, 181, 71, .16); border: 1px solid rgba(255, 181, 71, .4); color: #FFB547; }
.arisk-pill-high { background: rgba(255, 82, 111, .18); border: 1px solid rgba(255, 82, 111, .42); color: #FF526F; }
.adrawer-sec { margin-top: .75rem; }
.adrawer-sec-title {
  display: inline-flex; align-items: center; gap: .45rem; font-size: .8rem; font-weight: 600; color: #A8B3D3; margin-bottom: .4rem; line-height: 1.2;
}
.adrawer-sec-title .ic { display: block; flex-shrink: 0; }
.adrawer-json {
  background: #0B1024; border: 1px solid #29345F; border-radius: 10px; padding: .75rem .85rem;
  font-family: ui-monospace, "Cascadia Code", Consolas, monospace; font-size: .8rem; color: #E2E8FF;
  white-space: pre-wrap; word-break: break-word; margin: 0; line-height: 1.45;
}
.adrawer-reason {
  background: rgba(11, 16, 36, .72); border: 1px solid #29345F; border-radius: 10px; padding: .75rem .85rem;
  color: #F5F6FF; font-size: .84rem; line-height: 1.55;
}
.adrawer-reason-en { color: #A8B3D3; font-size: .78rem; margin-top: .45rem; padding-top: .45rem; border-top: 1px solid rgba(41, 52, 95, .6); }
.adrawer-checks { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .55rem; }
.adrawer-chk-chip {
  font-size: .71rem; padding: .14rem .48rem; border-radius: 6px;
  background: rgba(21, 29, 59, .9); border: 1px solid #29345F; color: #A8B3D3; white-space: nowrap;
}
.adrawer-chk-flagged { border-color: rgba(255, 82, 111, .45); color: #FF8A9E; background: rgba(255, 82, 111, .1); }

@media (max-width: 1200px) {
  .audit-kpis { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 760px) {
  .audit-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; gap: .6rem; }
  .aargs { max-width: 140px; }
}

/* ---------- Policies Page Premium Console (scoped) ---------- */
.policy-kpis { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .95rem; align-items: stretch; margin: .85rem 0 .85rem; }
.policy-kpi {
  background: linear-gradient(180deg, #1B2345 0%, #141B38 100%);
  border: 1px solid #29345F; border-radius: 14px; padding: 1.05rem 1.2rem;
  display: flex; gap: .95rem; align-items: center; height: 100%; box-sizing: border-box;
  box-shadow: 0 10px 26px -14px rgba(0, 0, 0, .6), inset 0 1px 0 rgba(255, 255, 255, .05);
  transition: transform .22s var(--ease), border-color .22s var(--ease);
}
.policy-kpi:hover { transform: translateY(-2px); border-color: rgba(145, 71, 255, .55); }
.policy-kpi-ic {
  width: 46px; height: 46px; border-radius: 12px; flex-shrink: 0;
  display: inline-flex !important; align-items: center; justify-content: center; line-height: 0;
}
.policy-kpi-ic .ic { display: block; margin: auto; }
.policy-kpi-num { font-size: 1.75rem; font-weight: 800; color: #F5F6FF; line-height: 1.08; letter-spacing: -0.02em; }
.policy-kpi-label { font-size: .83rem; font-weight: 500; color: #A8B3D3; margin-top: .18rem; }

/* Policy Filter & Search Toolbar */
.st-key-policy_toolbar { margin: .15rem 0 .85rem; }
.st-key-policy_decision_wrap [role="radiogroup"] {
  display: inline-flex !important; flex-direction: row !important; flex-wrap: wrap; gap: .4rem;
  background: rgba(13, 18, 40, .82); border: 1px solid #29345F; border-radius: 11px; padding: .24rem;
  min-height: 40px; align-items: center; box-sizing: border-box;
}
.st-key-policy_decision_wrap [role="radiogroup"] > div,
.st-key-policy_decision_wrap [role="radiogroup"] > label {
  border-radius: 8px !important; border: 1px solid transparent; padding: 0 !important; margin: 0 !important;
  transition: background .15s, border-color .15s, box-shadow .15s; position: relative;
}
.st-key-policy_decision_wrap [data-testid="stRadioOption"] { padding: .34rem .82rem !important; cursor: pointer; position: static; }
.st-key-policy_decision_wrap [data-testid="stRadioOption"] > div > div:first-child { display: none; }
.st-key-policy_decision_wrap [data-testid="stRadioOption"]::after {
  content: ""; position: absolute; inset: 0; border-radius: inherit; z-index: 1; cursor: pointer;
}
.st-key-policy_decision_wrap [data-testid="stRadioOption"] p { font-size: .82rem !important; font-weight: 600 !important; color: #A8B3D3; white-space: nowrap; margin: 0 !important; }
.st-key-policy_decision_wrap [role="radiogroup"] > div[data-selected="true"],
.st-key-policy_decision_wrap [role="radiogroup"] > label:has(input:checked) {
  background: linear-gradient(90deg, #9147FF, #C044FF) !important;
  border-color: rgba(233, 213, 255, .55) !important;
  box-shadow: 0 3px 16px rgba(145, 71, 255, .45);
}
.st-key-policy_decision_wrap [role="radiogroup"] > div[data-selected="true"] [data-testid="stRadioOption"] p,
.st-key-policy_decision_wrap [role="radiogroup"] > label:has(input:checked) p { color: #FFFFFF !important; }
.st-key-policy_add_wrap button {
  background: linear-gradient(90deg, #9147FF 0%, #C044FF 100%) !important;
  border: 1px solid rgba(233, 213, 255, .45) !important;
  color: #FFFFFF !important; font-weight: 700 !important; border-radius: 10px !important;
  box-shadow: 0 4px 18px rgba(145, 71, 255, .45), inset 0 1px 0 rgba(255, 255, 255, .22) !important;
}
.st-key-policy_add_wrap button:hover { filter: brightness(1.08); }

/* Policy Cards */
.pcard {
  background: linear-gradient(180deg, rgba(24, 32, 68, .9) 0%, rgba(16, 22, 48, .96) 100%);
  border: 1px solid #29345F; border-radius: 14px; padding: 1.15rem 1.3rem; margin-bottom: .9rem;
  display: flex; gap: .95rem; align-items: flex-start; position: relative; box-sizing: border-box;
  box-shadow: 0 12px 30px -14px rgba(0, 0, 0, .65), inset 0 1px 0 rgba(255, 255, 255, .04);
  transition: transform .22s var(--ease), border-color .22s var(--ease), box-shadow .22s var(--ease);
}
.pcard:hover { transform: translateY(-2px); border-color: rgba(145, 71, 255, .55); }
.pcard-block { border-left: 3.5px solid #FF526F; box-shadow: -6px 0 20px -10px rgba(255, 82, 111, .5), 0 12px 30px -14px rgba(0, 0, 0, .65); }
.pcard-ask { border-left: 3.5px solid #FFB547; box-shadow: -6px 0 20px -10px rgba(255, 181, 71, .45), 0 12px 30px -14px rgba(0, 0, 0, .65); }
.pcard-ic {
  width: 38px; height: 38px; border-radius: 10px; flex-shrink: 0; margin-top: .1rem;
  display: inline-flex !important; align-items: center; justify-content: center; line-height: 0;
}
.pcard-ic .ic { display: block; margin: auto; }
.pcard-ic-block { background: rgba(255, 82, 111, .14); border: 1px solid rgba(255, 82, 111, .36); color: #FF526F; }
.pcard-ic-ask { background: rgba(255, 181, 71, .14); border: 1px solid rgba(255, 181, 71, .36); color: #FFB547; }
.pcard-main { flex: 1; min-width: 0; }
.pcard-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; }
.pcard-id { font-size: 1.05rem; font-weight: 700; color: #F5F6FF; line-height: 1.25; letter-spacing: -0.01em; }
.pcard-desc { font-size: .85rem; color: #A8B3D3; margin-top: .2rem; line-height: 1.4; }
.pcard-actions { display: inline-flex; align-items: center; gap: .45rem; flex-shrink: 0; }
.pcard-badge {
  display: inline-flex !important; align-items: center; justify-content: center; gap: .35rem;
  padding: .24rem .68rem; border-radius: 7px; font-size: .72rem; font-weight: 700; letter-spacing: .04em; line-height: 1;
  margin-right: .2rem; white-space: nowrap;
}
.pcard-badge .ic { display: block; flex-shrink: 0; }
.pcard-badge-block { background: rgba(255, 82, 111, .16); border: 1px solid rgba(255, 82, 111, .42); color: #FF526F; }
.pcard-badge-ask { background: rgba(255, 181, 71, .16); border: 1px solid rgba(255, 181, 71, .42); color: #FFB547; }
.pcard-act-btn {
  width: 30px; height: 30px; border-radius: 8px;
  display: inline-flex !important; align-items: center; justify-content: center; line-height: 0;
  background: rgba(21, 29, 59, .85); border: 1px solid #29345F; color: #A8B3D3 !important;
  text-decoration: none !important; transition: background .15s, border-color .15s, color .15s;
}
.pcard-act-btn .ic { display: block; margin: auto; }
.pcard-act-btn:hover { background: rgba(145, 71, 255, .22); border-color: rgba(145, 71, 255, .55); color: #F5F6FF !important; }
.pcard-conds { display: flex; align-items: center; flex-wrap: wrap; gap: .45rem; margin-top: .75rem; }
.pcard-tools-lbl { font-size: .81rem; font-weight: 600; color: #A8B3D3; margin-right: .15rem; }
.pchip {
  display: inline-block; padding: .2rem .62rem; border-radius: 7px;
  font-family: ui-monospace, "Cascadia Code", Consolas, monospace; font-size: .77rem; line-height: 1.3;
  background: rgba(27, 35, 69, .9); border: 1px solid rgba(145, 71, 255, .28); color: #D8C7FF;
}
.pchip-tool { background: rgba(145, 71, 255, .18); border-color: rgba(192, 68, 255, .42); color: #E9D5FF; font-weight: 600; }
.pcard-bn {
  display: flex; align-items: center; gap: .5rem; margin-top: .8rem; padding-top: .7rem;
  border-top: 1px solid rgba(41, 52, 95, .6); font-size: .87rem; color: #D5DCF6; line-height: 1.45;
}
.pcard-bn .ic { display: block; flex-shrink: 0; color: #A8B3D3; }
.pcard-bn b { color: #F5F6FF; font-weight: 600; }

@media (max-width: 760px) {
  .policy-kpis { grid-template-columns: 1fr; gap: .6rem; }
}

/* ---------- Datasets Page Premium Console (scoped) ---------- */
[data-testid="stHorizontalBlock"]:has(.ds-card) {
  align-items: stretch !important;
}
[data-testid="stHorizontalBlock"]:has(.ds-card) > [data-testid="stColumn"],
[data-testid="stHorizontalBlock"]:has(.ds-card) > [data-testid="stColumn"] > div,
[data-testid="stHorizontalBlock"]:has(.ds-card) [data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"]:has(.ds-card) [data-testid="stElementContainer"],
[data-testid="stHorizontalBlock"]:has(.ds-card) [data-testid="stMarkdown"],
[data-testid="stHorizontalBlock"]:has(.ds-card) [data-testid="stMarkdownContainer"] {
  display: flex !important;
  flex-direction: column !important;
  flex: 1 1 auto !important;
  height: 100% !important;
}
.ds-card {
  background: linear-gradient(180deg, rgba(24, 32, 68, .9) 0%, rgba(15, 21, 46, .96) 100%);
  border: 1px solid #29345F; border-radius: 14px; padding: 1.15rem 1.3rem;
  flex: 1 1 auto; height: 100%; box-sizing: border-box;
  box-shadow: 0 12px 30px -14px rgba(0, 0, 0, .65), inset 0 1px 0 rgba(255, 255, 255, .04);
}
.ds-card-head { display: flex; align-items: center; gap: .8rem; margin-bottom: .85rem; }
.ds-card-ic {
  width: 38px; height: 38px; border-radius: 10px; flex-shrink: 0;
  display: inline-flex !important; align-items: center; justify-content: center; line-height: 0;
  background: rgba(145, 71, 255, .16); border: 1px solid rgba(192, 68, 255, .38); color: #D8B4FE;
}
.ds-card-ic .ic { display: block; margin: auto; }
.ds-card-title { font-size: 1.05rem; font-weight: 700; color: #F5F6FF; line-height: 1.2; }
.ds-card-sub { font-size: .8rem; color: #A8B3D3; margin-top: .14rem; }

/* Language Distribution Table */
.ds-lang-table { width: 100%; border-collapse: collapse; font-size: .84rem; margin-top: .25rem; }
.ds-lang-table thead th {
  text-align: left; color: #A8B3D3; font-weight: 500; font-size: .78rem;
  padding: .5rem .6rem; border-bottom: 1px solid #29345F; white-space: nowrap;
}
.ds-lang-table thead th.num, .ds-lang-table tbody td.num { text-align: right; font-variant-numeric: tabular-nums; }
.ds-lang-table tbody td {
  padding: .68rem .6rem; color: #F5F6FF; font-weight: 600;
  border-bottom: 1px solid rgba(41, 52, 95, .48); vertical-align: middle;
}
.ds-lang-table tbody tr:last-child td { border-bottom: none; }
.ds-dot {
  display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin: 0 3px; vertical-align: middle;
}
.ds-dot-att { background: #FF526F; box-shadow: 0 0 8px rgba(255, 82, 111, .65); }
.ds-dot-ben { background: #00D6A0; box-shadow: 0 0 8px rgba(0, 214, 160, .65); }
.ds-share-wrap { display: flex; align-items: center; gap: .65rem; min-width: 155px; }
.ds-share-pct { color: #A8B3D3; font-weight: 500; font-size: .8rem; min-width: 42px; font-variant-numeric: tabular-nums; }
.ds-bar-track {
  flex: 1; height: 8px; border-radius: 999px; background: rgba(41, 52, 95, .65); overflow: hidden; min-width: 80px;
}
.ds-bar-fill {
  height: 100%; border-radius: 999px;
  background: linear-gradient(90deg, #9147FF, #C044FF);
  box-shadow: 0 0 10px rgba(145, 71, 255, .55);
}

/* Donut Chart Overview Card */
.ds-donut-card {
  display: flex !important; flex-direction: row !important; align-items: center; justify-content: space-around; gap: 1.25rem;
  min-height: 232px; padding: 1.15rem 1.4rem;
}
.ds-donut-wrap { position: relative; width: 156px; height: 156px; flex-shrink: 0; }
.ds-donut-center {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center; text-align: center; pointer-events: none;
}
.ds-donut-num { font-size: 1.85rem; font-weight: 800; color: #F5F6FF; line-height: 1.05; letter-spacing: -0.02em; }
.ds-donut-lbl { font-size: .74rem; color: #A8B3D3; margin-top: .18rem; }
.ds-legend { display: flex; flex-direction: column; gap: .95rem; flex: 1; max-width: 220px; }
.ds-legend-row { display: flex; justify-content: space-between; align-items: center; gap: .75rem; font-size: .86rem; }
.ds-legend-k { display: inline-flex; align-items: center; gap: .5rem; color: #D5DCF6; font-weight: 500; white-space: nowrap; }
.ds-legend-sq { width: 11px; height: 11px; border-radius: 3px; flex-shrink: 0; }
.ds-legend-v { color: #F5F6FF; font-weight: 700; font-variant-numeric: tabular-nums; white-space: nowrap; }

/* Dataset Files Card & Table */
.st-key-ds_files_card {
  background: linear-gradient(180deg, rgba(24, 32, 68, .9) 0%, rgba(15, 21, 46, .96) 100%);
  border: 1px solid #29345F; border-radius: 14px; padding: 1.2rem 1.35rem; margin-top: .95rem; box-sizing: border-box;
  box-shadow: 0 12px 30px -14px rgba(0, 0, 0, .65), inset 0 1px 0 rgba(255, 255, 255, .04);
}
.ds-files-table { width: 100%; border-collapse: collapse; font-size: .84rem; margin-top: .35rem; }
.ds-files-table thead th {
  text-align: left; color: #A8B3D3; font-weight: 500; font-size: .78rem;
  padding: .6rem .7rem; border-bottom: 1px solid #29345F; white-space: nowrap;
}
.ds-files-table thead th:last-child, .ds-files-table tbody td:last-child { text-align: right; }
.ds-files-table tbody td {
  padding: .78rem .7rem; color: #F5F6FF; border-bottom: 1px solid rgba(41, 52, 95, .48); vertical-align: middle;
}
.ds-files-table tbody tr:last-child td { border-bottom: none; }
.ds-files-table tbody tr:hover td { background: rgba(145, 71, 255, .07); }
.dfile-cell { display: inline-flex; align-items: center; gap: .65rem; font-weight: 600; color: #F5F6FF; white-space: nowrap; }
.dfile-ic {
  width: 28px; height: 28px; border-radius: 7px; flex-shrink: 0;
  display: inline-flex !important; align-items: center; justify-content: center;
  background: rgba(145, 71, 255, .18); border: 1px solid rgba(192, 68, 255, .4);
  color: #D8B4FE; font-family: ui-monospace, Consolas, monospace; font-size: .73rem; font-weight: 700; line-height: 1;
}
.ds-prog-wrap { display: flex; align-items: center; gap: .75rem; min-width: 185px; }
.ds-prog-track {
  flex: 1; height: 8px; border-radius: 999px; background: rgba(41, 52, 95, .7); overflow: hidden; min-width: 110px;
}
.ds-prog-fill {
  height: 100%; border-radius: 999px;
  background: linear-gradient(90deg, #00D6A0, #10B981);
  box-shadow: 0 0 10px rgba(0, 214, 160, .45);
}
.ds-prog-pct { color: #A8B3D3; font-size: .79rem; font-weight: 600; min-width: 36px; font-variant-numeric: tabular-nums; }
.ds-src-pill {
  display: inline-flex !important; align-items: center; gap: .4rem;
  padding: .24rem .68rem; border-radius: 7px; font-size: .76rem; font-weight: 500;
  background: rgba(27, 35, 69, .92); border: 1px solid rgba(145, 71, 255, .32); color: #D8C7FF; line-height: 1.2;
  white-space: nowrap;
}
.ds-src-pill .ic { display: block; flex-shrink: 0; color: #C084FC; }
.ds-act-group { display: inline-flex; align-items: center; gap: .4rem; }
.ds-act-btn {
  width: 30px; height: 30px; border-radius: 8px;
  display: inline-flex !important; align-items: center; justify-content: center; line-height: 0;
  background: rgba(21, 29, 59, .85); border: 1px solid #29345F; color: #A8B3D3 !important;
  text-decoration: none !important; transition: background .15s, border-color .15s, color .15s;
}
.ds-act-btn .ic { display: block; margin: auto; }
.ds-act-btn:hover { background: rgba(145, 71, 255, .22); border-color: rgba(145, 71, 255, .55); color: #F5F6FF !important; }

@media (max-width: 900px) {
  .ds-donut-card { flex-direction: column !important; padding: 1rem; }
}

/* ---------- Benchmarks Page Premium Console (scoped) ---------- */
.bm-section { margin-bottom: 1.5rem; }
.bm-section-det { margin-bottom: .75rem; }
.bm-run-banner {
  background: linear-gradient(90deg, rgba(28, 36, 78, .92) 0%, rgba(16, 22, 48, .96) 100%);
  border: 1px solid #29345F; border-radius: 14px; padding: 1.05rem 1.25rem;
  display: flex; align-items: center; gap: 1rem; margin-bottom: .9rem; box-sizing: border-box;
  box-shadow: 0 12px 30px -14px rgba(0, 0, 0, .65), inset 0 1px 0 rgba(255, 255, 255, .05);
}
.bm-run-ic {
  width: 50px; height: 50px; border-radius: 13px; flex-shrink: 0;
  display: inline-flex !important; align-items: center; justify-content: center; line-height: 0;
  background: linear-gradient(135deg, rgba(145, 71, 255, .28), rgba(192, 68, 255, .14));
  border: 1px solid rgba(192, 68, 255, .48);
  box-shadow: 0 0 22px rgba(145, 71, 255, .32);
}
.bm-run-ic .ic { display: block; margin: auto; }
.bm-run-title { font-size: 1.2rem; font-weight: 800; color: #F5F6FF; line-height: 1.2; letter-spacing: -0.01em; }
.bm-pills { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .48rem; }
.bm-pill {
  display: inline-flex !important; align-items: center; gap: .38rem;
  padding: .22rem .68rem; border-radius: 7px; font-size: .75rem; font-weight: 500;
  background: rgba(15, 20, 44, .85); border: 1px solid rgba(140, 120, 255, .24); color: #C5CEE8; line-height: 1.2;
}
.bm-pill .ic { display: block; flex-shrink: 0; color: #B48EFF; }
.bm-pill-sim { border-color: rgba(255, 181, 71, .4); color: #FFD089; background: rgba(255, 181, 71, .1); }
.bm-pill-real { border-color: rgba(0, 214, 160, .4); color: #5CE6BE; background: rgba(0, 214, 160, .1); }

/* Agent Summary Cards + Comparison Table Grid */
.bm-agent-grid {
  display: grid; grid-template-columns: 248px minmax(0, 1fr); gap: .9rem; align-items: stretch; margin-bottom: 1.15rem;
}
.bm-kpi-stack { display: flex; flex-direction: column; gap: .85rem; justify-content: space-between; height: 100%; }
.bm-sum-card {
  flex: 1; border-radius: 14px; padding: 1rem 1.1rem; box-sizing: border-box;
  display: flex; align-items: flex-start; gap: .85rem;
  box-shadow: 0 10px 26px -14px rgba(0, 0, 0, .6), inset 0 1px 0 rgba(255, 255, 255, .05);
}
.bm-sum-safe {
  background: radial-gradient(150px 110px at 18% 22%, rgba(0, 214, 160, .20), transparent 72%),
              linear-gradient(180deg, rgba(16, 40, 46, .92) 0%, rgba(13, 24, 38, .96) 100%);
  border: 1px solid rgba(0, 214, 160, .48);
}
.bm-sum-benign {
  background: radial-gradient(150px 110px at 18% 22%, rgba(145, 71, 255, .24), transparent 72%),
              linear-gradient(180deg, rgba(28, 25, 66, .92) 0%, rgba(17, 21, 48, .96) 100%);
  border: 1px solid rgba(145, 71, 255, .52);
}
.bm-sum-ring {
  width: 38px; height: 38px; border-radius: 50%; flex-shrink: 0; margin-top: .1rem;
  display: inline-flex !important; align-items: center; justify-content: center; line-height: 0;
}
.bm-sum-ring .ic { display: block; margin: auto; }
.bm-sum-ring-safe {
  background: rgba(0, 214, 160, .16); border: 1.5px solid rgba(0, 214, 160, .55);
  box-shadow: 0 0 14px rgba(0, 214, 160, .32);
}
.bm-sum-ring-benign {
  background: rgba(145, 71, 255, .22); border: 1.5px solid rgba(192, 68, 255, .6);
  box-shadow: 0 0 14px rgba(145, 71, 255, .35);
}
.bm-sum-lbl { font-size: .77rem; font-weight: 600; color: #F5F6FF; line-height: 1.25; }
.bm-sum-lbl span { display: block; font-weight: 400; color: #A8B3D3; font-size: .73rem; }
.bm-sum-val { font-size: 1.85rem; font-weight: 800; color: #FFFFFF; line-height: 1.1; margin-top: .25rem; letter-spacing: -0.02em; }
.bm-sum-sub { font-size: .75rem; color: #A8B3D3; margin-top: .15rem; }

/* Benchmark Comparison Table */
.bm-table-card {
  background: linear-gradient(180deg, rgba(21, 29, 59, .92) 0%, rgba(13, 18, 40, .96) 100%);
  border: 1px solid #29345F; border-radius: 14px; overflow: hidden;
  display: flex; flex-direction: column; justify-content: center; height: 100%; box-sizing: border-box;
  box-shadow: 0 12px 30px -14px rgba(0, 0, 0, .65), inset 0 1px 0 rgba(255, 255, 255, .04);
}
.bm-table { width: 100%; border-collapse: collapse; font-size: .83rem; }
.bm-table thead th {
  text-align: left; color: #A8B3D3; font-weight: 500; font-size: .77rem; line-height: 1.35;
  padding: .75rem .9rem; border-bottom: 1px solid #29345F; border-right: 1px solid rgba(41, 52, 95, .4);
}
.bm-table thead th:last-child { border-right: none; }
.bm-table tbody td {
  padding: .85rem .9rem; color: #F5F6FF; font-weight: 500; font-variant-numeric: tabular-nums;
  border-bottom: 1px solid rgba(41, 52, 95, .48); border-right: 1px solid rgba(41, 52, 95, .35);
  vertical-align: middle;
}
.bm-table tbody td:first-child { font-weight: 700; color: #FFFFFF; }
.bm-table tbody td:last-child { border-right: none; }
.bm-table tbody tr:last-child td { border-bottom: none; }
.bm-table tbody tr:hover td { background: rgba(145, 71, 255, .06); }
.bm-safe-pill {
  display: inline-block; padding: .24rem .68rem; border-radius: 8px;
  background: rgba(0, 214, 160, .14); border: 1px solid rgba(0, 214, 160, .42);
  color: #2EE59D; font-weight: 700; font-size: .8rem; white-space: nowrap;
  box-shadow: 0 0 14px rgba(0, 214, 160, .16);
}

/* Outcomes Section */
.bm-out-head {
  display: flex; align-items: baseline; flex-wrap: wrap; gap: .55rem; margin: .2rem 0 .7rem;
}
.bm-out-title {
  display: inline-flex; align-items: center; gap: .5rem; font-size: 1.08rem; font-weight: 700; color: #F5F6FF; line-height: 1.2;
}
.bm-out-title .ic { display: block; flex-shrink: 0; color: #C084FC; }
.bm-out-sub { font-size: .82rem; color: #A8B3D3; font-weight: 400; }
.bm-outcome-grid {
  display: grid; grid-template-columns: minmax(310px, 1fr) minmax(0, 1.58fr); gap: .9rem; align-items: stretch;
}
.bm-item-pill {
  display: inline-flex !important; align-items: center; gap: .45rem; font-weight: 600; color: #F5F6FF; white-space: nowrap;
}
.bm-item-ic {
  width: 22px; height: 22px; border-radius: 6px; flex-shrink: 0;
  display: inline-flex !important; align-items: center; justify-content: center; line-height: 0;
}
.bm-item-ic .ic { display: block; margin: auto; }
.bm-item-att { background: rgba(255, 82, 111, .16); border: 1px solid rgba(255, 82, 111, .4); color: #FF526F; }
.bm-item-ben { background: rgba(0, 214, 160, .16); border: 1px solid rgba(0, 214, 160, .4); color: #00D6A0; }

/* Publication-Quality Benchmark Chart Card */
[class*="st-key-bm_chart_"] {
  background: linear-gradient(180deg, rgba(21, 29, 59, .92) 0%, rgba(12, 17, 38, .96) 100%);
  border: 1px solid rgba(145, 71, 255, .34); border-radius: 14px; padding: 1.05rem 1.25rem .75rem;
  margin: 0 0 1.65rem; box-sizing: border-box;
  box-shadow: 0 12px 30px -14px rgba(0, 0, 0, .65), inset 0 1px 0 rgba(255, 255, 255, .04);
}
.bm-chart-head {
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: .85rem;
  margin-bottom: .55rem; padding-bottom: .65rem; border-bottom: 1px solid rgba(41, 52, 95, .65);
}
.bm-chart-head-left { display: flex; align-items: center; gap: .8rem; }
.bm-chart-ic {
  width: 40px; height: 40px; border-radius: 10px; flex-shrink: 0;
  display: inline-flex !important; align-items: center; justify-content: center; line-height: 0;
  background: rgba(168, 85, 247, .16); border: 1px solid rgba(168, 85, 247, .4); color: #D8B4FE;
}
.bm-chart-ic .ic { display: block; margin: auto; }
.bm-chart-title { font-size: 1.04rem; font-weight: 700; color: #F5F6FF; line-height: 1.2; }
.bm-chart-sub { font-size: .8rem; color: #A8B3D3; margin-top: .16rem; line-height: 1.3; }
.bm-chart-legend {
  display: inline-flex; align-items: center; flex-wrap: wrap; gap: 1rem;
  padding: .34rem .78rem; border-radius: 9px;
  background: rgba(13, 18, 40, .78); border: 1px solid rgba(145, 71, 255, .24);
}
.bm-leg-item {
  display: inline-flex; align-items: center; gap: .42rem;
  font-size: .78rem; font-weight: 600; color: #E2E8FF; white-space: nowrap;
}
.bm-leg-dot {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; display: inline-block;
}

@media (max-width: 1050px) {
  .bm-agent-grid, .bm-outcome-grid { grid-template-columns: 1fr; }
  .bm-kpi-stack { flex-direction: row; }
}
@media (max-width: 680px) {
  .bm-kpi-stack { flex-direction: column; }
}

/* ---------- Premium Aurora Gradient & Curved Neon Wave Overlay ---------- */
[data-testid="stElementContainer"]:has(.aurora-bg) {
  position: fixed !important; inset: 0 !important; width: 0 !important; height: 0 !important;
  margin: 0 !important; padding: 0 !important; pointer-events: none !important; z-index: 0 !important;
}
.block-container, section[data-testid="stSidebar"] { position: relative; z-index: 1; }
.aurora-bg {
  position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden;
}
.aurora-orb-tr {
  position: absolute; top: -85px; right: -55px; width: 540px; height: 270px; border-radius: 50%;
  background: radial-gradient(ellipse at center, rgba(192, 68, 255, .24) 0%, rgba(145, 71, 255, .14) 48%, transparent 74%);
  filter: blur(42px); will-change: transform, opacity;
  animation: aurora-glow-pulse 14s ease-in-out infinite alternate;
}
.aurora-orb-tr2 {
  position: absolute; top: -35px; right: 160px; width: 380px; height: 190px; border-radius: 50%;
  background: radial-gradient(ellipse at center, rgba(145, 71, 255, .18) 0%, rgba(192, 68, 255, .08) 55%, transparent 75%);
  filter: blur(36px);
}
.aurora-orb-bl {
  position: absolute; bottom: -75px; left: -45px; width: 320px; height: 210px; border-radius: 50%;
  background: radial-gradient(ellipse at center, rgba(145, 71, 255, .20) 0%, rgba(192, 68, 255, .09) 52%, transparent 74%);
  filter: blur(34px);
}
.aurora-wave-tr {
  position: absolute; top: -14px; right: -22px; width: 620px; height: 210px;
  opacity: .88; will-change: transform;
  animation: aurora-wave-drift 18s ease-in-out infinite alternate;
}
.aurora-wave-bl {
  position: absolute; bottom: -14px; left: -18px; width: 300px; height: 150px;
  opacity: .72; will-change: transform;
  animation: aurora-wave-drift 22s ease-in-out infinite alternate-reverse;
}
@keyframes aurora-wave-drift {
  0% { transform: translate3d(0, 0, 0) scale(1); }
  100% { transform: translate3d(-10px, 4px, 0) scale(1.02); }
}
@keyframes aurora-glow-pulse {
  0% { opacity: .78; transform: translate3d(0, 0, 0) scale(1); }
  100% { opacity: 1; transform: translate3d(-8px, 6px, 0) scale(1.04); }
}
</style>
<div class="aurora-bg" aria-hidden="true">
  <div class="aurora-orb-tr"></div>
  <div class="aurora-orb-tr2"></div>
  <div class="aurora-orb-bl"></div>
  <svg class="aurora-wave-tr" viewBox="0 0 640 210" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="awCore" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#9147FF" stop-opacity="0"/>
        <stop offset="28%" stop-color="#9147FF" stop-opacity="0.55"/>
        <stop offset="64%" stop-color="#C044FF" stop-opacity="0.92"/>
        <stop offset="84%" stop-color="#F5D0FE" stop-opacity="0.95"/>
        <stop offset="100%" stop-color="#9147FF" stop-opacity="0.3"/>
      </linearGradient>
      <linearGradient id="awGlow" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#9147FF" stop-opacity="0"/>
        <stop offset="35%" stop-color="#9147FF" stop-opacity="0.32"/>
        <stop offset="72%" stop-color="#C044FF" stop-opacity="0.48"/>
        <stop offset="100%" stop-color="#9147FF" stop-opacity="0.12"/>
      </linearGradient>
    </defs>
    <path d="M 30 8 C 195 112, 355 -28, 520 52 C 578 80, 616 54, 650 18"
          stroke="url(#awGlow)" stroke-width="18" stroke-linecap="round" style="filter:blur(10px)"/>
    <path d="M 30 8 C 195 112, 355 -28, 520 52 C 578 80, 616 54, 650 18"
          stroke="url(#awCore)" stroke-width="2.4" stroke-linecap="round"/>
    <path d="M 95 -6 C 245 86, 390 -14, 545 64 C 592 88, 625 68, 655 38"
          stroke="url(#awCore)" stroke-width="1.15" stroke-opacity="0.52" stroke-linecap="round"/>
  </svg>
  <svg class="aurora-wave-bl" viewBox="0 0 300 150" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M -10 135 C 75 128, 130 68, 220 62 C 260 59, 285 72, 310 88"
          stroke="url(#awGlow)" stroke-width="14" stroke-linecap="round" style="filter:blur(8px)"/>
    <path d="M -10 135 C 75 128, 130 68, 220 62 C 260 59, 285 72, 310 88"
          stroke="url(#awCore)" stroke-width="1.9" stroke-opacity="0.78" stroke-linecap="round"/>
  </svg>
</div>
"""

SHIELD_ART = """
<svg class="shield-art" viewBox="0 0 580 265" xmlns="http://www.w3.org/2000/svg" aria-label="AgentShield">
  <defs>
    <linearGradient id="sg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#D47AFF"/>
      <stop offset="50%" stop-color="#8A3FFC"/>
      <stop offset="100%" stop-color="#491D8B"/>
    </linearGradient>
    <linearGradient id="sg2" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#2E1B6E"/>
      <stop offset="100%" stop-color="#120B36"/>
    </linearGradient>
    <linearGradient id="traceL" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#8B5CFF" stop-opacity=".18"/>
      <stop offset="100%" stop-color="#C98BFF" stop-opacity=".75"/>
    </linearGradient>
    <linearGradient id="traceR" x1="1" y1="0" x2="0" y2="0">
      <stop offset="0%" stop-color="#8B5CFF" stop-opacity=".18"/>
      <stop offset="100%" stop-color="#C98BFF" stop-opacity=".75"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="46%" r="48%">
      <stop offset="0%" stop-color="#9333EA" stop-opacity=".55"/>
      <stop offset="60%" stop-color="#6D28D9" stop-opacity=".18"/>
      <stop offset="100%" stop-color="#6D28D9" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="padglow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#C084FC" stop-opacity=".65"/>
      <stop offset="55%" stop-color="#7C3AED" stop-opacity=".28"/>
      <stop offset="100%" stop-color="#7C3AED" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <ellipse class="aura" cx="290" cy="122" rx="185" ry="118" fill="url(#glow)"/>

  <!-- Connector traces from the 6 feature pills into the shield -->
  <g class="connectors" fill="none" stroke-width="1.5">
    <path d="M 155 34 C 195 34, 205 74, 232 82" stroke="url(#traceL)"/>
    <path d="M 145 122 L 222 122" stroke="url(#traceL)"/>
    <path d="M 185 212 C 212 212, 218 164, 240 154" stroke="url(#traceL)"/>
    <path d="M 425 34 C 385 34, 375 74, 348 82" stroke="url(#traceR)"/>
    <path d="M 435 122 L 358 122" stroke="url(#traceR)"/>
    <path d="M 395 212 C 368 212, 362 164, 340 154" stroke="url(#traceR)"/>
    <circle cx="232" cy="82" r="3" fill="#E9D5FF"/>
    <circle cx="222" cy="122" r="3" fill="#E9D5FF"/>
    <circle cx="240" cy="154" r="3" fill="#E9D5FF"/>
    <circle cx="348" cy="82" r="3" fill="#E9D5FF"/>
    <circle cx="358" cy="122" r="3" fill="#E9D5FF"/>
    <circle cx="340" cy="154" r="3" fill="#E9D5FF"/>
  </g>

  <!-- Holographic pedestal rings -->
  <ellipse class="pad-glow" cx="290" cy="212" rx="96" ry="22" fill="url(#padglow)"/>
  <ellipse cx="290" cy="212" rx="86" ry="16" fill="none" stroke="#A855F7" stroke-opacity=".65" stroke-width="1.8"/>
  <ellipse cx="290" cy="212" rx="60" ry="10" fill="none" stroke="#E9D5FF" stroke-opacity=".75" stroke-width="1.5"/>
  <ellipse cx="290" cy="124" rx="108" ry="30" fill="none" stroke="#B44CFF" stroke-opacity=".28" stroke-width="1.2"/>
  <ellipse class="orbit" cx="290" cy="124" rx="108" ry="30" fill="none" stroke="#F3E8FF" stroke-width="2"
           stroke-linecap="round" pathLength="1000" stroke-dasharray="70 930"/>

  <!-- 3D Shield -->
  <g class="shield-body">
    <path d="M290 30 L352 54 C352 118 330 160 290 185 C250 160 228 118 228 54 Z"
          fill="url(#sg)" stroke="#F3E8FF" stroke-opacity=".85" stroke-width="2.2"/>
    <path d="M290 46 L337 64 C337 115 320 148 290 167 C260 148 243 115 243 64 Z"
          fill="url(#sg2)" stroke="#C084FC" stroke-opacity=".65" stroke-width="1.5"/>
    <path d="M267 108 L283 124 L316 90" fill="none" stroke="#FFFFFF" stroke-width="9.5"
          stroke-linecap="round" stroke-linejoin="round"/>
  </g>
</svg>
"""

FEATURES = [  # (label, icon, css position inside .hero-art)
    ("Prompt Injection", "zap", "left:1%; top:5%"),
    ("Data Tainting", "layers", "left:0%; top:39%"),
    ("Multilingual (BN / Banglish / EN)", "globe", "left:0%; top:73%"),
    ("Instruction Hiding", "eye-off", "right:1%; top:5%"),
    ("Unsafe Action", "alert", "right:0%; top:39%"),
    ("Policy Enforcement", "scale", "right:0%; top:73%"),
]


def hero_art() -> str:
    chips = "".join(
        f'<span class="feat" style="{pos}"><span class="feat-ic">{icon(ic, 13)}</span>{esc(label)}</span>'
        for label, ic, pos in FEATURES
    )
    return f'<div class="hero-art">{SHIELD_ART}{chips}</div>'


def kpi(icon_name: str, tint: str, number: str, label: str, note: str = "", trend: str = "") -> str:
    trend_html = f'<span class="trend">{esc(trend)}</span>' if trend else ""
    note_html = f'<div class="kpi-note">{esc(note)}</div>' if note else ""
    return (
        f'<div class="kpi"><div class="kpi-icon" style="background:{tint}1F;border:1px solid {tint}48">'
        f'{icon(icon_name, 22, tint)}</div>'
        f'<div><div class="kpi-num">{esc(number)}{trend_html}</div>'
        f'<div class="kpi-label">{esc(label)}</div>{note_html}</div></div>'
    )


def panel_title(icon_name: str, title: str, sub: str = "", badge: bool = False, right: str = "") -> str:
    if badge:
        ic = f'<span class="play-badge">{icon(icon_name, 17, "#fff")}</span>'
    else:
        ic = f'<span class="sec-badge">{icon(icon_name, 17, "#C9B6FF")}</span>'
    right_html = f'<div class="panel-right">{right}</div>' if right else ""
    sub_html = f'<div class="panel-sub">{esc(sub)}</div>' if sub else ""
    return (
        f'<div class="panel-head"><div><div class="panel-title">{ic}<span>{esc(title)}</span></div>'
        f'{sub_html}</div>{right_html}</div>'
    )


BADGE_CLASS = {"allow": ("ALLOW", "b-allow"), "ask_human": ("ASK", "b-ask"), "block": ("BLOCK", "b-block")}


def badge(decision: str) -> str:
    text, css = BADGE_CLASS[decision]
    return f'<span class="badge {css}">{text}</span>'


HOW_IT_WORKS = f"""
<div class="flow">
  <div class="node node-user"><span class="node-ic">{icon("mail", 20, "#FF6B78")}</span><b>Untrusted input</b><span class="node-sub">email · web · file</span></div>
  <div class="arrow">{icon("arrow-right", 20)}</div>
  <div class="node node-shield"><span class="node-ic">{icon("shield-check", 22, "#E2D4FF")}</span><b>AgentShield</b><span class="node-sub">checks each tool call</span></div>
  <div class="arrow">{icon("arrow-right", 20)}</div>
  <div class="node node-dec"><span class="node-ic">{icon("circle-check", 20, "#16C784")}</span><b>Decision</b><span class="node-sub">allow · ask · block</span></div>
</div>
"""

DECISIONS = f"""
<div class="decs">
  <div class="dec dec-allow"><div class="dec-head">{icon("circle-check", 20, "#16C784")}<b>ALLOW</b></div><span>Action follows from the user's request</span></div>
  <div class="dec dec-ask"><div class="dec-head">{icon("circle-help", 20, "#F5A623")}<b>ASK</b></div><span>Uncertain: the user approves or rejects</span></div>
  <div class="dec dec-block"><div class="dec-head">{icon("circle-x", 20, "#F04452")}<b>BLOCK</b></div><span>Clear attack or policy violation</span></div>
</div>
"""

PIPELINE = f"""
<div class="pipe">
  <div class="pnode"><span class="pnode-ic">{icon("layers", 19)}</span><span class="pnode-num">01</span><div class="pnode-body"><b>Taint Analysis</b><span class="pnode-sub">Where did each value come from?</span></div></div>
  <div class="arrow">{icon("arrow-right", 18)}</div>
  <div class="pnode"><span class="pnode-ic">{icon("target", 19)}</span><span class="pnode-num">02</span><div class="pnode-body"><b>Injection Classifier</b><span class="pnode-sub">Instructions hidden in data?</span></div></div>
  <div class="arrow">{icon("arrow-right", 18)}</div>
  <div class="pnode"><span class="pnode-ic">{icon("activity", 19)}</span><span class="pnode-num">03</span><div class="pnode-body"><b>Intent + Policy</b><span class="pnode-sub">Did the user ask? Fixed rules</span></div></div>
  <div class="arrow">{icon("arrow-right", 18)}</div>
  <div class="pnode"><span class="pnode-ic">{icon("zap", 19)}</span><span class="pnode-num">04</span><div class="pnode-body"><b>Agent Decision</b><span class="pnode-sub">Allow / Ask / Block + reason (BN/EN)</span></div></div>
</div>
"""


def _taka(amount: int) -> str:
    return f"৳ {amount:,}"


def summary_banner(name: str, stolen_without: int, stolen_with: int) -> tuple[str, str] | None:
    """(css class, text) for the bar above the two columns, or None.

    An attack scenario where the agent did not act on the injection by itself (real models often
    ignore blunt ones) must not be presented as a normal task or as AgentShield's success."""
    saved = stolen_without - stolen_with
    if saved > 0:
        return "", f"🛡️ AgentShield saved {_taka(saved)} · AgentShield {_taka(saved)} বাঁচিয়েছে"
    if stolen_without == 0 and name.startswith("attack"):
        return ("summary-neutral", "ℹ️ The agent ignored this attack on its own this time, so AgentShield had nothing "
                "to stop · এবার AI নিজেই attack উপেক্ষা করেছে, তাই AgentShield-এর আটকানোর কিছু ছিল না")
    if stolen_without == 0:
        return "", "✅ Normal task: AgentShield let it run · সাধারণ কাজ, AgentShield বাধা দেয়নি"
    return None


# ---------------------------------------------------------------------------
# Audit Log Console Builders
# ---------------------------------------------------------------------------
AUDIT_BADGE = {
    "allow": ("ALLOW", "abadge-allow"),
    "ask_human": ("ASK HUMAN", "abadge-ask_human"),
    "block": ("BLOCK", "abadge-block"),
}


def audit_badge(decision: str) -> str:
    text, css = AUDIT_BADGE.get(decision, (decision.upper(), "abadge-allow"))
    return f'<span class="abadge {css}">{esc(text)}</span>'


def format_risk_score(score: float) -> str:
    if score == 0:
        return "0"
    formatted = f"{score:.2f}"
    if formatted.endswith("0") and not formatted.endswith(".00"):
        return formatted.rstrip("0")
    if formatted.endswith(".00"):
        return formatted[:-3]
    return formatted


def audit_risk_level(score: float, ask_at: float = 0.4, block_at: float = 0.75) -> tuple[str, str, str]:
    """Classify risk score using backend DecisionThresholds (ask_human_at=0.4, block_at=0.75)."""
    num_str = format_risk_score(score)
    if score >= block_at:
        return num_str, "high", "High"
    if score >= ask_at:
        return num_str, "med", "Medium"
    return num_str, "low", "Low"


def audit_tool_icon(tool_name: str) -> str:
    lower = tool_name.lower()
    if "money" in lower or "pay" in lower or "transfer" in lower or "bank" in lower:
        return "wallet"
    if "mail" in lower or "inbox" in lower:
        return "mail"
    if "web" in lower or "http" in lower or "url" in lower:
        return "globe"
    if "file" in lower or "doc" in lower:
        return "file-text"
    return "terminal"


def audit_kpi_card(icon_name: str, tint: str, label: str, value: str, sub: str) -> str:
    return (
        f'<div class="audit-kpi" style="border-bottom:2px solid {tint}66">'
        f'<div class="audit-kpi-ring" style="background:{tint}1A;border:1.5px solid {tint}66;'
        f'box-shadow:0 0 16px {tint}2E">{icon(icon_name, 20, tint)}</div>'
        f'<div class="audit-kpi-body">'
        f'<div class="audit-kpi-label">{esc(label)}</div>'
        f'<div class="audit-kpi-val">{esc(value)}</div>'
        f'<div class="audit-kpi-meta" style="color:{tint}"><span>{esc(sub)}</span></div>'
        f'</div></div>'
    )


def audit_page_items(current_page: int, total_pages: int) -> list[int | str]:
    """Compact page list e.g. [1, 2, 3, 4, 5, '…', 33]."""
    if total_pages <= 7:
        return list(range(1, total_pages + 1))
    if current_page <= 4:
        return [1, 2, 3, 4, 5, "…", total_pages]
    if current_page >= total_pages - 3:
        return [1, "…", total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
    return [1, "…", current_page - 1, current_page, current_page + 1, "…", total_pages]


# ---------------------------------------------------------------------------
# Policies Console Builders
# ---------------------------------------------------------------------------
def policy_kpi_card(icon_name: str, tint: str, number: int | str, label: str) -> str:
    return (
        f'<div class="policy-kpi">'
        f'<div class="policy-kpi-ic" style="background:{tint}1A;border:1px solid {tint}4D;'
        f'box-shadow:0 0 16px {tint}26">{icon(icon_name, 21, tint)}</div>'
        f'<div><div class="policy-kpi-num">{esc(number)}</div>'
        f'<div class="policy-kpi-label">{esc(label)}</div></div></div>'
    )


def policy_card_html(rule: dict, inspect_href: str, copy_href: str, detail_href: str) -> str:
    is_block = rule.get("decision") == "block"
    card_cls = "pcard-block" if is_block else "pcard-ask"
    ic_cls = "pcard-ic-block" if is_block else "pcard-ic-ask"
    ic_name = "shield-x" if is_block else "circle-help"
    ic_color = "#FF526F" if is_block else "#FFB547"
    badge_cls = "pcard-badge-block" if is_block else "pcard-badge-ask"
    badge_ic = "circle-x" if is_block else "circle-help"
    badge_txt = "BLOCK" if is_block else "ASK"

    tools_chips = "".join(f'<span class="pchip pchip-tool">{esc(t)}</span>' for t in rule.get("tools", []))
    cond_chips = "".join(
        f'<span class="pchip">{esc(k)}: {esc(json.dumps(v, ensure_ascii=False))}</span>'
        for k, v in (rule.get("when") or {}).items()
    )

    return (
        f'<div class="pcard {card_cls}">'
        f'<div class="pcard-ic {ic_cls}">{icon(ic_name, 20, ic_color)}</div>'
        f'<div class="pcard-main">'
        f'<div class="pcard-top">'
        f'<div><div class="pcard-id">{esc(rule["id"])}</div>'
        f'<div class="pcard-desc">{esc(rule.get("description", ""))}</div></div>'
        f'<div class="pcard-actions">'
        f'<span class="pcard-badge {badge_cls}">{icon(badge_ic, 13, ic_color)}<span>{badge_txt}</span></span>'
        f'<a class="pcard-act-btn" href="{inspect_href}" target="_self" title="Inspect rule">{icon("edit", 14)}</a>'
        f'<a class="pcard-act-btn" href="{copy_href}" target="_self" title="Copy rule YAML">{icon("copy", 14)}</a>'
        f'<a class="pcard-act-btn" href="{detail_href}" target="_self" title="Rule details">{icon("more-vertical", 14)}</a>'
        f'</div></div>'
        f'<div class="pcard-conds"><span class="pcard-tools-lbl">Tools:</span>{tools_chips}{cond_chips}</div>'
        f'<div class="pcard-bn">{icon("message-square", 15, "#A8B3D3")}'
        f'<span><b>কারণ:</b> {esc(rule.get("reason_bn", ""))}</span></div>'
        f'</div></div>'
    )


# ---------------------------------------------------------------------------
# Datasets Console Builders
# ---------------------------------------------------------------------------
def dataset_lang_card_html(summary: dict[str, dict[str, int]]) -> str:
    grand_total = sum(c.get("attack", 0) + c.get("benign", 0) for c in summary.values())
    rows_html = []
    for lang, counts in sorted(summary.items()):
        att = counts.get("attack", 0)
        ben = counts.get("benign", 0)
        tot = att + ben
        share = (tot / grand_total * 100.0) if grand_total else 0.0
        bar_w = min(100.0, max(4.0, share * 1.6))
        rows_html.append(
            f'<tr>'
            f'<td>{esc(lang)}</td>'
            f'<td class="num">{att}</td>'
            f'<td class="num">{ben}</td>'
            f'<td class="num">{tot}</td>'
            f'<td><div class="ds-share-wrap">'
            f'<span class="ds-share-pct">{share:.1f}%</span>'
            f'<div class="ds-bar-track"><div class="ds-bar-fill" style="width:{bar_w:.1f}%"></div></div>'
            f'</div></td>'
            f'</tr>'
        )
    return (
        f'<div class="ds-card">'
        f'<div class="ds-card-head">'
        f'<div class="ds-card-ic">{icon("chart", 19, "#D8B4FE")}</div>'
        f'<div><div class="ds-card-title">Language Distribution</div>'
        f'<div class="ds-card-sub">Number of samples by language in the dataset.</div></div>'
        f'</div>'
        f'<table class="ds-lang-table">'
        f'<thead><tr>'
        f'<th>Language</th>'
        f'<th class="num">Attack (<span class="ds-dot ds-dot-att"></span>)</th>'
        f'<th class="num">Benign (<span class="ds-dot ds-dot-ben"></span>)</th>'
        f'<th class="num">Total</th>'
        f'<th>Share</th>'
        f'</tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        f'</table></div>'
    )


def dataset_donut_card_html(total_attack: int, total_benign: int) -> str:
    total = total_attack + total_benign
    att_pct = (total_attack / total * 100.0) if total else 0.0
    ben_pct = (total_benign / total * 100.0) if total else 0.0

    return (
        f'<div class="ds-card ds-donut-card">'
        f'<div class="ds-donut-wrap">'
        f'<svg width="156" height="156" viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">'
        f'<defs>'
        f'<linearGradient id="dsBenGrad" x1="0" y1="1" x2="0" y2="0">'
        f'<stop offset="0%" stop-color="#00D6A0"/>'
        f'<stop offset="100%" stop-color="#3B82F6"/>'
        f'</linearGradient>'
        f'</defs>'
        f'<circle cx="80" cy="80" r="60" fill="none" stroke="#1E2952" stroke-width="18"/>'
        f'<circle cx="80" cy="80" r="60" fill="none" stroke="url(#dsBenGrad)" stroke-width="18" '
        f'pathLength="100" stroke-dasharray="{ben_pct:.2f} {100 - ben_pct:.2f}" '
        f'stroke-dashoffset="{100 - att_pct:.2f}" transform="rotate(-90 80 80)"/>'
        f'<circle cx="80" cy="80" r="60" fill="none" stroke="#FF526F" stroke-width="18" '
        f'pathLength="100" stroke-dasharray="{att_pct:.2f} {100 - att_pct:.2f}" '
        f'stroke-dashoffset="0" transform="rotate(-90 80 80)"/>'
        f'</svg>'
        f'<div class="ds-donut-center">'
        f'<div class="ds-donut-num">{total}</div>'
        f'<div class="ds-donut-lbl">Total Samples</div>'
        f'</div></div>'
        f'<div class="ds-legend">'
        f'<div class="ds-legend-row">'
        f'<span class="ds-legend-k"><span class="ds-legend-sq" style="background:#FF526F"></span>Attack</span>'
        f'<span class="ds-legend-v">{total_attack} ({att_pct:.1f}%)</span>'
        f'</div>'
        f'<div class="ds-legend-row">'
        f'<span class="ds-legend-k"><span class="ds-legend-sq" style="background:#00D6A0"></span>Benign</span>'
        f'<span class="ds-legend-v">{total_benign} ({ben_pct:.1f}%)</span>'
        f'</div>'
        f'</div></div>'
    )


def dataset_files_table_html(files: list[dict]) -> str:
    rows_html = []
    for f in files:
        fname = f["file"]
        items = f["items"]
        rev_count = f["reviewed_count"]
        pct = round(rev_count / items * 100) if items else 0
        src_text = f["sources"]
        src_icon = "globe" if "external" in src_text else "laptop"
        preview_href = f"?page=Datasets&dfile={fname}&daction=preview"
        open_href = f"?page=Datasets&dfile={fname}&daction=open"

        rows_html.append(
            f'<tr>'
            f'<td><span class="dfile-cell"><span class="dfile-ic">{{}}</span><span>{esc(fname)}</span></span></td>'
            f'<td>{items}</td>'
            f'<td>{rev_count} / {items}</td>'
            f'<td><div class="ds-prog-wrap">'
            f'<div class="ds-prog-track"><div class="ds-prog-fill" style="width:{pct}%"></div></div>'
            f'<span class="ds-prog-pct">{pct}%</span>'
            f'</div></td>'
            f'<td><span class="ds-src-pill">{icon(src_icon, 14)}<span>{esc(src_text)}</span></span></td>'
            f'<td><div class="ds-act-group">'
            f'<a class="ds-act-btn" href="{preview_href}" target="_self" title="Preview {esc(fname)}">{icon("eye", 14)}</a>'
            f'<a class="ds-act-btn" href="{open_href}" target="_self" title="Inspect & download {esc(fname)}">{icon("external-link", 14)}</a>'
            f'</div></td>'
            f'</tr>'
        )
    return (
        f'<div class="audit-table-wrap"><table class="ds-files-table">'
        f'<thead><tr>'
        f'<th>File</th><th>Items</th><th>Reviewed</th><th>Review Progress</th><th>Source</th><th>Actions</th>'
        f'</tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        f'</table></div>'
    )


# ---------------------------------------------------------------------------
# Benchmarks Console Builders
# ---------------------------------------------------------------------------
def _parse_rate_cell(cell: str) -> tuple[str, str]:
    """Extract ('0%', '(0/20) overall') from e.g. '0% (0/20, 95% CI 0%–16%)'."""
    pct = cell.split(" ", 1)[0] if cell else "–"
    import re as _re
    m = _re.search(r"\((\d+/\d+)", cell or "")
    frac = f"({m.group(1)}) overall" if m else "overall"
    return pct, frac


def benchmark_agent_section_html(
    title: str,
    source_name: str,
    data: dict,
    rows: list[dict],
    outcomes: list[dict],
) -> str:
    provider = str(data.get("provider", "?"))
    note = str(data.get("note", ""))
    detector = str(data.get("detector", "heuristic"))
    runs = str(data.get("runs", 1))
    is_real = provider != "mock"
    prov_cls = "bm-pill-real" if is_real else "bm-pill-sim"
    prov_text = f"Provider: {provider} ({note})" if note else f"Provider: {provider}"

    all_row = next((r for r in rows if r["language"] == "all"), rows[0] if rows else {})
    att_pct, att_frac = _parse_rate_cell(all_row.get("attack success WITH AgentShield", ""))
    ben_pct, ben_frac = _parse_rate_cell(all_row.get("benign task done WITH", ""))

    trows_html = []
    for r in rows:
        trows_html.append(
            f'<tr>'
            f'<td>{esc(r["language"])}</td>'
            f'<td>{esc(r["attack success WITHOUT AgentShield"])}</td>'
            f'<td><span class="bm-safe-pill">{esc(r["attack success WITH AgentShield"])}</span></td>'
            f'<td>{esc(r["benign task done WITHOUT"])}</td>'
            f'<td>{esc(r["benign task done WITH"])}</td>'
            f'</tr>'
        )

    outcome_html = ""
    if outcomes:
        # Aggregate actual protected outcome counts from data["rows"]
        totals: dict[str, int] = {}
        for r in data.get("rows", []):
            if r.get("shield") and "outcome" in r:
                out_key = str(r["outcome"])
                totals[out_key] = totals.get(out_key, 0) + 1
        total_cases = sum(totals.values())

        # Canonical order matching the benchmark outcomes
        preferred_order = ["paid", "never tried", "blocked", "not attempted", "held for approval", "attacker paid"]
        ordered_keys = [k for k in preferred_order if k in totals] + [k for k in sorted(totals) if k not in preferred_order]
        palette = ["#8B5CF6", "#A855F7", "#EC4899", "#C084FC", "#38BDF8", "#FF526F"]

        circles_svg = []
        legend_rows = []
        offset_acc = 0.0
        for idx, k in enumerate(ordered_keys):
            cnt = totals[k]
            pct = (cnt / total_cases * 100.0) if total_cases else 0.0
            color = palette[idx % len(palette)]
            circles_svg.append(
                f'<circle cx="80" cy="80" r="58" fill="none" stroke="{color}" stroke-width="20" '
                f'pathLength="100" stroke-dasharray="{pct:.2f} {100.0 - pct:.2f}" '
                f'stroke-dashoffset="{-offset_acc:.2f}" transform="rotate(-90 80 80)"/>'
            )
            offset_acc += pct
            legend_rows.append(
                f'<div class="ds-legend-row">'
                f'<span class="ds-legend-k"><span class="ds-legend-sq" style="background:{color}"></span>'
                f'{esc(k.capitalize())}</span>'
                f'<span class="ds-legend-v">{cnt} ({pct:.1f}%)</span>'
                f'</div>'
            )

        out_table_rows = []
        for o in outcomes:
            is_att = o["item"] == "attack"
            ic_cls = "bm-item-att" if is_att else "bm-item-ben"
            ic_name = "bug" if is_att else "check"
            ic_col = "#FF526F" if is_att else "#00D6A0"
            out_table_rows.append(
                f'<tr>'
                f'<td>{esc(o["language"])}</td>'
                f'<td><span class="bm-item-pill"><span class="bm-item-ic {ic_cls}">{icon(ic_name, 13, ic_col, stroke=2.5)}</span>'
                f'<span>{esc(o["item"])}</span></span></td>'
                f'<td>{esc(o["outcomes with AgentShield"])}</td>'
                f'</tr>'
            )

        outcome_html = (
            f'<div class="bm-out-head">'
            f'<span class="bm-out-title">{icon("workflow", 18, "#C084FC")}'
            f'<span>How each case ended with AgentShield</span></span>'
            f'<span class="bm-out-sub">(held for approval = one human click, not a block)</span>'
            f'</div>'
            f'<div class="bm-outcome-grid">'
            f'<div class="ds-card ds-donut-card" style="min-height:215px">'
            f'<div class="ds-donut-wrap">'
            f'<svg width="156" height="156" viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">'
            f'<circle cx="80" cy="80" r="58" fill="none" stroke="#1E2952" stroke-width="20"/>'
            f'{"".join(circles_svg)}'
            f'</svg>'
            f'<div class="ds-donut-center">'
            f'<div class="ds-donut-num">{total_cases}</div>'
            f'<div class="ds-donut-lbl">Total Cases</div>'
            f'</div></div>'
            f'<div class="ds-legend" style="gap:.65rem">{"".join(legend_rows)}</div>'
            f'</div>'
            f'<div class="bm-table-card"><div class="audit-table-wrap"><table class="bm-table">'
            f'<thead><tr><th>Language</th><th>Item</th><th>Outcomes with AgentShield</th></tr></thead>'
            f'<tbody>{"".join(out_table_rows)}</tbody>'
            f'</table></div></div>'
            f'</div>'
        )

    return (
        f'<div class="bm-section">'
        f'<div class="bm-run-banner">'
        f'<div class="bm-run-ic">{icon("bot", 26, "#D8B4FE")}</div>'
        f'<div><div class="bm-run-title">{esc(title)}</div>'
        f'<div class="bm-pills">'
        f'<span class="bm-pill">{icon("file-text", 13)}<span>Source: {esc(source_name)}</span></span>'
        f'<span class="bm-pill {prov_cls}">{icon("laptop", 13)}<span>{esc(prov_text)}</span></span>'
        f'<span class="bm-pill">{icon("shield", 13)}<span>Detector: {esc(detector)}</span></span>'
        f'<span class="bm-pill">{icon("refresh", 13)}<span>Runs per item: {esc(runs)}</span></span>'
        f'</div></div></div>'
        f'<div class="bm-agent-grid">'
        f'<div class="bm-kpi-stack">'
        f'<div class="bm-sum-card bm-sum-safe">'
        f'<div class="bm-sum-ring bm-sum-ring-safe">{icon("shield-check", 19, "#00D6A0")}</div>'
        f'<div><div class="bm-sum-lbl">Attack Success<span>(WITH AgentShield)</span></div>'
        f'<div class="bm-sum-val">{esc(att_pct)}</div>'
        f'<div class="bm-sum-sub">{esc(att_frac)}</div></div></div>'
        f'<div class="bm-sum-card bm-sum-benign">'
        f'<div class="bm-sum-ring bm-sum-ring-benign">{icon("check", 19, "#C084FC", stroke=2.6)}</div>'
        f'<div><div class="bm-sum-lbl">Benign Success<span>(WITH AgentShield)</span></div>'
        f'<div class="bm-sum-val">{esc(ben_pct)}</div>'
        f'<div class="bm-sum-sub">{esc(ben_frac)}</div></div></div>'
        f'</div>'
        f'<div class="bm-table-card"><div class="audit-table-wrap"><table class="bm-table">'
        f'<thead><tr>'
        f'<th>Language</th>'
        f'<th>Attack success<br>WITHOUT AgentShield</th>'
        f'<th>Attack success<br>WITH AgentShield</th>'
        f'<th>Benign task done<br>WITHOUT</th>'
        f'<th>Benign task done<br>WITH</th>'
        f'</tr></thead>'
        f'<tbody>{"".join(trows_html)}</tbody>'
        f'</table></div></div>'
        f'</div>'
        f'{outcome_html}'
        f'</div>'
    )


def benchmark_detection_section_html(title: str, source_name: str, note: str, dataset_name: str, rows: list[dict]) -> str:
    trows_html = []
    for r in rows:
        trows_html.append(
            f'<tr>'
            f'<td><code>{esc(r["detector"])}</code></td>'
            f'<td>{esc(r["language"])}</td>'
            f'<td><span class="bm-safe-pill">{esc(r["attacks flagged"])}</span></td>'
            f'<td>{esc(r["benign flagged"])}</td>'
            f'</tr>'
        )
    return (
        f'<div class="bm-section bm-section-det">'
        f'<div class="bm-run-banner">'
        f'<div class="bm-run-ic">{icon("shield-check", 25, "#D8B4FE")}</div>'
        f'<div><div class="bm-run-title">{esc(title)}</div>'
        f'<div class="bm-pills">'
        f'<span class="bm-pill">{icon("file-text", 13)}<span>Source: {esc(source_name)}</span></span>'
        f'<span class="bm-pill">{icon("database", 13)}<span>Dataset: {esc(dataset_name)}</span></span>'
        f'<span class="bm-pill">{icon("activity", 13)}<span>{esc(note)}</span></span>'
        f'</div></div></div>'
        f'<div class="bm-table-card"><div class="audit-table-wrap"><table class="bm-table">'
        f'<thead><tr><th>Detector</th><th>Language</th><th>Attacks Flagged</th><th>Benign Flagged (False Positive)</th></tr></thead>'
        f'<tbody>{"".join(trows_html)}</tbody>'
        f'</table></div></div>'
        f'</div>'
    )


def benchmark_chart_header_html(
    legend_items: list[tuple[str, str]] | None = None,
    title: str = "Attack Detection by Language",
    sub: str = "Comparison of attack detection performance across languages and detectors.",
) -> str:
    legend_html = ""
    if legend_items:
        chips = "".join(
            f'<span class="bm-leg-item">'
            f'<span class="bm-leg-dot" style="background:{esc(color)};box-shadow:0 0 8px {esc(color)}88"></span>'
            f'<span>{esc(label)}</span></span>'
            for label, color in legend_items
        )
        legend_html = f'<div class="bm-chart-legend">{chips}</div>'
    return (
        f'<div class="bm-chart-head">'
        f'<div class="bm-chart-head-left">'
        f'<div class="bm-chart-ic">{icon("chart", 19, "#D8B4FE")}</div>'
        f'<div><div class="bm-chart-title">{esc(title)}</div>'
        f'<div class="bm-chart-sub">{esc(sub)}</div></div>'
        f'</div>{legend_html}</div>'
    )




