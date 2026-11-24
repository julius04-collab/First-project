import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("H", "Babe, I feel like you don't listen to me anymore.", None, 1.0, 1.0, 0.4, 1.2, None),    # 0
     ("G", "Baby, listen. Communication is the foundation of every healthy relationship.", None, 0.98, 1.0, 0.2, 0, None),  # 1
     ("H", "Okay...", "Okay…", 0.9, 0.9, 0.2, 0, None),                                              # 2
     ("G", "You need to express your feelings. Never bottle things up. And most importantly, partners must always make time for each other.", None, 1.05, 1.0, 0.2, 0, None),  # 3
     ("H", "Wow. Since when did you become a relationship expert?", None, 1.05, 1.0, 0.2, 0, None),   # 4
     ("G", "Experience, baby. Experience.", None, 0.92, 1.0, 0.4, 0, None),                          # 5
     ("H", "Okay, relationship expert. When was the last time you listened to me without checking your phone?", None, 1.1, 1.0, 0.5, 0, None),  # 6 -> scratch
     ("G", "That's a very good question.", None, 0.98, 1.0, 0.15, 0, None),                          # 7
     ("H", "I'm asking you!", "I'm asking YOU!", 1.0, 1.4, 0.15, 0, None),                           # 8
     ("G", "Baby, don't interrupt. Let me finish my professional analysis.", None, 1.05, 1.0, 0.15, 0, None),  # 9
     ("H", "You were checking football scores while I was talking to you yesterday!", None, 1.12, 1.2, 0.15, 0, None),  # 10
     ("G", "That's different. I was multitasking.", None, 1.0, 1.0, 0.5, 0, None),                   # 11 -> boing
     ("H", "And when was the last time you planned a date for us?", None, 1.05, 1.0, 0.15, 0, None), # 12
     ("G", "A healthy relationship requires effort from both partners.", "A healthy relationship requires effort from BOTH partners.", 1.0, 1.0, 0.15, 0, None),  # 13
     ("H", "So?", None, 1.0, 1.0, 0.15, 0, None),                                                    # 14
     ("G", "You can also plan something romantic sometimes.", None, 1.0, 1.0, 0.15, 0, None),        # 15
     ("H", "You're the one giving me advice!", "YOU'RE THE ONE GIVING ME ADVICE!", 1.05, 1.5, 0.15, 0, None),  # 16
     ("G", "Exactly! I'm teaching you how relationships work.", None, 1.05, 1.05, 0.9, 0, None),     # 17 -> stare
     ("H", "Fine. Professor, how do I deal with a boyfriend who doesn't listen, never plans dates, and always makes excuses?", None, 1.08, 1.1, 0.2, 0, None),  # 18
     ("G", "First, you need to identify the problem. Then, communicate your concerns calmly.", None, 1.0, 1.0, 0.2, 0, None),  # 19
     ("H", "The problem is you!", "The problem is YOU!", 1.0, 1.6, 1.2, 0, None),                    # 20 -> boom, silence
     ("G", "Okay... class dismissed.", "Okay… class dismissed.", 0.92, 1.0, 0.5, 0, None),           # 21 -> bell
     ("H", "Where are you going?!", "WHERE ARE YOU GOING?!", 1.05, 1.6, 0.1, 0, None),               # 22
     ("G", "To research another relationship strategy!", None, 1.12, 1.15, 0.0, 0, None)]            # 23
t = 0.0; buf = np.zeros(SR * 140, np.float32); segs = []
for i, (who, line, cap, sp, gain, pause, pre, fx) in enumerate(L):
    t += pre
    sp = min(1.3, sp * 1.12); pause = pause * 0.8 if pause < 0.6 else pause
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
