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

## Phase 2: AgentShield core v1 (by ~5 Nov): PAUSED
> Paused on 28 Oct. The user writes this phase later, with Claude helping by explaining, debugging and reviewing.
- [ ] "Delegated authority" scenarios: pay-bills task, legit known-contact bill + fake bills (EN / BN / Banglish); `allowed_recipients` in scenarios; mock pays bill requests
- [ ] Pydantic models (ToolCall, ContextItem, CheckResult, Decision)
- [ ] Taint tracking
- [ ] Policy engine + policies/default.yaml
- [ ] Heuristic injection classifier (EN / BN / Banglish) behind an interface
- [ ] Intent check (mock + real LLM)
- [ ] Risk scoring + ALLOW / ASK_HUMAN / BLOCK + bilingual reason
- [ ] Per-check latency measurement
- [ ] SQLite audit log
- [ ] SDK wrapper (protect tools in 2 lines)
- [ ] FastAPI gateway (basic)
- [ ] Attack scenario BLOCKED, benign tasks still work
- [ ] Unit tests for every check
- [ ] Update docs, commit

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
- [ ] Streamlit side-by-side demo (without vs with AgentShield)
- [ ] Live audit log view
- [ ] Metrics page with benchmark charts
- [ ] Works fully with mock LLM (offline-safe)
- [ ] Commit

## Phase 6: Polish + submission (by 19 Nov, buffer 20 Nov)
- [x] docs/business_model.md draft (business model, global readiness, NRB, risks); numbers still TBD
- [ ] User: verify market data, interview 5–10 potential customers for pricing
- [x] docs/ethics_impact.md draft (KPIs, data use, bias, transparency, oversight, limitations); KPI values TBD
- [ ] docs/architecture.md (diagram + explanation)
- [ ] docs/results.md (real numbers only)
- [ ] Clean README with setup steps
- [ ] Demo video script
- [ ] Pitch talking points mapped to judging criteria
- [ ] Optional: deploy to HF Spaces; one stretch feature
- [ ] Final commit
