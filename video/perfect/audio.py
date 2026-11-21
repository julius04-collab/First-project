import os, json, numpy as np, soundfile as sf, importlib.util
D = os.path.dirname(os.path.abspath(__file__)); SR = 24000
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR)
rng = np.random.default_rng(9)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
spec = importlib.util.spec_from_file_location('pf', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
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
mus = rom * fades(S(2) - 0.2, R.SCRATCH, 0.05) * 0.9 + ten * fades(R.STING + 0.8, S(16), 0.3) * 0.5 + ten * fades(S(17), R.THINK[0], 0.3) * 0.6 \
      + ten * fades(R.GRAB, R.FREEZE2[0], 0.05) * 0.9
# --- SFX
def P_(at_, sig, g): put(out, at_, sig, g)
# romantic sparkle while describing her
for j in range(10):
    t2 = env_t(0.5); P_(R.SPARK + j * 0.07, np.sin(2 * np.pi * note(84 + [0, 4, 7, 12, 16, 19, 16, 12, 7, 24][j]) * t2) * np.exp(-t2 * 8), 0.05)
# record scratch on "doesn't complain"
tt = env_t(0.45); f = 300 + 1600 * np.abs(np.sin(2 * np.pi * 3.3 * tt))
P_(R.SCRATCH, (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + np.convolve(rng.standard_normal(len(tt)), np.ones(4) / 4, 'same') * 0.6) * np.exp(-tt * 4), 0.5)
# suspense sting when her expression changes
t2 = env_t(1.0); P_(R.STING, (np.sin(2 * np.pi * 55 * t2) + 0.6 * np.sin(2 * np.pi * 58.3 * t2) + 0.4 * np.sin(2 * np.pi * 110 * t2)) * np.exp(-t2 * 2.5), 0.3)
# heartbeat during hesitation
for k_ in range(3):
    for dd in (0, 0.22):
        t2 = env_t(0.15); P_(R.HESIT[0] + 0.1 + k_ * 0.45 + dd, np.sin(2 * np.pi * 50 * t2) * np.exp(-t2 * 25), 0.55)
# thinking tick-tock
for j in range(3):
    t2 = env_t(0.03); P_(R.THINK[0] + 0.1 + j * 0.28, np.sin(2 * np.pi * (2400 if j % 2 else 1800) * t2) * np.exp(-t2 * 120), 0.15)
# dramatic impact on "Dangerous."
t2 = env_t(1.0); P_(S(27) + 0.05, (np.sin(2 * np.pi * (45 + 60 * np.exp(-t2 * 8)) * t2) * 0.8 + rng.standard_normal(len(t2)) * np.exp(-t2 * 12) * 0.3) * np.exp(-t2 * 3.5), 0.6)
# cartoon shock on "WHAT?!"
t2 = env_t(0.5); P_(S(28) - 0.02, np.sin(2 * np.pi * np.cumsum(600 + 1400 * t2 / 0.5) / SR) * np.exp(-t2 * 4), 0.15)
t2 = env_t(0.15); P_(S(28) - 0.02, rng.standard_normal(len(t2)) * np.exp(-t2 * 20), 0.2)
# pillow grab whoosh + running feet
t2 = env_t(0.3); P_(R.GRAB, np.convolve(rng.standard_normal(len(t2)), np.ones(10) / 10, 'same') * np.sin(np.pi * t2 / 0.3) ** 2, 0.5)
for j in range(int((R.FREEZE2[0] - R.RUN0) / 0.11)):
    t2 = env_t(0.05); P_(R.RUN0 + j * 0.11, np.sin(2 * np.pi * (300 if j % 2 else 380) * t2) * np.exp(-t2 * 60), 0.25)
for j in range(3):
    t2 = env_t(0.25); P_(R.RUN0 + 0.2 + j * 0.45, np.convolve(rng.standard_normal(len(t2)), np.ones(8) / 8, 'same') * np.sin(np.pi * t2 / 0.25) ** 2, 0.4)
# checklist ticks + tag pops
for (_, t0, _c) in R.LIST:
    t2 = env_t(0.06); P_(t0, np.sin(2 * np.pi * 1400 * t2) * np.exp(-t2 * 50), 0.12)
for at_ in (R.HESIT[0] + 0.2, S(23) + 0.6, S(26) + 0.3):
    t2 = env_t(0.08); P_(at_, np.sin(2 * np.pi * (500 + 1500 * t2 / 0.08) * t2) * np.exp(-t2 * 40), 0.25)
# freeze impact
t2 = env_t(0.5); P_(R.FREEZE2[0], (np.sin(2 * np.pi * (160 * np.exp(-t2 * 6) + 55) * t2) + rng.standard_normal(len(t2)) * np.exp(-t2 * 25) * 0.6) * np.exp(-t2 * 6), 0.5)
mus[int(R.FREEZE2[0] * SR):] = 0
duck = 1 - 0.45 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.05, 0, 1)
out += (mus * 0.12 * duck).astype(np.float32)
f = int(0.3 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
