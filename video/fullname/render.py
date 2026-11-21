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
GX, HX, GMEET, TRASHX = 330.0, 880.0, 500.0, 220.0
FREEZE = (E(0), S(1))                    # he freezes ~1s
WALK = (E(4) + 0.1, S(5) - 0.1)
STARE = (E(13), S(14))
SWEAT = (E(16), S(17))
REVEAL = S(24)
GRAB = (S(27) - 0.2, S(27) + 0.9)
RUN0 = S(29) + 0.35
FREEZE2 = (RUN0 + 0.12, TOTAL)
BLACK = TOTAL - 0.3
ANGRY = (4, 12, 22, 25, 29)

def at(t):
    return FREEZE2[0] if t >= FREEZE2[0] else t

def guy_x(t):
    if t < WALK[0]: return GX
    if t < GRAB[0]: return lerp(GX, GMEET, ss(WALK[0], WALK[1], t))
    if t < GRAB[1]: return lerp(GMEET, TRASHX + 90, ss(GRAB[0], GRAB[1], t))
    if t < RUN0: return lerp(TRASHX + 90, TRASHX + 10, ss(GRAB[1], S(29), t))
    return TRASHX + 10 - 700 * (t - RUN0)

def has_bag(t):
    return t >= GRAB[1] - 0.2

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
CROSS_L, CROSS_R = (60, 60), (-60, 60)
HIPS_L, HIPS_R = (-18, 168), (18, 168)

def walking(t):
    return abs(guy_x(t + 0.03) - guy_x(t - 0.03)) > 2

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.0), brows=(8, 8), mouth="smirk", grass="mouth", tilt=0, rise=0.0)
    st["blink"] = (t % 3.7) < 0.12
    if t < S(0):                                       # chilling with snacks
        eat = (t % 1.6) < 0.5
        st.update(look=(0.0, 0.1), mouth="o" if eat else "smile", eyes="happy" if not eat else "n", handL=(80, 40), handR=(-50, -110) if eat else (60, 40), lean=-6, snack=True)
    elif t < S(1):                                     # FROZEN
        st.update(look=(0.0, 0.0), eyes="wide", mouth="o", brows=(24, 24), handL=(80, 40), handR=(-50, -110), snack=True, lean=-6)
    elif t < WALK[0]:
        st.update(eyes="wide", brows=(20, 20), mouth="flat", snack=t < S(2), handL=(80, 40) if t < S(2) else REST_L)
        if S(1) <= t < E(1): st.update(mouth="smile")
        if S(4) <= t: st.update(rise=ss(S(4) + 0.2, E(4), t), sweat=True)
    else:
        st.update(rise=1.0, mouth="smile", brows=(16, 16), handL=CROSS_L, handR=CROSS_R)        # nervous smile approaching
        if S(6) <= t < S(7): st.update(brows=(16, 4), tilt=8, mouth="flat")                        # confused
        if S(7) <= t < STARE[0]:
            st.update(look=(0.3, -0.8), brows=(16, 8), handR=(-70, -150), mouth="flat", sweat=True)
            for i in (7, 9, 11):
                if S(i) <= t < E(i): st.update(look=(1.0, 0.0), handR=(130, -80), mouth="smile")
            if S(13) <= t: st.update(look=(1.0, 0.0), handL=(-140, -60), handR=(140, -60), brows=(20, 20))
        if STARE[0] <= t < S(17):
            st.update(eyes="wide", brows=(20, 20), mouth="flat", sweat=t >= SWEAT[0])
            if S(15) <= t < E(15): st.update(handR=(-60, -40), handL=(-110, -170), mouth="smile")
        if S(17) <= t < REVEAL:
            st.update(sweat=True, eyes="wide", mouth="smile", brows=(20, 20), handL=(-120, -70), handR=(120, -70))
            for i in (18, 20, 22):
                if S(i) <= t < S(i + 1): st.update(mouth="flat", handL=REST_L, handR=REST_R, tilt=-6)
            if S(22) <= t < S(23): st.update(lean=-10, eyes="closed")
            if S(23) <= t: st.update(handL=UP_L, handR=UP_R, mouth="o")
        if REVEAL <= t < GRAB[0]:
            st.update(eyes="wide", mouth="flat", brows=(24, 24), sweat=False)
            if S(25) <= t: st.update(handL=(-140, -80), handR=(140, -80), mouth="o", brows=(-6, 20))
            if S(26) <= t: st.update(eyes="wide", brows=(22, 22), handL=UP_L, handR=UP_R, mouth="o")
        if GRAB[0] <= t:
            st.update(look=(-1.0, 0.0), mouth="flat", brows=(-8, -8), handR=(60, 60) if has_bag(t) else REST_R)
            if S(28) <= t: st.update(look=(-1.0, 0.3), brows=(-12, 6), mouth="flat")         # relieved but annoyed, muttering
            if S(29) <= t: st.update(look=(1.0, 0.0), eyes="wide", brows=(24, 24), mouth="o", sweat=True)
            if RUN0 <= t: st.update(look=(-1.0, 0.0), handL=UP_L, lean=-10)
        if walking(t): st["walk"] = t * (16 if t >= RUN0 else 9)
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=HIPS_L, handR=HIPS_R, look=(-1.0, 0.0), brows=(-10, -10), mouth="flat", tilt=-4, rise=1.0)
    st["blink"] = (t % 4.1) < 0.12
    if S(2) <= t < E(2): st.update(handR=(-150, -110 + 14 * math.sin(t * 6)))
    if S(4) <= t < E(4) + 0.2: st.update(handR=(-170, -60), brows=(-20, -20))
    if S(5) <= t: st.update(handL=CROSS_L, handR=CROSS_R, brows=(-12, 12))                   # arms folded
    for i in (8, 10):
        if S(i) <= t < E(i): st.update(brows=(-16, 10), handR=(-150, -50))
    if S(12) <= t < E(12) + 0.3: st.update(handL=(-120, -190), handR=(120, -190), brows=(-26, -26), tilt=-10)
    if STARE[0] <= t < S(14): st.update(brows=(-20, -20), eyes="n", handL=CROSS_L, handR=CROSS_R)
    if S(16) <= t < S(17): st.update(brows=(-18, 4), tilt=-8)
    for i in (18, 20):
        if S(i) <= t < E(i) + 0.2: st.update(brows=(-20, -20))
    if S(22) <= t < E(22) + 0.3: st.update(handL=(-120, -195 + 12 * math.sin(t * 22)), handR=(120, -195 + 12 * math.cos(t * 22)), brows=(-28, -28), tilt=-10)
    if S(24) <= t < E(24): st.update(handR=(-180, -40), brows=(-22, -22))
    if S(26) <= t < E(26): st.update(handR=(-170, -90), brows=(-24, -24), tilt=-8)
    if GRAB[0] <= t: st.update(mouth="smile", brows=(6, -8), tilt=8, handL=HIPS_L, handR=HIPS_R)   # satisfied
    if S(29) <= t: st.update(mouth="o", brows=(-26, -26), handR=(-180, -110), tilt=-10)
    st["amp"] = amp("H", t)
    return st

def snack(cv, gx, st):
    hip = M.SEAT - 18 - 200 * st["rise"]
    hx, hy = gx - 94 + st["handL"][0], hip - 224 + st["handL"][1]
    cv.save(); cv.translate(hx + 10, hy - 30); cv.rotate(-10)
    bag = poly([(-46, -70), (46, -70), (54, 60), (-54, 60)])
    cv.drawPath(bag, P(C("e8424a"))); cv.drawPath(bag, P(INK, stroke=5))
    text(cv, "CHIPS", 0, 6, 26, C("ffd21f"), tf=TF_BLACK)
    cv.restore()
    cv.drawCircle(hx, hy, 16, P(C("ffffff"))); cv.drawCircle(hx, hy, 16, P(INK, stroke=5))
    if st.get("handR", (0, 0))[1] < -90:     # chip near mouth
        mx, my = gx - 30, hip - 330
        cv.drawOval(skia.Rect(mx - 14, my - 9, mx + 14, my + 9), P(C("ffcf5a"))); cv.drawOval(skia.Rect(mx - 14, my - 9, mx + 14, my + 9), P(INK, stroke=3))

def trash(cv, x, y):
    b = skia.Path(); b.moveTo(x - 60, y); b.cubicTo(x - 80, y - 80, x - 50, y - 150, x, y - 150); b.cubicTo(x + 50, y - 150, x + 80, y - 80, x + 60, y); b.close()
    cv.drawPath(b, P(C("2b2b38"))); cv.drawPath(b, P(INK, stroke=5))
    cv.drawLine(x - 14, y - 150, x - 26, y - 185, P(C("2b2b38"), stroke=12)); cv.drawLine(x + 14, y - 150, x + 26, y - 185, P(C("2b2b38"), stroke=12))
    cv.drawLine(x - 30, y - 60, x - 10, y - 110, P(C("4a4a5a"), stroke=5))
    for j in range(3):   # stink lines
        sx = x - 30 + j * 30
        p = skia.Path(); p.moveTo(sx, y - 200); p.cubicTo(sx - 15, y - 230, sx + 15, y - 250, sx, y - 280)
        cv.drawPath(p, P(C("7fb04a", 0.8), stroke=5))

def tv_glow(cv, t):
    if t < S(0) + 0.3:
        cv.drawRect(skia.Rect(-200, -200, W + 200, H + 200), P(C("6fb0ff", 0.05 + 0.03 * math.sin(t * 9))))

def G_CU(t, z=1.85):
    us = guy_state(t); return (z, guy_x(t) + 30, 990 - 190 * us["rise"])
def H_CU(t, z=1.85):
    return (z, HX - 10, 805)
MED = (1.25, 420, 1060)
WIDE = (1.0, 560, 1130)

def camera(t):
    if t < S(0): return MED
    if FREEZE[0] - 0.05 <= t < S(1):
        k = ss(FREEZE[0], S(1), t); return G_CU(t, lerp(1.8, 2.6, k))           # slow zoom into frozen face
    if S(0) <= t < FREEZE[0]: return (1.1, 600, 1080)
    if WALK[0] <= t < S(5): return WIDE
    if SWEAT[0] <= t < S(17):
        k = (t - SWEAT[0]) / (S(17) - SWEAT[0]); return G_CU(t, lerp(1.9, 2.5, k))
    if REVEAL <= t < S(25): return H_CU(t, 2.0)
    if GRAB[0] <= t:
        if t >= FREEZE2[0]:
            k = ss(FREEZE2[0], FREEZE2[0] + 0.12, t); return (lerp(1.5, 1.8, k), guy_x(FREEZE2[0]) + 60, 840)
        return (1.0, 560, 1130) if t < S(29) else (1.1, 420, 1100)
    shots = [(1, G_CU), (2, H_CU), (3, G_CU), (4, lambda t: H_CU(t, 2.1)), (5, G_CU), (6, H_CU), (7, G_CU), (8, H_CU),
             (9, G_CU), (10, H_CU), (11, G_CU), (12, lambda t: H_CU(t, 2.3)), (13, G_CU), (14, lambda t: H_CU(t, 2.0)),
             (15, G_CU), (16, H_CU), (17, lambda t: G_CU(t, 2.0)), (18, lambda t: H_CU(t, 2.0)), (19, lambda t: G_CU(t, 2.0)),
             (20, lambda t: H_CU(t, 2.1)), (21, lambda t: G_CU(t, 2.0)), (22, lambda t: H_CU(t, 2.3)), (23, G_CU),
             (25, lambda t: G_CU(t, 2.1)), (26, lambda t: H_CU(t, 2.1))]
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
    for i, amt in ((0, 12), (4, 12), (12, 18), (22, 16), (25, 12), (29, 14)):
        if S(i) <= t < S(i) + 0.4:
            d = 1 - (t - S(i)) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    return (0, 0)

HL = {0: {"JAMES": "b", "SMITH!": "b"}, 1: {"BABY?": "y"}, 2: {"HERE.": "y"}, 3: {"HAPPENED?": "y"}, 4: {"COME": "b", "HERE!": "b"},
      5: {"SOMETHING?": "y"}, 6: {"YOU": "y", "TELL": "y", "ME.": "y"}, 7: {"BIRTHDAY.": "y"}, 8: {"MY": "b", "BIRTHDAY!": "b"},
      9: {"FOOD!": "y"}, 10: {"ANYTHING!": "b"}, 11: {"FRIEND!": "y"}, 12: {"WHICH": "b", "FRIEND?!": "b"}, 13: {"CONFUSED!": "y"},
      14: {"WHAT": "y", "DID?": "y"}, 15: {"GOOD": "y", "BOYFRIEND!": "y"}, 16: {"VERY": "b", "IMPORTANT.": "b"}, 17: {"BIRTHDAY?": "y"},
      18: {"NO.": "b"}, 19: {"ANNIVERSARY?": "y"}, 20: {"NO!": "b"}, 21: {"VALENTINE'S": "y", "DAY?": "y"}, 22: {"MONTHS": "b", "AGO!": "b"},
      23: {"WHAT?!": "y"}, 24: {"TRASH!": "b"}, 25: {"FULL": "b", "NAME?!": "b"}, 26: {"FATHER'S": "b", "NAME": "y"},
      27: {"GOING!": "y"}, 28: {"CRIME…": "y"}, 29: {"HEARD": "b", "THAT!": "b"}}
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





GUESSES = [(7, 8), (9, 10), (11, 12), (17, 18), (19, 20), (21, 22)]
def wrong_marks(cv, t):
    if not (S(8) <= t < REVEAL):
        return
    n = sum(1 for _, r in GUESSES if t >= S(r))
    for j in range(n):
        r = GUESSES[j][1]
        k = ease_out_back(min(1, (t - S(r)) / 0.2), 2.5)
        x = 540 - (min(n, 6) - 1) * 70 + j * 140
        s = 44 * (1.8 - 0.8 * k)
        for d in (1, -1):
            cv.drawLine(x - s, 1230 - s * d, x + s, 1230 + s * d, P(C("ffffff"), stroke=s * 0.62))
            cv.drawLine(x - s, 1230 - s * d, x + s, 1230 + s * d, P(C("e8262a"), stroke=s * 0.42))

TOP = ["When she uses your FULL name…", "YOU KNOW YOU'RE IN TROUBLE"]

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
    if not has_bag(ta):
        trash(cv, TRASHX, 1600)
    M.draw_person(cv, ta, girl_state(ta), HX, "girl")
    us = guy_state(ta); ux = guy_x(ta)
    if ux > -300:
        M.draw_person(cv, ta, us, ux, "guy")
        if us.get("snack"): snack(cv, ux, us)
        if has_bag(ta):
            hip = M.SEAT - 18 - 200 * us["rise"]
            trash(cv, ux + 94 + us["handR"][0] + 10, hip - 224 + us["handR"][1] + 170)
    tv_glow(cv, ta)
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    if FREEZE[0] <= t < S(1):
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("7a7f8c", 0.3)))
    if t >= FREEZE2[0]:
        fl = max(0, 1 - (t - FREEZE2[0]) / 0.15)
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("ffffff", 0.6 * fl)))
    draw_top(cv, t)
    bubble(cv, t, FREEZE[0] + 0.1, S(1) + 0.3, "FULL NAME = DANGER", 540, 560, col="e8262a", fg="ffffff", size=66)
    tag(cv, t, S(7), S(14), "GUESSING WHAT HE DID…", 470, col="ffd23f", size=54)
    wrong_marks(cv, t)
    bubble(cv, t, REVEAL + 0.6, S(25) + 0.3, "THE CRIME: TRASH", 540, 560, col="ffd23f", fg="141414", size=70)
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
