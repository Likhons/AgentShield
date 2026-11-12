# SPEC: AgentShield demo film

Storyline: **A "The fake bill"**, with B's "follow the number" carrying the how-it-works beat (see STORYLINES.md).

```text
GOAL:    A judge who has never heard of AgentShield ends the film knowing: an AI agent paid a fake
         Bangla bill, AgentShield stopped it without stopping the real rent, and the numbers prove it
         (4/20 -> 0/20 thefts, 16/20 = 16/20 rent). They open the live demo link.

OUTPUT:  HyperFrames, 1920 x 1080, 30 fps, H.264 MP4 for YouTube (unlisted).

TIME:    ~155 s = ~4650 frames. Narrated: the voice is the clock. Beat starts (s, voice clip lengths):
         01 hook 0.0 (8.1) | 02 problem 8.7 (25.0) | 03 setup 34.3 (13.8) | 04 demo 48.7 (21.0)
         | 05 how 70.3 (26.3) | 06 proof 97.2 (28.1) | 07 trust 125.9 (16.0) | 08 close 142.5 (10.2)
         | end-card hold to ~155.0. 0.6 s of air between beats.

LOOK:    Three worlds, each a real medium, plus the end card. Palette shared:
           navy #080D24 (product ground, only where the product is), card #131A38, ink #F5F5FF,
           muted #A8B0CE, violet #7138FF (AgentShield only), red #F04452 (money lost only),
           green #16C784 (money safe / ALLOW only), amber #F5A623 (ASK only).
         W1 MAIL (hook, problem): a light mail client. Ground #EEF0F5, sheet #FFFFFF, ink #111827,
           hairline #D7DBE4. Real email copy from demo_agent/data. Soft paper shadow 0 18px 40px
           rgba(17,24,39,.14). No glow. The fake bill's payee number is the carrier object.
         W2 PRODUCT (setup, demo, proof, trust): the real dashboard captured at 1920x1080 (Playwright),
           shown in a browser frame on navy. Pieces pulled forward at 1.6-2x keep real labels/values.
         W3 GATES (how): a solid violet field #3A1C9E (flat, no gradient) with the number travelling
           left to right through four gate cards rebuilt from the dashboard's pipeline card
           (#131A38, 1px #8C78FF66, radius 18 px). Each gate stamps a verdict chip.
         Type: display Outfit 800, 112 px, tracking -2%, max 6 words a line; body Outfit 500 44 px;
           numbers IBM Plex Mono 600; Bangla Anek Bangla 600 (woff2 in assets/fonts).
           Readable text never under 28 px.
         Light: one paper shadow in W1; product frame shadow 0 40px 80px rgba(0,0,0,.45);
           2% film grain over everything, no vignette.

OBJECTS: the fake Bangla electricity bill email (subject, sender billing@dhaka-power.example,
         amount ৳ 4,500, payee 01000000666) and the landlord's rent email (Karim, ৳ 8,000,
         01000000102), both from the demo data; the payee number in IBM Plex Mono as the carrier;
         the four check gates; the BLOCK / ALLOW chips exactly as the dashboard draws them;
         the shield mark from the dashboard header (SVG, the brand's own).

MOTION:  enter power3.out 18 f; move power2.inOut 16 f; exit power2.in 9 f; camera expo.inOut 20 f;
         stamps: scale 1.25 -> 1 in 6 f power4.out with a 2-frame 6 px shake, nothing else bounces.
         One hero move per shot; secondary moves 60% as far, 4-6 f later. Text never moves while read.
         Transitions (5 kinds, each with a cause):
           T1 object-becomes-world: the notification card grows into the mail client (hook -> problem)
           T2 colour flood: the mail ground floods violet when "AgentShield" is named (-> product)
           T3 zoom through a button: the camera tracks to "Run Scenario" and pushes through it (setup -> demo)
           T4 carry across: the payee number lifts out of the BLOCK step and flies into gate 1 (demo -> how)
           T5 whip: horizontal 0.2 s smear between product pages (proof -> trust), used at most twice

SHOTS:   (s are film time; VO anchor word in quotes; each shot hands off by its transition)
  S1  0.0-4.0   W1. A phone-sized notification drops from top, 2 lines: "বিদ্যুৎ বিল পরিশোধ" /
                "৳ 4,500 · আজই". Anchor "pay bills". Sound: soft notification. -> grows (T1).
  S2  4.0-8.7   W1 mail client fills frame; two emails side by side become the inbox list, the
                fake one under the real rent. Anchor "fake": the payee number underlines red.
  S3  8.7-22.0  W1, push into the fake bill. Bangla body readable at 44 px. A cursor-less "agent
                reading" highlight sweeps line by line (key ticks). Anchor "planted": the number lifts
                1.12x and turns red; the rest dims to 40%.
  S4  22.0-33.7 W1 holds; a guardrail verdict card slides in from right, real model name
                "Prompt Guard 2", and the number "0 / 24" lands (pop) on "none". Holds 3 s.
  S5  34.3-48.1 T2 flood to navy; the real dashboard Playground (capture) arrives in a browser frame;
                camera to the Scenario card, scenario label readable; on "AgentShield" the shield mark in
                the header fills violet. Ends on the camera tracking to "Run Scenario".
  S6  48.7-69.7 T3 through the button into the results: split screen, left column red, right green.
                "paid the fake bill" -> left Stolen −৳ 4,500 counts up (cash tick).
                "blocked" -> right BLOCK chip stamps (lock clunk). "Bangla and English" -> Bangla reason
                pulled forward at 1.8x. "rent still goes through" -> rent ALLOW chip. Ends: the two
                columns collapse into one banner "AgentShield saved ৳ 4,500" (riser + impact, the one
                payoff of the film).
  S7  70.3-96.6 T4: the payee number flies into W3. Gate 1 Taint: a line traces back to the email
                ("came from" -> chip "untrusted email"). Gate 2 Classifier ("instruct the AI").
                Gate 3 Intent ("follow from what the user asked" -> "not asked"). Gate 4 Policy
                ("rules for money" -> BLOCK stamp). Then the rent number runs the same gates, all
                ALLOW. Final line types in: "AI where judgment is needed / Rules where certainty is needed".
  S8  97.2-125.3 W2 Benchmarks page (capture), real-LLM table isolated at 1.8x. "four attacks" ->
                4/20 lands red; "none did" -> 0/20 green; "sixteen of twenty, both times" -> 16/20 and
                16/20 slide to meet and lock together. Small CI caption stays readable.
  S9  125.9-141.9 T5 whip to Audit Log capture (rows with Bangla reasons), then Policies capture,
                then a code card with the real SDK call (ShieldSession.wrap).
  S10 142.5-155.0 End card on navy: the shield mark is carried in by the payee number turning into
                the checkmark stroke; wordmark wipes in; URL agentshield-demo.streamlit.app as a real
                button, held 3 s. Music resolves on the mark.

SOUND:   music bed: calm minimal pulse ~100 bpm, warm, low energy under W1, opens when the product
         appears (S5), holds back at S6 until the payoff, resolves on the end card; voice at 1.0,
         bed at 0.14. Effects only on visible actions: notification (S1), key ticks (S3 reading),
         pop (S4 0/24), whoosh x2 takes (T2, T5), cash tick (S6 money out), lock clunk (BLOCK, S6 and
         S7), riser+impact (S6 payoff, once). Mix -16 to -14 LUFS, true peak <= -1 dBTP.

BANNED:  the skill's default list, plus: dark void with floating UI (product always fills >= 60% of
         frame width), glow/neon/particles, purple gradients (violet is flat), glass cards, three
         cards in a row, KPI grids, everything fading up, titles drifting after they land,
         invented UI (every product pixel is a capture or a rebuild of a captured piece with real
         labels), mocked competitors, any number not in docs/results.md.

QA:      frames 1.0 (notification readable), 20.0 (Bangla legible), 30.0 (0/24), 40.0 (dashboard
         readable), 56.0 (split screen), 64.0 (Bangla reason at 1.8x), 69.0 (payoff banner),
         80.0 (gate 1 trace), 94.0 (two-line principle), 105.0 (4/20 vs 0/20), 120.0 (16 = 16),
         135.0 (audit), 152.0 (end card + URL). Every on-screen number matches docs/results.md
         and the recorded run.
```
