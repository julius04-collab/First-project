import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("H", "Babe, something happened today.", None, 1.0, 1.0, 0.15, 1.1, None),                       # 0
     ("G", "What happened?", None, 0.95, 0.95, 0.15, 0, None),                                          # 1
     ("H", "A guy approached me and asked for my number.", None, 1.0, 1.0, 0.3, 0, None),               # 2
     ("G", "Oh, okay.", None, 0.88, 0.9, 1.0, 0, None),                                                 # 3 -> comedic silence
     ("H", "Oh, okay?!", "OH, OKAY?!", 1.0, 1.6, 0.4, 0, None),                                         # 4 -> scratch
     ("G", "What? Did you give him your number?", None, 1.0, 1.0, 0.15, 0, None),                       # 5
     ("H", "No!", None, 1.0, 1.2, 0.15, 0, None),                                                       # 6
     ("G", "Then what's the problem?", None, 0.95, 1.0, 0.7, 0, None),                                  # 7 -> stare
     ("H", "So you're not even jealous?", None, 1.0, 1.05, 0.15, 0, None),                              # 8
     ("G", "Should I be?", None, 0.95, 1.0, 0.15, 0, None),                                             # 9
     ("H", "Your girlfriend just told you another man asked for her number!", None, 1.1, 1.25, 0.15, 0, None),  # 10
     ("G", "And you rejected him, right?", None, 1.0, 1.0, 0.15, 0, None),                              # 11
     ("H", "Yes.", None, 0.95, 1.0, 0.15, 0, None),                                                     # 12
     ("G", "Then congratulations, baby. You passed the test.", None, 1.0, 1.0, 0.3, 0, None),           # 13 -> victory
     ("H", "What test?!", "WHAT TEST?!", 1.0, 1.5, 0.15, 0, None),                                      # 14
     ("G", "The loyalty test. You rejected him. Very good.", None, 1.0, 1.0, 0.4, 0, None),             # 15
     ("H", "What if I had given him my number?", None, 1.0, 1.0, 0.15, 0, None),                        # 16
     ("G", "Then I would have asked why.", None, 1.0, 1.0, 0.15, 0, None),                              # 17
     ("H", "And if I said he was handsome?", None, 1.0, 1.05, 0.15, 0, None),                           # 18
     ("G", "I'd ask if he has a job.", None, 0.95, 1.0, 0.15, 0, None),                                 # 19
     ("H", "Why?!", "WHY?!", 1.0, 1.4, 0.15, 0, None),                                                  # 20
     ("G", "Because if you're leaving me, at least make sure you're upgrading!", None, 1.0, 1.05, 0.7, 0, None),  # 21 -> boom
     ("H", "So you're already accepting that I could leave you?!", "SO YOU'RE ALREADY ACCEPTING THAT I COULD LEAVE YOU?!", 1.1, 1.5, 0.15, 0, None),  # 22
     ("G", "Baby, I'm just being realistic.", None, 0.95, 1.0, 0.3, 0, None),                           # 23
     ("H", "You know what? Maybe I should give him a chance!", None, 1.05, 1.2, 0.5, 0, None),          # 24 -> phone down
     ("G", "Wait. You said he asked for your number?", None, 0.98, 1.0, 0.15, 0, None),                 # 25
     ("H", "Yes!", None, 1.0, 1.2, 0.15, 0, None),                                                      # 26
     ("G", "Did he leave his number?", None, 0.92, 1.0, 0.6, 0, None),                                  # 27 -> sting
     ("H", "Why?", None, 1.0, 1.0, 0.15, 0, None),                                                      # 28
     ("G", "I need to ask him something.", None, 0.95, 1.0, 0.15, 0, None),                             # 29
     ("H", "Ask him what?!", "ASK HIM WHAT?!", 1.0, 1.5, 0.15, 0, None),                                # 30
     ("G", "I want to know how he had the confidence to approach you while I'm still your boyfriend!", None, 1.08, 1.15, 0.9, 0, None),  # 31 -> she holds back laugh
     ("H", "You're so annoying!", None, 1.0, 1.1, 0.15, 0, None),                                       # 32
     ("G", "See? Now you're jealous too!", None, 1.05, 1.05, 0.9, 0, None),                             # 33 -> pillow
     ("G", "Baby! I was just trying to network!", "BABY! I WAS JUST TRYING TO NETWORK!", 1.1, 1.45, 0.0, 0, None)]  # 34
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
