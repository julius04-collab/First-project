import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("G", "Babe, what's your phone password?", None, 1.0, 1.0, 0.2, 1.0, None),                      # 0
     ("H", "Why?", None, 0.95, 1.0, 0.15, 0, None),                                                     # 1
     ("G", "Nothing. I just want to check something.", None, 1.0, 1.0, 0.15, 0, None),                  # 2
     ("H", "Check what?", None, 0.95, 1.0, 0.15, 0, None),                                              # 3
     ("G", "Relax! Are you hiding something from me?", None, 1.05, 1.05, 0.15, 0, None),                # 4
     ("H", "Are you hiding something from me?", "Are YOU hiding something from me?", 1.0, 1.1, 0.15, 0, None),  # 5
     ("G", "Me? Never! I'm an open book.", None, 1.0, 1.0, 0.5, 0, None),                               # 6
     ("H", "It's one, two, three, four.", "It's 1234.", 0.95, 1.0, 1.0, 0, None),                       # 7 -> unlocks
     ("G", "Hmm... what's this folder?", "Hmm… what's this folder?", 0.95, 1.0, 0.5, 0, None),          # 8 -> opens IMPORTANT
     ("G", "Screenshots? Why do you have so many screenshots of our conversations?", None, 1.05, 1.0, 0.15, 0, None),  # 9
     ("H", "Oh, those? Just memories.", None, 0.95, 1.0, 0.4, 0, None),                                 # 10
     ("G", "I'll send the money tomorrow.", "\"I'll send the money tomorrow.\"", 0.95, 1.0, 0.4, 0, None),  # 11
     ("G", "Baby, I'm five minutes away.", "\"Baby, I'm five minutes away.\"", 0.95, 1.0, 0.4, 0, None),    # 12
     ("G", "I didn't eat your food!", "\"I didn't eat your food!\"", 0.95, 1.0, 0.8, 0, None),          # 13 -> slowly turns
     ("G", "Why do you have evidence?!", "WHY DO YOU HAVE EVIDENCE?!", 1.0, 1.5, 0.4, 0, None),         # 14 -> scratch
     ("H", "I like keeping records.", None, 0.95, 1.0, 0.15, 0, None),                                  # 15
     ("G", "Records?! Am I under investigation?!", None, 1.05, 1.35, 0.5, 0, None),                     # 16 -> siren
     ("H", "No, baby. You're just very predictable.", None, 0.95, 1.0, 0.4, 0, None),                   # 17
     ("G", "Wait... what's this?", "Wait… what's this?", 0.95, 1.0, 0.6, 0, None),                      # 18
     ("G", "You actually have a list?!", None, 1.0, 1.3, 0.15, 0, None),                                # 19
     ("H", "Of course. I update it every week.", None, 0.95, 1.0, 0.4, 0, None),                        # 20 -> suspense
     ("G", "Every week?!", "EVERY WEEK?!", 1.0, 1.5, 0.15, 0, None),                                    # 21
     ("H", "Last update was yesterday. You said your network was bad, but you were online playing games.", None, 1.05, 1.05, 0.6, 0, None),  # 22 -> locks phone
     ("G", "Give me my phone!", None, 1.05, 1.2, 0.15, 0, None),                                        # 23
     ("H", "That's my phone.", None, 0.92, 1.0, 0.15, 0, None),                                         # 24
     ("G", "Exactly! And I think you should keep it private!", None, 1.05, 1.1, 0.15, 0, None),         # 25
     ("H", "But you wanted to check it.", None, 0.95, 1.0, 0.15, 0, None),                              # 26
     ("G", "I've seen enough. I respect your privacy now.", None, 1.0, 1.0, 0.2, 0, None),              # 27 -> retreat
     ("H", "Aww. What changed?", None, 0.95, 1.0, 0.15, 0, None),                                       # 28
     ("G", "I just discovered that I'm dating a detective!", None, 1.05, 1.1, 0.7, 0, None),            # 29 -> she unlocks again
     ("H", "Wait... you haven't seen the folder called, Things I Still Forgive Him For.", "Wait… you haven't seen the folder called \"Things I Still Forgive Him For.\"", 0.95, 1.0, 1.1, 0, None),  # 30 -> horror, freeze
     ("G", "Baby... let's not open that one.", "BABY… LET'S NOT OPEN THAT ONE.", 0.95, 1.1, 0.0, 0, None)]  # 31
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
total = t + 1.5
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); print(" ".join(f"{s['i']}:{s['start']}" for s in segs))
