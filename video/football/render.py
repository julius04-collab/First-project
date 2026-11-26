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
_src = open(os.path.join(HERE, "..", "mia", "render.py")).read().replace('TEE = "7d8494" if friend else "161616"', 'TEE = "7d8494" if friend else "d63031"')
M3 = importlib.util.module_from_spec(importlib.util.spec_from_loader("mia3", loader=None)); M3.__dict__["__file__"] = os.path.join(HERE, "..", "mia", "render.py")
exec(compile(_src, "mia3", "exec"), M3.__dict__)

GX, HX = 330.0, 760.0
ENTER = (0.1, 1.6)
SCRATCH1 = E(5) + 0.02
WHISTLE1 = S(6) + 0.25
SNACKS_DOWN = E(6) + 0.2
LOOKTV = (E(22), S(23))
WIN = S(25) + 0.6
BOOM = E(33) + 0.02
SCRATCH2 = E(34) + 0.02
GRAB = E(38) + 0.05
RUN0 = E(39) - 0.6
STOP = S(40) + 0.1
THROW = (E(41) - 0.25, E(41) + 0.25)
BLACK = E(41) + 0.6
ANGRY = (10, 12, 16, 18, 35, 39, 40, 41)

def guy_x(t):
    if t < RUN0: return GX
    return GX - 260 * (min(t, STOP) - RUN0)

def guy_rise(t):
    return ss(GRAB, RUN0, t)

def girl_x(t):
    if t < ENTER[1]: return lerp(1300, HX, ss(ENTER[0], ENTER[1], t))
    return HX

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
CLASP_L, CLASP_R = (60, 60), (-60, 60)
HIPS_L, HIPS_R = (-18, 168), (18, 168)

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.0), brows=(10, 10), mouth="smile", grass="mouth", tilt=0, rise=guy_rise(t))
    st["blink"] = (t % 3.7) < 0.12
    if t < SNACKS_DOWN:
        eat = (t % 1.7) < 0.45 and t < S(0)
        st.update(snack=True, handL=(80, 40), handR=(-50, -110) if eat else (60, 40), look=(0.0, 0.1), mouth="o" if eat else "smile", lean=-6, eyes="n")   # absorbed in the match
        if S(0) <= t: st.update(look=(0.3, 0.0), brows=(14, 14), mouth="flat")
        if S(3) <= t: st.update(look=(1.0, 0.0), brows=(16, 16), mouth="flat")                         # nervous
        if S(5) <= t < E(5): st.update(mouth="smile", handR=(120, -100), eyes="happy" if amp("G", t) < 0.05 else "n")
        if S(6) <= t: st.update(eyes="wide", mouth="flat", brows=(20, 20), sweat=True)
    elif t < GRAB:
        st.update(look=(1.0, 0.0), brows=(12, 12), mouth="smile")
        if S(7) <= t < S(20): st.update(brows=(10, 4), mouth="smirk", handR=(130, -80 + 20 * math.sin(t * 5)) if amp("G", t) > 0.02 else REST_R)   # confident negotiator
        for i in (10, 12, 14, 16, 18):
            if S(i) <= t < E(i) + 0.2: st.update(eyes="wide", brows=(20, 20), mouth="flat", handR=REST_R)
        if S(19) <= t < E(19): st.update(handR=(120, -120), mouth="smile", eyes="happy" if amp("G", t) < 0.05 else "n")
        if LOOKTV[0] <= t < S(23): st.update(look=(0.0, 0.1) if (t - LOOKTV[0]) < 0.5 else (1.0, 0.0), brows=(16, 16), mouth="flat")
        if S(23) <= t < S(33):
            st.update(mouth="smile", brows=(16, 16))
            if S(25) <= t < E(25): st.update(handL=(-130, -170), handR=(130, -170), eyes="happy", tilt=6)      # excited
            if S(27) <= t: st.update(handR=(130, -90) if amp("G", t) > 0.02 else REST_R)
        if S(33) <= t < S(35):
            st.update(handR=(110, -160), mouth="smile", brows=(18, 18))
            if S(34) <= t: st.update(handL=(-130, -160), handR=(130, -160), eyes="happy", mouth="smile", tilt=8)   # smug, solved it
        if S(35) <= t: st.update(eyes="wide", brows=(20, 20), mouth="flat", sweat=True)
        if S(36) <= t < E(36): st.update(handL=(-130, -60), handR=(130, -60), mouth="smile", eyes="n")
        if S(38) <= t: st.update(handR=(120, -130), mouth="smile", eyes="happy" if amp("G", t) < 0.05 else "n", sweat=False)
    if GRAB <= t:
        st.update(eyes="wide", mouth="o", brows=(24, 24), sweat=True, handL=(-60, 60), handR=(110, -200), look=(1.0, 0.0), tilt=-8, card=True)   # red card!
        if RUN0 <= t < STOP: st.update(walk=t * 16, lean=-10, look=(-1.0, 0.0))
        if STOP <= t: st.update(look=(0.0, 0.0), handR=(60, -60), handL=REST_L, card=False, eyes="wide", mouth="o", brows=(20, 4), tilt=8)   # distracted by goal
        if S(41) <= t: st.update(handL=(-120, -150), handR=(120, -150))
        if THROW[1] - 0.05 <= t: st.update(eyes="closed", tilt=-18)
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=HIPS_L, handR=HIPS_R, look=(-1.0, 0.0), brows=(-12, -12), mouth="flat", tilt=-4, rise=1.0)
    st["blink"] = (t % 4.1) < 0.12
    if t < ENTER[1]: st["walk"] = t * 9
    if S(4) <= t < E(4): st.update(handR=(-150, -60), brows=(-16, 10))
    if S(6) <= t < E(6) + 0.3: st.update(handR=(-170, -100), brows=(-18, -18), mouth="flat")             # serious ultimatum
    if S(7) <= t < S(20):
        st.update(brows=(-14, 10))
        for i in (10, 12, 14, 16, 18):
            if S(i) <= t < E(i) + 0.2: st.update(handL=(-120, -190 + 10 * math.sin(t * 20)), handR=(120, -190 + 10 * math.cos(t * 20)), brows=(-24, -24), tilt=-10)
    if S(19) <= t < S(20) + 0.6: st.update(brows=(-24, -24), eyes="n")
    if S(20) <= t < S(33):
        st.update(handL=CLASP_L, handR=CLASP_R, brows=(-16, 8))                                             # arms folded
        if S(22) <= t < E(22): st.update(handR=(-170, -40), handL=HIPS_L)
        if S(24) <= t < E(24): st.update(brows=(-6, 14), tilt=-8)
        if S(26) <= t: st.update(brows=(12, -6), tilt=8, mouth="flat")                                    # confused
        if S(32) <= t: st.update(handL=(-130, -150), handR=(130, -150), brows=(-20, -20))
    if S(33) <= t < S(35):
        st.update(handL=CLASP_L, handR=CLASP_R, brows=(-6, 10))
        if E(33) - 0.4 <= t: st.update(mouth="smile", eyes="happy", brows=(14, 14), tilt=8)               # she smiles...
        if SCRATCH2 - 0.3 <= t: st.update(mouth="o", eyes="wide", brows=(18, 18), tilt=0)                # ...smile disappears
    if S(35) <= t < GRAB:
        st.update(brows=(-24, -24))
        if S(35) <= t < E(35) + 0.2: st.update(handL=(-120, -195 + 12 * math.sin(t * 22)), handR=(120, -195 + 12 * math.cos(t * 22)), tilt=-10, mouth="o")
        if S(37) <= t: st.update(handL=HIPS_L, handR=(-150, -60), brows=(-18, 10))
        if S(38) <= t: st.update(eyes="wide", mouth="o", brows=(-28, -28), handR=HIPS_R)                 # furious
    if GRAB <= t:
        st.update(handR=(30, -230), handL=(-120, -60), brows=(-28, -28), mouth="o", pillow=t < THROW[0], tilt=-8)
        if THROW[0] <= t: st.update(handR=(-200, -80))
    st["amp"] = amp("H", t)
    return st

def snack(cv, gx, st):
    hip = M.SEAT - 18 - 200 * st["rise"]
    hx, hy = gx - 94 + st["handL"][0], hip - 224 + st["handL"][1]
    cv.save(); cv.translate(hx + 10, hy - 30); cv.rotate(-10)
    bag = poly([(-46, -70), (46, -70), (54, 60), (-54, 60)])
    cv.drawPath(bag, P(C("3a7bd5"))); cv.drawPath(bag, P(INK, stroke=5))
    text(cv, "CHIPS", 0, 6, 26, C("ffd21f"), tf=TF_BLACK)
    cv.restore()
    cv.drawCircle(hx, hy, 16, P(C("ffffff"))); cv.drawCircle(hx, hy, 16, P(INK, stroke=5))

def jersey_number(cv, gx, st):
    hip = M.SEAT - 18 - 200 * st["rise"] - st.get("bob", 0)
    text(cv, "10", gx, hip - 110, 70, C("ffffff"), tf=TF_BLACK, stroke=8, stroke_col=INK)

def red_card(cv, gx, st):
    hip = M.SEAT - 18 - 200 * st["rise"]
    hx, hy = gx + 94 + st["handR"][0], hip - 224 + st["handR"][1]
    cv.save(); cv.translate(hx, hy - 60); cv.rotate(10 + 6 * math.sin(time_ref[0] * 20))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-38, -55, 38, 55), 8, 8), P(C("e8262a"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-38, -55, 38, 55), 8, 8), P(INK, stroke=5))
    cv.restore()
    cv.drawCircle(hx, hy, 16, P(C("ffffff"))); cv.drawCircle(hx, hy, 16, P(INK, stroke=5))
time_ref = [0.0]

def pillow_shape(cv, x, y, rot):
    cv.save(); cv.translate(x, y); cv.rotate(rot)
    r = skia.RRect.MakeRectXY(skia.Rect(-70, -70, 70, 70), 26, 26)
    cv.drawRRect(r, P(C("7ec8a0"))); cv.drawRRect(r, P(INK, stroke=6))
    cv.restore()

def throw_fx(cv, t, gx):
    if THROW[0] <= t < THROW[1] + 0.4:
        x0, y0, x1, y1 = HX - 40, 800, gx + 20, 860
        if t < THROW[1]:
            q = (t - THROW[0]) / (THROW[1] - THROW[0])
            pillow_shape(cv, lerp(x0, x1, q), lerp(y0, y1, q) - 160 * math.sin(math.pi * q), -600 * q)
        else:
            d = t - THROW[1]; a = 1 - d / 0.4
            pts = [(x1 + (130 if k % 2 == 0 else 60) * (1 + d) * math.cos(k * math.pi / 8), y1 + (130 if k % 2 == 0 else 60) * (1 + d) * math.sin(k * math.pi / 8)) for k in range(16)]
            cv.drawPath(poly(pts), P(C("ffd21f", a))); cv.drawPath(poly(pts), P(INK, stroke=6))
            text(cv, "BONK!", x1, y1 + 22, 60, C("e8262a", a), tf=TF_BLACK)

def G_CU(t, z=1.85):
    return (z, guy_x(t) + 30, 990 - 190 * guy_rise(t))
def H_CU(t, z=1.85):
    return (z, girl_x(t) - 10, 805)
WIDE = (1.0, 560, 1130)
TWO = (1.25, 560, 1050)

def camera(t):
    if t < S(1): return WIDE
    if S(6) <= t < S(7): return H_CU(t, 2.0) if t < E(6) else G_CU(t, 2.0)
    if LOOKTV[0] <= t < S(23): return G_CU(t, 2.0)
    if S(25) <= t < S(27): return TWO
    if S(33) <= t < S(35):
        k = (t - S(33)) / (S(35) - S(33)); return G_CU(t, lerp(1.8, 2.3, k)) if t < E(33) - 0.4 or t > SCRATCH2 else H_CU(t, 2.1)
    if GRAB <= t:
        if STOP <= t: return G_CU(t, 1.6) if t < THROW[0] else (1.2, 300, 1000)
        return (1.0, 500, 1130)
    shots = [(1, G_CU), (2, H_CU), (3, G_CU), (4, H_CU), (5, G_CU), (8, H_CU), (9, lambda t: G_CU(t, 2.0)), (10, lambda t: H_CU(t, 2.2)),
             (11, G_CU), (12, lambda t: H_CU(t, 2.1)), (13, G_CU), (14, H_CU), (15, G_CU), (16, H_CU), (17, G_CU), (18, lambda t: H_CU(t, 2.3)),
             (19, G_CU), (20, H_CU), (21, G_CU), (22, H_CU), (23, G_CU), (24, H_CU), (27, TWO), (28, H_CU), (29, G_CU), (30, H_CU), (31, G_CU),
             (32, lambda t: H_CU(t, 2.1)), (35, lambda t: H_CU(t, 2.3)), (36, G_CU), (37, H_CU), (38, lambda t: G_CU(t, 2.0))]
    cur = None
    for i, c in shots:
        if S(i) <= t: cur = (i, c)
    i, c = cur
    c = c(t) if callable(c) else c
    nx = [S(j) for j, _ in shots if S(j) > S(i)]
    b = nx[0] if nx else TOTAL
    q = (t - S(i)) / max(0.1, b - S(i))
    return c if c is WIDE else (c[0] * (1 + 0.05 * q), c[1], c[2])

def shake(t):
    for a, amt in ((SCRATCH1, 8), (S(10), 10), (S(18), 12), (BOOM, 12), (S(35), 16), (S(40), 10), (THROW[1], 14)):
        if a <= t < a + 0.4:
            d = 1 - (t - a) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    return (0, 0)

HL = {0: {"TALK.": "y"}, 1: {"HALFTIME?": "y"}, 2: {"NO.": "b"}, 4: {"COMPETING": "y", "FOOTBALL": "b"}, 5: {"DIFFERENT": "y", "LEAGUES!": "b"},
      6: {"CHOOSE.": "b", "FOOTBALL?": "y"}, 7: {"QUESTION": "y"}, 9: {"FOREVER,": "y", "TODAY'S": "y"}, 10: {"FOREVER!": "b"},
      11: {"LONG": "y", "CONTRACT.": "b"}, 12: {"DANIEL!": "b"}, 13: {"HOBBY?": "y"}, 14: {"NO!": "b"}, 15: {"HIGHLIGHTS?": "y"}, 16: {"NO!": "b"},
      17: {"WITHOUT": "y", "SOUND?": "y"}, 18: {"NOT": "b", "LISTENING!": "b"}, 19: {"WITHOUT": "b", "SOUND!": "b"}, 20: {"LIVE": "y"},
      22: {"TURN": "b", "OFF.": "b"}, 23: {"BETTER": "y", "SOLUTION.": "y"}, 25: {"TOGETHER!": "b"}, 26: {"LIKE": "y"}, 27: {"SUPPORT": "y", "TEAM.": "y"},
      28: {"LOSES?": "y"}, 29: {"COMFORT": "y"}, 30: {"WIN?": "y"}, 31: {"CELEBRATE!": "y"}, 32: {"FIT": "b"}, 33: {"CHOOSE": "y", "YOU…": "b"},
      34: {"FOOTBALL!": "b"}, 35: {"BOTH!": "b"}, 36: {"LOVE,": "y", "PASSION.": "y"}, 37: {"DO?": "y"}, 38: {"REFEREE!": "b"},
      39: {"RED": "b", "CARD!": "b"}, 40: {"GOAL!": "b"}, 41: {"WHO": "y", "SCORED?!": "b"}}
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
            if who in ("G", "H", "C"):
                chip(cv, 540, CAP_Y - 128, {"H": "HER", "G": "HIM", "C": "TV"}[who], a=0.95, col="ffd23f" if who == "H" else "ffffff", fg="1a1a1a", size=30)
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





TOP = ["When she says \"Choose: me or football\"…", "HE CHOSE A RED CARD"]

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
    time_ref[0] = t
    z, wx, wy = camera(t)
    sx, sy = shake(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2 + sx, H / 2 + sy); cv.scale(z, z); cv.translate(-wx, -wy)
    CO.draw_room(cv, t); CO.draw_couch_back(cv); CO.draw_couch_front(cv)
    gs = girl_state(t); gx = girl_x(t)
    us = guy_state(t); ux = guy_x(t)
    M3.draw_person(cv, t, us, ux, "guy")
    jersey_number(cv, ux, us)
    if us.get("snack"): snack(cv, ux, us)
    if us.get("card"): red_card(cv, ux, us)
    M.draw_person(cv, t, gs, gx, "girl")
    if gs.get("pillow"):
        hip = M.SEAT - 18 - 200 * gs.get("rise", 0)
        pillow_shape(cv, gx + 84 + gs["handR"][0], hip - 224 + gs["handR"][1] - 40, 15 * math.sin(t * 12))
    throw_fx(cv, t, ux)
    if t < S(7) or S(39) <= t:    # TV glow flicker
        cv.drawRect(skia.Rect(-200, -200, W + 200, H + 200), P(C("6fb0ff", 0.04 + 0.03 * math.sin(t * 11))))
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    draw_top(cv, t)
    tag(cv, t, 0.3, S(0), "LIVE MATCH", 470, col="e8262a", fg="ffffff", size=58)
    tag(cv, t, WHISTLE1, S(7) + 0.3, "HER  vs  FOOTBALL", 470, col="ffd23f", size=60)
    tag(cv, t, S(9), S(20), "NEGOTIATIONS IN PROGRESS…", 470, col="ffffff", size=50)
    tag(cv, t, WIN, S(27), "\"THIRD OPTION\"", 470, col="3ccf5a", fg="141414", size=58)
    bubble(cv, t, GRAB + 0.2, STOP, "RED CARD!", 540, 560, col="e8262a", fg="ffffff", size=84)
    bubble(cv, t, S(40), S(41) + 0.3, "GOAL!", 540, 560, col="3ccf5a", fg="141414", size=110)
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
