import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella", "N": "am_fenrir"}
# (who, spoken, caption, speed, gain, pause_after, pre)
L = [("H", "You know what? I'm tired of this relationship!", None, 1.05, 1.2, 0.25, 0.6),        # 0
     ("G", "Baby, what did I do this time?", None, 1.0, 1.0, 0.2, 0),                           # 1
     ("H", "You never give me attention. You're always on your phone, watching football, or playing games!", None, 1.12, 1.15, 0.25, 0),  # 2
     ("G", "But I was watching football with you yesterday.", None, 1.0, 1.0, 0.2, 0),          # 3
     ("H", "I was sitting beside you while you watched football!", "I WAS SITTING BESIDE YOU WHILE YOU WATCHED FOOTBALL!", 1.12, 1.45, 0.25, 0),  # 4
     ("G", "Technically, we spent time together.", None, 0.98, 1.0, 1.1, 0),                     # 5 -> stare
     ("H", "You know what? I need space.", None, 0.95, 1.1, 1.0, 0),                             # 6 -> sting
     ("G", "Space?", None, 0.95, 1.0, 0.2, 0),                                                   # 7
     ("H", "Yes! Space!", "Yes! SPACE!", 1.0, 1.4, 0.3, 0),                                      # 8
     ("G", "Okay. No problem.", None, 1.0, 1.0, 0.5, 0),                                         # 9
     ("G", "How much space do you need?", None, 1.0, 1.0, 0.2, 0),                               # 10
     ("H", "What?", None, 1.0, 1.1, 0.2, 0),                                                     # 11
     ("G", "Like... two metres? Five metres?", "Like… 2 metres? 5 metres?", 0.98, 1.0, 0.2, 0),  # 12
     ("H", "Are you being serious right now?", None, 1.05, 1.1, 0.2, 0),                         # 13
     ("G", "I'm just trying to understand your requirements.", None, 1.0, 1.0, 0.8, 0),          # 14 -> grabs loveseat
     ("H", "What are you doing?!", "WHAT ARE YOU DOING?!", 1.05, 1.45, 0.2, 0),                  # 15
     ("G", "Creating space.", None, 0.95, 1.0, 2.6, 0),                                          # 16 -> drags, sits
     ("G", "Is this enough?", None, 1.0, 1.0, 1.1, 0),                                           # 17 -> she stares
     ("H", "You're actually unbelievable!", None, 1.05, 1.3, 0.4, 0),                            # 18
     ("G", "Wait! I have a better idea.", None, 1.05, 1.0, 0.3, 0),                              # 19
     ("H", "What are you doing now?", None, 1.0, 1.0, 0.2, 0),                                   # 20
     ("G", "Looking for apartments.", None, 0.95, 1.0, 0.3, 0),                                  # 21
     ("H", "Apartments?!", "APARTMENTS?!", 1.0, 1.45, 0.25, 0),                                  # 22
     ("G", "Yes. If you need more space, I can move out. That way, you'll have the entire house to yourself.", None, 1.02, 1.0, 0.2, 0),  # 23
     ("H", "You want to move out?!", "YOU WANT TO MOVE OUT?!", 1.05, 1.45, 0.2, 0),              # 24
     ("G", "I'm just respecting your boundaries, baby.", None, 0.98, 1.0, 0.25, 0),              # 25
     ("H", "I meant emotional space!", "I MEANT EMOTIONAL SPACE!", 1.0, 1.55, 1.1, 0),           # 26 -> scratch, freeze
     ("G", "Ohhh...", "Ohhh…", 0.85, 1.0, 0.8, 0),                                               # 27
     ("G", "So you don't need physical space?", None, 1.0, 1.0, 0.2, 0),                         # 28
     ("H", "No!", "NO!", 1.0, 1.5, 0.3, 0),                                                      # 29
     ("G", "Okay. That's easier. I'll cancel the apartment viewing.", None, 1.0, 1.0, 0.8, 0),   # 30
     ("H", "I just need you to give me some attention. Spend time with me. Make me feel loved.", None, 0.92, 1.0, 0.4, 0),  # 31
     ("G", "Okay, baby. I understand.", None, 0.95, 1.0, 3.0, 0),                                # 32 -> walks over, sits, arm
     ("G", "So... can I go back to watching football now?", "So… can I go back to watching football now?", 0.95, 1.0, 2.0, 0),  # 33 -> silence, slow turn
     ("H", "Get out!", "GET OUT!", 1.0, 1.7, 0.3, 0),                                             # 34
     ("G", "Wait! Is that emotional space or physical space?!", None, 1.1, 1.15, 1.3, 0),        # 35 -> pillow
     ("G", "Physical space! I understand!", "PHYSICAL SPACE! I UNDERSTAND!", 1.1, 1.5, 0.0, 0)]  # 36
t = 0.0; buf = np.zeros(SR * 120, np.float32); segs = []
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
total = t + 1.6
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); [print(s["i"], s["who"], s["start"], s["end"], s["text"][:50]) for s in segs]
