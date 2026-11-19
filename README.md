# AgentShield

**Runtime security gateway for AI agents.** AgentShield checks every tool call an agent wants to make before it runs, and blocks actions the user never asked for, especially ones triggered by hidden instructions in Bangla, Banglish or English inside untrusted data (emails, web pages, files).

> Status: core working end to end; benchmarks done for the preliminary submission. Live demos: web dashboard https://agent-shield-demo.vercel.app (the API sleeps on Render's free tier: the first request can take about 50 s) and the first Streamlit version https://agentshield-demo.streamlit.app. All numbers, sources and caveats: [docs/results.md](docs/results.md).

## Results (measured, small samples, 95% intervals in docs/results.md)
- **Real LLM agent** (qwen3.8-27b via Groq, 20 Bangla/Banglish attacks + 20 normal bill payments, 1 run each): attacks moved money in **4 of 20** cases without AgentShield and **0 of 20** with it. The landlord's real rent was paid in **16 of 20** cases both without and with AgentShield: it blocked every attacker payment and held no legitimate one.
- **Existing guardrail:** Meta Prompt Guard 2 flagged **0 of 24** Bangla/Banglish prompt-injection attacks (and 1 of 40 subtle English agent injections).
- **Simulated agent** (full dataset): attacks succeeded 22 of 60 times without AgentShield and **0 of 60** with it; rent paid 175 of 175 both ways.
- **Network check, simulated wallet** (600 users, one week; weights set on the same data, so this shows the method, not accuracy): looking across users cut the money reaching scammers from 334,300 to **96,000 BDT** and flagged **0 of 1,109** real accounts. It catches phone scams where the victim types the number in, which no single-call check can tell apart from a real request.

## See the attack, then see it stopped
```powershell
python -m demo_agent.run                    # agent reads a Bangla phishing email and sends money
python -m demo_agent.run --shield           # same agent, protected by AgentShield: blocked
python -m demo_agent.run --compare --all    # all 14 scenarios (6 benign, 8 attacks), side by side
```
By default this runs on the offline mock LLM, which simulates a naive agent that obeys instructions found in tool output. Add `--provider groq` to use the real model configured in `.env`.

## Dashboard
Web dashboard (React): the API and the site run separately.
```powershell
uvicorn webapi.app:build_app --factory --port 8000   # dashboard API
cd web; npm install; npm run dev                      # site on http://localhost:5173
```
On **Playground**, pick a scenario and run it: the left column runs the unprotected agent, the right column runs the same agent protected by AgentShield. The sidebar has **Benchmarks** (measured results), **Audit Log** (every decision), **Policies**, **Datasets** and **Network** (the cross-user check on a simulated wallet week).

The first version, in Streamlit, has the same pages except Network:
```powershell
streamlit run dashboard/app.py
```

## HTTP gateway (any language, any framework)
```powershell
uvicorn agentshield.api.app:create_app --factory --port 8000
```
Open http://localhost:8000/docs for the interactive API. Before every tool call, `POST /v1/check` with the user's request, the tool call and the labeled context; the answer is ALLOW / ASK_HUMAN / BLOCK with reasons. `GET /v1/audit` and `GET /v1/stats` return the decision log. Set `AGENTSHIELD_API_KEY` in `.env` to require an `X-API-Key` header.

## Benchmark
```powershell
python -m benchmark.dataset                                                    # validate data
python -m benchmark.run_detection --detectors heuristic,promptguard-86m,promptguard-22m
python -m benchmark.run_agent --languages bn,banglish                          # simulated agent
python -m benchmark.run_agent --provider groq --runs 1 --languages bn,banglish # real LLM (slow)
python -m benchmark.network --save                                            # simulated wallet, network check
```

## Docs
- [Measured results](docs/results.md)
- [Pitch and demo script](docs/pitch.md)
- [Putting the dashboard online](docs/deploy.md)
- [Architecture](docs/architecture.md)
- [Business model and global readiness](docs/business_model.md)
- [Real-world impact and ethical AI](docs/ethics_impact.md)

## How it works
Every tool call passes four checks before it runs:
1. **Taint tracking**: where did the data that triggered this call come from?
2. **Injection classifier**: does the data contain an injection attempt (EN / BN / Banglish)?
3. **Intent check**: does this action follow from what the user actually asked?
4. **Policy engine**: deterministic YAML rules (limits, allowed recipients).

Result: **ALLOW / ASK_HUMAN / BLOCK** with a reason in English and Bangla, written to an audit log. Protect any agent's tools in two lines:
```python
session = ShieldSession(engine, user_request=task, known_recipients=contacts)
send_money = session.wrap("send_money", send_money, source="tool:bank")
```

## Setup (Windows PowerShell)
```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env    # then edit .env yourself
pytest
```
The same tests run automatically on GitHub for every push (`.github/workflows/tests.yml`, Python 3.13 and 3.14, no secrets needed).

## Repo layout
| Folder | Purpose |
|---|---|
| `agentshield/` | The gateway: core, checks, llm, audit, api, sdk |
| `demo_agent/` | Vulnerable mock banking agent (fake MockPay wallet) |
| `datasets/` | Labeled attack + benign prompts |
| `benchmark/` | Evaluation runners and metrics; `network.py` simulates a wallet week for the network check |
| `training/` | Kaggle notebook for the classifier |
| `dashboard/` | Streamlit demo + audit view (first version) |
| `webapi/` | Dashboard API for the web dashboard (FastAPI) |
| `web/` | Web dashboard (React, TypeScript, Vite, Tailwind) |
| `policies/` | Policy rules (YAML) |
| `tests/` | pytest tests |
| `docs/` | Architecture, results, pitch notes |

## Ethics
All accounts, names, numbers and money are fake. Attack data exists only to test and improve defenses.
