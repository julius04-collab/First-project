import importlib.util, json, math, os, subprocess, sys
import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from render import C, clamp, ss, ease_out_back, P, lin, rad, poly, text, chip, pop, TF_BLACK, TF_B

spec = importlib.util.spec_from_file_location("mia_render", os.path.join(HERE, "..", "mia", "render.py"))
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)

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

T_LAMP = E(10) + 0.25       # lamp switches off
GX, HX = 380.0, 720.0

# ------------------------------------------------------------------ bedroom at night
def draw_room(cv, t, dark):
    cv.drawRect(skia.Rect(0, 0, W, 1420), P(C("3b3a63")))
    for i in range(9):
        cv.drawRect(skia.Rect(i * 130 + 60, 0, i * 130 + 70, 1420), P(C("35345a")))
    # window with moon
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(80, 260, 400, 700), 10, 10), P(C("5a5f85")))
    cv.drawRect(skia.Rect(98, 278, 382, 682), P(0, shader=lin(0, 278, 0, 682, [C("0e1838"), C("27305a")])))
    cv.drawCircle(300, 380, 42, P(C("f4f1d8")))
    cv.drawCircle(318, 368, 38, P(C("16204a")))
    for (sx, sy) in ((140, 330), (200, 450), (340, 560), (160, 600), (250, 300)):
        cv.drawCircle(sx, sy, 3, P(C("ffffff")))
    cv.drawLine(240, 278, 240, 682, P(C("5a5f85"), stroke=12)); cv.drawLine(98, 480, 382, 480, P(C("5a5f85"), stroke=12))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(80, 260, 400, 700), 10, 10), P(INK, stroke=7))
    cv.drawPath(poly([(320, 700), (560, 1420), (900, 1420), (420, 700)]), P(C("c8d4ff", 0.06)))
    # fairy lights
    pts = [(x, 160 + 50 * math.sin(math.pi * x / W)) for x in range(0, W + 1, 40)]
    pth = skia.Path(); pth.moveTo(*pts[0])
    for p_ in pts[1:]:
        pth.lineTo(*p_)
    cv.drawPath(pth, P(INK, stroke=3))
    for k, (x, y) in enumerate(pts[::2]):
        on = 0.7 + 0.3 * math.sin(t * 3 + k)
        col = ["ffd36e", "ff8fb3", "8fd8ff", "b5f58a"][k % 4]
        cv.drawCircle(x, y + 12, 22, P(C(col, 0.35 * on * (1 - 0.6 * dark)), blur=8))
        cv.drawCircle(x, y + 12, 8, P(C(col, on * (1 - 0.5 * dark))))
    # framed picture
    cv.drawRect(skia.Rect(640, 330, 860, 500), P(C("8a8fb0"))); cv.drawRect(skia.Rect(640, 330, 860, 500), P(INK, stroke=6))
    M.heart(cv, 750, 420, 1.3, "ff8fb3")
    # floor
    cv.drawRect(skia.Rect(0, 1420, W, H), P(C("3a3350")))
    for i in range(8):
        cv.drawLine(0, 1460 + i * 64, W, 1460 + i * 64, P(C("302a45"), stroke=4))

def draw_headboard(cv):
    hb = skia.RRect.MakeRectXY(skia.Rect(130, 900, 960, 1360), 50, 50)
    cv.drawRRect(hb, P(C("9a5a34"))); cv.drawRRect(hb, P(INK, stroke=7))
    for x in range(220, 900, 110):
        cv.drawLine(x, 940, x, 1330, P(C("7a4422"), stroke=6))
    for x in (GX, HX):
        pl = skia.RRect.MakeRectXY(skia.Rect(x - 150, 1110, x + 150, 1290), 60, 60)
        cv.drawRRect(pl, P(C("f4f1e8"))); cv.drawRRect(pl, P(INK, stroke=6))

def draw_blanket(cv):
    bl = skia.Path(); bl.moveTo(100, 1360)
    for x in range(100, 1000, 60):
        bl.lineTo(x, 1360 + 12 * math.sin(x * 0.03))
    bl.lineTo(990, 1700); bl.lineTo(90, 1700); bl.close()
    cv.drawPath(bl, P(C("5a8fe0"))); cv.drawPath(bl, P(INK, stroke=7))
    cv.drawRect(skia.Rect(100, 1350, 990, 1400), P(C("f4f1e8"))); cv.drawRect(skia.Rect(100, 1350, 990, 1400), P(INK, stroke=6))
    for k in range(5):
        cv.drawLine(180 + k * 170, 1430, 220 + k * 170, 1680, P(C("4a7fd0"), stroke=6))
    cv.drawRect(skia.Rect(90, 1690, 1000, 1760), P(C("9a5a34"))); cv.drawRect(skia.Rect(90, 1690, 1000, 1760), P(INK, stroke=6))

def draw_lamp(cv, on):
    cv.drawRect(skia.Rect(950, 1180, 1080, 1420), P(C("8a5a2e"))); cv.drawRect(skia.Rect(950, 1180, 1080, 1420), P(INK, stroke=6))
    cv.drawRect(skia.Rect(1005, 1090, 1019, 1180), P(INK))
    shade = poly([(960, 1100), (1064, 1100), (1040, 1000), (984, 1000)])
    cv.drawPath(shade, P(C("ffe9a8" if on else "6a6a80"))); cv.drawPath(shade, P(INK, stroke=6))
    if on:
        cv.drawCircle(1012, 1060, 300, P(C("ffe2a0", 0.28), blur=70))

# ------------------------------------------------------------------ acting
def guy_state(t):
    st = dict(handL=(70, 40), handR=(-10, 150), phone=True, look=(0.0, 0.6), brows=(0, 0), mouth="flat", grass="mouth", tilt=0, lean=0)
    st["bob"] = 1.5 * math.sin(t * 1.2)
    if S(6) <= t < S(7) + 0.2:
        st["look"] = (0.0, 0.6)
    if S(7) - 0.9 <= t < E(8) + 0.4:
        st["phone"] = t < S(7) - 0.5
        st["handL"] = lerp2((70, 40), (-20, 160), ss(S(7) - 0.9, S(7) - 0.5, t))
        st["look"] = (1.0, -0.1); st["brows"] = (6, 6); st["mouth"] = "smile" if t > E(7) else "flat"; st["tilt"] = 4
    if E(8) + 0.4 <= t < S(9):
        st["phone"] = True; st["look"] = (0.0, 0.6); st["mouth"] = "smile"
    if S(9) - 0.4 <= t:
        st["phone"] = False; st["handL"] = (-20, 160); st["look"] = (1.0, -0.1); st["brows"] = (4, 10); st["mouth"] = "flat"; st["tilt"] = 4
    if E(9) <= t:
        st["mouth"] = "flat"; st["brows"] = (8, 8)
    if S(10) <= t:
        st["brows"] = (14, 14); st["eyes"] = "n"
    st["amp"] = amp("G", t)
    st["blink"] = (t % 3.9) < 0.12
    return st

def girl_state(t):
    st = dict(handL=(-30, 160), handR=(-40, 150), look=(-1.0, -0.1), brows=(6, 6), mouth="smile", tilt=6, lean=0)
    st["bob"] = 1.5 * math.sin(t * 1.2 + 1)
    if S(0) - 0.2 <= t < E(0):
        st["handR"] = (-150, -30 + 15 * math.sin(t * 10)); st["eyes"] = "n"   # poking his arm
    if S(4) <= t < E(4) + 0.2:
        st["brows"] = (-6, 10); st["tilt"] = -4
    if E(5) <= t < E(5) + 0.5:
        st["handR"] = (-160, -50); st["eyes"] = "wide"; st["mouth"] = "o"; st["brows"] = (16, 16)   # gasp + slap
    if S(6) <= t < E(6) + 0.6:
        st["brows"] = (12, 4); st["tilt"] = 10; st["handR"] = (-40, 40); st["look"] = (-1.0, -0.3)
    if E(7) <= t < S(9):
        st["eyes"] = "happy"; st["mouth"] = "grin"; st["handR"] = (-30, -20); st["handL"] = (30, -20); st["tilt"] = 14
    if E(8) + 0.2 <= t < S(9) + 0.2:
        st["lean"] = -16 * ss(E(8) + 0.2, E(8) + 0.6, t)                       # head on his shoulder
    if S(9) + 0.2 <= t:
        st["lean"] = -16 * (1 - ss(S(9) + 0.2, S(9) + 0.6, t)); st["mouth"] = "smile"; st["eyes"] = "n"
    if E(9) - 0.1 <= t < S(10):
        st["mouth"] = "flat"; st["eyes"] = "wide"; st["brows"] = (14, 14)
        st["look"] = lerp2((-1.0, -0.1), (1.0, -0.3), ss(E(9) + 0.6, E(9) + 1.4, t)); st["tilt"] = 0
        st["sweat"] = t > E(9) + 1.2
    if S(10) <= t:
        st["eyes"] = "closed"; st["mouth"] = "o" if amp("H", t) < 0.06 else "flat"; st["handR"] = (60, -130); st["handL"] = (-60, -130)
        st["look"] = (1.0, 0.0); st["tilt"] = 8
    if E(10) <= t:
        st["handR"] = (130, -20); st["lean"] = 18 * ss(E(10), E(10) + 0.3, t); st["eyes"] = "closed"; st["mouth"] = "flat"
    st["amp"] = amp("H", t)
    st.setdefault("blink", (t % 4.3) < 0.12)
    return st

def camera(t):
    if t < S(0):
        return (1.05, 560, 1180)
    shots = [
        (S(0), E(0) + 0.1, (1.6, HX - 40, 1040)),
        (S(1), E(1) + 0.2, (1.8, GX + 20, 1020)),
        (S(2), E(2) + 0.1, (1.7, HX - 40, 1040)),
        (S(3), E(3) + 0.2, (1.8, GX + 20, 1020)),
        (S(4), E(4) + 0.1, (1.7, HX - 40, 1040)),
        (S(5), S(6), (1.25, 550, 1120)),
        (S(6), S(7) - 1.0, (1.85, HX - 30, 1020)),
        (S(7) - 1.0, E(7) + 0.2, (1.85, GX + 20, 1010)),
        (E(7) + 0.2, E(8) + 0.2, (1.75, HX - 30, 1020)),
        (E(8) + 0.2, S(9), (1.25, 550, 1120)),
        (S(9), E(9), (1.6, GX + 60, 1040)),
        (E(9), S(10), (1.95, HX - 30, 1010)),
    ]
    for a, b, c in shots:
        if a <= t < b:
            return c
    if t < T_LAMP + 0.8:
        return (1.15, 560, 1140)
    k = ss(T_LAMP + 0.8, TOTAL, t)
    return (lerp(1.15, 1.6, k), lerp(560, GX + 20, k), lerp(1140, 1040, k))

def chunks():
    out = []
    for s in SEGS:
        words = s["text"].split()
        cs, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= 3 or w[-1] in ",.?!…":
                cs.append(cur); cur = []
        if cur:
            cs.append(cur)
        wt = [sum(len(w) + 1 for w in c) for c in cs]; tot = sum(wt); acc = 0
        for c, x in zip(cs, wt):
            out.append((s["start"] + (s["end"] - s["start"]) * acc / tot, s["start"] + (s["end"] - s["start"]) * (acc + x) / tot, " ".join(c), s["who"]))
            acc += x
    return out
CAPS = chunks()

def draw_caption(cv, t):
    for (a, b, txt, who) in CAPS:
        if a <= t < b + 0.15:
            k = ease_out_back((t - a) / 0.2, 2.0)
            s = txt.upper()
            f = skia.Font(TF_BLACK, 80); w = f.measureText(s)
            if w > 980:
                f = skia.Font(TF_BLACK, 80 * 980 / w); w = f.measureText(s)
            cv.save(); cv.translate(540, 1745); cv.scale(k, k)
            col = C("ffd23f") if who == "H" else C("ffffff")
            cv.drawString(s, -w / 2, 28, f, P(C("000000"), stroke=16)); cv.drawString(s, -w / 2, 28, f, P(col))
            cv.restore()
            chip(cv, 540, 1640, "HER" if who == "H" else "HIM", a=0.95, col="ffd23f" if who == "H" else "ffffff", fg="1a1a1a", size=30)
            return

TOP = ["She asked 'Would you still love me if…'", "but wasn't ready for HIS question"]

def draw_top(cv, t):
    f = skia.Font(TF_B, 42)
    w = max(f.measureText(s) for s in TOP) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 286), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    for i, s in enumerate(TOP):
        text(cv, s, 540, 208 + i * 56, 42, C("111111"), tf=TF_B)
    te = E(11) + 0.3
    if t > te:
        a, k = pop(t, te, 0.45)
        chip(cv, 540, 400, "WHO'S WRONG?", a=a, scale=k, col="ffd23f", fg="1a1a1a", size=62)

def glowing_eyes(cv, t):
    """his eyes in the dark (world coords)"""
    hip_y = M.SEAT - 18
    hx, hy = GX, hip_y - 240 - 28 - M.HEAD_R + 4
    blink = (t - T_LAMP) % 2.2 > 2.05
    for ex in (-1, 1):
        cx, cy = hx + ex * 36 + 12, hy - 2
        if blink:
            cv.drawLine(cx - 18, cy, cx + 18, cy, P(C("ffffff"), stroke=6))
        else:
            cv.drawOval(skia.Rect(cx - 20, cy - 26, cx + 20, cy + 26), P(C("ffffff")))
            cv.drawCircle(cx + 10, cy, 9, P(INK))

def render_frame(cv, t):
    dark = ss(T_LAMP, T_LAMP + 0.08, t)
    z, wx, wy = camera(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-wx, -wy)
    draw_room(cv, t, dark)
    draw_headboard(cv)
    M.draw_person(cv, t, guy_state(t), GX, "guy")
    M.draw_person(cv, t, girl_state(t), HX, "girl")
    draw_blanket(cv)
    draw_lamp(cv, dark < 0.5)
    if dark > 0:
        cv.drawRect(skia.Rect(-200, -200, W + 200, H + 200), P(C("05060f", 0.86 * dark)))
        cv.drawPath(poly([(320, 700), (560, 1420), (900, 1420), (420, 700)]), P(C("c8d4ff", 0.07 * dark)))
        if t > T_LAMP + 0.5:
            glowing_eyes(cv, t)
    cv.restore()
    if E(9) <= t < S(10):
        pass
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("0a0a1a", 0.35)], [0.6, 1])))
    draw_top(cv, t)
    draw_caption(cv, t)
    fade = 1 - ss(TOTAL - 0.4, TOTAL, t)
    if t < 0.3:
        fade = min(fade, t / 0.3)
    if fade < 1:
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("000000", 1 - fade)))

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
        print("lamp", T_LAMP, "total", TOTAL)
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
