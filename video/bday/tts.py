import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
# (who, text, speed, gain, pause_after, pre)
L = [("H", "Happy birthday, babe!", 1.05, 1.0, 3.4, 1.0),                               # 0  -> he unpacks 3 items
     ("G", "Babe... why is it always boxers, singlet and belt?", 1.0, 1.0, 0.6, 0),    # 1
     ("H", "Boxers... so you're comfortable.", 1.0, 1.0, 0.3, 0),                     # 2
     ("H", "Singlet... so you stay cool.", 1.0, 1.0, 0.3, 0),                         # 3
     ("H", "And the belt...", 0.95, 1.0, 0.8, 0),                                      # 4
     ("H", "so your trousers don't fall when you're running after other girls.", 1.0, 1.0, 2.6, 0),  # 5
     ("G", "Happy birthday, babe!", 1.0, 1.0, 3.4, 1.6),                               # 6  -> she unpacks 3 items
     ("H", "Babe... what is this?", 1.0, 1.0, 0.6, 0),                                 # 7
     ("G", "Hair ties... so your hair stays out of your face.", 1.0, 1.0, 0.3, 0),    # 8
     ("G", "Slippers... so your feet are comfortable.", 1.0, 1.0, 0.3, 0),            # 9
     ("G", "And the toothbrush...", 0.95, 1.0, 0.8, 0),                                # 10
     ("G", "so your mouth stays fresh, for all the lies you tell your friends about my gifts.", 1.0, 1.0, 0.5, 0),  # 11
     ("H", "Excuse me?!", 1.1, 1.35, 0.6, 0),                                          # 12
     ("G", "Same energy, babe.", 0.95, 1.0, 0.0, 0)]                                   # 13
t = 0.0; buf = np.zeros(SR * 80, np.float32); segs = []
for i, (who, line, sp, gain, pause, pre) in enumerate(L):
    t += pre
    a, _ = k.create(line, voice=V[who], speed=sp, lang="en-us"); a = a * gain
    n0 = int(t * SR); buf[n0:n0 + len(a)] += a
    hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[j*hop:(j+1)*hop] ** 2))) for j in range(len(a) // hop)]
    segs.append(dict(i=i, who=who, text=line.replace("...", "…"), start=round(t, 3), end=round(t + len(a) / SR, 3), env=env))
    t += len(a) / SR + pause
p = np.percentile(np.concatenate([s["env"] for s in segs]), 95)
for s in segs: s["env"] = [round(min(1, e / p), 3) for e in s["env"]]
total = t + 2.8
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); [print(s["i"], s["who"], s["start"], s["end"], s["text"][:45]) for s in segs]
