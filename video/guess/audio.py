import os, json, numpy as np, soundfile as sf, importlib.util
D = os.path.dirname(os.path.abspath(__file__)); SR = 24000
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR)
rng = np.random.default_rng(5)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
spec = importlib.util.spec_from_file_location('gr', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
S, E = R.S, R.E
def note(m): return 440 * 2 ** ((m - 69) / 12)
def pluck(f, d):
    n = int(d * SR); p = max(2, int(SR / f)); buf = rng.uniform(-1, 1, p); o = np.zeros(n)
    for i in range(n):
        o[i] = buf[i % p]; buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.995
    return o
# bouncy, slightly sneaky comedy groove (original)
mus = np.zeros(N); beat = 60 / 100; cache = {}
prog = [[45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59], [40, 47, 52, 56]]
for b in range(int(T / (4 * beat)) + 1):
    ch = prog[b % 4]
    for q in range(8):
        m = ch[[0, 2, 1, 3, 0, 2, 3, 1][q]] + 12 * (q % 4 == 3)
        if m not in cache: cache[m] = pluck(note(m), 0.6)
        st = int((b * 4 + q * 0.5) * beat * SR); s_ = cache[m]; L = min(len(s_), N - st)
        if L > 0: mus[st:st + L] += s_[:L] * 0.35
    for q in range(4):
        st = int((b * 4 + q) * beat * SR); L = int(0.25 * SR); tt = np.arange(L) / SR
        if st + L < N:
            if q in (0, 2): mus[st:st + L] += np.sin(2 * np.pi * (55 + 45 * np.exp(-tt * 25)) * tt) * np.exp(-tt * 11) * 0.7
            else:
                n = rng.standard_normal(L); n -= np.convolve(n, np.ones(6) / 6, 'same'); mus[st:st + L] += n * np.exp(-tt * 24) * 0.3
mus = np.convolve(mus, np.ones(5) / 5, 'same'); mus /= np.abs(mus).max()
g = np.ones(N)
def gate(a, b, fade=0.08):
    i, j = int(a * SR), int(b * SR); f = int(fade * SR)
    g[i:j] = 0; g[max(0, i - f):i] *= np.linspace(1, 0, min(f, i)); g[j:j + f] *= np.linspace(0, 1, len(g[j:j + f]))
gate(R.T_REW[0], R.T_REW[1])            # rewind
gate(R.REVEAL, S(19) - 0.05)            # bomb + held silence
mus *= g
def put(at, sig):
    i = int(at * SR); L = min(len(sig), N - i)
    if L > 0: out[i:i + L] += sig[:L].astype(np.float32)
def env_t(d): return np.arange(int(d * SR)) / SR
# hook stamps
for j in range(3):
    tt = env_t(0.18); put(0.35 + j * 0.33, (np.sin(2 * np.pi * 140 * tt) + rng.standard_normal(len(tt)) * 0.5) * np.exp(-tt * 30) * 0.5)
# rewind: descending warble + tape noise
tt = env_t(R.T_REW[1] - R.T_REW[0])
f = 900 - 600 * tt / tt[-1] + 120 * np.sin(2 * np.pi * 14 * tt)
put(R.T_REW[0], (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.18 + rng.standard_normal(len(tt)) * 0.05) * np.sin(np.pi * tt / tt[-1]))
# wrong buzzers on each "No"
for i in (9, 11, 13):
    tt = env_t(0.32); sq = np.sign(np.sin(2 * np.pi * 110 * tt)) + np.sign(np.sin(2 * np.pi * 116 * tt))
    put(E(i) + 0.02, sq * np.exp(-tt * 6) * (0.10 if i != 13 else 0.15))
# pop for tags
for at in (S(5), S(8), S(10), S(12), S(14), S(19) + 0.6):
    tt = env_t(0.08); put(at, np.sin(2 * np.pi * (500 + 1500 * tt / 0.08) * tt) * np.exp(-tt * 40) * 0.25)
# bomb boom on reveal
tt = env_t(1.2); put(R.REVEAL, (np.sin(2 * np.pi * (45 + 60 * np.exp(-tt * 8)) * tt) * 0.8 + rng.standard_normal(len(tt)) * np.exp(-tt * 12) * 0.3) * np.exp(-tt * 3.5) * 0.7)
# crickets in held silence
a, b = E(17) + 0.3, S(18) - 0.05
tt = np.arange(int((b - a) * SR)) / SR
cr = np.sin(2 * np.pi * 4700 * tt) * (np.sin(2 * np.pi * 30 * tt) > 0.3) * ((tt % 0.5) < 0.18) * 0.05
put(a, cr)
duck = 1 - 0.45 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.05, 0, 1)
out += (mus * 0.12 * duck).astype(np.float32)
f = int(0.5 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
