import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": ("am_michael", 1.0), "H": ("af_bella", 1.05)}
L = [("H", "Babe... my friend's boyfriend just bought her a new phone.", 0.5),
     ("G", "Mm-hmm.", 0.5),
     ("H", "And remember, I cooked for you last week. I even did your laundry!", 0.7),
     ("G", "So let me get this straight. Every good thing you did for me came from your heart...", 0.25),
     ("H", "Exactly!", 0.3),
     ("G", "But everything I do for you has to come from my bank app?", 0.3),
     ("H", "Babe,", 0.1),
     ("G", "No, no, no. Let's do heart to heart.", 1.3),
     ("H", "Okay. Heart to heart... So tonight, you cook.", 0.6),
     ("H", "And do my laundry.", 0.0)]
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
total = t + 3.2
sf.write(D + "/vo.wav", buf[:int(total * SR)], SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); [print(s["i"], s["who"], s["start"], s["end"], s["text"]) for s in segs]
