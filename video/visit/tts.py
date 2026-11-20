import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella", "T": "bf_emma"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
# (who, spoken, caption, speed, gain, pause_after, pre, fx)
L = [("T", "Step one. Move your left foot to the side...", "Step one. Move your left foot to the side…", 1.0, 0.9, 0.3, 0.6, "phone"),   # 0
     ("G", "Left foot... right foot... easy!", "Left foot… right foot… easy!", 1.0, 1.0, 1.4, 0, None),                # 1 -> slip
     ("G", "What kind of complicated nonsense is this?", None, 1.05, 1.0, 1.2, 0, None),                                # 2 -> ringtone
     ("G", "Hello, baby!", None, 1.05, 1.0, 0.15, 0, None),                                                             # 3
     ("H", "Hey! What are you doing?", None, 1.05, 1.0, 0.15, 0, "phone"),                                              # 4
     ("G", "Nothing. Just relaxing.", None, 1.0, 1.0, 0.15, 0, None),                                                   # 5
     ("H", "Okay, baby. I miss you.", None, 1.0, 1.0, 0.15, 0, "phone"),                                                # 6
     ("G", "I miss you too.", None, 1.0, 1.0, 0.15, 0, None),                                                           # 7
     ("H", "Good. See you later!", None, 1.05, 1.0, 0.15, 0, "phone"),                                                  # 8
     ("G", "Wait, what do you mean?", None, 1.05, 1.0, 0.6, 0, None),                                                   # 9 -> hang up beep
     ("G", "See me later? What does that mean?", None, 1.0, 1.0, 1.0, 0, None),                                         # 10 -> doorbell
     ("G", "Who is that?!", "WHO IS THAT?!", 1.05, 1.4, 0.4, 0, None),                                                  # 11
     ("H", "Baby! Open the door!", None, 1.05, 1.2, 0.2, 0, "muffled"),                                                 # 12
     ("G", "Oh no!", "OH NO!", 1.0, 1.6, 0.3, 0, None),                                                                 # 13
     ("G", "The dance moves! The music! Everything!", None, 1.15, 1.25, 3.6, 0, None),                                  # 14 -> hide montage, door
     ("H", "Surprise!", "SURPRISE!", 1.0, 1.4, 0.3, 0, None),                                                           # 15
     ("G", "Baby! What a... wonderful surprise!", "BABY! What a… wonderful surprise!", 1.0, 1.1, 0.25, 0, None),        # 16
     ("H", "You don't look happy to see me.", None, 1.0, 1.0, 0.2, 0, None),                                            # 17
     ("G", "What? I'm very happy! I'm just... surprised.", "What? I'm VERY happy! I'm just… surprised.", 1.05, 1.1, 0.2, 0, None),  # 18
     ("H", "Well, I told you I missed you.", None, 1.0, 1.0, 0.2, 0, None),                                             # 19
     ("G", "Yes, but I thought you meant emotionally!", None, 1.05, 1.0, 1.9, 0, None),                                 # 20 -> she scans
     ("H", "Why is the room looking so strange?", None, 0.95, 1.0, 0.2, 0, None),                                       # 21
     ("G", "Strange? No, baby. This is how I normally arrange my furniture.", None, 1.05, 1.0, 0.25, 0, None),          # 22
     ("H", "Why is there a scarf covering your phone?", None, 1.0, 1.0, 0.4, 0, None),                                  # 23
     ("G", "It's cold.", None, 0.85, 1.0, 0.5, 0, None),                                                                # 24
     ("H", "Your phone is cold?!", "YOUR PHONE IS COLD?!", 1.0, 1.4, 0.25, 0, None),                                    # 25
     ("G", "You know how technology works.", None, 0.95, 1.0, 0.7, 0, None),                                            # 26 -> she grabs it
     ("G", "Baby, wait!", "BABY, WAIT!", 1.1, 1.5, 1.7, 0, None),                                                       # 27 -> reveal
     ("H", "What exactly is this?", None, 0.95, 1.0, 0.9, 0, None),                                                     # 28 -> freeze
     ("G", "I can explain.", None, 0.9, 1.0, 0.3, 0, None),                                                             # 29
     ("H", "You've been learning how to dance?", None, 1.0, 1.0, 0.2, 0, None),                                         # 30
     ("G", "Yes...", "Yes…", 0.85, 0.9, 0.25, 0, None),                                                                 # 31
     ("H", "Why?", None, 1.0, 1.0, 0.25, 0, None),                                                                      # 32
     ("G", "Our anniversary is next week. I wanted to surprise you with a romantic dance.", None, 0.98, 1.0, 1.1, 0, None),  # 33 -> she softens
     ("H", "Awww, baby! That's actually so sweet!", None, 1.0, 1.05, 0.2, 0, None),                                     # 34
     ("G", "Really?", None, 1.0, 1.0, 0.2, 0, None),                                                                    # 35
     ("H", "Yes! Show me what you've learnt!", None, 1.05, 1.1, 0.25, 0, None),                                         # 36
     ("G", "Now?", None, 0.95, 1.0, 0.2, 0, None),                                                                      # 37
     ("H", "Yes! Now!", "YES! NOW!", 1.0, 1.4, 5.0, 0, None),                                                           # 38 -> the dance
     ("H", "Babe!", "BABE!", 1.0, 1.3, 0.2, 0, None),                                                                   # 39
     ("G", "What?!", None, 1.0, 1.0, 0.25, 0, None),                                                                    # 40
     ("H", "I think you should surprise me with dinner instead.", None, 1.0, 1.0, 0.3, 0, None),                        # 41
     ("G", "That's actually why I was hiding.", None, 0.95, 1.0, 0.3, 0, None),                                         # 42
     ("H", "What?", None, 1.0, 1.0, 0.4, 0, None),                                                                      # 43
     ("G", "I burnt the food.", None, 0.88, 1.0, 1.6, 0, None),                                                         # 44 -> stare, alarm
     ("H", "You burnt the food too?!", "YOU BURNT THE FOOD TOO?!", 1.0, 1.9, 0.5, 0, None),                             # 45
     ("G", "Baby, can we just celebrate next year?", None, 0.95, 1.0, 0.0, 0, None)]                                    # 46
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
total = t + 1.4
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); print(" ".join(f"{s['i']}:{s['start']}" for s in segs))
