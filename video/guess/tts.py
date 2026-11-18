import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella", "N": "am_fenrir"}
# (who, spoken, caption, speed, gain, pause_after, pre)
L = [("N", "He guessed wrong three times.", None, 1.18, 1.0, 0.1, 0.25),                       # 0 hook
     ("N", "And the real answer? Nobody saw it coming.", None, 1.2, 1.0, 0.75, 0),           # 1 -> rewind
     ("N", "It's a quiet Sunday. Then she goes silent.", None, 1.2, 1.0, 0.15, 0),           # 2
     ("G", "Babe, what's wrong?", None, 1.1, 1.0, 0.15, 0),                                  # 3
     ("H", "Nothing.", None, 1.0, 1.0, 0.15, 0),                                             # 4
     ("N", "Rule number one. Nothing, is never nothing.", "Rule number one: \"nothing\" is NEVER nothing.", 1.2, 1.0, 0.15, 0),  # 5
     ("H", "If you loved me, you'd know what's wrong.", "If you loved me, you'd KNOW what's wrong.", 1.05, 1.15, 0.2, 0),        # 6
     ("N", "So he starts guessing.", None, 1.2, 1.0, 0.1, 0),                                # 7
     ("G", "You're hungry?", None, 1.1, 1.0, 0.1, 0),                                        # 8
     ("H", "No.", None, 1.0, 1.0, 0.35, 0),                                                  # 9
     ("G", "Your mum called?", None, 1.1, 1.0, 0.1, 0),                                      # 10
     ("H", "No.", None, 1.0, 1.0, 0.35, 0),                                                  # 11
     ("G", "I left the toilet seat up?", None, 1.1, 1.0, 0.1, 0),                            # 12
     ("H", "No!", "NO!", 1.0, 1.4, 0.4, 0),                                                  # 13
     ("N", "Brother thinks... he's running out of options.", None, 1.2, 1.0, 0.15, 0),       # 14
     ("G", "Okay, I give up. Just tell me.", None, 1.1, 1.0, 0.15, 0),                       # 15
     ("N", "Then she drops the bomb.", None, 1.2, 1.0, 0.15, 0),                             # 16
     ("H", "You liked a girl's picture... in twenty nineteen.", "You liked a girl's picture… in 2019.", 1.0, 1.0, 1.9, 0),  # 17 -> silence
     ("G", "How do you even remember that?", "…How do you even REMEMBER that?", 1.0, 1.0, 0.3, 0),  # 18
     ("N", "Guys... she remembers everything.", None, 1.15, 1.0, 0.0, 0)]                     # 19
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
total = t + 2.4
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); [print(s["i"], s["who"], s["start"], s["end"], s["text"][:50]) for s in segs]
