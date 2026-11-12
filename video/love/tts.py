import json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
L = [
("A","Why does my heart start racing anytime you text me? Be honest. Did you do something to me?"),
("T","Me? No oh. That's your brain. You want the romantic version, or the science version?"),
("A","Science. Impress me."),
("T","When you see me, a part of your brain called the V T A floods you with dopamine. The reward chemical."),
("A","Dopamine... like addiction?"),
("T","Exactly. Brain scans show love lights up some of the same reward areas as cocaine."),
("A","Okay, but why can't I stop thinking about you?"),
("T","Because your serotonin drops. Scientists see a similar pattern in people with O C D."),
("A","And the sweaty palms? The butterflies?"),
("T","Norepinephrine. Your body treats me like an emergency. Heart racing, blood rushing away from your stomach."),
("A","So that's why I ignore all your red flags?"),
("T","That's the scary part. The part of your brain that judges people goes quiet."),
("A","So love is just chemicals?"),
("T","And studies say that crazy phase usually fades in about two years."),
("A","Two years?! Then what?"),
("T","Then oxytocin takes over. The bonding chemical. That's when it becomes real love."),
("A","Hmm. So you're saying you're my drug."),
("T","No... I'm saying, give me two years."),
]
V = {"A": ("af_bella", 1.08), "T": ("am_michael", 1.0)}
out=[]; t=0.0; segs=[]; FPS=30
for i,(who,line) in enumerate(L):
    v, sp = V[who]
    a, sr = k.create(line, voice=v, speed=sp, lang="en-us")
    hop = sr//FPS
    env = [float(np.sqrt(np.mean(a[j*hop:(j+1)*hop]**2))) for j in range(len(a)//hop)]
    segs.append({"who":who,"start":t,"end":t+len(a)/sr,"text":line,"env":env})
    gap = 1.3 if i == 16 else 0.38
    out += [a, np.zeros(int(sr*gap), np.float32)]; t += len(a)/sr + gap
allenv = np.concatenate([s["env"] for s in segs]); p = np.percentile(allenv, 95)
for s in segs: s["env"] = [round(min(1.0, e/p),3) for e in s["env"]]
sf.write(D+"/vo.wav", np.concatenate(out), sr)
json.dump(segs, open(D+"/vo.json","w"))
print(round(t,2), [round(s["end"]-s["start"],1) for s in segs])
