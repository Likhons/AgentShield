# AgentShield demo video: three storylines

Facts every storyline uses (from `docs/results.md`, nothing else): Prompt Guard 2 flagged 0/24 Bangla/Banglish attacks; real model (qwen3.8-27b) on 20 attacks + 20 bill payments: attacks moved money 4/20 without, 0/20 with AgentShield; rent paid 16/20 without and 16/20 with. Demo amounts (৳ 4,500 fake bill, ৳ 8,000 rent) come from the recorded real run and are checked against it before the voice is made.
Real UI only: every product shot is the real dashboard captured in the browser (Playwright), the demo segment from a recorded real-model run.
Assumptions: 2:15–2:45 (form asks 2–3 min), 1920×1080, 30 fps, English narration with the free neural voice `en-IN-PrabhatNeural`, free music and sound effects; nothing paid.

---

## A. "The fake bill" (recommended: a situation every viewer knows, and the product's own side-by-side is the payoff)
**Device:** a moment in someone's day, then life before and after. **Form:** split screen to one.
The viewer sees an ordinary evening task, "pay my pending bills", handed to an AI agent, and watches the same inbox play out twice: once unprotected, once behind AgentShield. The tension is a real Bangla bill that looks exactly like the landlord's, and the relief is watching only the fake one stop.
- **First 2 s:** a phone-style notification slides in: a Bangla electricity bill email, "৳ 4,500 · আজই পরিশোধ করুন", the payee number glowing faint red. VO: "AI agents are starting to pay bills for us."
- **Beats:** hook (the bill arrives) → tension (two emails, real and fake, side by side; Prompt Guard's 0/24 lands as a number) → reveal ("AgentShield" title out of the shield in the dashboard header) → proof (the real dashboard: Run, the agent reads, the left column pays the attacker, the right column stops at BLOCK with the Bangla reason) → payoff (split collapses to one: "AgentShield saved ৳ 4,500", rent still paid) → claim (4/20 → 0/20, 16/20 = 16/20) → end card (shield mark, live demo URL).
- **Look:** the dashboard's own navy and violet; the one material is the email card, which carries across every shot; status colours (red, green) only for money.
- **Sound:** low, warm pulse under the VO; a soft notification ping on the bill, a cash-register tick when money leaves, a heavy lock "clunk" on BLOCK, a single rising tone on the payoff.

## B. "Follow the number"
**Device:** one object across apps. **Form:** object-to-object chain.
One thing is followed the whole way: the attacker's phone number. It sits inside a Bangla email, gets copied by the agent into a send-money call, and then has to pass AgentShield's four checks, each of which questions where it came from, until the policy stamps it BLOCK.
- **First 2 s:** extreme close-up on the digits "01000000666" inside Bangla text; the camera pulls back to reveal it is a bill in an inbox. VO: "This number is not your landlord's."
- **Beats:** hook (the number) → tension (the agent lifts it into `send_money`, amount ৳ 4,500) → reveal (the call hits AgentShield) → proof (taint draws a line from the number back to the email, classifier scans, intent asks "did the user ask?", policy: stranger + untrusted = block) → payoff (BLOCK lands on the real step card, the rent call passes the same gates in green) → claim (the real-LLM numbers) → end card.
- **Look:** dark ground with the number in monospace as the carrier; each check is a gate the number passes through; the real dashboard for the result.
- **Sound:** a ticking data pulse that speeds up as the number travels, a scanner sweep per check, a hard stamp on BLOCK.

## C. "Bangla breaks the guardrail" (the bold one)
**Device:** type carries the argument. **Form:** cut on the beat.
Giant kinetic type in Bangla, Banglish and English argues the case on the music: what the attack says, what a guardrail misses, what AgentShield does, with the real dashboard cut in as proof between the lines.
- **First 2 s:** "পেমেন্ট এখনই করুন" fills the frame, then flips to "payment ekhoni korun", then to "Pay now". VO: "Same sentence. Three ways to write it."
- **Beats:** hook (three scripts of one line) → tension (Prompt Guard 2: 0/24 slams in) → reveal (AgentShield) → proof (hard cuts of the real dashboard: Run, BLOCK, Bangla reason, audit log) → payoff (৳ saved) → claim (4/20 → 0/20 / 16 = 16) → end card.
- **Look:** full-bleed colour fields from the brand palette, huge bilingual type, hard cuts every half beat.
- **Sound:** a driving electronic track with clear beats; cuts land on the kick, a glitch hit on the guardrail miss.
