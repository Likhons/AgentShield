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
- [x] Classifier scope decided: B (score only items taint-linked to the arguments), commit `69d2e4d`; mixed inbox rent held 5/12 → 0/12, attacker still 0/12 (`mixed_20261105-164804`, simulated)
- [ ] FastAPI gateway (basic), optional
- [x] Policy template keys from rule args; whole-number match in `not_mentioned_by_user` (user)
- [x] Friendlier ALLOW reason when a check flagged but the action is allowed (user)

## Phase 3: Datasets + baseline benchmark (by ~9 Nov)
- [x] Benchmark plumbing: dataset loader/validator, metrics with Wilson CIs, detectors (heuristic, Prompt Guard 2 86m/22m via Groq, cached), text-level runner, tests (Claude)
- [x] Benign seed: 90 look-alikes, 30 per language (Claude, `reviewed=no`)
- [x] First run on benign only (27 Oct): FPR heuristic 0/90, Prompt Guard 86m 2/90, 22m 2/90 (all flags on English/Banglish "instructions" sentences). Caveat: benign seed written after reading the heuristic.
- [x] Benign seed expanded to 135 (45 per language; still `reviewed=no`)
- [x] External English attacks: 40 NVIDIA agentic indirect-injection items (CC-BY-4.0), deepset left out (language/label problems)
- [x] Run 2 (27 Oct, `detection_20261026-224448`): on 40 NVIDIA attacks, detection heuristic 0/40, Prompt Guard 86m 1/40, 22m 1/40. Benign FPR: heuristic 1/135, 86m 2/135, 22m 2/135. Sanity check: Prompt Guard 86m flags demo e10 (EN, 0.999) and e11 (BN, 0.998) but not e12 (Banglish, 0.002), n=1 each.
- [ ] User: review benign.jsonl wording; add independent benign items
- [ ] User: attacks.jsonl seed (EN / BN / Banglish; blunt + subtle; email / web / file / direct)
- [x] Agent-level benchmark runner `benchmark/run_agent.py` (items placed in inbox / web / file; direct attacks and non-banking tools skipped; `--provider groq --runs N`) (Claude)
- [x] Agent run 1 (27 Oct, mock agent, `agent_20261026-225012`): benign rent payment completed 135/135 without and 135/135 with AgentShield. Mock = simulated agent; no attack items applicable yet.
- [x] attacks.jsonl: 12 Bangla + 12 Banglish (7 blunt, 5 subtle each), LLM-generated, admission phrases removed and reviewed by the user
- [x] Text run 3 (`detection_20261027-151903`): Prompt Guard 2 flags 0/24 Bangla/Banglish attacks (86m and 22m); heuristic 4/7 blunt per language, 0/5 subtle
- [x] Agent run, simulated (`agent_20261027-151938`): attacks succeed 11/20 without, 0/20 with AgentShield; rent paid 90/90 with
- [x] Agent run with real Groq (`agent_20261027-153825`): attacks 4/20 without → 0/20 with; BUT rent paid 17/20 without → 0/20 with (all ASK_HUMAN): the gpt-oss-120b judge, which never sees the email, cannot tell the landlord is a saved contact and says "inconsistent"
- [x] Fix A (intent judge: saved-contact fact + prompt rule, `aa4b1b7`): real Groq rent paid 0/20 → 14/20 with AgentShield, attacks 0/20 (`agent_20261105-130607`); benchmark reports blocked / held / never tried separately
- [x] docs/results.md draft (measured numbers only), architecture.md updated, ethics KPIs filled, README results summary
- [x] Dashboard Benchmark tab reads benchmark/results (tables + chart)

- [x] Agent benchmark records outcomes (blocked / held for approval / paid ...) and balances `--limit` per language; dashboard shows them

## Phase 6 prep
- [x] docs/pitch.md: 3-minute pitch mapped to judging criteria, stage-safe demo plan, sayable numbers with limits, judge Q&A, demo video script
- [x] docs/deploy.md: Streamlit Cloud / HF Spaces steps (not deployed; publishing is the user's decision)
- [x] FastAPI gateway (`agentshield/api/app.py`)
- [x] Mixed-inbox experiment (`benchmark/run_mixed.py`): evidence for classifier scope B

## Phase 5 prep
- [x] Record/replay for the stage demo (`--record`, dashboard "recorded (groq)"); recordings still to be made after the intent fix

## Phase 4 prep
- [x] training/train_classifier.ipynb (XLM-R base, stratified 70/15/15 split, class weights, test-split-only metrics, saves split_ids.json). Not run yet (needs Kaggle GPU).
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
- [x] Streamlit side-by-side demo, redesigned dark UI (12 Nov), live at agentshield-demo.streamlit.app
- [x] Live audit log view
- [x] Metrics page with benchmark charts
- [x] Works fully with mock LLM (offline-safe)
- [ ] Commit

## Phase 6: Polish + submission (by 19 Nov, buffer 20 Nov)
- [x] docs/business_model.md draft (business model, global readiness, NRB, risks); numbers still TBD
- [ ] User: verify market data, interview 5–10 potential customers for pricing
- [x] docs/ethics_impact.md draft (KPIs, data use, bias, transparency, oversight, limitations); KPI values TBD
- [x] docs/architecture.md draft (diagram, component status, model selection); update after Phase 2
- [x] docs/results.md (real numbers only; real-LLM run 12 Nov: attacks 0/20 with, rent 16/20 = same as without)
- [ ] Clean README with setup steps
- [ ] Demo video script
- [ ] Pitch talking points mapped to judging criteria
- [ ] Optional: deploy to HF Spaces; one stretch feature
- [x] 16 Nov (main): Streamlit mobile fixes (results under Run, benchmark tables on phones, policy stats), polish (auto-scroll, Bangla font, outcome colours, language labels); Datasets page hides `attacks.jsonl` texts and download (live)
- [x] 16 Nov (branch `react-frontend`): React frontend (`web/`) + dashboard API (`webapi/`), all 5 pages, responsive pass 360–1920 px; API live on Render https://agentshield-api-k60w.onrender.com (smoke test 16/16)
- [x] 16 Nov: Vercel frontend live at https://agent-shield-azure.vercel.app (root `web`, production branch `react-frontend`); live browser check passed
- [ ] Decide which live link goes into the submission; later merge `react-frontend` into `main` or keep both
- [ ] Final commit
