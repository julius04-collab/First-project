import os, json, numpy as np, soundfile as sf, importlib.util
D = os.path.dirname(os.path.abspath(__file__)); SR = 24000
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR)
rng = np.random.default_rng(9)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
spec = importlib.util.spec_from_file_location('pw', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
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
mus = lt * fades(0.0, S(8), 0.2) * 0.6 + ten * fades(S(9), R.TURN[0], 0.3) * 0.4 + ten * fades(S(15), R.LOCK, 0.3) * 0.55 \
      + lt * fades(S(23), R.REUNLOCK[1], 0.3) * 0.5
# --- SFX
def P_(at_, sig, g): put(out, at_, sig, g)
def popsnd(at_, g=0.25):
    t2 = env_t(0.08); P_(at_, np.sin(2 * np.pi * (500 + 1500 * t2 / 0.08) * t2) * np.exp(-t2 * 40), g)
# unlock taps 1-2-3-4
for j in range(4):
    t2 = env_t(0.05); P_(R.UNLOCK[0] + 0.1 + j * 0.15, np.sin(2 * np.pi * (900 + j * 120) * t2) * np.exp(-t2 * 50), 0.15)
t2 = env_t(0.2); P_(R.UNLOCK[0] + 0.75, np.sin(2 * np.pi * 1400 * t2) * np.exp(-t2 * 20), 0.12)
# phone tapping while he scrolls
tt_ = R.UNLOCK[1]
while tt_ < R.LOCK:
    t2 = env_t(0.02); P_(tt_, rng.standard_normal(len(t2)) * np.exp(-t2 * 200), 0.05); tt_ += 0.5 + 0.3 * rng.random()
# folder opening: notification pop; screenshots: comedic pops
t2 = env_t(0.3); P_(R.OPEN, (np.sin(2 * np.pi * 1320 * t2) + np.sin(2 * np.pi * 1760 * t2)) * np.exp(-t2 * 12), 0.1)
for i in (11, 12, 13): popsnd(S(i) - 0.1, 0.3)
# record scratch on EVIDENCE
tt = env_t(0.45); f = 300 + 1600 * np.abs(np.sin(2 * np.pi * 3.3 * tt))
P_(R.SCRATCH, (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + np.convolve(rng.standard_normal(len(tt)), np.ones(4) / 4, 'same') * 0.6) * np.exp(-tt * 4), 0.5)
# police siren sting
d = 1.2; t2 = env_t(d); f = 750 + 250 * np.sign(np.sin(2 * np.pi * 2.5 * t2))
P_(R.SIREN, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, t2 * 10) * np.minimum(1, (d - t2) * 5), 0.08)
# small suspense on "every week"
t2 = env_t(0.9); P_(E(20) + 0.05, (np.sin(2 * np.pi * 98 * t2) + np.sin(2 * np.pi * 104 * t2)) * np.exp(-t2 * 3), 0.15)
# lock click
t2 = env_t(0.05); P_(R.LOCK, rng.standard_normal(len(t2)) * np.exp(-t2 * 100) + np.sin(2 * np.pi * 800 * t2) * np.exp(-t2 * 60), 0.3)
# dramatic retreat sound on "I've seen enough"
t2 = env_t(0.7); P_(S(27), np.sin(2 * np.pi * np.cumsum(900 * np.exp(-t2 * 3) + 120) / SR) * np.exp(-t2 * 2.5), 0.12)
# horror sting on final folder
d = 2.2; t2 = env_t(d)
hor = (np.sin(2 * np.pi * 233 * t2) + np.sin(2 * np.pi * 247 * t2) + 0.5 * np.sin(2 * np.pi * 466 * t2 * (1 + 0.01 * np.sin(2 * np.pi * 7 * t2)))) * np.minimum(1, t2 * 8) * np.exp(-t2 * 1.0)
P_(S(30) + 0.8, hor, 0.12)
t2 = env_t(0.8); P_(R.FROZE[0], np.sin(2 * np.pi * (45 + 40 * np.exp(-t2 * 8)) * t2) * np.exp(-t2 * 3), 0.5)
# comedic impact at cut to black
t2 = env_t(0.5); P_(R.BLACK - 0.02, (np.sin(2 * np.pi * (160 * np.exp(-t2 * 6) + 55) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 25) * 0.6) * np.exp(-t2 * 6), 0.5)
for at_ in (S(7), S(29) + 0.3): popsnd(at_)
mus *= 1 - fades(R.FROZE[0], T, 0.1)
duck = 1 - 0.45 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.05, 0, 1)
out += (mus * 0.12 * duck).astype(np.float32)
f = int(0.3 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
