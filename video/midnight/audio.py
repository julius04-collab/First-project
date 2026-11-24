import os, json, numpy as np, soundfile as sf, importlib.util
D = os.path.dirname(os.path.abspath(__file__)); SR = 24000
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR)
rng = np.random.default_rng(9)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
spec = importlib.util.spec_from_file_location('md', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
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
# soft night ambience pad, tension later
night = np.zeros(N); tt = np.arange(N) / SR
night += (np.sin(2 * np.pi * 110 * tt) + 0.6 * np.sin(2 * np.pi * 164.8 * tt) + 0.4 * np.sin(2 * np.pi * 220 * tt * (1 + 0.002 * np.sin(2 * np.pi * 0.3 * tt)))) * 0.3
mus = night * fades(0.0, S(4), 0.5) * 0.5 + ten * fades(S(6), R.SCRATCH, 0.3) * 0.45 + ten * fades(S(12) + 0.3, S(19), 0.3) * 0.65 \
      + ten * fades(S(22), T - 0.4, 0.05) * 0.85
# --- SFX
def P_(at_, sig, g): put(out, at_, sig, g)
def ding(at_, g=0.25):
    for j, m in enumerate((88, 93)):
        t2 = env_t(0.6); P_(at_ + j * 0.09, np.sin(2 * np.pi * note(m) * t2) * np.exp(-t2 * 7), g)
ding(R.DING1); ding(R.DING2, 0.3)
# suspense sting as she opens one eye
t2 = env_t(1.0); P_(R.EYE, (np.sin(2 * np.pi * 98 * t2) + np.sin(2 * np.pi * 104 * t2)) * np.exp(-t2 * 2.5), 0.15)
# comedic impact on "Nobody has a name?"
t2 = env_t(0.35); P_(E(2) - 0.05, (np.sin(2 * np.pi * (120 * np.exp(-t2 * 15) + 60) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 40) * 0.5) * np.exp(-t2 * 10), 0.4)
# record scratch on "Just a girl I used to know"
tt2 = env_t(0.45); f = 300 + 1600 * np.abs(np.sin(2 * np.pi * 3.3 * tt2))
P_(R.SCRATCH, (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + np.convolve(rng.standard_normal(len(tt2)), np.ones(4) / 4, 'same') * 0.6) * np.exp(-tt2 * 4), 0.5)
# dramatic boom as she sits up
t2 = env_t(1.4); P_(R.SITUP[1] - 0.25, (np.sin(2 * np.pi * (38 + 50 * np.exp(-t2 * 6)) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 10) * 0.3) * np.exp(-t2 * 2.2), 0.6)
# phone handover swish
t2 = env_t(0.25); P_(R.HAND[0], np.convolve(rng.standard_normal(len(t2)), np.ones(8) / 8, 'same') * np.sin(np.pi * t2 / 0.25) ** 2, 0.35)
# contact-name zoom whoosh + horror suspense sting on "that's my ex"
t2 = env_t(0.4); P_(R.ZNAME[0], np.convolve(rng.standard_normal(len(t2)), np.ones(6) / 6, 'same') * np.sin(np.pi * t2 / 0.4) ** 2, 0.4)
d = 2.0; t2 = env_t(d)
hor = (np.sin(2 * np.pi * 233 * t2) + np.sin(2 * np.pi * 247 * t2) + 0.5 * np.sin(2 * np.pi * 466 * t2 * (1 + 0.01 * np.sin(2 * np.pi * 7 * t2)))) * np.minimum(1, t2 * 8) * np.exp(-t2 * 1.2)
P_(E(21) + 0.02, hor, 0.12)
t2 = env_t(0.8); P_(E(21) + 0.02, np.sin(2 * np.pi * (45 + 40 * np.exp(-t2 * 8)) * t2) * np.exp(-t2 * 3), 0.5)
# pillow whoosh + bonk
d = R.PILLOW[1] - R.PILLOW[0]; t2 = env_t(d); P_(R.PILLOW[0], np.convolve(rng.standard_normal(len(t2)), np.ones(10) / 10, 'same') * np.sin(np.pi * t2 / d) ** 2, 0.5)
t2 = env_t(0.4); P_(R.PILLOW[1], (np.sin(2 * np.pi * (180 * np.exp(-t2 * 8) + 60) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 30) * 0.5) * np.exp(-t2 * 8), 0.5)
# cartoon running footsteps
for j in range(int((T - 0.4 - R.RUN0) / 0.1)):
    t2 = env_t(0.05); P_(R.RUN0 + j * 0.1, np.sin(2 * np.pi * (300 if j % 2 else 380) * t2) * np.exp(-t2 * 60), 0.25)
mus *= 1 - fades(R.ZNAME[1], S(22), 0.05)
duck = 1 - 0.45 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.05, 0, 1)
out += (mus * 0.12 * duck).astype(np.float32)
f = int(0.3 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
