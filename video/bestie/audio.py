import os, json, numpy as np, soundfile as sf, importlib.util
D = os.path.dirname(os.path.abspath(__file__)); SR = 24000
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR)
rng = np.random.default_rng(9)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
spec = importlib.util.spec_from_file_location('bf', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
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
mus = lt * fades(0.0, R.TURN[0], 0.1) * 0.6 + snk * fades(S(4), R.CARD[0], 0.3) * 0.7 + lt * fades(R.CARD[1], S(21), 0.3) * 0.6 \
      + ten * fades(S(21), R.LOOK[0], 0.3) * 0.55 + snk * fades(S(31), T, 0.3) * 0.6
# --- SFX
def P_(at_, sig, g): put(out, at_, sig, g)
def popsnd(at_, g=0.25):
    t2 = env_t(0.08); P_(at_, np.sin(2 * np.pi * (500 + 1500 * t2 / 0.08) * t2) * np.exp(-t2 * 40), g)
# slow head turn: suspense sting
t2 = env_t(1.0); P_(R.TURN[0], (np.sin(2 * np.pi * 98 * t2) + np.sin(2 * np.pi * 104 * t2) + 0.5 * np.sin(2 * np.pi * 196 * t2)) * np.exp(-t2 * 2.5), 0.15)
# his smile drops: record stop
tt = env_t(0.5); f = 400 * np.exp(-tt * 5) + 40; P_(R.DROP[0] + 0.05, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3), 0.2)
# phone lock click
t2 = env_t(0.05); P_(R.LOCK, rng.standard_normal(len(t2)) * np.exp(-t2 * 100) + np.sin(2 * np.pi * 800 * t2) * np.exp(-t2 * 60), 0.3)
# card whoosh + doorbell for Emily
t2 = env_t(0.5); P_(R.CARD[0], np.convolve(rng.standard_normal(len(t2)), np.ones(10) / 10, 'same') * np.sin(np.pi * t2 / 0.5) ** 2, 0.35)
for j, m in enumerate((76, 72)):
    t2 = env_t(1.0); P_(R.CARD[1] - 0.3 + j * 0.4, np.sin(2 * np.pi * note(m) * t2) * np.exp(-t2 * 3), 0.18)
# secrets exposed: dramatic stingers
for i in R.SECRETS:
    t2 = env_t(0.6); P_(S(i) + 0.3, (np.sin(2 * np.pi * (60 + 50 * np.exp(-t2 * 10)) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 25) * 0.4) * np.exp(-t2 * 5), 0.35)
    popsnd(S(i) + 0.3)
t2 = env_t(1.2); P_(S(24), (np.sin(2 * np.pi * (38 + 50 * np.exp(-t2 * 6)) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 10) * 0.3) * np.exp(-t2 * 2.5), 0.5)
# teddy "squeak"
t2 = env_t(0.25); P_(S(25) + 0.6, np.sin(2 * np.pi * np.cumsum(1200 + 600 * np.sin(np.pi * t2 / 0.25)) / SR) * np.exp(-t2 * 6), 0.1)
# the look exchange: sly two-note
for j, m in enumerate((64, 67)):
    t2 = env_t(0.3); P_(R.LOOK[0] + 0.1 + j * 0.25, np.sin(2 * np.pi * note(m) * t2) * np.exp(-t2 * 8), 0.12)
popsnd(S(31))
# both turn to him: dramatic boom
t2 = env_t(1.0); P_(R.TEAM[0] + 0.1, np.sin(2 * np.pi * (40 + 40 * np.exp(-t2 * 6)) * t2) * np.exp(-t2 * 3), 0.5)
# ending sting
for j, (m, d_) in enumerate([(62, 0.3), (61, 0.3), (60, 0.3), (59, 0.9)]):
    t2 = env_t(d_); s_ = np.sin(2 * np.pi * note(m) * t2) + 0.4 * np.sign(np.sin(2 * np.pi * note(m) * t2))
    P_(E(34) + 0.1 + j * 0.3, s_ * np.minimum(1, t2 * 30) * np.exp(-t2 * 2), 0.08)
mus *= 1 - fades(S(34), T, 0.2)
duck = 1 - 0.45 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.05, 0, 1)
out += (mus * 0.12 * duck).astype(np.float32)
f = int(0.3 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
