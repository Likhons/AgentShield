# AgentShield progress

## Phase 0: Setup (27 Oct)
- [x] CLAUDE.md + PROGRESS.md
- [x] git init + .gitignore
- [x] .venv + requirements.txt
- [x] .env.example
- [x] README.md skeleton
- [x] Folder structure with packages
- [x] pytest runs (smoke test)
- [x] Commit

## Phase 1: Vulnerable demo agent (27 Oct)
- [x] LLM provider abstraction (mock / gemini / groq), config from .env
- [x] Fake data: MockPay accounts, inbox (normal + attack emails in EN / BN / Banglish), web pages, files
- [x] Tools: read_inbox, read_email, get_balance, send_money, search_web, read_file
- [x] Agent loop (plain Python) using the mock LLM
- [x] One command runs the attack scenario and prints steps + "money stolen"
- [x] Tests for tools + attack scenario (31 tests passing)
- [x] Update CLAUDE.md / PROGRESS.md, commit
- [x] API keys: Gemini free tier unavailable (403) → switched to Groq (qwen3.8-27b), retry on 429/timeout
- [x] First real-LLM check (n=1): blunt attacks 0/5 on qwen and gpt-oss-120b; realistic Bangla fake bill fooled qwen (4500 BDT), not gpt-oss-120b. See CLAUDE.md "Key early finding".

## Phase 2: AgentShield core v1 (by ~5 Nov)
> The user writes the core files; Claude explains, reviews, probes and commits.
- [x] "Delegated authority" scenarios: `benign_pay_bills`, `attack_bill_bn` (Bangla fake bill), `allowed_recipients`; mock pays bill requests
- [x] EN and Banglish fake-bill variants (`attack_bill_en`, `attack_bill_banglish`)
- [x] `JUDGE_MODEL`: intent judge on its own Groq model (worst judge latency 15.6 s → 1.0 s in a 5-scenario run)
- [x] Pydantic models (user)
- [x] Policy engine + policies/default.yaml (user)
- [x] Taint tracking, per argument (user)
- [x] Intent check, real LLM + mock judge mode (user + Claude)
- [x] Decision engine: risk score, ALLOW / ASK_HUMAN / BLOCK, bilingual reason, per-check latency (user)
- [x] SQLite audit log with KPI stats (user)
- [x] SDK `ShieldSession.wrap()` (user)
- [x] Demo: `--shield`, `--compare`, `--approve`; dashboard side-by-side + audit tab (Claude)
- [x] All 6 attack scenarios stopped on mock, all 5 benign scenarios unchanged; fake bill blocked and landlord paid on real qwen (n=1)
- [x] Heuristic injection classifier behind a `predict()` interface (user), wired into the demo engine
- [x] Unit tests for every check (156 tests passing)
- [ ] Decide classifier scope (all untrusted items vs. items linked by taint) using Phase 3 over-refusal numbers
- [ ] FastAPI gateway (basic), optional
- [x] Policy template keys from rule args; whole-number match in `not_mentioned_by_user` (user)
- [x] Friendlier ALLOW reason when a check flagged but the action is allowed (user)

## Phase 3: Datasets + baseline benchmark (by ~9 Nov)
- [ ] Hand-written seed set (EN / BN / Banglish; direct, indirect, benign look-alikes)
- [ ] LLM-assisted variations (user reviews Bangla/Banglish samples)
- [ ] 300–500 labeled items, balanced
- [ ] Benchmark runner + metrics (ASR with/without, block rate, FPR, per-language, median latency, benign completion)
- [ ] Baselines: Prompt Guard, LlamaFirewall, BanglaVeilGuard (where usable; honest notes if not)
- [ ] Answer: do existing guardrails perform worse on Bangla/Banglish? (real numbers)
- [ ] Commit

## Phase 4: Classifier training (by ~13 Nov)
- [ ] training/train_classifier.ipynb (BanglaBERT or XLM-R)
- [ ] Kaggle step-by-step instructions
- [ ] Load exported model in checks/classifier.py (CPU)
- [ ] Re-run benchmark, per-language + over-refusal vs BanglaVeilGuard published numbers
- [ ] Commit

## Phase 5: Dashboard + demo (by ~16 Nov)
- [x] Streamlit skeleton: tabs, live demo of the unprotected agent (mock + groq), dashboard tests
- [ ] Streamlit side-by-side demo: right column "with AgentShield" (needs Phase 2)
- [ ] Live audit log view
- [ ] Metrics page with benchmark charts
- [ ] Works fully with mock LLM (offline-safe)
- [ ] Commit

## Phase 6: Polish + submission (by 19 Nov, buffer 20 Nov)
- [x] docs/business_model.md draft (business model, global readiness, NRB, risks); numbers still TBD
- [ ] User: verify market data, interview 5–10 potential customers for pricing
- [x] docs/ethics_impact.md draft (KPIs, data use, bias, transparency, oversight, limitations); KPI values TBD
- [x] docs/architecture.md draft (diagram, component status, model selection); update after Phase 2
- [ ] docs/results.md (real numbers only)
- [ ] Clean README with setup steps
- [ ] Demo video script
- [ ] Pitch talking points mapped to judging criteria
- [ ] Optional: deploy to HF Spaces; one stretch feature
- [ ] Final commit
