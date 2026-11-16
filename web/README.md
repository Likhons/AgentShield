# AgentShield web (React)

React frontend for the AgentShield dashboard (branch `react-frontend`, plan in `../docs/react_frontend_plan.md`).
The Streamlit dashboard in `../dashboard/` stays the live demo until this is ready.

Stack: React 19 + Vite + TypeScript, Tailwind CSS 4, React Router, TanStack Query, Recharts, Lucide icons.

## Run locally (two terminals)

```powershell
# 1) API (repo root, venv active)
uvicorn webapi.app:build_app --factory --port 8000

# 2) frontend
cd web
npm install
npm run dev        # http://localhost:5173  (proxies /api to port 8000)
```

`npm run build` type-checks and builds to `dist/`; `npm run lint` runs oxlint.
Point the dev proxy elsewhere with `AGENTSHIELD_API=http://host:port npm run dev`.
