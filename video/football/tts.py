import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella", "C": "bm_george"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("H", "Babe, we need to talk.", None, 1.0, 1.0, 0.15, 1.8, None),                                          # 0
     ("G", "Can it wait until halftime?", None, 1.0, 1.0, 0.15, 0, None),                                       # 1
     ("H", "No.", None, 0.95, 1.1, 0.2, 0, None),                                                               # 2
     ("G", "Okay... what's wrong?", "Okay… what's wrong?", 0.95, 1.0, 0.15, 0, None),                           # 3
     ("H", "I'm tired of competing with football for your attention.", None, 1.0, 1.05, 0.15, 0, None),         # 4
     ("G", "Competing? Baby, you're in completely different leagues!", None, 1.05, 1.05, 0.5, 0, None),          # 5 scratch
     ("H", "So choose. Me, or football?", "So CHOOSE. Me or football?", 0.95, 1.15, 0.9, 0, None),               # 6 whistle, snacks down
     ("G", "Can I ask a question first?", None, 0.95, 1.0, 0.15, 0, None),                                      # 7
     ("H", "What question?", None, 1.0, 1.0, 0.15, 0, None),                                                    # 8
     ("G", "Are we talking about football forever, or just today's match?", None, 1.05, 1.0, 0.15, 0, None),    # 9
     ("H", "Forever!", "FOREVER!", 1.0, 1.5, 0.2, 0, None),                                                     # 10
     ("G", "Wow. That's a very long contract.", None, 0.95, 1.0, 0.15, 0, None),                                # 11
     ("H", "Daniel!", "DANIEL!", 1.0, 1.45, 0.15, 0, None),                                                     # 12
     ("G", "Okay, okay! What if I choose you, but football becomes my hobby?", None, 1.1, 1.05, 0.15, 0, None),  # 13
     ("H", "No!", None, 1.0, 1.2, 0.15, 0, None),                                                               # 14
     ("G", "What if I watch only the highlights?", None, 1.05, 1.0, 0.15, 0, None),                             # 15
     ("H", "No!", "NO!", 1.0, 1.4, 0.15, 0, None),                                                              # 16
     ("G", "What if I watch without sound?", None, 1.05, 1.0, 0.15, 0, None),                                   # 17
     ("H", "You're not listening!", "YOU'RE NOT LISTENING!", 1.0, 1.55, 0.2, 0, None),                          # 18
     ("G", "Exactly! Without sound!", None, 1.05, 1.1, 0.6, 0, None),                                           # 19
     ("H", "So you can't live without football?", None, 1.0, 1.05, 0.15, 0, None),                              # 20
     ("G", "Of course I can!", None, 1.05, 1.05, 0.15, 0, None),                                                # 21
     ("H", "Then turn it off.", None, 0.92, 1.0, 1.0, 0, None),                                                 # 22 looks TV / her
     ("G", "Baby, I have a better solution.", None, 1.0, 1.0, 0.15, 0, None),                                   # 23
     ("H", "I'm listening.", None, 0.95, 1.0, 0.15, 0, None),                                                   # 24
     ("G", "We can watch football together!", None, 1.05, 1.15, 0.3, 0, None),                                  # 25 victory
     ("H", "I don't even like football!", None, 1.05, 1.15, 0.15, 0, None),                                     # 26
     ("G", "That's okay. You can support my team.", None, 1.0, 1.0, 0.15, 0, None),                             # 27
     ("H", "And if your team loses?", None, 1.0, 1.0, 0.15, 0, None),                                           # 28
     ("G", "Then you comfort me.", None, 0.95, 1.0, 0.15, 0, None),                                             # 29
     ("H", "And if they win?", None, 1.0, 1.0, 0.15, 0, None),                                                  # 30
     ("G", "Then we celebrate!", None, 1.05, 1.1, 0.15, 0, None),                                               # 31
     ("H", "So where do I fit into all this?!", None, 1.05, 1.3, 0.5, 0, None),                                 # 32
     ("G", "Wait! I've got it! I choose you...", "Wait! I've got it! I choose you…", 1.0, 1.1, 0.9, 0, None),   # 33 boom, she smiles
     ("G", "And football!", "…and FOOTBALL!", 1.0, 1.2, 0.4, 0, None),                                          # 34 scratch
     ("H", "You can't choose both!", "YOU CAN'T CHOOSE BOTH!", 1.0, 1.55, 0.15, 0, None),                       # 35
     ("G", "Why not? You're my love, and football is my passion.", None, 1.0, 1.0, 0.15, 0, None),              # 36
     ("H", "So what am I supposed to do?", None, 1.0, 1.1, 0.2, 0, None),                                       # 37
     ("G", "Become the referee!", None, 1.05, 1.1, 0.7, 0, None),                                               # 38 pillow
     ("G", "Red card! Red card! Baby, that's a red card!", "RED CARD! RED CARD! BABY, THAT'S A RED CARD!", 1.15, 1.4, 0.3, 0, None),  # 39
     ("C", "And it's a goal!", "AND IT'S A GOAL!", 1.1, 1.4, 0.3, 0, "phone"),                                  # 40 commentator
     ("G", "Wait! Who scored?!", "WAIT! WHO SCORED?!", 1.1, 1.3, 0.0, 0, None)]                                 # 41
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
total = t + 1.6
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); print(" ".join(f"{s['i']}:{s['start']}" for s in segs))
