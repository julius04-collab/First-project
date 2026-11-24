import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("H", "Babe, can you send me some money? I need to get a few things.", None, 1.05, 1.0, 0.15, 1.6, None),  # 0
     ("G", "Baby, I'm broke. Things are really hard right now.", None, 0.95, 0.95, 0.15, 0, None),             # 1
     ("H", "You said that yesterday.", None, 1.0, 1.0, 0.15, 0, None),                                          # 2
     ("G", "And today, things are even harder.", None, 0.95, 0.95, 1.4, 0, None),                               # 3 -> jacket, notebook falls
     ("H", "What's this?", None, 1.0, 1.0, 0.15, 0, None),                                                      # 4
     ("G", "Nothing! Just my personal documents!", None, 1.15, 1.2, 0.5, 0, None),                              # 5
     ("H", "Wait a minute... secret savings, eight hundred and fifty thousand naira?!", "Wait a minute… \"Secret savings: ₦850,000\"?!", 1.0, 1.3, 0.6, 0, None),  # 6 -> sting, zoom, scratch
     ("G", "Baby! That's not what it looks like!", "BABY! THAT'S NOT WHAT IT LOOKS LIKE!", 1.15, 1.35, 0.15, 0, None),  # 7
     ("H", "So you have eight hundred and fifty thousand, but you can't give me five thousand?", "So you have ₦850,000, but you can't give me ₦5,000?", 1.1, 1.15, 0.15, 0, None),  # 8
     ("G", "That's my emergency money!", None, 1.05, 1.05, 0.15, 0, None),                                      # 9
     ("H", "And what emergency are you preparing for?", None, 1.0, 1.0, 0.25, 0, None),                         # 10
     ("G", "You!", "YOU!", 1.0, 1.2, 1.3, 0, None),                                                             # 11 -> boom, silence, she turns
     ("G", "I mean... emergencies in general!", "I MEAN… emergencies in general!", 1.15, 1.25, 0.25, 0, None),   # 12
     ("H", "So when I asked you for money last week, you were saving?", None, 1.08, 1.05, 0.15, 0, None),       # 13
     ("G", "Exactly! Financial discipline.", None, 1.0, 1.0, 0.2, 0, None),                                     # 14
     ("H", "When I asked you to buy me a birthday gift?", None, 1.08, 1.05, 0.15, 0, None),                     # 15
     ("G", "Financial discipline.", None, 0.95, 1.0, 0.2, 0, None),                                             # 16
     ("H", "When I needed money for transport?", None, 1.08, 1.1, 0.15, 0, None),                               # 17
     ("G", "Baby, you have to respect the process!", None, 1.05, 1.0, 0.15, 0, None),                           # 18
     ("H", "What process?!", "WHAT PROCESS?!", 1.0, 1.55, 0.15, 0, None),                                       # 19
     ("G", "The process of becoming financially stable!", None, 1.05, 1.05, 0.15, 0, None),                     # 20
     ("H", "You're becoming financially stable, while I'm becoming financially stranded?!", None, 1.08, 1.35, 0.5, 0, None),  # 21 -> impact
     ("H", "Transfer one hundred thousand naira to me, right now.", "Transfer ₦100,000 to me right now.", 1.0, 1.05, 0.15, 0, None),  # 22
     ("G", "Hundred thousand?!", "HUNDRED THOUSAND?!", 1.0, 1.5, 0.15, 0, None),                                # 23
     ("H", "Yes. I want to celebrate your financial discipline.", None, 1.0, 1.0, 0.15, 0, None),               # 24
     ("G", "But that's my savings!", None, 1.05, 1.1, 0.15, 0, None),                                           # 25
     ("H", "And I'm your emergency, remember?", None, 0.95, 1.0, 1.1, 0, None),                                 # 26 -> opens banking app
     ("G", "Maybe I should have kept this money in cash...", "Maybe I should have kept this money in cash…", 0.95, 0.9, 0.15, 0, None),  # 27
     ("H", "Why?", None, 1.0, 1.0, 0.2, 0, None),                                                               # 28
     ("G", "At least cash doesn't ask questions!", None, 1.05, 1.1, 0.9, 0, None),                              # 29 -> pillow
     ("G", "Baby! My financial future!", "BABY! MY FINANCIAL FUTURE!", 1.1, 1.45, 0.0, 0, None)]                # 30
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
