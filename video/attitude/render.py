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
SIT = (0.1, 1.5)
PICKUP = (E(7) + 0.2, E(7) + 0.9)
STING = E(19) + 0.05
PUTDOWN = (E(28) + 0.05, S(29))
SCRATCH = E(35) + 0.02
SIL = (E(35), S(36))
PAUSE = (E(39), S(40))
GRAB = E(41) + 0.05
RUN0 = GRAB + 0.35
FREEZE2 = (S(42) + 0.9, TOTAL)
BLACK = TOTAL - 0.3
ANGRY = (26, 40, 42)
ONEWORD = [9, 11, 13, 17, 19, 21, 23, 25, 27, 31]

def at(t):
    return FREEZE2[0] if t >= FREEZE2[0] else t

def girl_x(t):
    if t < SIT[1]: return lerp(1300, HX, ss(SIT[0], SIT[1] - 0.3, t))
    if t < RUN0 + 0.2: return HX
    return max(GX + 120, HX - 380 * (t - RUN0 - 0.2))

def guy_x(t):
    return GX if t < RUN0 else GX - 260 * min(t - RUN0, 0.8)

def guy_rise(t):
    return ss(GRAB, RUN0, t)

def her_phone(t):
    return PICKUP[1] <= t < PUTDOWN[0] + 0.3

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
CLASP_L, CLASP_R = (60, 60), (-60, 60)

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.0), brows=(8, 8), mouth="smirk", grass="mouth", tilt=0, rise=guy_rise(t))
    st["blink"] = (t % 3.7) < 0.12
    if t < S(8):                                                   # scrolling, ignoring her
        st.update(phone=True, handL=(90, 40), look=(0.4, 0.7), mouth="flat", lean=-6, brows=(2, 2))
    if S(8) <= t < S(20):
        st.update(look=(1.0, 0.0), mouth="smile", brows=(12, 12))
        if S(12) <= t: st.update(brows=(16, 6), mouth="flat", tilt=6)                     # confused
        if S(16) <= t: st.update(brows=(14, 14), tilt=8)
        if S(18) <= t: st.update(brows=(-6, 14), mouth="flat", tilt=-6)                   # suspicious
    if S(20) <= t < S(32):
        k = ss(S(20), S(31), t)
        st.update(mouth="flat", brows=(lerp(-4, -16, k), lerp(-4, -16, k)), handR=(140, -60 + 20 * math.sin(t * 7)))   # frustrated, building
        if S(26) <= t < E(26) + 0.2: st.update(handL=(-130, -170), handR=(130, -170), mouth="o", brows=(-20, -20))
        if S(30) <= t < E(30): st.update(handL=(-140, -80), handR=(140, -80), mouth="o")
    if S(32) <= t < S(36):
        st.update(mouth="o", brows=(-16, -16), handR=(140, -80))
        if S(33) <= t: st.update(eyes="n", brows=(10, 10), mouth="flat", handR=REST_R)
        if S(35) <= t: st.update(eyes="wide", brows=(20, 20), mouth="flat")
    if S(36) <= t < S(39):
        st.update(look=(0.0, 0.5), brows=(14, 14), mouth="flat", tilt=-6)                 # embarrassed, thinking
        if S(37) <= t: st.update(look=(1.0, 0.0), tilt=0)
        if S(38) <= t: st.update(brows=(12, 12), mouth="smile", handR=(-60, -40))
    if S(39) <= t < GRAB:
        st.update(mouth="smirk", brows=(14, 4), tilt=8, look=(1.0, 0.0), handR=(110, -120) if t < E(39) else REST_R)   # smug
        if S(40) <= t: st.update(eyes="wide", mouth="o", brows=(20, 20))
        if S(41) <= t: st.update(eyes="n", mouth="smile", brows=(16, 16), handR=(-60, -40))
    if GRAB <= t:
        st.update(eyes="wide", mouth="o", brows=(24, 24), sweat=True, handL=UP_L, handR=UP_R, look=(1.0, 0.0), tilt=-8)
        if RUN0 <= t < RUN0 + 0.8: st.update(walk=t * 16, lean=-10)
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=CLASP_L, handR=CLASP_R, look=(-1.0, 0.0), brows=(12, 12), mouth="smile", tilt=6, rise=0.0)
    st["blink"] = (t % 4.1) < 0.12
    if t < SIT[1]: st.update(rise=1 - ss(SIT[1] - 0.4, SIT[1], t), walk=t * 9 if t < SIT[1] - 0.4 else None)
    if S(2) <= t < E(2): st.update(handR=(-120, -40), brows=(14, 14))
    if S(4) <= t < S(8): st.update(mouth="flat", brows=(6, 6), tilt=0)
    if S(6) <= t < S(8): st.update(brows=(14, 14), mouth="flat", look=(0.2, 0.5))         # disappointed
    if E(7) <= t: st.update(eyes="n", mouth="flat", brows=(4, 4), tilt=0)
    if her_phone(t): st.update(phone=True, handR=(-110, 40), look=(-0.4, 0.7), brows=(2, 2), mouth="flat")   # calmly imitates
    for i in ONEWORD:
        if S(i) <= t < E(i): st.update(mouth="flat")
    if S(21) <= t < E(21): st.update(brows=(14, 2), tilt=6)                                 # pretends not to understand
    if PUTDOWN[0] <= t < S(32): st.update(phone=False, handR=CLASP_R, look=(-1.0, 0.0), brows=(6, 6), mouth="flat", tilt=0)
    if S(33) <= t < S(39):
        st.update(phone=False, handR=CLASP_R, look=(-1.0, 0.0), mouth="smile", eyes="happy" if amp("H", t) < 0.05 and t < S(35) else "n", brows=(10, 10), tilt=8)   # sweet smile
        if S(35) <= t: st.update(eyes="n", brows=(-4, 10), mouth="smile")
        if S(38) <= t: st.update(eyes="happy", brows=(14, 14))
    if S(39) <= t < GRAB:
        st.update(eyes="n", mouth="flat", brows=(4, 4), tilt=0)
        if PAUSE[0] + 0.3 <= t: st.update(brows=(-16, -16))
        if S(40) <= t: st.update(handL=(-120, -195 + 12 * math.sin(t * 22)), handR=(120, -195 + 12 * math.cos(t * 22)), brows=(-28, -28), mouth="o", tilt=-10)
        if E(40) + 0.3 <= t: st.update(handL=CLASP_L, handR=CLASP_R, mouth="flat")
    if GRAB <= t:
        st.update(rise=ss(GRAB, RUN0, t), handR=(30, -230), handL=(-120, -60), brows=(-28, -28), mouth="o", pillow=True, tilt=-8, eyes="n", phone=False)
        if RUN0 + 0.2 <= t: st.update(walk=t * 14)
    st["amp"] = amp("H", t)
    return st

def feed(cv, t):
    a0, a1 = 3.0, 5.6
    if not (a0 <= t < a1): return
    k = ease_out_back(min(1, (t - a0) / 0.3), 1.6); a = min(1, (a1 - t) / 0.2)
    cv.save(); cv.translate(820, 640); cv.rotate(6); cv.scale(0.75 * k, 0.75 * k)
    body = skia.RRect.MakeRectXY(skia.Rect(-200, -340, 200, 340), 40, 40)
    cv.drawRRect(body, P(C("000000", 0.35 * a), blur=20)); cv.drawRRect(body, P(C("1d1d26", a)))
    cv.save(); cv.clipRect(skia.Rect(-176, -312, 176, 312))
    cv.drawRect(skia.Rect(-176, -312, 176, 312), P(C("f4f6fa", a)))
    off = ((t - a0) * 260) % 220
    for j in range(5):
        y = -312 + j * 220 - off
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-156, y + 10, 156, y + 200), 16, 16), P(C(["ffd6e6", "c9e4ff", "d6f5d6", "fff0b8", "e6d6ff"][j % 5], a)))
        cv.drawCircle(-120, y + 40, 16, P(C("9aa0ad", a)))
    cv.restore()
    cv.restore()

def G_CU(t, z=1.85):
    return (z, guy_x(t) + 30, 990 - 190 * guy_rise(t))
def H_CU(t, z=1.85):
    return (z, girl_x(t) - 20, 1040)
MED = (1.2, 560, 1060)
TWO = (1.35, 540, 1060)

def camera(t):
    if t < S(1): return MED
    if S(20) <= t < S(32):
        k = (t - S(20)) / (S(32) - S(20)); z0 = lerp(1.7, 2.3, k)
        return G_CU(t, z0) if amp("G", t) > 0 or (t > S(20) and any(S(i) <= t < S(i + 1) for i in (20, 22, 24, 26, 28, 30))) else H_CU(t, z0)
    if SIL[0] <= t < S(36):
        k = (t - SIL[0]) / (S(36) - SIL[0]); return TWO if k < 0.0 else (lerp(1.35, 1.6, k), 540, 1040)
    if PAUSE[0] <= t < S(40):
        k = (t - PAUSE[0]) / (S(40) - PAUSE[0]); return H_CU(t, lerp(1.8, 2.3, k))
    if S(33) <= t < S(36): return (1.5, 540, 1030) if t < S(34) or t >= S(35) else G_CU(t)
    if t >= FREEZE2[0]:
        k = ss(FREEZE2[0], FREEZE2[0] + 0.12, t); return (lerp(1.9, 2.4, k), guy_x(FREEZE2[0]) + 30, 990 - 190 * guy_rise(FREEZE2[0]))
    if GRAB <= t:
        k = ss(S(42), S(42) + 0.25, t); return (lerp(1.0, 1.4, k), lerp(540, 330, k), lerp(1130, 1000, k))
    if PICKUP[0] <= t < S(8): return H_CU(t, 1.7)
    shots = [(1, G_CU), (2, H_CU), (3, G_CU), (4, H_CU), (5, G_CU), (6, H_CU), (7, G_CU), (8, G_CU), (9, H_CU), (10, G_CU),
             (11, H_CU), (12, G_CU), (13, H_CU), (14, G_CU), (15, H_CU), (16, lambda t: G_CU(t, 2.1)), (17, H_CU), (18, G_CU),
             (19, lambda t: H_CU(t, 2.0)), (32, G_CU), (36, lambda t: G_CU(t, 2.0)), (37, H_CU), (38, G_CU), (39, lambda t: G_CU(t, 2.1)),
             (40, lambda t: H_CU(t, 2.4)), (41, G_CU)]
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
    for a, amt in ((S(26), 12), (S(40), 18), (SCRATCH, 8)):
        if a <= t < a + 0.4:
            d = 1 - (t - a) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    return (0, 0)

HL = {0: {"DAY?": "y"}, 1: {"FINE.": "b"}, 2: {"INTERESTING": "y"}, 3: {"NOTHING.": "b"}, 4: {"SOMETHING.": "y"}, 5: {"HMM.": "b"},
      6: {"NEVER": "y", "MIND.": "y"}, 7: {"OKAY.": "b"}, 8: {"CHARGER?": "y"}, 9: {"NO.": "b"}, 10: {"HELP": "y"}, 11: {"BUSY.": "b"},
      12: {"WHAT?": "y"}, 13: {"NOTHING.": "b"}, 14: {"HELP?": "y"}, 15: {"NOTHING.": "b"}, 16: {"UPSET?": "y"}, 17: {"NO.": "b"},
      18: {"SURE?": "y"}, 19: {"FINE.": "b"}, 20: {"BEHAVING": "y"}, 21: {"WHAT?": "b"}, 22: {"LISTENING": "y"}, 23: {"HMM.": "b"},
      24: {"ONE-WORD": "b", "ANSWERS!": "b"}, 25: {"OKAY.": "b"}, 26: {"BABE!": "b"}, 27: {"WHAT?": "b"}, 28: {"PHONE": "y", "DOWN": "y"},
      29: {"CONTINUE.": "y"}, 30: {"FIVE": "y", "MINUTES!": "y"}, 31: {"AND?": "b"}, 32: {"ANNOYING!": "b"}, 33: {"LIKED": "y", "ATTITUDE.": "b"},
      34: {"MEAN?": "y"}, 35: {"WAY": "y", "TREAT": "b"}, 36: {"BEHAVING?": "y"}, 37: {"EXACTLY.": "b"}, 38: {"CHANGE.": "y"},
      39: {"TOMORROW.": "b"}, 40: {"TOMORROW?!": "b"}, 41: {"MYSELF!": "y"}, 42: {"WORKING": "y"}}
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


def oneword_counter(cv, t):
    if not (S(9) <= t < S(32)): return
    n = sum(1 for i in ONEWORD if t >= S(i))
    last = max(S(i) for i in ONEWORD if t >= S(i))
    k = ease_out_back(min(1, (t - last) / 0.25), 2.2)
    cv.save(); cv.translate(540, 470); cv.scale(k, k)
    chip(cv, 0, 0, f"ONE-WORD ANSWERS: {n}", a=1, col="ffd23f", fg="141414", size=52)
    cv.restore()

TOP = ["When your girlfriend copies your attitude…", "HE DID NOT LIKE IT"]

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
    M.draw_person(cv, ta, us, ux, "guy")
    if gs.get("pillow"):
        hip = M.SEAT - 18 - 200 * gs.get("rise", 0)
        pillow_shape(cv, gx + 84 + gs["handR"][0], hip - 224 + gs["handR"][1] - 40, 15 * math.sin(ta * 12))
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    if t >= FREEZE2[0]:
        fl = max(0, 1 - (t - FREEZE2[0]) / 0.15)
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("ffffff", 0.6 * fl)))
    draw_top(cv, t)
    feed(cv, t)
    tag(cv, t, PICKUP[0], S(9) - 0.1, "MIRROR MODE: ON", 470, col="ff7aa8", fg="141414", size=58)
    oneword_counter(cv, t)
    tag(cv, t, SCRATCH, S(36) + 0.6, "ROLE REVERSAL", 470, col="e8262a", fg="ffffff", size=62)
    tag(cv, t, PAUSE[0] + 0.1, S(40), "…STARTING TOMORROW", 470, col="ffffff", size=56)
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
