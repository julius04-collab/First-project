import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("H", "Babe, let me ask you something.", None, 1.05, 1.0, 0.15, 1.7, None),                       # 0 (she sits)
     ("G", "Hmm?", None, 1.0, 1.0, 0.15, 0, None),                                                      # 1
     ("H", "Describe your perfect woman.", None, 1.0, 1.0, 0.4, 0, None),                               # 2
     ("G", "My perfect woman?", None, 1.0, 1.0, 0.15, 0, None),                                         # 3
     ("H", "Yes. Don't think too much. Just describe her.", None, 1.1, 1.0, 0.15, 0, None),             # 4
     ("G", "Okay... she's beautiful, intelligent, caring and understanding.", "Okay… she's beautiful, intelligent, caring and understanding.", 1.05, 1.0, 0.15, 0, None),  # 5
     ("H", "Aww. Anything else?", None, 1.05, 1.0, 0.15, 0, None),                                      # 6
     ("G", "Yeah. She doesn't complain too much,", None, 1.1, 1.0, 0.35, 0, None),                      # 7 -> scratch
     ("G", "she gives me space, supports my dreams, and doesn't disturb me when I'm watching football.", None, 1.15, 1.0, 0.6, 0, None),  # 8 -> smile drops, sting
     ("H", "Doesn't complain?", None, 0.95, 1.0, 0.15, 0, None),                                        # 9
     ("G", "Yes, you know... peaceful woman.", "Yes, you know… peaceful woman.", 1.05, 1.0, 0.15, 0, None),  # 10
     ("H", "So you want a woman who doesn't talk?", None, 1.05, 1.1, 0.15, 0, None),                    # 11
     ("G", "No, baby! I want a woman who knows when to talk.", None, 1.1, 1.0, 0.15, 0, None),          # 12
     ("H", "And who decides that?", None, 1.0, 1.0, 0.15, 0, None),                                     # 13
     ("G", "Definitely not me!", None, 1.1, 1.1, 0.05, 0, None),                                        # 14
     ("G", "Heh... heh.", "Heh… heh…", 0.9, 0.8, 0.4, 0, None),                                         # 15 nervous laugh
     ("H", "So... am I your perfect woman?", "So… am I your perfect woman?", 0.98, 1.0, 1.2, 0, None),  # 16 -> heartbeat hesitation
     ("G", "Of course, baby!", None, 1.05, 1.0, 0.15, 0, None),                                         # 17
     ("H", "Then why did you take so long to answer?", None, 1.1, 1.1, 0.15, 0, None),                  # 18
     ("G", "I was trying to remember all your qualities!", None, 1.1, 1.0, 0.15, 0, None),              # 19
     ("H", "And what are they?", None, 1.0, 1.0, 0.15, 0, None),                                        # 20
     ("G", "You're beautiful, caring, intelligent...", "You're beautiful, caring, intelligent…", 1.0, 1.0, 0.25, 0, None),  # 21
     ("H", "Go on.", None, 0.95, 1.0, 0.5, 0, None),                                                    # 22
     ("G", "And... very good at asking questions.", "And… very good at asking questions.", 1.0, 1.0, 0.4, 0, None),  # 23
     ("H", "So I'm not your perfect woman?", "So I'm NOT your perfect woman?", 1.05, 1.2, 0.15, 0, None),  # 24
     ("G", "You are! You're my perfect woman!", None, 1.1, 1.1, 0.15, 0, None),                         # 25
     ("H", "Then describe me in one word.", None, 1.0, 1.0, 0.9, 0, None),                              # 26 -> thinks
     ("G", "Dangerous.", None, 0.85, 1.0, 1.3, 0, None),                                                # 27 -> 1s silence
     ("H", "What?!", "WHAT?!", 1.0, 1.7, 0.2, 0, None),                                                 # 28
     ("G", "I mean... dangerously beautiful!", "I MEAN… DANGEROUSLY BEAUTIFUL!", 1.1, 1.35, 0.9, 0, None),  # 29 -> pillow chase
     ("G", "Baby! You said one word!", "BABY! YOU SAID ONE WORD!", 1.1, 1.45, 0.0, 0, None)]           # 30
t = 0.0; buf = np.zeros(SR * 140, np.float32); segs = []
for i, (who, line, cap, sp, gain, pause, pre, fx) in enumerate(L):
    t += pre
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
total = t + 1.0
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); print(" ".join(f"{s['i']}:{s['start']}" for s in segs))
