import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
L = [("H", "Babe, would you still love me if I gained fifty kilos?", 1.12, 1.0, 0.2, 0.4),   # 0
     ("G", "Yes.", 1.0, 1.0, 0.3, 0),                                                     # 1
     ("H", "What if I lost all my hair?", 1.1, 1.0, 0.25, 0),                             # 2
     ("G", "Yes.", 1.0, 1.0, 0.3, 0),                                                     # 3
     ("H", "What if I snored like a generator?", 1.1, 1.0, 0.25, 0),                      # 4
     ("G", "You already do. Yes.", 1.0, 1.0, 0.5, 0),                                     # 5
     ("H", "Okay... what if I turned into a worm?", 1.0, 1.0, 0.9, 0),                    # 6
     ("G", "I'd buy you a nice little box. With air holes.", 0.95, 1.0, 0.3, 0),          # 7
     ("H", "Awww, babe!", 1.0, 1.1, 0.6, 0),                                              # 8
     ("G", "My turn. Would you still love me if I lost my job?", 1.0, 1.0, 2.2, 0),       # 9
     ("H", "Babe, it's late. Let's sleep.", 1.15, 1.0, 0.8, 0),                           # 10
     ("G", "Babe?", 0.9, 0.9, 0.0, 0)]                                                    # 11
t = 0.0; buf = np.zeros(SR * 40, np.float32); segs = []
for i, (who, line, sp, gain, pause, pre) in enumerate(L):
    t += pre
    a, _ = k.create(line, voice=V[who], speed=sp, lang="en-us"); a = a * gain
    n0 = int(t * SR); buf[n0:n0 + len(a)] += a
    hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[j*hop:(j+1)*hop] ** 2))) for j in range(len(a) // hop)]
    cap = {7: "…I'd buy you a nice little box. With air holes.", 11: "…Babe?"}.get(i, line.replace("...", "…"))
    segs.append(dict(i=i, who=who, text=cap, start=round(t, 3), end=round(t + len(a) / SR, 3), env=env))
    t += len(a) / SR + pause
p = np.percentile(np.concatenate([s["env"] for s in segs]), 95)
for s in segs: s["env"] = [round(min(1, e / p), 3) for e in s["env"]]
total = max(30.0, t + 1.6)
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("speech end", round(t, 2), "total", round(total, 2)); [print(s["i"], s["who"], s["start"], s["end"], s["text"]) for s in segs]
