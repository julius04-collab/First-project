import os, json, numpy as np, soundfile as sf, importlib.util
D = os.path.dirname(os.path.abspath(__file__)); SR = 24000
T = json.load(open(D + "/vo.json"))["total"]; N = int(T * SR)
rng = np.random.default_rng(5)
vo, _ = sf.read(D + "/vo.wav", dtype="float32"); vo = vo / np.abs(vo).max() * 0.9
out = np.zeros(N, np.float32); out[:len(vo)] += vo[:N]
spec = importlib.util.spec_from_file_location('ar', D + '/render.py'); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
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
gate(R.T_REW[0], R.T_REW[1])
gate(E(15), S(19))            # she notices -> babe -> jolt
gate(E(22), E(24) + 0.3)      # stare + get out
mus *= g
def put(at, sig):
    i = int(at * SR); L = min(len(sig), N - i)
    if L > 0: out[i:i + L] += sig[:L].astype(np.float32)
def env_t(d): return np.arange(int(d * SR)) / SR
def snore(at, dur=1.3, amp_=0.22):
    tt = env_t(dur); e = np.sin(np.pi * tt / dur) ** 1.5
    saw = ((tt * 70) % 1 - 0.5) * 2; n = rng.standard_normal(len(tt))
    s = (saw * 0.7 + np.convolve(n, np.ones(30) / 30, 'same') * 3) * e * (1 + 0.6 * np.sin(2 * np.pi * 25 * tt))
    put(at, s * amp_)
def whistle(at, dur=0.9, amp_=0.06):
    tt = env_t(dur); f = 1400 - 500 * tt / dur
    put(at, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / dur) * amp_)
# hook snores
snore(0.3, 1.2, 0.12); whistle(1.55, 0.6, 0.04); snore(2.2, 1.2, 0.18)
tt = env_t(R.T_REW[1] - R.T_REW[0]); f = 900 - 600 * tt / tt[-1] + 120 * np.sin(2 * np.pi * 14 * tt)
put(R.T_REW[0], (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.18 + rng.standard_normal(len(tt)) * 0.05) * np.sin(np.pi * tt / tt[-1]))
# soft snores while she rants away
for at in np.arange(S(14) + 2.4, E(15), 2.2):
    snore(at, 1.2, 0.07); whistle(at + 1.25, 0.6, 0.025)
# big snore in the silence after "Babe?"
snore(E(16) + 0.15, 1.15, 0.28)
# jolt: cymbal-ish crash
tt = env_t(0.8); put(S(18) - 0.05, rng.standard_normal(len(tt)) * np.exp(-tt * 6) * 0.25)
# pops for tags
for at in (0.3, S(1) + 0.1, S(7), S(8), R.BACK2SLEEP + 0.4):
    tt = env_t(0.08); put(at, np.sin(2 * np.pi * (500 + 1500 * tt / 0.08) * tt) * np.exp(-tt * 40) * 0.25)
# eye twitch ticks
for at in np.arange(R.TWITCH[0], R.TWITCH[1] - 0.1, 1 / 9 * 2):
    tt = env_t(0.03); put(at, np.sin(2 * np.pi * 2500 * tt) * np.exp(-tt * 150) * 0.15)
# ending: back to sleep snores
for at in np.arange(R.BACK2SLEEP + 0.2, T - 1.0, 1.6):
    snore(at, 1.2, 0.14)
duck = 1 - 0.45 * np.clip(np.convolve(np.abs(out), np.ones(2400) / 2400, 'same') / 0.05, 0, 1)
out += (mus * 0.12 * duck).astype(np.float32)
f = int(0.5 * SR); out[-f:] *= np.linspace(1, 0, f)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, SR); print("ok")
