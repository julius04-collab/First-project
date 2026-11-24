import os, json, numpy as np, soundfile as sf, importlib.util
D = os.path.dirname(os.path.abspath(__file__)); SR = 24000
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR)
rng = np.random.default_rng(9)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
spec = importlib.util.spec_from_file_location('sr', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
S, E = R.S, R.E
def note(m): return 440 * 2 ** ((m - 69) / 12)
def pluck(f, d, damp=0.995):
    n = int(d * SR); p = max(2, int(SR / f)); buf = rng.uniform(-1, 1, p); o = np.zeros(n)
    for i in range(n):
        o[i] = buf[i % p]; buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * damp
    return o
def env_t(d): return np.arange(int(d * SR)) / SR
def put(buf, at, sig, g=1.0):
    i = int(at * SR); L = min(len(sig), len(buf) - i)
    if L > 0: buf[i:i + L] += (sig[:L] * g).astype(buf.dtype)
def fades(a, b, f=0.25):
    g = np.zeros(N); i, j = int(a * SR), int(b * SR); g[i:j] = 1; k = int(f * SR)
    g[i:i + k] *= np.linspace(0, 1, len(g[i:i + k])); g[max(i, j - k):j] *= np.linspace(1, 0, len(g[max(i, j - k):j])); return g
# 1) soft romantic: slow arpeggiated Rhodes-ish sines (Fmaj7 - Em7 - Dm7 - Cmaj7)
rom = np.zeros(N); beat = 60 / 76
prog = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]
for b in range(int(T / (4 * beat)) + 1):
    ch = prog[b % 4]
    for q in range(8):
        m = ch[[0, 1, 2, 3, 2, 1, 2, 3][q]] + 12
        tt = env_t(1.2); s = (np.sin(2 * np.pi * note(m) * tt) + 0.3 * np.sin(4 * np.pi * note(m) * tt)) * np.exp(-tt * 3)
        put(rom, (b * 4 + q * 0.5) * beat, s, 0.3)
    tt = env_t(4 * beat); put(rom, b * 4 * beat, np.sin(2 * np.pi * note(ch[0] - 12) * tt) * np.exp(-tt * 0.8), 0.35)
rom /= np.abs(rom).max()
# 2) tension comedy: staccato pizzicato in minor, faster
ten = np.zeros(N); beat2 = 60 / 124; cache = {}
pat = [45, 52, 45, 51, 45, 50, 45, 49]
for b in range(int(T / (8 * 0.5 * beat2)) + 1):
    for q, m in enumerate(pat):
        if m not in cache: cache[m] = pluck(note(m), 0.3, 0.98)
        put(ten, (b * 8 + q) * 0.5 * beat2, cache[m], 0.6 if q % 2 == 0 else 0.4)
    for q in range(4):
        tt = env_t(0.06); n = rng.standard_normal(len(tt)); put(ten, (b * 4 + q) * beat2 + beat2 * 0.5, n * np.exp(-tt * 60), 0.12)
ten /= np.abs(ten).max()
# sneaky snooping music
snk = np.zeros(N); b5 = 60 / 96; c3 = {}
for b in range(int(T / (4 * b5)) + 1):
    for q, m in enumerate([52, None, 55, None, 57, 56, 55, None]):
        if m is None: continue
        if m not in c3: c3[m] = pluck(note(m), 0.35, 0.985)
        put(snk, (b * 4 + q * 0.5) * b5, c3[m], 0.7)
snk /= np.abs(snk).max()
mus = rom * fades(0.0, E(0) + 0.6, 0.3) * 0.6 + snk * fades(S(1), R.BACK[0], 0.3) * 0.8 + ten * fades(S(9), E(13), 0.3) * 0.6
# --- SFX
def P_(at_, sig, g): put(out, at_, sig, g)
# phone unlock + typing taps + new search 'pop' each entry
t2 = env_t(0.15); P_(R.GRABP + 0.3, np.sin(2 * np.pi * 1600 * t2) * np.exp(-t2 * 25), 0.12)
for (i, _, _) in R.SEARCHES:
    for j in range(5):
        t2 = env_t(0.02); P_(S(i) - 0.35 + j * 0.06, rng.standard_normal(len(t2)) * np.exp(-t2 * 200), 0.12)
    t2 = env_t(0.1); P_(S(i), np.sin(2 * np.pi * (900 if i < 9 else 600) * t2) * np.exp(-t2 * 30), 0.15)
# "Aww" sparkle
for j in range(5):
    t2 = env_t(0.4); P_(E(2) - 0.6 + j * 0.06, np.sin(2 * np.pi * note(84 + [0, 4, 7, 12, 16][j]) * t2) * np.exp(-t2 * 9), 0.05)
# he walks back in and freezes: record scratch
tt = env_t(0.45); f = 300 + 1600 * np.abs(np.sin(2 * np.pi * 3.3 * tt))
P_(S(7) - 0.1, (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + np.convolve(rng.standard_normal(len(tt)), np.ones(4) / 4, 'same') * 0.6) * np.exp(-tt * 4), 0.45)
# "Sit down." low boom
t2 = env_t(1.0); P_(S(8), np.sin(2 * np.pi * (40 + 40 * np.exp(-t2 * 6)) * t2) * np.exp(-t2 * 2.5), 0.5)
# disappear: dramatic sting
t2 = env_t(1.2); P_(E(13) + 0.05, (np.sin(2 * np.pi * 55 * t2) + 0.6 * np.sin(2 * np.pi * 58.3 * t2) + 0.4 * np.sin(2 * np.pi * 110 * t2)) * np.exp(-t2 * 2.5), 0.3)
# WHAT IS THIS impact
t2 = env_t(0.6); P_(S(14), (np.sin(2 * np.pi * (45 + 60 * np.exp(-t2 * 8)) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 12) * 0.3) * np.exp(-t2 * 4), 0.45)
# dead silence + crickets in the straight-face pause
a_, b_ = R.PAUSE[0] + 0.1, S(17) - 0.05; tt = np.arange(int((b_ - a_) * SR)) / SR
P_(a_, np.sin(2 * np.pi * 4700 * tt) * (np.sin(2 * np.pi * 30 * tt) > 0.3) * ((tt % 0.55) < 0.18), 0.03)
# her explosion
t2 = env_t(0.5); P_(S(17) - 0.02, np.sin(2 * np.pi * np.cumsum(600 + 1400 * t2 / 0.5) / SR) * np.exp(-t2 * 4), 0.12)
# deadpan look-to-camera button, then run
t2 = env_t(0.25); P_(E(18) + 0.05, np.sin(2 * np.pi * (300 + 900 * np.exp(-t2 * 12)) * t2) * np.exp(-t2 * 10), 0.3)
for j in range(int((R.FREEZE2[0] - R.RUN0) / 0.09) + 2):
    t2 = env_t(0.05); P_(R.RUN0 + j * 0.09, np.sin(2 * np.pi * (300 if j % 2 else 380) * t2) * np.exp(-t2 * 60), 0.25)
t2 = env_t(0.5); P_(R.FREEZE2[0], (np.sin(2 * np.pi * (160 * np.exp(-t2 * 6) + 55) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 25) * 0.6) * np.exp(-t2 * 6), 0.5)
for at_ in (S(1) + 0.3, R.PAUSE[0] + 0.15):
    t2 = env_t(0.08); P_(at_, np.sin(2 * np.pi * (500 + 1500 * t2 / 0.08) * t2) * np.exp(-t2 * 40), 0.25)
mus[int(R.FREEZE2[0] * SR):] = 0
mus *= 1 - fades(R.PAUSE[0], S(17), 0.05)
duck = 1 - 0.45 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.05, 0, 1)
out += (mus * 0.12 * duck).astype(np.float32)
f = int(0.3 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
