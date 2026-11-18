# REVIEW: AgentShield film v2 (18 Nov 2026)

Render: `renders/agentshield_film2_v4.mp4` (173.5 s = 2:53, 1920x1080, 30 fps, `-q delivery`, about 7 min to render).
History: v1 had the two P1 issues fixed in v2 (below); v2 (134.5 s) was watched by the user, who asked to add the
ASK case; v3 adds the `ask` scene (uploaded to YouTube); v4 adds the `reach` scene (who it is for, how it scales)
after the portal's video guidance, which asks for "AI approach" and "Impact & next step" segments. The user ruled out
plans in the film ("not built yet"), so reach states only what exists. Measured on v4 (snapshot, check): no craft
warnings after two fixes (the judge line was on screen too briefly; a 3.75 s static end, now two lines on their words). Not in git: renders, 12 unused captures in `assets/ui/` (arch_final, bm_text,
dev_terminal, net_ring1, net_s1-3, pg_banner, pg_runcard, pg_step_stolen, pg_top, pg_with), the voice auditions in
`video/samples/`.

## Creative calls
- Built storyline A, "The bill that was never real", with B's 0.8 s decision clock folded into the "how" scene.
  Not built: B "0.8 seconds" as a whole film, C "Night and day" (`video/STORYLINES_v2.md`).
- Voice: en-US-AndrewMultilingualNeural (edge-tts, `video/make_vo2.py`); score synthesized by `video/make_score2.py`.
- ASK (v3) sits after the numbers and before the network act, not inside the payoff: it keeps the payoff's climax
  intact, and it bridges into the second act (a big transfer you type yourself is asked; a small one a scammer
  talks you into looks fine alone, so the network check is needed). Narration: "Some payments are real, just big.
  Fifteen thousand taka to your landlord, typed by you. No attack, but over the limit. So AgentShield asks you
  first." Every claim is from the recorded run (benign_send_large, 13 Nov). Picture: the same phone as the network
  act, then the real map's "Large transfer you typed" flow (live site, reduced motion = its final state), first
  the four checks beside the phone, then the window opens onto the decision and the three outcomes. Music: a held
  A-sus chord and a slow clock (waiting for the user's yes), resolving into the second act's D minor.

## Measured
- `hyperframes check`: 0 errors. 18 lint warnings `gsap_repeated_fromto_without_baseline` kept: every scene uses
  the `ft()` helper, which sets `immediateRender: false` on repeat tweens at runtime; the linter cannot see that.
- Blank frames (v2): only 0.1-0.6 s dips at cuts (24.5, 35.4, 68.6 s: dip to night before the next line). No
  stretch over 3 s without change except the end card (4.3 s hold, on purpose).
- Audio: v1 had the voice only 3.5-7 dB over the music (close line 1.4 dB). Fixed in v2: duck under narration
  0.5 -> 0.22, static loudness gain instead of the dynamic single-pass loudnorm, music `data-volume` 0.5 -> 0.4.
  Voice over music now 10.6-15 dB (ask line 15.0 dB, close line 8.5 dB); in the 300-4000 Hz speech band 13-27 dB
  over music + sfx. Measured, not heard.
- Score after the insert: before 99.6 s and (moved 12 s) after it, identical to the v2 score (difference -58 dB);
  the ask section uses its own random generator so nothing else changed.
- Sound effects: `impact.mp3` is 99.8% energy below 80 Hz (a sub boom). Full-band it outweighs the voice where it
  lands on a line (32.1 "thousand taka", 64.5 "blocked", 94.6 numbers, 138.5 close line); in the speech band the
  voice stays on top. Listen on headphones and on a laptop speaker before upload; lower the impacts if heavy.
- QA from SPEC: frame 0 is the phone with the Bangla bill; 0/24 on screen 19.9-24.2 s; BLOCK hit at 64.5 s with
  "blocked" at 64.65 s; clock 799.4 ms then 0.80 s; payoff lime banner 84.7-88.2 s; ask rings on "typed by you"
  (104.95), "No attack" (106.17), "over the limit" (107.02), ASK rings on "asks" (109.42); "Simulated" chip on
  every network number; URL on the end card about 4 s.

## Looked at only
- Contact sheets every 2 s, 24 key frames at full size, the ask scene at 16 moments. Not checked: the 360 px
  phone sheet.

## Fixed
- v2, P1 t=31.7-35.0 s: the push-in on the stolen tile (2.6x) cut "which the user ne|ver asked" at the right
  edge -> 2.4x, centred on the column.
- v2, P1 narration buried under the music (above).
- v3: an empty chat bubble sat on the phone for 0.8 s before the typing -> the bubble arrives with the typing.

## Open (P2)
- t=11.9-12.2 s: the inbox and the opened email crossfade with both texts readable for a moment.
- t=118-119 s: "One number, paid by many strangers." shows before the "Simulated wallet week" chip arrives
  (the capture itself is labelled simulated).
- Weakest shot: the architecture map at 62-67 s is small on a phone; the big clock carries the read there. The ask
  scene's map text (1.75x) is also small on a phone, fine on a laptop.
