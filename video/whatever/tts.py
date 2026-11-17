import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
# (who, spoken, caption, speed, gain, pause_after, pre)
L = [("G", "Babe, the boys are watching the match tonight. Can I go?", None, 1.05, 1.0, 0.5, 1.0),   # 0
     ("H", "Do whatever you want.", None, 0.95, 1.0, 0.5, 0),                                       # 1
     ("G", "Okay! Love you!", None, 1.1, 1.0, 5.6, 0),                                              # 2 -> leaves, twitch, 11:47 card, tiptoe, lamp
     ("H", "So... you really did whatever you wanted.", None, 0.95, 1.0, 0.4, 0),                  # 3
     ("G", "But you said...", "But you said—", 1.05, 1.0, 0.2, 0),                                  # 4
     ("H", "I said do whatever you want. I didn't mean, do whatever you want!", "I SAID \"do whatever you want.\" I didn't mean DO WHATEVER YOU WANT!", 1.1, 1.3, 0.6, 0),  # 5
     ("G", "Those are the same words.", "…Those are the same words.", 0.95, 1.0, 2.0, 0),          # 6 -> NEXT DAY card
     ("G", "Babe, I'm going to buy bread. Want anything?", None, 1.05, 1.0, 0.4, 0),               # 7
     ("H", "Do whatever you want.", None, 0.9, 1.0, 3.0, 0),                                        # 8 -> freeze, sweat, sits down
     ("G", "I'm actually not that hungry.", "…I'm actually not that hungry.", 0.95, 1.0, 0.0, 0)]  # 9
t = 0.0; buf = np.zeros(SR * 70, np.float32); segs = []
for i, (who, line, cap, sp, gain, pause, pre) in enumerate(L):
    t += pre
    a, _ = k.create(line, voice=V[who], speed=sp, lang="en-us"); a = a * gain
    n0 = int(t * SR); buf[n0:n0 + len(a)] += a
    hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[j*hop:(j+1)*hop] ** 2))) for j in range(len(a) // hop)]
    segs.append(dict(i=i, who=who, text=(cap or line).replace("...", "…"), start=round(t, 3), end=round(t + len(a) / SR, 3), env=env))
    t += len(a) / SR + pause
p = np.percentile(np.concatenate([s["env"] for s in segs]), 95)
for s in segs: s["env"] = [round(min(1, e / p), 3) for e in s["env"]]
total = t + 2.6
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); [print(s["i"], s["who"], s["start"], s["end"], s["text"][:50]) for s in segs]
