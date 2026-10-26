# AgentShield: Business Model and Global Readiness

> Draft, 28 Oct 2026. Every number marked **TBD** must come from a real source or a real measurement before it goes into the pitch. Prices are hypotheses to test, not facts.

## 1. The problem, in one paragraph

Companies are starting to give AI agents real permissions: reading customer emails, browsing the web, opening files, and calling payment or account tools. An agent cannot reliably tell the difference between an instruction from its user and text written by an attacker inside the data it reads. In Bangladesh this risk is sharper: much of that data is written in Bangla or Banglish (Bangla in Latin letters), and existing guardrails are built and tested mainly for English. A single wrong `send_money` call means real money lost and real trust lost.

## 2. Who pays

| Segment | Why they care | What they buy |
|---|---|---|
| **Mobile financial services (MFS) and digital wallets** (beachhead) | Building AI support and assistant agents that can touch money; heavy Bangla/Banglish customer traffic | Hosted gateway or on-prem license, compliance reports |
| **Banks and NBFIs** | Regulators expect human oversight and audit trails for automated decisions | On-prem license (data stays inside the bank), audit log export |
| **Fintech and e-commerce startups** | Shipping agents fast, no security team | Free SDK, then usage-based hosted plan |
| **Agent platform builders / AI agencies** | Need a security layer they can resell to clients | Partner / white-label plan |
| **Telecom and government service portals** | Bangla-first citizen-facing chat agents | Enterprise license, custom policies |

Beachhead choice: **MFS + digital wallets**, because the harm (money moving) is clear, the language mix is exactly our strength, and one reference customer there is credible across the whole region.

Market size: **TBD**. Sources to check: Bangladesh Bank MFS statistics (number of accounts, monthly transaction value), and published counts of Bangladeshi fintech startups.

## 3. Value proposition

- **Stops the action, not just the words.** Checks every tool call before it runs, so even an injection that slips past the language model is stopped at the moment it would cause harm.
- **Built for Bangla and Banglish.** Not an English tool with translation bolted on.
- **Low over-refusal.** Normal customer messages about bills and money must keep working; blocked benign tasks are measured and reported. Target value: **TBD after benchmark**.
- **Explainable.** Every decision comes with a plain reason in English and Bangla, plus an audit log. This is what compliance teams and regulators ask for.
- **Cheap to run.** Deterministic rules and a small classifier handle most calls; the LLM judge runs only when cheaper checks see risk. Cost per 1,000 checks: **TBD after measurement**.

## 4. How it is delivered

1. **Open-source SDK + basic rules (free).** Two lines of code to wrap an agent's tools. Builds trust and adoption among developers.
2. **Hosted gateway (SaaS).** Usage-based API. Includes the trained Bangla/Banglish classifier, the dashboard and audit retention.
3. **On-prem / private cloud license.** For banks and MFS providers that cannot send customer data outside their own infrastructure.
4. **Add-ons.** Custom policy packs per institution, compliance report exports, red-team testing service using our attack benchmark.

This is an **open-core** model: the free part spreads the product; the paid part is what institutions need for production (accuracy, audit, support, data residency).

## 5. Pricing hypotheses (to validate with real conversations)

| Plan | Who | Price idea (hypothesis) |
|---|---|---|
| Community | Developers, students | Free, self-hosted, heuristic checks |
| Startup | Small fintechs | Monthly fee including a quota of checks, then per-1,000-check pricing |
| Business | Mid-size companies | Higher quota, dashboard, longer audit retention, email support |
| Enterprise | Banks, MFS | Annual on-prem license + support contract |

Exact amounts: **TBD**. Method: talk to 5–10 potential customers (fintech founders, bank IT security staff) and ask what they spend today on fraud and security tooling.

## 6. Cost structure

- LLM calls (only for flagged, sensitive actions). Free tier during development.
- CPU inference for the classifier (no GPU needed in production).
- Cloud hosting for the gateway and dashboard.
- People: engineering, Bangla/Banglish data curation, customer support.

Unit economics: **TBD** after we measure how many tool calls per session trigger the LLM judge.

## 7. Go-to-market

1. **Now → Congress (Dec 2026):** working demo, honest public benchmark, open-source SDK.
2. **First 6 months:** 2–3 pilot partners in fintech/MFS; publish the Bangla agent-security benchmark so others measure against it.
3. **6–18 months:** paid hosted plan; on-prem pilots with banks; partnerships with agent platform builders.

Channels: developer community (GitHub, local tech meetups), fintech associations, security conferences, hackathon networks, and the NRB network (see section 9).

## 8. Global readiness

- **Language packs.** The architecture separates language-specific parts (classifier model, keyword lists, reason templates) from the language-neutral parts (taint tracking, policy engine, audit). Adding a new language means training one classifier and translating templates, not rebuilding the product.
  - Natural next markets: **West Bengal and other Bangla speakers**, then other South Asian languages with romanized ("code-mixed") variants, such as Hindi/Hinglish, Urdu, Nepali and Sinhala.
- **Framework-agnostic.** Works with any agent framework through the SDK or the HTTP gateway.
- **Cloud-agnostic.** Runs on any cloud, on-prem, or a laptop; LLM provider is a setting, not hard-coded.
- **Regulation-friendly by design.** Human approval for high-risk actions, full audit log and plain-language explanations match common AI governance expectations (human oversight, record keeping, transparency). Exact mapping to specific regulations (Bangladesh, EU AI Act, NIST AI RMF): **TBD, verify before claiming**.

## 9. NRB collaboration

Non-Resident Bangladeshis are a natural partner group:

- **Engineers abroad** as open-source contributors, reviewers and advisors (AI security, fintech).
- **Remittance corridors.** AI agents handling remittances are a high-value target; NRB-focused remittance services are a direct customer segment.
- **Data quality.** Diaspora communities write in Banglish every day; volunteers can help review and extend the benign and attack datasets.
- **Market bridge.** NRB founders and professionals can introduce the product to companies in their host countries that serve Bangla-speaking customers.

## 10. Competition and positioning

- **General guardrails (mostly English-focused).** Strong for English text; not designed for Bangla/Banglish agent workflows. Our own measurement on Bangla/Banglish: **TBD (Phase 3 benchmark)**.
- **Bangla safety research (chat-level).** Focuses on single-turn chat prompts rather than agent actions. Citations and numbers must be verified before the pitch.
- **Our position:** agent-action security for Bangla and Banglish. Claim: "first agent-action security for Bangla", not "first Bangla guardrail".
- **Moat:** curated Bangla/Banglish agent-attack dataset and benchmark, local relationships with fintechs, and the speed of a small focused team.

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Big guardrail vendors add Bangla | Move fast, own the benchmark, go deep on local policies and compliance |
| Too many false blocks annoy users | Measure over-refusal openly; human-approval path instead of hard blocks where unsure |
| Customers won't send data to a cloud service | On-prem license |
| Free-tier LLM limits | Mock/offline mode, LLM used only for flagged calls, provider is swappable |
| Small dataset limits accuracy | Community data contributions, continuous re-training |

## 12. Business KPIs to track

- Number of pilot partners and agents protected
- Tool calls checked per month
- Attacks stopped vs. benign actions wrongly blocked (from the dashboard)
- Median added latency per tool call
- Conversion from free SDK users to paid plans

## 13. Open questions for the team

1. Which 5–10 people can we interview for pricing validation before Congress Day?
2. Do we know anyone in an MFS or bank security team for a pilot letter of interest?
3. Which NRB contacts could act as advisors?
