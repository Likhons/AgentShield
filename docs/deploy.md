# Putting the dashboard online (free)

> Status (19 Nov 2026): the live demo is the React site https://agent-shield-demo.vercel.app (Vercel) with its API at https://agentshield-api-k60w.onrender.com (Render, free, Singapore), live since 16 Nov. See "React frontend" below.
> The first version, in Streamlit, is no longer online (removed 19 Nov); it runs locally with `streamlit run dashboard/app.py`, and Option 1 below shows how to put it online again.
> Publishing makes the demo reachable by anyone with the link: decide first what may be public (see "Before you publish").

## Before you publish
- **Secrets never go into the repo.** API keys (`GROQ_API_KEY`) go into the platform's secret settings. Without a key the dashboard still works in `mock` and `recorded (groq)` mode.
- **Default to offline modes.** For a public link, use `LLM_PROVIDER=mock` and the recorded real runs; a live `groq` button would spend the free-tier quota for every visitor.
- **What becomes visible:** the demo emails in `demo_agent/data/` (including the fake attack emails), the recordings and the benchmark tables.
- **Team-written attack texts (`datasets/attacks.jsonl`).** `docs/ethics_impact.md` says they are shared with researchers on request, not published.
  - The React version keeps them private by default: counts are shown, texts and download are not (`SHOW_ATTACK_TEXTS=1` turns them on).
  - The Streamlit Datasets page does the same since 16 Nov: counts, languages and labels; no texts, no download.
  - A platform that publishes the repo's files (a public Hugging Face Space, a public GitHub repo) publishes the file itself, whatever the dashboard shows.
- Record the stage demo first (`python -m demo_agent.run --all --compare --provider groq --record`) and commit `demo_agent/recordings/`.

## Option 1: Streamlit Community Cloud
1. Sign in at https://share.streamlit.io with the GitHub account that owns the repo.
2. *Create app* → choose the repo, branch `main`, main file `dashboard/app.py`.
3. *Advanced settings*: Python 3.12 or newer; secrets, if any, in TOML form, for example `LLM_PROVIDER = "mock"`.
4. Deploy. The app installs `requirements.txt` automatically.
5. Check on the platform's current docs whether private repositories are allowed on your plan before relying on it.

## Option 2: Hugging Face Spaces
1. Create a new Space at https://huggingface.co/new-space (free CPU hardware). Pick the Streamlit option if offered; otherwise the Docker option with a Streamlit template.
2. Push this repo's code to the Space (or connect it), with `dashboard/app.py` as the app file.
3. Add secrets under *Settings → Variables and secrets* (`LLM_PROVIDER=mock`; add `GROQ_API_KEY` only if live mode is wanted).
4. A Space can be private; a public Space is visible to everyone, including its files.

## After deploying
- Open the link in a private browser window and run `attack_bill_bn` in Offline and Recorded mode.
- Open every sidebar page (Benchmarks, Audit Log, Policies, Datasets).
- Live (Groq) needs `GROQ_API_KEY` in the secrets; without it the dashboard shows a clear "LLM error" and Offline keeps working.
- Never paste the key into a public file or issue; rotate it at https://console.groq.com/keys if it ever leaks.

---

## React frontend (branch `react-frontend`): Render + Vercel

```
browser ──> Vercel (static React app, web/)
              └─ /api/*  rewrite ──> Render (FastAPI, webapi/) ──> agentshield, demo_agent, benchmark readers
```
The browser only talks to Vercel; Vercel forwards `/api/*` to Render, so there is no CORS setup.
Render builds from the private GitHub repo, so dataset files are not published; only the API answers.
Check each platform's current free-tier terms when you sign up (limits, and whether a card is asked for).

### Files
| File | What it does |
|---|---|
| `render.yaml` | Render Blueprint: free web service `agentshield-api`, Singapore, branch `react-frontend`, `LLM_PROVIDER=mock`, a generated `AGENTSHIELD_API_KEY` for the raw gateway (`/v1/*`) |
| `requirements-api.txt` | Only the API's packages (no Streamlit, no torch), pinned to versions tested on Python 3.13.16 |
| `web/vercel.json` | Rewrites `/api/*` and `/health` to the Render service (https://agentshield-api-k60w.onrender.com); every other path serves the React app |

### 1. Backend on Render
1. The branch must be on GitHub first (`git push -u origin react-frontend`).
2. Sign in at https://render.com with GitHub and allow access to the `AgentShield` repository.
3. *New* → *Blueprint* → pick the repository. Render reads `render.yaml`; confirm with *Apply*.
4. Wait for the first build (a few minutes). Then open `https://agentshield-api-k60w.onrender.com/health` (Render adds a suffix such as `-k60w` when the plain name is taken): it must show `{"status":"ok"}`.
   - If Render gave the service a different address (the name was taken), copy that address into both lines of `web/vercel.json`, commit and push.
   - If the build stops at the Python version, change `PYTHON_VERSION` in Render → *Environment* to a 3.13 version Render lists, then *Manual Deploy*.
5. Open `…/api/overview`: it should list 104 attack samples and the real-LLM result (0/20 with, 4/20 without).

### 2. Frontend on Vercel
1. Sign in at https://vercel.com with GitHub. *Add New* → *Project* → import `AgentShield`.
2. *Root Directory*: `web`. Vercel detects Vite; keep `npm run build` and the output folder `dist`.
3. `main` has no `web/` folder, so a build from `main` fails. Before (or right after) the first deploy: *Settings* → *Git* → *Production Branch* = `react-frontend`, then *Deployments* → *Redeploy*.
   (Branch preview addresses may be login-protected; the production address is the public one.)
4. The production address looks like `https://agentshield-….vercel.app`. A nicer free name can be set under *Settings* → *Domains* if it is free.
5. What actually happened on 16 Nov: the Root Directory picker only lists `main`'s folders (no `web/`). Import with preset **Vite** and root `./` (the first build fails), then *Settings* → *Build and Deployment* → Root Directory `web`, *Environments* → *Production* → Branch Tracking `react-frontend`, and push any commit to the branch. If the address asks for a Vercel login, turn off *Settings* → *Deployment Protection* → *Vercel Authentication* for production.

### 3. Check (private browser window and a phone)
- Playground: run the Bangla email attack in *Offline* (5,000 vs 0), then the Bangla fake bill in *Recorded Run* (4,500 vs 0, rent 8,000 allowed).
- Benchmarks, Audit Log (open one event), Policies (*Add Policy* → *Validate*), Datasets: `attacks.jsonl` → *Inspect* shows "hidden" and no download button.
- Reload a deep link such as `/benchmarks`: the page must load (SPA rewrite).

### Good to know
- **Sleep:** the free Render service sleeps after 15 minutes without requests; the next request waits about a minute, and the first page load may show an error until it is awake. Before a demo, open the site (or `/health`) two minutes early.
- **Audit log resets** when Render restarts or redeploys (no disk on the free plan), like Streamlit Cloud.
- **Live (Groq)** turns on when `GROQ_API_KEY` is set in Render → *Environment* (the key never goes into a file; `render.yaml` sets the models). Visitors then spend the account's free-tier quota, so the API allows one live run at a time and `LIVE_RUNS_PER_HOUR` (20) per hour; above that it asks for Recorded Run. A real-model run can take up to a minute.
- **Raw gateway:** `/v1/check`, `/v1/audit`, `/v1/stats` need the `X-API-Key` header; the key is under Render → *Environment*. Interactive API docs: `https://agentshield-api-k60w.onrender.com/docs`.
- **Rollback:** revert the commit on `react-frontend` and push; Vercel and Render redeploy the previous code.
