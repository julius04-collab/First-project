import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("H", "James Smith!", "JAMES SMITH!", 0.95, 1.5, 1.3, 2.2, None),                          # 0 -> freeze 1s
     ("G", "...Yes, baby?", "…Yes, baby?", 0.85, 0.85, 0.2, 0, None),                           # 1
     ("H", "Come here.", None, 0.9, 1.0, 0.2, 0, None),                                         # 2
     ("G", "What happened?", None, 1.0, 1.0, 0.2, 0, None),                                     # 3
     ("H", "I said, come here!", "I said COME HERE!", 1.0, 1.5, 1.7, 0, None),                  # 4 -> approach
     ("G", "Baby, did I do something?", None, 1.0, 1.0, 0.15, 0, None),                         # 5
     ("H", "You tell me.", None, 0.9, 1.0, 0.5, 0, None),                                       # 6
     ("G", "Okay... I didn't forget your birthday.", "Okay… I didn't forget your birthday.", 1.05, 1.0, 0.15, 0, None),  # 7
     ("H", "It's not my birthday!", None, 1.05, 1.15, 0.15, 0, None),                           # 8
     ("G", "I didn't eat your food!", None, 1.1, 1.0, 0.15, 0, None),                           # 9
     ("H", "I haven't even asked you anything!", None, 1.1, 1.15, 0.15, 0, None),               # 10
     ("G", "I didn't talk to your friend!", None, 1.1, 1.0, 0.15, 0, None),                     # 11
     ("H", "Which friend?!", "WHICH FRIEND?!", 1.0, 1.6, 0.2, 0, None),                         # 12
     ("G", "See?! That's why I'm confused!", None, 1.1, 1.1, 0.8, 0, None),                     # 13 -> stare
     ("H", "So you really don't know what you did?", None, 1.0, 1.0, 0.15, 0, None),            # 14
     ("G", "Baby, I swear! I've been a good boyfriend!", None, 1.1, 1.0, 0.15, 0, None),        # 15
     ("H", "You forgot something very important.", None, 0.92, 1.0, 0.6, 0, None),              # 16 -> sweat
     ("G", "Your birthday?", None, 1.1, 1.0, 0.1, 0, None),                                     # 17
     ("H", "No.", None, 1.0, 1.0, 0.1, 0, None),                                                # 18
     ("G", "Our anniversary?", None, 1.1, 1.0, 0.1, 0, None),                                   # 19
     ("H", "No!", "NO!", 1.0, 1.3, 0.1, 0, None),                                               # 20
     ("G", "Valentine's Day?", None, 1.1, 1.0, 0.1, 0, None),                                   # 21
     ("H", "That was months ago!", "THAT WAS MONTHS AGO!", 1.05, 1.5, 0.15, 0, None),           # 22
     ("G", "Then what?!", None, 1.05, 1.2, 0.3, 0, None),                                       # 23
     ("H", "You forgot to take out the trash!", None, 1.0, 1.3, 0.5, 0, None),                  # 24 -> scratch
     ("G", "That's why you used my full name?!", "THAT'S WHY YOU USED MY FULL NAME?!", 1.05, 1.4, 0.15, 0, None),  # 25
     ("H", "Do you want me to call your father's name too?!", None, 1.1, 1.35, 0.3, 0, None),   # 26
     ("G", "I'm going! I'm going!", None, 1.15, 1.2, 0.5, 0, None),                             # 27
     ("G", "I thought I had committed a crime...", "I thought I had committed a crime…", 0.95, 0.55, 0.2, 0, None),  # 28 mutter
     ("H", "I heard that!", "I HEARD THAT!", 1.0, 1.6, 0.0, 0, None)]                           # 29
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
total = t + 1.8
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); print(" ".join(f"{s['i']}:{s['start']}" for s in segs))
