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
GX, HX, GBACK = 330.0, 740.0, 520.0
LEAVE = (E(0) + 0.1, E(0) + 1.3)
GRABP = E(1) + 0.2
BACK = (E(6) + 0.1, S(7) - 0.1)
SIT = (E(8) + 0.1, E(8) + 1.1)
PAUSE = (E(16), S(17))
RUN0 = E(18) + 0.5
FREEZE2 = (RUN0 + 0.15, TOTAL)
BLACK = TOTAL - 0.3
ANGRY = (14, 17)

def at(t):
    return FREEZE2[0] if t >= FREEZE2[0] else t

def guy_x(t):
    if t < LEAVE[0]: return GX
    if t < BACK[0]: return lerp(GX, -300, ss(LEAVE[0], LEAVE[1], t))
    if t < SIT[0]: return lerp(-300, GBACK, ss(BACK[0], BACK[1], t))
    if t < RUN0: return lerp(GBACK, GX, ss(SIT[0], SIT[0] + 0.6, t))
    return GX - 900 * (t - RUN0)

def guy_rise(t):
    if t < LEAVE[0]: return ss(E(0) - 0.4, E(0) + 0.1, t)
    if t < SIT[0] + 0.5: return 1.0
    if t < E(17) - 0.2: return 1 - ss(SIT[0] + 0.5, SIT[1], t)
    return ss(E(18) + 0.1, RUN0, t)

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
CLASP_L, CLASP_R = (60, 60), (-60, 60)

def moving(t):
    return abs(guy_x(t + 0.03) - guy_x(t - 0.03)) > 2

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.0), brows=(8, 8), mouth="smirk", grass="mouth", tilt=0, rise=guy_rise(t))
    st["blink"] = (t % 3.7) < 0.12
    if t < LEAVE[1]:
        st.update(look=(1.0, -0.1), mouth="smile", handR=(110, -100) if S(0) <= t < E(0) else REST_R)
    elif t < SIT[1]:
        st.update(bowl=True, handR=(120, -20), look=(1.0, 0.0), mouth="smile")
        if S(7) - 0.05 <= t: st.update(eyes="wide", brows=(24, 24), mouth="o", sweat=True)          # frozen
        if S(8) <= t: st.update(mouth="flat")
    else:
        st.update(sweat=True, eyes="wide", brows=(20, 20), mouth="flat", bowl=t < S(14), handR=(60, 60) if t < S(14) else REST_R)
        if S(10) <= t < E(10): st.update(mouth="smile", handL=(-130, -60), brows=(14, 14), eyes="n")
        if S(12) <= t < E(12): st.update(mouth="smile", handL=(-140, -80), brows=(16, 16), eyes="n")
        if S(14) <= t < S(15): st.update(handL=UP_L, handR=UP_R, mouth="o", brows=(24, 24))
        if S(15) <= t < S(17):
            st.update(eyes="n", brows=(2, 2), mouth="flat", sweat=False, handL=REST_L, handR=(110, -100) if t < E(15) else REST_R, tilt=0)   # dead serious
        if S(17) <= t: st.update(eyes="wide", mouth="o", brows=(24, 24), sweat=True, handL=UP_L, handR=UP_R)
        if S(18) <= t: st.update(look=(0.0, 0.0), eyes="n", mouth="flat", brows=(6, 6), handL=REST_L, handR=REST_R, sweat=False)   # to camera, deadpan
        if E(18) + 0.1 <= t: st.update(look=(-1.0, 0.0), eyes="wide", mouth="o", brows=(24, 24), handL=UP_L, handR=UP_R, sweat=True)
    if moving(t): st["walk"] = t * (16 if t >= RUN0 else 9)
    if LEAVE[0] <= t < BACK[0]: st["look"] = (-1.0, 0.0)
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=CLASP_L, handR=CLASP_R, look=(-1.0, 0.0), brows=(8, 8), mouth="smile", tilt=-4, rise=0.0)
    st["blink"] = (t % 4.1) < 0.12
    if t < LEAVE[1]: st.update(look=(-1.0, 0.0), brows=(10, 10))
    if S(1) <= t < GRABP: st.update(look=(-0.6, 0.6), brows=(-10, 14), mouth="flat", tilt=-8)       # suspicious
    if GRABP <= t: st.update(phone=True, handR=(-110, 40), look=(-0.5, 0.6), brows=(6, 6), mouth="flat")
    if S(2) <= t < S(3): st.update(mouth="smile", eyes="happy" if t > S(2) + 1.6 else "n", brows=(14, 14), tilt=8)
    if S(3) <= t: st.update(brows=(-6, 10), mouth="flat")
    if S(5) <= t: st.update(brows=(-12, 12))
    if S(6) <= t: st.update(brows=(-16, -10))
    if S(7) <= t: st.update(look=(-1.0, 0.0), brows=(-18, -18))
    if S(8) <= t < E(8) + 0.4: st.update(handL=(-150, 60))
    for i in (9, 11, 13):
        if S(i) <= t < E(i) + 0.3: st.update(look=(-0.5, 0.6), brows=(-16, -6))
    if S(13) <= t: st.update(brows=(-22, -22), eyes="n")
    if E(13) + 0.3 <= t < S(14): st.update(look=(-1.0, 0.0))
    if S(14) <= t < S(15): st.update(handR=(-140, -150), look=(-1.0, 0.0), brows=(-26, -26), mouth="o", tilt=-10)   # "WHAT IS THIS?!"
    if S(15) <= t: st.update(look=(-1.0, 0.0), brows=(-16, 12), mouth="flat", handR=(-110, 40))
    if PAUSE[0] <= t < S(17): st.update(eyes="wide", brows=(16, 16), mouth="flat")
    if S(17) <= t:
        st.update(rise=ss(S(17), S(17) + 0.3, t), handL=(-120, -195 + 12 * math.sin(t * 22)), handR=(120, -195 + 12 * math.cos(t * 22)), brows=(-28, -28), mouth="o", tilt=-10, phone=False)
    if E(17) + 0.3 <= t: st.update(handL=(-18, 168), handR=(18, 168), mouth="flat", eyes="n")
    if E(18) <= t: st.update(handR=(-180, -110), mouth="o", brows=(-28, -28))
    st["amp"] = amp("H", t)
    return st

def bowl(cv, gx, st):
    hip = M.SEAT - 18 - 200 * st["rise"]
    hx, hy = gx + 94 + st["handR"][0], hip - 224 + st["handR"][1]
    cv.drawPath(poly([(hx - 70, hy - 30), (hx + 70, hy - 30), (hx + 45, hy + 25), (hx - 45, hy + 25)]), P(C("3a7bd5")))
    cv.drawPath(poly([(hx - 70, hy - 30), (hx + 70, hy - 30), (hx + 45, hy + 25), (hx - 45, hy + 25)]), P(INK, stroke=5))
    for j in range(6):
        cv.drawOval(skia.Rect(hx - 60 + j * 20, hy - 52 + (j % 2) * 8, hx - 34 + j * 20, hy - 30 + (j % 2) * 8), P(C("ffcf5a")))
    cv.drawCircle(hx, hy, 16, P(C("ffffff"))); cv.drawCircle(hx, hy, 16, P(INK, stroke=5))

def phone_on_couch(cv, t):
    if LEAVE[0] <= t < GRABP:
        cv.save(); cv.translate(470, 1330); cv.rotate(-8)
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-40, -16, 40, 6), 6, 6), P(C("2b2b38"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-40, -16, 40, 6), 6, 6), P(INK, stroke=4))
        cv.restore()

SEARCHES = [(2, "how to make my girlfriend happy", "141414"), (3, "why is my girlfriend angry", "141414"),
            (4, "why is she angry when I didn't|do anything", "141414"), (5, "how to apologise for something|you don't know you did", "141414"),
            (6, "is it normal for girlfriends to|remember everything", "c0392b"), (9, "how to survive an argument|without talking", "c0392b"),
            (11, "how to hide from your girlfriend|in your own house", "e8262a"), (13, "how to disappear and start|a new life", "e8262a")]
SHOW = [(S(2) - 0.4, E(6) + 0.4), (S(9) - 0.1, E(9) + 0.5), (S(11) - 0.1, E(11) + 0.5), (S(13) - 0.1, E(13) + 0.9)]

def history(cv, t):
    win = None
    for a, b in SHOW:
        if a <= t < b: win = (a, b)
    if not win:
        return
    a0, a1 = win
    k = ease_out_back(min(1, (t - a0) / 0.25), 1.6); a = min(1, (a1 - t) / 0.18)
    shown = [s for s in SEARCHES if t >= S(s[0])]
    cv.save(); cv.translate(540, 830); cv.scale(k, k)
    body = skia.RRect.MakeRectXY(skia.Rect(-440, -520, 440, 520), 56, 56)
    cv.drawRRect(body, P(C("000000", 0.4 * a), blur=26)); cv.drawRRect(body, P(C("1d1d26", a)))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-412, -490, 412, 490), 34, 34), P(C("ffffff", a)))
    text(cv, "Search History", -360, -405, 54, C("141414", a), tf=TF_BLACK, align="l")
    cv.drawLine(-380, -370, 380, -370, P(C("d6dae2", a), stroke=4))
    y = -330
    for j, (i, txt, col) in enumerate(reversed(shown)):
        lines = txt.split("|"); h = 30 + 50 * len(lines)
        if y + h > 470: break
        newest = j == 0
        if newest:
            q = min(1, (t - S(i)) / 0.3)
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-395, y - 6, 395, y + h - 12), 18, 18), P(C("fff3a0", a * q)))
        cv.drawCircle(-350, y + 34, 18, P(C("9aa0ad", a), stroke=4)); cv.drawLine(-350, y + 34, -350, y + 22, P(C("9aa0ad", a), stroke=4)); cv.drawLine(-350, y + 34, -340, y + 40, P(C("9aa0ad", a), stroke=4))
        for li, ln in enumerate(lines):
            text(cv, ln, -312, y + 50 + li * 50, 38 if newest else 35, C(col, a), tf=TF_BLACK if newest else TF_B, align="l")
        y += h
    cv.restore()

def G_CU(t, z=1.85):
    return (z, guy_x(t) + 30, 990 - 190 * guy_rise(t))
def H_CU(t, z=1.85):
    return (z, HX - 20, 1040 - 190 * girl_state(t)["rise"])
MED = (1.2, 560, 1060)
WIDE = (1.0, 560, 1130)

def camera(t):
    if t < LEAVE[1]: return MED
    if t < S(2): return H_CU(t, 1.7)
    if BACK[0] <= t < S(8): return (1.15, 560, 1060) if t < S(7) else G_CU(t, 2.1)
    if PAUSE[0] <= t < S(17):
        k = (t - PAUSE[0]) / (S(17) - PAUSE[0]); return H_CU(t, lerp(1.8, 2.4, k))
    if t >= FREEZE2[0]:
        k = ss(FREEZE2[0], FREEZE2[0] + 0.12, t); return (lerp(1.6, 1.9, k), max(guy_x(FREEZE2[0]) + 40, 290), 840)
    if E(18) <= t: return WIDE
    shots = [(2, H_CU), (8, H_CU), (9, H_CU), (10, G_CU), (11, H_CU), (12, G_CU), (13, H_CU), (14, lambda t: H_CU(t, 2.3)),
             (15, G_CU), (16, lambda t: G_CU(t, 2.2)), (17, lambda t: H_CU(t, 2.0)), (18, lambda t: G_CU(t, 2.1))]
    if SIT[0] <= t < S(9): return (1.3, 540, 1060)
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
    for i, amt in ((14, 16), (17, 18)):
        if S(i) <= t < S(i) + 0.4:
            d = 1 - (t - S(i)) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    return (0, 0)

HL = {0: {"DON'T": "b", "TOUCH": "y", "PHONE.": "y"}, 1: {"WHY": "y"}, 2: {"HAPPY.": "y", "AWW!": "y"}, 3: {"ANGRY?": "y"},
      4: {"ANYTHING?": "y"}, 5: {"APOLOGISE": "y"}, 6: {"EVERYTHING?": "b"}, 7: {"PHONE?": "y"}, 8: {"SIT": "b", "DOWN.": "b"},
      9: {"WITHOUT": "y", "TALKING.": "y"}, 10: {"RESEARCH.": "b"}, 11: {"HIDE": "b"}, 12: {"JOKE.": "y"}, 13: {"DISAPPEAR": "b", "NEW": "y", "LIFE?": "y"},
      14: {"WHAT": "b", "IS": "b", "THIS?!": "b"}, 15: {"ONE": "y", "QUESTION.": "y"}, 16: {"LIFE": "b", "INSURANCE": "b", "BOYFRIENDS?": "y"},
      17: {"LIFE": "b", "INSURANCE?!": "b"}, 18: {"LOOK": "y", "NOW.": "b"}}
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





TOP = ["When she checks your search history…", "HE'S BEEN DOING RESEARCH"]

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
    phone_on_couch(cv, ta)
    M.draw_person(cv, ta, girl_state(ta), HX, "girl")
    us = guy_state(ta); ux = guy_x(ta)
    if ux > -280:
        M.draw_person(cv, ta, us, ux, "guy")
        if us.get("bowl"): bowl(cv, ux, us)
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    if t >= FREEZE2[0]:
        fl = max(0, 1 - (t - FREEZE2[0]) / 0.15)
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("ffffff", 0.6 * fl)))
    draw_top(cv, t)
    history(cv, t)
    tag(cv, t, S(1) + 0.3, GRABP + 0.6, "\"DON'T TOUCH MY PHONE\"", 470, col="e8262a", fg="ffffff", size=54)
    tag(cv, t, PAUSE[0] + 0.15, S(17), "STRAIGHT FACE", 470, col="ffffff", size=58)
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
