import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella", "N": "am_fenrir"}
# (who, spoken, caption, speed, gain, pause_after, pre)
L = [("N", "She yelled for five minutes straight.", None, 1.18, 1.0, 0.1, 0.25),                 # 0 hook
     ("N", "He heard about ten seconds of it.", None, 1.18, 1.0, 0.75, 0),                       # 1 -> rewind
     ("H", "So you're telling me you forgot what today is?", None, 1.05, 1.0, 0.2, 0),           # 2
     ("G", "Baby, what did I do?", None, 1.05, 1.0, 0.15, 0),                                    # 3
     ("H", "What did you do?! You came home yesterday, ate my food, watched football, and didn't even ask how my day went!", "What did you DO?! You came home yesterday, ate my food, watched football, and didn't even ask how my day went!", 1.15, 1.15, 0.2, 0),  # 4
     ("G", "But I asked if you wanted chicken.", None, 1.0, 1.0, 0.15, 0),                       # 5
     ("H", "That's not the point!", "THAT'S NOT THE POINT!", 1.05, 1.4, 0.3, 0),                 # 6
     ("N", "And then... she started pacing.", None, 1.18, 1.0, 0.1, 0),                         # 7
     ("H", "You never listen to me! Every time I talk, you're either on your phone, watching football, or doing something else!", None, 1.15, 1.1, 0.2, 0),  # 8
     ("G", "Okay baby. I'm listening.", "Okay, baby. I'm listening.", 1.0, 1.0, 0.15, 0),        # 9
     ("H", "Really? Then tell me what I just said.", None, 1.05, 1.0, 0.25, 0),                 # 10
     ("G", "You said... something about chicken?", None, 0.95, 1.0, 0.2, 0),                    # 11
     ("H", "Are you serious right now?!", "ARE YOU SERIOUS RIGHT NOW?!", 1.05, 1.4, 0.3, 0),    # 12
     ("N", "Brother is fighting for his life... against his own eyelids.", None, 1.18, 1.0, 0.15, 0),  # 13
     ("H", "And another thing! Last week, I told you I wanted us to spend more quality time together...", None, 1.1, 1.0, 0.2, 0),  # 14
     ("H", "And you know what? I think we need to talk about our relationship, because...", "And you know what? I think we need to talk about our relationship, because—", 1.1, 1.0, 0.9, 0),  # 15
     ("H", "Babe?", None, 1.0, 1.0, 1.4, 0),                                                     # 16 -> snore
     ("H", "BABE!", None, 1.0, 1.6, 0.1, 0),                                                     # 17
     ("G", "Huh?! What?! I'm sorry! I was listening!", "Huh?! WHAT?! I'm sorry! I was listening!", 1.15, 1.2, 0.3, 0),  # 18
     ("H", "You were sleeping?!", None, 1.0, 1.2, 0.2, 0),                                       # 19
     ("G", "No baby. I was just closing my eyes to concentrate.", "No, baby. I was just closing my eyes to concentrate.", 1.0, 1.0, 0.2, 0),  # 20
     ("H", "For five minutes?!", "For FIVE MINUTES?!", 1.0, 1.35, 0.3, 0),                       # 21
     ("G", "Well... you said you wanted me to listen. So I was listening in my dreams too.", None, 0.98, 1.0, 1.5, 0),  # 22 -> stare
     ("H", "Get out!", "GET OUT!", 1.0, 1.6, 0.6, 0),                                             # 23
     ("G", "Can I at least finish my dream?", None, 0.95, 1.0, 0.0, 0)]                           # 24
t = 0.0; buf = np.zeros(SR * 80, np.float32); segs = []
for i, (who, line, cap, sp, gain, pause, pre) in enumerate(L):
    t += pre
    a, _ = k.create(line, voice=V[who], speed=sp, lang="en-us"); a = a * gain
    # trim leading/trailing silence for tighter pacing
    nz = np.where(np.abs(a) > 0.01)[0]
    if len(nz): a = a[max(0, nz[0] - 600): nz[-1] + 1200]
    n0 = int(t * SR); buf[n0:n0 + len(a)] += a
    hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[j*hop:(j+1)*hop] ** 2))) for j in range(len(a) // hop)]
    segs.append(dict(i=i, who=who, text=(cap or line).replace("...", "…"), start=round(t, 3), end=round(t + len(a) / SR, 3), env=env))
    t += len(a) / SR + pause
p = np.percentile(np.concatenate([s["env"] for s in segs]), 95)
for s in segs: s["env"] = [round(min(1, e / p), 3) for e in s["env"]]
total = t + 3.0
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); [print(s["i"], s["who"], s["start"], s["end"], s["text"][:50]) for s in segs]
