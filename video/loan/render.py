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
GX, HX, GSTAND = 330.0, 740.0, 420.0
SEND = (E(4) + 0.1, S(5) - 0.05)
KISS = (E(5) + 0.05, E(5) + 0.6)
LEAVE = (E(5) + 0.5, E(5) + 1.3)
CAL = (E(5) + 1.2, S(6) - 0.15)
SPARK = S(2) + 0.6 * (E(2) - S(2))
ZOOM_H = (E(11), S(12))
DEST = (S(15), S(16))
GRAB = E(21) + 0.05
RUN0 = GRAB + 0.35
FREEZE2 = (S(22) + 0.9, TOTAL)
BLACK = TOTAL - 0.3
ANGRY = (8, 16, 18, 20, 22)

def at(t):
    return FREEZE2[0] if t >= FREEZE2[0] else t

def scene1(t):
    return t < CAL[0] + 0.5

def guy_x(t):
    if scene1(t):
        if t < S(0):
            return lerp(-200, GSTAND, ss(0.1, S(0) - 0.1, t))
        if t < LEAVE[0]:
            return GSTAND
        return lerp(GSTAND, -300, ss(LEAVE[0], LEAVE[1], t))
    if t < RUN0:
        return GX
    return GX - 260 * (t - RUN0) if t < RUN0 + 0.8 else GX - 208 + 0 * t

def girl_x(t):
    if t < RUN0 + 0.2:
        return HX
    return max(GX + 120, HX - 380 * (t - RUN0 - 0.2))

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
CLASP_L, CLASP_R = (60, 60), (-60, 60)
PLEAD_L, PLEAD_R = (70, -40), (-70, -40)
HIPS_L, HIPS_R = (-18, 168), (18, 168)

def walking(fn, t):
    return abs(fn(t + 0.03) - fn(t - 0.03)) > 2

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.0), brows=(10, 10), mouth="smirk", grass="mouth", tilt=0)
    st["blink"] = (t % 3.7) < 0.12
    if scene1(t):
        st.update(rise=1.0, mouth="smile", brows=(18, 18), handL=PLEAD_L, handR=PLEAD_R, tilt=8)      # sweet, pleading
        if t < S(0):
            st.update(handL=REST_L, handR=REST_R)
        if S(2) <= t < E(2):
            st.update(handR=(110, -120), tilt=4)
        if S(4) <= t < E(4):
            st.update(handR=(-60, -40), handL=(-110, -170), brows=(14, 14), tilt=0)       # hand on heart, other raised
        if SEND[0] <= t < S(5):
            st.update(eyes="wide", mouth="o", brows=(20, 20), handL=CLASP_L, handR=CLASP_R)
        if S(5) <= t:
            st.update(eyes="happy", mouth="smile", handL=UP_L, handR=UP_R, bob=30 * abs(math.sin(t * 9)) if t < E(5) else 0, tilt=0)
        if KISS[0] <= t:
            st.update(handR=(-20, -150), handL=REST_L, eyes="happy")
        if LEAVE[0] <= t:
            st.update(look=(-1.0, 0.0), handR=REST_R, mouth="smile")
        if walking(guy_x, t):
            st["walk"] = t * 9
        st["amp"] = amp("G", t)
        return st
    st.update(rise=0.0, look=(1.0, 0.0), brows=(8, 8))
    if S(7) <= t < S(8):
        st.update(brows=(16, 4), tilt=8, mouth="flat", look=(0.3, -0.6))                        # clueless
    if S(8) <= t < S(9):
        st.update(eyes="wide", brows=(20, 20), mouth="flat")
    if S(9) <= t < S(10):
        st.update(mouth="smile", brows=(16, 16), handR=(110, -120))
    if S(10) <= t < S(12):
        st.update(mouth="flat", brows=(6, 6), handR=(120, -40))                                  # serious, it makes sense
    if S(13) <= t < S(14):
        st.update(mouth="flat", brows=(4, 4), handR=(120, -60), look=(0.6, -0.3))
    if DEST[0] <= t < DEST[1]:
        st.update(look=(0.2, -0.9), brows=(10, 10), mouth="smile", handL=(-130, -160), handR=(130, -160), eyes="happy")
    if S(16) <= t < S(17):
        st.update(eyes="wide", brows=(18, 18), mouth="flat")
    if S(17) <= t < S(18):
        st.update(brows=(-12, -12), mouth="flat", handL=(-140, -40), handR=(140, -40), tilt=-6)  # offended
    if S(18) <= t < S(19):
        st.update(eyes="wide", brows=(22, 22), mouth="o", sweat=True)
    if S(19) <= t < GRAB:
        st.update(mouth="smile", brows=(16, 16), tilt=10, handL=PLEAD_L, handR=PLEAD_R, eyes="n")  # shameless
        if S(20) <= t < S(21):
            st.update(eyes="wide", mouth="flat")
    if GRAB <= t:
        k = ss(GRAB, RUN0, t)
        st.update(rise=k, eyes="wide", mouth="o", brows=(24, 24), sweat=True, handL=UP_L, handR=UP_R, look=(1.0, 0.0), tilt=-8)
        if RUN0 <= t:
            st.update(walk=t * 16, lean=-10)
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=CLASP_L, handR=CLASP_R, look=(-1.0, 0.0), brows=(-8, 12), mouth="flat", tilt=-4)
    st["blink"] = (t % 4.1) < 0.12
    if scene1(t):
        if S(1) <= t < E(1): st.update(brows=(-14, 10), handR=(-140, -40))
        if S(3) <= t < E(3) + 0.3: st.update(brows=(-12, 14), tilt=-8)
        if SEND[0] <= t < S(5) + 0.4:
            st.update(phone=True, handR=(-110, 40), look=(-0.5, 0.6), brows=(10, 10), mouth="flat", tilt=6)   # reluctant
        if S(5) <= t: st.update(brows=(8, 8), mouth="smile", tilt=6)
        if LEAVE[0] <= t: st.update(look=(-1.0, 0.0), mouth="flat", brows=(4, 4))
        st["amp"] = amp("H", t)
        return st
    st.update(phone=True, handR=(-110, 40), look=(-0.5, 0.6), brows=(-6, -6), mouth="flat", tilt=0)
    if S(6) <= t: st.update(phone=False, handR=CLASP_R, look=(-1.0, 0.0), brows=(-10, 10))
    if S(8) <= t < E(8) + 0.2:
        st.update(handL=(-120, -190 + 10 * math.sin(t * 20)), handR=(120, -190 + 10 * math.cos(t * 20)), brows=(-24, -24), tilt=-8)
    if S(10) <= t < E(10) + 0.2: st.update(handR=(-150, -60), brows=(-18, -18))
    if E(10) + 0.2 <= t < S(12):
        k = ss(E(11), E(11) + 0.6, t)
        st.update(look=(lerp(0.0, -1.0, k), 0.0) if E(11) <= t else (0.0, 0.0), brows=(-14, -14), mouth="flat", eyes="n")
    if S(12) <= t < S(16): st.update(brows=(-16, 10), handL=HIPS_L, handR=HIPS_R)
    if S(14) <= t < S(15): st.update(brows=(-10, 16), tilt=-8)
    if DEST[0] <= t < DEST[1]: st.update(eyes="wide", mouth="o", brows=(-6, 16))
    if S(16) <= t < S(17): st.update(handR=(-170, -80 + 14 * math.sin(t * 9)), brows=(-22, -22))
    if S(17) <= t < S(18): st.update(brows=(-20, -20))
    if S(18) <= t < E(18) + 0.3:
        st.update(handL=(-120, -195 + 12 * math.sin(t * 22)), handR=(120, -195 + 12 * math.cos(t * 22)), brows=(-28, -28), tilt=-10)
    if S(19) <= t: st.update(eyes="wide", brows=(18, 18), mouth="o", handL=CLASP_L, handR=CLASP_R, tilt=0)   # disbelief
    if S(20) <= t < E(20) + 0.2: st.update(handL=(-120, -190), handR=(120, -190), brows=(-26, -26))
    if S(21) <= t: st.update(eyes="n", brows=(-24, -24), mouth="flat")
    if GRAB <= t:
        st.update(rise=ss(GRAB, RUN0, t), handR=(30, -230), handL=(-120, -60), brows=(-28, -28), mouth="o", pillow=True, tilt=-8)
        if RUN0 + 0.2 <= t: st.update(walk=t * 14)
    st["amp"] = amp("H", t)
    return st

def G_CU(t, z=1.85):
    us = guy_state(t); r = us.get("rise", 0)
    return (z, guy_x(t) + 30, 990 - 190 * r)
def H_CU(t, z=1.85):
    return (z, girl_x(t) - 20, 1040)
MED = (1.2, 560, 1060)
TWO = (1.3, 540, 1060)

def camera(t):
    if t < S(1):
        return MED
    if SEND[0] <= t < S(5):
        return (1.35, 600, 1060)
    if scene1(t) and S(5) <= t:
        return MED
    if t < S(6) + 0.1:
        return TWO
    if ZOOM_H[0] <= t < ZOOM_H[1]:
        k = ss(ZOOM_H[0], ZOOM_H[0] + 0.9, t); return H_CU(t, lerp(1.6, 2.5, k))
    if DEST[0] <= t < DEST[1]:
        k = (t - DEST[0]) / (DEST[1] - DEST[0]); return G_CU(t, lerp(1.7, 2.1, k))
    if S(18) <= t < S(19):
        k = ss(S(18), S(18) + 0.3, t); return H_CU(t, lerp(1.8, 2.6, k))
    if t >= FREEZE2[0]:
        k = ss(FREEZE2[0], FREEZE2[0] + 0.12, t); us = guy_state(FREEZE2[0])
        return (lerp(1.9, 2.4, k), guy_x(FREEZE2[0]) + 30, 990 - 190 * us["rise"])
    if GRAB <= t:
        k = ss(S(22), S(22) + 0.25, t); return (lerp(1.0, 1.4, k), lerp(540, 330, k), lerp(1130, 1000, k))
    shots = [(1, H_CU), (2, G_CU), (3, H_CU), (4, G_CU), (6, H_CU), (7, G_CU), (8, lambda t: H_CU(t, 2.1)), (9, G_CU),
             (10, H_CU), (11, G_CU), (12, H_CU), (13, G_CU), (14, H_CU), (16, lambda t: H_CU(t, 2.1)), (17, G_CU),
             (19, lambda t: G_CU(t, 2.1)), (20, lambda t: H_CU(t, 2.3)), (21, G_CU)]
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
    for i, amt in ((8, 12), (16, 12), (18, 18), (20, 16)):
        if S(i) <= t < S(i) + 0.4:
            d = 1 - (t - S(i)) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    for a in (E(7) + 0.02, E(19) + 0.02):
        if a <= t < a + 0.25:
            d = 1 - (t - a) / 0.25; return (10 * d * math.sin(t * 90), 0)
    return (0, 0)

HL = {0: {"LEND": "y", "MONEY?": "b"}, 1: {"AGAIN?": "b", "LAST": "y", "WEEK?": "y"}, 2: {"EMERGENCY.": "y", "TOMORROW.": "b"},
      3: {"SURE?": "y"}, 4: {"MOTHER'S": "y", "LIFE!": "y", "TOMORROW,": "b"}, 5: {"BEST": "y", "GIRLFRIEND": "y"},
      6: {"MONEY": "y"}, 7: {"WHICH": "b", "MONEY?": "b"}, 8: {"TOMORROW!": "b"}, 9: {"THAT": "y"}, 10: {"THREE": "b", "MONTHS!": "b"},
      11: {"TOMORROW": "y", "PATIENT.": "b"}, 12: {"TOMORROW": "b"}, 13: {"SOON.": "y", "ENTER.": "b"}, 14: {"WHERE?": "y"},
      15: {"DESTINY.": "b"}, 16: {"JULIUS!": "b", "MONEY!": "y"}, 17: {"PRESSURE": "y", "STEAL?": "b"}, 18: {"MONEY!": "b"},
      19: {"ANOTHER": "b", "SMALL": "y"}, 20: {"WHAT?!": "b"}, 21: {"TOMORROW.": "b"}, 22: {"TRUST": "y", "TOMORROW?!": "b"}}
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

def heaven(cv, t, gx):
    if not (DEST[0] <= t < DEST[1] + 0.2):
        return
    a = min(1, (t - DEST[0]) / 0.3, (DEST[1] + 0.2 - t) / 0.2)
    cv.drawPath(poly([(gx - 70, -200), (gx + 70, -200), (gx + 240, 1600), (gx - 240, 1600)]), P(C("fff6c8", 0.45 * a), blur=20))
    cv.drawCircle(gx, 820, 260, P(C("fff3a0", 0.35 * a), blur=60))
    hy = 700 + 8 * math.sin(t * 4)
    cv.drawOval(skia.Rect(gx - 80, hy - 18, gx + 80, hy + 18), P(C("ffd21f", a), stroke=12))
    for j in range(6):
        q = ((t * 0.6) + j / 6) % 1
        sparkles(cv, t, gx + 150 * math.sin(j * 2.3), 900 - 300 * q, DEST[0], 2.4, 1, "ffffff")

def phone_send(cv, t):
    a0, a1 = SEND[0], S(5) + 0.4
    if not (a0 <= t < a1):
        return
    k = ease_out_back(min(1, (t - a0) / 0.3), 1.8); a = min(1, (a1 - t) / 0.2)
    sent = t > a0 + 0.8
    cv.save(); cv.translate(540, 800); cv.rotate(-4); cv.scale(k * 1.1, k * 1.1)
    body = skia.RRect.MakeRectXY(skia.Rect(-220, -380, 220, 380), 44, 44)
    cv.drawRRect(body, P(C("000000", 0.35 * a), blur=24)); cv.drawRRect(body, P(C("1d1d26", a)))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-196, -350, 196, 350), 26, 26), P(C("f4f6fa", a)))
    cv.drawRect(skia.Rect(-196, -350, 196, -230), P(C("2e7d4a", a)))
    text(cv, "Send Money", 0, -275, 44, C("ffffff", a), tf=TF_BLACK)
    text(cv, "To: Julius", 0, -160, 40, C("141414", a), tf=TF_B)
    text(cv, "₦50,000", 0, -40, 96, C("141414", a), tf=TF_BLACK)
    text(cv, "Reason: \"emergency\"", 0, 40, 30, C("6a7080", a), tf=TF_B)
    if sent:
        cv.drawCircle(0, 170, 74, P(C("3ccf5a", a))); cv.drawCircle(0, 170, 74, P(INK, stroke=5))
        text(cv, "✓", 0, 205, 100, C("ffffff", a), tf=TF_BLACK)
        text(cv, "SENT", 0, 300, 44, C("2e7d4a", a), tf=TF_BLACK)
    else:
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-150, 130, 150, 220), 40, 40), P(C("2e7d4a", a)))
        text(cv, "SEND", 0, 192, 48, C("ffffff", a), tf=TF_BLACK)
    cv.restore()

MONTHS = ["TOMORROW?", "WEEK 1", "WEEK 2", "WEEK 3", "MONTH 1", "MONTH 2", "MONTH 3"]
def calendar(cv, t):
    if not (CAL[0] <= t < CAL[1]):
        return
    a = min(1, (t - CAL[0]) / 0.15, (CAL[1] - t) / 0.15)
    cv.drawRect(skia.Rect(0, 0, W, H), P(C("1b1b24", a)))
    q = (t - CAL[0]) / (CAL[1] - CAL[0])
    idx = min(len(MONTHS) - 1, int(q * 1.4 * len(MONTHS)))
    flip = (q * 1.4 * len(MONTHS)) % 1 if idx < len(MONTHS) - 1 else 1
    cv.save(); cv.translate(540, 900)
    page = skia.RRect.MakeRectXY(skia.Rect(-300, -320, 300, 320), 28, 28)
    cv.drawRRect(page, P(C("ffffff", a))); cv.drawRRect(page, P(INK, stroke=8))
    cv.drawRect(skia.Rect(-300, -320, 300, -180), P(C("e8262a", a)))
    text(cv, "CALENDAR", 0, -230, 52, C("ffffff", a), tf=TF_BLACK)
    text(cv, MONTHS[idx], 0, 40, 90 if len(MONTHS[idx]) < 8 else 76, C("141414", a), tf=TF_BLACK)
    for j in (-150, 0, 150):
        cv.drawCircle(j, -320, 18, P(C("9aa0ad", a))); cv.drawCircle(j, -320, 18, P(INK, stroke=4))
    if flip < 0.5:   # page flying off
        h = 640 * (1 - flip * 2)
        cv.drawRect(skia.Rect(-300, -320, 300, -320 + h), P(C("f0f0f0", a * 0.9)))
    cv.restore()
    if q > 0.75:
        text(cv, "3 MONTHS LATER…", 540, 1400, 80, C("ffd21f", a), tf=TF_BLACK)

TOP = ["When he borrows money \"till tomorrow\"…", "TOMORROW NEVER CAME"]

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
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2 + sx, H / 2 + sy); cv.scale(z, z); cv.translate(-wx, -wy)
    CO.draw_room(cv, ta); CO.draw_couch_back(cv); CO.draw_couch_front(cv)
    gs = girl_state(ta); gx = girl_x(ta)
    M.draw_person(cv, ta, gs, gx, "girl")
    us = guy_state(ta); ux = guy_x(ta)
    heaven(cv, ta, ux)
    if ux > -280:
        M.draw_person(cv, ta, us, ux, "guy")
    if gs.get("pillow"):
        hip = M.SEAT - 18 - 200 * gs.get("rise", 0)
        pillow_shape(cv, gx + 84 + gs["handR"][0], hip - 224 + gs["handR"][1] - 40, 15 * math.sin(ta * 12))
    hip_g = M.SEAT - 18 - 200 * us.get("rise", 0)
    sparkles(cv, ta, ux, hip_g - 366, SPARK, 0.9)
    if KISS[0] <= ta < KISS[0] + 1.2:
        q = (ta - KISS[0]) / 1.2
        M.heart(cv, lerp(ux + 60, gx - 40, q), hip_g - 380 - 120 * math.sin(math.pi * q), 0.8 * (1 - 0.3 * q))
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    if t >= FREEZE2[0]:
        fl = max(0, 1 - (t - FREEZE2[0]) / 0.15)
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("ffffff", 0.6 * fl)))
    draw_top(cv, t)
    tag(cv, t, S(4) + 0.3, SEND[0], "\"ON MY MOTHER'S LIFE\"", 470, col="ffd23f", size=54)
    tag(cv, t, S(5), CAL[0], "DEBT: ₦50,000", 470, col="e8262a", fg="ffffff", size=58)
    tag(cv, t, S(6) + 0.2, S(8), "DAYS UNPAID: 92", 470, col="e8262a", fg="ffffff", size=58)
    tag(cv, t, ZOOM_H[0] + 0.2, ZOOM_H[1], "\"BE PATIENT\"", 470, col="ffffff", size=60)
    tag(cv, t, S(19) + 1.4, S(21), "NEW DEBT REQUEST", 470, col="e8262a", fg="ffffff", size=58)
    phone_send(cv, t)
    calendar(cv, t)
    if not (CAL[0] <= t < CAL[1]):
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
