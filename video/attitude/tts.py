import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("H", "Babe, how was your day?", None, 1.05, 1.0, 0.2, 1.7, None),                 # 0
     ("G", "Fine.", None, 0.9, 0.9, 0.2, 0, None),                                       # 1
     ("H", "Just fine? Anything interesting happen?", None, 1.05, 1.0, 0.2, 0, None),    # 2
     ("G", "Nothing.", None, 0.9, 0.9, 0.2, 0, None),                                    # 3
     ("H", "Okay... I wanted to tell you something.", "Okay… I wanted to tell you something.", 1.0, 1.0, 0.2, 0, None),  # 4
     ("G", "Hmm.", None, 0.9, 0.9, 0.5, 0, None),                                        # 5
     ("H", "Never mind.", None, 0.95, 0.95, 0.2, 0, None),                               # 6
     ("G", "Okay.", None, 0.9, 0.9, 1.2, 0, None),                                       # 7 -> comedic silence, she picks up phone
     ("G", "Babe, have you seen my charger?", None, 1.0, 1.0, 0.15, 0, None),            # 8
     ("H", "No.", None, 0.9, 0.9, 0.2, 0, None),                                         # 9
     ("G", "Can you help me look for it?", None, 1.0, 1.0, 0.15, 0, None),               # 10
     ("H", "I'm busy.", None, 0.9, 0.9, 0.2, 0, None),                                   # 11
     ("G", "Busy doing what?", None, 1.0, 1.0, 0.15, 0, None),                           # 12
     ("H", "Nothing.", None, 0.9, 0.9, 0.2, 0, None),                                    # 13
     ("G", "So why can't you help?", None, 1.0, 1.0, 0.15, 0, None),                     # 14
     ("H", "Because I'm doing nothing.", None, 0.9, 0.9, 0.4, 0, None),                  # 15
     ("G", "Are you upset?", None, 1.0, 1.0, 0.15, 0, None),                             # 16
     ("H", "No.", None, 0.9, 0.9, 0.2, 0, None),                                         # 17
     ("G", "You sure?", None, 1.0, 1.0, 0.2, 0, None),                                   # 18
     ("H", "I'm fine.", None, 0.85, 0.9, 0.7, 0, None),                                  # 19 -> sting
     ("G", "Why are you behaving like this?", None, 1.05, 1.05, 0.15, 0, None),          # 20
     ("H", "Like what?", None, 0.95, 0.9, 0.15, 0, None),                                # 21
     ("G", "You're not listening to me!", None, 1.05, 1.15, 0.15, 0, None),              # 22
     ("H", "Hmm.", None, 0.9, 0.9, 0.2, 0, None),                                        # 23
     ("G", "And you're just giving me one-word answers!", None, 1.1, 1.2, 0.15, 0, None), # 24
     ("H", "Okay.", None, 0.9, 0.9, 0.2, 0, None),                                       # 25
     ("G", "Babe!", "BABE!", 1.0, 1.45, 0.15, 0, None),                                  # 26
     ("H", "What?", None, 0.95, 0.95, 0.15, 0, None),                                    # 27
     ("G", "Can you at least put your phone down when I'm talking?", None, 1.1, 1.2, 0.9, 0, None),  # 28 -> puts phone down
     ("H", "Sorry. Continue.", None, 0.92, 0.95, 0.15, 0, None),                         # 29
     ("G", "I've been trying to talk to you for five minutes!", None, 1.1, 1.25, 0.15, 0, None),  # 30
     ("H", "And?", None, 0.9, 0.95, 0.25, 0, None),                                      # 31
     ("G", "You're actually becoming annoying!", None, 1.05, 1.25, 0.25, 0, None),       # 32
     ("H", "Really? That's strange. I thought you liked this attitude.", None, 1.0, 1.0, 0.15, 0, None),  # 33
     ("G", "What do you mean?", None, 1.0, 1.0, 0.2, 0, None),                           # 34
     ("H", "I'm just treating you the way you treat me.", None, 0.95, 1.0, 1.3, 0, None),  # 35 -> scratch, silence
     ("G", "So... this is how I've been behaving?", "So… this is how I've been behaving?", 0.95, 1.0, 0.15, 0, None),  # 36
     ("H", "Exactly.", None, 0.95, 1.0, 0.2, 0, None),                                   # 37
     ("G", "Wow. I need to change.", None, 0.95, 1.0, 0.7, 0, None),                     # 38 -> she smiles
     ("G", "Starting tomorrow.", None, 0.9, 1.0, 1.0, 0, None),                          # 39 -> dramatic pause
     ("H", "Why tomorrow?!", "WHY TOMORROW?!", 1.0, 1.6, 0.15, 0, None),                 # 40
     ("G", "Because today, I'm still being myself!", None, 1.05, 1.05, 0.9, 0, None),    # 41 -> pillow
     ("G", "Babe! I'm working on it!", "BABE! I'M WORKING ON IT!", 1.1, 1.45, 0.0, 0, None)]  # 42
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
total = t + 1.4
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); print(" ".join(f"{s['i']}:{s['start']}" for s in segs))
