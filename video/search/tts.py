import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("G", "Babe, I'm getting snacks. Don't touch my phone.", None, 1.0, 1.0, 1.4, 0.6, None),          # 0 -> walks off
     ("H", "Why would he say that?", "…Why would he say that?", 0.95, 1.0, 1.0, 0, None),               # 1 -> picks up phone
     ("H", "Let's see. How to make my girlfriend happy. Aww!", "Let's see. \"How to make my girlfriend happy.\" Aww!", 1.0, 1.0, 1.0, 0, None),  # 2
     ("H", "Why is my girlfriend angry?", "\"Why is my girlfriend angry?\"", 0.98, 1.0, 0.9, 0, None),  # 3
     ("H", "Why is she angry when I didn't do anything?", "\"Why is she angry when I didn't do anything?\"", 1.0, 1.0, 0.9, 0, None),  # 4
     ("H", "How to apologise for something you don't know you did.", "\"How to apologise for something you don't know you did.\"", 1.0, 1.0, 0.9, 0, None),  # 5
     ("H", "Is it normal for girlfriends to remember everything?", "\"Is it normal for girlfriends to remember EVERYTHING?\"", 1.0, 1.05, 1.1, 0, None),  # 6 -> he returns
     ("G", "Baby... what are you doing with my phone?", "Baby… what are you doing with my phone?", 0.95, 1.0, 0.3, 0, None),  # 7
     ("H", "Sit down.", None, 0.85, 1.0, 1.3, 0, None),                                                 # 8 -> he sits
     ("H", "How to survive an argument without talking.", "\"How to survive an argument without talking.\"", 1.0, 1.05, 0.5, 0, None),  # 9
     ("G", "That's... research.", "That's… research.", 0.95, 1.0, 0.4, 0, None),                        # 10
     ("H", "How to hide from your girlfriend in your own house.", "\"How to hide from your girlfriend in your own house.\"", 1.0, 1.1, 0.5, 0, None),  # 11
     ("G", "Okay, that one was a joke.", None, 1.0, 1.0, 0.5, 0, None),                                 # 12
     ("H", "How to disappear and start a new life?", "\"How to disappear and start a new life?\"", 0.92, 1.2, 1.2, 0, None),  # 13 -> stare
     ("H", "What is this?!", "WHAT IS THIS?!", 1.0, 1.6, 0.3, 0, None),                                # 14
     ("G", "Baby, I just have one question.", None, 0.95, 1.0, 0.8, 0, None),                           # 15
     ("G", "Is there life insurance for boyfriends?", None, 0.88, 1.0, 1.4, 0, None),                   # 16 -> deadpan pause
     ("H", "Why would you need life insurance?!", "WHY WOULD YOU NEED LIFE INSURANCE?!", 1.05, 1.6, 0.6, 0, None),  # 17
     ("G", "Look at you right now.", "…Look at you right now.", 0.9, 1.0, 0.0, 0, None)]                # 18
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
total = t + 2.2
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); print(" ".join(f"{s['i']}:{s['start']}" for s in segs))
