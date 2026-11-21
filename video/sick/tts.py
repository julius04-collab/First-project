import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella", "F": "am_adam", "K": "am_puck"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("H", "Babe, are you ready? Our date starts in thirty minutes!", "Babe, are you ready? Our date starts in 30 minutes!", 1.1, 1.0, 0.75, 1.5, "phone"),  # 0 (ringtone before)
     ("G", "Baby... I don't think I can make it.", "Baby… I don't think I can make it.", 0.88, 0.85, 0.2, 0, None),   # 1 (cough before)
     ("H", "Why? What's wrong?", None, 1.1, 1.0, 0.15, 0, "phone"),                                                    # 2
     ("G", "I'm seriously sick. My whole body is weak. I can barely move.", None, 0.92, 0.85, 0.2, 0, None),           # 3
     ("H", "Oh no! Should I come over?", None, 1.1, 1.0, 0.1, 0, "phone"),                                             # 4
     ("G", "No!", "NO!", 1.0, 1.5, 0.15, 0, None),                                                                     # 5
     ("G", "I mean... you don't want to catch it.", "I mean… you don't want to catch it.", 0.95, 0.85, 0.15, 0, None), # 6
     ("H", "Okay, baby. Get some rest. I'll check on you later.", None, 1.1, 1.0, 0.7, 0, "phone"),                    # 7 -> hang up, jump
     ("G", "Yes! Football time!", "YES! FOOTBALL TIME!", 1.1, 1.4, 1.3, 0, None),                                      # 8 -> transition to field
     ("F", "Bro! I thought you were sick!", None, 1.1, 1.1, 0.1, 0, None),                                             # 9
     ("G", "I was! But football is good for recovery!", None, 1.1, 1.1, 0.1, 0, None),                                 # 10
     ("K", "Ha ha! You're crazy, bro!", None, 1.1, 1.1, 2.3, 0, None),                                                 # 11 -> pass, shot, goal
     ("G", "Goooal! Who's sick now?!", "GOOOOAL! WHO'S SICK NOW?!", 1.05, 1.5, 0.3, 0, None),                          # 12
     ("H", "You, apparently!", "YOU, APPARENTLY!", 1.0, 1.5, 1.0, 0, None),                                            # 13 -> scratch, freeze
     ("G", "Baby?!", "BABY?!", 1.0, 1.4, 0.15, 0, None),                                                               # 14
     ("H", "So this is what your hospital looks like?", None, 1.0, 1.0, 0.15, 0, None),                                # 15
     ("G", "I can explain!", None, 1.1, 1.1, 0.1, 0, None),                                                            # 16
     ("H", "You said you could barely move!", None, 1.1, 1.15, 0.1, 0, None),                                          # 17
     ("G", "I was... recovering!", "I was… recovering!", 1.0, 1.0, 0.1, 0, None),                                      # 18
     ("H", "By playing football?!", "BY PLAYING FOOTBALL?!", 1.05, 1.45, 0.1, 0, None),                                # 19
     ("G", "Doctor's orders!", None, 1.05, 1.1, 0.25, 0, None),                                                        # 20
     ("F", "Bro, which doctor?", None, 0.95, 0.55, 0.9, 0, None),                                                      # 21 whisper -> angry look
     ("H", "Fine! Since you're strong enough to play football, you're strong enough to pay for dinner!", None, 1.12, 1.15, 0.15, 0, None),  # 22
     ("G", "Wait... what?", "Wait… what?", 1.0, 1.0, 0.15, 0, None),                                                   # 23
     ("H", "And you're buying dessert too!", None, 1.1, 1.1, 0.25, 0, None),                                           # 24
     ("G", "I should have stayed sick.", None, 0.95, 0.5, 0.2, 0, None),                                               # 25 quietly
     ("H", "What did you say?!", "WHAT DID YOU SAY?!", 1.05, 1.5, 0.15, 0, None),                                      # 26
     ("G", "I said I'm still sick, baby!", "I SAID I'M STILL SICK, BABY!", 1.1, 1.3, 0.05, 0, None),                   # 27
     ("F", "Ha ha ha ha ha!", None, 1.0, 1.0, -1.0, 0, None),                                                          # 28 laugh (overlaps next)
     ("K", "Ha ha ha ha ha ha!", None, 1.05, 0.9, 0.0, 0, None)]                                                       # 29
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
total = t + 0.8
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); print(" ".join(f"{s['i']}:{s['start']}" for s in segs))
