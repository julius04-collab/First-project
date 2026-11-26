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
SPARK = S(3) + 0.1
SCRATCH1 = E(7) + 0.02
FOLD = E(13) + 0.05
FLAGS = E(21) + 0.1
BOOM = S(22)
SCRATCH2 = E(29) + 0.02
GRAB = E(29) + 0.1
RUN0 = E(30) + 0.05
FREEZE2 = (S(31) + 0.9, TOTAL)
BLACK = TOTAL - 0.3
ANGRY = (22, 30, 31)

def at(t):
    return FREEZE2[0] if t >= FREEZE2[0] else t

def girl_x(t):
    if t < RUN0 + 0.2:
        x = lerp(600, HX, ss(E(7) + 0.2, E(7) + 0.9, t))          # cuddled up, then scoots away
        return x
    return max(GX + 120, HX - 380 * (t - RUN0 - 0.2))

def guy_x(t):
    return GX if t < RUN0 else GX - 260 * min(t - RUN0, 0.8)

def guy_rise(t):
    return ss(GRAB + 0.3, RUN0, t)

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
CLASP_L, CLASP_R = (60, 60), (-60, 60)

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.0), brows=(10, 10), mouth="smile", grass="mouth", tilt=4, rise=guy_rise(t))
    st["blink"] = (t % 3.7) < 0.12
    if t < S(7):
        st.update(handR=(170, -70), tilt=8, mouth="smile")                                                   # arm around her, affectionate
        if S(3) <= t < E(5): st.update(eyes="happy" if amp("G", t) < 0.05 else "n", brows=(14, 14))      # confident
    if S(7) <= t < S(8): st.update(mouth="smirk", brows=(14, 4), tilt=8, handR=(120, -110))               # slightly smug
    if S(8) <= t < S(14):
        st.update(brows=(16, 16), mouth="smile", sweat=t > S(10))                                         # nervous
        for i in (9, 11, 13):
            if S(i) <= t < E(i): st.update(handL=(-130, -60), handR=(130, -60))
        if S(13) <= t < E(13): st.update(mouth="smirk", brows=(12, 4), handR=(120, -110), handL=REST_L)
    if S(14) <= t < FLAGS:
        st.update(mouth="smile", brows=(12, 12))
        if S(15) <= t < E(15): st.update(handR=(130, -80), mouth="flat", brows=(4, 4))
        if S(17) <= t < E(17): st.update(eyes="happy" if amp("G", t) < 0.05 else "n", handR=(120, -110))
        if S(19) <= t: st.update(mouth="smile", look=(0.3, -0.5), tilt=6)
        if S(21) <= t: st.update(look=(1.0, 0.0))
    if FLAGS <= t < S(23): st.update(eyes="wide", mouth="flat", brows=(24, 24), sweat=True, look=(0.0, 0.0))   # realises
    if S(23) <= t < GRAB:
        st.update(sweat=True, brows=(18, 18), mouth="smile", handL=(-130, -80), handR=(130, -80))
        if S(25) <= t < E(25): st.update(handL=(-150, -120), handR=(150, -120))
        if S(27) <= t < E(27): st.update(handL=REST_L, handR=(120, -90), mouth="smile", eyes="n")
        if S(29) <= t: st.update(handL=REST_L, handR=(120, -110), mouth="smirk", brows=(10, 4), sweat=False)
    if GRAB <= t:
        st.update(eyes="wide", mouth="o", brows=(24, 24), sweat=True, handL=UP_L, handR=UP_R, look=(1.0, 0.0), tilt=-8)
        if RUN0 <= t < RUN0 + 0.8: st.update(walk=t * 16, lean=-10, look=(-1.0, 0.0))
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=CLASP_L, handR=CLASP_R, look=(-1.0, 0.0), brows=(12, 12), mouth="smile", tilt=-16, rise=0.0)
    st["blink"] = (t % 4.1) < 0.12
    if t < S(7):                                                                           # head on his shoulder
        st.update(tilt=-18, eyes="happy" if amp("H", t) < 0.03 else "n", brows=(14, 14))
        if S(4) <= t < E(4): st.update(eyes="n", brows=(16, 16), mouth="smile")
    if S(7) <= t < S(8):
        k = ss(S(7) + 0.5, E(7) + 0.6, t)                                                  # smile slowly disappears
        st.update(mouth="smile" if k < 0.5 else "flat", eyes="n", brows=(lerp(14, -12, k), lerp(14, 12, k)), tilt=lerp(-18, -4, k))
    if S(8) <= t < FOLD: st.update(brows=(-12, 14), mouth="flat", tilt=-6, eyes="n")      # suspicious
    if S(12) <= t < E(12): st.update(handR=(-160, -70 + 12 * math.sin(t * 9)), brows=(-18, -18))
    if FOLD <= t < FLAGS:
        st.update(brows=(-16, 8), mouth="flat", tilt=-6, eyes="n")                         # arms folded
        if S(16) <= t < E(16): st.update(brows=(-20, 10), tilt=-10)
        if S(17) <= t < S(18): st.update(brows=(-6, 10), mouth="smirk")
        if S(18) <= t: st.update(brows=(-4, 10), mouth="flat")
        if S(20) <= t: st.update(mouth="smile", eyes="happy", brows=(14, 14), tilt=8)
        if S(21) <= t + 0.0 and t > E(21) - 0.6: st.update(eyes="n", mouth="flat", brows=(10, 10))
    if FLAGS <= t < S(23):
        st.update(eyes="wide", mouth="o", brows=(20, 20), tilt=0)                           # shocked
        if S(22) <= t: st.update(handL=(-120, -195 + 12 * math.sin(t * 22)), handR=(120, -195 + 12 * math.cos(t * 22)), brows=(-28, -28), tilt=-10)
    if S(23) <= t < GRAB:
        st.update(brows=(-18, -18), mouth="flat", eyes="n", tilt=-6)
        if S(24) <= t < E(24): st.update(handR=(-160, -60), brows=(-20, 12))
        if S(26) <= t < E(26): st.update(brows=(-14, 16))
        if S(28) <= t < E(28): st.update(brows=(-10, 16), tilt=-10)
        if S(29) <= t: st.update(brows=(-24, -24))
    if GRAB <= t:
        st.update(rise=ss(GRAB, RUN0, t), handR=(30, -230), handL=(-120, -60), brows=(-26, -26), mouth="smile", pillow=True, tilt=-8, eyes="n")
        if RUN0 + 0.2 <= t: st.update(walk=t * 14)
    st["amp"] = amp("H", t)
    return st

def G_CU(t, z=1.85):
    return (z, guy_x(t) + 30, 990 - 190 * guy_rise(t))
def H_CU(t, z=1.85):
    return (z, girl_x(t) - 20, 1040)
MED = (1.2, 560, 1060)
TWO = (1.35, 540, 1060)

def camera(t):
    if t < S(2): return (1.25, 520, 1050)
    if E(7) <= t < S(8): return H_CU(t, 2.0)
    if S(14) <= t < FLAGS and S(16) <= t < S(17): return H_CU(t, 2.0)
    if FLAGS <= t < S(22):
        k = (t - FLAGS) / (S(22) - FLAGS); return G_CU(t, lerp(1.7, 2.1, k)) if k < 0.5 else H_CU(t, lerp(1.9, 2.4, k))
    if S(22) <= t < S(23): return H_CU(t, 2.4)
    if E(29) <= t < S(30): return G_CU(t, 1.9)
    if t >= FREEZE2[0]:
        k = ss(FREEZE2[0], FREEZE2[0] + 0.12, t); return (lerp(1.9, 2.4, k), guy_x(FREEZE2[0]) + 30, 990 - 190 * guy_rise(FREEZE2[0]))
    if GRAB <= t:
        k = ss(S(31), S(31) + 0.25, t); return (lerp(1.0, 1.4, k), lerp(540, 330, k), lerp(1130, 1000, k))
    shots = [(2, H_CU), (3, G_CU), (4, H_CU), (5, G_CU), (6, H_CU), (7, lambda t: G_CU(t, 2.0)), (8, H_CU), (9, lambda t: G_CU(t, 1.9)), (10, H_CU),
             (11, G_CU), (12, lambda t: H_CU(t, 2.0)), (13, G_CU), (14, H_CU), (15, G_CU), (17, G_CU), (18, lambda t: H_CU(t, 1.8)), (19, G_CU), (20, H_CU),
             (21, G_CU), (23, G_CU), (24, H_CU), (25, G_CU), (26, H_CU), (27, G_CU), (28, H_CU), (29, lambda t: G_CU(t, 2.0)), (30, G_CU)]
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
    for a, amt in ((SCRATCH1, 8), (BOOM, 18), (SCRATCH2, 8)):
        if a <= t < a + 0.4:
            d = 1 - (t - a) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    return (0, 0)

HL = {0: {"ASK": "y"}, 2: {"BACK": "y", "TIME": "y", "CHOOSE": "b"}, 3: {"COURSE!": "b"}, 4: {"REALLY?": "y"}, 5: {"WITHOUT": "y", "HESITATION.": "y"},
      6: {"SWEET.": "y", "WHY?": "y"}, 7: {"GETTING": "b", "MYSELF": "b", "INTO.": "b"}, 8: {"MEAN?": "y"}, 9: {"PERSONALITY.": "y"},
      10: {"WOULDN'T": "b"}, 11: {"STILL": "y"}, 12: {"GETTING": "y", "INTO!": "b"}, 13: {"FULL": "b", "INFORMATION.": "b"}, 14: {"RISK?": "b"},
      15: {"RISK,": "y"}, 16: {"RISK?": "b"}, 17: {"BEAUTIFUL": "y", "RISK.": "b"}, 18: {"DIFFERENTLY": "y"}, 19: {"EARLIER.": "y"},
      20: {"AWW!": "y"}, 21: {"RED": "b", "FLAGS.": "b"}, 22: {"RED": "b", "FLAGS?!": "b"}, 23: {"JOKING!": "y"}, 24: {"ADMIT": "y", "FLAGS?": "b"},
      25: {"EVERYBODY": "y", "FLAGS!": "b"}, 26: {"ONE": "y"}, 27: {"TALK": "y", "MUCH": "y"}, 28: {"BIGGEST": "y", "PROBLEM?": "y"},
      29: {"HONESTLY.": "b"}, 30: {"HONESTY!": "b"}, 31: {"YES": "y", "QUIET!": "b"}}


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


def red_flags(cv, t, gx):
    if not (FLAGS <= t < S(23) + 0.5): return
    for j, (dx, dy, d) in enumerate(((-170, -520, 0.0), (150, -560, 0.15), (-60, -640, 0.3), (230, -440, 0.45), (-230, -400, 0.6))):
        t0 = FLAGS + d
        if t < t0: continue
        k = ease_out_back(min(1, (t - t0) / 0.25), 2.2)
        x, y = gx + dx, M.SEAT + dy + 6 * math.sin(t * 6 + j)
        cv.save(); cv.translate(x, y); cv.scale(k, k)
        cv.drawLine(0, 0, 0, 110, P(INK, stroke=8))
        fl = skia.Path(); fl.moveTo(0, 0); fl.quadTo(40, -12 + 8 * math.sin(t * 9 + j), 80, 4); fl.lineTo(80, 50); fl.quadTo(40, 38 + 8 * math.sin(t * 9 + j), 0, 52); fl.close()
        cv.drawPath(fl, P(C("e8262a"))); cv.drawPath(fl, P(INK, stroke=5))
        cv.restore()

TOP = ["When she asks if you'd date her again…", "DON'T BE THIS HONEST"]

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
    red_flags(cv, ta, ux)
    if gs.get("pillow"):
        hip = M.SEAT - 18 - 200 * gs.get("rise", 0)
        pillow_shape(cv, gx + 84 + gs["handR"][0], hip - 224 + gs["handR"][1] - 40, 15 * math.sin(ta * 12))
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    if t >= FREEZE2[0]:
        fl = max(0, 1 - (t - FREEZE2[0]) / 0.15)
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("ffffff", 0.6 * fl)))
    draw_top(cv, t)
    tag(cv, t, FOLD - 0.4, S(14) + 0.3, "\"FULL INFORMATION\"", 470, col="3a7bd5", fg="ffffff", size=56)
    tag(cv, t, S(17) + 0.4, S(18) + 0.2, "RISK LEVEL: BEAUTIFUL", 470, col="ff7aa8", fg="141414", size=54)
    tag(cv, t, S(29) + 0.8, GRAB + 0.4, "TOO HONEST", 470, col="e8262a", fg="ffffff", size=60)
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
