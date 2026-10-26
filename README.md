# AgentShield

**Runtime security gateway for AI agents.** AgentShield checks every tool call an agent wants to make before it runs, and blocks actions the user never asked for, especially ones triggered by hidden instructions in Bangla, Banglish or English inside untrusted data (emails, web pages, files).

> Status: Phase 2 (core) working; classifier and benchmark in progress. Benchmark results: TBD.

## See the attack, then see it stopped
```powershell
python -m demo_agent.run                    # agent reads a Bangla phishing email and sends money
python -m demo_agent.run --shield           # same agent, protected by AgentShield: blocked
python -m demo_agent.run --compare --all    # all 11 scenarios (5 benign, 6 attacks), side by side
```
By default this runs on the offline mock LLM, which simulates a naive agent that obeys instructions found in tool output. Add `--provider groq` to use the real model configured in `.env`.

## Dashboard
```powershell
streamlit run dashboard/app.py
```
Opens in the browser. Pick a scenario and press **Run scenario**: the left column runs the unprotected agent, the right column runs the same agent protected by AgentShield. The **Audit log** tab lists every decision.

## Docs
- [Architecture](docs/architecture.md)
- [Business model and global readiness](docs/business_model.md)
- [Real-world impact and ethical AI](docs/ethics_impact.md)

## How it works (planned)
Every tool call passes four checks:
1. **Taint tracking**: where did the data that triggered this call come from?
2. **Injection classifier**: does the data contain an injection attempt (EN / BN / Banglish)?
3. **Intent check**: does this action follow from what the user actually asked?
4. **Policy engine**: deterministic YAML rules (limits, allowed recipients).

Result: **ALLOW / ASK_HUMAN / BLOCK** with a reason in English and Bangla, written to an audit log.

## Setup (Windows PowerShell)
```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env    # then edit .env yourself
pytest
```

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
