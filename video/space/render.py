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
WW, OFF = 2400.0, 1280.0
HX = OFF + 740           # her seat
SEAT2 = OFF + 330        # seat beside her
GX0 = 1450.0
LS0, LS1 = 1135.0, 640.0
T_GRAB = E(14) + 0.1
T_PUSHEND = S(17) - 1.3
T_SAT = S(17) - 0.75
T_WALK2 = E(32) + 0.1
T_SIT2 = T_WALK2 + 2.0
SILENCE = (E(33), S(34))
FREEZE = (E(26) + 0.02, S(27) - 0.05)
PILLOW = (E(35) + 0.1, E(35) + 0.75)
FREEZE2 = (S(36) + 0.35, E(36) + 0.6)
BLACK = FREEZE2[1]
ANGRY = (4, 8, 15, 22, 24, 26, 29, 34, 36)

def at(t):
    if FREEZE[0] <= t < FREEZE[1]:
        return FREEZE[0]
    if t >= FREEZE2[0]:
        return FREEZE2[0]
    return t

def ls_x(t):
    return lerp(LS0, LS1, ss(T_GRAB + 0.3, T_PUSHEND, t))

def guy_x(t):
    if t < T_GRAB:
        return lerp(GX0, LS0 + 250, ss(T_GRAB - 0.0, T_GRAB + 0.3, t)) if t >= T_GRAB else GX0
    if t < T_PUSHEND:
        return lerp(GX0, LS0 + 250, ss(T_GRAB, T_GRAB + 0.3, t)) if t < T_GRAB + 0.3 else ls_x(t) + 250
    if t < T_WALK2:
        return lerp(LS1 + 250, LS1, ss(T_PUSHEND, T_SAT, t))
    if t < S(36):
        return lerp(LS1, SEAT2, ss(T_WALK2, T_SIT2, t))
    return SEAT2 - 1300 * (t - S(36))

def guy_rise(t):
    r = 1.0
    if T_SAT <= t < S(19) + 0.5:
        r = 1 - ss(T_SAT, T_SAT + 0.6, t) + ss(S(19), S(19) + 0.5, t)
    if T_SIT2 <= t < S(34) + 0.25:
        r = 1 - ss(T_SIT2, T_SIT2 + 0.6, t) + ss(S(34), S(34) + 0.25, t)
    if PILLOW[0] + 0.15 <= t < PILLOW[1] + 0.4:
        r = min(r, 1 - 0.45 * min(ss(PILLOW[0] + 0.15, PILLOW[0] + 0.3, t), 1 - ss(PILLOW[1] + 0.15, PILLOW[1] + 0.4, t)))
    return r

def moving(t):
    return abs(guy_x(t + 0.03) - guy_x(t - 0.03)) > 2

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
CROSS_L, CROSS_R = (60, 60), (-60, 60)

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.1), brows=(10, 10), mouth="flat", grass="mouth", tilt=0)
    st["blink"] = (t % 3.7) < 0.12
    st["rise"] = guy_rise(t)
    if S(1) <= t < E(1) + 0.2:
        st.update(handL=(-140, -20), handR=(140, -20), brows=(16, 16))
    if S(3) <= t < E(3) + 0.1:
        st.update(handR=(130, -50), mouth="smile", brows=(12, 12), tilt=6)
    if S(5) <= t < E(5) + 0.1:
        st.update(handR=(110, -150), mouth="smirk", brows=(14, 4), tilt=6)
    if E(6) <= t < S(7):
        st.update(look=(0.3, -0.9), brows=(16, 2), tilt=-6)
    if S(7) <= t < E(7) + 0.2:
        st.update(brows=(18, 4), tilt=8)
    if S(9) <= t < E(9) + 0.3:
        st.update(mouth="smile", handR=(110, -120))
    if S(10) <= t < E(12) + 0.2:
        w = 0.5 + 0.5 * math.sin((t - S(10)) * 2)
        st.update(handL=(-60 - 80 * w, -40), handR=(60 + 80 * w, -40), brows=(12, 12), mouth="flat")
    if S(14) <= t < E(14):
        st.update(brows=(4, 4), handR=(120, -60))
    if T_GRAB <= t < T_PUSHEND:
        st.update(look=(-1.0, 0.1), handL=(-160, 40), handR=(-40, 40), brows=(-2, -2), tilt=-6)
    if T_PUSHEND <= t < S(19):
        st.update(look=(1.0, 0.0), brows=(10, 10), mouth="smile")
        if T_SAT + 0.6 <= t:
            st.update(handL=REST_L, handR=REST_R)
    if S(19) <= t < S(21):
        st.update(handR=(100, -170), mouth="smile", brows=(16, 16), eyes="wide" if t < S(19) + 0.4 else "n")
    if S(21) <= t < FREEZE[1]:
        st.update(phone=True, handL=(100, 60), look=(0.4, 0.7), brows=(6, 6), mouth="flat")
        if S(23) <= t < E(23):
            st["look"] = (1.0, 0.0)
        if S(25) <= t:
            st.update(look=(1.0, 0.0), handR=(-70, -30), mouth="smile", brows=(12, 12))
        if FREEZE[0] <= t:
            st.update(eyes="wide", mouth="o", brows=(20, 20))
    if FREEZE[1] <= t < T_WALK2:
        st.update(look=(1.0, 0.0), brows=(14, 14))
        if S(27) <= t < S(28):
            st.update(mouth="o", eyes="wide", brows=(20, 20))
        if S(28) <= t < S(29):
            st.update(brows=(14, 4), tilt=8)
        if S(30) <= t:
            st.update(mouth="smile", handR=(110, -120) if t < E(30) else REST_R)
        if S(31) <= t:
            st.update(look=(1.0, 0.15 * math.sin((t - S(31)) * 4)), mouth="flat", brows=(12, 12))
        if S(32) <= t:
            st.update(mouth="smile", eyes="happy" if amp("G", t) < 0.05 else "n")
    if T_WALK2 <= t < S(34):
        st.update(look=(1.0, 0.0), mouth="smile", brows=(10, 10))
        if T_SIT2 + 0.6 <= t:
            st.update(handR=(170, -60))
        if S(33) <= t:
            st.update(brows=(16, 16), eyes="happy" if amp("G", t) < 0.05 else "n")
        if SILENCE[0] + 1.0 <= t:
            st.update(eyes="wide", brows=(18, 18), mouth="flat", sweat=True)
    if S(34) <= t:
        st.update(eyes="wide", brows=(22, 22), mouth="o", sweat=True, look=(1.0, 0.0))
        if S(35) <= t:
            st.update(handL=UP_L, handR=UP_R)
        if PILLOW[0] + 0.1 <= t < PILLOW[1] + 0.3:
            st.update(handL=(-60, -230), handR=(60, -230), eyes="closed")
        if S(36) <= t:
            st.update(look=(0.0, 0.0), handL=UP_L, handR=UP_R, eyes="wide", mouth="o", tilt=-8)
    if moving(t):
        st["walk"] = t * (14 if t >= S(36) else 9)
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=CROSS_L, handR=CROSS_R, look=(-1.0, 0.0), brows=(-14, -14), mouth="flat", tilt=-4)
    st["blink"] = (t % 4.1) < 0.12
    rant = lambda: st.update(handR=(-160, -70 + 14 * math.sin(t * 9)), brows=(-18, -18))
    furious = lambda: st.update(handL=(-120, -190 + 10 * math.sin(t * 20)), handR=(120, -190 + 10 * math.cos(t * 20)), brows=(-24, -24), tilt=-8)
    if S(0) <= t < E(0): rant()
    if S(2) <= t < E(2): rant()
    if S(4) <= t < E(4) + 0.3: furious()
    if E(5) <= t < S(6): st.update(brows=(-22, -22), eyes="n", tilt=-8)
    if S(6) <= t < S(8): st.update(look=(1.0, 0.1), tilt=10, brows=(-12, -12))
    if S(8) <= t < E(8) + 0.2: furious()
    if S(11) <= t < S(12): st.update(brows=(-6, 14), tilt=6)
    if S(13) <= t < E(13) + 0.2: st.update(brows=(-14, 10), handR=(-140, -40))
    if T_GRAB <= t < S(18):
        st.update(eyes="wide", mouth="o", brows=(16, 16), tilt=0)
        if S(15) <= t < E(15) + 0.3: furious()
        if S(17) <= t: st.update(mouth="flat", eyes="n", brows=(-6, 16))
    if S(18) <= t < E(18) + 0.2: st.update(handL=(-140, -40), handR=(140, -40), brows=(-16, -16), mouth="flat")
    if S(20) <= t < E(20): st.update(brows=(-10, 12))
    if S(21) <= t < S(22): st.update(eyes="wide", mouth="o", brows=(14, 14))
    for i in (22, 24, 26):
        if S(i) <= t < E(i) + 0.3: furious()
    if S(25) <= t < S(26): st.update(eyes="wide", brows=(-10, 14), mouth="o")
    if S(28) <= t < S(29): st.update(brows=(-12, -12))
    if S(29) <= t < E(29) + 0.3: st.update(handR=(-170, 20), brows=(-22, -22))
    if S(30) <= t < S(31): st.update(look=(0.2, -0.6), brows=(-10, -10), tilt=8)
    if S(31) <= t < T_SIT2:
        st.update(brows=(14, 14), tilt=6, handL=(70, 40), handR=(-70, 40), mouth="flat")
    if T_SIT2 <= t < SILENCE[0]:
        st.update(look=(0.0, 0.2), mouth="smile", eyes="happy" if t > T_SIT2 + 0.6 else "n", brows=(10, 10), tilt=-8, handL=CROSS_L, handR=CROSS_R)
    if SILENCE[0] <= t < S(34):
        k = ss(SILENCE[0] + 0.2, SILENCE[1] - 0.3, t)
        st.update(look=(lerp(0.0, -1.0, k), lerp(0.2, 0.0, k)), mouth="flat", eyes="n", brows=(lerp(10, -24, k), lerp(10, -24, k)), tilt=lerp(-8, -4, k))
    if S(34) <= t < S(35):
        st.update(handR=(-190, -110), brows=(-26, -26), tilt=-10)
    if S(35) <= t < PILLOW[0]:
        st.update(handR=(60, -190), brows=(-24, -24), pillow=True)
    if PILLOW[0] <= t:
        st.update(handR=(-190, -60) if t < PILLOW[0] + 0.4 else CROSS_R, brows=(-24, -24))
    st["amp"] = amp("H", t)
    return st

def G_CU(t, z=1.85):
    r = guy_rise(t); return (z, guy_x(t) + 30, 990 - 190 * r)
def H_CU(t, z=1.85):
    return (z, HX - 20, 1040)
MAIN = (1.0, 1720, 1130)
DIST = (0.62, 1330, 1150)

def camera(t):
    if FREEZE[0] <= t < FREEZE[1]:
        k = ss(FREEZE[0], FREEZE[0] + 0.12, t); return G_CU(FREEZE[0], lerp(1.85, 2.2, k))
    if t >= FREEZE2[0]:
        k = ss(FREEZE2[0], FREEZE2[0] + 0.12, t); c = G_CU(FREEZE2[0], lerp(1.9, 2.4, k)); return (c[0], c[1], c[2])
    if E(5) <= t < S(6):
        k = (t - E(5)) / (S(6) - E(5)); return H_CU(t, lerp(1.8, 2.3, k))
    if E(6) <= t < S(7):
        k = (t - E(6)) / (S(7) - E(6)); return G_CU(t, lerp(1.8, 2.2, k))
    if T_GRAB <= t < T_SAT + 0.1 and not (S(15) <= t < E(15)):
        return (0.7, min(1650, (ls_x(t) - 150 + HX) / 2), 1120)
    if T_SAT + 0.1 <= t < E(17) + 0.5:
        return DIST
    if E(17) + 0.5 <= t < S(18):
        return H_CU(t, 2.1)
    if SILENCE[0] <= t < S(34):
        k = (t - SILENCE[0]) / (S(34) - SILENCE[0]); return H_CU(t, lerp(1.6, 2.3, k))
    if T_WALK2 <= t < T_SIT2 + 0.4:
        return (0.7, min(1650, max(1330, (guy_x(t) + HX) / 2)), 1120)
    if T_SIT2 + 0.4 <= t < SILENCE[0]:
        return (1.3, (SEAT2 + HX) / 2, 1060)
    if PILLOW[0] <= t < S(36):
        return (1.0, 1600, 1080)
    shots = [(0, MAIN), (1, G_CU), (2, H_CU), (3, G_CU), (4, lambda t: H_CU(t, 2.1)), (5, G_CU), (6, H_CU),
             (7, G_CU), (8, lambda t: H_CU(t, 2.1)), (9, G_CU), (10, (1.1, 1720, 1060)), (11, H_CU), (12, G_CU),
             (13, H_CU), (14, G_CU), (15, lambda t: H_CU(t, 2.1)), (18, H_CU), (19, G_CU), (20, H_CU), (21, G_CU),
             (22, lambda t: H_CU(t, 2.2)), (23, G_CU), (24, lambda t: H_CU(t, 2.2)), (25, G_CU), (26, lambda t: H_CU(t, 2.3)),
             (27, G_CU), (29, H_CU), (30, G_CU), (31, H_CU), (32, G_CU), (34, lambda t: H_CU(t, 2.4)), (35, G_CU), (36, G_CU)]
    cur = shots[0]
    for i, c in shots:
        if S(i) <= t:
            cur = (i, c)
    i, c = cur
    c = c(t) if callable(c) else c
    nx = [S(j) for j, _ in shots if S(j) > S(i)]
    b = nx[0] if nx else TOTAL
    q = (t - S(i)) / max(0.1, b - S(i))
    return c if c is MAIN else (c[0] * (1 + 0.05 * q), c[1], c[2])

def shake(t):
    for i, amt in ((4, 10), (8, 10), (15, 10), (22, 12), (24, 12), (26, 16), (29, 8), (34, 18)):
        if S(i) <= t < S(i) + 0.4:
            d = 1 - (t - S(i)) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    if PILLOW[1] - 0.05 <= t < PILLOW[1] + 0.3:
        d = 1 - (t - PILLOW[1] + 0.05) / 0.35; return (12 * d * math.sin(t * 90), 8 * d * math.cos(t * 70))
    return (0, 0)

HL = {0: {"TIRED": "b"}, 1: {"DO": "y"}, 2: {"ATTENTION.": "b", "PHONE,": "y", "FOOTBALL,": "y", "GAMES!": "y"},
      3: {"FOOTBALL": "y", "YESTERDAY.": "y"}, 4: {"BESIDE": "y", "FOOTBALL!": "b"}, 5: {"TECHNICALLY,": "b"},
      6: {"SPACE.": "b"}, 7: {"SPACE?": "y"}, 8: {"SPACE!": "b"}, 9: {"PROBLEM.": "y"}, 10: {"SPACE": "y"},
      11: {"WHAT?": "y"}, 12: {"2": "b", "5": "b"}, 13: {"SERIOUS": "b"}, 14: {"REQUIREMENTS.": "b"},
      15: {"DOING?!": "b"}, 16: {"SPACE.": "b"}, 17: {"ENOUGH?": "y"}, 18: {"UNBELIEVABLE!": "b"},
      19: {"BETTER": "y", "IDEA.": "y"}, 20: {"NOW?": "y"}, 21: {"APARTMENTS.": "b"}, 22: {"APARTMENTS?!": "b"},
      23: {"MOVE": "y", "OUT.": "y", "ENTIRE": "y"}, 24: {"MOVE": "b", "OUT?!": "b"}, 25: {"BOUNDARIES,": "y"},
      26: {"EMOTIONAL": "b"}, 27: {"OHHH…": "y"}, 28: {"PHYSICAL": "y"}, 29: {"NO!": "b"}, 30: {"CANCEL": "y", "VIEWING.": "y"},
      31: {"ATTENTION.": "y", "LOVED.": "b"}, 32: {"UNDERSTAND.": "y"}, 33: {"FOOTBALL": "b"}, 34: {"GET": "b", "OUT!": "b"},
      35: {"EMOTIONAL": "y", "PHYSICAL": "b"}, 36: {"PHYSICAL": "b", "SPACE!": "b", "UNDERSTAND!": "y"}}
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



def draw_world_bg(cv, t):
    cv.drawRect(skia.Rect(-400, -1600, WW + 400, 1420), P(C("f3d9b8")))
    for k in range(-5, 24):
        x = 10 + 120 * k
        cv.drawRect(skia.Rect(x, -1600, x + 12, 1420), P(C("ebcda8")))
    cv.drawRect(skia.Rect(-400, 1420, WW + 400, 2900), P(C("c99260")))
    for i in range(24):
        cv.drawLine(-400, 1460 + i * 64, WW + 400, 1460 + i * 64, P(C("b07c4c"), stroke=4))
    # TV corner (left side of the room)
    cv.drawRect(skia.Rect(150, 1180, 640, 1420), P(C("8a5a3a"))); cv.drawRect(skia.Rect(150, 1180, 640, 1420), P(INK, stroke=7))
    cv.drawLine(395, 1190, 395, 1410, P(INK, stroke=5))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(180, 800, 610, 1110), 14, 14), P(C("1b1b22"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(180, 800, 610, 1110), 14, 14), P(INK, stroke=7))
    cv.drawRect(skia.Rect(200, 820, 590, 1090), P(C("3e9a4a")))
    for k in range(4):
        cv.drawRect(skia.Rect(200 + k * 97, 820, 248 + k * 97, 1090), P(C("46a853")))
    cv.drawLine(395, 820, 395, 1090, P(C("ffffff", 0.8), stroke=4)); cv.drawCircle(395, 955, 50, P(C("ffffff", 0.8), stroke=4))
    bx = 395 + 150 * math.sin(t * 1.3); by = 955 + 80 * math.sin(t * 2.1)
    cv.drawCircle(bx, by, 12, P(C("ffffff"))); cv.drawCircle(bx, by, 12, P(INK, stroke=3))
    cv.drawLine(395, 1110, 395, 1180, P(INK, stroke=14))
    # framed photo + clock on the left wall
    cv.drawRect(skia.Rect(760, 420, 980, 600), P(C("ffffff"))); cv.drawRect(skia.Rect(760, 420, 980, 600), P(INK, stroke=7))
    cv.drawCircle(870, 510, 46, P(C("ffcf3f")))
    cv.drawCircle(400, 520, 70, P(C("ffffff"))); cv.drawCircle(400, 520, 70, P(INK, stroke=7))
    cv.drawLine(400, 520, 400, 470, P(INK, stroke=6)); cv.drawLine(400, 520, 440, 530, P(INK, stroke=6))

def loveseat(cv, cx):
    col, dark = C("e0a43a"), C("c48a28")
    cv.drawOval(skia.Rect(cx - 250, 1590, cx + 250, 1660), P(C("000000", 0.22), blur=14))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - 210, 1000, cx + 210, 1330), 50, 50), P(col)); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - 210, 1000, cx + 210, 1330), 50, 50), P(INK, stroke=7))
    cv.save(); cv.translate(cx - 90, 1185); cv.rotate(-8)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-70, -70, 70, 70), 26, 26), P(C("f2786b"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-70, -70, 70, 70), 26, 26), P(INK, stroke=6))
    cv.restore()
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - 200, 1330, cx + 200, 1440), 26, 26), P(C("eab550"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - 200, 1330, cx + 200, 1440), 26, 26), P(INK, stroke=7))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - 210, 1430, cx + 210, 1560), 22, 22), P(dark)); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(cx - 210, 1430, cx + 210, 1560), 22, 22), P(INK, stroke=7))
    for x in (cx - 250, cx + 160):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x, 1180, x + 90, 1560), 38, 38), P(col)); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x, 1180, x + 90, 1560), 38, 38), P(INK, stroke=7))
    for x in (cx - 170, cx + 170):
        cv.drawRect(skia.Rect(x - 10, 1560, x + 10, 1610), P(C("5a3a24")))

def pillow_shape(cv, x, y, rot, s=1.0):
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(s, s)
    r = skia.RRect.MakeRectXY(skia.Rect(-70, -70, 70, 70), 26, 26)
    cv.drawRRect(r, P(C("7ec8a0"))); cv.drawRRect(r, P(INK, stroke=6))
    cv.restore()

def draw_pillow_fx(cv, t):
    x0, y0, x1, y1 = HX - 40, 920, 1180, 860
    if PILLOW[0] <= t < PILLOW[1]:
        q = (t - PILLOW[0]) / (PILLOW[1] - PILLOW[0])
        pillow_shape(cv, lerp(x0, x1, q), lerp(y0, y1, q) - 260 * math.sin(math.pi * q), -720 * q)
        for k in range(1, 4):   # speed lines
            qq = max(0, q - k * 0.06)
            cv.drawLine(lerp(x0, x1, qq) + 90, lerp(y0, y1, qq) - 260 * math.sin(math.pi * qq), lerp(x0, x1, qq) + 160, lerp(y0, y1, qq) - 260 * math.sin(math.pi * qq), P(C("ffffff", 0.7 - k * 0.15), stroke=8))
    elif t >= PILLOW[1]:
        d = t - PILLOW[1]
        y = min(1490, y1 + 900 * d * d)
        pillow_shape(cv, x1 + 40 * min(1, d * 3), y, 20 * min(1, d * 2), 1.0 if d > 0.08 else 0.8)
        if d < 0.45:   # impact star
            a = 1 - d / 0.45; s = 1 + d * 2
            pts = []
            for k in range(16):
                r = (150 if k % 2 == 0 else 70) * s
                pts.append((x1 - 60 + r * math.cos(k * math.pi / 8), y1 + r * math.sin(k * math.pi / 8)))
            cv.drawPath(poly(pts), P(C("ffd21f", a))); cv.drawPath(poly(pts), P(INK, stroke=6))
            text(cv, "BONK!", x1 - 60, y1 + 22, 64, C("e8262a", a), tf=TF_BLACK)

def lightbulb(cv, t, gx, rise):
    if not (S(27) <= t < S(28) + 0.4):
        return
    a, k = pop(t, S(27), 0.35)
    hip = M.SEAT - 18 - 200 * rise
    x, y = gx + 20, hip - 366 - 190
    cv.save(); cv.translate(x, y); cv.scale(k, k)
    cv.drawCircle(0, 0, 90, P(C("fff3a0", 0.5 * a), blur=30))
    cv.drawCircle(0, 0, 52, P(C("ffe24a", a))); cv.drawCircle(0, 0, 52, P(INK, stroke=6))
    cv.drawRect(skia.Rect(-24, 44, 24, 84), P(C("9aa0ad", a))); cv.drawRect(skia.Rect(-24, 44, 24, 84), P(INK, stroke=5))
    for j in range(8):
        an = j * math.pi / 4 + 0.2
        cv.drawLine(math.cos(an) * 72, math.sin(an) * 72, math.cos(an) * 100, math.sin(an) * 100, P(C("ffb020", a), stroke=7))
    cv.restore()

def draw_distance(cv, t):
    if not (T_SAT + 0.6 <= t < E(17) + 0.5):
        return
    k = ss(T_SAT + 0.6, T_SAT + 1.1, t)
    xa, xb, y = LS1 + 40, LS1 + 40 + (HX - 40 - LS1 - 40) * k, 1655
    cv.drawLine(xa, y, xb, y, P(C("ffffff"), stroke=16)); cv.drawLine(xa, y, xb, y, P(C("e8262a"), stroke=9))
    for x in (xa, xb):
        cv.drawLine(x, y - 40, x, y + 40, P(C("e8262a"), stroke=10))
    if k > 0.9:
        chip(cv, (xa + xb) / 2, y - 90, "5 METRES", a=1, col="ffd23f", fg="141414", size=120)

SEARCH = "cheap apartments near me"
def phone_screen(cv, t, mode):
    if mode == "search":
        a0, a1 = S(21) - 0.3, S(23) + 1.2
    else:
        a0, a1 = S(30) + 1.2, E(30) + 0.7
    if not (a0 <= t < a1):
        return
    k = ease_out_back(min(1, (t - a0) / 0.3), 1.8); a = min(1, (a1 - t) / 0.2)
    cv.save(); cv.translate(540, 800); cv.rotate(-5); cv.scale(k * 1.15, k * 1.15)
    body = skia.RRect.MakeRectXY(skia.Rect(-220, -380, 220, 380), 44, 44)
    cv.drawRRect(body, P(C("000000", 0.35 * a), blur=24)); cv.drawRRect(body, P(C("1d1d26", a)))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-196, -350, 196, 350), 26, 26), P(C("ffffff", a)))
    bar = skia.RRect.MakeRectXY(skia.Rect(-176, -320, 176, -250), 35, 35)
    cv.drawRRect(bar, P(C("eef0f4", a))); cv.drawRRect(bar, P(C("c8ccd6", a), stroke=4))
    n = len(SEARCH) if mode != "search" else int(min(1, (t - a0 - 0.25) / 1.6) * len(SEARCH)) if t > a0 + 0.25 else 0
    s = SEARCH[:n] + ("|" if (t * 3) % 1 < 0.5 and n < len(SEARCH) else "")
    text(cv, s, -160, -273, 27, C("141414", a), tf=TF_B, align="l")
    if mode == "search" and n >= len(SEARCH):
        for j, (ttl, pr) in enumerate((("Studio • 2 min", "$450/mo"), ("1-Bed • Quiet", "$600/mo"), ("Room • Far from her", "$300/mo"))):
            y = -200 + j * 150
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-176, y, 176, y + 130), 18, 18), P(C("f4f6fa", a)))
            cv.drawRect(skia.Rect(-160, y + 15, -60, y + 115), P(C("9cc4e8", a)))
            text(cv, ttl, -45, y + 55, 24, C("141414", a), tf=TF_B, align="l")
            text(cv, pr, -45, y + 95, 26, C("2e9a4a", a), tf=TF_BLACK, align="l")
    if mode == "cancel":
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-176, -200, 176, 200), 22, 22), P(C("fff0f0", a)))
        text(cv, "APARTMENT", 0, -90, 46, C("141414", a), tf=TF_BLACK)
        text(cv, "VIEWING", 0, -30, 46, C("141414", a), tf=TF_BLACK)
        chip(cv, 0, 80, "CANCELLED", a=a, col="e8262a", fg="ffffff", size=50)
    cv.restore()

TOP = ["When she says \"I need space\"…", "HE TOOK IT LITERALLY"]

def draw_top(cv, t):
    f = skia.Font(TF_B, 44)
    w = max(f.measureText(TOP[0]), skia.Font(TF_BLACK, 48).measureText(TOP[1])) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 286), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    text(cv, TOP[0], 540, 208, 44, C("111111"), tf=TF_B)
    text(cv, TOP[1], 540, 264, 48, C("e74c3c"), tf=TF_BLACK)

def render_frame(cv, t):
    ta = at(t)
    z, wx, wy = camera(t)
    sx, sy = shake(t)
    wx = min(max(wx, W / 2 / z - 300), WW + 300 - W / 2 / z)
    wy = min(max(wy, H / 2 / z - 1600), 2900 - H / 2 / z)
    cv.save(); cv.translate(W / 2 + sx, H / 2 + sy); cv.scale(z, z); cv.translate(-wx, -wy)
    draw_world_bg(cv, ta)
    cv.save(); cv.translate(OFF, 0)
    CO.draw_room(cv, ta); CO.draw_couch_back(cv); CO.draw_couch_front(cv)
    cv.restore()
    loveseat(cv, ls_x(ta))
    gs = girl_state(ta)
    M.draw_person(cv, ta, gs, HX, "girl")
    if gs.get("pillow"):
        pillow_shape(cv, HX + 84 + 60, 1345 - 18 - 224 - 190 - 30, 10)
    us = guy_state(ta); ux = guy_x(ta)
    M.draw_person(cv, ta, us, ux, "guy")
    lightbulb(cv, ta, ux, us["rise"])
    draw_pillow_fx(cv, ta)
    draw_distance(cv, ta)
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    if FREEZE[0] <= t < FREEZE[1]:
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("7a7f8c", 0.4)))
    if t >= FREEZE2[0]:
        fl = max(0, 1 - (t - FREEZE2[0]) / 0.15)
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("ffffff", 0.6 * fl)))
    draw_top(cv, t)
    tag(cv, t, S(10), S(12), "HE TOOK IT LITERALLY", 470, col="e8262a", fg="ffffff", size=58)
    tag(cv, t, S(25), S(26), "BOUNDARIES: RESPECTED", 470, col="3ccf5a", fg="141414", size=54)
    phone_screen(cv, t, "search")
    phone_screen(cv, t, "cancel")
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
