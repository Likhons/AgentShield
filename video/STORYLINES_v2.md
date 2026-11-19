# AgentShield demo film v2 (new web UI): three storylines

Why v2: the first film (`STORYLINES.md`, `SPEC.md`, now only in git history) was built on the old Streamlit dashboard (navy and violet). The product now
lives at https://agent-shield-demo.vercel.app with a new look (warm black #0a0b09 / cream #f2f0e8, pastel lime #c2ef6a,
Bricolage Grotesque, Fraunces italic accent, JetBrains Mono, Anek Bangla / Baloo Da 2), a live architecture map and a
Network page. Every product shot is captured from that site.

Facts every storyline may use (sources: `docs/results.md`, the 13 Nov recorded run, `benchmark/results/network_20261117-175247`):
- Prompt Guard 2 flagged 0 of 24 Bangla/Banglish attacks.
- Real model (qwen3.8-27b), 20 attacks + 20 bill payments: money moved 4/20 without, 0/20 with AgentShield; rent paid 16/20 both.
- Recorded run (13 Nov, n=1): unprotected, qwen paid the fake bill (৳4,500 to 01000000666); protected: fake bill BLOCK
  (taint 0.90, classifier 0.30, intent 0.90, policy 0.95; score 0.72 → ask, rule → block), rent ৳8,000 ALLOW, reasons in Bangla.
- Network check, SIMULATED wallet week: the phone-scam ring's numbers were flagged after 12, then 4, then 1 people;
  0 of 1,109 real accounts flagged.
Assumptions: 2:20–2:45, 1920×1080, 30 fps, English narration with the free neural voice `en-IN-PrabhatNeural` (edge-tts),
the project's own synthesized score and sound effects; nothing paid.

---

## A. "The bill that was never real" (recommended: a situation anyone follows, and it has a second act the old film lacked)
**Device:** a moment in someone's day, then one number followed through the product. **Form:** object-to-object chain.
A person asks their agent to pay the bills and wakes up to a payment for a bill that never existed. We follow the
attacker's number from the Bangla email into AgentShield's gateway, watch four checks question it, and see it stopped
while the real rent goes through. Then a twist: a scam with no email at all, caught only by looking across all users.
- **First 2 s:** a phone lock screen at night, one notification in Bangla: "বিদ্যুৎ বিল · ৳4,500 · আজই পরিশোধ করুন",
  then an agent toast underneath: "Paid ৳4,500". VO: "We asked an AI agent to pay our bills."
- **Beats:** hook (the payment) → tension (two emails, one fake; Prompt Guard 0/24; the real model pays) → reveal
  ("The agent proposes. AgentShield decides.") → proof (the number travels the real architecture map; four checks; BLOCK)
  → payoff (Playground side by side: attacker ৳0, rent paid, Bangla reason) → claim (4/20 → 0/20, 16/20 = 16/20)
  → second act (phone scam, network check, 12 → 4 → 1, simulated) → end card.
- **Look:** the product's own warm black and lime; the one carrier is the payee number in JetBrains Mono, lime when
  trusted, red when tainted; day mode (cream paper) for the mail world, night for the product.
- **Sound:** low warm pulse under the voice; a phone buzz on the notification, a soft cash tick when money leaves,
  a heavy stamp on BLOCK, one rising tone on the payoff.

## B. "0.8 seconds" (the bold one)
**Device:** the object is the explanation. **Form:** one continuous take, in slow motion.
The real decision on the fake bill took about 0.8 seconds. The film replays those 0.8 seconds stretched across a minute,
with a running clock in the corner, while the camera travels through the gateway: 0.31 ms taint, 0.36 ms classifier,
797 ms for the judge, 0.16 ms policy, then the stamp.
- **First 2 s:** a clock at 0.000 s over the agent's `send_money(01000000666, 4500)`; the clock starts crawling. VO:
  "This is the most important second of an AI agent's day."
- **Beats:** hook (the clock) → tension (what the agent read; 0/24) → reveal (the gateway) → proof (each check as a stop,
  its real time on the clock) → payoff (BLOCK at 0.799 s, rent passes) → claim (numbers) → end card.
- **Look:** near-black with the clock as the carrier; the architecture map as the set.
- **Sound:** a ticking pulse that slows and speeds with the clock; a deep hit when time snaps back to real speed.

## C. "Night and day"
**Device:** life before and after. **Form:** match cuts on the product's own theme switch.
The unprotected story plays in the dark (night mode); every time the narrator says "AgentShield", the real theme switch
in the header flips and the same screen returns in day mode, protected. The switch's circular wipe is the transition.
- **First 2 s:** the night-mode moon switch in close-up; a finger taps it; the frame wipes from black to cream. VO:
  "Same agent. Same inbox. One switch."
- **Beats:** hook (the switch) → tension (night: the agent pays the fake bill) → reveal (switch: day) → proof (day: the
  checks, BLOCK, rent paid) → claim → twist (network) → end card.
- **Look:** the two real themes as the two worlds; the switch as the carrier.
- **Sound:** a crisp click on each switch; the night side has a low drone, the day side opens up.

---

## A, full narration script (draft, about 330 words, about 2:35)

| # | Time | On screen | Voice |
|---|---|---|---|
| 1 | 0:00–0:07 | Phone at night. Bangla bill notification, then the agent's toast "Paid ৳4,500". Freeze. | "We asked an AI agent to pay our bills. It paid one that was never real." |
| 2 | 0:07–0:20 | Day-mode mail client: the landlord's real rent email and the fake Bangla bill side by side. The payee number 01000000666 turns red. | "Agents now read our emails and pay what they find. An attacker only needs a bill that looks real." |
| 3 | 0:20–0:30 | The fake bill's Bangla text; a guardrail card slides in: "Prompt Guard 2", and **0 / 24** stamps. | "And in Bangla, today's guardrails barely notice: Prompt Guard 2 flagged zero of our twenty-four Bangla and Banglish attacks." |
| 4 | 0:30–0:40 | Playground, recorded run, left column only: the agent reads, pays, "−৳4,500" counts up. | "A real open model, asked to pay the pending bills, paid the attacker four and a half thousand taka." |
| 5 | 0:40–0:47 | Hard cut to black, then the landing line types in: "The agent proposes." / "AgentShield decides." (Fraunces italic) | "So we built a gate between the agent and its tools. The agent proposes. AgentShield decides." |
| 6 | 0:47–1:20 | The architecture map. The payee number rides the trace into the gateway. Each check row lights with its real score as it is named. Decision strip: 0.72 → BLOCK stamp. | "Every tool call stops here before it runs. Where did this number come from? An email, not you. Is the email giving the AI orders? No, it reads like a normal bill. Did you ask for this payment? The judge says no. Then a fixed rule settles it: money to a stranger, found only in untrusted text, is blocked." |
| 7 | 1:20–1:27 | Line on the map's ground: "AI where judgment is needed. Rules where certainty is needed." | "AI where judgment is needed. Rules where certainty is needed." |
| 8 | 1:27–1:45 | Playground side by side: left −৳4,500 red, right ৳0; BLOCK step with the Bangla reason pulled forward; the rent ALLOW; banner "AgentShield saved ৳4,500". | "Same model, same inbox. The fake bill never runs, the real rent still goes through, and the user reads why, in Bangla." |
| 9 | 1:45–2:02 | Benchmarks: 4/20 → 0/20 lands; 16/20 and 16/20 meet. | "Across twenty attacks and twenty real bills: four thefts without AgentShield, none with it, and the rent paid exactly as often." |
| 10 | 2:02–2:26 | Second act. A user types a number after a call; the map shows every check passing: ALLOW. Cut to the Network page: 12 strangers, 89% passed on, FLAGGED; "caught after 12 → 4 → 1"; tag SIMULATED. | "Some scams skip the email: the victim types the number. One call looks fine. Across all users it does not. In our simulated wallet week, the network check flagged the scam number after twelve people, and the next ones after four, then one." |
| 11 | 2:26–2:34 | Developer terminal (Python SDK tab), the two `session.wrap` lines highlighted; the real audit log. | "A few lines of code put AgentShield in front of an agent's tools, and every decision is logged with its reason." |
| 12 | 2:34–2:42 | End card: the shield mark carried in by the number, "The agent may be fooled. The money is not.", agent-shield-demo.vercel.app | "The agent may be fooled. The money is not." |


**Picked (18 Nov): A + B's clock**, voice en-US-AndrewMultilingualNeural, English only. Built in `film2/` (SPEC.md there); the final narration is `make_vo2.py`.
