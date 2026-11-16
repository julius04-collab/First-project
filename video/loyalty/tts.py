import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"D": ("am_michael", 1.0), "H": ("af_bella", 1.05), "F": ("am_adam", 1.0)}
L = [("H", "Babe... there's a lady trending these days. I think her name is Mia Khalifa?", 0.4, 1.8),
     ("D", "Who's Mia Khalifa?", 0.6, 0),
     ("H", "She's a jewelry designer.", 0.4, 0),
     ("D", "Babe, I'm not into jewelry. I don't know any jewelry designers.", 0.5, 0),
     ("H", "Are you serious? You don't know Mia Khalifa?", 0.4, 0),
     ("D", "No. Show me her picture.", 1.4, 0),
     ("H", "Girl! Dave doesn't know Mia Khalifa! I told you, he's not into all that rubbish!", 1.6, 0),
     ("F", "Bro... God saved you. I was sure I'd be helping you pack your stuff tonight. And I'm tired.", 0.9, 0),
     ("D", "You don't trust me?", 0.7, 0),
     ("D", "Bro... I've been training for this moment for years.", 0.0, 0)]
t = 0.0; buf = np.zeros(SR * 45, np.float32); segs = []
for i, (who, line, pause, pre) in enumerate(L):
    t += pre
    v, sp = V[who]
    a, _ = k.create(line, voice=v, speed=sp, lang="en-us")
    n0 = int(t * SR); buf[n0:n0 + len(a)] += a
    hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[j*hop:(j+1)*hop] ** 2))) for j in range(len(a) // hop)]
    segs.append(dict(i=i, who=who, text=line.replace("...", "…"), start=round(t, 3), end=round(t + len(a) / SR, 3), env=env))
    t += len(a) / SR + pause
p = np.percentile(np.concatenate([s["env"] for s in segs]), 95)
for s in segs: s["env"] = [round(min(1, e / p), 3) for e in s["env"]]
total = t + 3.0
sf.write(D + "/vo.wav", buf[:int(total * SR)], SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); [print(s["i"], s["who"], s["start"], s["end"], s["text"]) for s in segs]
