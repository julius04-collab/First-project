import os, json, numpy as np, soundfile as sf, importlib.util
D = os.path.dirname(os.path.abspath(__file__)); SR = 24000
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR)
rng = np.random.default_rng(9)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
spec = importlib.util.spec_from_file_location('sp', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
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
# bouncy quirky groove for the literal-minded chaos
qk = np.zeros(N); beat3 = 60 / 112; cache2 = {}
bass = [43, 43, 50, 43, 45, 45, 52, 47]
for b in range(int(T / (8 * 0.5 * beat3)) + 1):
    for q, m in enumerate(bass):
        if m not in cache2: cache2[m] = pluck(note(m), 0.45, 0.99)
        put(qk, (b * 8 + q) * 0.5 * beat3, cache2[m], 0.7)
    for q, m in enumerate([67, None, 71, 74, None, 72, 71, None]):
        if m is None: continue
        tt = env_t(0.18); put(qk, (b * 8 + q) * 0.5 * beat3, np.sign(np.sin(2 * np.pi * note(m) * tt)) * np.exp(-tt * 18), 0.12)
qk /= np.abs(qk).max()
mus = ten * fades(S(0) - 0.4, E(6), 0.3) * 0.7 + qk * fades(S(9), R.FREEZE[0], 0.2) * 0.8 + qk * fades(S(28), S(31), 0.2) * 0.7 \
      + rom * fades(S(31), R.SILENCE[0], 0.3) * 0.8 + ten * fades(S(34), R.FREEZE2[0], 0.05) * 0.8
# --- SFX
# suspense sting on "I need space"
d = 0.95; tt = env_t(d)
put(out, E(6) + 0.02, (np.sin(2 * np.pi * 55 * tt) + 0.6 * np.sin(2 * np.pi * 58.3 * tt) + 0.4 * np.sin(2 * np.pi * 110 * tt)) * np.exp(-tt * 2.5), 0.3)
t2 = env_t(0.4); put(out, E(6) + 0.02, rng.standard_normal(len(t2)) * np.exp(-t2 * 9), 0.12)
# furniture drag: filtered noise with judder
a, b = R.T_GRAB + 0.3, R.T_PUSHEND
tt = np.arange(int((b - a) * SR)) / SR; n = rng.standard_normal(len(tt))
n = np.convolve(n, np.ones(40) / 40, 'same') * 6
jud = 0.6 + 0.4 * (np.sin(2 * np.pi * 9 * tt) > 0)
put(out, a, (n * jud + np.sin(2 * np.pi * 70 * tt) * 0.3) * np.minimum(1, tt * 6) * np.minimum(1, (tt[-1] - tt) * 6), 0.12)
# chair creak when he sits
t2 = env_t(0.35); put(out, R.T_SAT + 0.3, np.sin(2 * np.pi * (300 + 200 * t2) * t2) * np.exp(-t2 * 9) * (np.sin(2 * np.pi * 40 * t2) > 0), 0.1)
# phone typing clicks
for j in range(len(R.SEARCH)):
    t2 = env_t(0.025); put(out, S(21) - 0.05 + j * 1.6 / len(R.SEARCH) + rng.uniform(-0.01, 0.01), (rng.standard_normal(len(t2)) * 0.5 + np.sin(2 * np.pi * 3000 * t2)) * np.exp(-t2 * 200), 0.18)
for at_ in (S(21) + 1.8, S(30) + 1.3):
    t2 = env_t(0.06); put(out, at_, np.sin(2 * np.pi * 1800 * t2) * np.exp(-t2 * 60), 0.2)
# record scratch on EMOTIONAL SPACE
tt = env_t(0.45); f = 300 + 1600 * np.abs(np.sin(2 * np.pi * 3.3 * tt)); n = rng.standard_normal(len(tt))
put(out, R.FREEZE[0], (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + np.convolve(n, np.ones(4) / 4, 'same') * 0.6) * np.exp(-tt * 4), 0.5)
# lightbulb ding
t2 = env_t(0.8); put(out, S(27), (np.sin(2 * np.pi * 1568 * t2) + 0.5 * np.sin(2 * np.pi * 2093 * t2)) * np.exp(-t2 * 5), 0.12)
# tag pops
for at_ in (S(10), S(25), R.T_SAT + 1.1):
    t2 = env_t(0.08); put(out, at_, np.sin(2 * np.pi * (500 + 1500 * t2 / 0.08) * t2) * np.exp(-t2 * 40), 0.25)
# whoosh + cartoon impact
d = R.PILLOW[1] - R.PILLOW[0]; tt = env_t(d); n = rng.standard_normal(len(tt))
put(out, R.PILLOW[0], np.convolve(n, np.ones(8) / 8, 'same') * np.sin(np.pi * tt / d) ** 2, 0.5)
t2 = env_t(0.5); put(out, R.PILLOW[1], (np.sin(2 * np.pi * (180 * np.exp(-t2 * 6) + 60) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 30) * 0.5) * np.exp(-t2 * 7), 0.55)
t2 = env_t(0.5); put(out, R.PILLOW[1] + 0.05, np.sin(2 * np.pi * np.cumsum(900 + 600 * np.sin(2 * np.pi * 8 * t2)) / SR) * np.exp(-t2 * 6), 0.08)   # boing
# comedic outro: quick "wah wah wahhh"
for j, (m, d_) in enumerate([(62, 0.3), (61, 0.3), (60, 0.3), (59, 0.9)]):
    t2 = env_t(d_); vib = 1 + 0.02 * np.sin(2 * np.pi * 6 * t2) * (j == 3)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(note(m) * vib) / SR)) * 0.5 + np.sin(2 * np.pi * np.cumsum(note(m) * vib) / SR)
    put(out, R.FREEZE2[0] + 0.15 + j * 0.32, s * np.minimum(1, t2 * 30) * np.exp(-t2 * 2), 0.12)
mus[int(R.FREEZE2[0] * SR):] = 0
duck = 1 - 0.45 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.05, 0, 1)
out += (mus * 0.12 * duck).astype(np.float32)
f = int(0.3 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
