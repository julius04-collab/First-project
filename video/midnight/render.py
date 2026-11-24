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
DING1, EYE = 0.8, 1.6
DING2 = E(3) + 0.15
SCRATCH = E(11) + 0.02
SITUP = (E(11) + 0.1, S(12))
HAND = (E(18) + 0.05, S(19))
ZNAME = (E(20) + 0.05, E(20) + 0.95)
SIL = (E(21), S(22))
PILLOW = (E(25) + 0.05, E(25) + 0.55)
RUN0 = S(27) + 0.1
BLACK = TOTAL - 0.35
ANGRY = (6, 12, 18, 20, 22, 24, 26, 27)

def guy_x(t):
    return GX if t < RUN0 else GX - 420 * (t - RUN0)

def guy_rise(t):
    return ss(E(26) - 0.1, RUN0, t)

def girl_lean(t):
    return lerp(-14, 0, ss(SITUP[0], SITUP[1] - 0.1, t))

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
CLASP_L, CLASP_R = (60, 60), (-60, 60)

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, -0.1), brows=(8, 8), mouth="smirk", grass="mouth", tilt=-8, rise=guy_rise(t), lean=-14)
    st["blink"] = (t % 3.7) < 0.12
    if t < S(1): st.update(eyes="closed", mouth="flat", look=(0.0, 0.3), tilt=-10)                     # sleepy
    if S(1) <= t < HAND[0]: st.update(phone=True, handL=(80, -40), lean=-10, tilt=-4)
    if S(1) <= t < S(3): st.update(eyes="n", mouth="smile", brows=(10, 10), look=(0.4, 0.6))           # nervous smile
    if S(3) <= t < S(5): st.update(eyes="n", mouth="flat", brows=(14, 14), look=(1.0, 0.0))
    if DING2 <= t < S(5): st.update(eyes="wide", brows=(22, 22), mouth="o", handL=(60, -120))          # grabs phone
    if S(5) <= t < S(11): st.update(eyes="n", mouth="smile", brows=(14, 14), look=(1.0, 0.0), tilt=6)  # fake innocent
    if S(9) <= t < E(9): st.update(handR=(130, -80))
    if S(11) <= t < S(18): st.update(sweat=True, mouth="smile", brows=(18, 18))
    if S(12) <= t < S(13): st.update(eyes="wide", mouth="flat")
    if S(15) <= t < E(17): st.update(handR=(130, -80), lean=-6)
    if S(18) <= t < HAND[1]: st.update(eyes="wide", mouth="flat", brows=(22, 22), sweat=True, handL=(150, -60), phone=t < HAND[0] + 0.3)
    if HAND[1] <= t < S(21): st.update(sweat=True, eyes="wide", brows=(24, 24), mouth="o", phone=False, handL=REST_L)   # panicking
    if ZNAME[1] <= t < S(21): st.update(eyes="wide", mouth="o", brows=(26, 26), tilt=0)                # terrified
    if S(21) <= t < S(22): st.update(eyes="n", mouth="smile", brows=(16, 16), sweat=True, handR=(110, -80) if t < E(21) else REST_R)
    if SIL[0] + 0.6 <= t < S(22): st.update(eyes="wide", mouth="o", brows=(26, 26), handR=REST_R)    # realises
    if S(22) <= t < PILLOW[0]: st.update(eyes="wide", brows=(22, 22), mouth="o", sweat=True, handL=UP_L, handR=UP_R, lean=-6)
    if S(23) <= t < E(23): st.update(mouth="smile", handL=(-130, -60), handR=(130, -60))
    if S(25) <= t < E(25): st.update(mouth="smile", handR=(120, -100), eyes="n", brows=(14, 14))
    if PILLOW[1] - 0.05 <= t < PILLOW[1] + 0.4: st.update(eyes="closed", tilt=-18, lean=-18)
    if PILLOW[1] + 0.4 <= t: st.update(eyes="wide", mouth="o", brows=(24, 24), sweat=True, handL=(-60, -220), handR=UP_R, lean=-4)
    if E(26) - 0.1 <= t: st.update(phone=True, handL=(70, -40), look=(-1.0, 0.0), lean=-8)
    if RUN0 <= t: st["walk"] = t * 16
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=CLASP_L, handR=CLASP_R, look=(-1.0, 0.0), brows=(4, 4), mouth="flat", tilt=8, rise=0.0, lean=girl_lean(t))
    st["blink"] = (t % 4.1) < 0.12
    if t < EYE: st.update(eyes="closed", look=(0.0, 0.3), tilt=10)
    if EYE <= t < S(0): st.update(eyes="closed" if (t * 5) % 1 < 0.3 else "n", look=(-1.0, 0.4), brows=(-10, 10))   # one eye open...
    if S(0) <= t: st.update(look=(-1.0, 0.2), brows=(-10, 12), mouth="flat")                                   # suspicious
    if S(2) <= t < E(2) + 0.2: st.update(brows=(-14, 20), tilt=-8)                                            # raised eyebrow
    if S(4) <= t < E(4) + 0.2: st.update(brows=(-18, -18), handR=(-150, -60), tilt=-4)
    if S(6) <= t < E(6) + 0.2: st.update(brows=(-20, -20), eyes="wide", mouth="o")
    if S(8) <= t < S(11): st.update(brows=(-14, 12), tilt=-4)
    if SITUP[0] <= t < S(13): st.update(eyes="wide", mouth="o", brows=(20, 20), tilt=0)                       # shocked, sits up
    if S(12) <= t < E(12) + 0.2: st.update(handL=(-120, -190), handR=(120, -190), brows=(-24, -24))
    if S(14) <= t < HAND[0]: st.update(brows=(-20, -20), tilt=-6)
    if S(16) <= t < E(16): st.update(handR=(-150, -60))
    if S(18) <= t < E(18) + 0.2: st.update(handR=(-180, -40), brows=(-26, -26), tilt=-10)                     # GIVE ME THE PHONE
    if HAND[0] + 0.3 <= t < S(21): st.update(phone=True, handR=(-110, 40), look=(-0.5, 0.6), brows=(-16, -10))
    if S(20) <= t < S(21): st.update(look=(-1.0, 0.0), brows=(-22, -22))
    if SIL[0] <= t < S(22): st.update(eyes="wide", mouth="flat", brows=(10, 10), phone=True, handR=(-110, 40), look=(-1.0, 0.0))
    if S(22) <= t: st.update(handL=(-120, -195 + 12 * math.sin(t * 22)), handR=(120, -195 + 12 * math.cos(t * 22)), brows=(-28, -28), mouth="o", tilt=-10, phone=False)
    if E(22) + 0.3 <= t: st.update(handL=CLASP_L, handR=CLASP_R, mouth="flat", eyes="n")
    if S(24) <= t < E(24) + 0.2: st.update(handR=(-170, -80 + 12 * math.sin(t * 9)), brows=(-26, -26))
    if E(25) - 0.3 <= t < PILLOW[0]: st.update(handR=(60, -200), pillow=True)
    if PILLOW[0] <= t < PILLOW[0] + 0.4: st.update(handR=(-190, -60))
    if S(27) <= t: st.update(handR=(-180, -110), brows=(-28, -28), mouth="o")
    st["amp"] = amp("H", t)
    return st

def draw_bedroom(cv, t):
    cv.drawRect(skia.Rect(-200, -400, W + 200, 1420), P(C("3a3f6a")))
    for i in range(10):
        cv.drawRect(skia.Rect(i * 120 + 50, -400, i * 120 + 62, 1420), P(C("353a62")))
    # window with moon + stars
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(640, 300, 980, 700), 10, 10), P(C("c9cbe0")))
    cv.drawRect(skia.Rect(656, 316, 964, 684), P(C("141a3a")))
    cv.drawCircle(880, 400, 46, P(C("fff6c8"))); cv.drawCircle(860, 390, 46, P(C("141a3a")))
    for (x, y) in ((700, 360), (760, 450), (700, 600), (930, 620), (820, 540)):
        cv.drawCircle(x, y, 4, P(C("ffffff")))
    cv.drawLine(810, 316, 810, 684, P(C("c9cbe0"), stroke=10)); cv.drawLine(656, 500, 964, 500, P(C("c9cbe0"), stroke=10))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(640, 300, 980, 700), 10, 10), P(INK, stroke=7))
    # clock
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(180, 420, 440, 540), 18, 18), P(C("141414"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(180, 420, 440, 540), 18, 18), P(INK, stroke=6))
    text(cv, "12:00", 310, 505, 72, C("ff4a4a"), tf=TF_BLACK)
    cv.drawRect(skia.Rect(-200, 1420, W + 200, H + 200), P(C("4a3a50")))
    # headboard + pillows
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(90, 900, 990, 1360), 50, 50), P(C("7a4a3a"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(90, 900, 990, 1360), 50, 50), P(INK, stroke=7))
    for x in (GX, HX):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 170, 1020, x + 170, 1200), 60, 60), P(C("e8ecf6"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 170, 1020, x + 170, 1200), 60, 60), P(INK, stroke=6))

def draw_blanket(cv, t):
    bl = poly([(110, 1300), (970, 1300), (990, 1560), (90, 1560)])
    cv.drawPath(bl, P(C("5a7fc4"))); cv.drawPath(bl, P(INK, stroke=7))
    for k in range(6):
        cv.drawLine(170 + k * 150, 1320, 150 + k * 150, 1540, P(C("6f93d6"), stroke=10))
    cv.drawRect(skia.Rect(90, 1550, 990, 1610), P(C("7a4a3a"))); cv.drawRect(skia.Rect(90, 1550, 990, 1610), P(INK, stroke=6))

def phone_glow(cv, t, gx, st):
    if not st.get("phone"): return
    lit = (DING1 <= t < DING1 + 2.5) or (DING2 <= t < DING2 + 3.0) or (S(1) <= t < S(20))
    if lit:
        hip = M.SEAT - 18 - 200 * st["rise"]
        hx, hy = gx - 94 + st["handL"][0], hip - 224 + st["handL"][1] - 40
        cv.drawCircle(hx, hy, 160, P(C("8fd3ff", 0.25), blur=40))

def banner(cv, t, t0, dur, title, msg):
    if not (t0 <= t < t0 + dur): return
    q = min(1, (t - t0) / 0.25, (t0 + dur - t) / 0.25)
    y = lerp(240, 470, ease_out_back(q, 1.4)) if t - t0 < 0.25 else 470
    a = q
    r = skia.RRect.MakeRectXY(skia.Rect(70, y - 80, 1010, y + 90), 36, 36)
    cv.drawRRect(r, P(C("000000", 0.35 * a), blur=16)); cv.drawRRect(r, P(C("f4f6fa", 0.97 * a))); cv.drawRRect(r, P(INK, stroke=4))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(100, y - 50, 190, y + 40), 20, 20), P(C("3ccf5a", a)))
    text(cv, "✉", 145, y + 22, 56, C("ffffff", a), tf=TF_BLACK)
    text(cv, title, 220, y - 12, 44, C("141414", a), tf=TF_BLACK, align="l")
    text(cv, msg, 220, y + 52, 46, C("333333", a), tf=TF_B, align="l")
    if "miss" in msg:
        f = skia.Font(TF_B, 46); M.heart(cv, 220 + f.measureText(msg) + 40, y + 36, 0.75)
    text(cv, "now", 970, y - 12, 32, C("8a8f99", a), tf=TF_B, align="r")

def chat(cv, t):
    a0, a1 = S(19) - 0.2, ZNAME[1]
    if not (a0 <= t < a1): return
    k = ease_out_back(min(1, (t - a0) / 0.3), 1.6); a = min(1, (a1 - t) / 0.12)
    zq = ss(ZNAME[0], ZNAME[0] + 0.5, t)        # zoom into the contact name
    cv.save(); cv.translate(540, lerp(820, 1400, zq)); cv.scale(k * lerp(1.3, 2.8, zq), k * lerp(1.3, 2.8, zq))
    body = skia.RRect.MakeRectXY(skia.Rect(-220, -380, 220, 380), 44, 44)
    cv.drawRRect(body, P(C("000000", 0.35 * a), blur=24)); cv.drawRRect(body, P(C("1d1d26", a)))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-196, -350, 196, 350), 26, 26), P(C("f4f6fa", a)))
    cv.drawRect(skia.Rect(-196, -350, 196, -230), P(C("e9ebf2", a)))
    cv.drawCircle(-140, -290, 34, P(C("ff9ec4", a)))
    text(cv, "EX", -80, -272, 56, C("e8262a", a), tf=TF_BLACK, align="l")
    M.heart(cv, 30, -292, 0.8)
    for j, (ln, w) in enumerate((("I miss you so much.", 330), ("I can't stop thinking", 340), ("about you.", 200))):
        y = -170 + j * 70
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-176, y - 40, -176 + w, y + 22), 22, 22), P(C("e2e5ee", a)))
        text(cv, ln, -160, y + 4, 30, C("141414", a), tf=TF_B, align="l")
    text(cv, "12:00 AM", 0, 120, 26, C("8a8f99", a), tf=TF_B)
    cv.restore()

def pillow_fx(cv, t):
    x0, y0, x1, y1 = HX - 60, 880, GX + 30, 920
    if PILLOW[0] <= t < PILLOW[1]:
        q = (t - PILLOW[0]) / (PILLOW[1] - PILLOW[0])
        x, y = lerp(x0, x1, q), lerp(y0, y1, q) - 150 * math.sin(math.pi * q)
        cv.save(); cv.translate(x, y); cv.rotate(-600 * q)
        r = skia.RRect.MakeRectXY(skia.Rect(-80, -55, 80, 55), 30, 30); cv.drawRRect(r, P(C("e8ecf6"))); cv.drawRRect(r, P(INK, stroke=6))
        cv.restore()
    elif PILLOW[1] <= t < PILLOW[1] + 0.45:
        d = t - PILLOW[1]; a = 1 - d / 0.45
        pts = [(x1 + (130 if k % 2 == 0 else 60) * (1 + d) * math.cos(k * math.pi / 8), y1 + (130 if k % 2 == 0 else 60) * (1 + d) * math.sin(k * math.pi / 8)) for k in range(16)]
        cv.drawPath(poly(pts), P(C("ffd21f", a))); cv.drawPath(poly(pts), P(INK, stroke=6))
        text(cv, "BONK!", x1, y1 + 22, 60, C("e8262a", a), tf=TF_BLACK)

def G_CU(t, z=1.85):
    return (z, guy_x(t) + 30, 990 - 190 * guy_rise(t))
def H_CU(t, z=1.85):
    return (z, HX - 20, 1040)
WIDE = (1.0, 560, 1130)
TWO = (1.3, 540, 1060)

def camera(t):
    if t < EYE: return WIDE
    if t < S(0): return (2.0, HX - 20, 1030)
    if DING2 <= t < S(4): return (1.6, GX + 60, 1020)
    if SITUP[0] <= t < S(12): return (1.3, 560, 1060)
    if HAND[0] <= t < S(19): return TWO
    if ZNAME[1] <= t < S(21): return G_CU(t, 2.4)
    if SIL[0] <= t < S(22):
        if t < SIL[0] + 0.6: k = (t - SIL[0]) / 0.6; return H_CU(t, lerp(1.9, 2.3, k))
        k = (t - SIL[0] - 0.6) / (S(22) - SIL[0] - 0.6); return G_CU(t, lerp(1.9, 2.5, k))
    if PILLOW[0] <= t < S(26): return TWO
    if S(26) <= t: return WIDE if t < RUN0 else (1.0, 520, 1130)
    shots = [(0, H_CU), (1, G_CU), (2, lambda t: H_CU(t, 2.1)), (3, G_CU), (4, H_CU), (5, G_CU), (6, lambda t: H_CU(t, 2.2)),
             (7, G_CU), (8, H_CU), (9, G_CU), (10, H_CU), (11, G_CU), (12, lambda t: H_CU(t, 2.1)), (13, G_CU), (14, H_CU),
             (15, G_CU), (16, H_CU), (17, G_CU), (18, lambda t: H_CU(t, 2.3)), (20, lambda t: H_CU(t, 2.2)), (21, lambda t: G_CU(t, 2.2)),
             (22, lambda t: H_CU(t, 2.4)), (23, G_CU), (24, lambda t: H_CU(t, 2.2)), (25, G_CU)]
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
    for a, amt in ((S(6), 10), (S(12), 16), (S(18), 12), (S(22), 20), (S(24), 12), (PILLOW[1], 12)):
        if a <= t < a + 0.4:
            d = 1 - (t - a) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    return (0, 0)

HL = {0: {"WHO": "y", "TEXTED": "y"}, 1: {"NOBODY.": "b"}, 2: {"NOBODY": "y", "NAME?": "b"}, 3: {"NOTIFICATION.": "y"},
      4: {"MISS": "b", "YOU?!": "b"}, 5: {"SOMEBODY.": "y"}, 6: {"SOMEBODY?!": "b"}, 7: {"OLD": "y", "FRIEND.": "y"},
      8: {"MIDNIGHT?": "b"}, 9: {"EMOTIONAL": "y"}, 10: {"WHO": "y"}, 11: {"GIRL": "b"}, 12: {"GIRL?!": "b"}, 13: {"TECHNICALLY,": "y"},
      14: {"FEMALE": "y", "MIDNIGHT?": "b"}, 15: {"NOTHING": "y"}, 16: {"HIDING": "b"}, 17: {"PROTECTING": "y", "PEACE.": "y"},
      18: {"PHONE!": "b"}, 19: {"MISS": "y", "THINKING": "y"}, 20: {"EXPLAIN!": "b"}, 21: {"EX!": "b"}, 22: {"EX?!": "b"},
      23: {"FRIENDS": "y"}, 24: {"MIDNIGHT?!": "b"}, 25: {"MOVED": "y", "ON!": "y"}, 26: {"MISSED": "b"}, 27: {"NOTIFICATIONS!": "b"}}
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





TOP = ["When she asks who texted you at midnight…", "WHO IS SHE?!"]

def draw_top(cv, t):
    f = skia.Font(TF_B, 44)
    w = max(f.measureText(TOP[0]), skia.Font(TF_BLACK, 48).measureText(TOP[1])) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 286), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    text(cv, TOP[0], 540, 208, 44, C("111111"), tf=TF_B)
    text(cv, TOP[1], 540, 264, 48, C("e74c3c"), tf=TF_BLACK)

def render_frame(cv, t):
    z, wx, wy = camera(t)
    sx, sy = shake(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2 + sx, H / 2 + sy); cv.scale(z, z); cv.translate(-wx, -wy)
    draw_bedroom(cv, t)
    gs = girl_state(t)
    M.draw_person(cv, t, gs, HX, "girl")
    if gs.get("pillow"):
        cv.save(); cv.translate(HX + 84 + 60, M.SEAT - 18 - 224 - 200 - 40); r = skia.RRect.MakeRectXY(skia.Rect(-80, -55, 80, 55), 30, 30)
        cv.drawRRect(r, P(C("e8ecf6"))); cv.drawRRect(r, P(INK, stroke=6)); cv.restore()
    us = guy_state(t); ux = guy_x(t)
    if ux > -300:
        M.draw_person(cv, t, us, ux, "guy")
        phone_glow(cv, t, ux, us)
    draw_blanket(cv, t)
    pillow_fx(cv, t)
    cv.drawRect(skia.Rect(-300, -600, W + 300, H + 300), P(C("0a0f2a", 0.28)))     # night tint
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("05060f", 0.45)], [0.55, 1])))
    draw_top(cv, t)
    banner(cv, t, DING1, 2.3, "Unknown Contact", "1 new message")
    banner(cv, t, DING2, 3.0, "Unknown Contact", "I miss you")
    chat(cv, t)
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
