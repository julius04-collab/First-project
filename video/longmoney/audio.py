import os, json, numpy as np, soundfile as sf, importlib.util
D = os.path.dirname(os.path.abspath(__file__)); SR = 24000
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR)
rng = np.random.default_rng(9)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
spec = importlib.util.spec_from_file_location('lm', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
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
lt = np.zeros(N); b7 = 60 / 100; c5 = {}
for b in range(int(T / (4 * b7)) + 1):
    for q, m in enumerate([55, 62, 59, 62, 57, 64, 60, 64]):
        if m not in c5: c5[m] = pluck(note(m), 0.5, 0.992)
        put(lt, (b * 4 + q * 0.5) * b7, c5[m], 0.5)
lt /= np.abs(lt).max()
snk = np.zeros(N); b5 = 60 / 96; c3 = {}
for b in range(int(T / (4 * b5)) + 1):
    for q, m in enumerate([52, None, 55, None, 57, 56, 55, None]):
        if m is None: continue
        if m not in c3: c3[m] = pluck(note(m), 0.35, 0.985)
        put(snk, (b * 4 + q * 0.5) * b5, c3[m], 0.7)
snk /= np.abs(snk).max()
tt0 = np.arange(N) / SR
pad = (np.sin(2 * np.pi * 110 * tt0) + 0.6 * np.sin(2 * np.pi * 164.8 * tt0)) * 0.4
mus = pad * fades(0.0, R.REWIND[0], 0.3) * 0.6 + rom * fades(R.CARD0[0], R.CARD0[1], 0.3) * 0.6 \
      + lt * fades(R.CARD0[1], R.CARD1[0], 0.3) * 0.7 + snk * fades(R.CARD1[1], R.CARD2[0], 0.3) * 0.8 \
      + lt * fades(R.CARD2[1], S(25), 0.3) * 0.6 + ten * fades(S(27), E(36), 0.3) * 0.45 + ten * fades(S(37), E(50), 0.4) * 0.6 \
      + rom * fades(S(51) - 0.5, E(63) + 1.0, 1.0) * 0.75 + lt * fades(S(64), R.BUZZ, 0.3) * 0.7 + ten * fades(R.GRAB, R.BLACK, 0.05) * 0.9 \
      + rom * fades(R.ENDCARD, T, 0.5) * 0.7
# --- SFX
def P_(at_, sig, g): put(out, at_, sig, g)
def ding(at_, g=0.25):
    for j, m in enumerate((88, 93)):
        t2 = env_t(0.6); P_(at_ + j * 0.09, np.sin(2 * np.pi * note(m) * t2) * np.exp(-t2 * 7), g)
def whoosh(at_, d=0.4, g=0.4):
    t2 = env_t(d); P_(at_, np.convolve(rng.standard_normal(len(t2)), np.ones(10) / 10, 'same') * np.sin(np.pi * t2 / d) ** 2, g)
def scratch(at_, g=0.45):
    tt = env_t(0.45); f = 300 + 1600 * np.abs(np.sin(2 * np.pi * 3.3 * tt))
    P_(at_, (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + np.convolve(rng.standard_normal(len(tt)), np.ones(4) / 4, 'same') * 0.6) * np.exp(-tt * 4), g)
def boom(at_, g=0.6):
    t2 = env_t(1.4); P_(at_, (np.sin(2 * np.pi * (38 + 50 * np.exp(-t2 * 6)) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 10) * 0.3) * np.exp(-t2 * 2.2), g)
ding(0.6); ding(R.DING2, 0.3)
# rewind warble
tt = env_t(R.REWIND[1] - R.REWIND[0]); f = 900 - 600 * tt / tt[-1] + 120 * np.sin(2 * np.pi * 14 * tt)
P_(R.REWIND[0], (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.18 + rng.standard_normal(len(tt)) * 0.05) * np.sin(np.pi * tt / tt[-1]), 1.0)
for c in (R.CARD0, R.CARD1, R.CARD2): whoosh(c[0], 0.5, 0.35)
# S1 small comic stings
t2 = env_t(0.3); P_(E(12) + 0.1, np.sin(2 * np.pi * (300 + 900 * np.exp(-t2 * 12)) * t2) * np.exp(-t2 * 10), 0.25)
# S3: jacket rustle, envelope plop, paper, discovery sting, tray wobble clatter
t2 = env_t(0.3); P_(R.JACKET[0], np.convolve(rng.standard_normal(len(t2)), np.ones(5) / 5, 'same') * np.exp(-t2 * 8), 0.25)
t2 = env_t(0.18); P_(R.JACKET[0] + 0.95, np.sin(2 * np.pi * (220 * np.exp(-t2 * 25) + 80) * t2) * np.exp(-t2 * 22), 0.5)
t2 = env_t(0.3); P_(S(24) + 0.45, np.convolve(rng.standard_normal(len(t2)), np.ones(3) / 3, 'same') * np.exp(-t2 * 10), 0.25)
t2 = env_t(1.3); P_(S(25), (np.sin(2 * np.pi * 55 * t2) + 0.6 * np.sin(2 * np.pi * 58.3 * t2) + 0.4 * np.sin(2 * np.pi * 110 * t2)) * np.exp(-t2 * 2.2), 0.3)
for j in range(6):
    t2 = env_t(0.06); P_(S(28) + 0.5 + j * 0.12, np.sin(2 * np.pi * (2200 + 300 * (j % 2)) * t2) * np.exp(-t2 * 50) + rng.standard_normal(len(t2)) * np.exp(-t2 * 80) * 0.3, 0.12)
scratch(E(28) + 0.05)
boom(S(36) + 0.05, 0.4)
# S4 small impacts on key comebacks
for i in (43, 45):
    t2 = env_t(0.35); P_(E(i) - 0.2, (np.sin(2 * np.pi * (140 * np.exp(-t2 * 15) + 60) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 40) * 0.5) * np.exp(-t2 * 10), 0.35)
# S6: hug sparkle, buzz + record scratch, pillow, running
for j in range(6):
    t2 = env_t(0.5); P_(R.HUG + j * 0.07, np.sin(2 * np.pi * note(84 + [0, 4, 7, 12, 16, 19][j]) * t2) * np.exp(-t2 * 8), 0.05)
for j in range(3):
    t2 = env_t(0.18); P_(R.BUZZ + j * 0.25, np.sin(2 * np.pi * 180 * t2) * (np.sin(2 * np.pi * 40 * t2) > 0), 0.2)
scratch(R.BUZZ + 0.4, 0.5)
whoosh(R.GRAB, 0.3, 0.5)
for j in range(int((R.BLACK - R.RUN0) / 0.1)):
    t2 = env_t(0.05); P_(R.RUN0 + j * 0.1, np.sin(2 * np.pi * (300 if j % 2 else 380) * t2) * np.exp(-t2 * 60), 0.25)
t2 = env_t(0.5); P_(R.BLACK, (np.sin(2 * np.pi * (160 * np.exp(-t2 * 6) + 55) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 25) * 0.6) * np.exp(-t2 * 6), 0.5)
duck = 1 - 0.45 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.05, 0, 1)
out += (mus * 0.12 * duck).astype(np.float32)
f = int(1.0 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
