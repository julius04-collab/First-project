import os, numpy as np, soundfile as sf
D = os.path.dirname(os.path.abspath(__file__))
SR = 24000; import json
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR); t = np.arange(N) / SR
rng = np.random.default_rng(3)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
def note(m): return 440 * 2 ** ((m - 69) / 12)
def pluck(f, d):
    n = int(d * SR); p = max(2, int(SR / f)); buf = rng.uniform(-1, 1, p); o = np.zeros(n)
    for i in range(n):
        o[i] = buf[i % p]; buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.995
    return o
mus = np.zeros(N)
prog = [[52, 59, 64, 67, 71], [48, 55, 60, 64, 67], [45, 52, 57, 60, 64], [50, 57, 62, 66, 69]]  # Em9-ish lofi
beat = 60 / 72; cache = {}
for b in range(int(T / (4 * beat)) + 1):
    ch = prog[b % 4]
    for j, m in enumerate(ch):
        if (m, 2.5) not in cache: cache[(m, 2.5)] = pluck(note(m), 2.5)
        st = int((b * 4 * beat + j * 0.09) * SR); s_ = cache[(m, 2.5)]; L = min(len(s_), N - st)
        if L > 0: mus[st:st + L] += s_[:L] * 0.5
    for q in range(4):
        st = int((b * 4 + q) * beat * SR); L = int(0.25 * SR); tt = np.arange(L) / SR
        if st + L < N:
            if q in (0, 2): mus[st:st + L] += np.sin(2 * np.pi * (50 + 40 * np.exp(-tt * 25)) * tt) * np.exp(-tt * 10) * 0.6
            else:
                n = rng.standard_normal(L); n -= np.convolve(n, np.ones(6) / 6, 'same'); mus[st:st + L] += n * np.exp(-tt * 22) * 0.25
mus = np.convolve(mus, np.ones(6) / 6, 'same'); mus /= np.abs(mus).max()
import importlib.util
spec = importlib.util.spec_from_file_location('wr', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
g = np.ones(N); a_, b_ = int((R.T_LEAVE + 1.3) * SR), int(R.CARD2[1] * SR)
g[a_:b_] = 0; mus = mus * g
def put(at, sig):
    i = int(at * SR); L = min(len(sig), N - i)
    if L > 0: out[i:i + L] += sig[:L].astype(np.float32)
tt = np.arange(int(0.4 * SR)) / SR
put(R.T_LEAVE + 1.25, np.sin(2 * np.pi * (70 + 60 * np.exp(-tt * 20)) * tt) * np.exp(-tt * 9) * 0.7 + rng.standard_normal(len(tt)) * np.exp(-tt * 25) * 0.25)   # door shuts
for j, (mn, d) in enumerate([(76, 0.35), (79, 0.25), (76, 0.35), (72, 0.5)]):                   # nervous whistle
    t2 = np.arange(int(d * SR)) / SR; f = 440 * 2 ** ((mn - 69) / 12)
    put(R.T_ENTER + 0.1 + sum(x[1] for x in [(76, 0.35), (79, 0.25), (76, 0.35), (72, 0.5)][:j]), np.sin(2 * np.pi * f * t2 + 3 * np.sin(2 * np.pi * 6 * t2) * 0.02) * np.sin(np.pi * t2 / d) * 0.12)
t3 = np.arange(int(0.06 * SR)) / SR
put(R.T_LAMP, (rng.standard_normal(len(t3)) * 0.4 + np.sin(2 * np.pi * 2000 * t3)) * np.exp(-t3 * 80) * 0.6)                       # lamp click
duck = 1 - 0.35 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.06, 0, 1)
out += (mus * 0.13 * duck).astype(np.float32)
for k in range(9):  # birds
    st = rng.uniform(0.3, 28.5); L = int(0.35 * SR); tt = np.arange(L) / SR
    f = 3200 + 900 * np.sin(tt * 60) + rng.uniform(-300, 300)
    chirp = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / 0.35) ** 2 * 0.06
    i = int(st * SR); out[i:i + L] += chirp[:N - i].astype(np.float32)
f = int(0.6 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
