"""Original background score for the v2 film (new web UI), synthesized from code (no samples, no licence).

    python video/make_score2.py     # writes video/film2/assets/music/score.mp3

Same instruments as make_score.py; the sections follow film2's scenes (seconds = film time): a dark pulse under
the phone, minor tension through the inbox and the stolen money, a held breath for the reveal, a driving
arpeggio through the four checks, silence for the BLOCK hit, a lift into the principle and the payoff,
confident numbers, a held question while a big transfer waits for the user's yes, a short return to tension
for the second act, a warm build for who it is for and how it scales, and the resolved chord on the mark.
The music ducks under the narration (clip times read from film2/index.html).
Two scenes were inserted on 18 Nov (INSERTS): ask at 99.6 s and reach before the close card. The sections below
keep their original times and place() moves them; the inserted sections play at their final film times.
"""
import json
import re
import subprocess
import wave
from pathlib import Path

import numpy as np

SR = 44100
# (original time, seconds inserted there): a section written for t >= that time plays that much later
INSERTS = [(99.6, 12.0), (126.0, 27.0)]       # ask (12 s), reach (27 s, where the close card started)
ASK0, ASK_LEN = INSERTS[0]                    # the ask section plays at 99.6-111.6 film time
REACH_AT, REACH_LEN = 126.0 + 12.0, 27.0      # the reach section plays at 138.0-165.0 film time
DUR = 134.5 + sum(n for _, n in INSERTS)
SHIFT_ON = True                               # off while the inserted sections are written
N = int(SR * DUR)
BEAT = 60 / 90          # 90 BPM
BAR = 4 * BEAT
HERE = Path(__file__).resolve().parent
FILM = HERE / "film2"
OUT = FILM / "assets" / "music" / "score.mp3"
rng = np.random.default_rng(7)

dry = np.zeros((2, N))
send = np.zeros((2, N))   # reverb send


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def place(sig, t0, gain=1.0, pan=0.0, rev=0.3, shift=None):
    """Mix a mono signal at film time t0; pan -1..1 (equal power). Original section times move by the scenes
    inserted before them (INSERTS); the inserted sections are written in final film time (shift off)."""
    if SHIFT_ON if shift is None else shift:
        t0 += sum(n for at, n in INSERTS if t0 >= at - 1e-9)
    i = int(t0 * SR)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    a = (pan + 1) * np.pi / 4
    for ch, g in ((0, np.cos(a)), (1, np.sin(a))):
        dry[ch, i:i + len(sig)] += sig * g
        send[ch, i:i + len(sig)] += sig * g * rev


def smooth_env(n, attack, release):
    e = np.ones(n)
    a, r = min(int(attack * SR), n // 2), min(int(release * SR), n // 2)
    if a:
        x = np.linspace(0, 1, a)
        e[:a] = x * x * (3 - 2 * x)
    if r:
        x = np.linspace(1, 0, r)
        e[-r:] *= x * x * (3 - 2 * x)
    return e


# ---------- instruments ----------
def pad(notes, dur, bright=1.0):
    """Warm detuned additive pad; bright widens the harmonic roll-off (a filter opening)."""
    n = int((dur + 2.0) * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for m in notes:
        for cents in (-7, 0, 7):
            f = hz(m) * 2 ** (cents / 1200)
            for h in range(1, 9):
                if f * h > 6000:
                    break
                amp = np.exp(-h / (1.6 * bright)) / h
                out += amp * np.sin(2 * np.pi * f * h * t + rng.uniform(0, 2 * np.pi))
    out *= 1 + 0.12 * np.sin(2 * np.pi * 0.17 * t)
    return out * smooth_env(n, 1.4, 2.0) / (len(notes) * 3)


def piano(m, length=2.8):
    """Soft felt-piano pluck."""
    n = int(length * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k, a in enumerate((1.0, 0.42, 0.2, 0.1, 0.05), start=1):
        f = hz(m) * k * (1 + 0.0004 * k * k)
        out += a * np.sin(2 * np.pi * f * t) * np.exp(-t * (1.1 + 1.4 * k))
    att = np.minimum(1, t / 0.006)
    return out * att * 0.5


def pluck(m, length=0.9):
    """Bright synth pluck for arpeggios."""
    n = int(length * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, 7):
        out += (1 / k) * np.sin(2 * np.pi * hz(m) * k * t) * np.exp(-t * (5 + 3 * k))
    return out * np.minimum(1, t / 0.003) * 0.45


def sub(m, length):
    n = int(length * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * hz(m) * t) + 0.25 * np.sin(4 * np.pi * hz(m) * t)
    return s * np.minimum(1, t / 0.01) * np.exp(-t * 2.2 / length)


def kick():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 44 + 90 * np.exp(-t / 0.035)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)


def tick():
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    noise = np.diff(rng.standard_normal(n + 1))
    return noise * np.exp(-t / 0.007) * 0.25


# ---------- harmony ----------
DM7 = [50, 57, 60, 65]       # D minor 7
BBMAJ7 = [46, 53, 57, 62]
GM9 = [43, 50, 53, 57, 58]
ASUS = [45, 52, 57, 62]
A7 = [45, 52, 55, 61]
FADD9 = [41, 53, 57, 60, 67]
CADD9 = [48, 55, 62, 64]
DM9 = [50, 57, 60, 64, 65]
DARK = [38, 45, 50]

MINOR = [DM7, BBMAJ7, GM9, ASUS]
MAJOR = [BBMAJ7, FADD9, CADD9, DM9]


def chords(t0, t1, prog, bars_each, pad_gain, bright=1.0):
    t, i = t0, 0
    while t < t1 - 0.3:
        c = prog[i % len(prog)]
        d = min(bars_each * BAR, t1 - t)
        place(pad(c, d, bright), t, pad_gain, 0, rev=0.5)
        place(sub(c[0] - 12, d), t, pad_gain * 0.9, 0, rev=0.05)
        t += bars_each * BAR
        i += 1


def chord_at(t, t0, prog, bars_each):
    return prog[int((t - t0) // (bars_each * BAR)) % len(prog)]


def grid(t0, t1, step):
    return np.arange(t0, t1 - 0.05, step)


# ---------- the score, section by section (film seconds) ----------
# 1 PHONE 0-7.2: a dark drone, a clock tick, a heartbeat
place(pad(DARK, 7.0, 0.6), 0.0, 0.55, 0, rev=0.4)
place(sub(26, 7.1), 0.2, 0.5, 0, rev=0.0)
for k, t in enumerate(grid(0.2, 7.1, BEAT / 2)):
    place(tick(), t, 0.5 if k % 2 else 0.25, 0.35 if k % 2 else -0.35, rev=0.15)
for t in grid(0.2, 7.1, BAR / 2):
    place(kick(), t, 0.22, 0, rev=0.05)
    place(kick(), t + 0.22, 0.14, 0, rev=0.05)

# 2 INBOX 7.2-25.0: minor progression, sparse felt piano, quiet ticks
chords(7.2, 25.0, MINOR, 2, 0.5)
for t in grid(7.2, 25.0, BEAT / 2):
    pos = round((t - 7.2) / (BEAT / 2)) % 8
    if pos in (0, 3, 6):
        c = chord_at(t, 7.2, MINOR, 2)
        place(piano(c[[0, 2, 3, 1][pos % 4] % len(c)] + 12), t, 0.3, rng.uniform(-0.4, 0.4), rev=0.45)
    place(tick(), t, 0.18 if pos % 2 else 0.08, 0.3, rev=0.1)

# 3 THE MONEY GOES 25.0-35.4: a bass pulse and a soft kick
chords(25.0, 35.4, MINOR, 2, 0.5)
for t in grid(25.0, 35.4, BEAT / 2):
    c = chord_at(t, 25.0, MINOR, 2)
    place(sub(c[0] - 12, 0.3), t, 0.28, 0, rev=0.0)
    pos = round((t - 25.0) / (BEAT / 2)) % 8
    if pos in (0, 4):
        place(kick(), t, 0.3, 0, rev=0.05)
    if pos in (0, 3, 6):
        place(piano(c[pos % len(c)] + 12), t, 0.26, rng.uniform(-0.4, 0.4), rev=0.45)
    place(tick(), t, 0.16 if pos % 2 else 0.07, -0.3, rev=0.1)

# 4 REVEAL 35.4-43.6: a held breath (suspended chord), then the zoom through the dot
place(pad(ASUS, 7.4, 1.0), 35.4, 0.5, 0, rev=0.6)
place(sub(33, 7.6), 35.4, 0.4, 0, rev=0.0)
for j, m in enumerate([57, 62, 64, 69]):
    place(piano(m + 12, 4.0), 41.7 + j * 0.06, 0.24, -0.3 + j * 0.2, rev=0.6)

# 5 THE CHECKS 43.6-64.5: harmony every bar, 16th arpeggio, soft four-on-the-floor
chords(43.6, 62.4, MINOR, 1, 0.45, bright=1.3)
for t in grid(43.6, 62.4, BEAT / 4):
    c = chord_at(t, 43.6, MINOR, 1)
    k = round((t - 43.6) / (BEAT / 4))
    place(pluck(c[k % len(c)] + 12), t, 0.2, 0.5 if k % 2 else -0.5, rev=0.35)
    if k % 4 == 0:
        place(kick(), t, 0.33, 0, rev=0.05)
        place(sub(c[0] - 12, 0.4), t, 0.3, 0, rev=0.0)
    place(tick(), t, 0.12 if k % 2 else 0.05, 0.2, rev=0.1)
# 62.4-64.45: the dominant swells, then silence for the BLOCK
place(pad(A7, 2.1, 2.2), 62.4, 0.62, 0, rev=0.6)
place(sub(33, 2.1), 62.4, 0.5, 0, rev=0.0)

# 6 LIFT 65.6-74.8: the major lift through "AI where judgment is needed"
chords(65.6, 74.8, MAJOR, 2, 0.46, bright=1.2)
for t in grid(65.6, 74.8, BEAT / 2):
    c = chord_at(t, 65.6, MAJOR, 2)
    k = round((t - 65.6) / (BEAT / 2))
    place(pluck(c[k % len(c)] + 12, 1.2), t, 0.15, 0.45 if k % 2 else -0.45, rev=0.5)

# 7 PAYOFF 74.8-88.2: builds to the payoff (84.82), then a full chord rings
chords(74.8, 84.8, MAJOR, 1, 0.45, bright=1.3)
for t in grid(74.8, 84.7, BEAT / 4):
    c = chord_at(t, 74.8, MAJOR, 1)
    k = round((t - 74.8) / (BEAT / 4))
    place(pluck(c[k % len(c)] + 12), t, 0.12 + 0.08 * (t - 74.8) / 10, 0.5 if k % 2 else -0.5, rev=0.35)
    if k % 8 == 0:
        place(kick(), t, 0.3, 0, rev=0.05)
place(pad(FADD9 + [72], 3.6, 1.6), 84.82, 0.68, 0, rev=0.7)
place(sub(29, 3.4), 84.82, 0.55, 0, rev=0.0)
for j, m in enumerate([53, 57, 60, 67, 72]):
    place(piano(m + 12, 3.4), 84.82 + j * 0.035, 0.3, -0.4 + j * 0.2, rev=0.7)

# 8 NUMBERS 88.2-99.6: full and confident
chords(88.2, 99.6, MAJOR, 2, 0.5, bright=1.35)
for t in grid(88.2, 99.6, BEAT / 4):
    c = chord_at(t, 88.2, MAJOR, 2)
    k = round((t - 88.2) / (BEAT / 4))
    place(pluck(c[k % len(c)] + 12), t, 0.15, 0.5 if k % 2 else -0.5, rev=0.35)
    if k % 8 == 0:
        place(kick(), t, 0.32, 0, rev=0.05)
    if k % 2 == 0:
        place(sub(c[0] - 12, 0.3), t, 0.22, 0, rev=0.0)

# 9 SECOND ACT 99.6-117.0: back to minor for the scam call, then the network lifts it (from 105)
chords(99.6, 105.0, MINOR, 1, 0.45)
for t in grid(99.6, 105.0, BEAT / 2):
    pos = round((t - 99.6) / (BEAT / 2)) % 8
    place(tick(), t, 0.16 if pos % 2 else 0.07, 0.3, rev=0.1)
    if pos in (0, 4):
        place(kick(), t, 0.26, 0, rev=0.05)
chords(105.0, 117.0, MAJOR, 2, 0.46, bright=1.25)
for t in grid(105.0, 117.0, BEAT / 4):
    c = chord_at(t, 105.0, MAJOR, 2)
    k = round((t - 105.0) / (BEAT / 4))
    place(pluck(c[k % len(c)] + 12), t, 0.14, 0.5 if k % 2 else -0.5, rev=0.35)
    if k % 8 == 0:
        place(kick(), t, 0.28, 0, rev=0.05)

# 10 DEVELOPERS 117.0-126.0: calmer, pad and piano
chords(117.0, 126.0, MAJOR, 2, 0.44)
for t in grid(117.0, 126.0, BEAT / 2):
    c = chord_at(t, 117.0, MAJOR, 2)
    k = round((t - 117.0) / (BEAT / 2))
    place(pluck(c[k % len(c)] + 12, 1.2), t, 0.12, 0.4 if k % 2 else -0.4, rev=0.5)
    if k % 8 in (0, 5):
        place(piano(c[(k // 3) % len(c)] + 12), t, 0.2, rng.uniform(-0.3, 0.3), rev=0.5)

# 11 CLOSE 126.0-134.5: the resolved chord on the mark (126.45) rings out
final = pad(FADD9 + [72], 7.8, 1.5)
place(final, 126.45, 0.7, 0, rev=0.7)
place(sub(29, 7.8), 126.45, 0.6, 0, rev=0.0)
for j, m in enumerate([53, 57, 60, 67, 72]):
    place(piano(m + 12, 6.0), 126.45 + j * 0.035, 0.3, -0.4 + j * 0.2, rev=0.7)

# 8b ASK 99.6-111.6 (real film time): the transfer the user typed waits for their yes. An open, suspended chord
# (a question; it resolves into the D minor of the second act), a slow clock, a soft piano on "asks you first".
# Own random generator, so every other section (and the reverb) sounds exactly as before the insert.
_rng_main, rng = rng, np.random.default_rng(8)
A0 = ASK0
place(pad(ASUS, ASK_LEN - 0.6, 1.0), A0, 0.48, 0, rev=0.6, shift=False)
place(sub(33, ASK_LEN - 0.4), A0, 0.34, 0, rev=0.0, shift=False)
for k, t in enumerate(grid(A0 + 0.33, A0 + ASK_LEN - 0.5, BEAT)):
    place(tick(), t, 0.14 if k % 2 else 0.08, 0.3 if k % 2 else -0.3, rev=0.15, shift=False)
for j, m in enumerate([57, 62, 64]):
    place(piano(m + 12, 3.5), A0 + 9.82 + j * 0.06, 0.24, -0.3 + j * 0.3, rev=0.6, shift=False)
rng = _rng_main

# 10b REACH 138.0-165.0 (real film time): who it is for and how it scales. Warm and building: pads and an
# eighth-note pluck that grows, a soft kick from the second act of the scene; it ends on C so the close card's
# F chord resolves it. Own random generator, as above.
_rng_main, rng = rng, np.random.default_rng(9)
SHIFT_ON = False
R0, REACH_PROG, REACH_BARS = REACH_AT, [BBMAJ7, CADD9, DM9, CADD9], 2.5
chords(R0, R0 + REACH_LEN - 0.3, REACH_PROG, REACH_BARS, 0.42, bright=1.2)
for t in grid(R0 + 0.3, R0 + REACH_LEN - 0.6, BEAT / 2):
    c = chord_at(t, R0, REACH_PROG, REACH_BARS)
    k = round((t - R0) / (BEAT / 2))
    place(pluck(c[k % len(c)] + 12, 1.1), t, 0.09 + 0.06 * (t - R0) / REACH_LEN, 0.45 if k % 2 else -0.45, rev=0.45)
    if k % 8 == 0 and t > R0 + 6.0:
        place(kick(), t, 0.22, 0, rev=0.05)
SHIFT_ON = True
rng = _rng_main


# ---------- reverb: stereo decaying noise IR, convolved by FFT ----------
def reverb(x, seconds=3.2):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.zeros_like(x)
    size = 1 << int(np.ceil(np.log2(x.shape[1] + n)))
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-t * 6.9 / seconds)
        ir = np.convolve(ir, np.ones(6) / 6, mode="same")      # darker tail
        ir[: int(0.02 * SR)] = 0                              # 20 ms pre-delay
        y = np.fft.irfft(np.fft.rfft(x[ch], size) * np.fft.rfft(ir, size), size)[: x.shape[1]]
        out[ch] = y / np.sqrt(np.sum(ir ** 2))
    return out


mix = dry + 0.45 * reverb(send)

# the BLOCK hit (64.54) lands in silence; the lift swells in from 65.6
g0, g1, ramp = int(64.45 * SR), int(65.55 * SR), int(0.04 * SR)
mix[:, g0:g0 + ramp] *= np.linspace(1, 0, ramp)
mix[:, g0 + ramp:g1] = 0

# ---------- duck under the narration ----------
html = (FILM / "index.html").read_text(encoding="utf-8")
gain = np.ones(N)
for start, length in re.findall(r'id="vo-[^"]+" src="[^"]+" data-start="([0-9.]+)" data-duration="([0-9.]+)"', html):
    a, b = int(float(start) * SR), int((float(start) + float(length)) * SR)
    gain[a:b] = 0.22     # about -13 dB under the voice (0.5 left the voice only 3-7 dB over the music)
k = int(0.3 * SR)
c = np.concatenate([np.zeros(1), np.cumsum(np.pad(gain, (k // 2, k - k // 2 - 1), mode="edge"))])
gain = (c[k:] - c[:-k]) / k   # 0.3 s moving average (same as the old convolve, much faster)
mix *= gain
# fade the very end to silence
tail = int(1.2 * SR)
mix[:, -tail:] *= np.linspace(1, 0, tail) ** 2

mix = np.tanh(mix / (np.max(np.abs(mix)) + 1e-9) * 1.4) / np.tanh(1.4) * 0.89
pcm = (mix.T * 32767).astype(np.int16)

OUT.parent.mkdir(parents=True, exist_ok=True)
wav = OUT.with_suffix(".wav")
with wave.open(str(wav), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
# One static gain to about -20 LUFS (single-pass loudnorm is dynamic and would partly undo the ducking).
meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(wav), "-af", "loudnorm=I=-20:TP=-2:print_format=json",
                       "-f", "null", "-"], capture_output=True, text=True).stderr
meas = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
db = min(-20.0 - float(meas["input_i"]), -1.0 - float(meas["input_tp"]))
print(f"score: {float(meas['input_i']):.1f} LUFS, true peak {float(meas['input_tp']):.1f} dB -> gain {db:+.1f} dB")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-af", f"volume={db:.2f}dB",
                "-ar", "44100", "-c:a", "libmp3lame", "-q:a", "2", str(OUT)], check=True)
wav.unlink()
print("saved", OUT)
