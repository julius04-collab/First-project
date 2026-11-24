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
GX, HX, JX = 330.0, 760.0, 590.0
ENTER = (0.1, 1.5)
JACKET = (E(3) + 0.05, E(3) + 0.6)
PLOP = E(3) + 0.75
REVEAL = S(6) + 0.4 * (E(6) - S(6))
ZOOM = (E(6), S(7))
SIL = (E(11), S(12))
APP = (E(26) + 0.05, S(28))
GRAB = E(29) + 0.05
RUN0 = GRAB + 0.35
FREEZE2 = (S(30) + 0.9, TOTAL)
BLACK = TOTAL - 0.3
ANGRY = (7, 19, 21, 23, 30)

def at(t):
    return FREEZE2[0] if t >= FREEZE2[0] else t

def girl_x(t):
    if t < ENTER[1]: return lerp(1300, HX, ss(ENTER[0], ENTER[1], t))
    if t < RUN0 + 0.2: return HX
    return max(GX + 140, HX - 380 * (t - RUN0 - 0.2))

def guy_x(t):
    return GX if t < RUN0 else GX - 260 * min(t - RUN0, 0.8)

def guy_rise(t):
    return ss(GRAB, RUN0, t)

def has_notebook(t):
    return PLOP + 0.5 <= t < S(13)

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
CLASP_L, CLASP_R = (60, 60), (-60, 60)
HIPS_L, HIPS_R = (-18, 168), (18, 168)

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.0), brows=(8, 8), mouth="smirk", grass="mouth", tilt=0, rise=guy_rise(t))
    st["blink"] = (t % 3.7) < 0.12
    if t < S(1): st.update(phone=True, handL=(90, 50), look=(0.4, 0.7), lean=-8, mouth="smile")                     # relaxed
    if S(1) <= t < JACKET[0]: st.update(phone=True, handL=(90, 50), brows=(16, 16), mouth="flat", tilt=8)           # "broke"
    if JACKET[0] <= t < S(6): st.update(eyes="wide", brows=(20, 20), mouth="o", sweat=True)                         # nervous
    if S(5) <= t < E(5): st.update(handL=(-130, -80), handR=(130, -80), mouth="smile")
    if S(6) <= t < S(13): st.update(sweat=True, eyes="wide", brows=(22, 22), mouth="flat")
    if S(7) <= t < E(7): st.update(handL=(-140, -90), handR=(140, -90), mouth="o")
    if S(9) <= t < E(9): st.update(handR=(120, -80), mouth="smile", eyes="n")
    if S(11) <= t < E(11): st.update(eyes="n", mouth="smile", brows=(10, 10), handR=(130, -60))                     # "You!"
    if SIL[0] + 0.4 <= t < S(12): st.update(eyes="wide", mouth="o", brows=(26, 26))
    if S(12) <= t < S(13): st.update(handL=(-140, -80), handR=(140, -80), mouth="smile")
    if S(13) <= t < S(22):
        st.update(mouth="smile", brows=(16, 16), eyes="n", sweat=True)                                               # fake smile
        for i in (14, 16, 18, 20):
            if S(i) <= t < E(i): st.update(handR=(130, -110 + 20 * math.sin(t * 5)), brows=(4, 4), mouth="smile", look=(0.6, -0.3))
        if S(19) <= t < S(20): st.update(eyes="wide", mouth="o", brows=(22, 22))
        if S(21) <= t: st.update(eyes="wide", mouth="flat")
    if S(22) <= t < GRAB:
        st.update(sweat=True, eyes="wide", brows=(24, 24), mouth="o")
        if S(23) <= t < E(23): st.update(handL=UP_L, handR=UP_R)                                                     # horrified
        if S(25) <= t < E(25): st.update(handL=(-130, -60), handR=(130, -60), mouth="flat")
        if APP[0] <= t: st.update(phone=True, handL=(90, 30), look=(0.4, 0.7), mouth="flat", brows=(16, 16), eyes="n")
        if S(27) <= t: st.update(look=(0.0, 0.2), mouth="flat", brows=(14, 14))
        if S(29) <= t: st.update(look=(1.0, 0.0), mouth="smile", handR=(120, -100))
    if GRAB <= t:
        st.update(eyes="wide", mouth="o", brows=(24, 24), sweat=True, handL=UP_L, handR=UP_R, look=(1.0, 0.0), tilt=-8, phone=False)
        if RUN0 <= t < RUN0 + 0.8: st.update(walk=t * 16, lean=-10)
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=HIPS_L, handR=HIPS_R, look=(-1.0, 0.0), brows=(6, 6), mouth="smile", tilt=-4, rise=1.0)
    st["blink"] = (t % 4.1) < 0.12
    if t < ENTER[1]: st["walk"] = t * 9
    if S(0) <= t < E(0): st.update(handR=(-120, -40), mouth="smile", tilt=6)                                          # casual
    if S(2) <= t < S(3): st.update(brows=(-10, 12), mouth="flat")
    if E(3) <= t < JACKET[0]: st.update(eyes="closed", look=(0.0, -0.6))                                            # eye roll
    if JACKET[0] <= t < PLOP + 0.5: st.update(handR=(-160, 140), look=(-0.6, 0.6), brows=(-6, -6), mouth="flat", lean=8)
    if PLOP + 0.5 <= t < S(13): st.update(handR=(-110, 30), handL=(-50, 40), look=(-0.3, 0.6), brows=(-12, 12), mouth="flat")   # reading notebook
    if S(6) <= t < S(7): st.update(eyes="wide", mouth="o", brows=(20, 20))                                          # shocked
    if S(8) <= t < S(13): st.update(look=(-1.0, 0.0), brows=(-18, -18))
    if S(10) <= t < S(11): st.update(brows=(-14, 14), tilt=-8)
    if SIL[0] <= t < S(12):
        k = ss(SIL[0] + 0.1, SIL[1] - 0.3, t)
        st.update(look=(lerp(0.2, -1.0, k), 0.0), eyes="n", brows=(lerp(10, -26, k), lerp(10, -26, k)), mouth="flat", tilt=0)   # slowly turns
    if S(13) <= t < S(22):
        st.update(brows=(-16, 10), mouth="flat")
        for i in (13, 15, 17):
            if S(i) <= t < E(i): st.update(handR=(-160, -70 + 12 * math.sin(t * 9)), brows=(-18, -18))
        if S(19) <= t < E(19) + 0.2: st.update(handL=(-120, -195 + 12 * math.sin(t * 22)), handR=(120, -195), brows=(-26, -26), tilt=-10)
        if S(21) <= t < E(21) + 0.3: st.update(handL=(-120, -195 + 12 * math.sin(t * 22)), handR=(120, -195 + 12 * math.cos(t * 22)), brows=(-28, -28), tilt=-10)
    if S(22) <= t < GRAB:
        st.update(handR=(-170, 0), handL=HIPS_L, brows=(-10, 10), mouth="smirk", tilt=6)                             # hand stretched out
        if S(24) <= t: st.update(mouth="smile", eyes="happy" if amp("H", t) < 0.05 else "n", brows=(4, 4))
        if S(26) <= t: st.update(mouth="smirk", eyes="n", brows=(-8, 14), tilt=10)                                    # smug
        if S(28) <= t: st.update(brows=(-12, 12), handR=HIPS_R)
        if S(29) <= t + 0.0 and t > E(29) - 0.3: st.update(brows=(-24, -24), mouth="flat")
    if GRAB <= t:
        st.update(handR=(30, -230), handL=(-120, -60), brows=(-28, -28), mouth="o", pillow=True, tilt=-8, eyes="n")
        if RUN0 + 0.2 <= t: st.update(walk=t * 14)
    st["amp"] = amp("H", t)
    return st

def jacket(cv, t, gx, gs):
    if t < JACKET[0] + 0.25:
        x, y, rot = JX, 1300, -10
    else:
        hip = M.SEAT - 18 - 200 * gs["rise"]
        x, y, rot = gx + 84 + gs["handR"][0] - 20, hip - 224 + gs["handR"][1] + 30, 70
        if t > PLOP + 0.4:
            x, y, rot = JX, 1300, -10       # tossed back on the couch
    cv.save(); cv.translate(x, y); cv.rotate(rot)
    jp = poly([(-110, -60), (110, -60), (120, 60), (-120, 60)])
    cv.drawPath(jp, P(C("3b5a8a"))); cv.drawPath(jp, P(INK, stroke=6))
    cv.drawLine(0, -60, 0, 60, P(INK, stroke=4)); cv.drawLine(-60, -60, -20, 0, P(INK, stroke=4)); cv.drawLine(60, -60, 20, 0, P(INK, stroke=4))
    cv.restore()

def notebook_obj(cv, x, y, rot, s=1.0):
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(s, s)
    cv.drawRect(skia.Rect(-40, -52, 40, 52), P(C("c0392b"))); cv.drawRect(skia.Rect(-40, -52, 40, 52), P(INK, stroke=5))
    cv.drawRect(skia.Rect(-26, -30, 26, -10), P(C("f3e3b0")))
    cv.restore()

def notebook_fall(cv, t, gs, gx):
    if JACKET[0] + 0.25 <= t < PLOP:
        q = (t - JACKET[0] - 0.25) / (PLOP - JACKET[0] - 0.25)
        notebook_obj(cv, lerp(gx - 80, gx - 140, q), lerp(1150, 1580, q * q), 400 * q)
    elif PLOP <= t < PLOP + 0.5:
        notebook_obj(cv, gx - 140, 1580, 30)
    elif has_notebook(t):
        hip = M.SEAT - 18 - 200 * gs["rise"]
        notebook_obj(cv, gx + 84 + gs["handR"][0] + 10, hip - 224 + gs["handR"][1] - 30, -8, 1.1)

def notebook_insert(cv, t):
    a0, a1 = S(6) - 0.1, E(6) + 0.1
    if not (a0 <= t < a1): return
    k = ease_out_back(min(1, (t - a0) / 0.3), 1.6); a = min(1, (a1 - t) / 0.15)
    cv.save(); cv.translate(540, 820); cv.rotate(-3); cv.scale(k, k)
    page = skia.RRect.MakeRectXY(skia.Rect(-400, -330, 400, 330), 18, 18)
    cv.drawRRect(page, P(C("000000", 0.35 * a), blur=22)); cv.drawRRect(page, P(C("fffdf2", a))); cv.drawRRect(page, P(INK, stroke=6))
    for j in range(9):
        cv.drawLine(-380, -230 + j * 64, 380, -230 + j * 64, P(C("a9c8ea", a), stroke=3))
    cv.drawLine(-310, -330, -310, 330, P(C("f19aa8", a), stroke=4))
    text(cv, "MONEY RECORD", -280, -260, 44, C("141414", a), tf=TF_BLACK, align="l")
    text(cv, "Jan:  ₦150,000", -280, -150, 42, C("3a3f4a", a), tf=TF_B, align="l")
    text(cv, "Feb:  ₦300,000", -280, -86, 42, C("3a3f4a", a), tf=TF_B, align="l")
    text(cv, "Mar:  ₦400,000", -280, -22, 42, C("3a3f4a", a), tf=TF_B, align="l")
    rq = ss(REVEAL - 0.1, REVEAL + 0.3, t)
    if rq > 0:
        cv.save(); cv.translate(0, 140); cv.scale(0.6 + 0.4 * rq, 0.6 + 0.4 * rq)
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-370, -70, 370, 70), 20, 20), P(C("fff3a0", a)))
        text(cv, "SECRET SAVINGS:", 0, -12, 42, C("141414", a), tf=TF_BLACK)
        text(cv, "₦850,000", 0, 56, 70, C("e8262a", a), tf=TF_BLACK)
        cv.restore()
    text(cv, "(DON'T TELL BABY)", 0, 280, 32, C("8a8f99", a), tf=TF_B)
    cv.restore()

def bank_app(cv, t):
    a0, a1 = APP[0], APP[1] + 0.2
    if not (a0 <= t < a1): return
    k = ease_out_back(min(1, (t - a0) / 0.3), 1.8); a = min(1, (a1 - t) / 0.2)
    cv.save(); cv.translate(540, 800); cv.rotate(-4); cv.scale(k * 1.1, k * 1.1)
    body = skia.RRect.MakeRectXY(skia.Rect(-220, -380, 220, 380), 44, 44)
    cv.drawRRect(body, P(C("000000", 0.35 * a), blur=24)); cv.drawRRect(body, P(C("1d1d26", a)))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-196, -350, 196, 350), 26, 26), P(C("f4f6fa", a)))
    cv.drawRect(skia.Rect(-196, -350, 196, -150), P(C("2e7d4a", a)))
    text(cv, "Balance", 0, -280, 34, C("d8f0de", a), tf=TF_B)
    text(cv, "₦850,000", 0, -200, 70, C("ffffff", a), tf=TF_BLACK)
    text(cv, "Transfer to: Baby", 0, -70, 36, C("141414", a), tf=TF_B)
    text(cv, "₦100,000", 0, 30, 80, C("e8262a", a), tf=TF_BLACK)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-150, 150, 150, 240), 40, 40), P(C("2e7d4a", a)))
    text(cv, "SEND", 0, 212, 48, C("ffffff", a), tf=TF_BLACK)
    # shaking finger hovering
    fx = 40 + 8 * math.sin(t * 30)
    cv.drawCircle(fx, 300, 34, P(C("ffffff", a))); cv.drawCircle(fx, 300, 34, P(INK, stroke=5))
    cv.restore()

def G_CU(t, z=1.85):
    return (z, guy_x(t) + 30, 990 - 190 * guy_rise(t))
def H_CU(t, z=1.85):
    return (z, girl_x(t) - 10, 805)
MED = (1.05, 560, 1110)
TWO = (1.2, 560, 1060)

def camera(t):
    if t < S(1): return MED
    if JACKET[0] <= t < S(4): return (1.3, 560, 1150)
    if ZOOM[0] <= t < S(7):
        k = ss(ZOOM[0], ZOOM[0] + 0.25, t); return G_CU(t, lerp(1.8, 2.6, k))          # dramatic zoom on his face
    if SIL[0] <= t < S(12):
        k = (t - SIL[0]) / (S(12) - SIL[0]); return H_CU(t, lerp(1.7, 2.3, k))
    if S(22) <= t < S(23): return TWO
    if t >= FREEZE2[0]:
        k = ss(FREEZE2[0], FREEZE2[0] + 0.12, t); return (lerp(1.9, 2.4, k), guy_x(FREEZE2[0]) + 30, 990 - 190 * guy_rise(FREEZE2[0]))
    if GRAB <= t:
        k = ss(S(30), S(30) + 0.25, t); return (lerp(1.0, 1.4, k), lerp(540, 330, k), lerp(1130, 1000, k))
    shots = [(1, G_CU), (2, H_CU), (3, G_CU), (4, H_CU), (5, G_CU), (6, H_CU), (7, G_CU), (8, H_CU), (9, G_CU), (10, H_CU),
             (11, lambda t: G_CU(t, 2.1)), (12, G_CU), (13, H_CU), (14, G_CU), (15, H_CU), (16, G_CU), (17, H_CU), (18, G_CU),
             (19, lambda t: H_CU(t, 2.2)), (20, G_CU), (21, lambda t: H_CU(t, 2.1)), (23, lambda t: G_CU(t, 2.2)), (24, H_CU),
             (25, G_CU), (26, H_CU), (27, G_CU), (28, H_CU), (29, G_CU)]
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
    for a, amt in ((S(7), 12), (S(11) + 0.1, 16), (S(19), 12), (E(21) - 0.6, 12), (S(23), 14), (PLOP, 6)):
        if a <= t < a + 0.4:
            d = 1 - (t - a) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    return (0, 0)

HL = {0: {"MONEY?": "y"}, 1: {"BROKE.": "b", "HARD": "y"}, 2: {"YESTERDAY.": "y"}, 3: {"EVEN": "y", "HARDER.": "b"}, 4: {"THIS?": "y"},
      5: {"PERSONAL": "y", "DOCUMENTS!": "y"}, 6: {"SECRET": "y", "SAVINGS:": "y", "₦850,000\"?!": "b"}, 7: {"NOT": "b"},
      8: {"₦850,000,": "b", "₦5,000?": "y"}, 9: {"EMERGENCY": "y"}, 10: {"EMERGENCY": "y", "PREPARING": "y"}, 11: {"YOU!": "b"},
      12: {"EMERGENCIES": "y", "GENERAL!": "y"}, 13: {"SAVING?": "b"}, 14: {"FINANCIAL": "y", "DISCIPLINE.": "y"}, 15: {"BIRTHDAY": "y", "GIFT?": "y"},
      16: {"FINANCIAL": "b", "DISCIPLINE.": "b"}, 17: {"TRANSPORT?": "y"}, 18: {"RESPECT": "y", "PROCESS!": "b"}, 19: {"PROCESS?!": "b"},
      20: {"FINANCIALLY": "y", "STABLE!": "y"}, 21: {"STABLE,": "y", "STRANDED?!": "b"}, 22: {"₦100,000": "b"}, 23: {"HUNDRED": "b", "THOUSAND?!": "b"},
      24: {"CELEBRATE": "y"}, 25: {"SAVINGS!": "y"}, 26: {"EMERGENCY,": "b"}, 27: {"CASH…": "y"}, 28: {"WHY?": "y"},
      29: {"CASH": "y", "QUESTIONS!": "b"}, 30: {"FINANCIAL": "b", "FUTURE!": "b"}}
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


TOP = ["When she finds your secret savings…", "\"BABY, I'M BROKE\" 💀"]
TOP[1] = "\"BABY, I'M BROKE\""

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
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2 + sx, H / 2 + sy); cv.scale(z, z); cv.translate(-wx, -wy)
    CO.draw_room(cv, ta); CO.draw_couch_back(cv); CO.draw_couch_front(cv)
    gs = girl_state(ta); gx = girl_x(ta)
    if ta < JACKET[0] + 0.25 or ta > PLOP + 0.4: jacket(cv, ta, gx, gs)
    us = guy_state(ta); ux = guy_x(ta)
    M.draw_person(cv, ta, us, ux, "guy")
    M.draw_person(cv, ta, gs, gx, "girl")
    if JACKET[0] + 0.25 <= ta <= PLOP + 0.4: jacket(cv, ta, gx, gs)
    notebook_fall(cv, ta, gs, gx)
    if gs.get("pillow"):
        hip = M.SEAT - 18 - 200 * gs.get("rise", 0)
        pillow_shape(cv, gx + 84 + gs["handR"][0], hip - 224 + gs["handR"][1] - 40, 15 * math.sin(ta * 12))
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    if t >= FREEZE2[0]:
        fl = max(0, 1 - (t - FREEZE2[0]) / 0.15)
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("ffffff", 0.6 * fl)))
    draw_top(cv, t)
    bubble(cv, t, PLOP, PLOP + 0.7, "PLOP!", 380, 1200, col="ffd23f", size=60)
    notebook_insert(cv, t)
    tag(cv, t, S(8) + 0.3, S(10), "₦850,000 vs ₦5,000", 470, col="e8262a", fg="ffffff", size=58)
    for i in (14, 16):
        tag(cv, t, S(i), E(i) + 0.4, "FINANCIAL DISCIPLINE™", 470, col="3a7bd5", fg="ffffff", size=54)
    tag(cv, t, S(26) + 0.3, APP[0], "SHE'S THE EMERGENCY", 470, col="ff7aa8", fg="141414", size=54)
    bank_app(cv, t)
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
