# AgentShield: context for Claude Code sessions

> Read this first. Keep it short and current; details live in PROGRESS.md and the code.

## RESUME HERE (last updated 27 Oct 2026)
- **Phase:** 3 (datasets + benchmark) nearly done, ahead of schedule (deadline ~9 Nov). Phases 0–2 done. Phase 4 notebook ready.
- **Done 27 Oct:** `datasets/attacks.jsonl` (24 BN/Banglish, reviewed). Text benchmark: Prompt Guard 2 flags 0/24. Simulated agent: 0/20 attacks succeed with AgentShield. `docs/results.md` drafted; dashboard Benchmark tab live.
- **Real-Groq agent run done** (`agent_20261027-153825`): attacks 4/20 → 0/20, but legit rent 17/20 → 0/20 (all held for approval). Cause: gpt-oss-120b judge can't see that the recipient is a saved contact. **Fix A postponed by the user (do later, together with classifier scope B)**: user adds "recipient is a saved contact: yes/no" (from `known_recipients`) to `build_messages()` in `checks/intent.py` + one prompt sentence; Claude explains step by step, then re-runs `python -m benchmark.run_agent --provider groq --runs 1 --languages bn,banglish --limit 10` (balanced now) and records before/after in docs/results.md §3b.
- **After the fix:** record the stage demo once: `python -m demo_agent.run --all --compare --provider groq --record` (dashboard option "recorded (groq)" replays it instantly; recordings in `demo_agent/recordings/groq/`).
- GitHub is up to date as of `d15133d` (pushed 27 Oct); ask the user before pushing again.
- **Open user tasks:** read all 135 items in `datasets/benign.jsonl` (then `reviewed=yes`); add ~15 own hand-written benign items per language (BN/Banglish) in `datasets/benign_own.jsonl` (removes bias, see below); ideally a few hand-written attacks too.
- **Next:** decide classifier scope (Open decisions); Phase 4 = user runs `training/train_classifier.ipynb` on Kaggle (instructions inside), then a model-backed detector + benchmark on test-split ids only (`split_ids.json`).
- **Claude-side work is caught up** (27 Oct): gateway, mixed-inbox experiment, record/replay, `docs/pitch.md`, `docs/deploy.md`. Everything left depends on the user: fix A + scope B (their files), own benign items, Kaggle run, publish decision. After A+B: re-run real Groq benchmark, record the demo, update results.md/pitch.md numbers.

## How we work (important)
- Talk to the user in **simple Bangla**; code, comments, files, docs in **English**. User knows basic/intermediate Python; explain briefly what and why. Give exact PowerShell commands. One step at a time when the user asks for it.
- **Division of work:** the user writes AgentShield core files (`agentshield/core`, `checks`, `audit`, `sdk`) and their tests; Claude explains beforehand, reviews, probes (demo data + real Groq), and commits. Claude owns demo_agent, llm, dashboard, benchmark plumbing, docs.
- **Claude does not write prompt-injection attack texts or injection signal/phrase lists.** The user writes `attacks.jsonl` and classifier signals. Claude may write benign data, tooling, metrics.
- User-pasted code: ask them to save it in VS Code themselves (Claude then reads from disk). Very long attack-pattern files must be saved by the user.
- **Only one AI tool should edit this repo at a time** (another tool once produced files elsewhere that never reached this folder).
- Never invent results; numbers only from `benchmark/results/` or real runs, else "TBD". Label mock results as simulation. n=1 runs are anecdotes.
- Never ask for API keys in chat. `.env` lines Claude may edit: LLM_PROVIDER, LLM_MODEL, JUDGE_MODEL (never key lines).
- Commit after each step with a clear message. Disagree openly before changing the plan.
- Priority if slipping: side-by-side demo > honest benchmark > trained classifier > dashboard polish > stretch.

## Project
Runtime security gateway for AI agents: checks every tool call **before** it runs and stops actions the user never asked for, especially ones triggered by hidden instructions in **Bangla, Banglish or English** inside emails, web pages, files (indirect prompt injection). Claim: "first agent-action security for Bangla" (NOT "first Bangla guardrail"). Principle: **"AI where judgment is needed, deterministic rules where certainty is needed."**

Competition: International AI Builders Congress 2026 (CloudCamp Bangladesh), "Idea to Unicorn", SecureAI + AgentOps. Preliminary submission **20 Nov 2026**; final **26 Dec 2026** Dhaka (3-min pitch + live demo). Judging: Innovation 20, Technical Execution 20, Business + Global 20, Impact + Ethical AI 20, Scalability + NRB 10, Presentation 10.

Positioning (verify citations before the pitch; Claude could not verify BanglaVeilGuard): BanglaVeilGuard (arXiv 2608.21880, single-turn chat, reported ~39–44% over-refusal), LlamaFirewall (arXiv 2505.03574, English-focused).

## Architecture (all built)
Tool call → taint, classifier, intent (LLM, only if needed), policy → score `taint*0.3 + classifier*0.3 + intent*0.4` (weights NOT re-normalized when a check is skipped) → stricter of score decision (ask ≥0.4, block ≥0.75) and policy's forced decision → ALLOW / ASK_HUMAN / BLOCK + reason EN/BN → SQLite audit.
- `core/models.py` (user): SourceType (tool:bank trusted, tool output never user), GuardRequest (`known_recipients`, fail-safe `is_tainted`), CheckResult (`skipped`, `forced_decision`), Verdict (`llm_called`), AuditRecord, DatasetSample. `core/text.py`: NFC, Bangla digits, `detect_language` (misses some Banglish; only used for classifier details).
- `checks/policy.py` + `policies/default.yaml` (user): tainted transfer to stranger → block; unknown recipient not typed by user → ask_human; amount > 10,000 → ask_human; whole-number matching.
- `checks/taint.py` (user): per-argument provenance (user / tool_data+item / unknown).
- `checks/intent.py` (user): judge sees only user request + tool call, never tool-output text; errors → 0.5 fail-safe. Mock has a keyword judge mode (offline).
- `checks/classifier.py` (user): heuristic `Detector.predict(text)` behind a swappable protocol; Phase 4 model replaces it.
- `core/engine.py` (user): crashing check → ask_human; calm ALLOW explanation. `audit/log.py` (user): SQLite, `?` placeholders. `sdk/session.py` (user): `ShieldSession.wrap(name, func, source)`.
- `llm/` (Claude): mock / groq / gemini via httpx; `complete(dicts)`; Groq retries on 429 + timeouts.
- `demo_agent/` (Claude): MockPay world, 6 tools with source labels, agent loop, 14 scenarios (6 benign incl. `benign_send_large` = ASK_HUMAN demo, 8 attacks incl. fake bills EN/BN/Banglish), `run.py` (`--shield --compare --approve --judge-model`, `run_world()`). `dashboard/app.py`: side-by-side + audit tab.
- `benchmark/` (Claude): `dataset.py`, `metrics.py` (Wilson CIs), `detectors.py` (heuristic, Prompt Guard 2 86m/22m on Groq, cached), `run_detection.py`, `run_agent.py`.
- `api/app.py` (Claude): FastAPI gateway, `uvicorn agentshield.api.app:create_app --factory`; optional `AGENTSHIELD_API_KEY`. `benchmark/run_mixed.py`: mixed-inbox experiment; `run_world(..., classifier=False)` for ablations. `demo_agent/recording.py`: record/replay.

## Data
- `datasets/benign.jsonl`: 135 look-alikes (45 per language), LLM-written, `reviewed=no`. **Bias caveat:** written after reading the heuristic's code.
- `datasets/external.jsonl`: 40 NVIDIA agentic indirect injections (EN, CC-BY-4.0, non-banking tools → skipped by `run_agent`). deepset left out (mislabeled languages, non-injection "attacks").
- `datasets/attacks.jsonl`: 24 items (12 bn, 12 banglish; 7 blunt + 5 subtle each), ChatGPT-generated, admission phrases removed by the user, `reviewed=yes`. Bangla and Banglish items are near-parallel translations (useful for language comparison, low diversity).
- Fake data only: numbers start `010`, domains `.example`, wallet "MockPay".

## Findings so far (27 Oct)
- Real LLMs (qwen3.8-27b, gpt-oss-120b) resisted all blunt demo attacks; a realistic **Bangla fake bill** fooled qwen (paid attacker 4500 BDT). With AgentShield (real qwen, n=1): fake bill blocked by policy, landlord's 8000 BDT still paid. The intent judge calls the fake bill "consistent" → policy/taint are what catch it.
- Mock, 13 scenarios: all 8 attacks stopped, all 5 benign unchanged.
- Text-level (`detection_20261026-224448`): on 40 NVIDIA indirect injections heuristic 0/40, Prompt Guard 2 1/40 (both sizes). Benign FPR: heuristic 1/135, Prompt Guard 2/135 (English/Banglish "instructions" sentences). Prompt Guard flagged demo e10 (EN) and e11 (BN) but missed e12 (Banglish), n=1.
- Agent-level, mock (`agent_20261026-225012`): rent bill paid for 135/135 benign items both without and with AgentShield.
- Latency: separate `JUDGE_MODEL=openai/gpt-oss-120b` cut worst judge latency 15.6 s → 1.0 s.

## Open decisions / known risks
- Classifier scope: it scans ALL untrusted context, so a legit payment becomes ASK_HUMAN (~0.57) when an unrelated injection email is in the same inbox. Option A (current) keep; option B score only items taint linked to the arguments. **Data now (`mixed_20261027-160905`, simulated):** attack email read first → rent held 5/12 with the classifier, 0/12 without it, attacker paid 0/12 either way. Evidence favors B. User's files (`checks/classifier.py` / `core/engine.py`); do together with intent fix A, later.
- Live demo: the agent (qwen) hits Groq's rate limit; a protected scenario took 17–59 s. Fix in Phase 5 (left column on mock/cached run, pauses, or lighter agent model).
- Gemini free tier returns 403 for this account → Groq is the real LLM. `openai/gpt-oss-20b` incompatible (forces native tool calls).

## Environment
Windows 11, PowerShell, 8 GB RAM, no GPU (no local LLMs/training). Python 3.14.2 venv `.venv` (3.13 installed as fallback). Budget zero: Groq free tier, Kaggle GPU (Phase 4), HF Spaces / Streamlit Cloud. `.env`: `LLM_PROVIDER=groq`, `LLM_MODEL=qwen/qwen3.8-27b`, `JUDGE_MODEL=openai/gpt-oss-120b`. Inline `python -c` with quotes breaks in PowerShell: write scripts to the scratchpad instead.
GitHub: `origin` = https://github.com/Likhons/AgentShield (private; `main` tracks `origin/main`). Push only when the user asks; before pushing, scan history for keys (gsk_, AIza, AQ.) and keep `.env`, `*.db`, `benchmark/cache/` ignored. If the repo is ever made public, decide first whether `datasets/attacks.jsonl` may be public (see docs/ethics_impact.md, misuse section).

## Phase plan
0 Setup ✓ · 1 Vulnerable demo agent ✓ · 2 Core ✓ · **3 Datasets + benchmark (by ~9 Nov)** · 4 Classifier training on Kaggle (by ~13 Nov) · 5 Dashboard + demo (by ~16 Nov) · 6 Polish + submission (by 19 Nov, buffer 20 Nov). Docs drafted: `docs/business_model.md`, `docs/ethics_impact.md`, `docs/architecture.md` (architecture status table is outdated: Phase 2 is now built).

## Commands
```powershell
.\.venv\Scripts\Activate.ps1
pytest                                          # 195 tests
python -m demo_agent.run --compare --all        # all scenarios, without vs with AgentShield (mock unless --provider groq)
streamlit run dashboard/app.py                  # side-by-side demo + audit log
python -m benchmark.dataset                     # validate dataset, show balance
python -m benchmark.run_detection --detectors heuristic,promptguard-86m,promptguard-22m
python -m benchmark.run_agent [--provider groq --runs 3 --languages bn,banglish]
```
