# AgentShield

**Runtime security gateway for AI agents.** AgentShield checks every tool call an agent wants to make before it runs, and blocks actions the user never asked for, especially ones triggered by hidden instructions in Bangla, Banglish or English inside untrusted data (emails, web pages, files).

> Status: early development (Phase 1: vulnerable demo agent). Results: TBD.

## See the attack (no AgentShield yet)
```powershell
python -m demo_agent.run          # agent reads a Bangla phishing email and sends money
python -m demo_agent.run --all    # all 9 scenarios (4 benign, 5 attacks)
```
This runs on the offline mock LLM, which simulates a naive agent that obeys instructions found in tool output.

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
