# AgentShield

**Runtime security gateway for AI agents.** AgentShield checks every tool call an agent wants to make before it runs, and blocks actions the user never asked for, especially ones triggered by hidden instructions in Bangla, Banglish or English inside untrusted data (emails, web pages, files).

> Status: core working end to end; benchmark in progress (Phase 3). All numbers: [docs/results.md](docs/results.md).

## Results so far (measured, small samples)
- Meta Prompt Guard 2 flagged **0 of 24** Bangla/Banglish prompt-injection attacks (and 1 of 40 subtle English agent injections).
- On a simulated agent, Bangla/Banglish attacks moved money in 11 of 20 cases without AgentShield and **0 of 20** with it, while the user's real rent payment still went through in **135 of 135** benign cases.
- Real-LLM agent results: TBD. Details, sources and caveats in [docs/results.md](docs/results.md).

## See the attack, then see it stopped
```powershell
python -m demo_agent.run                    # agent reads a Bangla phishing email and sends money
python -m demo_agent.run --shield           # same agent, protected by AgentShield: blocked
python -m demo_agent.run --compare --all    # all 14 scenarios (6 benign, 8 attacks), side by side
```
By default this runs on the offline mock LLM, which simulates a naive agent that obeys instructions found in tool output. Add `--provider groq` to use the real model configured in `.env`.

## Dashboard
```powershell
streamlit run dashboard/app.py
```
Opens in the browser. Pick a scenario and press **Run scenario**: the left column runs the unprotected agent, the right column runs the same agent protected by AgentShield. The **Audit log** tab lists every decision; the **Benchmark** tab shows the latest measured results.

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
| `benchmark/` | Evaluation runner and metrics |
| `training/` | Kaggle notebook for the classifier |
| `dashboard/` | Streamlit demo + audit view |
| `policies/` | Policy rules (YAML) |
| `tests/` | pytest tests |
| `docs/` | Architecture, results, pitch notes |

## Ethics
All accounts, names, numbers and money are fake. Attack data exists only to test and improve defenses.
