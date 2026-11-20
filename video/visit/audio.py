import os, json, numpy as np, soundfile as sf, importlib.util
D = os.path.dirname(os.path.abspath(__file__)); SR = 24000
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR)
rng = np.random.default_rng(9)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
spec = importlib.util.spec_from_file_location('vi', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
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
# upbeat tutorial music (thin, as if from the phone)
tut = np.zeros(N); bt = 60 / 120
for b in range(int(T / (4 * bt)) + 1):
    for q in range(8):
        m = [60, 64, 67, 72, 67, 64, 62, 65][q]
        t2 = env_t(0.2); put(tut, (b * 4 + q * 0.5) * bt, np.sign(np.sin(2 * np.pi * note(m) * t2)) * np.exp(-t2 * 12), 0.3)
    for q in range(4):
        t2 = env_t(0.12); put(tut, (b * 4 + q) * bt, np.sin(2 * np.pi * (80 + 60 * np.exp(-t2 * 30)) * t2) * np.exp(-t2 * 18), 0.8)
F = np.fft.rfft(tut); f = np.fft.rfftfreq(N, 1 / SR); F[(f < 300) | (f > 3500)] = 0; tut = np.fft.irfft(F, N)
tut /= np.abs(tut).max()
mus = tut * fades(0.2, R.RING[0], 0.1) * 0.8 + tut * fades(E(9) + 0.3, S(12), 0.05) * 0.6 \
      + ten * fades(S(13), R.DOOR[0], 0.1) * 0.9 + rom * fades(R.DANCE[0], R.DANCE[0] + 0.86 * (R.DANCE[1] - R.DANCE[0]), 0.1) * 1.1
mus += rom * fades(R.SOFT[0], S(38), 0.4) * 0.6 + ten * fades(S(21), R.PICK[0], 0.3) * 0.5
# --- SFX
def pop_(at_, g=0.25):
    t2 = env_t(0.08); put(out, at_, np.sin(2 * np.pi * (500 + 1500 * t2 / 0.08) * t2) * np.exp(-t2 * 40), g)
def whoosh(at_, d=0.3, g=0.45):
    t2 = env_t(d); n = rng.standard_normal(len(t2)); put(out, at_, np.convolve(n, np.ones(10) / 10, 'same') * np.sin(np.pi * t2 / d) ** 2, g)
# cartoon slip: rising slide whistle + squeak
d = 0.7; t2 = env_t(d); f = 600 + 900 * t2 / d
put(out, R.SLIP[0], np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t2 / d), 0.12)
t2 = env_t(0.12); put(out, R.SLIP[0] + 0.05, np.sin(2 * np.pi * 2400 * t2) * np.exp(-t2 * 30), 0.1)
# ringtone (two-tone trill)
for j in range(2):
    for k_ in range(8):
        t2 = env_t(0.05); put(out, R.RING[0] + j * 0.55 + k_ * 0.05, np.sin(2 * np.pi * (1300 if k_ % 2 else 1650) * t2), 0.08)
# hang-up beeps
for j in range(3):
    t2 = env_t(0.12); put(out, E(9) + 0.05 + j * 0.18, np.sin(2 * np.pi * 480 * t2) * np.minimum(1, (0.12 - t2) * 80), 0.08)
# doorbell ding-dong (twice)
for at_ in (R.BELL1, R.HIDE[2][0] + 0.2):
    for j, m in enumerate((76, 72)):
        t2 = env_t(1.2); put(out, at_ + j * 0.45, (np.sin(2 * np.pi * note(m) * t2) + 0.4 * np.sin(2 * np.pi * note(m) * 2.76 * t2) * np.exp(-t2 * 6)) * np.exp(-t2 * 2.5), 0.22)
# knock under "open the door"
for j in range(3):
    t2 = env_t(0.12); put(out, S(12) - 0.45 + j * 0.13, np.sin(2 * np.pi * 120 * t2) * np.exp(-t2 * 40) + rng.standard_normal(len(t2)) * np.exp(-t2 * 60) * 0.3, 0.4)
# tutorial pause click
t2 = env_t(0.03); put(out, S(12) - 0.1, rng.standard_normal(len(t2)) * np.exp(-t2 * 150), 0.2)
# hiding whooshes + chair scrape + door creak
for h in R.HIDE:
    whoosh(h[0], 0.28, 0.5)
a_, b_ = R.HIDE[1][0] + 0.1, R.HIDE[1][1] - 0.1; tt = np.arange(int((b_ - a_) * SR)) / SR
n = np.convolve(rng.standard_normal(len(tt)), np.ones(30) / 30, 'same') * 5 * (0.6 + 0.4 * (np.sin(2 * np.pi * 12 * tt) > 0))
put(out, a_, n * np.minimum(1, tt * 8) * np.minimum(1, (tt[-1] - tt) * 8), 0.12)
d = 0.6; t2 = env_t(d); put(out, R.DOOR[0], np.sin(2 * np.pi * np.cumsum(400 + 300 * np.sin(2 * np.pi * 3 * t2)) / SR) * (np.sin(2 * np.pi * 35 * t2) > 0) * np.sin(np.pi * t2 / d), 0.06)
# tag pops
for at_ in (0.3, R.SLIP[0], S(13), R.SCAN[0], S(33) + 0.8):
    pop_(at_)
# reveal sting
d = 1.4; t2 = env_t(d)
s_ = sum(np.sin(2 * np.pi * note(m) * t2) * w for m, w in ((57, 1), (60, 0.7), (64, 0.6), (69, 0.4)))
put(out, R.REVEAL[0], s_ * np.minimum(1, t2 * 20) * np.exp(-t2 * 2), 0.12)
t2 = env_t(0.5); put(out, R.REVEAL[0], rng.standard_normal(len(t2)) * np.exp(-t2 * 8), 0.12)
# freeze "caught" thud
t2 = env_t(0.25); put(out, R.FREEZE[0], np.sin(2 * np.pi * 90 * t2) * np.exp(-t2 * 20), 0.5)
# awful dance: squeaky steps, the spin swish, toe-step yelp thump, couch impact
D0, D1 = R.DANCE
for j in range(6):
    t2 = env_t(0.06); put(out, D0 + 0.2 + j * 0.38, np.sin(2 * np.pi * 2600 * t2) * np.exp(-t2 * 50), 0.06)
whoosh(D0 + 0.48 * (D1 - D0), 0.8, 0.4)
t2 = env_t(0.15); put(out, D0 + 0.68 * (D1 - D0), np.sin(2 * np.pi * 140 * t2) * np.exp(-t2 * 30), 0.4)
fall = D0 + 0.9 * (D1 - D0)
t2 = env_t(0.5); put(out, fall, (np.sin(2 * np.pi * (160 * np.exp(-t2 * 6) + 55) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 25) * 0.6) * np.exp(-t2 * 6), 0.6)
t2 = env_t(0.6); put(out, fall + 0.05, np.sin(2 * np.pi * np.cumsum(500 + 300 * np.sin(2 * np.pi * 9 * t2)) / SR) * np.exp(-t2 * 5), 0.08)   # spring boing
# smoke alarm beeping from the burnt food
for j in range(int((R.BLACK - R.STARE[0]) / 0.6)):
    at_ = R.STARE[0] + 0.1 + j * 0.6
    t2 = env_t(0.18); put(out, at_, np.sign(np.sin(2 * np.pi * 3100 * t2)), 0.035)
# comedic button at the end
for j, (m, d_) in enumerate([(67, 0.12), (60, 0.12), (61, 0.5)]):
    t2 = env_t(d_ + 0.2); put(out, E(46) + 0.1 + j * 0.16, np.sin(2 * np.pi * note(m) * t2) * np.exp(-t2 * 6) + 0.3 * np.sign(np.sin(2 * np.pi * note(m) * t2)) * np.exp(-t2 * 9), 0.12)
mus[int(R.BLACK * SR):] = 0
duck = 1 - 0.45 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.05, 0, 1)
out += (mus * 0.12 * duck).astype(np.float32)
f = int(0.3 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
