import os, numpy as np, soundfile as sf
D = os.path.dirname(os.path.abspath(__file__))
a, sr = sf.read(D + "/song.wav", dtype="float32")
A, B = 24.18, 4.82
x1 = a[:int(A*sr)]; x2 = a[int(B*sr):int(A*sr)].copy()
cf = int(0.015*sr)
r = np.linspace(0, 1, cf)[:, None]
x1[-cf:] = x1[-cf:]*(1-r) + x2[:cf]*r
song = np.concatenate([x1, x2[cf:]])
f = int(0.35*sr); song[-f:] *= np.linspace(1, 0, f)[:, None]
total = 43.54 + 4.2
N = int(total*sr)
out = np.zeros((N, 2), np.float32)
out[:len(song)] += song[:N]
t = np.arange(N)/sr
# outro: soft office room tone + ding on thumbs up
rng = np.random.default_rng(1)
s0 = len(song)
n = rng.standard_normal(N - s0); n = np.convolve(n, np.ones(60)/60, 'same')
out[s0:, 0] += n*0.02; out[s0:, 1] += n*0.02
for tt, f0 in ((44.95, 1318.5), (45.1, 1760.0)):
    i = int(tt*sr); L = int(0.9*sr); k = np.arange(L)/sr
    d = (np.sin(2*np.pi*f0*k) + 0.3*np.sin(2*np.pi*2*f0*k))*np.exp(-k*5)*0.18
    out[i:i+L, 0] += d; out[i:i+L, 1] += d
out /= max(1.0, np.abs(out).max()/0.97)
sf.write(D + "/mix.wav", out, sr); print("song", round(len(song)/sr, 2), "total", total)
