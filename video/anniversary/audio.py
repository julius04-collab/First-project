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
segs = json.load(open(D + '/vo.json'))['segs']
# soft TV crowd murmur (filtered noise with slow swells), quieter during her long stare
cr = rng.standard_normal(N); cr = np.convolve(cr, np.ones(40) / 40, 'same'); cr -= np.convolve(cr, np.ones(600) / 600, 'same')
sw = 0.6 + 0.4 * np.sin(np.arange(N) / SR * 0.9) * np.sin(np.arange(N) / SR * 0.37)
cg = np.ones(N); a_, b_ = int(segs[11]['end'] * SR), int(segs[12]['start'] * SR); cg[a_:b_] = 0.2
out += (cr / np.abs(cr).max() * sw * cg * 0.05).astype(np.float32)
mus = mus.copy(); g = np.ones(N); g[a_:b_] = 0; mus *= g
hit = segs[14]['end'] + 0.6
i = int(hit * SR); L = int(0.25 * SR); tt = np.arange(L) / SR
th = (rng.standard_normal(L) * 0.6 + np.sin(2 * np.pi * (180 - 300 * tt) * tt)) * np.exp(-tt * 18) * 0.7
out[i:i + L] += th[:N - i].astype(np.float32)
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
