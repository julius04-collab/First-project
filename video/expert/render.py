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
PROF = (S(1), S(20) + 0.3)              # professor glasses on
CATCH = E(6) + 0.02
BOING = E(11) + 0.05
STARE = (E(17), S(18))
BOOM = S(20) + 0.25
SIL = (E(20), S(21))
BELL = E(21) + 0.05
LEAVE0 = S(22) - 0.2
BLACK = TOTAL - 0.5
ANGRY = (8, 16, 20, 22)

def guy_x(t):
    if t < LEAVE0: return GX
    return GX - 380 * (t - LEAVE0 - 0.3) if t > LEAVE0 + 0.3 else GX

def guy_rise(t):
    return ss(LEAVE0, LEAVE0 + 0.3, t)

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
CLASP_L, CLASP_R = (60, 60), (-60, 60)
GLASSES_HAND = (-60, -200)

def professor(st, t, i):
    """serious lecturing gestures"""
    w = math.sin(t * 3.2)
    st.update(look=(1.0, 0.0), brows=(-2, -2), mouth="flat", tilt=4 * w, handR=(130, -110 + 30 * w))
    if (t % 3.0) < 0.5: st.update(handR=GLASSES_HAND)          # adjusts the glasses
    if (t % 1.4) < 0.25: st["look"] = (1.0, 0.25)               # confident nod

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.0), brows=(8, 8), mouth="smirk", grass="mouth", tilt=0, rise=guy_rise(t))
    st["blink"] = (t % 3.7) < 0.12
    if t < S(1): st.update(look=(1.0, 0.0), brows=(12, 12), mouth="flat")
    if S(1) <= t < S(4): professor(st, t, 1)
    if S(4) <= t < S(5): st.update(mouth="smile", brows=(10, 10))
    if S(5) <= t < S(6): st.update(mouth="smile", eyes="happy", handR=GLASSES_HAND, tilt=8, brows=(14, 4))   # proud
    if S(6) <= t < S(12):
        st.update(phone=True, handL=(90, 50), look=(0.4, 0.7), mouth="smirk")
        if S(7) <= t: st.update(look=(1.0, 0.0), mouth="smile", brows=(14, 14))
        if S(8) <= t < S(9): st.update(eyes="wide", brows=(18, 18), mouth="flat")
        if S(9) <= t < E(9): professor(st, t, 9); st.update(phone=True, handL=(90, 50))
        if S(10) <= t < S(11): st.update(eyes="wide", mouth="flat", sweat=True)
        if S(11) <= t: st.update(mouth="smile", brows=(16, 16), handR=(120, -80), sweat=True)     # fake professional smile
    if S(12) <= t < S(18):
        st.update(mouth="smile", brows=(14, 14))
        if S(13) <= t < E(13): professor(st, t, 13)
        if S(15) <= t < E(15): st.update(handR=(130, -60), mouth="smile", brows=(10, 10))
        if S(16) <= t < S(17): st.update(eyes="wide", brows=(20, 20), mouth="flat", sweat=True)
        if S(17) <= t: professor(st, t, 17); st.update(mouth="smile")
    if S(18) <= t < S(20):
        st.update(rise=0, mouth="flat", brows=(4, 4), lean=-4)
        if S(19) <= t: professor(st, t, 19)                                                     # sits up confidently
    if S(20) <= t < S(21):
        st.update(eyes="wide", mouth="o", brows=(24, 24), sweat=True, handR=REST_R, look=(1.0, 0.0), tilt=0)   # shocked
    if S(21) <= t: st.update(mouth="smile", eyes="n", brows=(16, 16), sweat=True, look=(0.0, 0.0), phone=True, handL=(90, 30))   # awkward smile
    if LEAVE0 <= t:
        st.update(look=(-1.0, 0.0), mouth="smile", eyes="n")
        if LEAVE0 + 0.3 <= t: st["walk"] = t * 10
        if S(23) <= t: st.update(look=(1.0, 0.0) if t < S(23) + 0.6 else (-1.0, 0.0), handR=(120, -120))
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=CLASP_L, handR=CLASP_R, look=(-1.0, 0.0), brows=(-8, -8), mouth="flat", tilt=-4, rise=0.0)
    st["blink"] = (t % 4.1) < 0.12
    if t < S(1): st.update(look=(-0.2, 0.4), brows=(14, 14), tilt=6)                         # frustrated
    if S(1) <= t < S(4): st.update(brows=(6, 6), mouth="flat")
    if S(3) + 2 <= t < S(5): st.update(eyes="wide", mouth="smile", brows=(16, 16), tilt=8)    # impressed
    if S(5) <= t < S(6): st.update(brows=(-12, 14), mouth="flat", tilt=-6)                    # suspicious
    if S(6) <= t < S(12):
        st.update(brows=(-14, 10))
        if S(8) <= t < E(8): st.update(handR=(-160, -70), brows=(-20, -20))
        if S(10) <= t < E(10): st.update(handR=(-160, -70 + 12 * math.sin(t * 9)), brows=(-18, -18))
        if S(11) <= t: st.update(brows=(-16, 12))
    if S(12) <= t < S(18):
        st.update(brows=(-14, 10))
        if S(14) <= t < S(15): st.update(brows=(-12, 16), tilt=-8)
        if S(16) <= t < E(16) + 0.3:
            st.update(handL=(-120, -195 + 12 * math.sin(t * 22)), handR=(120, -195 + 12 * math.cos(t * 22)), brows=(-26, -26), tilt=-10)
        if STARE[0] <= t: st.update(brows=(-20, -20), eyes="n")
    if S(18) <= t: st.update(brows=(-16, 8), mouth="flat")
    if S(18) <= t < E(18): st.update(handR=(-140, -60))
    if S(20) <= t < E(20) + 0.3: st.update(handR=(-180, -90), brows=(-26, -26), tilt=-10)
    if SIL[0] + 0.3 <= t < S(22): st.update(handL=CLASP_L, handR=CLASP_R, mouth="smirk", brows=(-10, 6), tilt=6)   # satisfied
    if S(22) <= t: st.update(handL=(-120, -190), handR=(120, -190), brows=(-26, -26), mouth="o", tilt=-10)
    if E(22) + 0.4 <= t: st.update(handL=CLASP_L, handR=CLASP_R, mouth="flat", brows=(-20, -20), look=(-1.0, 0.0))
    st["amp"] = amp("H", t)
    return st

def glasses(cv, gx, st, t):
    hip = M.SEAT - 18 - 200 * st["rise"] - st.get("bob", 0)
    lean = math.radians(st.get("lean", 0))
    hcx = gx + (-(240 + 28 + 98)) * -math.sin(lean) * 0
    hc = (gx - (240 + 28 + 98) * math.sin(lean) * -1 * 0, hip - 366)
    lx, ly = st.get("look", (0, 0))
    cv.save(); cv.translate(gx - 366 * math.sin(lean), hip - 366 * math.cos(lean) + 0); cv.rotate(st.get("tilt", 0) + math.degrees(lean) * 0.5)
    for ex in (-1, 1):
        cx, cy = ex * 36 + lx * 14, -2 + ly * 10
        cv.drawCircle(cx, cy, 30, P(C("ffffff", 0.25))); cv.drawCircle(cx, cy, 30, P(INK, stroke=7))
    cv.drawLine(-6 + lx * 14, -6 + ly * 10, 6 + lx * 14, -6 + ly * 10, P(INK, stroke=6))
    cv.drawLine(66 + lx * 14, -10 + ly * 10, 96, -18, P(INK, stroke=6))
    cv.restore()

def falling_glasses(cv, t, gx):
    if not (BOOM <= t < BOOM + 1.2): return
    d = t - BOOM; y = M.SEAT - 18 - 366 + 600 * d * d; x = gx + 60 * d
    cv.save(); cv.translate(x, min(y, 1590)); cv.rotate(200 * d)
    for ex in (-1, 1):
        cv.drawCircle(ex * 36, 0, 30, P(INK, stroke=7))
    cv.drawLine(-6, -4, 6, -4, P(INK, stroke=6))
    cv.restore()

def phone_scores(cv, t):
    a0, a1 = CATCH, S(8) + 0.2
    if not (a0 <= t < a1): return
    k = ease_out_back(min(1, (t - a0) / 0.25), 1.8); a = min(1, (a1 - t) / 0.15)
    cv.save(); cv.translate(540, 820); cv.rotate(-5); cv.scale(k, k)
    body = skia.RRect.MakeRectXY(skia.Rect(-220, -380, 220, 380), 44, 44)
    cv.drawRRect(body, P(C("000000", 0.35 * a), blur=24)); cv.drawRRect(body, P(C("1d1d26", a)))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-196, -350, 196, 350), 26, 26), P(C("14361f", a)))
    chip(cv, 0, -280, "LIVE", a=a, col="e8262a", fg="ffffff", size=40)
    text(cv, "FOOTBALL SCORES", 0, -190, 40, C("ffffff", a), tf=TF_BLACK)
    for j, (h1, s1, a2, h2) in enumerate((("LIONS", "2", "1", "EAGLES"), ("TIGERS", "0", "0", "SHARKS"), ("BULLS", "3", "2", "WOLVES"))):
        y = -90 + j * 140
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-176, y - 50, 176, y + 60), 18, 18), P(C("1f4d2c", a)))
        text(cv, h1, -160, y + 20, 30, C("ffffff", a), tf=TF_B, align="l")
        text(cv, f"{s1} - {a2}", 0, y + 22, 44, C("ffd21f", a), tf=TF_BLACK)
        text(cv, h2, 160, y + 20, 30, C("ffffff", a), tf=TF_B, align="r")
    cv.restore()

def G_CU(t, z=1.85):
    return (z, guy_x(t) + 30, 990 - 190 * guy_rise(t))
def H_CU(t, z=1.85):
    return (z, HX - 20, 1040)
TWO = (1.3, 540, 1060)
WIDE = (1.0, 560, 1130)

def camera(t):
    if t < S(1): return TWO
    if S(1) <= t < S(4):
        k = (t - S(1)) / (S(4) - S(1)); return (lerp(1.4, 1.75, k), GX + 60, 1000)
    if STARE[0] <= t < S(18):
        k = (t - STARE[0]) / (S(18) - STARE[0]); return H_CU(t, lerp(1.8, 2.3, k))
    if S(18) <= t < S(20): return (1.2, 540, 1060)
    if S(20) <= t < S(21):
        if t < E(20): return H_CU(t, 2.2)
        k = (t - E(20)) / (S(21) - E(20)); return G_CU(t, lerp(1.9, 2.5, k))
    if LEAVE0 <= t: return WIDE
    shots = [(4, H_CU), (5, G_CU), (6, H_CU), (7, G_CU), (8, lambda t: H_CU(t, 2.1)), (9, G_CU), (10, H_CU), (11, G_CU),
             (12, TWO), (13, G_CU), (14, H_CU), (15, G_CU), (16, lambda t: H_CU(t, 2.3)), (17, G_CU), (21, G_CU)]
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
    for a, amt in ((S(8), 10), (S(16), 14), (BOOM, 20), (S(22), 14), (CATCH, 8)):
        if a <= t < a + 0.4:
            d = 1 - (t - a) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    return (0, 0)

HL = {0: {"LISTEN": "b"}, 1: {"COMMUNICATION": "b", "FOUNDATION": "y"}, 3: {"EXPRESS": "y", "FEELINGS.": "y", "TIME": "b"},
      4: {"RELATIONSHIP": "y", "EXPERT?": "b"}, 5: {"EXPERIENCE,": "y", "EXPERIENCE.": "b"}, 6: {"LISTENED": "y", "PHONE?": "b"},
      7: {"GOOD": "y", "QUESTION.": "y"}, 8: {"YOU!": "b"}, 9: {"PROFESSIONAL": "y", "ANALYSIS.": "y"}, 10: {"FOOTBALL": "b", "SCORES": "b"},
      11: {"MULTITASKING.": "b"}, 12: {"DATE": "y"}, 13: {"BOTH": "b"}, 14: {"SO?": "y"}, 15: {"YOU": "y", "ROMANTIC": "y"},
      16: {"ADVICE!": "b"}, 17: {"TEACHING": "y"}, 18: {"PROFESSOR,": "y", "LISTEN,": "y", "DATES,": "y", "EXCUSES?": "b"},
      19: {"PROBLEM.": "y", "CALMLY.": "y"}, 20: {"YOU!": "b"}, 21: {"CLASS": "b", "DISMISSED.": "b"}, 22: {"GOING?!": "b"},
      23: {"RESEARCH": "y", "STRATEGY!": "y"}}
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





TOP = ["When your boyfriend becomes a…", "\"RELATIONSHIP EXPERT\""]

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
    CO.draw_room(cv, t); CO.draw_couch_back(cv); CO.draw_couch_front(cv)
    M.draw_person(cv, t, girl_state(t), HX, "girl")
    us = guy_state(t); ux = guy_x(t)
    if ux > -300:
        M.draw_person(cv, t, us, ux, "guy")
        if PROF[0] <= t < BOOM: glasses(cv, ux, us, t)
    falling_glasses(cv, t, ux)
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    draw_top(cv, t)
    tag(cv, t, S(1) + 0.2, S(2), "PROFESSOR MODE: ON", 470, col="3a7bd5", fg="ffffff", size=56)
    tag(cv, t, S(5) + 0.3, S(6), "15 YEARS OF EXPERIENCE*", 470, col="ffd23f", size=52)
    phone_scores(cv, t)
    tag(cv, t, BOING, S(12), "\"MULTITASKING\"", 470, col="ffffff", size=58)
    tag(cv, t, S(19) + 0.3, S(20), "PROFESSIONAL ADVICE", 470, col="3a7bd5", fg="ffffff", size=54)
    bubble(cv, t, BELL, S(22) + 0.4, "CLASS DISMISSED", 540, 560, col="ffd23f", size=76)
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
