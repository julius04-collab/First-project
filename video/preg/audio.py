import os, json, numpy as np, soundfile as sf, importlib.util
D = os.path.dirname(os.path.abspath(__file__)); SR = 24000
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR)
rng = np.random.default_rng(9)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
spec = importlib.util.spec_from_file_location('pg', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
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
# gentle original ukulele-ish strum loop
uk = np.zeros(N); b6 = 60 / 92; c4 = {}
chords = [[60, 64, 67, 72], [57, 60, 64, 69], [53, 57, 60, 65], [55, 59, 62, 67]]
for b in range(int(T / (4 * b6)) + 1):
    ch = chords[b % 4]
    for q, pat in enumerate([1, 0, 1, 1, 0, 1, 1, 0]):
        if not pat: continue
        for j, m in enumerate(ch):
            if m not in c4: c4[m] = pluck(note(m), 0.7, 0.993)
            put(uk, (b * 4 + q * 0.5) * b6 + j * 0.012, c4[m], 0.25)
uk /= np.abs(uk).max()
mus = uk * fades(0.0, E(4) + 0.1, 0.1) * 0.8 + uk * fades(R.END, T, 0.3) * 0.5
# --- SFX
def P_(at_, sig, g): put(out, at_, sig, g)
# record-stop when he hears "father"
tt = env_t(0.5); f = 400 * np.exp(-tt * 5) + 40
P_(E(4) + 0.05, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3), 0.25)
# brain cell pops out + tiny footsteps + whoosh away
t2 = env_t(0.12); P_(R.BRAIN[0], np.sin(2 * np.pi * (400 + 1600 * t2 / 0.12) * t2) * np.exp(-t2 * 25), 0.3)
for j in range(10):
    t2 = env_t(0.04); P_(R.BRAIN[0] + 0.35 + j * 0.12, np.sin(2 * np.pi * (1800 if j % 2 else 2200) * t2) * np.exp(-t2 * 80), 0.08)
t2 = env_t(0.6); P_(R.BRAIN[1] - 0.6, np.convolve(rng.standard_normal(len(t2)), np.ones(8) / 8, 'same') * np.sin(np.pi * t2 / 0.6) ** 2, 0.25)
# crickets through the deadpan silence
a_, b_ = E(4) + 0.2, R.END; tt = np.arange(int((b_ - a_) * SR)) / SR
P_(a_, np.sin(2 * np.pi * 4700 * tt) * (np.sin(2 * np.pi * 30 * tt) > 0.3) * ((tt % 0.6) < 0.18), 0.03)
# loading ticks
for j in range(int((R.BRAIN[1] - R.BRAIN[0]) / 0.25)):
    t2 = env_t(0.02); P_(R.BRAIN[0] + 0.1 + j * 0.25, rng.standard_normal(len(t2)) * np.exp(-t2 * 200), 0.08)
# end chip pop + comedic button
t2 = env_t(0.08); P_(R.END + 0.2, np.sin(2 * np.pi * (500 + 1500 * t2 / 0.08) * t2) * np.exp(-t2 * 40), 0.25)
for j, (m, d_) in enumerate([(67, 0.12), (60, 0.12), (61, 0.5)]):
    t2 = env_t(d_ + 0.2); P_(R.END + 0.4 + j * 0.16, np.sin(2 * np.pi * note(m) * t2) * np.exp(-t2 * 6) + 0.3 * np.sign(np.sin(2 * np.pi * note(m) * t2)) * np.exp(-t2 * 9), 0.12)
duck = 1 - 0.45 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.05, 0, 1)
out += (mus * 0.12 * duck).astype(np.float32)
f = int(0.3 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
