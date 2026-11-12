import json, os, numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
vo, sr = sf.read(os.path.join(HERE, "vo.wav"), dtype="float32")
segs = json.load(open(os.path.join(HERE, "vo.json")))
LEAD, TAIL = 0.5, 2.0
total = segs[-1]["end"] + LEAD + TAIL
N = int(total * sr) + sr
t = np.arange(N) / sr
out = np.zeros(N, np.float32)
v = vo / (np.abs(vo).max() + 1e-9) * 0.9
s0 = int(LEAD * sr)
out[s0:s0 + len(v)] += v[: N - s0]

# soft ambient pad: Am - F - C - G, 4 s each
def note(m):
    return 440 * 2 ** ((m - 69) / 12)
chords = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]
pad = np.zeros(N)
CL = 4.0
for ci in range(int(total / CL) + 1):
    ch = chords[ci % 4]
    a, b = int(ci * CL * sr), int(min(N, (ci + 1) * CL * sr + 1.0 * sr))
    tt = t[a:b] - ci * CL
    env = np.minimum(1, tt / 1.2) * np.clip((CL + 1.0 - tt) / 1.2, 0, 1)
    sig = np.zeros(b - a)
    for m in ch + [ch[0] - 12]:
        f = note(m)
        for det in (-0.6, 0.6):
            sig += np.sin(2 * np.pi * (f + det) * tt) + 0.3 * np.sin(2 * np.pi * 2 * (f + det) * tt) + 0.1 * np.sin(2 * np.pi * 3 * (f + det) * tt)
    pad[a:b] += sig * env
# gentle pluck pulse on 8ths
for k in range(int(total / 0.5)):
    a = int(k * 0.5 * sr); b = min(N, a + int(0.4 * sr))
    ch = chords[int(k * 0.5 / CL) % 4]
    f = note(ch[k % 3] + 12)
    tt = t[a:b] - k * 0.5
    pad[a:b] += 0.5 * np.sin(2 * np.pi * f * tt) * np.exp(-tt * 9)
pad = pad / np.abs(pad).max()
out += (pad * 0.11).astype(np.float32)

# whooshes at scene changes
bounds = [segs[i]["start"] + LEAD - 0.15 for i in range(1, len(segs))]
rng = np.random.default_rng(1)
for bt in bounds:
    L = int(0.6 * sr)
    n = rng.standard_normal(L)
    k = 40
    n = np.convolve(n, np.ones(k) / k, mode="same")
    n -= np.convolve(n, np.ones(400) / 400, mode="same")
    env = np.sin(np.linspace(0, np.pi, L)) ** 2
    a = int((bt - 0.3) * sr)
    out[a:a + L] += (n / np.abs(n).max() * env * 0.12).astype(np.float32)
    # pop on timer change
    pl = int(0.09 * sr); tt = np.arange(pl) / sr
    pp = np.sin(2 * np.pi * (900 - 4000 * tt) * tt) * np.exp(-tt * 40)
    a = int(bt * sr)
    out[a:a + pl] += (pp * 0.15).astype(np.float32)
fade = int(1.0 * sr)
end = int(total * sr)
out = out[:end]
out[-fade:] *= np.linspace(1, 0, fade)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(os.path.join(HERE, "mix.wav"), out, sr)
print("audio", round(total, 2))
