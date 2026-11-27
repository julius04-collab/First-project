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
GX, HX = 330.0, 760.0
ENTER = (0.1, 1.5)
PLACE = S(0) + 0.2
BITE1 = (E(1) + 0.1, E(1) + 2.0)
FREEZE = (E(6), S(7))
TASTE = (E(13) + 0.1, S(14))
HORROR = (E(22), S(23))
SPOON = (E(24) + 0.05, S(25))
BITE2 = E(25) + 0.15
BLACK = TOTAL - 0.4
ANGRY = (8, 14, 24)

def girl_x(t):
    return lerp(1300, HX, ss(ENTER[0], ENTER[1], t))

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
CLASP_L, CLASP_R = (60, 60), (-60, 60)
HIPS_L, HIPS_R = (-18, 168), (18, 168)
SPOON_REST = (120, -10)
SPOON_MOUTH = (-60, -115)

def chewing(t, t0, t1):
    return t0 <= t < t1

def guy_state(t):
    st = dict(handL=(60, 40), handR=SPOON_REST, look=(1.0, 0.0), brows=(12, 12), mouth="smile", grass="mouth", tilt=0, rise=0.0, spoon=True)
    st["blink"] = (t % 3.7) < 0.12
    if t < S(1): st.update(look=(1.0, 0.0), mouth="smile")
    if S(1) <= t < E(1): st.update(eyes="happy" if amp("G", t) < 0.03 else "n", brows=(16, 16), handR=(130, -80))
    if BITE1[0] <= t < S(3):
        q = t - BITE1[0]
        st.update(handR=SPOON_MOUTH if q < 0.5 else SPOON_REST, look=(0.3, 0.5))
        if q >= 0.5:                                                         # smile slowly disappears, struggles
            st.update(mouth="o" if (t * 3) % 1 < 0.5 else "flat", brows=(18, 18), eyes="wide" if q > 1.0 else "n", sweat=q > 0.9, tilt=4 * math.sin(t * 6))
    if S(3) <= t < S(6):
        st.update(mouth="smile", brows=(18, 18), sweat=True, look=(1.0, 0.0))
        if S(5) <= t < E(5): st.update(handR=(130, -90))
    if S(6) <= t < S(7): st.update(eyes="wide", mouth="flat", brows=(22, 22), sweat=True)
    if FREEZE[0] <= t < S(7): st.update(look=(0.4, 0.7) if (t - FREEZE[0]) < 0.5 else (1.0, 0.0))     # food, then her
    if S(7) <= t < S(9): st.update(handR=(130, -80), mouth="flat", brows=(4, 4), sweat=True)
    if S(8) <= t < S(9): st.update(eyes="wide", brows=(24, 24), handR=SPOON_REST)
    if S(9) <= t < TASTE[0]:
        st.update(handR=(130, -150), mouth="smile", brows=(20, 20), sweat=True, eyes="n")
        if S(11) <= t: st.update(handR=(130, -80), brows=(16, 16))
        if S(13) <= t: st.update(handR=(130, -110), mouth="smile", eyes="happy")
    if TASTE[0] <= t < S(22):
        st.update(eyes="wide", brows=(22, 22), mouth="flat", sweat=True, handR=SPOON_REST)
        if S(15) <= t < E(15): st.update(handL=(-130, -60), handR=(130, -60), mouth="smile")
        if S(17) <= t < E(17): st.update(mouth="smile", eyes="happy", brows=(14, 14))
        if S(19) <= t < E(19): st.update(mouth="smile", eyes="n", brows=(14, 14), handR=(-60, -40))
        if S(21) <= t < E(21): st.update(mouth="smirk", brows=(10, 4), handR=(130, -110), sweat=False)
    if S(22) <= t:
        st.update(eyes="wide", mouth="o", brows=(24, 24), sweat=True, look=(0.4, 0.7) if HORROR[0] <= t < S(23) else (1.0, 0.0), handR=SPOON_REST)
        if S(23) <= t < E(23): st.update(mouth="smile", brows=(16, 16), handL=(-130, -80), handR=(130, -80), eyes="n")
        if S(24) <= t: st.update(eyes="wide", mouth="flat")
        if SPOON[0] <= t: st.update(handR=(110, -40), look=(0.4, 0.6), brows=(20, 20), mouth="flat", eyes="n")
        if S(25) <= t: st.update(look=(0.0, 0.0), brows=(16, 16), mouth="flat")
        if BITE2 <= t:
            q = t - BITE2
            st.update(handR=SPOON_MOUTH if q < 0.5 else SPOON_REST, eyes="closed" if q > 0.5 else "n", mouth="o" if (t * 3) % 1 < 0.5 else "flat", look=(0.0, 0.0))
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=CLASP_L, handR=CLASP_R, look=(-1.0, 0.0), brows=(14, 14), mouth="smile", tilt=8, rise=1.0, eyes="happy")
    st["blink"] = (t % 4.1) < 0.12
    if t < ENTER[1]: st.update(walk=t * 9, handR=(-160, -30), handL=(-80, -30), plate=True, eyes="n")
    if ENTER[1] <= t < PLACE + 0.5: st.update(handR=(-200, 60), handL=(-120, 60), plate=t < PLACE, eyes="n")
    if S(1) <= t < S(3): st.update(eyes="happy", brows=(16, 16), tilt=10)                                      # proud
    if S(2) <= t < E(2): st.update(eyes="n", brows=(16, 16))
    if S(4) <= t < S(6): st.update(eyes="n", brows=(-8, 14), mouth="flat", tilt=-4)
    if S(6) <= t < S(7): st.update(eyes="n", brows=(12, 12), mouth="smile")
    if S(8) <= t < E(8) + 0.2: st.update(eyes="n", brows=(-22, -22), mouth="flat", handR=(-170, -60), tilt=-8)
    if S(9) <= t < TASTE[0]:
        st.update(eyes="n", brows=(14, 14), mouth="smile", tilt=8)
        if S(10) <= t < E(10): st.update(eyes="happy", brows=(18, 18))
        if S(12) <= t: st.update(brows=(-8, 14), mouth="flat", tilt=-4)
        if S(13) <= t: st.update(brows=(-6, 10))
    if TASTE[0] <= t < S(14):
        q = t - TASTE[0]
        st.update(eyes="n", brows=(4, 4), mouth="flat", tilt=0, look=(-0.6, 0.6))
        st["handR"] = (-200, 110) if q < 0.5 else (-40, -130)
        if q > 0.9: st.update(eyes="wide", mouth="o", brows=(22, 22), look=(0.0, 0.0), handR=(-60, -150))           # tastes it
    if S(14) <= t < E(14) + 0.2: st.update(eyes="wide", mouth="o", brows=(18, 18), handL=(-120, -190), handR=(120, -190), tilt=0)
    if E(14) + 0.2 <= t < S(22):
        st.update(eyes="n", brows=(-14, 10), mouth="flat", tilt=-4)
        for i in (16, 18, 20):
            if S(i) <= t < E(i): st.update(handR=(-160, -60), brows=(-18, -18))
        if S(19) <= t < E(19) + 0.2: st.update(brows=(4, 4), mouth="smile", tilt=6)
        if S(20) <= t: st.update(brows=(-18, 12))
        if S(21) <= t < E(21) + 0.3: st.update(brows=(-12, 18), tilt=-10)
    if S(22) <= t:
        st.update(eyes="n", brows=(-16, 6), mouth="smirk", tilt=-4)
        if S(22) <= t < E(22): st.update(handR=(-200, 80))
        if S(24) <= t < E(24): st.update(handR=(-200, 60), brows=(-24, -24), mouth="flat")
        if SPOON[0] <= t: st.update(handL=CLASP_L, handR=CLASP_R, brows=(-10, 8), mouth="smirk")                    # arms folded
    st["amp"] = amp("H", t)
    return st

def chair(cv, cx, side):
    wood, dk = C("b9773f"), C("8a5426")
    bx = cx - side * 110
    cv.drawRect(skia.Rect(bx - 12, 1050, bx + 12, 1420), P(wood)); cv.drawRect(skia.Rect(bx - 12, 1050, bx + 12, 1420), P(INK, stroke=5))
    cv.drawRect(skia.Rect(cx - 120, 1360, cx + 120, 1395), P(dk)); cv.drawRect(skia.Rect(cx - 120, 1360, cx + 120, 1395), P(INK, stroke=5))
    for x in (cx - 105, cx + 95): cv.drawRect(skia.Rect(x, 1395, x + 14, 1600), P(wood))

def table(cv):
    cv.drawRect(skia.Rect(420, 1240, 700, 1268), P(C("a0683f"))); cv.drawRect(skia.Rect(420, 1240, 700, 1268), P(INK, stroke=6))
    cv.drawRect(skia.Rect(410, 1222, 710, 1245), P(C("ffffff"))); cv.drawRect(skia.Rect(410, 1222, 710, 1245), P(INK, stroke=4))   # tablecloth
    for x in (440, 664): cv.drawRect(skia.Rect(x, 1268, x + 16, 1600), P(C("8a5426"))); cv.drawRect(skia.Rect(x, 1268, x + 16, 1600), P(INK, stroke=4))

def food(cv, x, y, t, s=1.0):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    cv.drawOval(skia.Rect(-80, -14, 80, 14), P(C("ffffff"))); cv.drawOval(skia.Rect(-80, -14, 80, 14), P(INK, stroke=4))
    blob = skia.Path(); blob.moveTo(-55, -4); blob.cubicTo(-60, -40, -20, -55, 0, -45); blob.cubicTo(25, -60, 60, -35, 52, -4); blob.close()
    cv.drawPath(blob, P(C("7c8a3a"))); cv.drawPath(blob, P(INK, stroke=4))
    cv.drawCircle(-20, -30, 9, P(C("5a4a2a"))); cv.drawCircle(18, -36, 7, P(C("a8b04a"))); cv.drawCircle(30, -18, 6, P(C("5a4a2a")))
    for j in range(3):   # bubbles
        q = ((t * 0.8) + j / 3) % 1
        cv.drawCircle(-25 + j * 25, -40 - 30 * q, 6 * (1 - q) + 2, P(C("a8b04a", 1 - q), stroke=3))
    for j in range(3):   # stink lines
        sx = -30 + j * 30
        p = skia.Path(); p.moveTo(sx, -70); p.cubicTo(sx - 14, -95 - 8 * math.sin(t * 4 + j), sx + 14, -115, sx, -140)
        cv.drawPath(p, P(C("7fb04a", 0.7), stroke=5))
    cv.restore()

def spoon(cv, gx, st):
    hip = M.SEAT - 18 - 200 * st["rise"]
    hx, hy = gx + 94 + st["handR"][0], hip - 224 + st["handR"][1]
    cv.drawLine(hx, hy, hx + 50, hy - 30, P(C("9aa0ad"), stroke=8)); cv.drawLine(hx, hy, hx + 50, hy - 30, P(INK, stroke=2))
    cv.drawOval(skia.Rect(hx + 40, hy - 46, hx + 72, hy - 26), P(C("c9ccd6"))); cv.drawOval(skia.Rect(hx + 40, hy - 46, hx + 72, hy - 26), P(INK, stroke=3))
    cv.drawCircle(hx, hy, 16, P(C("ffffff"))); cv.drawCircle(hx, hy, 16, P(INK, stroke=5))

def green_face(cv, x, rise, a):
    if a <= 0: return
    hip = M.SEAT - 18 - 200 * rise
    cv.drawCircle(x, hip - 366 + 30, 80, P(C("6fbf4a", 0.45 * a), blur=10))

def G_CU(t, z=1.85): return (z, GX + 40, 990)
def H_CU(t, z=1.85): return (z, girl_x(t) - 10, 805)
TWO = (1.2, 550, 1060)
FOOD_CU = (2.6, 470, 1150)

def camera(t):
    if t < S(1): return TWO
    if PLACE <= t < S(1) and False: return FOOD_CU
    if BITE1[0] <= t < S(2): k = (t - BITE1[0]) / (S(2) - BITE1[0]); return G_CU(t, lerp(1.8, 2.3, k))
    if FREEZE[0] <= t < S(7): return FOOD_CU if (t - FREEZE[0]) < 0.5 else G_CU(t, 2.2)
    if S(9) <= t < S(10): return G_CU(t, 2.0)
    if TASTE[0] <= t < S(14): return H_CU(t, 2.0) if t > TASTE[0] + 0.6 else TWO
    if HORROR[0] <= t < S(23): return FOOD_CU if (t - HORROR[0]) < 0.45 else G_CU(t, 2.2)
    if SPOON[0] <= t < S(25): return TWO
    if S(25) <= t: k = ss(S(25), TOTAL, t); return G_CU(t, lerp(1.8, 2.4, k))
    shots = [(1, G_CU), (2, H_CU), (3, G_CU), (4, H_CU), (5, G_CU), (6, H_CU), (7, G_CU), (8, lambda t: H_CU(t, 2.2)), (10, H_CU), (11, G_CU), (12, H_CU),
             (13, G_CU), (14, lambda t: H_CU(t, 2.2)), (15, G_CU), (16, H_CU), (17, G_CU), (18, H_CU), (19, G_CU), (20, lambda t: H_CU(t, 2.1)),
             (21, G_CU), (22, H_CU), (23, G_CU), (24, lambda t: H_CU(t, 2.3))]
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
    for a, amt in ((S(8), 10), (S(14), 14), (S(24), 14)):
        if a <= t < a + 0.4:
            d = 1 - (t - a) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    return (0, 0)

HL = {0: {"SPECIAL": "y"}, 1: {"AMAZING.": "y"}, 2: {"HOW": "y"}, 3: {"INTERESTING.": "b"}, 4: {"INTERESTING?": "b"}, 5: {"NEVER": "y", "EXPERIENCED": "y"},
      6: {"RATE": "y", "1": "b", "10.": "b"}, 7: {"HONEST": "y", "ALIVE?": "b"}, 8: {"DANIEL!": "b"}, 9: {"10!": "b", "10": "b", "10!": "b"},
      10: {"REALLY?": "y"}, 11: {"TASTE": "y", "SURPRISED.": "b"}, 12: {"SURPRISED?": "y"}, 13: {"GOOD": "y"}, 14: {"TERRIBLE!": "b"},
      15: {"BAD!": "y"}, 16: {"STRUGGLING": "y", "SWALLOW?": "b"}, 17: {"SLOWLY.": "y"}, 18: {"10?": "b"}, 19: {"LOVE": "y"}, 20: {"LIED?": "b"},
      21: {"PROTECTED": "y", "RELATIONSHIP.": "y"}, 22: {"FINISH": "b", "WHOLE": "b", "PLATE.": "b"}, 23: {"PATIENT.": "y", "KIND.": "y", "STOP": "b", "EATING.": "b"},
      24: {"FINISH": "b", "IT!": "b"}, 25: {"SURVIVE": "y", "STOMACH": "b"}}
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
                chip(cv, 540, CAP_Y - 128, {"H": "SOPHIA", "G": "DANIEL"}[who], a=0.95, col="ffd23f" if who == "H" else "ffffff", fg="1a1a1a", size=30)
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





TOP = ["When she asks you to rate her cooking…", "HONESTY OR SURVIVAL?"]

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
    z, wx, wy = camera(t)
    sx, sy = shake(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2 + sx, H / 2 + sy); cv.scale(z, z); cv.translate(-wx, -wy)
    CO.draw_room(cv, t)
    chair(cv, GX, 1)
    gs = girl_state(t); gx = girl_x(t)
    us = guy_state(t)
    M.draw_person(cv, t, us, GX, "guy")
    table(cv)
    if t >= PLACE: food(cv, 470, 1220, t)
    M.draw_person(cv, t, gs, gx, "girl")
    if gs.get("plate"):
        hip = M.SEAT - 18 - 200; px, py = gx + 84 + gs["handR"][0] - 40, hip - 224 + gs["handR"][1] - 20
        food(cv, px, py, t)
    spoon(cv, GX, us)
    ga = 0
    if BITE1[0] + 0.6 <= t < S(4): ga = min(1, (t - BITE1[0] - 0.6) / 0.6)
    if BITE2 + 0.5 <= t: ga = min(1, (t - BITE2 - 0.5) / 0.5)
    green_face(cv, GX, 0, ga)
    if TASTE[0] + 1.0 <= t < S(14) + 0.8: green_face(cv, gx, 1, min(1, (t - TASTE[0] - 1.0) / 0.4))
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    draw_top(cv, t)
    tag(cv, t, S(6), S(7), "RATE IT: 1 – 10", 470, col="ffd23f", size=60)
    tag(cv, t, S(7) + 1.0, S(8), "HONESTY vs SURVIVAL", 470, col="e8262a", fg="ffffff", size=56)
    bubble(cv, t, S(9) + 0.2, S(10) + 0.4, "10/10", 540, 600, col="3ccf5a", fg="141414", size=120)
    tag(cv, t, S(21) + 0.6, S(22), "\"PROTECTED OUR RELATIONSHIP\"", 470, col="3a7bd5", fg="ffffff", size=44)
    bubble(cv, t, BITE2 + 0.8, BLACK, "RIP TASTE BUDS", 540, 600, col="141414", fg="ffffff", size=70)
    draw_caption(cv, t)
    if t >= BLACK: cv.drawRect(skia.Rect(0, 0, W, H), P(C("000000")))

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
