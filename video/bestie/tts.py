import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella", "E": "af_sky"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("H", "Babe, who are you texting?", None, 1.0, 1.0, 0.15, 1.0, None),                                  # 0
     ("G", "My best friend.", None, 0.95, 1.0, 0.15, 0, None),                                              # 1
     ("H", "Oh, I didn't know you had a best friend.", None, 1.0, 1.0, 0.15, 0, None),                      # 2
     ("G", "Yeah. She's a girl.", None, 0.95, 1.0, 0.9, 0, None),                                           # 3 slow head turn
     ("H", "A girl?", None, 0.92, 1.05, 0.2, 0, None),                                                      # 4
     ("G", "Yes. We've been friends for years.", None, 1.0, 1.0, 0.15, 0, None),                           # 5
     ("H", "Interesting. I'd love to meet her.", None, 0.95, 1.0, 0.6, 0, None),                           # 6 his smile drops
     ("G", "Meet her? Why?", None, 1.0, 1.05, 0.15, 0, None),                                               # 7
     ("H", "Because she's your best friend. I should know her, right?", None, 1.0, 1.0, 0.15, 0, None),     # 8
     ("G", "Of course! But she's... very busy.", "Of course! But she's… very busy.", 1.0, 1.0, 0.15, 0, None),  # 9
     ("H", "Then let's invite her for dinner.", None, 1.0, 1.0, 0.15, 0, None),                             # 10
     ("G", "She's actually travelling.", None, 1.0, 1.0, 0.15, 0, None),                                    # 11
     ("H", "Where?", None, 0.95, 1.0, 0.15, 0, None),                                                       # 12
     ("G", "Somewhere far.", None, 0.95, 1.0, 0.25, 0, None),                                               # 13
     ("H", "Daniel, you just said she's texting you.", None, 1.0, 1.05, 0.6, 0, None),                      # 14 locks phone
     ("G", "Technology is amazing. You can text people from anywhere.", None, 1.05, 1.0, 2.8, 0, None),     # 15 -> card, Emily walks in
     ("G", "Sophia, this is Emily. My female best friend.", None, 1.0, 1.0, 0.2, 0, None),                 # 16
     ("E", "Finally! You're the girlfriend!", None, 1.05, 1.1, 0.2, 0, None),                               # 17
     ("H", "Yes. And you're the famous best friend.", None, 0.95, 1.0, 0.2, 0, None),                       # 18
     ("E", "Famous? What has he told you about me?", None, 1.05, 1.0, 0.15, 0, None),                       # 19
     ("H", "That you're very close.", None, 0.95, 1.0, 0.2, 0, None),                                       # 20
     ("E", "Oh, we're extremely close. I know all his secrets.", None, 1.0, 1.05, 0.3, 0, None),            # 21
     ("G", "Emily, maybe we don't need to discuss everything.", None, 1.05, 1.0, 0.15, 0, None),            # 22
     ("E", "Remember when he cried because his favourite cartoon character died?", None, 1.05, 1.05, 0.2, 0, None),  # 23
     ("H", "What?!", "WHAT?!", 1.0, 1.5, 0.2, 0, None),                                                     # 24
     ("E", "And he still sleeps with that old teddy bear!", None, 1.05, 1.1, 0.15, 0, None),                # 25
     ("H", "Daniel?!", "DANIEL?!", 1.0, 1.4, 0.15, 0, None),                                                # 26
     ("G", "I was a child!", None, 1.05, 1.2, 0.2, 0, None),                                                # 27
     ("E", "Last week, he called me because he couldn't decide which shirt to wear.", None, 1.05, 1.0, 0.15, 0, None),  # 28
     ("H", "You called another woman to help you dress?!", None, 1.05, 1.35, 0.15, 0, None),               # 29
     ("G", "She's my best friend!", None, 1.05, 1.15, 0.9, 0, None),                                        # 30 look exchange
     ("E", "Girl, we need to talk.", None, 0.95, 1.0, 0.3, 0, None),                                        # 31
     ("G", "Wait... why are you two teaming up?", "Wait… why are you two teaming up?", 1.0, 1.05, 0.6, 0, None),  # 32
     ("H", "Because apparently, we're both your best friends now.", None, 0.95, 1.0, 0.8, 0, None),         # 33
     ("G", "I think I need new friends.", None, 0.9, 0.95, 0.0, 0, None)]                                   # 34
t = 0.0; buf = np.zeros(SR * 140, np.float32); segs = []
for i, (who, line, cap, sp, gain, pause, pre, fx) in enumerate(L):
    t += pre
    sp = min(1.3, sp * 1.08)
    a, _ = k.create(line, voice=V[who], speed=sp, lang="en-us")
    nz = np.where(np.abs(a) > 0.01)[0]
    if len(nz): a = a[max(0, nz[0] - 600): nz[-1] + 1200]
    if fx == "phone":
        a = band(a, 350, 3200) * 1.6; a = np.tanh(a * 1.5) / 1.5
    elif fx == "muffled":
        a = band(a, 80, 900) * 1.5
    a = a * gain
    n0 = int(t * SR); buf[n0:n0 + len(a)] += a
    hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[j*hop:(j+1)*hop] ** 2))) for j in range(len(a) // hop)]
    segs.append(dict(i=i, who=who, fx=fx, text=(cap or line).replace("...", "…"), start=round(t, 3), end=round(t + len(a) / SR, 3), env=env))
    t += len(a) / SR + pause
p = np.percentile(np.concatenate([s["env"] for s in segs]), 95)
for s in segs: s["env"] = [round(min(1, e / p), 3) for e in s["env"]]
total = t + 1.8
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); print(" ".join(f"{s['i']}:{s['start']}" for s in segs))
