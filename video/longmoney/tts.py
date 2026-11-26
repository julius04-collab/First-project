import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
def band(a, lo, hi):
    F = np.fft.rfft(a); f = np.fft.rfftfreq(len(a), 1 / SR); F[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(F, len(a)).astype(np.float32)
L = [("G", "Finally! Eight thousand dollars!", "Finally! $8,000!", 1.0, 1.15, 2.2, 1.4, None),                  # 0 hook
     ("G", "Oh no... this is bad. I'm officially broke.", "Oh no… this is bad. I'm officially broke.", 0.95, 1.0, 0.25, 2.8, None),  # 1 S1
     ("H", "Babe, did you remember the money we were supposed to put aside for our weekend trip?", None, 1.05, 1.0, 0.25, 0, None),  # 2
     ("G", "Weekend trip?", None, 0.95, 1.0, 0.25, 0, None),                                                         # 3
     ("H", "Yes. We agreed to save a little every week.", None, 1.0, 1.0, 0.2, 0, None),                             # 4
     ("G", "Oh... right. About that. Things are really tight this month.", "Oh… right. About that. Things are really tight this month.", 0.95, 1.0, 0.25, 0, None),  # 5
     ("H", "Again?", None, 0.95, 1.05, 0.25, 0, None),                                                               # 6
     ("G", "Baby, money doesn't grow on trees.", None, 1.0, 1.0, 0.25, 0, None),                                     # 7
     ("H", "I know. But somehow, you always have money when your friends invite you out.", None, 1.05, 1.0, 0.25, 0, None),  # 8
     ("G", "That's different. Friendship is an investment.", None, 1.0, 1.0, 0.25, 0, None),                         # 9
     ("H", "And what am I?", None, 0.95, 1.0, 0.25, 0, None),                                                        # 10
     ("G", "You're a long-term investment.", None, 1.0, 1.0, 0.6, 0, None),                                          # 11
     ("H", "You better hope your investment doesn't withdraw.", None, 0.95, 1.05, 1.4, 0, None),                     # 12
     ("G", "Finally! Eight thousand dollars!", "Finally! $8,000!", 1.0, 1.15, 0.9, 3.2, None),                       # 13 S2 (card + ding before)
     ("H", "What was that?", None, 1.0, 1.0, 0.2, 0, None),                                                          # 14
     ("G", "Nothing.", None, 0.95, 1.0, 0.25, 0, None),                                                              # 15
     ("H", "You looked very happy for someone who was broke five minutes ago.", None, 1.0, 1.0, 0.25, 0, None),      # 16
     ("G", "It was just a funny video.", None, 1.0, 1.0, 0.2, 0, None),                                              # 17
     ("H", "Let me see.", None, 1.0, 1.0, 0.2, 0, None),                                                             # 18
     ("G", "See what?", None, 1.0, 1.0, 0.2, 0, None),                                                               # 19
     ("H", "The funny video.", None, 1.0, 1.0, 0.25, 0, None),                                                       # 20
     ("G", "It disappeared.", None, 0.95, 1.0, 0.25, 0, None),                                                       # 21
     ("H", "Videos don't disappear that quickly, Daniel.", None, 1.0, 1.0, 0.3, 0, None),                            # 22
     ("G", "This one was very shy.", None, 0.95, 1.0, 1.4, 0, None),                                                 # 23
     ("H", "What's this?", None, 0.95, 1.0, 0.9, 3.6, None),                                                         # 24 S3 (card, jacket, envelope)
     ("H", "Eight thousand dollars?!", "$8,000?!", 1.0, 1.4, 0.5, 0, None),                                          # 25
     ("H", "Daniel?!", "DANIEL?!", 1.0, 1.4, 1.1, 0, None),                                                          # 26 -> he walks in
     ("G", "Good morning, beautiful!", None, 1.0, 1.0, 0.2, 0, None),                                                # 27
     ("H", "Good morning, Mister Eight Thousand Dollars!", "GOOD MORNING, MR. $8,000!", 1.0, 1.45, 0.9, 0, None),    # 28 -> tray wobble
     ("G", "What?", None, 0.95, 1.0, 0.2, 0, None),                                                                  # 29
     ("H", "You have eight thousand dollars saved?!", "You have $8,000 saved?!", 1.05, 1.3, 0.2, 0, None),           # 30
     ("G", "Where did you get that?!", None, 1.05, 1.15, 0.2, 0, None),                                              # 31
     ("H", "Your jacket confessed.", None, 0.95, 1.0, 0.3, 0, None),                                                 # 32
     ("G", "I knew I shouldn't have trusted that jacket!", None, 1.05, 1.1, 0.25, 0, None),                          # 33
     ("H", "So you've been telling me you're broke, while sitting on eight thousand dollars?", "So you've been telling me you're broke while sitting on $8,000?", 1.05, 1.15, 0.25, 0, None),  # 34
     ("G", "Technically, I'm not sitting on it. It's in a savings account.", None, 1.0, 1.0, 0.3, 0, None),          # 35
     ("H", "Daniel!", "DANIEL!", 1.0, 1.55, 1.0, 0, None),                                                           # 36
     ("H", "So when I asked you to contribute to our trip, you said you had nothing?", None, 1.05, 1.05, 0.25, 0, None),  # 37 S4
     ("G", "That money is not for spending.", None, 1.0, 1.0, 0.25, 0, None),                                        # 38
     ("H", "And when I needed help buying groceries?", None, 1.05, 1.05, 0.25, 0, None),                             # 39
     ("G", "I was protecting my financial future.", None, 1.0, 1.0, 0.25, 0, None),                                  # 40
     ("H", "What about when you bought those expensive headphones?", None, 1.05, 1.05, 0.25, 0, None),               # 41
     ("G", "Those were necessary.", None, 0.95, 1.0, 0.25, 0, None),                                                 # 42
     ("H", "Necessary for what? Listening to your empty bank account?", None, 1.05, 1.15, 0.3, 0, None),             # 43
     ("G", "First of all, they're noise-cancelling headphones.", None, 1.0, 1.0, 0.25, 0, None),                     # 44
     ("H", "Clearly. Because you can't hear me asking where all your money is!", None, 1.05, 1.25, 0.3, 0, None),    # 45
     ("G", "Sophia, you don't understand. I've been saving for months.", None, 1.0, 1.05, 0.25, 0, None),            # 46
     ("H", "Then why didn't you tell me?", None, 1.0, 1.1, 0.25, 0, None),                                           # 47
     ("G", "Because every time I save something, there's always another expense!", None, 1.05, 1.15, 0.25, 0, None), # 48
     ("H", "So your solution was to pretend you had nothing?", None, 1.0, 1.05, 0.3, 0, None),                       # 49
     ("G", "I just wanted to protect what I worked hard for.", None, 0.9, 0.95, 2.0, 0, None),                       # 50 -> she softens, they sit
     ("H", "Daniel, I'm not angry because you saved money. I'm angry because you lied about it.", None, 0.92, 1.0, 0.5, 0, None),  # 51 S5
     ("G", "I didn't want you to think I was being selfish.", None, 0.9, 0.95, 0.5, 0, None),                        # 52
     ("H", "You know what's selfish? Making me feel like we're struggling together, when you won't even communicate with me.", None, 0.92, 1.0, 0.5, 0, None),  # 53
     ("G", "I understand.", None, 0.88, 0.95, 0.6, 0, None),                                                         # 54
     ("H", "We don't have to share every dollar. You can have your personal savings. I have mine too. But if we're making plans together, we should be honest about what we can afford.", None, 0.95, 1.0, 0.5, 0, None),  # 55
     ("G", "You're right.", None, 0.9, 0.95, 0.6, 0, None),                                                          # 56
     ("H", "So what's the money for?", None, 0.92, 1.0, 1.4, 0, None),                                               # 57 -> he looks down, smiles
     ("G", "I wanted to use it as a deposit for my own small business.", None, 0.92, 1.0, 0.5, 0, None),             # 58
     ("H", "A business?", None, 0.92, 1.0, 0.4, 0, None),                                                            # 59
     ("G", "I've been planning it for almost a year. I wanted to surprise you when everything was ready.", None, 0.95, 1.0, 0.5, 0, None),  # 60
     ("H", "You could have told me you were working towards something.", None, 0.92, 1.0, 0.4, 0, None),             # 61
     ("G", "I know. I just wanted to prove I could do it myself.", None, 0.9, 0.95, 0.5, 0, None),                   # 62
     ("H", "You don't have to hide your dreams to surprise me.", None, 0.9, 1.0, 1.6, 0, None),                      # 63
     ("H", "Okay. I'm proud of you for saving. But we still need to talk about our weekend trip.", None, 1.0, 1.0, 0.25, 0, None),  # 64 S6
     ("G", "Of course. I'll contribute.", None, 1.0, 1.0, 0.2, 0, None),                                             # 65
     ("H", "Really?", None, 1.0, 1.0, 0.2, 0, None),                                                                 # 66
     ("G", "Yes. I'll transfer the money tonight.", None, 1.0, 1.0, 0.25, 0, None),                                  # 67
     ("H", "That's my responsible man!", None, 1.0, 1.1, 1.6, 0, None),                                              # 68 -> hug, phone buzz
     ("H", "Wait... you bought those expensive headphones on credit?!", "Wait… you bought those expensive headphones ON CREDIT?!", 1.0, 1.4, 0.3, 0, None),  # 69
     ("G", "Well... technically, the headphones are part of my financial journey.", "Well… technically, the headphones are part of my financial journey.", 0.95, 1.0, 0.3, 0, None),  # 70
     ("H", "Daniel!", "DANIEL!", 1.0, 1.6, 0.25, 0, None),                                                           # 71
     ("G", "Baby! I said I'm learning!", "BABY! I SAID I'M LEARNING!", 1.1, 1.4, 0.9, 0, None),                      # 72 -> pillow
     ("G", "I need to save money for my safety now!", "I NEED TO SAVE MONEY FOR MY SAFETY NOW!", 1.12, 1.4, 0.0, 0, None)]  # 73
t = 0.0; buf = np.zeros(SR * 400, np.float32); segs = []
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
total = t + 8.0
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); print(" ".join(f"{s['i']}:{s['start']}" for s in segs))
