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
UNLOCK = (E(7) + 0.05, S(8))
OPEN = E(8) + 0.1
TURN = (E(13), S(14))
SCRATCH = E(14) + 0.02
SIREN = E(16) + 0.02
LOCK = E(22) + 0.1
GIVEBACK = S(26) - 0.3
REUNLOCK = (E(29) + 0.05, S(30))
FROZE = (E(30), S(31))
BLACK = E(31) + 0.6
ANGRY = (14, 16, 21, 31)

def guy_has(t):  return UNLOCK[0] <= t < GIVEBACK
def girl_has(t): return t < UNLOCK[0] - 0.2 or t >= GIVEBACK

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
CLASP_L, CLASP_R = (60, 60), (-60, 60)

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.0), brows=(8, 8), mouth="smirk", grass="mouth", tilt=0, rise=0.0)
    st["blink"] = (t % 3.7) < 0.12
    if t < S(0): st.update(phone=True, handL=(90, 40), look=(0.4, 0.7), lean=-6)
    if S(0) <= t < S(7): st.update(brows=(-8, 12), mouth="flat", tilt=-4)                              # curious, suspicious
    if S(4) <= t < E(4): st.update(handR=(130, -80), brows=(-12, 10))
    if S(6) <= t < E(6): st.update(handR=(-60, -40), mouth="smile", eyes="happy" if amp("G", t) < 0.05 else "n", brows=(14, 14), tilt=6)   # open book
    if guy_has(t):
        st.update(phone=True, handL=(90, 30), look=(0.4, 0.7), mouth="flat", brows=(6, 6))
        if S(9) <= t < S(14): st.update(brows=(16, 4), mouth="flat", tilt=6)                           # confused
        if TURN[0] <= t < S(15): st.update(look=(lerp(0.4, 1.0, ss(TURN[0], TURN[1], t)), lerp(0.7, 0.0, ss(TURN[0], TURN[1], t))), eyes="wide", brows=(22, 22), mouth="o")
        if S(15) <= t < S(18): st.update(look=(1.0, 0.0), eyes="wide", brows=(18, 18), mouth="flat")
        if S(16) <= t < E(16): st.update(handR=(140, -90), mouth="o", brows=(22, 22))
        if S(18) <= t: st.update(look=(0.4, 0.7), eyes="wide", brows=(22, 22), mouth="o", sweat=True)   # shocked, sweating
        if S(21) <= t < S(22): st.update(look=(1.0, 0.0), handR=(140, -90))
        if S(22) <= t: st.update(look=(1.0, 0.0), sweat=True)
        if LOCK <= t: st.update(look=(1.0, 0.0), handL=(60, 60), eyes="wide", mouth="flat")
        if S(23) <= t < E(23): st.update(handR=(140, -60), mouth="o")
        if S(25) <= t: st.update(mouth="smile", handR=(120, -60), brows=(16, 16), handL=(150, 0) if t > GIVEBACK - 0.5 else (60, 60))
    if GIVEBACK <= t < FROZE[0]:
        st.update(look=(1.0, 0.0), mouth="smile", brows=(14, 14), sweat=True)
        if S(27) <= t < E(27): st.update(handL=(-130, -60), handR=(130, -60), lean=-8, mouth="flat")  # suddenly respectful, retreating
        if S(29) <= t: st.update(handR=(130, -110), mouth="smile", eyes="n", brows=(16, 16))
        if S(30) <= t: st.update(eyes="wide", mouth="flat", brows=(20, 20), handR=REST_R)
    if FROZE[0] <= t:
        st.update(look=(1.0, 0.0), eyes="wide", mouth="o", brows=(26, 26), sweat=True, handL=REST_L, handR=REST_R, lean=0, tilt=0)   # frozen in fear
        if S(31) <= t: st.update(handL=(-120, -100), handR=(120, -100), mouth="smile")
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=CLASP_L, handR=CLASP_R, look=(-1.0, 0.0), brows=(-6, 12), mouth="flat", tilt=-4, rise=0.0)
    st["blink"] = (t % 4.1) < 0.12
    if girl_has(t) and t < S(0): st.update(phone=True, handR=(-110, 40), look=(-0.4, 0.7), brows=(4, 4))
    if S(1) <= t < S(7): st.update(brows=(-12, 12), mouth="flat")                                       # calm, suspicious
    if S(5) <= t < E(5): st.update(handR=(-150, -60), brows=(-16, 10), tilt=-8)
    if S(7) <= t < UNLOCK[0]: st.update(phone=True, handR=(-160, -40), brows=(-8, 10))
    if UNLOCK[0] <= t < GIVEBACK:
        st.update(look=(-0.6, 0.3), brows=(4, 4), mouth="flat", tilt=4)                                   # unbothered
        if S(10) <= t < E(10): st.update(mouth="smile", eyes="happy" if amp("H", t) < 0.05 else "n", tilt=8)
        if S(11) <= t < S(14): st.update(mouth="smirk", brows=(-4, 10))                                  # slightly amused
        if S(15) <= t: st.update(look=(-1.0, 0.0), mouth="smirk", brows=(-6, 14), tilt=8)               # smug
        if S(17) <= t < E(17): st.update(eyes="happy" if amp("H", t) < 0.05 else "n", mouth="smile")
        if S(20) <= t < S(23): st.update(mouth="smirk", brows=(-8, 16), handR=(-130, -60) if S(22) <= t < E(22) else CLASP_R)
    if GIVEBACK <= t:
        st.update(phone=True, handR=(-110, 40), look=(-1.0, 0.0), mouth="smile", brows=(6, 6), tilt=6)
        if S(24) <= t < E(24): st.update(brows=(-10, 14), mouth="flat")
        if S(28) <= t < E(28): st.update(eyes="happy" if amp("H", t) < 0.05 else "n", brows=(14, 14), tilt=10)
        if REUNLOCK[0] <= t: st.update(look=(-0.5, 0.6), mouth="smile")
        if S(30) <= t: st.update(look=(-1.0, 0.0), mouth="smile", eyes="happy" if amp("H", t) < 0.05 else "n", brows=(14, 14), tilt=10)   # innocent smile
    st["amp"] = amp("H", t)
    return st

def phone_frame(cv, a, k, rot=-4, s=1.15):
    cv.translate(540, 820); cv.rotate(rot); cv.scale(k * s, k * s)
    body = skia.RRect.MakeRectXY(skia.Rect(-220, -380, 220, 380), 44, 44)
    cv.drawRRect(body, P(C("000000", 0.35 * a), blur=24)); cv.drawRRect(body, P(C("1d1d26", a)))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-196, -350, 196, 350), 26, 26), P(C("f4f6fa", a)))

def win(t, a0, a1):
    if not (a0 <= t < a1): return None
    return ease_out_back(min(1, (t - a0) / 0.25), 1.6), min(1, (a1 - t) / 0.15)

def folder_icon(cv, x, y, label, a, hl=False, col="f2c230"):
    if hl: cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 80, y - 70, x + 80, y + 100), 20, 20), P(C("fff3a0", a)))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 60, y - 40, x + 60, y + 40), 12, 12), P(C(col, a)))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 60, y - 52, x - 10, y - 30), 8, 8), P(C(col, a)))
    text(cv, label, x, y + 80, 24 if len(label) < 10 else 20, C("141414", a), tf=TF_BLACK if hl else TF_B)

def phone_overlays(cv, t):
    w = win(t, S(8) - 0.1, E(9) + 0.3)
    if w:
        k, a = w; cv.save(); phone_frame(cv, a, k)
        if t < OPEN:
            text(cv, "Files", -170, -290, 44, C("141414", a), tf=TF_BLACK, align="l")
            for j, (lab, x, y) in enumerate((("Photos", -100, -150), ("Work", 100, -150), ("Music", -100, 50), ("IMPORTANT", 100, 50))):
                folder_icon(cv, x, y, lab, a, hl=lab == "IMPORTANT", col="e8262a" if lab == "IMPORTANT" else "f2c230")
        else:
            text(cv, "IMPORTANT", -170, -290, 44, C("e8262a", a), tf=TF_BLACK, align="l")
            text(cv, "247 screenshots", -170, -245, 26, C("8a8f99", a), tf=TF_B, align="l")
            for j in range(12):
                x = -130 + (j % 3) * 130; y = -170 + (j // 3) * 130
                cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 55, y - 50, x + 55, y + 60), 10, 10), P(C("e2e5ee", a)))
                cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 40, y - 30, x + 30, y - 10), 8, 8), P(C("4a90e2", a)))
                cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 30, y + 5, x + 40, y + 25), 8, 8), P(C("c9ccd6", a)))
        cv.restore()
    for i, msg in ((11, ("I'll send the", "money tomorrow.")), (12, ("Baby, I'm five", "minutes away.")), (13, ("I didn't eat", "your food!"))):
        w = win(t, S(i) - 0.1, E(i) + 0.35 if i != 13 else TURN[1])
        if w:
            k, a = w; cv.save(); phone_frame(cv, a, k, rot=-4 + (i - 12) * 3)
            text(cv, "Screenshot", 0, -290, 34, C("8a8f99", a), tf=TF_B)
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-150, -100, 176, 60), 30, 30), P(C("4a90e2", a)))
            for li, ln in enumerate(msg):
                text(cv, ln, -128, -38 + li * 52, 32, C("ffffff", a), tf=TF_BLACK, align="l")
            text(cv, "Him • 3 months ago", 176, 110, 26, C("8a8f99", a), tf=TF_B, align="r")
            cv.drawCircle(150, 230, 46, P(C("e8262a", a)))
            text(cv, "EVIDENCE", 0, 330, 1, C("ffffff", 0), tf=TF_B)
            cv.restore()
            chip(cv, 760, 1130, f"EVIDENCE #{i - 10}", a=a, col="e8262a", fg="ffffff", size=46)
    w = win(t, S(18) - 0.1, E(20) + 0.5) or win(t, S(22), E(22) + 0.3)
    if w:
        k, a = w; cv.save(); phone_frame(cv, a, k)
        text(cv, "EXCUSES HE", 0, -280, 42, C("e8262a", a), tf=TF_BLACK)
        text(cv, "HAS USED", 0, -230, 42, C("e8262a", a), tf=TF_BLACK)
        items = ["\"My phone died\"", "\"I'm 5 mins away\"", "\"I didn't see it\"", "\"I was sleeping\"", "\"Traffic was bad\"", "\"Network was bad\""]
        for j, it in enumerate(items):
            y = -150 + j * 62
            last = j == len(items) - 1 and t >= S(22)
            if last: cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-180, y - 40, 180, y + 16), 12, 12), P(C("fff3a0", a)))
            text(cv, f"{j + 1}. {it}", -170, y, 30, C("141414", a), tf=TF_BLACK if last else TF_B, align="l")
        text(cv, "Last updated: YESTERDAY", 0, 270, 28, C("e8262a", a), tf=TF_BLACK)
        cv.restore()
    w = win(t, S(30) + 0.8, FROZE[1] + 0.2)
    if w:
        k, a = w; cv.save(); phone_frame(cv, a, k)
        cv.drawRect(skia.Rect(-196, -350, 196, 350), P(C("1a0e14", a)))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-120, -180, 120, 0), 20, 20), P(C("8a1c2c", a)))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-120, -205, -30, -170), 10, 10), P(C("8a1c2c", a)))
        text(cv, "THINGS I STILL", 0, 90, 38, C("ffffff", a), tf=TF_BLACK)
        text(cv, "FORGIVE HIM FOR", 0, 140, 38, C("ffffff", a), tf=TF_BLACK)
        text(cv, "1,284 items", 0, 210, 30, C("ff6b6b", a), tf=TF_BLACK)
        cv.restore()

def G_CU(t, z=1.85):
    return (z, GX + 30, 990)
def H_CU(t, z=1.85):
    return (z, HX - 20, 1040)
MED = (1.2, 560, 1060)
TWO = (1.35, 540, 1060)

def camera(t):
    if t < S(1): return MED
    if UNLOCK[0] <= t < S(8): return (1.5, GX + 120, 1060)
    if TURN[0] <= t < S(14):
        k = (t - TURN[0]) / (TURN[1] - TURN[0]); return G_CU(t, lerp(1.8, 2.2, k))
    if S(18) <= t < S(21):
        k = (t - S(18)) / (S(21) - S(18)); return G_CU(t, lerp(1.7, 2.3, k))               # gradual zoom on him
    if REUNLOCK[0] <= t < S(30): return H_CU(t, 1.8)
    if FROZE[0] <= t:
        k = ss(FROZE[0], FROZE[0] + 0.3, t); return G_CU(t, lerp(1.8, 2.6, k))             # dramatic zoom
    shots = [(1, H_CU), (2, G_CU), (3, H_CU), (4, G_CU), (5, lambda t: H_CU(t, 2.0)), (6, G_CU), (7, H_CU), (8, G_CU),
             (10, H_CU), (11, G_CU), (14, lambda t: G_CU(t, 2.3)), (15, H_CU), (16, lambda t: G_CU(t, 2.1)), (17, H_CU),
             (21, lambda t: G_CU(t, 2.3)), (22, H_CU), (23, G_CU), (24, H_CU), (25, G_CU), (26, H_CU), (27, G_CU),
             (28, H_CU), (29, G_CU), (30, H_CU)]
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
    for a, amt in ((S(14), 16), (S(16), 12), (S(21), 12)):
        if a <= t < a + 0.4:
            d = 1 - (t - a) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    return (0, 0)

HL = {0: {"PASSWORD?": "b"}, 1: {"WHY?": "y"}, 2: {"CHECK": "y"}, 3: {"WHAT?": "y"}, 4: {"HIDING": "b"}, 5: {"YOU": "b", "HIDING": "y"},
      6: {"NEVER!": "y", "OPEN": "y", "BOOK.": "y"}, 7: {"1234.": "b"}, 8: {"FOLDER?": "y"}, 9: {"SCREENSHOTS?": "b", "CONVERSATIONS?": "y"},
      10: {"MEMORIES.": "y"}, 11: {"TOMORROW.": "b"}, 12: {"FIVE": "b", "MINUTES": "b"}, 13: {"DIDN'T": "b", "FOOD!": "y"},
      14: {"EVIDENCE?!": "b"}, 15: {"RECORDS.": "y"}, 16: {"RECORDS?!": "y", "INVESTIGATION?!": "b"}, 17: {"PREDICTABLE.": "b"},
      18: {"THIS?": "y"}, 19: {"LIST?!": "b"}, 20: {"EVERY": "y", "WEEK.": "y"}, 21: {"EVERY": "b", "WEEK?!": "b"},
      22: {"YESTERDAY.": "y", "NETWORK": "b", "GAMES.": "b"}, 23: {"PHONE!": "y"}, 24: {"MY": "b"}, 25: {"PRIVATE!": "y"},
      26: {"CHECK": "y"}, 27: {"ENOUGH.": "y", "PRIVACY": "b"}, 28: {"CHANGED?": "y"}, 29: {"DETECTIVE!": "b"},
      30: {"FORGIVE": "b"}, 31: {"NOT": "b", "OPEN": "b"}}
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





TOP = ["When your boyfriend asks for your password…", "SHE HAD RECEIPTS"]

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
    CO.draw_room(cv, t); CO.draw_couch_back(cv); CO.draw_couch_front(cv)
    M.draw_person(cv, t, girl_state(t), HX, "girl")
    M.draw_person(cv, t, guy_state(t), GX, "guy")
    if SIREN <= t < SIREN + 1.2:      # police lights
        q = (t * 6) % 1
        cv.drawRect(skia.Rect(-200, -200, W + 200, H + 200), P(C("e8262a" if q < 0.5 else "3a7bd5", 0.18)))
    if FROZE[0] <= t:
        cv.drawRect(skia.Rect(-200, -200, W + 200, H + 200), P(C("2a0010", 0.25 * min(1, (t - FROZE[0]) / 0.3))))
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    draw_top(cv, t)
    tag(cv, t, S(7), UNLOCK[1] + 0.5, "PASSWORD: 1234", 470, col="ffd23f", size=58)
    tag(cv, t, SIREN, S(17) + 0.3, "UNDER INVESTIGATION", 470, col="e8262a", fg="ffffff", size=58)
    tag(cv, t, S(29) + 0.3, REUNLOCK[1], "DATING A DETECTIVE", 470, col="3a7bd5", fg="ffffff", size=58)
    phone_overlays(cv, t)
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
