import os, json, numpy as np, soundfile as sf, importlib.util
D = os.path.dirname(os.path.abspath(__file__)); SR = 24000
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR)
rng = np.random.default_rng(9)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
spec = importlib.util.spec_from_file_location('fb', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
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
mus = ten * fades(S(7), S(20), 0.3) * 0.45 + lt * fades(S(23), S(33), 0.3) * 0.6 + lt * fades(S(36), R.GRAB, 0.3) * 0.5 \
      + ten * fades(R.GRAB, S(40), 0.05) * 0.9
# --- SFX
def P_(at_, sig, g): put(out, at_, sig, g)
def scratch(at_, g=0.5):
    tt = env_t(0.45); f = 300 + 1600 * np.abs(np.sin(2 * np.pi * 3.3 * tt))
    P_(at_, (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + np.convolve(rng.standard_normal(len(tt)), np.ones(4) / 4, 'same') * 0.6) * np.exp(-tt * 4), g)
def whistle(at_, d=0.5, g=0.12, trill=True):
    t2 = env_t(d); f = 2800 * (1 + (0.04 * np.sign(np.sin(2 * np.pi * 30 * t2)) if trill else 0))
    P_(at_, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, t2 * 40) * np.minimum(1, (d - t2) * 20), g)
# football crowd ambience through the opening (TV), returns at the end
def crowd(a, b, g):
    tt = np.arange(int((b - a) * SR)) / SR
    c = np.convolve(rng.standard_normal(len(tt)), np.ones(60) / 60, 'same') * 6 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.4 * tt))
    P_(a, c * np.minimum(1, tt * 2) * np.minimum(1, (tt[-1] - tt) * 2), g)
crowd(0.0, S(7) + 0.5, 0.035); crowd(S(39), T - 0.3, 0.04)
for j in range(int(S(0) / 1.7) + 1):
    for k_ in range(3):
        t2 = env_t(0.05); P_(j * 1.7 + 0.3 + k_ * 0.09, rng.standard_normal(len(t2)) * np.exp(-t2 * 60), 0.1)
scratch(R.SCRATCH1)
whistle(R.WHISTLE1, 0.6, 0.12)
# comedic ticking during negotiations
for j in range(int((S(20) - S(9)) / 0.25)):
    t2 = env_t(0.02); P_(S(9) + j * 0.25, np.sin(2 * np.pi * (2400 if j % 2 else 1800) * t2) * np.exp(-t2 * 150), 0.08)
# small victory sound for "watch together"
for j, m in enumerate((72, 76, 79, 84)):
    t2 = env_t(0.35 if j < 3 else 0.7); P_(R.WIN + j * 0.1, (np.sign(np.sin(2 * np.pi * note(m) * t2)) * 0.4 + np.sin(2 * np.pi * note(m) * t2)) * np.exp(-t2 * (6 if j < 3 else 3)), 0.07)
# dramatic boom on "I choose you..." then record scratch "...and football"
t2 = env_t(1.2); P_(R.BOOM - 0.3, (np.sin(2 * np.pi * (38 + 50 * np.exp(-t2 * 6)) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 10) * 0.3) * np.exp(-t2 * 2.5), 0.55)
scratch(R.SCRATCH2)
# pillow grab whoosh, referee whistles on RED CARD
t2 = env_t(0.3); P_(R.GRAB, np.convolve(rng.standard_normal(len(t2)), np.ones(10) / 10, 'same') * np.sin(np.pi * t2 / 0.3) ** 2, 0.5)
for j in range(3): whistle(S(39) + j * 0.7, 0.35, 0.14)
for j in range(int((R.STOP - R.RUN0) / 0.1)):
    t2 = env_t(0.05); P_(R.RUN0 + j * 0.1, np.sin(2 * np.pi * (300 if j % 2 else 380) * t2) * np.exp(-t2 * 60), 0.25)
# goal roar under the commentator
a_ = S(40) - 0.1; tt = env_t(2.2)
P_(a_, np.convolve(rng.standard_normal(len(tt)), np.ones(40) / 40, 'same') * 8 * np.minimum(1, tt * 5) * np.exp(-tt * 0.8), 0.06)
t2 = env_t(0.9); P_(a_ + 0.1, sum(np.sign(np.sin(2 * np.pi * f_ * t2)) for f_ in (440, 554, 659)) * np.minimum(1, t2 * 30) * np.minimum(1, (0.9 - t2) * 10), 0.03)
# pillow throw whoosh + cartoon impact
d = R.THROW[1] - R.THROW[0]; t2 = env_t(d); P_(R.THROW[0], np.convolve(rng.standard_normal(len(t2)), np.ones(10) / 10, 'same') * np.sin(np.pi * t2 / d) ** 2, 0.5)
t2 = env_t(0.5); P_(R.THROW[1], (np.sin(2 * np.pi * (180 * np.exp(-t2 * 8) + 60) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 30) * 0.5) * np.exp(-t2 * 7), 0.6)
t2 = env_t(0.5); P_(R.THROW[1] + 0.05, np.sin(2 * np.pi * np.cumsum(900 + 600 * np.sin(2 * np.pi * 8 * t2)) / SR) * np.exp(-t2 * 6), 0.08)
for at_ in (0.3, S(9), R.WIN):
    t2 = env_t(0.08); P_(at_, np.sin(2 * np.pi * (500 + 1500 * t2 / 0.08) * t2) * np.exp(-t2 * 40), 0.2)
mus *= 1 - fades(R.BOOM - 0.3, S(35), 0.05)
duck = 1 - 0.45 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.05, 0, 1)
out += (mus * 0.12 * duck).astype(np.float32)
f = int(0.3 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
