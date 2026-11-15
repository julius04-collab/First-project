"""Synthesize original music.mp3 (playful pizzicato/ukulele) and all SFX into public/ (royalty-free, made from scratch)."""
import os, subprocess
import numpy as np, soundfile as sf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100
rng = np.random.default_rng(7)
def save(name, x):
    x = np.asarray(x, np.float32); x /= max(1e-9, np.abs(x).max()) / 0.9
    wav = os.path.join(ROOT, "public", name.replace(".mp3", ".wav"))
    os.makedirs(os.path.dirname(wav), exist_ok=True)
    sf.write(wav, x, SR)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "160k", wav.replace(".wav", ".mp3")], check=True)
    os.remove(wav)
def tt(d): return np.arange(int(d * SR)) / SR
def env(d, a=0.01, r=None):
    t = tt(d); e = np.minimum(1, t / a)
    if r: e *= np.exp(-t / r)
    return e
def noise(d, lp=1):
    n = rng.standard_normal(int(d * SR))
    return np.convolve(n, np.ones(lp) / lp, "same") if lp > 1 else n
def pluck(f, d, bright=0.5):
    N = int(d * SR); p = max(2, int(SR / f)); buf = rng.uniform(-1, 1, p); out = np.zeros(N)
    for i in range(N):
        out[i] = buf[i % p]; buf[i % p] = bright * buf[i % p] + (1 - bright) * 0.996 * buf[(i + 1) % p] if False else 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.996
    return out
def note(m): return 440 * 2 ** ((m - 69) / 12)
def mix_at(buf, i, sig):
    i = int(i); L = min(len(sig), len(buf) - i)
    if L > 0: buf[i:i + L] += sig[:L]
# ---------------- music: 112 bpm, C - Am - F - G, bouncy pizzicato bass + ukulele strums + glock melody
bpm = 112; beat = 60 / bpm; bars = 48; L = int(bars * 4 * beat * SR) + SR
m = np.zeros(L)
prog = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]
mel = [76, 79, 81, 79, 76, 74, 72, 74, 76, 76, 74, 72, 69, 72, 74, 72]
cache = {}
def pl(mn, d=0.6):
    if (mn, d) not in cache: cache[(mn, d)] = pluck(note(mn), d)
    return cache[(mn, d)]
for b in range(bars):
    ch = prog[b % 4]
    for q in range(4):
        st = (b * 4 + q) * beat * SR
        mix_at(m, st, pl(ch[0] - 24 + (7 if q % 2 else 0), 0.5) * 0.9)          # pizzicato bass
        if q in (1, 3):
            for j, nn in enumerate(ch + [ch[0] + 12]):                          # uke strum
                mix_at(m, st + j * 0.012 * SR, pl(nn, 0.35) * 0.35)
        if q in (0, 2):
            mix_at(m, st, noise(0.04, 1) * env(0.04, 0.001, 0.01) * 0.15)        # shaker
        if b % 2 == 1 or b >= 8:
            mn = mel[(b * 4 + q) % len(mel)]
            t = tt(0.5); mix_at(m, st + 0.5 * beat * SR * (q % 2), (np.sin(2 * np.pi * note(mn) * t) + 0.3 * np.sin(4 * np.pi * note(mn) * t)) * np.exp(-t * 7) * 0.25)
save("music.mp3", m)
# ---------------- sfx
S = "sfx/"
t = tt(1.4); f = 300 * np.exp(-t * 0.6) + 80 * np.sin(t * 3)
yawn = (np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * noise(1.4, 30)) * np.sin(np.pi * t / 1.4) ** 1.5
save(S + "yawn.mp3", yawn)
c = np.zeros(int(3.0 * SR))
for k in range(9):
    st = k * 0.33 + rng.uniform(0, 0.05)
    for j in range(3):
        tt2 = tt(0.03); mix_at(c, (st + j * 0.045) * SR, np.sin(2 * np.pi * 4600 * tt2) * np.hanning(len(tt2)))
save(S + "crickets.mp3", c)
ap = np.zeros(int(2.5 * SR))
for k in range(400):
    st = rng.uniform(0, 2.2); mix_at(ap, st * SR, noise(0.03, 3) * env(0.03, 0.001, 0.006))
ap *= np.minimum(1, tt(2.5) / 0.2) * np.clip((2.5 - tt(2.5)) / 0.8, 0, 1)
save(S + "applause.mp3", ap)
t = tt(1.0); sk = np.sin(2 * np.pi * np.cumsum(900 + 300 * np.sin(t * 40) - 400 * t) / SR) * 0.5 + noise(1.0, 2) * 0.5
save(S + "skid.mp3", sk * np.minimum(1, t / 0.05) * np.clip((1.0 - t) / 0.3, 0, 1))
t = tt(0.6); save(S + "thud.mp3", np.sin(2 * np.pi * (55 + 90 * np.exp(-t * 20)) * t) * np.exp(-t * 7) + noise(0.6, 8) * np.exp(-t * 12) * 0.6)
ft = np.zeros(int(2.0 * SR))
for k in range(5):
    tt2 = tt(0.12); mix_at(ft, k * 0.42 * SR, (noise(0.12, 6) * 0.6 + np.sin(2 * np.pi * 140 * tt2)) * np.exp(-tt2 * 40))
save(S + "foot-tap.mp3", ft)
t = tt(0.3); save(S + "facepalm-slap.mp3", noise(0.3, 2) * np.exp(-t * 30) + np.sin(2 * np.pi * 220 * t) * np.exp(-t * 25) * 0.5)
t = tt(1.4); save(S + "slide-whistle.mp3", np.sin(2 * np.pi * np.cumsum(500 + 900 * (t / 1.4) + 60 * np.sin(t * 30)) / SR) * np.minimum(1, t / 0.05) * np.clip((1.4 - t) / 0.15, 0, 1))
t = tt(1.4)
cr = noise(1.4, 2) * np.exp(-t * 4) + (np.sin(2 * np.pi * 180 * t) + 0.6 * np.sin(2 * np.pi * 523 * t) + 0.4 * np.sin(2 * np.pi * 1210 * t)) * np.exp(-t * 3.5) * 0.6 + np.sin(2 * np.pi * (50 + 80 * np.exp(-t * 15)) * t) * np.exp(-t * 6)
save(S + "crash.mp3", cr)
t = tt(0.7); save(S + "wrong-buzzer.mp3", np.sign(np.sin(2 * np.pi * 110 * t)) * 0.6 * np.minimum(1, t / 0.02) * np.clip((0.7 - t) / 0.1, 0, 1))
t = tt(1.2); save(S + "correct-ding.mp3", (np.sin(2 * np.pi * 1318.5 * t) + 0.5 * np.sin(2 * np.pi * 1975.5 * t)) * np.exp(-t * 4))
fl = np.zeros(int(1.6 * SR))
for k in range(7):
    st = rng.uniform(0, 1.4); d = rng.uniform(0.03, 0.09); tt2 = tt(d)
    mix_at(fl, st * SR, (noise(d, 1) * 0.5 + np.sign(np.sin(2 * np.pi * 120 * tt2)) * 0.5) * np.hanning(len(tt2)))
save(S + "flicker.mp3", fl)
t = tt(12.0); dr = (np.sin(2 * np.pi * 55 * t) + 0.5 * np.sin(2 * np.pi * 55.7 * t) + 0.3 * np.sin(2 * np.pi * 82.4 * t)) * (0.8 + 0.2 * np.sin(t * 0.7))
save(S + "drone.mp3", dr * np.minimum(1, t / 1.5) * np.clip((12 - t) / 1.0, 0, 1))
t = tt(2.2); save(S + "boom.mp3", np.sin(2 * np.pi * (40 + 60 * np.exp(-t * 6)) * t) * np.exp(-t * 2) + noise(2.2, 40) * np.exp(-t * 3) * 0.5)
t = tt(0.55); fr = 300 + 900 * np.abs(np.sin(t * 2 * np.pi * 3.0))
save(S + "record-scratch.mp3", (np.sign(np.sin(2 * np.pi * np.cumsum(fr) / SR)) * 0.5 + noise(0.55, 4) * 0.5) * np.exp(-t * 2.5))
t = tt(1.6); f0 = 330 * (1 + 0.15 * np.sin(np.pi * t / 1.6)) * (1 - 0.25 * t / 1.6)
aw = sum(np.sin(2 * np.pi * np.cumsum(f0 * (1 + d)) / SR) for d in (-0.02, 0, 0.015, 0.03, 0.5, 0.52))
save(S + "aww.mp3", aw * np.sin(np.pi * t / 1.6) * (1 + 0.3 * np.sin(t * 30)))
tp = np.zeros(int(2.4 * SR))
for k in range(6):
    tt2 = tt(0.25); mn = [72, 74, 72, 74, 76, 74][k]
    mix_at(tp, k * 0.4 * SR, pluck(note(mn), 0.25) * 0.8 + noise(0.25, 10) * np.exp(-tt2 * 40) * 0.3)
save(S + "sneaky-tiptoe.mp3", tp)
t = tt(0.5); ah = np.sin(2 * np.pi * np.cumsum(130 + 40 * np.exp(-t * 6)) / SR) * (0.6 + 0.4 * noise(0.5, 60)) * np.sin(np.pi * t / 0.5)
save(S + "ahem.mp3", np.concatenate([ah, np.zeros(int(0.15 * SR)), ah * 0.9]))
print("ok")
