import os, json, numpy as np, soundfile as sf, importlib.util
D = os.path.dirname(os.path.abspath(__file__)); SR = 24000
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR)
rng = np.random.default_rng(9)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
spec = importlib.util.spec_from_file_location('pr', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
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
mus = rom * fades(S(2), R.FREEZE[0], 0.05) * 0.9 + ten * (fades(S(13) + 0.3, R.LOOK4[0], 0.3) + fades(S(31), R.NOD[0], 0.2) + fades(S(36) + 0.5, R.EXIT[1], 0.2)) * 0.8
# hook: low tense pad
tt = env_t(R.T_REW[0]); put(mus, 0, (np.sin(2 * np.pi * 55 * tt) + 0.5 * np.sin(2 * np.pi * 82.4 * tt)) * np.minimum(1, tt * 4) * 0.4)
# outro: lonely little plucks for his last line
for j, m in enumerate([64, 62, 60, 59]):
    put(mus, S(40) + j * 0.9, pluck(note(m), 1.0), 0.4)
# --- SFX
tt = env_t(R.T_REW[1] - R.T_REW[0]); f = 900 - 600 * tt / tt[-1] + 120 * np.sin(2 * np.pi * 14 * tt)
put(out, R.T_REW[0], (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.18 + rng.standard_normal(len(tt)) * 0.05) * np.sin(np.pi * tt / tt[-1]))
# record scratch
tt = env_t(0.45); f = 300 + 1600 * np.abs(np.sin(2 * np.pi * 3.3 * tt)); n = rng.standard_normal(len(tt))
sc = (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + np.convolve(n, np.ones(4) / 4, 'same') * 0.6) * np.exp(-tt * 4)
put(out, R.FREEZE[0], sc, 0.5)
# suspense sting during slow head turn: rising drone + heartbeat
d = R.TURN[1] - R.TURN[0] + 0.3; tt = env_t(d); f = 70 + 40 * tt / d
put(out, R.TURN[0], (np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)) * np.minimum(1, tt / d * 1.5) * 0.18)
for k in range(2):
    for dd in (0, 0.22):
        t2 = env_t(0.15); put(out, R.TURN[0] + 0.2 + k * 0.6 + dd, np.sin(2 * np.pi * 50 * t2) * np.exp(-t2 * 25), 0.5)
# whoosh/pops for tags and danger meter
for at in (0.3, S(1) + 0.1, S(21), S(26) + 0.3, R.NOD[0] + 0.1, E(40) + 0.05):
    t2 = env_t(0.08); put(out, at, np.sin(2 * np.pi * (500 + 1500 * t2 / 0.08) * t2) * np.exp(-t2 * 40), 0.25)
# spotlight clunk
t2 = env_t(0.3); put(out, S(21) - 0.05, (np.sin(2 * np.pi * 90 * t2) + rng.standard_normal(len(t2)) * 0.4) * np.exp(-t2 * 18), 0.5)
# dramatic shock "dun dun DUNNN" on YOUR EX
for j, (m, d_) in enumerate([(45, 0.22), (45, 0.22), (44, 1.1)]):
    t2 = env_t(d_ + 0.4); s = sum(np.sin(2 * np.pi * note(m + o) * t2) * w for o, w in ((0, 1), (12, 0.5), (7, 0.4), (-12, 0.6)))
    put(out, S(32) + 0.05 + j * 0.28, s * np.exp(-t2 * (2.5 if j == 2 else 6)), 0.13)
# wrong-answer stamp thud
t2 = env_t(0.2); put(out, R.FREEZE[0] + 0.05, np.sin(2 * np.pi * 120 * t2) * np.exp(-t2 * 25), 0.4)
# door slam as she leaves
t2 = env_t(0.4); put(out, R.EXIT[1] - 0.1, np.sin(2 * np.pi * (70 + 60 * np.exp(-t2 * 20)) * t2) * np.exp(-t2 * 9) * 0.7 + rng.standard_normal(len(t2)) * np.exp(-t2 * 25) * 0.25)
# comedic pop at final punchline
t2 = env_t(0.25); put(out, E(40) + 0.05, np.sin(2 * np.pi * (300 + 900 * np.exp(-t2 * 12)) * t2) * np.exp(-t2 * 10), 0.35)
mus[int(R.BLACK * SR):] = 0
duck = 1 - 0.45 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.05, 0, 1)
out += (mus * 0.12 * duck).astype(np.float32)
f = int(0.4 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
