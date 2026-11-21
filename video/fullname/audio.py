import os, json, numpy as np, soundfile as sf, importlib.util
D = os.path.dirname(os.path.abspath(__file__)); SR = 24000
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR)
rng = np.random.default_rng(9)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
spec = importlib.util.spec_from_file_location('fn', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
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
# light background music while he chills
lt = np.zeros(N); b7 = 60 / 100; c5 = {}
for b in range(int(T / (4 * b7)) + 1):
    for q, m in enumerate([55, 62, 59, 62, 57, 64, 60, 64]):
        if m not in c5: c5[m] = pluck(note(m), 0.5, 0.992)
        put(lt, (b * 4 + q * 0.5) * b7, c5[m], 0.5)
lt /= np.abs(lt).max()
mus = lt * fades(0.0, S(0), 0.05) * 0.9 + ten * fades(S(7), R.STARE[0], 0.2) * 0.45 + ten * fades(S(17), R.REVEAL, 0.1) * 0.7 \
      + lt * fades(R.GRAB[0], R.FREEZE2[0], 0.2) * 0.6
# --- SFX
def P_(at_, sig, g): put(out, at_, sig, g)
def scratch(at_, g=0.5):
    tt = env_t(0.45); f = 300 + 1600 * np.abs(np.sin(2 * np.pi * 3.3 * tt))
    P_(at_, (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + np.convolve(rng.standard_normal(len(tt)), np.ones(4) / 4, 'same') * 0.6) * np.exp(-tt * 4), g)
# TV chatter (muffled) before the call
tt = np.arange(int(S(0) * SR)) / SR
P_(0, np.convolve(rng.standard_normal(len(tt)), np.ones(80) / 80, 'same') * 4 * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * tt)), 0.03)
# crunch crunch
for j in range(int(S(0) / 1.6) + 1):
    for k_ in range(3):
        t2 = env_t(0.05); P_(j * 1.6 + 0.3 + k_ * 0.09, rng.standard_normal(len(t2)) * np.exp(-t2 * 60), 0.12)
# dramatic cinematic boom on full name + record scratch as he freezes
t2 = env_t(1.6); P_(S(0) + 0.02, (np.sin(2 * np.pi * (38 + 50 * np.exp(-t2 * 6)) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 10) * 0.4) * np.exp(-t2 * 2), 0.75)
scratch(E(0) + 0.02, 0.45)
# suspense footsteps while approaching
for j in range(5):
    t2 = env_t(0.12); P_(R.WALK[0] + j * 0.32, np.sin(2 * np.pi * 70 * t2) * np.exp(-t2 * 30), 0.5)
t2 = env_t(R.WALK[1] - R.WALK[0]); P_(R.WALK[0], np.sin(2 * np.pi * 65 * t2) * 0.5, 0.15)
# fast ticking while he guesses
for j in range(int((R.STARE[0] - S(7)) / 0.25)):
    t2 = env_t(0.02); P_(S(7) + j * 0.25, np.sin(2 * np.pi * (2400 if j % 2 else 1800) * t2) * np.exp(-t2 * 150), 0.1)
for j in range(int((R.REVEAL - S(17)) / 0.2)):
    t2 = env_t(0.02); P_(S(17) + j * 0.2, np.sin(2 * np.pi * (2600 if j % 2 else 2000) * t2) * np.exp(-t2 * 150), 0.1)
# WHICH FRIEND?! dramatic impact
t2 = env_t(0.8); P_(S(12), (np.sin(2 * np.pi * (45 + 60 * np.exp(-t2 * 8)) * t2) * 0.8 + rng.standard_normal(len(t2)) * np.exp(-t2 * 12) * 0.3) * np.exp(-t2 * 4), 0.55)
# wrong buzzers
for (_, r) in R.GUESSES:
    t2 = env_t(0.25); P_(E(r) + 0.02, (np.sign(np.sin(2 * np.pi * 110 * t2)) + np.sign(np.sin(2 * np.pi * 116 * t2))) * np.exp(-t2 * 7), 0.07)
# sweat suspense drone
d = R.SWEAT[1] - R.SWEAT[0]; t2 = env_t(d); P_(R.SWEAT[0], (np.sin(2 * np.pi * 98 * t2) + np.sin(2 * np.pi * 104 * t2)) * np.minimum(1, (d - t2) * 6), 0.12)
# cartoon punch on "THAT WAS MONTHS AGO!"
t2 = env_t(0.3); P_(S(22) + 0.05, (np.sin(2 * np.pi * (200 * np.exp(-t2 * 15) + 70) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 40) * 0.8) * np.exp(-t2 * 12), 0.6)
# comedic record scratch on the trash reveal
scratch(E(24) + 0.02, 0.5)
t2 = env_t(0.3); P_(E(24) + 0.4, np.sin(2 * np.pi * np.cumsum(500 + 300 * np.sin(2 * np.pi * 9 * t2)) / SR) * np.exp(-t2 * 5), 0.1)
# bag rustle on grab
t2 = env_t(0.4); P_(R.GRAB[1] - 0.25, np.convolve(rng.standard_normal(len(t2)), np.ones(3) / 3, 'same') * np.exp(-t2 * 6), 0.15)
# cartoon running
for j in range(int((R.FREEZE2[0] - R.RUN0) / 0.09) + 1):
    t2 = env_t(0.05); P_(R.RUN0 + j * 0.09, np.sin(2 * np.pi * (300 if j % 2 else 380) * t2) * np.exp(-t2 * 60), 0.25)
t2 = env_t(0.4); P_(R.RUN0, np.sin(2 * np.pi * np.cumsum(300 + 1200 * t2) / SR) * np.exp(-t2 * 3), 0.1)
# pops
for at_ in (R.FREEZE[0] + 0.1, S(7), R.REVEAL + 0.6):
    t2 = env_t(0.08); P_(at_, np.sin(2 * np.pi * (500 + 1500 * t2 / 0.08) * t2) * np.exp(-t2 * 40), 0.25)
# freeze impact
t2 = env_t(0.5); P_(R.FREEZE2[0], (np.sin(2 * np.pi * (160 * np.exp(-t2 * 6) + 55) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 25) * 0.6) * np.exp(-t2 * 6), 0.5)
mus[int(R.FREEZE2[0] * SR):] = 0
duck = 1 - 0.45 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.05, 0, 1)
out += (mus * 0.12 * duck).astype(np.float32)
f = int(0.3 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
