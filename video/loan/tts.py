import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("G", "Baby, please, can you lend me some money?", None, 1.0, 1.0, 0.2, 1.6, None),                    # 0 (walks in)
     ("H", "Again? What happened to the money I gave you last week?", None, 1.1, 1.0, 0.2, 0, None),         # 1
     ("G", "Baby, it's an emergency. I'll pay you back tomorrow. I promise!", None, 1.1, 1.0, 0.2, 0, None), # 2
     ("H", "Are you sure?", None, 1.0, 1.0, 0.15, 0, None),                                                  # 3
     ("G", "On my mother's life! Tomorrow, first thing in the morning!", None, 1.12, 1.15, 1.5, 0, None),    # 4 -> she sends money
     ("G", "You're the best girlfriend in the world!", None, 1.1, 1.15, 3.0, 0, None),                       # 5 -> kiss, walk off, calendar
     ("H", "Baby, remember that money I lent you?", None, 1.05, 1.0, 0.15, 0, None),                         # 6
     ("G", "Which money?", None, 1.0, 1.0, 0.45, 0, None),                                                   # 7 -> scratch
     ("H", "The money you promised to pay back tomorrow!", "THE MONEY YOU PROMISED TO PAY BACK TOMORROW!", 1.1, 1.4, 0.15, 0, None),  # 8
     ("G", "Ohhh, that money!", "Ohhh, THAT money!", 1.0, 1.0, 0.15, 0, None),                              # 9
     ("H", "Yes! It's been three months!", None, 1.05, 1.2, 0.15, 0, None),                                  # 10
     ("G", "Baby, tomorrow is still coming. Be patient.", None, 0.98, 1.0, 1.3, 0, None),                    # 11 -> 1s zoom on her
     ("H", "So when exactly is this tomorrow coming?", None, 1.05, 1.0, 0.15, 0, None),                      # 12
     ("G", "Very soon. I'm just waiting for some money to enter.", None, 1.05, 1.0, 0.15, 0, None),          # 13
     ("H", "From where?", None, 1.0, 1.0, 0.2, 0, None),                                                     # 14
     ("G", "That's between me and my destiny.", None, 0.92, 1.0, 0.8, 0, None),                              # 15 -> heavenly
     ("H", "Julius! Pay me my money!", "JULIUS! Pay me my money!", 1.05, 1.4, 0.15, 0, None),                # 16
     ("G", "Why are you putting pressure on me? Do you want me to go and steal?", None, 1.1, 1.0, 0.15, 0, None),  # 17
     ("H", "I want my money!", "I WANT MY MONEY!", 1.0, 1.6, 0.5, 0, None),                                  # 18
     ("G", "Baby, actually... can you lend me another small amount?", "Baby, actually… can you lend me another small amount?", 1.0, 1.0, 0.45, 0, None),  # 19 -> scratch
     ("H", "What?!", "WHAT?!", 1.0, 1.6, 0.2, 0, None),                                                      # 20
     ("G", "Just to settle something. I'll pay everything back tomorrow.", None, 1.1, 1.0, 1.0, 0, None),    # 21 -> pillow, chase
     ("G", "Baby! Don't you trust tomorrow?!", "BABY! DON'T YOU TRUST TOMORROW?!", 1.1, 1.4, 0.0, 0, None)]  # 22
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
total = t + 1.0
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); print(" ".join(f"{s['i']}:{s['start']}" for s in segs))
