import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
L = [
"Leo thought it was going to be an ordinary morning. Until he noticed something strange on his bedroom floor.",
"His shadow wasn't following him anymore. Instead, it was pointing toward the apartment door.",
"Leo followed its warning. Seconds later, a flowerpot crashed exactly where he had been standing.",
"That was impossible. But his shadow seemed to know something he didn't, so Leo decided to follow.",
"Outside, it warned him again. A cyclist lost control, but Leo moved just in time.",
"The shadow wasn't playing tricks. It was leading him somewhere, and it seemed increasingly desperate.",
"At the next street, a little girl chased her ball toward an approaching vehicle.",
"Leo understood the warning and pulled her safely back. His strange shadow had just helped save a life.",
"Then it pointed above him. A heavy shop sign was hanging by a nearly broken bracket.",
"Leo looked up, but he was standing directly beneath it. The sign was already beginning to fall.",
"Suddenly, his shadow moved him aside. The sign crashed down, missing him by inches.",
"Everything returned to normal. But as Leo walked away, his shadow secretly waved goodbye.",
]
SR = 24000; out = np.zeros(SR * 121, np.float32); info = []
for i, line in enumerate(L):
    a, sr = k.create(line, voice="am_michael", speed=0.98, lang="en-us")
    st = i * 10 + 0.45
    n0 = int(st * SR); out[n0:n0 + len(a)] += a
    info.append(dict(clip=i + 1, start=st, dur=round(len(a) / SR, 2), text=line))
sf.write(D + "/narration.wav", out[:SR * 120], SR)
json.dump(info, open(D + "/narration.json", "w"), indent=1)
for x in info: print(x["clip"], x["dur"])
