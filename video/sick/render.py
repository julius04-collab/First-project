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
_src = open(os.path.join(HERE, "..", "mia", "render.py")).read().replace('"7d8494"', '"f2c230"').replace('"e04444"', '"3a7bd5"').replace('"c03030"', '"2a5fb0"')
M2 = importlib.util.module_from_spec(importlib.util.spec_from_loader("mia2", loader=None)); M2.__dict__["__file__"] = os.path.join(HERE, "..", "mia", "render.py")
exec(compile(_src, "mia2", "exec"), M2.__dict__)

BEDX = 540.0
JUMP = (E(7) + 0.25, S(8))
TRANS = (E(8) + 0.25, S(9) - 0.15)
GS = E(11) + 0.1                       # goal sequence start
GOAL_T = GS + 1.45                     # ball hits the net
FREEZE = (E(13) + 0.05, S(14) - 0.05)
FREEZE2 = (S(27) + 0.75, TOTAL)
BLACK = TOTAL - 0.35
ANGRY = (5, 8, 12, 13, 14, 19, 26, 27)
KX, GX, FX0, FX1, HXF = 200.0, 920.0, 1300.0, 1130.0, 560.0
FW = 1700.0

def field(t):
    return t >= TRANS[0] + 0.3

def at(t):
    if FREEZE[0] <= t < FREEZE[1]:
        return FREEZE[0]
    if t >= FREEZE2[0]:
        return FREEZE2[0]
    return t

def f1_x(t):
    return lerp(FX0, FX1, ss(S(16), S(16) + 1.2, t))

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
HIPS_L, HIPS_R = (-18, 168), (18, 168)
CROSS_L, CROSS_R = (60, 60), (-60, 60)

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.1), brows=(8, 8), mouth="smirk", grass="mouth", tilt=0, rise=1.0)
    st["blink"] = (t % 3.7) < 0.12
    if not field(t):
        st.update(rise=0.0, lean=-8, look=(0.2, 0.3))
        if t < S(0):     # chilling, phone rings
            st.update(phone=True, handL=(90, 60), look=(0.4, 0.7), mouth="smile")
        elif t < E(7) + 0.2:
            sick = (t // 1.6) % 2 == 0
            st.update(phone=True, handL=(70, -150), handR=(-80, -150), eyes="closed" if (t % 1.3) < 0.5 else "n", brows=(14, 14), mouth="flat", tilt=10, look=(0.0, 0.5))
            if S(0) <= t < E(0):
                st.update(handR=REST_R, eyes="n", look=(0.0, 0.0), mouth="smile", tilt=0, brows=(8, 8))
            if E(0) <= t < S(1):           # cough cough
                c = (t - E(0)) / (S(1) - E(0))
                st.update(lean=-8 + 8 * math.sin(c * 25), mouth="o", eyes="closed")
            if S(5) <= t < E(5) + 0.05:
                st.update(eyes="wide", brows=(22, 22), mouth="o", handR=(120, -60), tilt=0, look=(0.0, 0.0))
        elif t < JUMP[0]:
            st.update(handL=REST_L, look=(0.0, 0.0), eyes="n", brows=(16, 16), mouth="smirk", tilt=0)
        else:
            k = ss(JUMP[0], JUMP[0] + 0.25, t)
            st.update(rise=k, lean=0, bob=120 * math.sin(math.pi * min(1, (t - JUMP[0]) / 0.5)) if t < JUMP[0] + 0.5 else 0,
                      handL=UP_L, handR=UP_R, eyes="happy", mouth="smile", brows=(18, 18), look=(0.0, 0.0))
            if S(8) <= t:
                pump = math.sin((t - S(8)) * 14)
                st.update(handL=(-120, -190 + 30 * pump), handR=(130, -60 + 40 * pump), bob=20 * abs(pump))
        st["amp"] = amp("G", t)
        return st
    # ---- football field
    st.update(look=(1.0, 0.0), mouth="smile", brows=(10, 10))
    if t < GS:
        w = math.sin(t * 3)
        st.update(look=(-1.0, 0.1), handL=(-120, 40), handR=(120, 40), walk=t * 5 if abs(w) > 0.5 else None)
        if S(10) <= t < E(10):
            st.update(handR=(120, -120), mouth="smile", brows=(16, 16), eyes="happy" if amp("G", t) < 0.05 else "n")
    elif t < S(12):
        q = t - GS
        st.update(look=(-1.0, 0.1) if q < 0.7 else (1.0, 0.0), brows=(-6, -6), mouth="flat", handL=(-140, 40), handR=(140, 40))
        if 0.7 <= q < 0.95:
            st.update(walk=(q - 0.7) * 20, lean=-10)
        if q >= 1.45:
            st.update(eyes="wide", mouth="o", brows=(20, 20))
    elif t < S(13):
        h = abs(math.sin((t - S(12)) * 9))
        st.update(handL=UP_L, handR=UP_R, bob=50 * h, eyes="happy", mouth="smile", brows=(20, 20), look=(0.0, 0.0))
    elif t < S(14):
        st.update(handL=UP_L, handR=UP_R, eyes="wide", mouth="o", brows=(24, 24), look=(-1.0, 0.0), sweat=True)
    else:
        st.update(look=(-1.0, 0.0), eyes="wide", mouth="flat", brows=(20, 20), sweat=True)
        if S(16) <= t < E(16) + 0.1:
            st.update(handL=(-140, -60), handR=(140, -60), eyes="n")
        if S(18) <= t < E(18) + 0.1:
            st.update(handL=(-90, -150), handR=(-40, -150), eyes="closed", mouth="flat", tilt=8)      # "recovering"
        if S(20) <= t < E(20) + 0.1:
            st.update(handR=(110, -150), mouth="smile", eyes="n", brows=(14, 4))
        if E(21) - 0.2 <= t < S(22):
            st.update(look=(1.0, 0.0), brows=(-22, -22), eyes="n", mouth="flat", sweat=False)       # glare at friend
        if S(22) <= t:
            st.update(eyes="n", mouth="flat", brows=(16, 16))
        if S(23) <= t < E(23) + 0.2:
            st.update(eyes="wide", mouth="o", brows=(22, 22))
        if S(24) <= t:
            st.update(eyes="n", brows=(14, 14), mouth="flat", tilt=6)
        if S(25) <= t < S(26):
            st.update(look=(0.0, 0.0), brows=(10, 10), mouth="flat", tilt=-6)
        if S(26) <= t:
            st.update(eyes="wide", brows=(24, 24), mouth="o", sweat=True, look=(-1.0, 0.0), tilt=0)
        if S(27) <= t:
            st.update(eyes="n", mouth="smile", handL=(-60, 40), handR=(60, 40), brows=(18, 18), look=(0.0, 0.0), tilt=8)
    st["amp"] = amp("G", t)
    return st

def girl_state(t, pip=False):
    st = dict(handL=CROSS_L, handR=CROSS_R, look=(-1.0, 0.0), brows=(-14, -14), mouth="flat", tilt=-4, rise=0.0 if pip else 1.0)
    st["blink"] = (t % 4.1) < 0.12
    if pip:
        st.update(phone=True, handR=(-70, -160), handL=REST_L, look=(-0.4, 0.0), brows=(10, 10), mouth="smile", tilt=6)
        if S(2) <= t:
            st.update(brows=(16, 16), mouth="flat", tilt=-4)
        if S(4) <= t:
            st.update(brows=(20, 20), mouth="o")
        if S(7) <= t:
            st.update(brows=(12, 12), mouth="smile", tilt=6)
        st["amp"] = amp("H", t)
        return st
    if t < S(15):
        st.update(brows=(-22, -22), tilt=-8)
    elif t < S(22):
        st.update(brows=(-12, 18), tilt=-6)                              # one eyebrow raised
        if S(17) <= t: st.update(brows=(-18, -2), handR=(-160, -70 + 12 * math.sin(t * 9)))
        if S(19) <= t < E(19) + 0.3:
            st.update(handL=(-120, -190 + 10 * math.sin(t * 20)), handR=(120, -190 + 10 * math.cos(t * 20)), brows=(-24, -24), tilt=-10)
        if S(20) <= t: st.update(handL=CROSS_L, handR=CROSS_R, brows=(-16, 14))
        if S(21) <= t: st.update(look=(1.0, -0.1), brows=(-6, 16))
    else:
        st.update(handL=HIPS_L, handR=HIPS_R, mouth="smile", eyes="n", brows=(-6, 10), tilt=8)   # satisfied
        if S(22) <= t < E(22): st.update(handR=(-160, -60))
        if S(24) <= t < E(24) + 0.3: st.update(eyes="happy" if amp("H", t) < 0.05 else "n")
        if S(26) <= t:
            st.update(handL=(-120, -190), handR=(120, -190), brows=(-26, -26), mouth="flat", tilt=-10)
        if S(27) <= t:
            st.update(handL=HIPS_L, handR=HIPS_R, brows=(-16, 14), tilt=-6)
    st["amp"] = amp("H", t)
    return st

def k_state(t):        # friend 2 (laughs)
    st = dict(handL=(-120, 40), handR=(120, 40), look=(1.0, 0.0), brows=(8, 8), mouth="smile", tilt=0, rise=1.0)
    st["blink"] = (t % 4.4) < 0.12
    if S(11) <= t < E(11) + 0.4 or t >= S(28):
        h = math.sin(t * 16)
        st.update(eyes="happy", mouth="o" if h > 0 else "smile", handL=(-60, 40), handR=(60, 40), lean=-8 * abs(h), tilt=8 * h)
    elif S(13) <= t < S(28):
        st.update(eyes="wide", mouth="o", brows=(18, 18), handL=REST_L, handR=REST_R)
        if S(22) <= t: st.update(eyes="n", mouth="smirk", brows=(10, 10))
    elif GS <= t < GS + 0.7:
        st.update(walk=(t - GS) * 14 if t < GS + 0.3 else None, lean=-6)
    st["amp"] = amp("K", t)
    return st

def f_state(t):        # friend 1 (goalkeeper; drawn mirrored so +look = toward the left)
    st = dict(handL=(-120, -40), handR=(120, -40), look=(1.0, 0.0), brows=(10, 10), mouth="flat", tilt=0, rise=1.0)
    st["blink"] = (t % 3.9) < 0.12
    if S(9) <= t < E(9) + 0.1:
        st.update(handR=(150, -120), brows=(-6, 16), mouth="o")
    if GS + 0.9 <= t < GS + 2.2:     # dives, misses
        k = ss(GS + 0.9, GS + 1.3, t)
        st.update(lean=-28 * k, handL=(-170, -150), handR=(170, -150), eyes="wide", mouth="o", bob=-60 * k)
    if S(13) <= t:
        st.update(handL=REST_L, handR=REST_R, eyes="wide", brows=(18, 18), mouth="flat")
    if S(16) <= t < S(16) + 1.2:
        st["walk"] = t * 8
    if S(19) <= t:
        st.update(brows=(16, 2), tilt=8)
    if S(21) <= t < E(21) + 0.2:
        st.update(lean=8, handR=(60, -170), look=(1.0, 0.0), brows=(14, 14), mouth="o")   # whisper
    if E(21) + 0.2 <= t < S(22):
        st.update(eyes="wide", brows=(22, 22), mouth="flat", sweat=True)
    if t >= S(28):
        h = math.sin(t * 15)
        st.update(eyes="happy", mouth="o" if h > 0 else "smile", handL=(-60, 40), handR=(60, 40), lean=-8 * abs(h), tilt=-8 * h)
    st["amp"] = amp("F", t)
    return st

def ball_pos(t):
    if t < GS:
        per = 1.4; c = int((t - TRANS[0]) // per); q = ((t - TRANS[0]) % per) / per
        a, b = (KX + 60, GX - 60) if c % 2 == 0 else (GX - 60, KX + 60)
        return (lerp(a, b, q), 1575 - 140 * math.sin(math.pi * q))
    q = t - GS
    if q < 0.7:
        return (lerp(KX + 60, GX + 40, q / 0.7), 1575)
    if q < 0.95:
        return (GX + 70, 1575)
    if q < 1.45:
        k = (q - 0.95) / 0.5
        return (lerp(GX + 70, 1480, k), lerp(1575, 1330, k) - 160 * math.sin(math.pi * k))
    d = q - 1.45
    return (1480 + 25 * min(1, d * 4), min(1575, 1330 + 600 * d * d))

def draw_field(cv, t):
    cv.drawRect(skia.Rect(-200, -900, FW + 200, 900), P(0, shader=lin(0, -600, 0, 900, [C("5aa9e8"), C("bfe3ff")])))
    cv.drawCircle(1350, 330, 70, P(C("fff2b0")))
    # stands
    cv.drawRect(skia.Rect(-200, 640, FW + 200, 1000), P(C("6b7280"))); cv.drawRect(skia.Rect(-200, 640, FW + 200, 1000), P(INK, stroke=6))
    cheer = 1.0 + 2.5 * max(0, 1 - abs(t - GOAL_T - 0.8) / 1.6)
    cols = ["e8424a", "3a7bd5", "f2c230", "ffffff", "3ccf5a", "ff8a3d"]
    for row in range(4):
        y = 690 + row * 75
        for i in range(36):
            x = -150 + i * 58 + (row % 2) * 29
            bob = 6 * cheer * math.sin(t * 7 + i * 1.7 + row) if cheer > 1.2 else 2 * math.sin(t * 2 + i)
            cv.drawCircle(x, y + bob, 18, P(C(cols[(i * 7 + row * 3) % 6])))
            cv.drawCircle(x, y - 26 + bob, 13, P(C("f3d9b8")))
    cv.drawRect(skia.Rect(-200, 990, FW + 200, 1010), P(C("ffffff")))
    # pitch
    cv.drawRect(skia.Rect(-200, 1000, FW + 200, 2900), P(C("4fa84a")))
    for i in range(-2, 15):
        cv.drawRect(skia.Rect(i * 140, 1000, i * 140 + 70, 2900), P(C("5cb757")))
    cv.drawLine(-200, 1520, FW + 200, 1520, P(C("ffffff", 0.7), stroke=6))
    # goal (right)
    gx0, gx1, gy0, gy1 = 1420, 1560, 1250, 1600
    bulge = 30 * max(0, 1 - abs(t - GOAL_T) / 0.5) if t >= GOAL_T - 0.05 else 0
    for k in range(9):
        y = gy0 + k * (gy1 - gy0) / 8
        cv.drawLine(gx0, y, gx1 + bulge * math.sin(math.pi * k / 8), y, P(C("ffffff", 0.55), stroke=3))
    for k in range(6):
        x = gx0 + k * (gx1 - gx0) / 5
        cv.drawLine(x, gy0, x + bulge * (k / 5), gy1, P(C("ffffff", 0.55), stroke=3))
    cv.drawLine(gx0, gy0, gx0, gy1, P(INK, stroke=22)); cv.drawLine(gx0, gy0, gx0, gy1, P(C("ffffff"), stroke=14))
    cv.drawLine(gx0, gy0, gx1 + 20, gy0, P(INK, stroke=22)); cv.drawLine(gx0, gy0, gx1 + 20, gy0, P(C("ffffff"), stroke=14))

def draw_ball(cv, x, y, t):
    cv.drawOval(skia.Rect(x - 26, 1592, x + 26, 1604), P(C("000000", 0.25)))
    cv.drawCircle(x, y, 26, P(C("ffffff"))); cv.drawCircle(x, y, 26, P(INK, stroke=5))
    cv.save(); cv.translate(x, y); cv.rotate(x * 2)
    cv.drawPath(poly([(0, -11), (10, -3), (6, 9), (-6, 9), (-10, -3)]), P(INK))
    cv.restore()

def draw_pip(cv, t):
    a0, a1 = S(0) - 0.4, E(7) + 0.35
    if not (a0 <= t < a1):
        return
    k = ease_out_back(min(1, (t - a0) / 0.3), 1.8) * min(1, (a1 - t) / 0.2)
    cx, cy, r = 820, 560, 170
    cv.save(); cv.translate(cx, cy); cv.scale(k, k)
    cv.drawCircle(0, 0, r + 10, P(C("000000", 0.3), blur=12))
    path = skia.Path(); path.addCircle(0, 0, r)
    cv.save(); cv.clipPath(path, doAntiAlias=True)
    cv.drawRect(skia.Rect(-r, -r, r, r), P(0, shader=lin(0, -r, 0, r, [C("ffd6e6"), C("f7a8c8")])))
    cv.scale(0.62, 0.62); cv.translate(0, -945 + 60)
    M.draw_person(cv, t, girl_state(t, pip=True), 0, "girl")
    cv.restore()
    cv.drawCircle(0, 0, r, P(C("ffffff"), stroke=12)); cv.drawCircle(0, 0, r + 6, P(INK, stroke=4))
    chip(cv, 0, r + 20, "BABY", a=1, col="ff7aa8", fg="141414", size=40)
    cv.restore()

def G_CU(t, z=1.85):
    us = guy_state(t); r = us["rise"]; x = BEDX if not field(t) else GX
    return (z, x + 30, 990 - 190 * r)
def H_CU(t, z=1.85):
    return (z, HXF - 10, 805)
def F_CU(t, z=1.85):
    return (z, f1_x(t) - 30, 805)
BED_MED = (1.25, BEDX, 1050)
WIDE_F = (0.8, 850, 1150)

def camera(t):
    if not field(t):
        if t < S(0): return BED_MED
        if t < JUMP[0]:
            k = (t - S(0)) / (JUMP[0] - S(0)); return (lerp(1.6, 2.1, k), BEDX + 30, 990)
        k = ss(JUMP[0], JUMP[0] + 0.15, t)
        return (lerp(1.4, 1.9, k), BEDX + 30, lerp(980, 820, k))
    if t < S(9):
        return WIDE_F
    if FREEZE[0] <= t < FREEZE[1]:
        k = ss(FREEZE[0], FREEZE[0] + 0.12, t); return G_CU(FREEZE[0], lerp(1.9, 2.3, k))
    if t >= FREEZE2[0]:
        k = ss(FREEZE2[0], FREEZE2[0] + 0.12, t); return G_CU(FREEZE2[0], lerp(1.9, 2.4, k))
    if GS <= t < S(12):
        return WIDE_F
    if S(13) <= t < E(13):   # dramatic close-up as she appears
        k = (t - S(13)) / (E(13) - S(13)); return H_CU(t, lerp(1.8, 2.3, k))
    if E(21) <= t < S(22):
        return G_CU(t, 2.2)
    shots = [(9, F_CU), (10, G_CU), (11, (1.6, KX + 40, 820)), (12, (1.25, GX - 20, 980)), (14, lambda t: G_CU(t, 2.1)),
             (15, H_CU), (16, G_CU), (17, H_CU), (18, G_CU), (19, lambda t: H_CU(t, 2.2)), (20, G_CU), (21, (1.45, 1030, 900)),
             (22, (0.95, 760, 1100)), (23, G_CU), (24, H_CU), (25, lambda t: G_CU(t, 2.2)), (26, lambda t: H_CU(t, 2.4)), (27, G_CU)]
    cur = None
    for i, c in shots:
        if S(i) <= t:
            cur = (i, c)
    i, c = cur
    c = c(t) if callable(c) else c
    nx = [S(j) for j, _ in shots if S(j) > S(i)]
    b = nx[0] if nx else TOTAL
    q = (t - S(i)) / max(0.1, b - S(i))
    return (c[0] * (1 + 0.05 * q), c[1], c[2])

def shake(t):
    for i, amt in ((5, 10), (12, 10), (13, 14), (14, 12), (19, 12), (26, 16)):
        if S(i) <= t < S(i) + 0.4:
            d = 1 - (t - S(i)) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    if GOAL_T <= t < GOAL_T + 0.3:
        d = 1 - (t - GOAL_T) / 0.3; return (8 * d * math.sin(t * 90), 6 * d * math.cos(t * 70))
    return (0, 0)

HL = {0: {"READY?": "y", "30": "b", "MINUTES!": "b"}, 1: {"CAN'T": "y", "MAKE": "y"}, 2: {"WRONG?": "y"},
      3: {"SERIOUSLY": "y", "SICK.": "b", "BARELY": "y", "MOVE.": "y"}, 4: {"COME": "y", "OVER?": "y"}, 5: {"NO!": "b"},
      6: {"CATCH": "y"}, 7: {"REST.": "y"}, 8: {"FOOTBALL": "b", "TIME!": "b"}, 9: {"SICK!": "b"}, 10: {"RECOVERY!": "b"},
      11: {"CRAZY,": "y"}, 12: {"GOOOOAL!": "b", "SICK": "y"}, 13: {"APPARENTLY!": "b"}, 14: {"BABY?!": "b"},
      15: {"HOSPITAL": "b"}, 16: {"EXPLAIN!": "y"}, 17: {"BARELY": "y", "MOVE!": "b"}, 18: {"RECOVERING!": "b"},
      19: {"FOOTBALL?!": "b"}, 20: {"DOCTOR'S": "b", "ORDERS!": "b"}, 21: {"DOCTOR?": "b"}, 22: {"FOOTBALL,": "y", "PAY": "b", "DINNER!": "b"},
      23: {"WHAT?": "y"}, 24: {"DESSERT": "b"}, 25: {"STAYED": "y", "SICK.": "y"}, 26: {"SAY?!": "b"}, 27: {"STILL": "b", "SICK,": "b"},
      28: {}, 29: {}}
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
            if who in ("G", "H", "F", "K") and not (i >= 28):
                chip(cv, 540, CAP_Y - 128, {"H": "HER", "G": "HIM", "F": "FRIEND", "K": "FRIEND"}[who], a=0.95, col="ffd23f" if who == "H" else "ffffff", fg="1a1a1a", size=30)
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





TOP = ["When he fakes being sick to skip date night…", "SHE FOUND HIM"]

def draw_top(cv, t):
    f = skia.Font(TF_B, 44)
    w = max(f.measureText(TOP[0]), skia.Font(TF_BLACK, 48).measureText(TOP[1])) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 286), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    text(cv, TOP[0], 540, 208, 44, C("111111"), tf=TF_B)
    text(cv, TOP[1], 540, 264, 48, C("e74c3c"), tf=TF_BLACK)

def bubble(cv, t, t0, t1, label, x, y, col="ffffff", fg="141414", size=70, rot=-6):
    if t0 <= t < t1:
        a, k = pop(t, t0, 0.3); a = min(a, (t1 - t) / 0.15)
        cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(k, k)
        chip(cv, 0, 0, label, a=a, col=col, fg=fg, size=size)
        cv.restore()

def render_frame(cv, t):
    ta = at(t)
    z, wx, wy = camera(t)
    sx, sy = shake(t)
    if field(ta):
        wy = min(wy, 2900 - H / 2 / z); wx = min(max(wx, W / 2 / z - 200), FW + 200 - W / 2 / z)
    else:
        wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2 + sx, H / 2 + sy); cv.scale(z, z); cv.translate(-wx, -wy)
    if not field(ta):
        CO.draw_room(cv, ta); CO.draw_couch_back(cv); CO.draw_couch_front(cv)
        M.draw_person(cv, ta, guy_state(ta), BEDX, "guy")
    else:
        draw_field(cv, ta)
        M2.draw_person(cv, ta, k_state(ta), KX, "friend")
        cv.save(); cv.translate(f1_x(ta), 0); cv.scale(-1, 1)
        M.draw_person(cv, ta, f_state(ta), 0, "friend")
        cv.restore()
        if ta >= S(13) - 0.05:
            M.draw_person(cv, ta, girl_state(ta), HXF, "girl")
        M.draw_person(cv, ta, guy_state(ta), GX, "guy")
        bx, by = ball_pos(ta); draw_ball(cv, bx, by, ta)
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.3)], [0.6, 1])))
    if not field(t):
        draw_pip(cv, t)
    if FREEZE[0] <= t < FREEZE[1]:
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("7a7f8c", 0.4)))
        bubble(cv, t, FREEZE[0], FREEZE[1], "CAUGHT", 540, 760, col="e8262a", fg="ffffff", size=90)
    if t >= FREEZE2[0]:
        fl = max(0, 1 - (t - FREEZE2[0]) / 0.15)
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("ffffff", 0.6 * fl)))
    # transition wipe
    if TRANS[0] <= t < TRANS[0] + 0.6:
        q = (t - TRANS[0]) / 0.6
        x = lerp(-W, W, q)
        cv.drawRect(skia.Rect(x, 0, x + W, H), P(C("ffd21f")))
    draw_top(cv, t)
    tag(cv, t, 0.2, S(0), "DATE NIGHT IN 30 MINS", 470, col="ff7aa8", size=54)
    tag(cv, t, S(1), E(3) + 0.3, "OSCAR-WINNING PERFORMANCE", 470, col="ffd23f", size=50)
    tag(cv, t, TRANS[0] + 0.3, S(9) + 0.9, "MEANWHILE… AT THE FIELD", 470, col="ffffff", size=56)
    bubble(cv, t, GOAL_T, S(13) - 0.2, "GOAL!", 540, 600, col="3ccf5a", fg="141414", size=110)
    tag(cv, t, S(22) + 1.2, S(25), "DINNER + DESSERT: ON HIM", 470, col="3ccf5a", fg="141414", size=52)
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
