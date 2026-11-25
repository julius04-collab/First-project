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
SCRATCH = S(4) - 0.05
WIN = S(13) + 0.75 * (E(13) - S(13))
BOOM = E(21) - 0.6
STING = E(27) + 0.05
HOLD = (E(31), S(32))
GRAB = E(33) + 0.05
RUN0 = GRAB + 0.35
FREEZE2 = (S(34) + 0.9, TOTAL)
BLACK = TOTAL - 0.3
ANGRY = (4, 14, 20, 22, 30, 34)

def at(t):
    return FREEZE2[0] if t >= FREEZE2[0] else t

def girl_x(t):
    if t < RUN0 + 0.2: return HX
    return max(GX + 120, HX - 380 * (t - RUN0 - 0.2))

def guy_x(t):
    return GX if t < RUN0 else GX - 260 * min(t - RUN0, 0.8)

def guy_rise(t):
    return ss(GRAB, RUN0, t)

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
CLASP_L, CLASP_R = (60, 60), (-60, 60)

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.0), brows=(8, 8), mouth="smirk", grass="mouth", tilt=0, rise=guy_rise(t))
    st["blink"] = (t % 3.7) < 0.12
    if t < E(24) + 0.3:
        st.update(phone=True, handL=(90, 40), look=(0.4, 0.7), mouth="flat", lean=-6, brows=(4, 4))
        if S(5) <= t < E(5): st.update(look=(1.0, 0.0), brows=(12, 12))
        if S(9) <= t < E(9): st.update(look=(1.0, 0.0), brows=(14, 4))
        if S(13) <= t < S(16):
            st.update(look=(1.0, 0.0), mouth="smile", brows=(12, 12), handR=(120, -120), eyes="happy" if amp("G", t) < 0.05 else "n")
        for i in (17, 19):
            if S(i) <= t < E(i): st.update(look=(1.0, 0.0), mouth="flat", brows=(2, 2))
        if S(21) <= t < S(22): st.update(look=(1.0, 0.0), mouth="flat", brows=(0, 0), handR=(120, -60))
        if S(23) <= t < E(23): st.update(look=(1.0, 0.0), mouth="flat", brows=(6, 6))
    if S(22) <= t < S(23): st.update(eyes="wide", brows=(18, 18), mouth="flat")
    if E(24) + 0.3 <= t < GRAB:
        st.update(phone=False, handL=REST_L, look=(1.0, 0.0), brows=(-8, 12), mouth="flat", lean=0)
        if S(27) <= t < S(28): st.update(brows=(-14, 10), tilt=6)
        if S(31) <= t < E(31): st.update(brows=(-16, -16), handR=(140, -70 + 14 * math.sin(t * 8)), mouth="flat")
        if S(32) <= t: st.update(brows=(14, 4), mouth="smirk")
        if S(33) <= t: st.update(handR=(120, -110), mouth="smile", eyes="happy" if amp("G", t) < 0.05 else "n")
    if GRAB <= t:
        st.update(eyes="wide", mouth="o", brows=(24, 24), sweat=True, handL=UP_L, handR=UP_R, look=(1.0, 0.0), tilt=-8, phone=False)
        if RUN0 <= t < RUN0 + 0.8: st.update(walk=t * 16, lean=-10)
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=CLASP_L, handR=CLASP_R, look=(-1.0, 0.0), brows=(10, 10), mouth="smile", tilt=6, rise=0.0)
    st["blink"] = (t % 4.1) < 0.12
    if t < 0.9: st.update(phone=True, handR=(-110, 40), look=(-0.4, 0.7))
    if S(0) <= t < S(3): st.update(mouth="smirk", brows=(6, 14), eyes="n")
    if S(3) <= t < S(4): st.update(eyes="wide", mouth="flat", brows=(10, 10), tilt=0)
    if S(4) <= t < E(4) + 0.2: st.update(handL=(-120, -190), handR=(120, -190), brows=(-24, -24), mouth="o", tilt=-10)
    if E(4) + 0.2 <= t < S(13): st.update(brows=(-12, 12), mouth="flat", tilt=-4)
    if E(7) <= t < S(8): st.update(brows=(14, 14), look=(0.0, 0.4))
    if S(10) <= t < E(10): st.update(handR=(-160, -70 + 14 * math.sin(t * 9)), brows=(-18, -18))
    if S(13) <= t < S(16): st.update(brows=(-12, 14), mouth="flat")
    if S(14) <= t < E(14) + 0.2: st.update(handL=(-120, -190), handR=(120, -190), brows=(-24, -24), mouth="o")
    if E(15) <= t < S(24): st.update(brows=(-16, 8), mouth="flat", tilt=-6)
    if S(20) <= t < E(20) + 0.2: st.update(handR=(-150, -60), brows=(-18, -18))
    if BOOM <= t < S(23): st.update(eyes="wide", mouth="o", brows=(20, 20), tilt=0)
    if S(22) <= t < E(22) + 0.2: st.update(handL=(-120, -195 + 12 * math.sin(t * 22)), handR=(120, -195 + 12 * math.cos(t * 22)), brows=(-28, -28))
    if S(24) <= t < E(24) + 0.2: st.update(look=(1.0, -0.2), tilt=14, brows=(-10, -10), mouth="flat", handL=CLASP_L, handR=CLASP_R)
    if S(25) <= t < S(31): st.update(brows=(-12, 14), mouth="flat", tilt=-4)
    if S(30) <= t < E(30) + 0.2: st.update(handL=(-120, -190), handR=(120, -190), brows=(-24, -24), mouth="o")
    if HOLD[0] <= t < S(32): st.update(mouth="smile" if (t * 4) % 1 < 0.6 else "flat", eyes="happy", brows=(-6, 10), tilt=8)
    if S(32) <= t < GRAB: st.update(mouth="smile", brows=(-10, 8), tilt=6, eyes="n")
    if S(33) <= t < GRAB: st.update(brows=(-20, -20), mouth="flat")
    if GRAB <= t:
        st.update(rise=ss(GRAB, RUN0, t), handR=(30, -230), handL=(-120, -60), brows=(-24, -24), mouth="smile", pillow=True, tilt=-8, eyes="n")
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
    if t < S(1): return MED
    if E(3) <= t < S(4): return H_CU(t, 2.0)
    if BOOM - 0.2 <= t < S(22):
        k = ss(BOOM - 0.2, BOOM + 0.2, t); return H_CU(t, lerp(1.8, 2.4, k))
    if E(24) <= t < S(26): return G_CU(t, 2.0)
    if HOLD[0] <= t < S(32): return H_CU(t, 2.1)
    if t >= FREEZE2[0]:
        k = ss(FREEZE2[0], FREEZE2[0] + 0.12, t); return (lerp(1.9, 2.4, k), guy_x(FREEZE2[0]) + 30, 990 - 190 * guy_rise(FREEZE2[0]))
    if GRAB <= t:
        k = ss(S(34), S(34) + 0.25, t); return (lerp(1.0, 1.4, k), lerp(540, 330, k), lerp(1130, 1000, k))
    shots = [(1, G_CU), (2, H_CU), (3, G_CU), (4, lambda t: H_CU(t, 2.2)), (5, G_CU), (6, H_CU), (7, G_CU), (8, lambda t: H_CU(t, 2.0)),
             (9, G_CU), (10, H_CU), (11, G_CU), (12, H_CU), (13, lambda t: G_CU(t, 2.0)), (14, lambda t: H_CU(t, 2.2)), (15, G_CU),
             (16, H_CU), (17, G_CU), (18, H_CU), (19, G_CU), (20, lambda t: H_CU(t, 2.1)), (21, G_CU), (22, lambda t: H_CU(t, 2.2)),
             (23, G_CU), (24, H_CU), (26, H_CU), (27, lambda t: G_CU(t, 2.2)), (28, H_CU), (29, G_CU), (30, lambda t: H_CU(t, 2.2)),
             (31, G_CU), (32, H_CU), (33, G_CU)]
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
    for a, amt in ((SCRATCH, 12), (S(14), 10), (BOOM, 18), (S(22), 14), (S(30), 12)):
        if a <= t < a + 0.4:
            d = 1 - (t - a) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    return (0, 0)

HL = {0: {"SOMETHING": "y", "HAPPENED": "y"}, 2: {"GUY": "y", "NUMBER.": "b"}, 3: {"OKAY.": "b"}, 4: {"OH,": "b", "OKAY?!": "b"},
      5: {"NUMBER?": "y"}, 6: {"NO!": "b"}, 7: {"PROBLEM?": "y"}, 8: {"JEALOUS?": "b"}, 9: {"BE?": "y"}, 10: {"ANOTHER": "y", "MAN": "y", "NUMBER!": "b"},
      11: {"REJECTED": "y"}, 13: {"PASSED": "y", "TEST.": "b"}, 14: {"TEST?!": "b"}, 15: {"LOYALTY": "b", "GOOD.": "y"}, 16: {"GIVEN": "y", "NUMBER?": "y"},
      17: {"WHY.": "y"}, 18: {"HANDSOME?": "y"}, 19: {"JOB.": "b"}, 20: {"WHY?!": "b"}, 21: {"LEAVING": "y", "UPGRADING!": "b"},
      22: {"LEAVE": "b"}, 23: {"REALISTIC.": "y"}, 24: {"CHANCE!": "b"}, 25: {"WAIT.": "b"}, 27: {"HIS": "b", "NUMBER?": "b"},
      29: {"ASK": "y"}, 30: {"WHAT?!": "b"}, 31: {"CONFIDENCE": "b", "BOYFRIEND!": "y"}, 32: {"ANNOYING!": "y"}, 33: {"JEALOUS": "b"},
      34: {"NETWORK!": "b"}}

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


def jealousy(cv, t):
    if S(3) + 0.3 <= t < S(11):
        lvl = 0.0
    elif S(27) + 0.3 <= t < S(32):
        lvl = ss(S(27) + 0.3, E(31), t)
    else:
        return
    cv.save(); cv.translate(150, 440)
    text(cv, "HIS JEALOUSY", 110, -40, 34, C("ffffff"), tf=TF_BLACK, stroke=8, stroke_col=C("000000"))
    body = skia.RRect.MakeRectXY(skia.Rect(-20, -18, 240, 40), 12, 12)
    cv.drawRRect(body, P(C("141414"))); cv.drawRRect(body, P(C("ffffff"), stroke=6))
    if lvl > 0.01: cv.drawRect(skia.Rect(-10, -8, -10 + 240 * lvl, 30), P(C("3ccf5a" if lvl < 0.5 else "e8262a")))
    text(cv, f"{int(lvl * 100)}%", 300, 26, 44, C("ffffff"), tf=TF_BLACK, stroke=8, stroke_col=C("000000"))
    cv.restore()

TOP = ["When she says a guy asked for her number…", "HE WASN'T JEALOUS"]

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
    jealousy(cv, t)
    tag(cv, t, WIN, S(15), "LOYALTY TEST: PASSED ✓", 470, col="3ccf5a", fg="141414", size=54)
    tag(cv, t, BOOM, E(21) + 0.7, "\"AT LEAST UPGRADE\"", 470, col="e8262a", fg="ffffff", size=54)
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
