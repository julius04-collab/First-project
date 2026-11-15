"""Generate narration.mp3 + src/timeline.json (sentence-level timing, one segment per caption line)."""
import json, os, subprocess, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = sys.argv[1]  # folder with kokoro.onnx + voices.bin
k = Kokoro(os.path.join(MODEL, "kokoro.onnx"), os.path.join(MODEL, "voices.bin"))
VOICE = {"N": ("bm_george", 1.2), "L": ("am_michael", 1.08), "C": ("bm_lewis", 1.0)}
# (scene, speaker, text, pause_after)
S = [
 (1, "N", "One morning, Leo noticed something wrong with his shadow.", 0.35),
 (1, "N", "He raised his hand.", 0.45),
 (1, "N", "His shadow... yawned.", 0.7),
 (2, "N", "He waved. He jumped. He did a full victory dance.", 0.35),
 (2, "N", "The shadow just leaned against the wall like, \"Bro. It's seven a.m.\"", 0.7),
 (3, "N", "Leo tried to film it, but on camera, it acted completely normal.", 0.4),
 (3, "N", "The second he lowered the phone, it took a bow.", 0.8),
 (4, "N", "On his way to work, the shadow stopped at the bus stop and pointed at the bus.", 0.3),
 (4, "N", "Leo said,", 0.15),
 (4, "L", "Since when do shadows pick my bus?", 0.35),
 (4, "N", "And he got on.", 0.6),
 (5, "N", "Two streets later, the bus skidded into a ditch.", 0.4),
 (5, "N", "Everyone climbed out, dusty but fine.", 0.4),
 (6, "N", "And his shadow was waiting on the sidewalk. Arms folded. Tapping its foot.", 0.8),
 (7, "N", "From that day, Leo listened.", 0.3),
 (7, "N", "A man called:", 0.2),
 (7, "C", "Hi, this is your bank. Just read me the three digits on the back of your card.", 0.35),
 (7, "N", "The shadow facepalmed. Leo hung up.", 0.7),
 (8, "N", "When the shadow pointed at the door, Leo said,", 0.15),
 (8, "L", "This is my apartment!", 0.35),
 (8, "N", "The shadow dragged him out by the ankle.", 0.4),
 (8, "N", "Seconds later, the ceiling fan crashed onto his chair.", 0.8),
 (9, "N", "Soon, it was picking his outfits. It was never wrong.", 0.9),
 (10, "N", "Until one night, the light flickered.", 0.6),
 (10, "N", "The shadow turned around, pointed straight at Leo, and started shaking.", 0.8),
 (11, "N", "Leo slowly looked behind him.", 0.9),
 (11, "N", "There was a second shadow on the wall.", 0.8),
 (11, "N", "It waved. Shyly.", 0.7),
 (11, "N", "His shadow wasn't scared. It was nervous. It was introducing its girlfriend.", 0.8),
 (12, "N", "Now Leo has two shadows. And neither of them lets him eat pizza after midnight.", 0.7),
 (12, "N", "Would you trust your shadow? Comment below.", 1.6),
]
SR = 24000; LEAD = 0.5
out = [np.zeros(int(LEAD * SR), np.float32)]; t = LEAD; segs = []
for i, (sc, who, text, pause) in enumerate(S):
    v, sp = VOICE[who]
    a, _ = k.create(text, voice=v, speed=sp, lang="en-us")
    if who == "N" and sc in (10, 11) and i < 26:
        a, _ = k.create(text, voice=v, speed=1.02, lang="en-us")
    segs.append(dict(id=i, scene=sc, speaker=who, text=text.replace("...", "…"), start=round(t, 3), end=round(t + len(a) / SR, 3)))
    pause *= 0.8; out += [a, np.zeros(int(pause * SR), np.float32)]; t += len(a) / SR + pause
audio = np.concatenate(out); audio /= np.abs(audio).max() / 0.9
os.makedirs(os.path.join(ROOT, "public"), exist_ok=True)
wav = os.path.join(ROOT, "public", "narration.wav"); sf.write(wav, audio, SR)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "160k", os.path.join(ROOT, "public", "narration.mp3")], check=True)
os.remove(wav)
json.dump(dict(fps=30, duration=round(t, 3), segments=segs), open(os.path.join(ROOT, "src", "timeline.json"), "w"), indent=1)
print("duration", round(t, 2))
for s in segs: print(s["scene"], s["start"], s["text"][:50])
