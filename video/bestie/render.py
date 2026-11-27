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
_src = open(os.path.join(HERE, "..", "mia", "render.py")).read().replace('C("ffcf3f")', 'C("8fd3c8")').replace('C("2a1a14")', 'C("e0a93a")').replace('cv.drawCircle(52, -80, 16, P(C("ff6b8b")))', 'cv.drawCircle(52, -80, 16, P(C("7a5cff")))')
ME = importlib.util.module_from_spec(importlib.util.spec_from_loader("mia_e", loader=None)); ME.__dict__["__file__"] = os.path.join(HERE, "..", "mia", "render.py")
exec(compile(_src, "mia_e", "exec"), ME.__dict__)

GX, HX1, HX2, EX = 330.0, 740.0, 680.0, 930.0
TURN = (E(3), S(4))
DROP = (E(6), S(7))
LOCK = E(14) + 0.1
CARD = (E(15) + 0.3, E(15) + 1.8)
EM_IN = (CARD[1] - 0.1, S(16) - 0.1)
LOOK = (E(30), S(31))
TEAM = (E(32), S(33))
BLACK = E(34) + 0.8
ANGRY = (24, 26, 29)
SECRETS = [23, 25, 28]

def scene3(t): return t >= CARD[0] + 0.7
def her_x(t): return HX2 if scene3(t) else HX1
def em_x(t):
    if not scene3(t): return None
    return lerp(1400, EX, ss(EM_IN[0], EM_IN[1], t))

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
CLASP_L, CLASP_R = (60, 60), (-60, 60)
HIPS_L, HIPS_R = (-18, 168), (18, 168)

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.0), brows=(10, 10), mouth="smile", grass="mouth", tilt=0, rise=0.0)
    st["blink"] = (t % 3.7) < 0.12
    if not scene3(t):
        st.update(phone=True, handL=(90, 40), look=(0.4, 0.7), lean=-6, mouth="smile")
        if S(1) <= t < E(5): st.update(look=(0.6, 0.4) if amp("G", t) < 0.02 else (1.0, 0.0), eyes="happy" if amp("G", t) < 0.02 and t < E(1) else "n")
        if TURN[0] <= t < S(5): st.update(look=(0.4, 0.7), mouth="smile")
        if DROP[0] <= t: st.update(look=(1.0, 0.0), mouth="flat", brows=(18, 18), eyes="wide" if t < E(7) else "n", lean=0)   # smile disappears
        if S(9) <= t: st.update(sweat=True, mouth="smile", brows=(16, 16))
        for i in (9, 11, 13):
            if S(i) <= t < E(i): st.update(handR=(130, -80), look=(0.3, -0.6) if i == 13 else (1.0, 0.0))
        if LOCK <= t: st.update(handL=(90, 90), mouth="smile", eyes="n")
        if S(15) <= t < E(15): st.update(handR=(130, -110), brows=(14, 4))
    else:
        st.update(look=(1.0, 0.0), mouth="smile", brows=(12, 12))
        if S(16) <= t < E(16): st.update(handR=(140, -90), eyes="happy" if amp("G", t) < 0.03 else "n")
        if S(21) <= t: st.update(sweat=True, eyes="wide", mouth="flat", brows=(20, 20))                     # sweating
        if S(22) <= t < E(22): st.update(handL=(-130, -60), handR=(130, -60), mouth="smile", eyes="n")
        if S(24) <= t < S(28): st.update(eyes="wide", brows=(24, 24), mouth="o")
        if S(27) <= t < E(27): st.update(handL=UP_L, handR=UP_R, mouth="o")
        if S(28) <= t: st.update(eyes="wide", brows=(22, 22), mouth="flat")
        if S(30) <= t < E(30): st.update(handR=(140, -80), mouth="o")
        if S(32) <= t: st.update(eyes="wide", brows=(18, 6), mouth="flat", tilt=8, handR=(120, -60) if t < E(32) else REST_R)
        if TEAM[0] <= t: st.update(eyes="wide", brows=(24, 24), sweat=True)
        if S(34) <= t: st.update(eyes="n", brows=(10, 10), mouth="flat", sweat=False, look=(0.0, 0.1), tilt=-4, phone=True, handL=(90, 110))   # puts phone down
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=CLASP_L, handR=CLASP_R, look=(-1.0, 0.0), brows=(8, 8), mouth="smile", tilt=-4, rise=0.0)
    st["blink"] = (t % 4.1) < 0.12
    if not scene3(t):
        if t < S(2): st.update(look=(-0.6, 0.4), brows=(10, 10))
        if TURN[0] <= t < S(4):
            k = ss(TURN[0], TURN[1] - 0.1, t); st.update(look=(lerp(0.3, -1.0, k), 0.0), mouth="flat", brows=(lerp(10, -12, k), lerp(10, 14, k)), tilt=lerp(6, -6, k))   # slow turn
        if S(4) <= t: st.update(mouth="flat", brows=(-12, 14), tilt=-6)
        if S(6) <= t < E(6): st.update(mouth="smile", brows=(-6, 12), tilt=8)                                # "interesting"
        if S(8) <= t: st.update(mouth="smile", brows=(-8, 12))
        if S(12) <= t: st.update(mouth="flat", brows=(-14, 12))
        if S(14) <= t < E(14): st.update(handR=(-150, -60), brows=(-18, 10))
        if LOCK <= t: st.update(brows=(-16, -16), mouth="flat")
    else:
        st.update(look=(1.0, 0.0) if em_x(t) and t < S(18) + 0.5 else (-1.0, 0.0), mouth="smile", brows=(6, 6), tilt=4)
        for i in (17, 19, 21, 23, 25, 28, 31):
            if S(i) <= t < E(i): st["look"] = (1.0, 0.0)
        if S(18) <= t < E(18): st.update(look=(1.0, 0.0), mouth="smile", brows=(-6, 12), tilt=8)
        if S(20) <= t < E(20): st.update(look=(1.0, 0.0), mouth="smirk", brows=(-8, 12))
        if S(24) <= t < E(24) + 0.2: st.update(look=(-1.0, 0.0), eyes="wide", mouth="o", brows=(22, 22), handL=(-120, -190), handR=(120, -190), tilt=0)
        if S(26) <= t < E(26) + 0.2: st.update(look=(-1.0, 0.0), eyes="wide", mouth="o", brows=(-20, 20), handR=(-150, -60))
        if S(29) <= t < E(29) + 0.2: st.update(look=(-1.0, 0.0), handL=(-120, -190), handR=(120, -190), brows=(-24, -24), mouth="o", tilt=-8)
        if LOOK[0] <= t < S(32): st.update(look=(1.0, 0.0), mouth="smirk", brows=(-6, 12), tilt=8)          # exchange a look
        if TEAM[0] <= t: st.update(look=(-1.0, 0.0), mouth="smirk", brows=(-12, 10), tilt=-6)                # both turn to him
    st["amp"] = amp("H", t)
    return st

def em_state(t):
    st = dict(handL=HIPS_L, handR=HIPS_R, look=(-1.0, 0.0), brows=(14, 14), mouth="smile", tilt=6, rise=1.0)
    st["blink"] = (t % 3.9) < 0.12
    if t < EM_IN[1]: st["walk"] = t * 9
    if S(16) <= t < E(16): st.update(handR=(-150, -170 + 20 * math.sin(t * 9)))                              # waves
    if S(17) <= t < E(17) + 0.2: st.update(handL=(-150, -120), handR=(150, -120), eyes="happy", mouth="smile")  # arms open
    if S(19) <= t < E(19): st.update(brows=(16, 6), tilt=8)
    if S(21) <= t < S(30):
        st.update(mouth="smile", eyes="n", brows=(16, 16), tilt=6)
        for i in (21, 23, 25, 28):
            if S(i) <= t < E(i): st.update(handR=(-150, -80 + 20 * math.sin(t * 7)), eyes="happy" if amp("E", t) < 0.03 else "n", look=(-1.0, 0.1))
    if LOOK[0] <= t < S(32): st.update(look=(-1.0, 0.2), mouth="smirk", brows=(-6, 12), tilt=-6)
    if S(31) <= t < E(31): st.update(handR=(-160, -60), mouth="smirk")
    if TEAM[0] <= t: st.update(handL=CLASP_L, handR=CLASP_R, mouth="smirk", brows=(-10, 10), tilt=-6, look=(-1.0, 0.0))
    st["amp"] = amp("E", t)
    return st

def teddy(cv, x, y, s, a):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    br = C("b07a4a", a)
    for dx in (-48, 48): cv.drawCircle(dx, -70, 26, P(br)); cv.drawCircle(dx, -70, 26, P(INK, stroke=5))
    cv.drawCircle(0, -30, 60, P(br)); cv.drawCircle(0, -30, 60, P(INK, stroke=6))
    cv.drawOval(skia.Rect(-60, 10, 60, 120), P(br)); cv.drawOval(skia.Rect(-60, 10, 60, 120), P(INK, stroke=6))
    cv.drawOval(skia.Rect(-24, -24, 24, 6), P(C("e8c9a0", a)))
    cv.drawCircle(-22, -42, 7, P(INK)); cv.drawCircle(22, -42, 7, P(INK)); cv.drawCircle(0, -16, 8, P(INK))
    cv.restore()

def shirts(cv, x, y, a):
    for j, col in enumerate(("3a7bd5", "e8424a")):
        cx = x - 90 + j * 180
        sp = poly([(cx - 70, y - 60), (cx - 25, y - 80), (cx + 25, y - 80), (cx + 70, y - 60), (cx + 55, y - 20), (cx + 40, y - 30), (cx + 40, y + 70), (cx - 40, y + 70), (cx - 40, y - 30), (cx - 55, y - 20)])
        cv.drawPath(sp, P(C(col, a))); cv.drawPath(sp, P(INK, stroke=5))
    text(cv, "?", x, y + 10, 110, C("ffd21f", a), tf=TF_BLACK, stroke=10, stroke_col=C("000000", a))

def G_CU(t, z=1.85): return (z, GX + 30, 990)
def H_CU(t, z=1.85): return (z, her_x(t) - 20, 1040)
def E_CU(t, z=1.85): return (z, EX - 10, 805)
MED = (1.2, 560, 1060)
THREE = (1.05, 620, 1090)

def camera(t):
    if t < S(1): return MED
    if TURN[0] <= t < S(4): k = (t - TURN[0]) / (S(4) - TURN[0]); return H_CU(t, lerp(1.8, 2.2, k))
    if DROP[0] <= t < S(7): return G_CU(t, 2.1)
    if CARD[0] + 0.7 <= t < S(16) + 0.3: return THREE
    if S(17) <= t < S(18): return E_CU(t)
    if LOOK[0] <= t < S(31): return (1.4, 800, 980)
    if TEAM[0] <= t < S(33): return (1.25, 640, 1020)
    if S(34) <= t: k = ss(S(34), BLACK, t); return G_CU(t, lerp(1.8, 2.2, k))
    shots = [(1, G_CU), (2, H_CU), (3, G_CU), (4, lambda t: H_CU(t, 2.1)), (5, G_CU), (6, H_CU), (7, lambda t: G_CU(t, 2.0)), (8, H_CU), (9, G_CU),
             (10, H_CU), (11, G_CU), (12, H_CU), (13, G_CU), (14, lambda t: H_CU(t, 2.0)), (15, G_CU),
             (18, H_CU), (19, E_CU), (20, H_CU), (21, E_CU), (22, lambda t: G_CU(t, 2.0)), (23, E_CU), (24, lambda t: H_CU(t, 2.3)), (25, E_CU),
             (26, lambda t: H_CU(t, 2.2)), (27, lambda t: G_CU(t, 2.1)), (28, E_CU), (29, lambda t: H_CU(t, 2.2)), (30, G_CU), (31, E_CU),
             (32, G_CU), (33, (1.25, 640, 1020))]
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
    for a, amt in ((S(24), 16), (S(26), 12), (S(29), 12)):
        if a <= t < a + 0.4:
            d = 1 - (t - a) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    return (0, 0)

HL = {0: {"TEXTING?": "y"}, 1: {"BEST": "y", "FRIEND.": "y"}, 2: {"BEST": "y", "FRIEND.": "y"}, 3: {"GIRL.": "b"}, 4: {"GIRL?": "b"}, 5: {"YEARS.": "y"},
      6: {"INTERESTING.": "y", "MEET": "b"}, 7: {"MEET": "b", "WHY?": "y"}, 8: {"KNOW": "y"}, 9: {"BUSY.": "y"}, 10: {"DINNER.": "y"},
      11: {"TRAVELLING.": "y"}, 12: {"WHERE?": "y"}, 13: {"FAR.": "b"}, 14: {"TEXTING": "b"}, 15: {"TECHNOLOGY": "y", "ANYWHERE.": "y"},
      16: {"EMILY.": "y", "FEMALE": "b"}, 17: {"GIRLFRIEND!": "y"}, 18: {"FAMOUS": "y"}, 19: {"FAMOUS?": "y"}, 20: {"CLOSE.": "y"},
      21: {"EXTREMELY": "y", "SECRETS.": "b"}, 22: {"EVERYTHING.": "y"}, 23: {"CRIED": "b", "CARTOON": "y"}, 24: {"WHAT?!": "b"},
      25: {"TEDDY": "b", "BEAR!": "b"}, 26: {"DANIEL?!": "b"}, 27: {"CHILD!": "y"}, 28: {"SHIRT": "b"}, 29: {"ANOTHER": "y", "WOMAN": "y", "DRESS?!": "b"},
      30: {"BEST": "y", "FRIEND!": "y"}, 31: {"TALK.": "b"}, 32: {"TEAMING": "b", "UP?": "b"}, 33: {"BOTH": "y", "BEST": "y", "FRIENDS": "y"},
      34: {"NEW": "b", "FRIENDS.": "b"}}
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
            if who in ("G", "H", "E"):
                chip(cv, 540, CAP_Y - 128, {"H": "SOPHIA", "G": "DANIEL", "E": "EMILY"}[who], a=0.95, col={"H": "ffd23f", "G": "ffffff", "E": "8fd3c8"}[who], fg="1a1a1a", size=30)
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





TOP = ["When he says he has a female best friend…", "SHE KNOWS ALL HIS SECRETS"]

def draw_top(cv, t):
    f = skia.Font(TF_B, 44)
    w = max(f.measureText(TOP[0]), skia.Font(TF_BLACK, 48).measureText(TOP[1])) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 286), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    text(cv, TOP[0], 540, 208, 44, C("111111"), tf=TF_B)
    text(cv, TOP[1], 540, 264, 48, C("e74c3c"), tf=TF_BLACK)

def card(cv, t, rng, l1):
    if not (rng[0] <= t < rng[1]): return
    a = min(1, (t - rng[0]) / 0.2, (rng[1] - t) / 0.2)
    cv.drawRect(skia.Rect(0, 0, W, H), P(C("101018", a)))
    text(cv, l1, 540, 960, 96, C("ffffff", a), tf=TF_BLACK)

def render_frame(cv, t):
    z, wx, wy = camera(t)
    sx, sy = shake(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2 + sx, H / 2 + sy); cv.scale(z, z); cv.translate(-wx, -wy)
    CO.draw_room(cv, t); CO.draw_couch_back(cv); CO.draw_couch_front(cv)
    M.draw_person(cv, t, girl_state(t), her_x(t), "girl")
    M.draw_person(cv, t, guy_state(t), GX, "guy")
    ex = em_x(t)
    if ex is not None and ex < 1350: ME.draw_person(cv, t, em_state(t), ex, "girl")
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    draw_top(cv, t)
    n = sum(1 for i in SECRETS if t >= S(i))
    if n and t < S(31):
        last = max(S(i) for i in SECRETS if t >= S(i)); k = ease_out_back(min(1, (t - last) / 0.25), 2.2)
        cv.save(); cv.translate(540, 470); cv.scale(k, k); chip(cv, 0, 0, f"SECRETS EXPOSED: {n}", a=1, col="e8262a", fg="ffffff", size=54); cv.restore()
    if S(25) + 0.6 <= t < E(25) + 0.6:
        a = min(1, (t - S(25) - 0.6) / 0.2, (E(25) + 0.6 - t) / 0.2); teddy(cv, 260, 700, ease_out_back(min(1, (t - S(25) - 0.6) / 0.3), 2.0) * 1.7, a)
    if S(28) + 1.4 <= t < E(28) + 0.5:
        a = min(1, (t - S(28) - 1.4) / 0.2, (E(28) + 0.5 - t) / 0.2); cv.save(); cv.translate(270, 700); cv.scale(1.4, 1.4); shirts(cv, 0, 0, a); cv.restore()
    tag(cv, t, S(31), S(33) + 0.5, "BESTIE ALLIANCE", 470, col="7a5cff", fg="ffffff", size=60)
    card(cv, t, CARD, "THE NEXT WEEKEND")
    if not (CARD[0] <= t < CARD[1]): draw_caption(cv, t)
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
