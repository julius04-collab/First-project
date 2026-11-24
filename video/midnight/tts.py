import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("H", "Babe... who just texted you?", "Babe… who just texted you?", 0.92, 0.9, 0.2, 2.6, None),   # 0 (ding, one eye opens)
     ("G", "Nobody.", None, 0.95, 0.9, 0.2, 0, None),                                                    # 1
     ("H", "Nobody has a name?", None, 1.0, 1.0, 0.2, 0, None),                                          # 2
     ("G", "It's probably a notification.", None, 1.0, 1.0, 1.0, 0, None),                               # 3 -> ding 2
     ("H", "A notification that says, I miss you?!", "A notification that says \"I miss you\"?!", 1.0, 1.35, 0.2, 0, None),  # 4
     ("G", "Oh... that's just somebody.", "Oh… that's just somebody.", 1.0, 1.0, 0.2, 0, None),         # 5
     ("H", "Somebody?!", "SOMEBODY?!", 1.0, 1.45, 0.15, 0, None),                                        # 6
     ("G", "Baby, relax. It's an old friend.", None, 1.05, 1.0, 0.15, 0, None),                          # 7
     ("H", "An old friend who misses you at midnight?", None, 1.05, 1.0, 0.15, 0, None),                 # 8
     ("G", "Yeah. You know how people get emotional at night.", None, 1.05, 1.0, 0.15, 0, None),         # 9
     ("H", "Who is it?", None, 1.0, 1.0, 0.15, 0, None),                                                 # 10
     ("G", "Just a girl I used to know.", None, 1.0, 1.0, 1.0, 0, None),                                 # 11 -> scratch, she sits up
     ("H", "A girl?!", "A GIRL?!", 1.0, 1.6, 0.2, 0, None),                                              # 12
     ("G", "Technically, yes.", None, 0.95, 1.0, 0.2, 0, None),                                          # 13
     ("H", "So you have a female friend texting you, I miss you, at midnight?", "So you have a female friend texting you \"I miss you\" at midnight?", 1.1, 1.1, 0.15, 0, None),  # 14
     ("G", "Baby, nothing is happening!", None, 1.1, 1.1, 0.15, 0, None),                                # 15
     ("H", "Then why are you hiding your phone?", None, 1.05, 1.1, 0.15, 0, None),                       # 16
     ("G", "I'm not hiding it! I'm protecting our peace.", None, 1.1, 1.0, 0.2, 0, None),                # 17
     ("H", "Give me the phone!", "GIVE ME THE PHONE!", 1.0, 1.6, 1.0, 0, None),                          # 18 -> hands it over
     ("H", "I miss you so much. I can't stop thinking about you.", "\"I miss you so much. I can't stop thinking about you.\"", 0.95, 1.0, 0.4, 0, None),  # 19
     ("H", "Explain!", "EXPLAIN!", 1.0, 1.5, 1.7, 0, None),                                              # 20 -> zoom on contact, his face
     ("G", "Baby... that's my ex!", "Baby… that's my ex!", 0.95, 1.0, 1.3, 0, None),                    # 21 -> 1s silence
     ("H", "Your ex?!", "YOUR EX?!", 1.0, 1.7, 0.15, 0, None),                                           # 22
     ("G", "But we're just friends now!", None, 1.1, 1.1, 0.15, 0, None),                                # 23
     ("H", "Why is your ex missing you at midnight?!", "WHY IS YOUR EX MISSING YOU AT MIDNIGHT?!", 1.05, 1.5, 0.15, 0, None),  # 24
     ("G", "Maybe she hasn't moved on!", None, 1.1, 1.1, 0.8, 0, None),                                  # 25 -> pillow
     ("G", "Baby! I didn't say I missed her!", "BABY! I DIDN'T SAY I MISSED HER!", 1.1, 1.4, 0.3, 0, None),  # 26
     ("G", "I should have turned off my notifications!", "I SHOULD HAVE TURNED OFF MY NOTIFICATIONS!", 1.15, 1.4, 0.0, 0, None)]  # 27
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
total = t + 0.9
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); print(" ".join(f"{s['i']}:{s['start']}" for s in segs))
