# REVIEW: AgentShield film v2 (18 Nov 2026)

Render: `renders/agentshield_film2_v2.mp4` (134.5 s, 1920x1080, 30 fps, `-q delivery`, 30.9 MB, about 6 min to
render). v1 (`agentshield_film2_v1.mp4`) had the two P1 issues below. Not in git: renders, 12 unused captures in
`assets/ui/` (arch_final, bm_text, dev_terminal, net_ring1, net_s1-3, pg_banner, pg_runcard, pg_step_stolen, pg_top,
pg_with), the voice auditions in `video/samples/`.

## Creative calls
- Built storyline A, "The bill that was never real", with B's 0.8 s decision clock folded into the "how" scene.
  Not built: B "0.8 seconds" as a whole film, C "Night and day" (`video/STORYLINES_v2.md`).
- Voice: en-US-AndrewMultilingualNeural (edge-tts, `video/make_vo2.py`); score synthesized by `video/make_score2.py`.

## Measured (on the rendered v1 file, then on the fixed inputs)
- `hyperframes check`: 0 errors. 16 lint warnings `gsap_repeated_fromto_without_baseline` kept: every scene uses the
  `ft()` helper, which sets `immediateRender: false` on repeat tweens at runtime; the linter cannot see that. The
  rendered frames show no element in a wrong rest state.
- Blank frames: only 0.1-0.6 s dips at cuts (24.5, 35.4, 68.6 s: dip to night before the next line). No stretch over
  3 s without change except the end card (4.3 s hold, on purpose).
- Audio (v1): -16.7 LUFS integrated, true peak -1 dB, no clipping. Voice was only 3.5-7 dB over the music during
  speech (close line 1.4 dB). Fixed: duck under narration 0.5 -> 0.22, static loudness gain instead of the dynamic
  single-pass loudnorm, music `data-volume` 0.5 -> 0.4. Now 10.6-14.7 dB (close line 8.7 dB); music between lines
  stays at the v1 level. Measured, not heard.
- QA from SPEC: frame 0 is the phone with the Bangla bill; 0/24 on screen 19.9-24.2 s; BLOCK hit at 64.5 s with
  "blocked" at 64.65 s; clock 799.4 ms then 0.80 s; payoff lime banner 84.7-88.2 s; "Simulated" chip on every
  network number; URL on the end card about 4 s.

- v2 render checked: frames differ from v1 only at 31.7-35.4 s (the reframed shot); -16.6 LUFS, true peak -1.1 dB.
- Sound effects: `impact.mp3` is 99.8% energy below 80 Hz (a sub boom). Full-band it outweighs the voice where it
  lands on a line (32.1 "thousand taka", 64.5 "blocked", 94.6 numbers, 126.5 close line), but in the 300-4000 Hz
  speech band the voice sits 13-27 dB over music + sfx on average (worst 10% of frames: 5.7 dB, the close line).
  Listen on headphones and on a laptop speaker before upload; lower the impacts if the booms feel too heavy.

## Looked at only
- Contact sheets every 2 s and 24 key frames at full size. Not checked: the 360 px phone sheet.

## Fixed in v2
- P1 t=31.7-35.0 s: the push-in on the stolen tile (2.6x) cut "which the user ne|ver asked" at the right edge ->
  2.4x, centred on the column; the whole "MONEY STOLEN" line and the user's request now sit inside the frame.
- P1 narration buried under the music (above).

## Open (P2)
- t=11.9-12.2 s: the inbox and the opened email crossfade with both texts readable for a moment.
- t=106-107 s: "One number, paid by many strangers." shows before the "Simulated wallet week" chip arrives
  (the capture itself is labelled simulated).
- Weakest shot: the architecture map at 62-67 s is small on a phone; the big clock carries the read there.
