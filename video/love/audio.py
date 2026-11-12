import json, os, numpy as np, soundfile as sf
D = os.path.dirname(os.path.abspath(__file__))
vo, sr = sf.read(D + "/vo.wav", dtype="float32")
segs = json.load(open(D + "/vo.json"))
LEAD, TAIL = 0.5, 3.4
total = segs[-1]["end"] + LEAD + TAIL
N = int(total * sr); t = np.arange(N) / sr
out = np.zeros(N, np.float32)
v = vo / np.abs(vo).max() * 0.9
s0 = int(LEAD * sr); out[s0:s0 + len(v)] += v[:N - s0]
scratch_t = segs[16]["end"] + LEAD + 0.15
resume_t = segs[17]["end"] + LEAD + 0.2
def note(m): return 440 * 2 ** ((m - 69) / 12)
chords = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]  # Fmaj7 Em7 Dm7 Cmaj7
beat = 60 / 78
mus = np.zeros(N)
nb = int(total / beat) + 1
rng = np.random.default_rng(3)
for b in range(nb):
    bt = b * beat
    ch = chords[(b // 4) % 4]
    a = int(bt * sr); L = min(N - a, int(beat * 1.6 * sr))
    if L <= 0: break
    tt = np.arange(L) / sr
    if b % 2 == 0:
        for m in ch:
            f = note(m)
            mus[a:a+L] += (np.sin(2*np.pi*f*tt) + 0.25*np.sin(2*np.pi*2*f*tt)) * np.exp(-tt*2.2) * 0.5
        f = note(ch[0] - 12); mus[a:a+L] += np.sin(2*np.pi*f*tt) * np.exp(-tt*1.5) * 0.7
    if b % 4 in (0, 2):
        kl = min(L, int(0.25*sr)); k = np.arange(kl)/sr
        mus[a:a+kl] += np.sin(2*np.pi*(55 + 60*np.exp(-k*30))*k) * np.exp(-k*14) * 1.4
    if b % 4 in (1, 3):
        sl = min(L, int(0.2*sr)); n = rng.standard_normal(sl); n = n - np.convolve(n, np.ones(8)/8, 'same')
        mus[a:a+sl] += n * np.exp(-np.arange(sl)/sr*25) * 0.35
    for h in (0, 0.5):
        ha = int((bt + h*beat) * sr); hl = min(N - ha, int(0.05*sr))
        if hl > 0:
            n = rng.standard_normal(hl); n = n - np.convolve(n, np.ones(3)/3, 'same')
            mus[ha:ha+hl] += n * np.exp(-np.arange(hl)/sr*80) * 0.15
mus /= np.abs(mus).max()
gate = np.ones(N)
gate[(t >= scratch_t) & (t < resume_t)] = 0
ramp = int(0.05*sr); ia = int(scratch_t*sr); gate[max(0, ia-ramp):ia] = np.linspace(1, 0, min(ramp, ia))
ib = int(resume_t*sr); gate[ib:ib+int(0.4*sr)] = np.linspace(0, 1, len(gate[ib:ib+int(0.4*sr)]))
out += (mus * gate * 0.10).astype(np.float32)
# record scratch
sl = int(0.45*sr); st = np.arange(sl)/sr
fr = 300 + 900*np.abs(np.sin(st*2*np.pi*3.3))
ph = 2*np.pi*np.cumsum(fr)/sr
scr = (np.sign(np.sin(ph))*0.5 + rng.standard_normal(sl)*0.4) * np.exp(-st*3)
scr = np.convolve(scr, np.ones(6)/6, 'same')
out[ia:ia+sl] += (scr/np.abs(scr).max()*0.35).astype(np.float32)
# whooshes on cutaways
for li, frac in [(3,0.42),(7,0.38),(9,0.3),(11,0.4)]:
    s = segs[li]; ct = s["start"] + LEAD + (s["end"]-s["start"])*frac
    L = int(0.5*sr); n = rng.standard_normal(L); n = np.convolve(n, np.ones(30)/30, 'same'); n -= np.convolve(n, np.ones(300)/300, 'same')
    a = int((ct-0.25)*sr); out[a:a+L] += (n/np.abs(n).max()*np.sin(np.linspace(0,np.pi,L))**2*0.12).astype(np.float32)
fade = int(0.8*sr); out[-fade:] *= np.linspace(1, 0, fade)
out /= max(1.0, np.abs(out).max()/0.97)
sf.write(D + "/mix.wav", out, sr); print("audio", round(total, 2))
