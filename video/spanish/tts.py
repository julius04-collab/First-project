import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
FPS = 30
QA = [("Potato","Papa"),("Dad","Papá"),("Pope","Papa"),("Llama","Llama"),("Flame","Llama"),("Calls","Llama"),("Wine","Vino"),("Came","Vino")]
lines = [("G","Spanish is easy, right? What's potato in Spanish?", "en-us", None)]
lines.append(("S", "Papa.", "es", "Potato"))
for i,(en,es) in enumerate(QA[1:]):
    q = {"Dad":"Okay. Dad?","Pope":"Pope?","Llama":"Wait... llama?","Flame":"Flame?","Calls":"Calls?","Wine":"Wine?","Came":"And came?"}[en]
    lines.append(("G", q, "en-us", None)); lines.append(("S", es + ".", "es", en))
lines.append(("G","Okay. Say this in Spanish. Dad calls the llama next to the flame, and the Pope came with wine and potatoes.","en-us",None))
CHUNKS = ["Papá llama a la llama,", "junto a la llama,", "y el Papa vino", "con vino y papa."]
V = {"G": ("am_michael", 1.05), "S": ("ef_dora", 1.0)}
def say(who, txt, lang, sp=None):
    v, sp0 = V[who]; a, sr = k.create(txt, voice=v, speed=sp or sp0, lang=lang); return a, sr
segs=[]; out=[]; t=0.0; SR=24000
def env_of(a):
    hop = SR//FPS; return [float(np.sqrt(np.mean(a[j*hop:(j+1)*hop]**2))) for j in range(len(a)//hop)]
for i,(who,txt,lang,word) in enumerate(lines):
    a, SR = say(who, txt, lang)
    segs.append(dict(who=who, text=txt, start=t, end=t+len(a)/SR, env=env_of(a), word=word))
    gap = 0.22 if who == "G" else 0.4
    out += [a, np.zeros(int(SR*gap), np.float32)]; t += len(a)/SR + gap
# sentence on the beat: 96 bpm, one chunk per bar, starting after a short pause
BPM = 96; BAR = 4*60/BPM
t += 0.5
beat_start = t
buf = np.concatenate(out)
for j, ch in enumerate(CHUNKS):
    a, _ = say("S", ch, "es", 1.15)
    st = beat_start + j*BAR*0.5 if False else beat_start + j*(BAR/2)
    segs.append(dict(who="S", text=ch, start=st, end=st+len(a)/SR, env=env_of(a), word=None, sentence=j))
    n0 = int(st*SR); need = n0 + len(a)
    if len(buf) < need: buf = np.concatenate([buf, np.zeros(need-len(buf), np.float32)])
    buf[n0:n0+len(a)] += a
t = segs[-1]["end"] + BAR*0.75
for who, txt, lang in [("G","So... Spanish is just three words?","en-us"),("S","Sí.","es")]:
    a,_ = say(who, txt, lang)
    segs.append(dict(who=who, text=txt, start=t, end=t+len(a)/SR, env=env_of(a), word=None))
    n0=int(t*SR); need=n0+len(a)
    if len(buf) < need: buf = np.concatenate([buf, np.zeros(need-len(buf), np.float32)])
    buf[n0:n0+len(a)] += a; t += len(a)/SR + 0.35
allenv=np.concatenate([s["env"] for s in segs]); p=np.percentile(allenv,95)
for s in segs: s["env"]=[round(min(1,e/p),3) for e in s["env"]]
sf.write(D+"/vo.wav", buf, SR)
json.dump(dict(segs=segs, beat_start=beat_start, bpm=BPM, end=t), open(D+"/vo.json","w"))
print("beat at", round(beat_start,2), "end", round(t,2)); print([(s["who"], round(s["start"],1), s["text"][:30]) for s in segs])
