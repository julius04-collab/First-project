import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella", "N": "am_fenrir"}
# (who, spoken, caption, speed, gain, pause_after, pre)
L = [("N", "She asked him to be honest.", None, 1.15, 1.0, 0.1, 0.25),                          # 0 hook
     ("N", "Big mistake. He actually was.", None, 1.15, 1.0, 0.75, 0),                         # 1 -> rewind
     ("H", "Babe?", None, 1.0, 1.0, 0.2, 0),                                                   # 2
     ("G", "Hmm?", None, 1.0, 1.0, 0.2, 0),                                                    # 3
     ("H", "Do you think I'm beautiful?", None, 1.0, 1.0, 0.2, 0),                             # 4
     ("G", "Of course, baby.", None, 1.05, 1.0, 0.2, 0),                                        # 5
     ("H", "No, I mean... really beautiful?", None, 1.0, 1.0, 0.2, 0),                          # 6
     ("G", "Yes, obviously.", None, 1.05, 1.0, 0.2, 0),                                         # 7
     ("H", "Be honest. Don't just say it because I'm your girlfriend.", None, 1.05, 1.0, 0.3, 0),  # 8
     ("G", "You want me to be completely honest?", None, 1.0, 1.0, 0.2, 0),                     # 9
     ("H", "Yes, baby. I can handle the truth.", None, 1.0, 1.0, 0.5, 0),                       # 10
     ("G", "Okay...", "Okay…", 0.9, 1.0, 0.5, 0),                                               # 11
     ("G", "I mean, you're beautiful... but not like those Instagram models.", None, 1.0, 1.0, 2.4, 0),  # 12 -> scratch, freeze, slow turn
     ("H", "Excuse me?", None, 0.9, 1.0, 0.2, 0),                                               # 13
     ("G", "No, no! I mean... you're beautiful in your own way!", None, 1.15, 1.1, 0.2, 0),     # 14
     ("H", "In my own way?", "In my OWN way?", 0.95, 1.1, 0.2, 0),                              # 15
     ("G", "Yes! Like... naturally beautiful!", None, 1.1, 1.1, 0.2, 0),                        # 16
     ("H", "So I'm not normally beautiful?", None, 1.0, 1.1, 0.2, 0),                           # 17
     ("G", "What?! That's not what I said!", "WHAT?! That's not what I said!", 1.15, 1.3, 0.3, 0),  # 18
     ("H", "So who exactly are these Instagram models you're comparing me to?", None, 1.05, 1.1, 0.2, 0),  # 19
     ("G", "Nobody! I don't even know them!", None, 1.2, 1.2, 0.3, 0),                          # 20
     ("N", "And now... the interrogation.", None, 1.1, 1.0, 0.2, 0),                           # 21
     ("H", "Okay. Let me ask you something.", None, 1.0, 1.0, 0.15, 0),                         # 22
     ("G", "Baby, please...", "Baby, please…", 1.0, 1.0, 0.15, 0),                              # 23
     ("H", "If you saw me and one of those Instagram girls standing together, who would you choose?", None, 1.1, 1.0, 0.15, 0),  # 24
     ("G", "You!", "YOU!", 1.1, 1.4, 0.35, 0),                                                  # 25
     ("H", "Why did you hesitate?", None, 0.95, 1.0, 0.2, 0),                                   # 26
     ("G", "I was breathing!", "I WAS BREATHING!", 1.1, 1.5, 0.25, 0),                          # 27
     ("H", "So now breathing is an excuse?", None, 1.0, 1.1, 0.2, 0),                           # 28
     ("G", "Jesus Christ...", "Jesus Christ…", 0.95, 1.0, 0.15, 0),                             # 29
     ("H", "Don't bring Jesus into this conversation!", None, 1.1, 1.35, 1.5, 0),               # 30 -> fourth wall look
     ("H", "Fine. Since I'm not beautiful enough, let me call my ex.", None, 1.0, 1.0, 0.2, 0),  # 31
     ("G", "Your ex?!", "YOUR EX?!", 1.0, 1.5, 0.25, 0),                                        # 32
     ("H", "At least he always told me I was the most beautiful woman in the world.", None, 1.05, 1.0, 0.2, 0),  # 33
     ("G", "Then why did you break up with him?", None, 1.05, 1.0, 0.2, 0),                     # 34
     ("H", "Because he was a liar!", None, 1.05, 1.3, 1.2, 0),                                  # 35 -> slow nod
     ("G", "Ohhh... so that's why you asked me to be honest.", "Ohhh… so THAT'S why you asked me to be honest.", 0.95, 1.0, 0.25, 0),  # 36
     ("H", "What did you just say?!", "WHAT DID YOU JUST SAY?!", 1.05, 1.6, 0.2, 0),             # 37
     ("G", "Nothing, baby! You're the most beautiful woman in the universe!", None, 1.2, 1.2, 0.2, 0),  # 38
     ("H", "Too late!", "TOO LATE!", 1.0, 1.4, 1.6, 0),                                         # 39 -> walks out
     ("G", "Next time... I'm dating someone who asks if the food is ready.", "Next time… I'm dating someone who asks if the FOOD is ready.", 0.95, 0.9, 0.0, 0)]  # 40
t = 0.0; buf = np.zeros(SR * 120, np.float32); segs = []
for i, (who, line, cap, sp, gain, pause, pre) in enumerate(L):
    t += pre
    a, _ = k.create(line, voice=V[who], speed=sp, lang="en-us"); a = a * gain
    # trim leading/trailing silence for tighter pacing
    nz = np.where(np.abs(a) > 0.01)[0]
    if len(nz): a = a[max(0, nz[0] - 600): nz[-1] + 1200]
    n0 = int(t * SR); buf[n0:n0 + len(a)] += a
    hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[j*hop:(j+1)*hop] ** 2))) for j in range(len(a) // hop)]
    segs.append(dict(i=i, who=who, text=(cap or line).replace("...", "…"), start=round(t, 3), end=round(t + len(a) / SR, 3), env=env))
    t += len(a) / SR + pause
p = np.percentile(np.concatenate([s["env"] for s in segs]), 95)
for s in segs: s["env"] = [round(min(1, e / p), 3) for e in s["env"]]
total = t + 2.2
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); [print(s["i"], s["who"], s["start"], s["end"], s["text"][:50]) for s in segs]
