import json, os, numpy as np, soundfile as sf
D = os.path.dirname(os.path.abspath(__file__))
vo, sr = sf.read(D + "/vo.wav", dtype="float32")
d = json.load(open(D + "/vo.json"))
LEAD = 0.6
total = d["end"] + LEAD + 2.6
N = int(total * sr); t = np.arange(N) / sr
out = np.zeros(N, np.float32)
v = vo / np.abs(vo).max() * 0.9
s0 = int(LEAD * sr); out[s0:s0 + len(v)] += v[:N - s0]
BT = d["beat_start"] + LEAD; beat = 60 / d["bpm"]; bar = 4 * beat
rng = np.random.default_rng(7)
def note(m): return 440 * 2 ** ((m - 69) / 12)
prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
mus = np.zeros(N)
def add(i, sig):
    if i >= N: return
    L = min(len(sig), N - i); mus[i:i + L] += sig[:L]
# soft pad under the quiz (before the beat)
pad_end = BT
for ci in range(int(pad_end / bar) + 1):
    a = ci * bar; L = int(min(bar + 0.6, pad_end - a + 0.3) * sr)
    if L <= 0: break
    tt = np.arange(L) / sr; env = np.minimum(1, tt / 0.6) * np.clip((L / sr - tt) / 0.6, 0, 1)
    sig = sum(np.sin(2 * np.pi * note(m) * tt) for m in prog[ci % 4]) * env
    add(int(a * sr), sig * 0.12)
# riser into the drop
L = int(1.2 * sr); tt = np.arange(L) / sr
n = rng.standard_normal(L); n = n - np.convolve(n, np.ones(20) / 20, 'same')
add(int((BT - 1.2) * sr), n * (tt / 1.2) ** 2 * 0.25)
# dembow beat from BT to end
nb = int((total - BT) / beat) + 1
for b in range(nb):
    bt = BT + b * beat
    i = int(bt * sr)
    kl = int(0.25 * sr); k = np.arange(kl) / sr
    add(i, np.sin(2 * np.pi * (50 + 70 * np.exp(-k * 35)) * k) * np.exp(-k * 12) * 1.3)
    for off in ((0.75, 1.5) if b % 2 == 0 else (0.75,)):
        pass
    bar_pos = b % 4
    for sn in ([0.75] if bar_pos in (0, 2) else [0.5]):
        j = int((bt + sn * beat) * sr); sl = int(0.15 * sr)
        n = rng.standard_normal(sl); n = n - np.convolve(n, np.ones(6) / 6, 'same')
        sig = n * np.exp(-np.arange(sl) / sr * 28) * 0.5 + np.sin(2 * np.pi * 190 * np.arange(sl) / sr) * np.exp(-np.arange(sl) / sr * 30) * 0.4
        add(j, sig)
    for h in (0, 0.5):
        j = int((bt + h * beat) * sr); hl = int(0.04 * sr)
        n = rng.standard_normal(hl); n = n - np.convolve(n, np.ones(3) / 3, 'same')
        add(j, n * np.exp(-np.arange(hl) / sr * 90) * 0.18)
    ch = prog[(b // 4) % 4]
    bl = int(beat * 0.9 * sr); tb = np.arange(bl) / sr
    add(i, np.sin(2 * np.pi * note(ch[0] - 24) * tb) * np.exp(-tb * 2) * 0.55)
    for q in (0, 0.5):
        j = int((bt + q * beat) * sr); pl = int(0.25 * sr); tp = np.arange(pl) / sr
        m = ch[(b * 2 + int(q * 2)) % 3] + 12
        add(j, (np.sin(2 * np.pi * note(m) * tp) + 0.3 * np.sin(4 * np.pi * note(m) * tp)) * np.exp(-tp * 12) * 0.25)
mus /= np.abs(mus).max()
duck = np.ones(N)
out += (mus * 0.16 * duck).astype(np.float32)
fade = int(1.0 * sr); out[-fade:] *= np.linspace(1, 0, fade)
out /= max(1.0, np.abs(out).max() / 0.97)
sf.write(D + "/mix.wav", out, sr); print("audio", round(total, 2))
