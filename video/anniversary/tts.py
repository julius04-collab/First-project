import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
SR, FPS = 24000, 30
V = {"G": "am_michael", "H": "af_bella"}
# (who, spoken, caption, speed, gain, pause_after, pre)
L = [("H", "Babe... do you know what today is?", None, 1.05, 1.0, 0.4, 1.3),
     ("G", "Tuesday?", None, 1.0, 1.0, 0.6, 0),
     ("H", "It's our anniversary.", None, 0.95, 1.0, 1.3, 0),
     ("G", "I knew that. I was just... testing you.", "…I knew that. I was just… testing you.", 1.05, 1.0, 0.4, 0),
     ("H", "Oh really? Okay. When did we first meet?", None, 1.05, 1.0, 0.3, 0),
     ("G", "In... the summer... of... a year.", None, 1.0, 1.0, 0.4, 0),
     ("H", "What's my birthday?", None, 1.05, 1.0, 0.3, 0),
     ("G", "March... something. Or May. It has an M.", None, 1.0, 1.0, 0.5, 0),
     ("H", "Okay. When is Cristiano Ronaldo's birthday?", None, 1.0, 1.0, 0.25, 0),
     ("G", "Fifth of February, nineteen eighty-five. Born in Funchal, Madeira, Portugal.", "5th of February, 1985. Born in Funchal, Madeira, Portugal.", 1.15, 1.0, 0.3, 0),
     ("H", "Messi?", None, 1.0, 1.0, 0.2, 0),
     ("G", "Twenty-fourth of June, nineteen eighty-seven. Rosario, Argentina.", "24th of June, 1987. Rosario, Argentina.", 1.15, 1.0, 1.6, 0),
     ("H", "I hate you anyways.", None, 0.95, 1.0, 1.7, 0),
     ("H", "Happy anniversary, babe.", None, 0.95, 1.0, 1.0, 0),
     ("G", "Can I still watch the second half?", "…Can I still watch the second half?", 0.92, 0.75, 0.0, 0)]
t = 0.0; buf = np.zeros(SR * 70, np.float32); segs = []
for i, (who, line, cap, sp, gain, pause, pre) in enumerate(L):
    t += pre
    a, _ = k.create(line, voice=V[who], speed=sp, lang="en-us"); a = a * gain
    n0 = int(t * SR); buf[n0:n0 + len(a)] += a
    hop = SR // FPS
    env = [float(np.sqrt(np.mean(a[j*hop:(j+1)*hop] ** 2))) for j in range(len(a) // hop)]
    segs.append(dict(i=i, who=who, text=(cap or line).replace("...", "…"), start=round(t, 3), end=round(t + len(a) / SR, 3), env=env))
    t += len(a) / SR + pause
p = np.percentile(np.concatenate([s["env"] for s in segs]), 95)
for s in segs: s["env"] = [round(min(1, e / p), 3) for e in s["env"]]
total = t + 2.8
buf = buf[:int(total * SR)]; buf /= max(1.0, np.abs(buf).max() / 0.95)
sf.write(D + "/vo.wav", buf, SR)
json.dump(dict(segs=segs, total=round(total, 2)), open(D + "/vo.json", "w"))
print("total", round(total, 2)); [print(s["i"], s["who"], s["start"], s["end"], s["text"][:50]) for s in segs]
