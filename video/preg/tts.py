import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("H", "Babe, come inside. I need to tell you something.", None, 1.0, 1.0, 0.25, 0.8, None),        # 0
     ("G", "Nah, you come outside. The breeze is nice.", None, 0.95, 1.0, 0.3, 0, None),               # 1
     ("H", "Babe. You need to come inside with me.", None, 1.0, 1.05, 0.25, 0, None),                  # 2
     ("G", "Why? What happened?", None, 1.0, 1.0, 0.4, 0, None),                                       # 3
     ("H", "Because... you're going to be a father.", "Because… you're going to be a father.", 0.92, 1.0, 2.4, 0, None),  # 4 -> brain cell leaves
     ("G", "Am I pregnant?", None, 0.95, 1.0, 0.5, 0, None),                                           # 5
     ("H", "No. I'm pregnant.", "No. I'M pregnant.", 0.88, 1.0, 1.2, 0, None),                         # 6
     ("G", "Am I pregnant too?", None, 0.95, 1.0, 0.9, 0, None),                                       # 7
     ("H", "Yes, babe. We're pregnant.", None, 0.82, 0.95, 0.0, 0, None)]                              # 8
t = 0.0; buf = np.zeros(SR * 140, np.float32); segs = []
for i, (who, line, cap, sp, gain, pause, pre, fx) in enumerate(L):
    t += pre
    a, _ = k.create(line, voice=V[who], speed=sp, lang="en-us")
    nz = np.where(np.abs(a) > 0.01)[0]
    if len(nz): a = a[max(0, nz[0] - 600): nz[-1] + 1200]
    if fx == "phone":
        a = band(a, 350, 3200) * 1.6; a = np.tanh(a * 1.5) / 1.5
    elif fx == "muffled":
        a = band(a, 80, 900) * 1.5
    a = a * gain
    n0 = int(t * SR); buf[n0:n0 + len(a)] += a
    hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[j*hop:(j+1)*hop] ** 2))) for j in range(len(a) // hop)]
    segs.append(dict(i=i, who=who, fx=fx, text=(cap or line).replace("...", "…"), start=round(t, 3), end=round(t + len(a) / SR, 3), env=env))
    t += len(a) / SR + pause
p = np.percentile(np.concatenate([s["env"] for s in segs]), 95)
for s in segs: s["env"] = [round(min(1, e / p), 3) for e in s["env"]]
total = t + 2.6
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); print(" ".join(f"{s['i']}:{s['start']}" for s in segs))
