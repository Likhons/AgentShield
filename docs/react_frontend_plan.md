# React frontend: plan (branch `react-frontend`)

> Experiment. `main` keeps the Streamlit dashboard and the live demo (Streamlit Cloud deploys `main`).
> If the React version is not ready in time, this branch is simply not merged.

## Goal
Same five pages as the Streamlit dashboard (Playground, Benchmarks, Audit Log, Policies, Datasets),
rebuilt in React, talking to the existing Python code through an HTTP API. AgentShield core is not touched.

## Stack
| Part | Choice | Why |
|---|---|---|
| Frontend | React + Vite + TypeScript | Dashboard, no SEO or server rendering needed; static build |
| Routing | React Router | Five pages |
| Styling | Tailwind CSS | Port the colours and cards from `dashboard/ui.py` |
| Charts | Recharts | Bar + donut charts |
| Data | TanStack Query | API calls, loading states, caching |
| Backend | FastAPI (`webapi/`) | Reuses demo_agent, benchmark, audit log as they are |
| Hosting | Vercel (frontend) + Render or HF Spaces (backend) | Free tiers; SQLite audit log needs a real disk |

## Folders
```
webapi/          FastAPI app for the dashboard (new). Mounts the existing gateway (/v1/check, /v1/audit, /v1/stats)
                 and adds read-only dashboard endpoints plus the demo scenario runner.
web/             React app (new)
dashboard/       Streamlit, unchanged
agentshield/     core library, unchanged
```
`webapi/` lives outside `agentshield/` on purpose: it imports `demo_agent` and `benchmark`, which the
library itself must not depend on.

## API (`uvicorn webapi.app:build_app --factory --reload --port 8000`, docs at /docs)
| Endpoint | Page | Returns |
|---|---|---|
| `GET /api/overview` | sidebar, KPIs | version, provider, detector, checks, rule count, decisions logged, attack samples per language, newest real-LLM attack numbers |
| `GET /api/scenarios` | Playground | scenario list (name, attack/benign, description, has recording) |
| `POST /api/scenarios/{name}/run` | Playground | without + with AgentShield: money outcome, steps with verdicts (EN/BN reasons, per-check scores), final answer, summary banner |
| `GET /api/audit` | Audit Log | filtered, paginated records + counts (decision, search, tool, tainted, min risk, since) |
| `GET /api/audit/{id}` | Audit Log drawer | one record |
| `GET /api/audit.csv` | Audit Log export | CSV, UTF-8 with BOM (same columns as Streamlit) |
| `GET /api/benchmarks` | Benchmarks | the four sections the Streamlit page shows (rows, outcomes, chart data) |
| `GET /api/policies` | Policies | rules from `default.yaml` + decision thresholds |
| `GET /api/datasets` | Datasets | language summary + file list (items, reviewed, sources) |
| `GET /api/datasets/{file}` | Datasets preview | first N records of one file |

Numbers come only from the same sources as Streamlit (`benchmark/results/`, audit DB, datasets).

## Steps (one commit each)
1. `webapi/` with the endpoints above + tests.
2. Scaffold `web/` (Vite, TS, Tailwind, Router, Query), theme tokens, layout (sidebar, mobile drawer).
3. Playground (hero, KPIs, scenario runner, side-by-side result, pipeline, recent evaluations).
4. Audit Log (filters, pagination, drawer, CSV).
5. Benchmarks, Policies, Datasets.
6. Responsive pass at 390 / 820 / 1440 px (Playwright screenshots).
7. Deploy: backend first, then Vercel with `/api/*` rewrite to the backend.
8. Decide: merge into `main` and switch the live link, or keep Streamlit.

## Open points for the user
- Datasets preview shows record text, including `attacks.jsonl`. The Streamlit live demo already does this;
  `docs/ethics_impact.md` says the attack set is shared on request. Decide before deploying either version publicly.
- Live (Groq) mode on a public backend spends the free-tier token budget. Default: off unless a key is set.
