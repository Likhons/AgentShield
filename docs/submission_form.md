# Preliminary submission: form text (copy into the CloudCamp portal)

> Draft, 12 Nov 2026. Deadline: 20 Nov 2026, 11:59 PM GMT+6 (per other teams' notes; **confirm in the portal**). Our target: 19 Nov.
> Field list taken from other teams' public notes about the portal, not from the official page: check every field name against the live form.
> Numbers: only from `docs/results.md` (real-LLM run `agent_20261112-111137`).
> Fill only what is true. The portal auto-scores listed technologies; do not list anything we do not use (RAG, MCP, vector DBs, local LLM runtimes are **not** used).

---

## Required fields

### Project name
AgentShield

### Elevator pitch (one sentence)
AgentShield checks every action an AI agent is about to take, such as sending money, and blocks the ones the user never asked for, even when the trick is hidden in Bangla or Banglish inside an email, web page or file.

### Public summary
AI agents are starting to pay bills and move money for people. They read emails, web pages and files, and they cannot reliably tell the user's instruction from text an attacker planted there (indirect prompt injection). In Bangladesh that text is often Bangla or Banglish, where existing guardrails are weakest: in our tests Meta's Prompt Guard 2 flagged 0 of 24 Bangla/Banglish attacks. AgentShield is a runtime security gateway that sits between the agent and its tools. Before any tool runs it checks where each argument came from, whether untrusted text tries to instruct the AI, whether the action follows from what the user asked, and fixed policy rules, then answers ALLOW, ASK (the user decides) or BLOCK, with a reason in Bangla and English and an audit record. With a real model (20 Bangla/Banglish attacks, 20 normal bill payments), attacks moved money 4 times without AgentShield and 0 times with it, while legitimate rent payments went through just as often as without protection (16/20).

### Problem statement
Banks, wallets and fintech apps are giving AI agents tools that move money. An agent treats everything it reads as possible instructions, so an attacker does not need to hack the bank: a fake bill in an inbox, a line on a web page or a note in a file can make the agent pay the attacker. This is indirect prompt injection, listed by OWASP as the top risk for LLM applications. Defences today are mostly text classifiers trained on English. On our Bangla and Banglish attacks, Meta's Prompt Guard 2 flagged 0 of 24, and it caught only 1 of 40 subtle English agent attacks from a public NVIDIA dataset. The most dangerous attacks do not even address the AI: a realistic fake bill looks exactly like a real one. A real open model (qwen3.8-27b) paid such a Bangla fake bill in our tests. Bangladesh runs on mobile financial services and has a fast-growing fintech sector, so this gap will matter as soon as agents handle payments. [Optional: add the current number of MFS accounts from Bangladesh Bank, with the source, before submitting.]

### Solution description
AgentShield is a gateway that every tool call passes through before it runs (Python SDK `ShieldSession.wrap()` or an HTTP API). Four checks run on each call:
1. Taint tracking: traces each argument (recipient, amount) to its source: the user's own words, a specific email/web page/file, or nowhere.
2. Injection classifier: scans the untrusted text that supplied the arguments for attempts to instruct the AI, in English, Bangla and Banglish.
3. Intent check: an LLM judge decides whether the action follows from the user's request. It sees only the request and the tool call, never the untrusted text, so the attacker cannot talk to it.
4. Policy engine: readable YAML rules, e.g. money to an unknown number that only appears in untrusted data is blocked; transfers above 10,000 BDT need approval.
The scores are combined and the stricter of the score and the policy decides: ALLOW, ASK_HUMAN or BLOCK, with a reason in Bangla and English. Every decision is stored in an audit log. Principle: AI where judgment is needed, deterministic rules where certainty is needed. A dashboard shows the same scenario side by side without and with AgentShield, plus the audit log, benchmarks, policies and datasets.

### Data & AI provenance
- Attack data: 64 Bangla/Banglish prompt-injection texts written for this project (24 drafted with ChatGPT and then edited and reviewed by the team, 40 hand-written by the team), plus 40 English agentic indirect-injection items sampled from NVIDIA's Nemotron-RL-Agentic-Indirect-Prompt-Injection-v1 (CC-BY-4.0).
- Benign data: 230 texts: 135 LLM-written look-alikes reviewed by the team, 35 hand-written by a team member who had not seen the classifier code, 60 LLM-written legitimate payment requests.
- All data is fake: phone numbers start with 010 (not used by operators), domains end in .example, the wallet is the fictional "MockPay". No personal data is collected or used.
- Models: agent qwen/qwen3.8-27b and intent judge openai/gpt-oss-120b via the Groq API; baselines Meta Llama Prompt Guard 2 (86M, 22M) via Groq; an XLM-RoBERTa-base classifier we fine-tuned on Kaggle (experimental, not used at runtime, see Evaluation).
- Results: every number comes from saved benchmark runs (`benchmark/results/`) with 95% Wilson confidence intervals; `docs/results.md` lists sources and limits.

### Tooling & IDE
VS Code on Windows 11; Claude Code (Anthropic) as AI pair programmer for implementation, reviews, benchmarking and UI work; ChatGPT for first drafts of attack texts (team-edited); Python 3.14; Pydantic, FastAPI, Streamlit, httpx, PyYAML; pytest (246 tests) with GitHub Actions CI on Python 3.13 and 3.14; Groq API (free tier) for LLMs; Kaggle notebooks (T4 GPU) with Hugging Face Transformers for fine-tuning; SQLite for the audit log; Playwright for UI checks; Streamlit Community Cloud for the live demo.

### YouTube video
TBD: 2–3 minute walkthrough of the working software (script in `docs/pitch.md` §5, to be updated).

### Demo / live links
- Live demo: https://agentshield-demo.streamlit.app (offline simulated agent and recorded real-model runs; no API key needed)
- GitHub repository: **TBD, must be public** (decide what to do with `datasets/attacks.jsonl` first, see `docs/ethics_impact.md` §9)

---

## Optional links
- Design / architecture: `docs/architecture.md` (works only once the repo is public)
- Other links (up to 3): `docs/results.md` (measured results), `docs/ethics_impact.md`, `docs/business_model.md`

## Team
TBD by the team: team name, members and roles, team lead contact, NRB member (yes/no), female member (yes/no). Claim only what is true.

---

## Structured tabs (fill those the portal shows)

### AI models used
qwen/qwen3.8-27b (demo agent, via Groq); openai/gpt-oss-120b (intent judge, via Groq, separate model so the judge has its own rate-limit budget); Meta Llama Prompt Guard 2 86M and 22M (baselines, via Groq); xlm-roberta-base fine-tuned by us on Kaggle (experimental injection classifier). The runtime injection detector is a transparent rule-based classifier.

### Prompt strategy
The intent judge gets a short, fixed prompt with only three inputs: the user's request, the tool call, and trusted facts from the bank (for example whether the recipient is a saved contact). It never sees email, web or file text, so injected instructions cannot reach it. It must answer in a fixed JSON format (consistent / inconsistent with a score). After we found that the judge called legitimate bill payments "inconsistent", we added an explicit rule: a general request such as "pay my bills" covers payments to saved contacts, but not to strangers or other amounts. On 11 hand-made judge cases repeated 3 times, correct answers went from 28/33 to 33/33. Errors fail safe: if the judge fails, its risk is set to 0.5 and the user is asked.

### Token optimization
The LLM judge is called only for sensitive tools and only when another check already sees risk; most tool calls are decided by local checks in under a millisecond. The judge prompt contains only the request and the tool call (no inbox or page text), which keeps it short. The judge runs on its own model so it does not compete with the agent for the free-tier rate limit (worst-case judge latency fell from 15.6 s to 1.0 s). Baseline scores are cached on disk, and real-model demo runs can be recorded and replayed without new calls.

### Agent / orchestration
A demo banking agent with six tools (read inbox, read email, web search, read file, get balance, send money), each labelled with its data source. Every tool is wrapped by `ShieldSession.wrap()`, which builds a guard request (user request, tool call, labelled context, saved contacts) and runs the four checks before the tool executes. The same checks are available as an HTTP gateway (FastAPI: `POST /v1/check`, `GET /v1/audit`, `GET /v1/stats`) so any framework can use them.

### Fine-tuning / adaptation
We fine-tuned xlm-roberta-base on Kaggle (T4 GPU, 6 epochs, class weights, stratified 70/15/15 split by language and label, 334 items). On the held-out test split it flagged 16/16 attacks and 3/35 benign texts. In the agent-level benchmark it held legitimate rent payments for approval, because it reacts to email header formatting it never saw in training. We therefore keep the rule-based classifier at runtime and publish this finding; retraining on texts in the runtime format is the next step.

### Evaluation and quality
Two benchmarks with 95% confidence intervals, all runs saved: (1) text level: do detectors flag attack texts and leave benign ones alone, per language; (2) agent level: does money reach a recipient the user never asked for, and is the user's real rent still paid, without vs with AgentShield. Simulated agent (full dataset): attacks succeeded 22/60 without and 0/60 with AgentShield; rent paid 175/175 in both. Real LLM (qwen3.8-27b via Groq, 20 attacks + 20 normal bill payments, 12 Nov): attacks moved money 4/20 without and 0/20 with AgentShield; the landlord's rent was paid 16/20 both without and with, so AgentShield blocked every attacker payment and held no legitimate one. 246 automated tests and CI on every push.

### Guardrails, safety and privacy
AgentShield is itself the guardrail: it acts on actions, not on what people may write. Uncertain cases go to the user (ASK) instead of being blocked; only clear attacks are blocked. Fail-safe defaults: a crashing check leads to ASK, a failed judge call to a medium risk. Every decision is explained in Bangla and English and logged. API keys stay in environment variables or platform secrets, never in the repository (checked before every push). The judge never receives untrusted text, which also limits what leaves the device.

### Data quality
A dataset validator rejects malformed rows and duplicate ids. Every item carries language, label, attack type, source and a reviewed flag. Data is balanced per language and reported per language. Known biases are documented (e.g. LLM-written benign texts, near-parallel Bangla/Banglish attacks), and we added independent hand-written items to reduce them.

### Privacy and compliance
No real user data: all names, numbers and wallets are fake. The public dataset we use is CC-BY-4.0 and credited with the changes we made. The attack dataset is shared with researchers on request rather than published openly, to avoid giving attackers a ready-made toolkit. The audit log stays on the operator's machine (SQLite).

### Lineage and observability
Each decision is stored with time, user request, tool, arguments, per-check scores, latency, decision and reason (SQLite audit log, also via `GET /v1/audit` and `/v1/stats`). Each benchmark run is saved as JSON and Markdown with a timestamp, provider, detector and per-item outcomes. All changes are in git with one commit per step.

### AI-DLC / engineering process
Phased plan (vulnerable demo agent → core checks → datasets and benchmark → classifier training → dashboard → submission). Every step ends with tests and a commit; 246 tests run in GitHub Actions on Python 3.13 and 3.14. Numbers are only reported from saved runs, and failures we found in our own system (judge over-refusal, classifier scope, trained-model over-refusal) are documented with the fix or the decision.

### Build level
Working prototype: core gateway, SDK, HTTP API, demo agent, dashboard and benchmarks run end to end; live demo online.

### Publicly hosted environment
Streamlit Community Cloud: https://agentshield-demo.streamlit.app

### Not used (leave empty)
RAG / vector databases, MCP, local LLM runtimes (Ollama etc.), workflow automation tools (n8n etc.), tunneling.
