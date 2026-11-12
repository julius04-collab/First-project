import sys, json, os, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
D = os.path.dirname(os.path.abspath(__file__))
k = Kokoro(D + "/../tts/kokoro.onnx", D + "/../tts/voices.bin")
lines = [
"You've been brushing your teeth wrong your whole life. And mistake number one is something almost everybody does.",
"Mistake one: you rinse. That foam you spit out is full of fluoride, the stuff that repairs and strengthens your enamel. Rinse with water, and you wash it straight down the sink.",
"Spit. Don't rinse.",
"Mistake two: you brush right after breakfast. Orange juice, Zobo, soft drinks. They soften your enamel for up to an hour.",
"Brush then, and you're scrubbing away your own teeth. Brush before you eat, or wait an hour.",
"Mistake three: you scrub like you're washing a pot. Hard back-and-forth strokes push your gums back and wear down your enamel.",
"Tilt the brush toward your gums and use small, gentle circles.",
"Mistake four: you're done in forty-five seconds. The rule is two full minutes, twice a day.",
"Mistake five: you skip your tongue. It's covered in bacteria, and it's a major cause of bad breath.",
"Mistake six: you've had that toothbrush for a year. Change it every three months, or once the bristles start to spread.",
"And the most important brush of the day? The one before bed. While you sleep, your mouth dries out, and bacteria have all night to attack.",
"Be honest. How many of these are you guilty of? Drop the number in the comments.",
]
voice = sys.argv[1]; out=[]; t=0; segs=[]
for i,l in enumerate(lines):
    a, sr = k.create(l, voice=voice, speed=1.15, lang="en-us")
    gap = np.zeros(int(sr*(1.0 if i == 2 else 0.45 if i+1 < len(lines) and lines[i+1].startswith(("Mistake","And","Be")) else 0.3)), dtype=np.float32)
    segs.append({"start": t, "end": t+len(a)/sr, "text": l})
    out += [a, gap]; t += (len(a)+len(gap))/sr
sf.write(f"{D}/vo.wav", np.concatenate(out), sr)
json.dump(segs, open(f"{D}/vo.json","w"), indent=1)
print(voice, round(t,2), [round(s['end']-s['start'],1) for s in segs])
