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
gate = np.ones(N)
a_, b_ = int(segs[9]['end'] * SR), int(segs[11]['start'] * SR)
gate[a_:b_] = 0; gate[max(0, a_ - 2400):a_] = np.linspace(1, 0, min(2400, a_))
mus = mus * gate
sfx = np.zeros(N)
def put(at, sig):
    i = int(at * SR); L = min(len(sig), N - i)
    if L > 0: sfx[i:i + L] += sig[:L]
tt = np.arange(int(0.12 * SR)) / SR
put(segs[0]['start'] + 0.3, np.sin(2 * np.pi * (900 - 3000 * tt) * tt) * np.exp(-tt * 40) * 0.5)            # poke pop
put(segs[5]['end'] + 0.1, rng.standard_normal(int(0.2 * SR)) * np.exp(-np.arange(int(0.2 * SR)) / SR * 30) * 0.5)  # playful slap
for k in range(6):                                                                                             # crickets in the silence
    for j in range(3):
        t2 = np.arange(int(0.03 * SR)) / SR
        put(segs[9]['end'] + 0.3 + k * 0.33 + j * 0.045, np.sin(2 * np.pi * 4600 * t2) * np.hanning(len(t2)) * 0.25)
t3 = np.arange(int(0.06 * SR)) / SR
put(segs[10]['end'] + 0.25, (rng.standard_normal(len(t3)) * 0.4 + np.sin(2 * np.pi * 2000 * t3)) * np.exp(-t3 * 80) * 0.6)   # lamp click
out += sfx.astype(np.float32)
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
