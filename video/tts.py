import sys, json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
k = Kokoro("kokoro.onnx", "voices.bin")
lines = [
"You just swallowed a bite of jollof rice. Here's what happens in the next sixty minutes.",
"Eight seconds later, it drops into your stomach, a bag about the size of your fist that stretches to hold over a litre.",
"Right away, the walls start pouring in acid. It's strong enough to dissolve metal, so your stomach coats itself in thick mucus to keep from digesting itself. It even replaces its inner lining every few days.",
"Next, an enzyme called pepsin starts cutting the chicken's protein into smaller pieces.",
"Around minute ten, the muscles start squeezing, three waves every minute, mashing everything into a thick paste called chyme.",
"At twenty minutes, your brain finally gets the \"I'm full\" signal.",
"And by the hour mark, a tiny valve opens, letting the first spoonfuls into your small intestine.",
"The real journey has just started.",
]
voice = sys.argv[1]; out=[]; t=0; segs=[]
for i,l in enumerate(lines):
    a, sr = k.create(l, voice=voice, speed=1.12, lang="en-us")
    gap = np.zeros(int(sr*0.35), dtype=np.float32)
    segs.append({"start": t, "end": t+len(a)/sr, "text": l})
    out += [a, gap]; t += (len(a)+len(gap))/sr
sf.write(f"vo_{voice}.wav", np.concatenate(out), sr)
json.dump(segs, open(f"vo_{voice}.json","w"), indent=1)
print(voice, round(t,2))
