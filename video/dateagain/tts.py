import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("H", "Babe, can I ask you something?", None, 1.0, 1.0, 0.15, 1.2, None),                                   # 0
     ("G", "Sure, baby.", None, 0.95, 1.0, 0.15, 0, None),                                                         # 1
     ("H", "If you could go back in time and meet me again, would you still choose me?", None, 1.0, 1.0, 0.2, 0, None),  # 2
     ("G", "Of course!", None, 1.0, 1.1, 0.2, 0, None),                                                            # 3 sparkle
     ("H", "Aww. Really?", None, 1.0, 1.0, 0.15, 0, None),                                                         # 4
     ("G", "Absolutely. Without hesitation.", None, 1.0, 1.0, 0.2, 0, None),                                       # 5
     ("H", "That's so sweet. Why?", None, 1.0, 1.0, 0.3, 0, None),                                                 # 6
     ("G", "Well... now I know what I'm getting myself into.", "Well… now I know what I'm getting myself into.", 0.95, 1.0, 1.0, 0, None),  # 7 scratch
     ("H", "What does that mean?", None, 0.95, 1.0, 0.15, 0, None),                                                # 8
     ("G", "Nothing bad! I just mean I already know your personality.", None, 1.05, 1.0, 0.15, 0, None),           # 9
     ("H", "So you wouldn't choose me if you didn't know me?", None, 1.05, 1.05, 0.15, 0, None),                   # 10
     ("G", "No, no! I'd still choose you.", None, 1.05, 1.05, 0.15, 0, None),                                      # 11
     ("H", "But you just said you know what you're getting yourself into!", None, 1.05, 1.2, 0.15, 0, None),       # 12
     ("G", "Exactly! That's why I'm choosing you with full information.", None, 1.0, 1.0, 0.6, 0, None),           # 13 she folds arms
     ("H", "So you're saying dating me is a risk?", None, 1.0, 1.05, 0.15, 0, None),                               # 14
     ("G", "Every relationship is a risk, baby.", None, 1.0, 1.0, 0.15, 0, None),                                  # 15
     ("H", "And I'm a risk?", None, 0.95, 1.1, 0.2, 0, None),                                                      # 16
     ("G", "A very beautiful risk.", None, 0.95, 1.0, 0.3, 0, None),                                               # 17
     ("H", "Wow. So what would you do differently if we met again?", None, 1.0, 1.0, 0.15, 0, None),               # 18
     ("G", "I'd probably ask for your number earlier.", None, 1.0, 1.0, 0.15, 0, None),                            # 19
     ("H", "Aww!", None, 1.0, 1.0, 0.2, 0, None),                                                                  # 20
     ("G", "Before you had time to notice my red flags.", None, 0.95, 1.0, 1.2, 0, None),                          # 21 silence
     ("H", "Your red flags?!", "YOUR RED FLAGS?!", 1.0, 1.6, 0.3, 0, None),                                        # 22 boom
     ("G", "Baby, I'm joking!", None, 1.1, 1.15, 0.15, 0, None),                                                   # 23
     ("H", "So you admit you have red flags?", None, 1.0, 1.1, 0.15, 0, None),                                     # 24
     ("G", "Everybody has red flags!", None, 1.05, 1.1, 0.15, 0, None),                                            # 25
     ("H", "Name one of yours.", None, 0.95, 1.0, 0.2, 0, None),                                                   # 26
     ("G", "I talk too much sometimes.", None, 1.0, 1.0, 0.15, 0, None),                                           # 27
     ("H", "That's your biggest problem?", None, 1.0, 1.05, 0.2, 0, None),                                         # 28
     ("G", "No. My biggest problem is answering your questions honestly.", None, 0.98, 1.0, 0.7, 0, None),         # 29 scratch, pillow
     ("G", "Wait! You asked for honesty!", "WAIT! YOU ASKED FOR HONESTY!", 1.1, 1.4, 0.25, 0, None),               # 30
     ("G", "Next time, I'm saying yes and keeping quiet!", "NEXT TIME, I'M SAYING YES AND KEEPING QUIET!", 1.12, 1.4, 0.0, 0, None)]  # 31
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
