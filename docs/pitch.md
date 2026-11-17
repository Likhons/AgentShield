# AgentShield: Pitch and Demo Script

> Draft, updated 17 Nov 2026. Every number here is in [results.md](results.md) with its source file. Re-check them after the final benchmark run; anything still TBD there must not be said on stage.

## 1. The 3-minute pitch

| Time | Say | Show | Criterion |
|---|---|---|---|
| 0:00–0:25 | **Problem.** "Banks and wallets are giving AI agents the power to move money. An agent cannot tell its user's instruction from text an attacker hid in an email, a web page or a file. In Bangladesh that text is often Bangla or Banglish." | One fake Bangla bill email on screen | Real-world impact |
| 0:25–0:50 | **Proof the danger is real.** "We gave a real open model a realistic Bangla fake electricity bill with the task *pay my pending bills*. It paid the attacker." | Recorded run, left column: money stolen | Impact, Technical execution |
| 0:50–1:30 | **Live demo.** "Same agent, same email, now protected by AgentShield. The fake bill is blocked; the landlord's real rent still goes through. Every decision comes with a reason in Bangla and English." | Dashboard side by side, BLOCK with Bangla reason, then the Audit log tab | Technical execution, Ethical AI (transparency) |
| 1:30–2:00 | **How it works.** "Four checks before any tool runs: where did each argument come from (taint), does the text try to instruct the AI (classifier), does the action follow from what the user asked (an LLM judge, only when needed), and readable YAML rules. AI where judgment is needed, deterministic rules where certainty is needed." | Architecture diagram | Innovation, Technical execution |
| 2:00–2:30 | **Measured, honestly.** "A widely used guardrail, Meta's Prompt Guard 2, flagged 0 of our 24 Bangla and Banglish attacks. With a real model, AgentShield stopped every attacker payment and held no legitimate bill. We also found and fixed our own weaknesses: early versions held real bills for approval too often, and we publish that." | Benchmark tab (chart) | Technical execution, Ethical AI |
| 2:30–2:50 | **Business and scale.** "Open-core: free SDK, paid hosted gateway and on-prem licence for banks and wallets. Works with any agent framework over HTTP. Bangla first, then other code-mixed languages: Hindi/Hinglish, Urdu, Nepali." | One slide | Business + global readiness, Scalability |
| 2:50–3:00 | **Close.** "AgentShield: agent-action security for Bangla. The agent may be fooled; the money is not." | Logo | Presentation |

Say "first agent-action security for Bangla", never "first Bangla guardrail".

## 2. Demo plan (stage-safe)

1. Before the event: record real-model runs once (`python -m demo_agent.run --all --compare --provider groq --record`) after the intent-judge fix.
2. On stage: dashboard → scenario **attack_bill_bn** → LLM **recorded (groq)** → Run. Instant, no internet needed; the screen says it is a recording.
3. If asked to go live: switch to **groq** (needs internet; may take 20–60 s per scenario on the free tier) or **mock** (offline simulation; say so).
4. Backup: the same flow in the terminal: `python -m demo_agent.run --scenario attack_bill_bn --compare --provider mock`.
5. Show the **Audit log** tab (every decision stored) and the **Benchmark** tab (measured numbers).

## 3. Numbers you may say (with their limits)

| Claim | Number | Limit to state if asked |
|---|---|---|
| Prompt Guard 2 on our Bangla/Banglish attacks | 0/24 flagged (both 86m and 22m) | 24 items; it also missed 39/40 subtle English agent injections, so the gap is not only language |
| Real model fooled by a Bangla fake bill | Happened in our tests (4/20 attacks moved money without protection) | 20 items, 1 run each |
| AgentShield with a real model | 0/20 attacks moved money (4/20 without); rent paid 16/20 with and 16/20 without AgentShield | 20 + 20 items, 1 run each, `agent_20261112-111137`. The 4 blocked attacks are exactly the 4 that stole without protection; the other 16 the agent never tried. The 4 unpaid rents were also unpaid without AgentShield |
| Simulated agent | 0/60 attacks succeed with AgentShield (22/60 without); 175/175 rent payments completed | Simulation (mock agent), say so; `agent_20261111-122758` |
| Speed | ~0.1–0.6 ms per check without an LLM call; LLM judge called only when needed | Free-tier LLM latency varies |
| Network check across users | Simulated wallet week: money reaching scammers 334,300 → 96,000 BDT; 0 of 1,109 real accounts flagged; phone-scam numbers caught after 12, then 4, then 1 person | **Simulation**: 600 fake users, our own scam patterns, weights chosen on the same data. Shows the method, not accuracy. 46 real payments needed an extra confirmation, 1 small scam was missed. `network_20261117-175247` |

## 4. Likely judge questions and honest answers

- **"Isn't this just a prompt-injection classifier?"** No. Text classifiers, including ours, miss subtle attacks such as a fake bill that never addresses the AI. We stop the *action*: the payee number came from an untrusted email and is not a saved contact, so the transfer is blocked whatever the text says.
- **"Why not just use a better LLM?"** Models change and can be fooled; rules on money do not. We use the LLM only where judgment is needed, and we measured that the judge alone would have approved the fake bill.
- **"Your dataset is small."** Yes: 24 team-written Bangla/Banglish attacks, 40 public English agent attacks, 135 benign look-alikes. Every number comes with a 95% interval. Growing the dataset with native speakers is part of the plan (NRB volunteers).
- **"How do you avoid blocking normal Bangla users?"** We test benign look-alikes on purpose (money, bills, "ignore", "assistant" in normal sentences) and report false positives per language. When unsure we ask the human instead of blocking.
- **"What does it cost to run?"** Most checks are local and take under a millisecond; the LLM judge runs only for sensitive tools when another check sees risk (8 of 34 checks in our demo comparison).
- **"Do you do fraud detection across transactions, or graph analysis?"** Per call, no: each check judges one tool call. On top of that we built a network check that looks across all users of a wallet: a number that many unrelated people pay, and that sends the money straight on, is flagged for everyone, and numbers that send money to a known cash-out account are caught after one or two victims. We have only tested it on a simulated wallet week, and we say so. With a partner wallet's transaction data it would need re-tuning and real fraud labels. It is a rule-based score, not a trained streaming model.
- **"Who pays?"** Wallets and banks deploying agents (on-prem licence), fintech startups (hosted plan), agent platforms (partner plan). Pricing is still being validated with interviews.

## 5. Demo video script (about 2 minutes)

1. (0:00) Title card: "AgentShield: agent-action security for Bangla".
2. (0:05) Screen: a Bangla fake bill email. Voice: the problem in two sentences.
3. (0:20) Dashboard, recorded real run, left column: the agent pays the attacker.
4. (0:40) Right column: AgentShield blocks it; zoom on the Bangla reason; rent still paid.
5. (1:05) Audit log tab: every decision with risk score and reason.
6. (1:20) Benchmark tab: Prompt Guard 0/24 on Bangla/Banglish; AgentShield stopped all attacks in agent tests.
7. (1:40) Architecture diagram + "AI where judgment is needed, rules where certainty is needed".
8. (1:55) Closing line and repo/contact.
