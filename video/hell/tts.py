import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": ("am_michael", 1.0), "H": ("af_bella", 1.05)}
L = [("H", "Babe... if you were on your way to heaven, and you saw me going to hell, what would you do?", 0.5),
     ("G", "Hmm... I don't get it.", 0.4),
     ("H", "Wouldn't you follow me?", 0.5),
     ("G", "Wait... you want me to follow you... to hell?", 0.5),
     ("H", "I thought you loved me! Have you forgotten? Ride or die! Forever and ever, till death do us part!", 0.7),
     ("G", "Babe... by the time we get there, death has already done us part.", 1.0),
     ("G", "Matter of fact... I don't even know you.", 0.8),
     ("H", "I'm breaking up with you.", 0.0)]
t = 1.2; buf = np.zeros(SR * 40, np.float32); segs = []
for i, (who, line, pause) in enumerate(L):
    v, sp = V[who]
    a, _ = k.create(line, voice=v, speed=sp, lang="en-us")
    n0 = int(t * SR); buf[n0:n0 + len(a)] += a
    hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[j*hop:(j+1)*hop] ** 2))) for j in range(len(a) // hop)]
    segs.append(dict(i=i, who=who, text=line.replace("...", "…"), start=round(t, 3), end=round(t + len(a) / SR, 3), env=env))
    t += len(a) / SR + pause
p = np.percentile(np.concatenate([s["env"] for s in segs]), 95)
for s in segs: s["env"] = [round(min(1, e / p), 3) for e in s["env"]]
total = t + 3.6
sf.write(D + "/vo.wav", buf[:int(total * SR)], SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); [print(s["i"], s["who"], s["start"], s["end"], s["text"]) for s in segs]
