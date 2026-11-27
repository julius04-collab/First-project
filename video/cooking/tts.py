import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("H", "Babe, I made something special for you today.", None, 1.0, 1.0, 0.15, 1.6, None),                # 0
     ("G", "Wow! It looks amazing.", None, 1.0, 1.05, 2.2, 0, None),                                       # 1 -> first bite
     ("H", "So... how is it?", "So… how is it?", 0.95, 1.0, 0.3, 0, None),                                # 2
     ("G", "It's... interesting.", "It's… interesting.", 0.88, 0.95, 0.2, 0, None),                        # 3
     ("H", "Interesting?", None, 0.95, 1.05, 0.15, 0, None),                                               # 4
     ("G", "Yeah. I've never experienced anything like it.", None, 0.95, 1.0, 0.2, 0, None),               # 5
     ("H", "Okay, rate it from one to ten.", "Okay, rate it from 1 to 10.", 1.0, 1.0, 1.1, 0, None),        # 6 -> he freezes
     ("G", "Do you want the honest answer, or the answer that keeps me alive?", None, 1.0, 1.0, 0.15, 0, None),  # 7
     ("H", "Daniel!", "DANIEL!", 1.0, 1.45, 0.15, 0, None),                                                # 8
     ("G", "Ten! Ten out of ten!", "10! 10 out of 10!", 1.1, 1.2, 0.15, 0, None),                          # 9
     ("H", "Really?", None, 1.0, 1.0, 0.15, 0, None),                                                      # 10
     ("G", "Absolutely. My taste buds are just... surprised.", "Absolutely. My taste buds are just… surprised.", 0.98, 1.0, 0.15, 0, None),  # 11
     ("H", "Surprised?", None, 0.95, 1.05, 0.15, 0, None),                                                 # 12
     ("G", "In a good way!", None, 1.05, 1.1, 1.8, 0, None),                                               # 13 -> she tastes
     ("H", "Oh my goodness. This is terrible!", "Oh my goodness. This is TERRIBLE!", 1.0, 1.35, 0.15, 0, None),  # 14
     ("G", "No, no! It's not that bad!", None, 1.1, 1.1, 0.15, 0, None),                                   # 15
     ("H", "Then why were you struggling to swallow?", None, 1.0, 1.05, 0.15, 0, None),                    # 16
     ("G", "I was appreciating it slowly.", None, 0.95, 1.0, 0.15, 0, None),                               # 17
     ("H", "And why did you give it ten?", "And why did you give it 10?", 1.0, 1.05, 0.15, 0, None),       # 18
     ("G", "Because I love you.", None, 0.95, 1.0, 0.2, 0, None),                                          # 19
     ("H", "So you lied?", None, 0.95, 1.1, 0.2, 0, None),                                                 # 20
     ("G", "I prefer the words, protected our relationship.", "I prefer the words \"protected our relationship.\"", 1.0, 1.0, 0.4, 0, None),  # 21
     ("H", "Fine. Since you love it so much, finish the whole plate.", None, 0.98, 1.05, 1.0, 0, None),   # 22 -> horror
     ("G", "Babe, love is patient. Love is kind. Love also knows when to stop eating.", None, 1.0, 1.0, 0.2, 0, None),  # 23
     ("H", "Finish it!", "FINISH IT!", 1.0, 1.5, 0.9, 0, None),                                            # 24 -> picks up spoon
     ("G", "If I don't survive this, tell my stomach I tried.", None, 0.92, 0.95, 0.0, 0, None)]           # 25
t = 0.0; buf = np.zeros(SR * 140, np.float32); segs = []
for i, (who, line, cap, sp, gain, pause, pre, fx) in enumerate(L):
    t += pre
    sp = min(1.3, sp * 1.08)
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
