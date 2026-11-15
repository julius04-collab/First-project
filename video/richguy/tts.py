import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
L = [("So let me get this straight.", 0.7),
     ("I pretended to be broke.", 0.6),
     ("I asked you out, you said yes...", 0.35),
     ("and we fell in love.", 0.8),
     ("Now you find out I'm actually rich...", 0.35),
     ("and you're the one who's angry, and wants to break up?", 0.9),
     ("So what do you want me to do? Go back to being broke?", 0.7),
     ("What does that even change?", 1.1),
     ("I'm confused.", 0.0)]
t = 2.9; buf = np.zeros(SR * 31, np.float32); segs = []
for i, (line, pause) in enumerate(L):
    a, _ = k.create(line, voice="am_michael", speed=1.0 if i < 8 else 0.9, lang="en-us")
    n0 = int(t * SR); buf[n0:n0 + len(a)] += a
    hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[j*hop:(j+1)*hop] ** 2))) for j in range(len(a) // hop)]
    segs.append(dict(i=i, text=line.replace("...", "…"), start=round(t, 3), end=round(t + len(a) / SR, 3), env=env))
    t += len(a) / SR + pause
p = np.percentile(np.concatenate([s["env"] for s in segs]), 95)
for s in segs: s["env"] = [round(min(1, e / p), 3) for e in s["env"]]
sf.write(D + "/vo.wav", buf[:SR * 30], SR)
json.dump(segs, open(D + "/vo.json", "w"))
print("speech ends", round(t, 2)); [print(s["i"], s["start"], s["end"], s["text"]) for s in segs]
