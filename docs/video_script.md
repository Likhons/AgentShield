# Demo video script (target 2:30, limit 2–3 min)

> For the preliminary submission (YouTube link, scored on "working software UI, features, workflow; crisp audio").
> Narration in English (international judges), read by a team member; Bangla appears on screen in the product itself.
> About 320 spoken words at a calm pace. Every number is from `docs/results.md`.
> Screen footage: the real dashboard, captured in the browser. The demo segment uses a **recorded real-model run** ("Recorded run" mode), recorded with the Groq model before the video is made.
> The amounts in rows 0:50–1:15 (৳ 4,500, the rent) come from a live test on 12 Nov; a real model can act differently in the recording, so **match the narration to the recording** before the voice is recorded.

| Time | On screen | Narration |
|---|---|---|
| 0:00–0:10 | Title card: shield, "AgentShield", subtitle "Agent-action security for Bangla". | "AI agents are starting to pay bills for us. What happens when one of those bills is fake?" |
| 0:10–0:35 | A Bangla fake electricity bill email, next to the landlord's real rent email. Then a text card: "Meta Prompt Guard 2: 0 of 24 Bangla and Banglish attacks flagged". | "An agent reads emails, web pages and files, and it cannot always tell its user's request from text an attacker planted there. This is indirect prompt injection. In Bangladesh that text is often Bangla or Banglish. A widely used guardrail, Meta's Prompt Guard 2, flagged none of our 24 Bangla and Banglish attacks." |
| 0:35–0:50 | Dashboard, Playground. Select "Attack: Realistic Bangla fake electricity bill", agent mode "Recorded run", press Run Scenario. | "Here is a real model, asked to pay the pending bills in its inbox. On the left it runs unprotected; on the right, the same agent runs behind AgentShield." |
| 0:50–1:15 | Left column: "Stolen −৳ 4,500", red MONEY STOLEN box. Right column: "৳ 0", green Safe box; zoom on the BLOCK step and its Bangla reason; then the rent payment marked ALLOW. Banner "AgentShield saved ৳ 4,500". | "Unprotected, the model paid the rent, and it also paid the fake bill: four and a half thousand taka to the attacker. With AgentShield, the fake bill is blocked before any money moves, with the reason in Bangla and English, and the landlord's real rent still goes through." |
| 1:15–1:40 | The Evaluation Pipeline card (four checks lighting up in turn), then the How AgentShield Works card. | "AgentShield checks every tool call before it runs. Where did each value come from? Does the untrusted text try to instruct the AI? Does this action follow from what the user asked? And fixed policy rules for money. AI where judgment is needed, deterministic rules where certainty is needed." |
| 1:40–2:05 | Benchmarks page: the real-LLM table. Highlight 4/20 → 0/20 and 16/20 = 16/20. | "We measured it with the same real model on twenty Bangla and Banglish attacks and twenty normal bill payments. Without AgentShield, four attacks stole money. With it, none did. And the rent was paid just as often as without protection: sixteen of twenty both times. It stopped every theft and blocked no real payment. The samples are small, so we publish every number with its confidence interval." |
| 2:05–2:20 | Audit Log page (decisions with risk and Bangla reasons), then Policies page. | "Every decision is logged with its reason, and the rules are plain, readable policy. Developers add AgentShield with a few lines of Python, one wrapper per tool, or through an HTTP API from any framework." |
| 2:20–2:30 | Closing card: "AgentShield", live demo link `agentshield-demo.streamlit.app`, team name. | "The agent may be fooled. The money is not. Try the live demo at agentshield-demo dot streamlit dot app." |

## Recording plan
1. **Real-model recordings** (Claude, on a day with Groq budget): only the scenarios the video and stage need, e.g. `python -m demo_agent.run --scenario attack_bill_bn --compare --provider groq --record`, plus `attack_bill_banglish`, `benign_pay_bills`, `benign_send_large`. Commit `demo_agent/recordings/`, push, reboot the app.
2. **Screen footage** (Claude): Playwright drives the real dashboard and records each segment as video at 1920×1080; the Recorded run makes it instant and identical every take.
3. **Voice** (team member): read the narration column in a quiet room, phone microphone is fine; one file per row or one take. Speak slowly; pauses are fine.
4. **Edit** (Claude): title and closing cards, captions (English, with Bangla where the product shows Bangla), cuts timed to the voice, export MP4 1080p.
5. **Upload** (team): YouTube, visibility "Unlisted", title "AgentShield: agent-action security for Bangla (CloudCamp AI Builders Congress 2026)". Paste the link into the form.

## Checks before upload
- Every number on screen and in the voice matches `docs/results.md`.
- The recorded run is labelled as a recording in the dashboard (it is, automatically).
- Length between 2:00 and 3:00; audio clear; no API keys, emails or personal data visible.
