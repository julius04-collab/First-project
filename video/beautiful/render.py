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

GX, HX0, HX1 = 330.0, 840.0, 650.0
T_REW = (E(1) + 0.05, S(2))
FREEZE = (E(12) + 0.05, E(12) + 1.0)
TURN = (FREEZE[1], S(13))
LOOK4 = (E(30) + 0.1, S(31))
NOD = (E(35) + 0.1, S(36))
EXIT = (E(39) + 0.15, E(39) + 1.5)
BLACK = E(40) + 1.3
ANGRY = (18, 27, 30, 32, 37, 39)

def at(t):
    return FREEZE[0] if FREEZE[0] <= t < FREEZE[1] else t

def girl_x(t):
    if t < T_REW[0]:
        return HX1
    if t < S(22):
        return HX0
    if t < EXIT[0]:
        return lerp(HX0, HX1, ss(S(22), S(22) + 1.3, t))
    return lerp(HX1, 1450, ss(EXIT[0], EXIT[1], t))

def girl_vx(t):
    return (girl_x(t + 0.02) - girl_x(t - 0.02)) / 0.04

HIPS_L, HIPS_R = (-18, 168), (18, 168)
CLASP_L, CLASP_R = (60, 60), (-60, 60)
REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)

def girl_state(t):
    vx = girl_vx(t)
    st = dict(handL=HIPS_L, handR=HIPS_R, look=(-1.0, 0.0), brows=(-14, -14), mouth="flat", tilt=-4, rise=1.0)
    st["blink"] = (t % 4.1) < 0.12
    if t < T_REW[0]:
        st.update(brows=(-22, -22), tilt=-8); st["amp"] = 0
        return st
    def at_mirror():
        st.update(look=(1.0, -0.1), mouth="smile", brows=(8, 8), tilt=6, handR=(70, -115), handL=(-30, -160), mirror=True)
        if (t % 2.6) > 1.6:
            st["eyes"] = "happy"
    if t < S(4):
        at_mirror()
    elif t < S(11):
        st.update(look=(-1.0, 0.0), mouth="smile", brows=(10, 10), tilt=8, handL=CLASP_L, handR=CLASP_R)
        if S(8) <= t < E(8):
            st.update(handR=(-150, -60 + 12 * math.sin(t * 8)), handL=HIPS_L, brows=(4, 4), tilt=-4)
        if S(10) <= t:
            st.update(handL=HIPS_L, handR=HIPS_R, brows=(12, 12), tilt=10)
    elif t < TURN[0]:
        at_mirror(); st["eyes"] = "n"
    elif t < S(13):
        k = ss(TURN[0], TURN[1] - 0.2, t)
        st.update(look=(lerp(1.0, -1.0, k), 0.0), mouth="flat", brows=(lerp(8, -8, k), lerp(8, 18, k)), tilt=lerp(6, -4, k))
    elif t < S(19):
        st.update(brows=(-8, 18), mouth="flat")
        if S(15) <= t:
            st.update(brows=(-14, 10), handL=HIPS_L, handR=HIPS_R)
        if S(17) <= t:
            st.update(brows=(-18, -2), tilt=-8)
    elif t < S(22):
        st.update(handL=CLASP_L, handR=CLASP_R, brows=(-18, -18), tilt=-6)   # folds her arms
    elif t < S(31):
        st.update(brows=(-18, -18))
        if S(24) <= t < E(24):
            st.update(handR=(-160, -70 + 10 * math.sin(t * 8)))
        if S(26) <= t < E(26) + 0.4:
            st.update(brows=(-24, -24), tilt=-12, eyes="n")
        if S(28) <= t < E(28):
            st.update(handL=(-130, -60), handR=(130, -60))
        if S(30) <= t < E(30) + 0.3:
            st.update(handL=(UP_L[0], UP_L[1] + 10 * math.sin(t * 20)), handR=(UP_R[0], UP_R[1] + 10 * math.cos(t * 20)), brows=(-26, -26), tilt=-10)
    elif t < S(35):
        st.update(phone=True, handR=(-110, 40), mouth="smirk", brows=(-4, 12), tilt=-10, look=(-0.6, 0.3))
        if S(33) <= t < E(33):
            st.update(eyes="happy", look=(-1.0, -0.2), tilt=10)
    elif t < S(37):
        st.update(brows=(-16, -16), handL=HIPS_L, handR=HIPS_R)
        if E(35) <= t:
            st.update(brows=(-8, -8))
        if S(36) + 0.6 <= t:
            st.update(eyes="wide", brows=(-4, 16), mouth="o")
    elif t < S(38):
        st.update(handL=(UP_L[0], UP_L[1] + 10 * math.sin(t * 20)), handR=(UP_R[0], UP_R[1] + 10 * math.cos(t * 20)), brows=(-26, -26), tilt=-10)
    elif t < S(39):
        st.update(look=(1.0, -0.3), tilt=14, brows=(-14, -14), handL=CLASP_L, handR=CLASP_R)
    else:
        st.update(handR=(-170, -90), brows=(-24, -24), look=(-1.0, 0.0))
        if EXIT[0] <= t:
            st.update(handR=HIPS_R, look=(1.0, -0.2), tilt=12)
    if abs(vx) > 5:
        st["walk"] = t * 9
        st["look"] = (1.0 if vx > 0 else -1.0, st["look"][1])
    st["amp"] = amp("H", t)
    return st

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, -0.25), brows=(4, 4), mouth="smirk", grass="mouth", tilt=0)
    st["blink"] = (t % 3.7) < 0.12
    if t < T_REW[0]:
        st.update(look=(0.0, 0.0), eyes="wide", brows=(16, 16), mouth="flat", sweat=True, tilt=6)
        st["amp"] = 0; return st
    if t < S(9):
        st.update(phone=True, handL=(100, 95), handR=(30, 175), look=(0.4, 0.7), mouth="smirk", brows=(2, 2))
        if S(7) <= t < E(7):
            st["look"] = (1.0, -0.2)
    elif t < S(11):
        st.update(brows=(8, 8), mouth="smile")
    elif t < S(12):
        st.update(look=(0.3, -0.9), brows=(14, 2), mouth="flat", tilt=-6)
    elif t < TURN[0]:
        st.update(brows=(10, 10), mouth="smile", handR=(130, -50), tilt=6)
    elif t < S(21):
        k = ss(TURN[0], S(13), t)
        st.update(eyes="wide" if k > 0.5 else "n", brows=(lerp(10, 20, k), lerp(10, 20, k)), mouth="flat", sweat=k > 0.6)
        if S(14) <= t:
            w = math.sin(t * 10)
            st.update(mouth="smile", handL=(-130, -80 + 30 * w), handR=(130, -80 - 30 * w), eyes="n", brows=(16, 16))
        if S(15) <= t < S(16) or S(17) <= t < S(18):
            st.update(handL=REST_L, handR=REST_R, eyes="wide", mouth="flat")
        if S(16) <= t < S(17):
            st.update(mouth="smile", handR=(130, -60), handL=REST_L)
        if S(18) <= t < S(19):
            st.update(eyes="wide", mouth="o", handL=UP_L, handR=UP_R)
        if S(19) <= t:
            st.update(eyes="wide", mouth="flat", handL=REST_L, handR=REST_R)
        if S(20) <= t:
            w = math.sin(t * 14)
            st.update(handL=(-130, -100 + 25 * w), handR=(130, -100 - 25 * w), mouth="o")
    elif t < S(31):
        st.update(sweat=True, eyes="wide", brows=(18, 18), mouth="flat")
        if S(23) <= t < E(23) + 0.2:
            st.update(handL=(70, 30), handR=(-70, 30), eyes="n", brows=(20, 20))
        if S(25) <= t < E(25) + 0.2:
            st.update(handR=(150, -70), mouth="o")
        if S(27) <= t < E(27) + 0.2:
            st.update(handL=UP_L, handR=UP_R, mouth="o")
        if S(29) <= t < E(29) + 0.1:
            st.update(handR=(-70, -150), eyes="closed", brows=(10, 10))
        if E(30) <= t:
            st.update(look=(0.0, 0.0), brows=(14, 14), eyes="n", tilt=6, handL=REST_L, handR=REST_R)
    elif t < NOD[0]:
        st.update(brows=(6, 6), mouth="flat")
        if S(32) <= t < E(32) + 0.3:
            st.update(eyes="wide", brows=(22, 22), mouth="o", handL=UP_L, handR=UP_R, lean=4)
        if E(32) + 0.3 <= t:
            st.update(brows=(-12, -12), handL=(70, 60), handR=(-70, 60))
        if S(34) <= t:
            st.update(brows=(12, -6), tilt=8, handL=REST_L, handR=REST_R)
    elif t < S(37):
        st.update(look=(1.0, -0.25 + 0.35 * math.sin((t - NOD[0]) * 7)), mouth="o", brows=(8, 8))
        if S(36) <= t:
            st.update(look=(1.0, -0.25), mouth="smile", handR=(110, -140), brows=(12, -2), tilt=6)
    elif t < EXIT[0]:
        st.update(eyes="wide", brows=(22, 22), mouth="flat", sweat=True)
        if S(38) <= t:
            st.update(mouth="smile", handL=(70, 30), handR=(-70, 30), eyes="n")
    else:
        st.update(look=(1.0, -0.1), brows=(10, 10), mouth="flat", sweat=True)
        if S(40) - 0.3 <= t:
            st.update(look=(0.0, 0.1), brows=(10, 10), mouth="flat", tilt=8, lean=-3, sweat=False, handL=REST_L, handR=REST_R)
            if E(40) <= t:
                st.update(eyes="closed" if (t - E(40)) % 2 < 0.5 else "n")
    st["amp"] = amp("G", t)
    return st

WIDE = (1.0, 560, 1130)
G_CU = (1.85, GX + 30, 990)
TWO = (1.2, 570, 1040)
def H_CU(t, z=1.8):
    return (z, girl_x(t) - 10, 805)

def camera(t):
    if t < S(1):
        return (lerp(2.0, 2.25, t / S(1)), GX + 30, 985)
    if t < T_REW[0]:
        return (lerp(2.0, 2.3, (t - S(1)) / (T_REW[0] - S(1))), HX1 - 10, 805)
    if t < S(2) + 0.3:
        k = ss(T_REW[0], S(2) + 0.3, t)
        return (lerp(2.3, 1.0, k), lerp(HX1, 560, k), lerp(805, 1130, k))
    if FREEZE[0] <= t < FREEZE[1]:
        k = ss(FREEZE[0], FREEZE[0] + 0.12, t); return (lerp(1.85, 2.15, k), GX + 30, 985)
    if TURN[0] <= t < S(13):
        k = (t - TURN[0]) / (S(13) - TURN[0]); return H_CU(t, lerp(1.7, 2.2, k))
    if S(26) <= t < S(27):
        k = (t - S(26)) / (S(27) - S(26)); return (lerp(1.8, 2.7, k), GX + 30, lerp(990, 960, k))
    if S(40) - 0.3 <= t:
        k = ss(S(40) - 0.3, BLACK, t); return (lerp(1.8, 2.3, k), GX + 30, lerp(990, 975, k))
    if S(22) <= t < S(23):
        return (1.1, lerp(620, 520, ss(S(22), S(23), t)), 1080)
    if EXIT[0] <= t < S(40) - 0.3:
        return (1.05, 560, 1110)
    H = H_CU
    shots = [(2, WIDE), (3, G_CU), (4, H), (5, G_CU), (6, H), (7, G_CU), (8, H), (9, G_CU), (10, H), (11, TWO), (12, G_CU),
             (13, lambda t: H_CU(t, 2.2)), (14, G_CU), (15, H), (16, G_CU), (17, H), (18, G_CU), (19, lambda t: H_CU(t, 1.5)), (20, G_CU),
             (21, WIDE), (23, G_CU), (24, H), (25, G_CU), (27, (2.2, GX + 30, 985)), (28, H), (29, G_CU), (30, lambda t: H_CU(t, 2.2)),
             (31, H), (32, (2.2, GX + 30, 985)), (33, H), (34, G_CU), (35, H), (36, G_CU), (37, lambda t: H_CU(t, 2.4)), (38, G_CU), (39, H)]
    if LOOK4[0] <= t < LOOK4[1]:
        return (2.3, GX + 30, 985)
    if NOD[0] <= t < S(36):
        k = (t - NOD[0]) / (S(36) - NOD[0]); return (lerp(1.8, 2.2, k), GX + 30, 985)
    cur = None
    for i, c in shots:
        if S(i) <= t:
            cur = (i, c)
    i, c = cur
    c = c(t) if callable(c) else c
    nxt = [S(j) for j, _ in shots if S(j) > S(i)]
    b = nxt[0] if nxt else TOTAL
    q = (t - S(i)) / max(0.1, b - S(i))
    return c if c is WIDE else (c[0] * (1 + 0.05 * q), c[1], c[2])

def shake(t):
    for i, amt in ((18, 8), (25, 8), (27, 12), (30, 14), (32, 14), (37, 18), (39, 10)):
        if S(i) <= t < S(i) + 0.4:
            d = 1 - (t - S(i)) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    if FREEZE[0] <= t < FREEZE[0] + 0.25:
        d = 1 - (t - FREEZE[0]) / 0.25; return (10 * d * math.sin(t * 90), 0)
    return (0, 0)

HL = {0: {"HONEST.": "b"}, 1: {"MISTAKE.": "y", "WAS.": "b"}, 4: {"BEAUTIFUL?": "y"}, 6: {"REALLY": "y", "BEAUTIFUL?": "y"},
      7: {"OBVIOUSLY.": "y"}, 8: {"HONEST.": "b", "GIRLFRIEND.": "y"}, 9: {"HONEST?": "b"}, 10: {"TRUTH.": "y"},
      12: {"BEAUTIFUL…": "y", "INSTAGRAM": "b", "MODELS.": "b"}, 13: {"EXCUSE": "b", "ME?": "b"}, 14: {"OWN": "y", "WAY!": "y"},
      15: {"OWN": "b"}, 16: {"NATURALLY": "y"}, 17: {"NORMALLY": "b"}, 18: {"WHAT?!": "b"}, 19: {"INSTAGRAM": "y", "MODELS": "y", "COMPARING": "b"},
      20: {"NOBODY!": "b"}, 21: {"INTERROGATION.": "b"}, 22: {"ASK": "y"}, 23: {"PLEASE…": "y"}, 24: {"INSTAGRAM": "y", "CHOOSE?": "b"},
      25: {"YOU!": "b"}, 26: {"HESITATE?": "b"}, 27: {"BREATHING!": "b"}, 28: {"BREATHING": "y", "EXCUSE?": "b"}, 29: {"JESUS": "y"},
      30: {"JESUS": "b"}, 31: {"EX.": "b"}, 32: {"EX?!": "b"}, 33: {"BEAUTIFUL": "y", "WORLD.": "y"}, 34: {"WHY": "y"},
      35: {"LIAR!": "b"}, 36: {"THAT'S": "y", "HONEST.": "b"}, 37: {"SAY?!": "b"}, 38: {"UNIVERSE!": "y"}, 39: {"TOO": "b", "LATE!": "b"},
      40: {"FOOD": "b", "READY.": "y"}}
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
                chip(cv, 540, CAP_Y - 128, "HER" if who == "H" else "HIM", a=0.95, col="ffd23f" if who == "H" else "ffffff", fg="1a1a1a", size=30)
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



DANGER = [(TURN[0], 0.25), (S(15), 0.4), (S(17), 0.55), (S(19), 0.68), (S(24), 0.8), (S(26), 0.9), (S(30), 1.0)]
def danger(cv, t):
    if not (TURN[0] <= t < EXIT[0]):
        return
    a, k = pop(t, TURN[0], 0.35)
    lvl = 0
    for t0, v in DANGER:
        if t >= t0:
            lvl = lvl + (v - lvl) * min(1, (t - t0) / 0.3)
    cv.save(); cv.translate(150, 440); cv.scale(k, k)
    text(cv, "DANGER LEVEL", 110, -40, 34, C("ffffff", a), tf=TF_BLACK, stroke=8, stroke_col=C("000000", a))
    body = skia.RRect.MakeRectXY(skia.Rect(-20, -18, 240, 40), 12, 12)
    cv.drawRRect(body, P(C("141414", a))); cv.drawRRect(body, P(C("ffffff", a), stroke=6))
    col = "ffd21f" if lvl < 0.5 else ("ff8a1f" if lvl < 0.85 else "e8262a")
    if not (lvl > 0.95 and (t * 5) % 1 < 0.35):
        cv.drawRect(skia.Rect(-10, -8, -10 + 240 * lvl, 30), P(C(col, a)))
    lab = "MAX" if lvl > 0.97 else f"{int(lvl * 100)}%"
    text(cv, lab, 300, 26, 44, C("ffffff", a), tf=TF_BLACK, stroke=8, stroke_col=C("000000", a))
    cv.restore()

def hand_mirror(cv, t, gx, rel):
    hx, hy = gx + 84 + rel[0], 1127 - 224 + rel[1]
    cv.drawLine(hx, hy, hx + 10, hy - 60, P(C("e56b9a"), stroke=14)); cv.drawLine(hx, hy, hx + 10, hy - 60, P(INK, stroke=3))
    o = skia.Rect(hx - 40, hy - 160, hx + 60, hy - 50)
    cv.drawOval(o, P(C("e56b9a"))); cv.drawOval(o, P(INK, stroke=6))
    o2 = skia.Rect(hx - 30, hy - 150, hx + 50, hy - 60)
    cv.drawOval(o2, P(C("cfeeff")))
    cv.drawLine(hx - 10, hy - 130, hx + 10, hy - 140, P(C("ffffff"), stroke=6))
    cv.drawCircle(hx, hy, 16, P(C("ffffff"))); cv.drawCircle(hx, hy, 16, P(INK, stroke=5))

def draw_ex_phone(cv, t):
    a0 = S(31) + 0.7 * (E(31) - S(31)); a1 = S(32) + 0.9
    if not (a0 <= t < a1):
        return
    k = ease_out_back(min(1, (t - a0) / 0.3), 1.8); a = min(1, (a1 - t) / 0.2)
    cv.save(); cv.translate(540, 820); cv.rotate(5); cv.scale(k, k)
    body = skia.RRect.MakeRectXY(skia.Rect(-210, -360, 210, 360), 44, 44)
    cv.drawRRect(body, P(C("000000", 0.35 * a), blur=24)); cv.drawRRect(body, P(C("1d1d26", a)))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-186, -330, 186, 330), 26, 26), P(C("2e3440", a)))
    text(cv, "Calling…", 0, -220, 40, C("c9d1e0", a), tf=TF_B)
    cv.drawCircle(0, -70, 90, P(C("8a93a6", a)))
    M.heart(cv, 0, -70, 1.6)
    cv.drawLine(-10, -120, 10, -80, P(C("2e3440", a), stroke=8)); cv.drawLine(10, -80, -8, -40, P(C("2e3440", a), stroke=8))
    text(cv, "MY EX", 0, 90, 64, C("ffffff", a), tf=TF_BLACK)
    for x, col in ((-90, "e8262a"), (90, "3ccf5a")):
        cv.drawCircle(x, 230, 52, P(C(col, a)))
    cv.restore()

def draw_spotlight(cv, t):
    a = min(ss(S(21), S(21) + 0.4, t), 1 - ss(S(31) - 0.2, S(31) + 0.2, t))
    if a <= 0:
        return
    cv.drawRect(skia.Rect(-300, -300, W + 300, H + 300),
                P(0, shader=rad(GX + 20, 1050, 420, [C("05060f", 0), C("05060f", 0.8 * a)], [0.55, 1])))
    cv.drawPath(poly([(GX - 40, 0), (GX + 80, 0), (GX + 330, 1500), (GX - 290, 1500)]), P(C("fff3c0", 0.08 * a)))

TOP = ["When she asks \"Do you think I'm beautiful?\"…", "DON'T BE HONEST"]

def draw_top(cv, t):
    f = skia.Font(TF_B, 44)
    w = max(f.measureText(TOP[0]), skia.Font(TF_BLACK, 48).measureText(TOP[1])) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 286), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    text(cv, TOP[0], 540, 208, 44, C("111111"), tf=TF_B)
    text(cv, TOP[1], 540, 264, 48, C("e74c3c"), tf=TF_BLACK)
    te = E(40) + 0.05
    if t > te:
        a, k = pop(t, te, 0.45)
        chip(cv, 540, 420, "NEVER BE THAT HONEST", a=a, scale=k, col="ffd23f", fg="1a1a1a", size=58)

def draw_rewind(cv, t):
    a0, a1 = T_REW
    if a0 <= t < a1 + 0.9:
        if t < a1:
            cv.drawRect(skia.Rect(0, 0, W, H), P(C("10131c", 0.35)))
            for j in range(9):
                y = (j * 233 + (t * 2400)) % H
                cv.drawRect(skia.Rect(0, y, W, y + 10 + 14 * (j % 3)), P(C("ffffff", 0.18)))
            cv.save(); cv.translate(540, 900)
            for dx in (-70, 10):
                cv.drawPath(poly([(dx + 60, -60), (dx + 60, 60), (dx - 20, 0)]), P(C("ffffff", 0.95)))
            cv.restore()
        tag(cv, t, a0 + 0.1, a1 + 0.9, "15 MINUTES EARLIER", 1100, col="ffffff", size=64)

def render_frame(cv, t):
    ta = at(t)
    z, wx, wy = camera(t)
    sx, sy = shake(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2 + sx, H / 2 + sy); cv.scale(z, z); cv.translate(-wx, -wy)
    CO.draw_room(cv, ta); CO.draw_couch_back(cv); CO.draw_couch_front(cv)
    M.draw_person(cv, ta, guy_state(ta), GX, "guy")
    gx = girl_x(ta)
    if gx < 1400:
        gs = girl_state(ta)
        M.draw_person(cv, ta, gs, gx, "girl")
        if gs.get("mirror"):
            hand_mirror(cv, ta, gx, gs["handR"])
    draw_spotlight(cv, t)
    if t < T_REW[0]:
        cv.drawRect(skia.Rect(-200, -200, W + 200, H + 200), P(C("2a1030", 0.12)))
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    if FREEZE[0] <= t < FREEZE[1]:
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("7a7f8c", 0.45)))
        k = ease_out_back(min(1, (t - FREEZE[0]) / 0.18), 2.5)
        cv.save(); cv.translate(540, 760); cv.rotate(-8); cv.scale(k * 1.0, k * 1.0)
        chip(cv, 0, 0, "WRONG ANSWER", a=1, col="e8262a", fg="ffffff", size=84)
        cv.restore()
    draw_top(cv, t)
    if t < T_REW[0]:
        tag(cv, t, 0.3, S(1), "\"BE HONEST\"", 470, col="ffffff", size=64)
        tag(cv, t, S(1) + 0.1, T_REW[0], "HE WAS.", 470, col="e8262a", fg="ffffff", size=70)
    danger(cv, t)
    tag(cv, t, S(21), S(22) + 0.5, "THE INTERROGATION", 560, col="e8262a", fg="ffffff", size=60)
    tag(cv, t, S(26) + 0.3, S(27), "HESITATION: 0.3 SEC", 560, col="ffd23f", size=56)
    tag(cv, t, NOD[0] + 0.1, S(36), "WAIT A MINUTE…", 560, col="ffffff", size=58)
    draw_ex_phone(cv, t)
    draw_rewind(cv, t)
    if not (FREEZE[0] <= t < FREEZE[1]):
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
