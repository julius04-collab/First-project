import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
FPS, SR = 30, 24000
QA = [("Tail", "Cola", "Spanish part two. Easy, right? What's tail in Spanish?"),
      ("Line", "Cola", "Okay. Line? Like a queue?"),
      ("Glue", "Cola", "Glue?"),
      ("Soda", "Cola", "Wait... soda?"),
      ("Bank", "Banco", "Okay, okay. Bank?"),
      ("Bench", "Banco", "Bench?"),
      ("Cat", "Gato", "Cat?"),
      ("Jack", "Gato", "And a car jack?")]
V = {"G": ("am_michael", 1.05), "S": ("ef_dora", 1.0)}
def say(who, txt, lang, sp=None):
    v, s0 = V[who]; a, _ = k.create(txt, voice=v, speed=sp or s0, lang=lang); return a
def env_of(a):
    hop = SR // FPS; return [float(np.sqrt(np.mean(a[j*hop:(j+1)*hop]**2))) for j in range(len(a)//hop)]
segs = []; buf = np.zeros(SR * 80, np.float32); t = 0.0
def place(who, txt, lang, st, kind, word=None, sp=None, sentence=None):
    a = say(who, txt, lang, sp); n0 = int(st * SR); buf[n0:n0+len(a)] += a
    d = dict(who=who, text=txt, start=st, end=st+len(a)/SR, env=env_of(a), word=word, kind=kind)
    if sentence is not None: d["sentence"] = sentence
    segs.append(d); return d["end"]
for en, es, q in QA:
    e = place("G", q, "en-us", t, "q"); t = e + 0.22
    e = place("S", es + ".", "es", t, "a", word=en); t = e + 0.4
e = place("G", "Okay. Say this in Spanish. At the bank, the cat with a tail stands in line to buy glue, and then sits on the bench with a car jack and a soda.", "en-us", t, "instr")
BPM = 96; EIGHTH = 60 / BPM / 2
beat = e + 0.5
CH = ["En el banco,", "el gato con cola", "hace cola", "para comprar cola,", "y después se sienta", "en el banco", "con un gato", "y una cola."]
nxt = beat
for j, ch in enumerate(CH):
    grid = beat + j * 4 * EIGHTH
    st = max(grid, nxt + 0.04)
    st = beat + np.ceil((st - beat) / EIGHTH - 1e-6) * EIGHTH
    nxt = place("S", ch, "es", st, "sent", sp=1.15, sentence=j)
t = nxt + 1.0
e = place("G", "So... half of Spanish is just cola?", "en-us", t, "end1"); t = e + 0.35
e = place("S", "Sí. Cola.", "es", t, "end2"); t = e + 0.35
allenv = np.concatenate([s["env"] for s in segs]); p = np.percentile(allenv, 95)
for s in segs: s["env"] = [round(min(1, x / p), 3) for x in s["env"]]
sf.write(D + "/vo.wav", buf[:int((t + 0.5) * SR)], SR)
json.dump(dict(segs=segs, beat_start=beat, bpm=BPM, end=t), open(D + "/vo.json", "w"))
print("beat", round(beat, 2), "end", round(t, 2))
for s in segs[-10:]: print(s["kind"], round(s["start"], 2), round(s["end"], 2), s["text"][:40])
