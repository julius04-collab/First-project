import os, json, numpy as np, soundfile as sf, importlib.util
D = os.path.dirname(os.path.abspath(__file__)); SR = 24000
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR)
rng = np.random.default_rng(9)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
spec = importlib.util.spec_from_file_location('sk', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
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
# light comedy groove (scene 1)
qk = np.zeros(N); b3 = 60 / 104; c2 = {}
for b in range(int(T / (4 * b3)) + 1):
    for q, m in enumerate([48, 55, 52, 55, 50, 57, 53, 57]):
        if m not in c2: c2[m] = pluck(note(m), 0.4, 0.99)
        put(qk, (b * 4 + q * 0.5) * b3, c2[m], 0.6)
    for q, m in enumerate([72, None, 76, 74, None, 72, 69, None]):
        if m: t2 = env_t(0.16); put(qk, (b * 4 + q * 0.5) * b3, np.sin(2 * np.pi * note(m) * t2) * np.exp(-t2 * 14), 0.25)
qk /= np.abs(qk).max()
# energetic football music: driving drums + stabs
fb = np.zeros(N); b4 = 60 / 140
for b in range(int(T / (4 * b4)) + 1):
    for q in range(8):
        st_ = (b * 4 + q * 0.5) * b4
        if q % 2 == 0:
            t2 = env_t(0.18); put(fb, st_, np.sin(2 * np.pi * (60 + 70 * np.exp(-t2 * 30)) * t2) * np.exp(-t2 * 14), 0.9)
        t2 = env_t(0.05); put(fb, st_ + 0.25 * b4, rng.standard_normal(len(t2)) * np.exp(-t2 * 70), 0.25)
        if q in (2, 6):
            t2 = env_t(0.1); put(fb, st_, rng.standard_normal(len(t2)) * np.exp(-t2 * 30), 0.5)
    for q, m in enumerate([57, 57, 60, 62]):
        t2 = env_t(0.22); put(fb, (b * 4 + q) * b4, sum(np.sign(np.sin(2 * np.pi * note(m + o) * t2)) for o in (0, 7)) * np.exp(-t2 * 10), 0.12)
fb /= np.abs(fb).max()
mus = qk * fades(0.0, R.TRANS[0], 0.2) * 0.8 + fb * fades(R.TRANS[0] + 0.3, S(13), 0.05) * 0.85 \
      + ten * fades(R.FREEZE[1], S(22), 0.3) * 0.6 + qk * fades(S(22), R.FREEZE2[0], 0.3) * 0.7
# --- SFX
def env_put(at_, sig, g): put(out, at_, sig, g)
# ringtone
for j in range(2):
    for k_ in range(8):
        t2 = env_t(0.05); env_put(0.25 + j * 0.55 + k_ * 0.05, np.sin(2 * np.pi * (1300 if k_ % 2 else 1650) * t2), 0.08)
# cartoon fake coughs
for j in range(3):
    t2 = env_t(0.17); n = rng.standard_normal(len(t2)); s_ = (np.convolve(n, np.ones(6) / 6, 'same') * 2 + np.sin(2 * np.pi * 180 * t2)) * np.exp(-t2 * 16)
    env_put(E(0) + 0.05 + j * 0.22, s_, 0.35)
t2 = env_t(0.15); env_put(S(3) - 0.15, (np.convolve(rng.standard_normal(len(t2)), np.ones(6) / 6, 'same') * 2 + np.sin(2 * np.pi * 180 * t2)) * np.exp(-t2 * 16), 0.3)
# call disconnect
for j in range(3):
    t2 = env_t(0.12); env_put(E(7) + 0.05 + j * 0.16, np.sin(2 * np.pi * 480 * t2), 0.07)
# boing on the jump
t2 = env_t(0.6); env_put(R.JUMP[0], np.sin(2 * np.pi * np.cumsum(250 + 500 * t2 + 120 * np.sin(2 * np.pi * 12 * t2)) / SR) * np.exp(-t2 * 4), 0.2)
# transition whoosh
t2 = env_t(0.5); env_put(R.TRANS[0], np.convolve(rng.standard_normal(len(t2)), np.ones(10) / 10, 'same') * np.sin(np.pi * t2 / 0.5) ** 2, 0.5)
# crowd bed during the match + roar on goal
a_, b_ = R.TRANS[0] + 0.3, S(13) + 0.3; tt = np.arange(int((b_ - a_) * SR)) / SR
crowd = np.convolve(rng.standard_normal(len(tt)), np.ones(60) / 60, 'same') * 6
gate_ = np.minimum(1, tt * 2) * np.minimum(1, (tt[-1] - tt) * 4)
roar = 1 + 3 * np.clip(1 - np.abs(tt - (R.GOAL_T - a_ + 0.8)) / 1.6, 0, 1)
env_put(a_, crowd * gate_ * roar, 0.05)
# ball kicks
for at_ in [R.TRANS[0] + 0.3 + 1.4 * j for j in range(int((R.GS - R.TRANS[0]) / 1.4))] + [R.GS, R.GS + 0.92]:
    t2 = env_t(0.08); env_put(at_, np.sin(2 * np.pi * 150 * t2) * np.exp(-t2 * 50) + rng.standard_normal(len(t2)) * np.exp(-t2 * 80) * 0.4, 0.4)
# goal: net swish + air horn
t2 = env_t(0.35); env_put(R.GOAL_T, np.convolve(rng.standard_normal(len(t2)), np.ones(3) / 3, 'same') * np.exp(-t2 * 8), 0.3)
t2 = env_t(0.9); env_put(R.GOAL_T + 0.1, sum(np.sign(np.sin(2 * np.pi * f_ * t2)) for f_ in (440, 554, 659)) * np.minimum(1, t2 * 30) * np.minimum(1, (0.9 - t2) * 10), 0.05)
# dramatic sting when she appears + record scratch
t2 = env_t(1.0); env_put(S(13) - 0.05, (np.sin(2 * np.pi * 55 * t2) + 0.6 * np.sin(2 * np.pi * 58.3 * t2) + 0.4 * np.sin(2 * np.pi * 110 * t2)) * np.exp(-t2 * 2.5), 0.3)
tt = env_t(0.45); f = 300 + 1600 * np.abs(np.sin(2 * np.pi * 3.3 * tt))
env_put(R.FREEZE[0], (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + np.convolve(rng.standard_normal(len(tt)), np.ones(4) / 4, 'same') * 0.6) * np.exp(-tt * 4), 0.5)
# tag pops
for at_ in (0.2, S(1), R.TRANS[0] + 0.3, S(22) + 1.2):
    t2 = env_t(0.08); env_put(at_, np.sin(2 * np.pi * (500 + 1500 * t2 / 0.08) * t2) * np.exp(-t2 * 40), 0.25)
# final comedic impact on the freeze frame
t2 = env_t(0.5); env_put(R.FREEZE2[0], (np.sin(2 * np.pi * (160 * np.exp(-t2 * 6) + 55) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 25) * 0.6) * np.exp(-t2 * 6), 0.55)
t2 = env_t(0.3); env_put(R.FREEZE2[0] + 0.05, np.sin(2 * np.pi * (1200 - 800 * t2 / 0.3) * t2) * np.exp(-t2 * 8), 0.12)
mus[int(R.FREEZE2[0] * SR):] = 0
duck = 1 - 0.45 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.05, 0, 1)
out += (mus * 0.12 * duck).astype(np.float32)
f = int(0.3 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
