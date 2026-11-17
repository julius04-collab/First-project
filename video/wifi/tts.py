import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
# (who, spoken text, caption text, speed, gain, pause_after, pre_pause)
L = [("H", "Babe, what's the Wi-Fi password?", None, 1.05, 1.0, 0.5, 1.2),
     ("G", "Ask nicely.", None, 1.0, 1.0, 0.7, 0),
     ("H", "Ask nicely? Excuse me?", None, 1.08, 1.1, 0.5, 0),
     ("H", "Okay... My darling, my king, light of my life... can I please have the Wi-Fi password?", None, 0.95, 1.0, 0.6, 0),
     ("G", "Ask nicely.", None, 1.0, 1.0, 0.4, 0),
     ("H", "I just did! What is wrong with you?!", None, 1.15, 1.35, 0.3, 0),
     ("H", "So I cook for you, I iron your shirts, I listen to your boring football stories... and I have to beg for Wi-Fi in my own house?!", None, 1.15, 1.35, 1.6, 0),
     ("G", "Babe. The password... is, ask nicely. One word. All lowercase.", "Babe. The password… is \"asknicely\". One word. All lowercase.", 0.95, 1.0, 2.2, 0),
     ("H", "Oh.", "…Oh.", 0.9, 0.8, 0.9, 0),
     ("H", "Well... your face was rude.", None, 1.0, 1.0, 2.6, 0),
     ("G", "Babe, the Wi-Fi isn't working. Did you change the password?", None, 1.0, 1.0, 0.5, 0),
     ("H", "Say sorry.", None, 0.95, 1.0, 0.6, 0),
     ("G", "Sorry?", "…Sorry?", 0.95, 1.0, 0.5, 0),
     ("H", "No. Say sorry. One word.", "No. \"saysorry\". One word.", 0.95, 1.0, 0.0, 0)]
t = 0.0; buf = np.zeros(SR * 70, np.float32); segs = []
for i, (who, line, cap, sp, gain, pause, pre) in enumerate(L):
    t += pre
    a, _ = k.create(line, voice=V[who], speed=sp, lang="en-us")
    a = a * gain
    n0 = int(t * SR); buf[n0:n0 + len(a)] += a
    hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[j*hop:(j+1)*hop] ** 2))) for j in range(len(a) // hop)]
    segs.append(dict(i=i, who=who, text=(cap or line).replace("...", "…"), start=round(t, 3), end=round(t + len(a) / SR, 3), env=env))
    t += len(a) / SR + pause
p = np.percentile(np.concatenate([s["env"] for s in segs]), 95)
for s in segs: s["env"] = [round(min(1, e / p), 3) for e in s["env"]]
total = t + 2.8
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); [print(s["i"], s["who"], s["start"], s["end"], s["text"][:50]) for s in segs]
