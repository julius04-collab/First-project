import importlib.util, json, math, os, subprocess, sys
import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from render import C, clamp, ss, ease_out_back, P, lin, rad, poly, text, chip, pop, TF_BLACK, TF_B

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
M = _load("mia_render", os.path.join(HERE, "..", "mia", "render.py"))
CO = _load("couch_render", os.path.join(HERE, "..", "couch", "render.py"))

W, H, FPS = 1080, 1920, 30
D = json.load(open(os.path.join(HERE, "vo.json")))
SEGS, TOTAL = D["segs"], D["total"]
INK = C("141414")

def lerp(a, b, t):
    return a + (b - a) * t

def lerp2(p, q, t):
    return (lerp(p[0], q[0], t), lerp(p[1], q[1], t))

def S(i):
    return SEGS[i]["start"]

def E(i):
    return SEGS[i]["end"]

def amp(who, t):
    for s in SEGS:
        if s["who"] == who and s["start"] <= t < s["end"]:
            j = int((t - s["start"]) * FPS)
            if j < len(s["env"]):
                return s["env"][j]
    return 0.0
GX, HX = 330.0, 740.0
SIT = (0.2, 1.5)
SPARK = S(5) + 0.35 * (E(5) - S(5))
SCRATCH = E(7) + 0.02
STING = E(8) + 0.05
HESIT = (E(16), S(17))
THINK = (E(26), S(27))
SIL = (E(27), S(28))
GRAB = E(29) + 0.05
RUN0 = GRAB + 0.35
FREEZE2 = (S(30) + 0.9, TOTAL)
BLACK = TOTAL - 0.3
ANGRY = (28, 29, 30)

def at(t):
    return FREEZE2[0] if t >= FREEZE2[0] else t

def girl_x(t):
    if t < SIT[1]:
        return lerp(1300, HX, ss(SIT[0], SIT[1] - 0.3, t))
    if t < RUN0 + 0.2:
        return HX
    return max(GX + 120, HX - 380 * (t - RUN0 - 0.2))

def guy_x(t):
    if t < RUN0:
        return GX
    return GX - 260 * min(t - RUN0, 0.8)

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
CLASP_L, CLASP_R = (60, 60), (-60, 60)
HIPS_L, HIPS_R = (-18, 168), (18, 168)

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.0), brows=(8, 8), mouth="smirk", grass="mouth", tilt=0, rise=0.0)
    st["blink"] = (t % 3.7) < 0.12
    if t < S(3):
        st.update(phone=True, handL=(90, 60), look=(0.4, 0.7), lean=-6)                      # relaxed, distracted
        if S(1) <= t: st["look"] = (0.6, 0.5)
    if S(3) <= t < S(5): st.update(eyes="wide", brows=(18, 18), mouth="flat", look=(1.0, 0.0))
    if S(5) <= t < STING:                                                                       # confident
        st.update(look=(0.2, -0.4), brows=(14, 14), mouth="smile", handR=(120, -90), tilt=6, eyes="happy" if amp("G", t) < 0.05 else "n")
        if S(8) <= t: st.update(handL=(-130, -60), handR=(130, -80), lean=-6)
    if STING <= t < S(16):
        st.update(mouth="smile", brows=(12, 12))
        if S(9) <= t: st.update(eyes="n", brows=(16, 16), mouth="flat")
        if S(10) <= t < E(10): st.update(handR=(120, -60), mouth="smile", eyes="happy")
        if S(12) <= t < E(12): st.update(handL=(-140, -50), handR=(140, -50), brows=(20, 20), eyes="wide")
        if S(14) <= t: st.update(mouth="smile", eyes="happy" if (t * 6) % 1 < 0.5 else "n", sweat=True, tilt=6 * math.sin(t * 12))   # nervous laugh
    if S(16) <= t < S(24):
        st.update(sweat=True, brows=(18, 18), mouth="flat", eyes="wide")
        if HESIT[0] <= t < S(17): st.update(mouth="smile", eyes="n", brows=(16, 16))           # fake frozen smile
        if S(17) <= t < E(17) + 0.2: st.update(mouth="smile", handR=(120, -110), eyes="n")
        if S(19) <= t < E(19): st.update(handL=(-130, -60), handR=(130, -60), eyes="n")
        if S(21) <= t < S(23): st.update(look=(0.3, -0.8), eyes="n", brows=(14, 4), mouth="flat", handR=(-60, -150))
        if S(23) <= t: st.update(look=(1.0, 0.0), mouth="smile", eyes="n", brows=(16, 16), handR=REST_R)
    if S(24) <= t < GRAB:
        st.update(sweat=True, eyes="wide", brows=(20, 20), mouth="flat")
        if S(25) <= t < E(25): st.update(handL=(-140, -60), handR=(140, -60), mouth="smile", eyes="n")
        if THINK[0] <= t < S(27): st.update(look=(0.3, -0.9), eyes="n", brows=(14, 2), handR=(-70, -60), tilt=-6, sweat=False)
        if S(27) <= t < S(28): st.update(look=(1.0, 0.0), eyes="n", brows=(0, 0), mouth="flat", handR=REST_R, tilt=0, sweat=False)   # dead serious
        if S(28) <= t: st.update(eyes="wide", mouth="o", brows=(24, 24), handL=UP_L, handR=UP_R, sweat=True)
        if S(29) <= t: st.update(mouth="smile", handL=(-140, -80), handR=(140, -80))
    if GRAB <= t:
        st.update(rise=ss(GRAB, RUN0, t), eyes="wide", mouth="o", brows=(24, 24), sweat=True, handL=UP_L, handR=UP_R, look=(1.0, 0.0), tilt=-8)
        if RUN0 <= t < RUN0 + 0.8: st.update(walk=t * 16, lean=-10)
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=CLASP_L, handR=CLASP_R, look=(-1.0, 0.0), brows=(12, 12), mouth="smile", tilt=6, rise=0.0)
    st["blink"] = (t % 4.1) < 0.12
    if t < SIT[1]:
        st.update(rise=1 - ss(SIT[1] - 0.4, SIT[1], t), walk=t * 9 if t < SIT[1] - 0.4 else None)
    if S(5) <= t < S(7): st.update(eyes="happy", brows=(16, 16), tilt=10)                     # happy
    if S(6) <= t < E(6): st.update(eyes="n", handR=(-110, -80))
    if S(8) <= t:                                                                                # smile slowly disappears
        k = ss(S(8), E(8), t)
        st.update(mouth="smile" if k < 0.55 else "flat", brows=(lerp(12, -14, k), lerp(12, 10, k)), tilt=lerp(6, -4, k), eyes="n")
    if STING <= t < S(16):
        st.update(brows=(-14, 12), mouth="flat", tilt=-6)
        if S(11) <= t < E(11): st.update(handR=(-150, -60), brows=(-18, 10))
        if S(13) <= t: st.update(brows=(-12, 16), handL=HIPS_L, handR=HIPS_R)
        if S(14) <= t: st.update(brows=(-18, -18))
    if S(16) <= t < S(24):
        st.update(brows=(4, 4), mouth="flat", tilt=0, handL=CLASP_L, handR=CLASP_R)
        if S(16) <= t < E(16): st.update(mouth="smile", tilt=8, brows=(10, 10))
        if HESIT[0] <= t: st.update(brows=(-14, -14), eyes="n")                                  # angry at the hesitation
        if S(18) <= t < E(18): st.update(handR=(-150, -70 + 12 * math.sin(t * 9)), brows=(-20, -20))
        if S(20) <= t: st.update(brows=(-12, 14))
        if S(22) <= t: st.update(handR=(-120, -40), brows=(-10, 12))
        if S(23) <= t + 0.0 and t > S(23) + 1.0: st.update(brows=(-18, -18), handR=CLASP_R)
    if S(24) <= t < GRAB:
        st.update(brows=(-18, -18), mouth="flat", tilt=-6)                                       # arms folded
        if S(26) <= t: st.update(brows=(-12, 14), tilt=-4)
        if SIL[0] <= t: st.update(eyes="wide", mouth="o", brows=(20, 20), tilt=0)                 # completely shocked
        if S(28) <= t: st.update(handL=(-120, -195 + 12 * math.sin(t * 22)), handR=(120, -195 + 12 * math.cos(t * 22)), brows=(-28, -28), tilt=-10)
        if E(28) + 0.3 <= t: st.update(handL=CLASP_L, handR=CLASP_R, eyes="n", mouth="flat")
    if GRAB <= t:
        st.update(rise=ss(GRAB, RUN0, t), handR=(30, -230), handL=(-120, -60), brows=(-28, -28), mouth="o", pillow=True, tilt=-8, eyes="n")
        if RUN0 + 0.2 <= t: st.update(walk=t * 14)
    st["amp"] = amp("H", t)
    return st

def G_CU(t, z=1.85):
    us = guy_state(t); return (z, guy_x(t) + 30, 990 - 190 * us["rise"])
def H_CU(t, z=1.85):
    return (z, girl_x(t) - 20, 1040)
MED = (1.2, 560, 1060)
TWO = (1.35, 540, 1060)

def camera(t):
    if t < S(1): return MED
    if t >= FREEZE2[0]:
        k = ss(FREEZE2[0], FREEZE2[0] + 0.12, t); us = guy_state(FREEZE2[0])
        return (lerp(1.9, 2.4, k), guy_x(FREEZE2[0]) + 30, 990 - 190 * us["rise"])
    if GRAB <= t:
        k = ss(S(30), S(30) + 0.25, t); return (lerp(1.0, 1.4, k), lerp(540, 330, k), lerp(1130, 1000, k))
    if STING <= t < S(9):
        k = ss(STING, STING + 0.3, t); return H_CU(t, lerp(1.8, 2.3, k))
    if HESIT[0] <= t < S(17):
        k = (t - HESIT[0]) / (S(17) - HESIT[0]); return G_CU(t, lerp(1.9, 2.5, k))
    if S(27) <= t < S(28):
        if t < SIL[0]: return G_CU(t, 2.3)
        k = (t - SIL[0]) / (S(28) - SIL[0]); return H_CU(t, lerp(1.8, 2.4, k))
    shots = [(1, G_CU), (2, H_CU), (3, G_CU), (4, H_CU), (5, TWO), (6, H_CU), (7, MED), (8, lambda t: H_CU(t, 2.0)),
             (9, H_CU), (10, G_CU), (11, H_CU), (12, G_CU), (13, H_CU), (14, G_CU), (16, lambda t: H_CU(t, 2.2)),
             (17, G_CU), (18, H_CU), (19, G_CU), (20, H_CU), (21, G_CU), (22, H_CU), (23, G_CU), (24, H_CU), (25, G_CU),
             (26, H_CU), (28, lambda t: H_CU(t, 2.4)), (29, G_CU)]
    if THINK[0] <= t < S(27): return G_CU(t, 2.0)
    cur = None
    for i, c in shots:
        if S(i) <= t: cur = (i, c)
    i, c = cur
    c = c(t) if callable(c) else c
    nx = [S(j) for j, _ in shots if S(j) > S(i)]
    b = nx[0] if nx else TOTAL
    q = (t - S(i)) / max(0.1, b - S(i))
    return (c[0] * (1 + 0.05 * q), c[1], c[2])

def shake(t):
    for i, amt in ((28, 20), (29, 10)):
        if S(i) <= t < S(i) + 0.4:
            d = 1 - (t - S(i)) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    for a, amt in ((SCRATCH, 10), (STING, 8), (S(27) + 0.05, 10)):
        if a <= t < a + 0.25:
            d = 1 - (t - a) / 0.25; return (amt * d * math.sin(t * 90), 0)
    return (0, 0)

HL = {0: {"ASK": "y"}, 2: {"PERFECT": "b", "WOMAN.": "b"}, 3: {"PERFECT": "y"}, 4: {"THINK": "y", "DESCRIBE": "y"},
      5: {"BEAUTIFUL,": "y", "INTELLIGENT,": "y", "CARING": "y", "UNDERSTANDING.": "y"}, 6: {"AWW.": "y"},
      7: {"COMPLAIN": "b"}, 8: {"SPACE,": "y", "DREAMS,": "y", "FOOTBALL.": "b"}, 9: {"COMPLAIN?": "b"}, 10: {"PEACEFUL": "y"},
      11: {"TALK?": "b"}, 12: {"WHEN": "y", "TALK.": "y"}, 13: {"DECIDES": "b"}, 14: {"NOT": "b", "ME!": "b"},
      16: {"PERFECT": "b"}, 17: {"COURSE,": "y"}, 18: {"LONG": "b"}, 19: {"QUALITIES!": "y"}, 21: {"BEAUTIFUL,": "y", "CARING,": "y", "INTELLIGENT…": "y"},
      22: {"GO": "y", "ON.": "y"}, 23: {"QUESTIONS.": "b"}, 24: {"NOT": "b"}, 25: {"PERFECT": "y"}, 26: {"ONE": "b", "WORD.": "b"},
      27: {"DANGEROUS.": "b"}, 28: {"WHAT?!": "b"}, 29: {"DANGEROUSLY": "b", "BEAUTIFUL!": "y"}, 30: {"ONE": "b", "WORD!": "b"}}
def chunks():
    out = []
    for s in SEGS:
        words = s["text"].replace('"', "").split()
        cs, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= 3 or w[-1] in ",.?!…:—":
                cs.append(cur); cur = []
        if cur:
            cs.append(cur)
        wt = [sum(len(w) + 2 for w in c) for c in cs]; tot = sum(wt); acc = 0
        for c, x in zip(cs, wt):
            out.append((s["start"] + (s["end"] - s["start"]) * acc / tot, s["start"] + (s["end"] - s["start"]) * (acc + x) / tot, c, s["who"], s["i"]))
            acc += x
    return out
CAPS = chunks()
CAP_Y = 1460

def draw_caption(cv, t):
    for n, (a, b, words, who, i) in enumerate(CAPS):
        nxt = CAPS[n + 1][0] if n + 1 < len(CAPS) else b + 0.4
        if a <= t < min(b + 0.35, nxt):
            k = ease_out_back(min(1, (t - a) / 0.16), 2.2)
            ws = [w.upper() for w in words]
            size = 96
            f = skia.Font(TF_BLACK, size); gap = 26
            wid = lambda: sum(f.measureText(w) for w in ws) + gap * (len(ws) - 1)
            if wid() > 960:
                size *= 960 / wid(); f = skia.Font(TF_BLACK, size); gap *= size / 96
            tw = wid()
            jx = 6 * math.sin(t * 50) if i in ANGRY else 0
            cv.save(); cv.translate(540 + jx, CAP_Y); cv.scale(k, k)
            x = -tw / 2
            for w in ws:
                st = HL.get(i, {}).get(w)
                ww = f.measureText(w)
                if st == "b":
                    r = skia.RRect.MakeRectXY(skia.Rect(x - 12, -size * 0.78, x + ww + 12, size * 0.2), 14, 14)
                    cv.drawRRect(r, P(C("000000"), stroke=12)); cv.drawRRect(r, P(C("e8262a")))
                    cv.drawString(w, x, 0, f, P(C("ffffff")))
                else:
                    cv.drawString(w, x, 0, f, P(C("000000"), stroke=18))
                    cv.drawString(w, x, 0, f, P(C("ffd21f") if st == "y" else C("ffffff")))
                x += ww + gap
            cv.restore()
            if who in ("G", "H"):
                chip(cv, 540, CAP_Y - 128, {"H": "HER", "G": "HIM"}[who], a=0.95, col="ffd23f" if who == "H" else "ffffff", fg="1a1a1a", size=30)
            return

# ---------------------------------------------------------------- pop-up graphics
def xmark(cv, x, y, s, a=1.0):
    for d in (1, -1):
        cv.drawLine(x - s, y - s * d, x + s, y + s * d, P(C("ffffff", a), stroke=s * 0.62))
        cv.drawLine(x - s, y - s * d, x + s, y + s * d, P(C("e8262a", a), stroke=s * 0.42))

def tag(cv, t, t0, t1, label, y, col="ffd23f", fg="141414", size=56):
    if t0 <= t < t1:
        a, k = pop(t, t0, 0.35)
        a = min(a, (t1 - t) / 0.15)
        chip(cv, 540, y, label, a=a, scale=k, col=col, fg=fg, size=size)




def pillow_shape(cv, x, y, rot):
    cv.save(); cv.translate(x, y); cv.rotate(rot)
    r = skia.RRect.MakeRectXY(skia.Rect(-70, -70, 70, 70), 26, 26)
    cv.drawRRect(r, P(C("7ec8a0"))); cv.drawRRect(r, P(INK, stroke=6))
    cv.restore()

def sparkles(cv, t, x, y, t0, dur=0.9, n=8, col="ffe24a"):
    if not (t0 <= t < t0 + dur):
        return
    q = (t - t0) / dur
    for j in range(n):
        an = j * 2 * math.pi / n + q * 2
        r = 80 + 140 * q
        px, py = x + r * math.cos(an), y + r * math.sin(an)
        s = 22 * (1 - q) + 6
        pts = [(px + s * math.cos(k * math.pi / 4) * (1 if k % 2 == 0 else 0.35), py + s * math.sin(k * math.pi / 4) * (1 if k % 2 == 0 else 0.35)) for k in range(8)]
        cv.drawPath(poly(pts), P(C(col, 1 - q)))


def wfrac(i, f):
    return S(i) + f * (E(i) - S(i))
LIST = [("BEAUTIFUL", wfrac(5, 0.3), "3ccf5a"), ("INTELLIGENT", wfrac(5, 0.5), "3ccf5a"), ("CARING", wfrac(5, 0.68), "3ccf5a"),
        ("UNDERSTANDING", wfrac(5, 0.88), "3ccf5a"), ("DOESN'T COMPLAIN", wfrac(7, 0.7), "ff8a1f"), ("GIVES ME SPACE", wfrac(8, 0.18), "ff8a1f"),
        ("SUPPORTS MY DREAMS", wfrac(8, 0.38), "ff8a1f"), ("NO DISTURBING FOOTBALL", wfrac(8, 0.85), "e8262a")]
def checklist(cv, t):
    a0, a1 = LIST[0][1] - 0.2, S(9) + 0.3
    if not (a0 <= t < a1):
        return
    a = min(1, (t - a0) / 0.2, (a1 - t) / 0.2)
    jx = 8 * math.sin(t * 60) * max(0, 1 - (t - STING) / 0.4) if t >= STING else 0
    shown = [it for it in LIST if t >= it[1]]
    hgt = 100 + 66 * len(shown)
    cv.save(); cv.translate(60 + jx, 400)
    r = skia.RRect.MakeRectXY(skia.Rect(0, 0, 700, hgt), 20, 20)
    cv.drawRRect(r, P(C("000000", 0.3 * a), blur=10)); cv.drawRRect(r, P(C("ffffff", 0.95 * a))); cv.drawRRect(r, P(INK, stroke=5))
    text(cv, "HIS PERFECT WOMAN:", 24, 62, 46, C("141414", a), tf=TF_BLACK, align="l")
    for j, (lab, t0, col) in enumerate(shown):
        k = ease_out_back(min(1, (t - t0) / 0.2), 2.0)
        y = 122 + j * 66
        cv.save(); cv.translate(40, y); cv.scale(k, k)
        cv.drawCircle(0, 0, 22, P(C(col, a)))
        text(cv, "✓", 0, 11, 28, C("ffffff", a), tf=TF_BLACK)
        cv.restore()
        text(cv, lab, 74, y + 14, 40, C(col if col != "3ccf5a" else "141414", a), tf=TF_BLACK, align="l")
    cv.restore()

TOP = ["When she asks you to describe your perfect woman…", "CHOOSE YOUR WORDS CAREFULLY"]

def draw_top(cv, t):
    f = skia.Font(TF_B, 40)
    w = max(f.measureText(TOP[0]), skia.Font(TF_BLACK, 48).measureText(TOP[1])) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 286), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    text(cv, TOP[0], 540, 208, 40, C("111111"), tf=TF_B)
    text(cv, TOP[1], 540, 264, 48, C("e74c3c"), tf=TF_BLACK)

def render_frame(cv, t):
    ta = at(t)
    z, wx, wy = camera(t)
    sx, sy = shake(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2 + sx, H / 2 + sy); cv.scale(z, z); cv.translate(-wx, -wy)
    CO.draw_room(cv, ta); CO.draw_couch_back(cv); CO.draw_couch_front(cv)
    gs = girl_state(ta); gx = girl_x(ta)
    M.draw_person(cv, ta, gs, gx, "girl")
    us = guy_state(ta); ux = guy_x(ta)
    M.draw_person(cv, ta, us, ux, "guy")
    if gs.get("pillow"):
        hip = M.SEAT - 18 - 200 * gs.get("rise", 0)
        pillow_shape(cv, gx + 84 + gs["handR"][0], hip - 224 + gs["handR"][1] - 40, 15 * math.sin(ta * 12))
    sparkles(cv, ta, ux, M.SEAT - 18 - 366, SPARK, 1.0, 10, "ff9ec4")
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    if t >= FREEZE2[0]:
        fl = max(0, 1 - (t - FREEZE2[0]) / 0.15)
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("ffffff", 0.6 * fl)))
    draw_top(cv, t)
    checklist(cv, t)
    tag(cv, t, HESIT[0] + 0.2, S(17), "HESITATION: 1.2 SEC", 470, col="e8262a", fg="ffffff", size=56)
    tag(cv, t, S(23) + 0.6, S(24), "WRONG QUALITY", 470, col="e8262a", fg="ffffff", size=58)
    tag(cv, t, S(26) + 0.3, S(27), "ONE WORD ONLY", 470, col="ffd23f", size=58)
    draw_caption(cv, t)
    if t >= BLACK:
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("000000")))

def worker(args):
    k, f0, f1, out = args
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for fi in range(f0, f1):
        cv = surf.getCanvas(); cv.clear(C("000000"))
        render_frame(cv, fi / FPS)
        ff.stdin.write(surf.makeImageSnapshot().toarray().tobytes())
    ff.stdin.close(); ff.wait()
    return out

if __name__ == "__main__":
    if sys.argv[1] == "still":
        surf = skia.Surface(W, H)
        for ts in sys.argv[2:]:
            cv = surf.getCanvas(); cv.clear(C("000000"))
            render_frame(cv, float(ts))
            surf.makeImageSnapshot().save(os.path.join(HERE, f"still_{ts}.png"), skia.kPNG)
        print("total", TOTAL)
    else:
        from multiprocessing import Pool
        N = int(TOTAL * FPS); nw = 4; step = N // nw
        jobs = [(k, k * step, N if k == nw - 1 else (k + 1) * step, os.path.join(HERE, f"part{k}.mp4")) for k in range(nw)]
        with Pool(nw) as p:
            outs = p.map(worker, jobs)
        with open(os.path.join(HERE, "parts.txt"), "w") as f:
            for o in outs:
                f.write(f"file '{o}'\n")
        print("frames", N)
