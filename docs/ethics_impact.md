# AgentShield: Real-World Impact and Ethical AI

> Draft, 27 Oct 2026. Every number marked **TBD** must come from an actual benchmark run before it goes into the pitch, README or slides.

## 1. Who is protected, and from what

- **End users of AI-powered financial services**, especially people who use Bangla or Banglish every day and may not recognise a well-written fake bill or official-looking message.
- **Companies deploying agents**, who carry the financial and reputational cost when an agent is tricked.
- **Regulators and auditors**, who need to see why an automated system took (or refused) an action.

The harm we target is concrete: an AI agent moving money, or leaking data, because of text an attacker placed inside an email, web page or file.

## 2. Measurable KPIs

All values come from the benchmark runner (Phase 3) and are reported per language (English, Bangla, Banglish).

| KPI | What it means | Target direction | Value |
|---|---|---|---|
| Attack success rate, without AgentShield | How often attacks succeed on an unprotected agent | (baseline) | TBD |
| Attack success rate, with AgentShield | How often attacks still succeed when protected | as low as possible | TBD |
| Over-refusal (false positive rate) | Share of benign actions wrongly blocked or held | as low as possible | TBD |
| Benign task completion | Share of normal tasks that finish correctly | as high as possible | TBD |
| Per-language gap | Difference in over-refusal between Bangla/Banglish and English | close to zero | TBD |
| Median added latency | Extra time per tool call | small enough not to be noticed | TBD |
| LLM judge call rate | Share of tool calls that needed the LLM | low (cost and privacy) | TBD |

**Early observation (anecdotal, not a statistic).** On 27 Oct 2026 we ran our demo agent once per model on two real LLMs. Blunt "ignore your instructions" style attacks did not work on either model. A realistic, polite-looking Bangla bill with an attacker's payment number did fool one of the two models into paying. This single run is why the benchmark must include subtle, realistic attacks and run each case many times before we claim any rate.

## 3. Responsible data use

- **All demo data is synthetic.** Fake wallet name ("MockPay"), fake people, fake amounts. Phone numbers use the `010` prefix, which no Bangladeshi operator uses, so they cannot reach a real person. Email addresses use the reserved `.example` domain.
- **No real customer data** is used for development, training or testing.
- **Attack examples stay defensive.** They exist only inside this repository to test and improve defenses, and they target fake accounts only.
- **Dataset documentation.** The dataset will ship with a datasheet: how items were written, which were generated with an LLM and reviewed by a human, language and category balance, and known gaps.
- **Community contributions** (for example from NRB volunteers) will be accepted only with clear consent and without personal information.

## 4. Bias and fairness

The main fairness risk for a Bangla guardrail is **blocking Bangla speakers more often than English speakers** for the same normal request. Prior Bangla safety work has reported high over-refusal on benign prompts (citation and numbers to be verified before the pitch). Our mitigations:

- **Balanced dataset** across English, Bangla and Banglish, and across attack and benign items.
- **Benign look-alikes on purpose.** Normal messages that mention money, bills, numbers or sending (a sibling thanking for money sent, a paid electricity bill, a monthly budget) must not be blocked. These are part of every test run.
- **Per-language reporting.** Over-refusal is always reported separately for each language, never only as one average that could hide a gap.
- **Native speaker review.** Bangla and Banglish samples are reviewed by a native speaker for natural wording, including different spellings of the same Banglish word.
- **Graded responses.** When unsure, AgentShield asks the human (ASK_HUMAN) instead of silently blocking, so a false alarm costs one click, not a failed task.

## 5. Transparency and explainability

- Every decision (ALLOW / ASK_HUMAN / BLOCK) carries a **plain-language reason in English and Bangla**, naming which check fired and why.
- Every decision is written to an **audit log** with the risk score, each check's result and its latency.
- **Design principle:** "AI where judgment is needed, deterministic rules where certainty is needed." Rules are readable YAML that a compliance officer can inspect and change without code.
- **Honest reporting.** Only measured numbers are published. Results from the offline mock model are always labelled as simulation, never presented as real-model results.

## 6. Human oversight

- High-risk actions (for example transfers above a set limit, or payments to recipients the user never mentioned) require **human approval**.
- The safe default when approval is missing is **not to act**.
- Institutions can tune limits and rules for their own risk appetite.

## 7. Privacy

- The LLM judge is called **only when cheaper checks see risk**, so most tool calls never leave the local system.
- On-prem deployment keeps customer data inside the institution.
- Planned: redaction of personal data in the audit log, configurable retention period.

## 8. Known limitations (stated openly)

- A determined attacker can adapt to any fixed rule or classifier; AgentShield reduces risk, it does not remove it.
- The first classifier is a simple heuristic; the trained model is planned for Phase 4.
- The LLM judge can make mistakes, and free-tier models change over time.
- Our dataset is small (target 300–500 items) compared with large English benchmarks.
- The demo agent is simplified; real agents have more tools and longer conversations.

## 9. Misuse considerations

- Publishing a Bangla attack dataset could help attackers as well as defenders. Release plan: share benchmark results openly; share the attack items with researchers and partners on request, with a short use agreement. Decision **TBD** before any public release.
- AgentShield must not be used to censor normal speech; it acts only on agent tool calls, not on what people are allowed to write.
