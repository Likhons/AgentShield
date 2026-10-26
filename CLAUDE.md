# AgentShield: context for Claude Code sessions

> Read this file first in every session. Keep it updated at the end of every phase.

## Current phase
**Phase 1: Vulnerable demo agent, done.** Waiting for the user to say "next" before starting Phase 2.

## What exists so far
- `agentshield/config.py`: settings from `.env` (defaults to mock).
- `agentshield/llm/`: `LLMProvider` interface (`generate(messages) -> str`), `Message` model, providers `mock` / `gemini` / `groq` (plain `httpx` REST, no vendor SDKs), factory `get_provider()`.
  - `mock.py` imitates a *naive* agent model: plans tools from task keywords and **obeys money instructions found in tool output** (repeatable worst case). Has `find_money_order()` (EN/BN/Banglish, Bangla digits, NFC normalization).
- `demo_agent/`: `tools.py` (`MockPayWorld` with 6 tools; each `ToolSpec` has a `source` taint label like `tool:email`), `agent.py` (`BankingAgent` think→act→observe loop, JSON action protocol, **no security check in `execute()`**: this is where AgentShield hooks in), `scenarios.py` (load data, `judge_outcome`: a transfer is unauthorized if its recipient is not in the user's request), `run.py` (CLI).
- `demo_agent/data/`: `account.json`, `emails.json` (e1–e3 normal, e10–e12 attacks EN/BN/Banglish), `web_pages.json`, `files.json`, `scenarios.json` (4 benign + 5 attack scenarios).
- Fake phone numbers use prefix `010` (not used by any Bangladeshi operator); email domains use `.example`.
- Agent protocol: LLM replies `{"action":"tool","tool":...,"args":{...}}` or `{"action":"final","answer":...}`.

## Project summary
AgentShield is a **runtime security gateway for AI agents**. It checks every tool call an agent wants to make *before* it runs, and blocks actions the user never asked for. The focus is actions triggered by hidden instructions in **Bangla, Banglish or English** inside untrusted data (emails, web pages, files), i.e. *indirect prompt injection*.

Claim: **"first agent-action security for Bangla"** (NOT "first Bangla guardrail").

Positioning (verify citations before putting them in the pitch):
- BanglaVeilGuard (BRAC University, Aug 2026, arXiv 2608.21880): Bangla/Banglish safety benchmark + guard, single-turn chat only, no agents/tools, high over-refusal (~39–44% of benign prompts blocked).
- LlamaFirewall (Meta, 2025, arXiv 2505.03574): agent guardrail with AlignmentCheck, English-focused.
- Our gap: Bangla/Banglish indirect injection inside agent workflows, defended at the action level, with low over-refusal.

Design principle: **"AI where judgment is needed, deterministic rules where certainty is needed."**

## Competition
International AI Builders Congress 2026 (CloudCamp Bangladesh), "Idea to Unicorn". Domain InfraSphere AI, challenges SecureAI + AgentOps.
- Preliminary submission: **20 Nov 2026**. Final: **26 Dec 2026**, Dhaka (3-min pitch + live demo).
- Judging: Innovation 20, Technical Execution 20, Business + Global Readiness 20, Real-World Impact + Ethical AI 20, Scalability + NRB collaboration 10, Presentation 10.
- Point out which criterion a technical decision helps.

## Architecture
Every tool call → four checks → combined risk score → **ALLOW / ASK_HUMAN / BLOCK** with a plain-language reason (English + Bangla) → SQLite audit log → dashboard.

1. **Taint tracking** (deterministic): every piece of context is labeled by source (`user`, `system`, `tool:email`, `tool:web`, `tool:file`...). Calls triggered by / with arguments from untrusted sources get higher risk.
2. **Injection classifier** (ML): EN/BN/Banglish. Heuristic baseline first, behind a clean interface; later fine-tuned BanglaBERT or XLM-R (trained on Kaggle, CPU inference locally).
3. **Intent check** (LLM-as-judge): "User asked X, agent wants tool Y with args Z. Does Y follow from X?" → verdict + reason. Only called when cheaper checks flag risk.
4. **Policy engine** (YAML rules): e.g. transfers > 10,000 BDT need human approval; no data to unknown external recipients; sensitive tools need user-origin intent.

The latency of every check is measured.

## Repo layout
```
agentshield/       # the product (installable package)
  core/            # decision engine, risk scoring, pydantic models
  checks/          # taint.py, classifier.py, intent.py, policy.py
  llm/             # provider abstraction: gemini, groq, mock
  audit/           # SQLite audit log
  api/             # FastAPI gateway service
  sdk/             # 2-line wrapper to protect any agent's tools
demo_agent/        # vulnerable mock banking agent (MockPay wallet)
  data/            # fake emails, web pages, accounts (JSON)
datasets/          # attack + benign prompts (EN/BN/Banglish), labeled
benchmark/         # runner + metrics + baselines
training/          # Kaggle notebook for the classifier
dashboard/         # Streamlit app
policies/          # default.yaml
tests/             # pytest
docs/              # architecture.md, results.md, pitch notes
```

## Constraints
- User machine: Windows 11, PowerShell, 8 GB RAM, no GPU. **No local LLMs, no local training.** Keep dependencies light.
- Python 3.14.2 venv at `.venv`. Python 3.13 is also installed (`py -3.13`) as a fallback if an AI library has no 3.14 wheels.
- Budget zero: Gemini free tier (primary), Groq free tier (backup), Kaggle GPU for training, HF Spaces / Streamlit Cloud for hosting.
- LLM provider + model come from `.env` (`LLM_PROVIDER`, `LLM_MODEL`). Never hardcode model names. `mock` provider is deterministic so everything runs without keys.
- All data is fake: "MockPay" wallet, fake names/numbers/emails. No real brands.
- Defensive research only: attack data stays in this repo, fake targets only.

## Working rules
- Talk to the user in **simple Bangla**; code, comments, file names and docs in **English**.
- User knows basic/intermediate Python: explain what each important piece does and why, briefly.
- After each phase: stop, Bangla summary, exact PowerShell commands + expected output, wait for "next".
- Never ask for API keys in chat. Keys go in `.env` (git-ignored); `.env.example` has placeholders.
- **Never invent results.** Numbers in docs/README/pitch come from real runs, otherwise "TBD".
- Simple readable code, type hints, docstrings, small functions. pytest tests for every check + end-to-end scenario.
- Commit after each phase. Disagree openly (with reasons) before changing the plan.
- Priority if slipping: side-by-side demo > honest benchmark > trained classifier > dashboard polish > stretch.

## Phase plan
- Phase 0: Setup (27 Oct): done
- Phase 1: Vulnerable demo agent on mock LLM (27 Oct): done
- Phase 2: AgentShield core v1 (by ~5 Nov)
- Phase 3: Datasets + baseline benchmark (by ~9 Nov)
- Phase 4: Classifier training on Kaggle (by ~13 Nov)
- Phase 5: Dashboard + demo (by ~16 Nov)
- Phase 6: Polish + submission material (by 19 Nov, buffer 20 Nov)

See PROGRESS.md for the detailed checklist.

## Commands
```powershell
.\.venv\Scripts\Activate.ps1      # activate venv
pip install -r requirements.txt   # install deps
pytest                            # run tests
python -m demo_agent.run          # Bangla email attack, unprotected agent
python -m demo_agent.run --all    # all scenarios + summary
python -m demo_agent.run --list
```
