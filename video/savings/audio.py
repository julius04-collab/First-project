import os, json, numpy as np, soundfile as sf, importlib.util
D = os.path.dirname(os.path.abspath(__file__)); SR = 24000
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR)
rng = np.random.default_rng(9)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
spec = importlib.util.spec_from_file_location('sv', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
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
mus = lt * fades(0.0, S(6), 0.2) * 0.7 + ten * fades(S(7), E(11), 0.3) * 0.55 + ten * fades(S(17), S(22), 0.3) * 0.55 \
      + ten * fades(S(22), R.GRAB, 0.3) * 0.4 + ten * fades(R.GRAB, R.FREEZE2[0], 0.05) * 0.9
# --- SFX
def P_(at_, sig, g): put(out, at_, sig, g)
# notebook plop
t2 = env_t(0.18); P_(R.PLOP, np.sin(2 * np.pi * (220 * np.exp(-t2 * 25) + 80) * t2) * np.exp(-t2 * 22), 0.55)
t2 = env_t(0.25); P_(R.JACKET[0], np.convolve(rng.standard_normal(len(t2)), np.ones(5) / 5, 'same') * np.exp(-t2 * 8), 0.2)
# dramatic suspense sting on the savings reveal
t2 = env_t(1.4); P_(R.REVEAL, (np.sin(2 * np.pi * 55 * t2) + 0.6 * np.sin(2 * np.pi * 58.3 * t2) + 0.4 * np.sin(2 * np.pi * 110 * t2)) * np.exp(-t2 * 2.2), 0.3)
# record scratch on his face zoom
tt = env_t(0.45); f = 300 + 1600 * np.abs(np.sin(2 * np.pi * 3.3 * tt))
P_(R.ZOOM[0] + 0.02, (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + np.convolve(rng.standard_normal(len(tt)), np.ones(4) / 4, 'same') * 0.6) * np.exp(-tt * 4), 0.5)
# dramatic boom on "You!"
t2 = env_t(1.6); P_(S(11) + 0.08, (np.sin(2 * np.pi * (38 + 50 * np.exp(-t2 * 6)) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 10) * 0.35) * np.exp(-t2 * 2), 0.7)
# soft inspirational swell on each "financial discipline"
for i in (14, 16):
    d = E(i) - S(i) + 0.6; t2 = env_t(d)
    sw = sum(np.sin(2 * np.pi * note(m) * t2) for m in (60, 64, 67, 72)) * np.minimum(1, t2 * 3) * np.minimum(1, (d - t2) * 3)
    P_(S(i), sw, 0.06)
    for j, m in enumerate((72, 76, 79, 84)):
        t3 = env_t(0.6); P_(S(i) + j * 0.08, np.sin(2 * np.pi * note(m) * t3) * np.exp(-t3 * 6), 0.06)
# comedic impact on "financially stranded"
t2 = env_t(0.35); P_(E(21) - 0.25, (np.sin(2 * np.pi * (140 * np.exp(-t2 * 15) + 60) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 40) * 0.6) * np.exp(-t2 * 10), 0.5)
# banking app beeps
for j in range(3):
    t2 = env_t(0.06); P_(R.APP[0] + 0.3 + j * 0.25, np.sin(2 * np.pi * 1800 * t2) * np.exp(-t2 * 40), 0.12)
# pillow whoosh + running
t2 = env_t(0.3); P_(R.GRAB, np.convolve(rng.standard_normal(len(t2)), np.ones(10) / 10, 'same') * np.sin(np.pi * t2 / 0.3) ** 2, 0.5)
for j in range(int((R.FREEZE2[0] - R.RUN0) / 0.11)):
    t2 = env_t(0.05); P_(R.RUN0 + j * 0.11, np.sin(2 * np.pi * (300 if j % 2 else 380) * t2) * np.exp(-t2 * 60), 0.25)
for j in range(3):
    t2 = env_t(0.25); P_(R.RUN0 + 0.2 + j * 0.45, np.convolve(rng.standard_normal(len(t2)), np.ones(8) / 8, 'same') * np.sin(np.pi * t2 / 0.25) ** 2, 0.4)
# funny suspense sting at the end
for j, m in enumerate((62, 61, 62, 61, 67)):
    t2 = env_t(0.25 if j < 4 else 0.6); P_(R.FREEZE2[0] + j * 0.14, np.sign(np.sin(2 * np.pi * note(m) * t2)) * np.exp(-t2 * (8 if j < 4 else 3)), 0.06)
# tag pops
for at_ in (S(8) + 0.3, S(14), S(16), S(26) + 0.3):
    t2 = env_t(0.08); P_(at_, np.sin(2 * np.pi * (500 + 1500 * t2 / 0.08) * t2) * np.exp(-t2 * 40), 0.25)
mus *= 1 - fades(S(11), S(12), 0.05)
mus[int(R.FREEZE2[0] * SR):] = 0
duck = 1 - 0.45 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.05, 0, 1)
out += (mus * 0.12 * duck).astype(np.float32)
f = int(0.3 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
