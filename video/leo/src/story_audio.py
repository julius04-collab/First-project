import os, numpy as np, soundfile as sf
D = os.path.dirname(os.path.abspath(__file__))
SR = 24000; T = 120.0; N = int(T * SR); t = np.arange(N) / SR
rng = np.random.default_rng(11)
vo, _ = sf.read(D + "/narration.wav", dtype="float32")
vo = vo / np.abs(vo).max() * 0.9
mix = np.zeros(N, np.float32); mix[:len(vo)] += vo[:N]
def note(m): return 440 * 2 ** ((m - 69) / 12)
mus = np.zeros(N)
def add(buf, i, sig):
    i = int(i)
    if i >= N or i < 0: return
    L = min(len(sig), N - i); buf[i:i + L] += sig[:L]
# mysterious pad: Dm - Bb - F - C (warm resolve at the end: F major)
prog = [[50, 57, 62, 65], [46, 53, 58, 62], [41, 53, 57, 60], [48, 55, 60, 64]]
bar = 4.0
for b in range(int(T / bar) + 1):
    ch = prog[b % 4] if b < 27 else [41, 53, 57, 60]
    L = int((bar + 1.5) * SR); tt = np.arange(L) / SR
    env = np.minimum(1, tt / 1.2) * np.clip((bar + 1.5 - tt) / 1.5, 0, 1)
    sig = sum((np.sin(2 * np.pi * note(m) * tt) + 0.25 * np.sin(2 * np.pi * 2 * note(m) * tt + 0.3)) for m in ch) * env
    add(mus, b * bar * SR, sig * 0.18)
    # music-box motif
    for j, m in enumerate([ch[2] + 12, ch[3] + 12, ch[1] + 24, ch[3] + 12]):
        L2 = int(1.2 * SR); t2 = np.arange(L2) / SR
        add(mus, (b * bar + j * 1.0) * SR, np.sin(2 * np.pi * note(m) * t2) * np.exp(-t2 * 4) * 0.12)
# tension pulse 60-110 s (low heartbeat)
for k in range(int(50 / 0.8)):
    st = 60 + k * 0.8
    rate = 0.8 if st < 95 else 0.55
    L = int(0.25 * SR); tt = np.arange(L) / SR
    for off in (0, 0.18):
        add(mus, (st + off) * SR, np.sin(2 * np.pi * (48 + 30 * np.exp(-tt * 20)) * tt) * np.exp(-tt * 12) * (0.35 if off == 0 else 0.22))
mus /= np.abs(mus).max()
duck = np.ones(N)
env_vo = np.convolve(np.abs(mix), np.ones(2400) / 2400, mode="same")
duck = 1 - 0.45 * np.clip(env_vo / 0.08, 0, 1)
mix += (mus * 0.16 * duck).astype(np.float32)
sfx = np.zeros(N)
def noise(dur, lp=4):
    n = rng.standard_normal(int(dur * SR))
    return np.convolve(n, np.ones(lp) / lp, mode="same")
def shatter(at, amp=0.5):
    n = noise(0.5, 2); e = np.exp(-np.arange(len(n)) / SR * 9)
    add(sfx, at * SR, n * e * amp)
    for k in range(10):
        f = rng.uniform(2500, 6000); L = int(0.25 * SR); tt = np.arange(L) / SR
        add(sfx, (at + rng.uniform(0, 0.35)) * SR, np.sin(2 * np.pi * f * tt) * np.exp(-tt * 30) * amp * 0.4)
def whoosh(at, dur=0.6, amp=0.25):
    n = noise(dur, 30); n -= np.convolve(n, np.ones(300) / 300, mode="same")
    add(sfx, at * SR, n / (np.abs(n).max() + 1e-9) * np.sin(np.linspace(0, np.pi, len(n))) ** 2 * amp)
def bell(at, amp=0.25):
    L = int(0.8 * SR); tt = np.arange(L) / SR
    add(sfx, at * SR, (np.sin(2 * np.pi * 2200 * tt) + 0.5 * np.sin(2 * np.pi * 3300 * tt)) * np.exp(-tt * 6) * amp)
def creak(at, dur=1.2, amp=0.15):
    L = int(dur * SR); tt = np.arange(L) / SR
    f = 380 + 120 * np.sin(tt * 7)
    add(sfx, at * SR, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.linspace(0, np.pi, L)) * amp * (0.6 + 0.4 * np.sign(np.sin(tt * 90))))
def crash(at, amp=0.7):
    n = noise(1.2, 3); e = np.exp(-np.arange(len(n)) / SR * 4)
    add(sfx, at * SR, n * e * amp)
    L = int(1.5 * SR); tt = np.arange(L) / SR
    add(sfx, at * SR, (np.sin(2 * np.pi * 180 * tt) + 0.6 * np.sin(2 * np.pi * 431 * tt) + 0.4 * np.sin(2 * np.pi * 977 * tt)) * np.exp(-tt * 3) * amp * 0.5)
    L = int(0.4 * SR); tt = np.arange(L) / SR
    add(sfx, at * SR, np.sin(2 * np.pi * (60 + 80 * np.exp(-tt * 15)) * tt) * np.exp(-tt * 8) * amp)
def chime(at, amp=0.18):
    for j, m in enumerate([77, 81, 84, 89]):
        L = int(1.6 * SR); tt = np.arange(L) / SR
        add(sfx, (at + j * 0.12) * SR, np.sin(2 * np.pi * note(m) * tt) * np.exp(-tt * 3) * amp)
whoosh(2.0, 0.5, 0.08)
chime(8.9, 0.1)                     # shadow arm drops (clip 1)
whoosh(27.0, 0.5, 0.2); shatter(27.95)   # flowerpot
bell(44.8, 0.15); creak(46.2, 0.8, 0.08); whoosh(47.0, 0.8, 0.3)   # cyclist
whoosh(75.4, 1.4, 0.35)             # car passes
creak(86.5, 2.5, 0.12); creak(93.0, 2.0, 0.14); creak(99.3, 0.8, 0.2)   # sign bracket
whoosh(102.0, 0.9, 0.4)             # shadow yank
crash(104.9)
chime(117.4)                        # secret wave
mix += (sfx * 0.9).astype(np.float32)
f = int(1.2 * SR); mix[-f:] *= np.linspace(1, 0, f)
mix /= max(1.0, np.abs(mix).max() / 0.97)
sf.write(D + "/story_mix.wav", mix, SR); print("mix ok")
