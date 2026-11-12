"""Original background score for the AgentShield film, synthesized from code (no samples, no licence).

    python video/make_score.py      # writes video/film/assets/music/score.mp3

Every section starts on a cut of the film (seconds below = film time), so the music turns when
the picture does: dark pulse under the cold open, minor-key tension through the problem and the
demo, silence for the BLOCK hit, a warm major lift for "how" and the proof, a resolved chord on
the logo. The music ducks under the narration (clip times read from film/index.html).
"""
import re
import subprocess
import wave
from pathlib import Path

import numpy as np

SR = 44100
DUR = 155.0
N = int(SR * DUR)
BEAT = 60 / 90          # 90 BPM
BAR = 4 * BEAT
HERE = Path(__file__).resolve().parent
FILM = HERE / "film"
OUT = FILM / "assets" / "music" / "score.mp3"
rng = np.random.default_rng(7)

dry = np.zeros((2, N))
send = np.zeros((2, N))   # reverb send


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def place(sig, t0, gain=1.0, pan=0.0, rev=0.3):
    """Mix a mono signal at film time t0; pan -1..1 (equal power)."""
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
# 1 COLD OPEN 0-8.7: a dark drone, a clock tick, a heartbeat; dips for the rewind at 5.1
place(pad(DARK, 8.4, 0.6), 0.0, 0.55, 0, rev=0.4)
place(sub(26, 8.6), 0.25, 0.5, 0, rev=0.0)
for k, t in enumerate(grid(0.3, 8.6, BEAT / 2)):
    if 5.0 < t < 5.7:
        continue
    place(tick(), t, 0.5 if k % 2 else 0.25, 0.35 if k % 2 else -0.35, rev=0.15)
for t in grid(0.3, 8.6, BAR / 2):
    if 5.0 < t < 5.7:
        continue
    place(kick(), t, 0.22, 0, rev=0.05)
    place(kick(), t + 0.22, 0.14, 0, rev=0.05)

# 2 PROBLEM 8.7-34.3: minor progression, sparse felt piano, quiet ticks
chords(8.7, 34.3, MINOR, 2, 0.5)
for t in grid(8.7, 34.3, BEAT / 2):
    pos = round((t - 8.7) / (BEAT / 2)) % 8
    if pos in (0, 3, 6):
        c = chord_at(t, 8.7, MINOR, 2)
        place(piano(c[[0, 2, 3, 1][pos % 4] % len(c)] + 12), t, 0.3, rng.uniform(-0.4, 0.4), rev=0.45)
    place(tick(), t, 0.18 if pos % 2 else 0.08, 0.3, rev=0.1)

# 3 SETUP 34.3-48.7: add a bass pulse and a soft kick
chords(34.3, 48.7, MINOR, 2, 0.5)
for t in grid(34.3, 48.7, BEAT / 2):
    c = chord_at(t, 34.3, MINOR, 2)
    place(sub(c[0] - 12, 0.3), t, 0.28, 0, rev=0.0)
    pos = round((t - 34.3) / (BEAT / 2)) % 8
    if pos in (0, 4):
        place(kick(), t, 0.3, 0, rev=0.05)
    if pos in (0, 3, 6):
        place(piano(c[pos % len(c)] + 12), t, 0.26, rng.uniform(-0.4, 0.4), rev=0.45)
    place(tick(), t, 0.16 if pos % 2 else 0.07, -0.3, rev=0.1)

# 4 DEMO 48.7-65.3: harmony moves every bar, 16th arpeggio, four-on-the-floor (soft)
chords(48.7, 65.3, MINOR, 1, 0.45, bright=1.3)
for t in grid(48.7, 65.3, BEAT / 4):
    c = chord_at(t, 48.7, MINOR, 1)
    k = round((t - 48.7) / (BEAT / 4))
    place(pluck(c[k % len(c)] + 12), t, 0.2, 0.5 if k % 2 else -0.5, rev=0.35)
    if k % 4 == 0:
        place(kick(), t, 0.33, 0, rev=0.05)
        place(sub(c[0] - 12, 0.4), t, 0.3, 0, rev=0.0)
    place(tick(), t, 0.12 if k % 2 else 0.05, 0.2, rev=0.1)
# 65.3-68.6: the dominant swells with the riser, then everything stops for the BLOCK
place(pad(A7, 3.3, 2.2), 65.3, 0.62, 0, rev=0.6)
place(sub(33, 3.3), 65.3, 0.5, 0, rev=0.0)

# 5 HOW 70.3-97.2: the major lift; gentle 8th arpeggio, kick enters after 4 bars
chords(70.3, 97.2, MAJOR, 2, 0.48, bright=1.2)
for t in grid(70.3, 97.2, BEAT / 2):
    c = chord_at(t, 70.3, MAJOR, 2)
    k = round((t - 70.3) / (BEAT / 2))
    place(pluck(c[k % len(c)] + 12, 1.2), t, 0.17, 0.45 if k % 2 else -0.45, rev=0.5)
    if k % 8 in (0, 3, 6):
        place(piano(c[(k // 2) % len(c)] + 12), t, 0.22, rng.uniform(-0.3, 0.3), rev=0.45)
    if t > 70.3 + 4 * BAR and k % 4 == 0:
        place(kick(), t, 0.26, 0, rev=0.05)

# 6 PROOF 97.2-125.9: full and confident
chords(97.2, 125.9, MAJOR, 2, 0.5, bright=1.35)
for t in grid(97.2, 125.9, BEAT / 4):
    c = chord_at(t, 97.2, MAJOR, 2)
    k = round((t - 97.2) / (BEAT / 4))
    place(pluck(c[k % len(c)] + 12), t, 0.16, 0.5 if k % 2 else -0.5, rev=0.35)
    if k % 8 == 0:
        place(kick(), t, 0.34, 0, rev=0.05)
    if k % 2 == 0:
        place(sub(c[0] - 12, 0.3), t, 0.24, 0, rev=0.0)
        place(tick(), t, 0.13 if k % 4 else 0.06, 0.25, rev=0.1)

# 7 TRUST 125.9-142.5: calmer, pad and piano with a soft 8th arpeggio
chords(125.9, 142.5, MAJOR, 2, 0.45)
for t in grid(125.9, 142.5, BEAT / 2):
    c = chord_at(t, 125.9, MAJOR, 2)
    k = round((t - 125.9) / (BEAT / 2))
    place(pluck(c[k % len(c)] + 12, 1.2), t, 0.13, 0.4 if k % 2 else -0.4, rev=0.5)
    if k % 8 in (0, 5):
        place(piano(c[(k // 3) % len(c)] + 12), t, 0.22, rng.uniform(-0.3, 0.3), rev=0.5)

# 8 CLOSE 142.5-155: a short climb, then the resolved chord on the logo (148.9) rings out
place(pad(BBMAJ7, BAR * 1.2, 1.4), 142.5, 0.5, 0, rev=0.5)
place(pad(CADD9, 148.9 - 142.5 - BAR * 1.2, 1.8), 142.5 + BAR * 1.2, 0.56, 0, rev=0.5)
for t in grid(142.5, 148.8, BEAT / 4):
    k = round((t - 142.5) / (BEAT / 4))
    c = BBMAJ7 if t < 142.5 + BAR * 1.2 else CADD9
    place(pluck(c[k % len(c)] + 12), t, 0.12 + 0.1 * (t - 142.5) / 6.3, 0.5 if k % 2 else -0.5, rev=0.35)
final = pad(FADD9 + [72], 5.6, 1.5)
place(final, 148.9, 0.7, 0, rev=0.7)
place(sub(29, 6.0), 148.9, 0.6, 0, rev=0.0)
for j, m in enumerate([53, 57, 60, 67, 72]):
    place(piano(m + 12, 5.0), 148.9 + j * 0.035, 0.3, -0.4 + j * 0.2, rev=0.7)


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

# the BLOCK hit (68.71) lands in silence; the major lift swells in from 70.3
g0, g1, ramp = int(68.62 * SR), int(70.25 * SR), int(0.04 * SR)
mix[:, g0:g0 + ramp] *= np.linspace(1, 0, ramp)
mix[:, g0 + ramp:g1] = 0

# ---------- duck under the narration ----------
html = (FILM / "index.html").read_text(encoding="utf-8")
gain = np.ones(N)
for start, length in re.findall(r'id="vo-[^"]+" src="[^"]+" data-start="([0-9.]+)" data-duration="([0-9.]+)"', html):
    a, b = int(float(start) * SR), int((float(start) + float(length)) * SR)
    gain[a:b] = 0.5
k = int(0.3 * SR)
gain = np.convolve(gain, np.ones(k) / k, mode="same")
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
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-af", "loudnorm=I=-20:TP=-2:LRA=11",
                "-ar", "44100", "-c:a", "libmp3lame", "-q:a", "2", str(OUT)], check=True)
wav.unlink()
print("saved", OUT)
