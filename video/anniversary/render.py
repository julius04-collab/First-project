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

GX, HX = 330.0, 800.0
T_JERSEY = E(12) + 0.3       # pulls the jersey out of the bag
T_HIT = E(14) + 0.35

def girl_x(t):
    return lerp(1250, HX, ss(0, 1.2, t))

# ------------------------------------------------------------------ props
def scarf(cv, t, cx, bob):
    hip_y = M.SEAT - 18 - bob
    ny = hip_y - 240
    p = skia.RRect.MakeRectXY(skia.Rect(cx - 70, ny - 14, cx + 70, ny + 22), 16, 16)
    cv.drawRRect(p, P(C("e74c3c"))); cv.drawRRect(p, P(INK, stroke=5))
    for k in range(4):
        cv.drawRect(skia.Rect(cx - 56 + k * 34, ny - 12, cx - 40 + k * 34, ny + 20), P(C("ffffff")))
    tail = poly([(cx + 20, ny + 10), (cx + 62, ny + 10), (cx + 70, ny + 150), (cx + 30, ny + 150)])
    cv.drawPath(tail, P(C("e74c3c"))); cv.drawPath(tail, P(INK, stroke=5))
    for k in range(3):
        y = ny + 40 + k * 36
        cv.drawRect(skia.Rect(cx + 24, y, cx + 66, y + 14), P(C("ffffff")))
    for k in range(4):
        cv.drawLine(cx + 34 + k * 9, ny + 150, cx + 34 + k * 9, ny + 170, P(INK, stroke=4))

def gift_bag(cv, x, y, s=1.0):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    p = poly([(-60, -80), (60, -80), (72, 60), (-72, 60)])
    cv.drawPath(p, P(C("e84a7a"))); cv.drawPath(p, P(INK, stroke=6))
    cv.drawArc(skia.Rect(-34, -122, 34, -50), 180, 180, False, P(INK, stroke=6))
    M.heart(cv, 0, -10, 0.9, "ffd23f")
    cv.restore()

def jersey(cv, x, y, s=1.0, rot=0.0):
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(s, s)
    p = poly([(-90, -110), (-40, -125), (40, -125), (90, -110), (140, -60), (105, -20), (80, -40), (80, 130), (-80, 130), (-80, -40), (-105, -20), (-140, -60)])
    cv.drawPath(p, P(C("e74c3c"))); cv.drawPath(p, P(INK, stroke=6))
    cv.drawRect(skia.Rect(-80, 100, 80, 130), P(C("ffffff")))
    cv.drawPath(p, P(INK, stroke=6))
    text(cv, "DAVE", 0, -62, 46, C("ffffff"), tf=TF_BLACK)
    text(cv, "3", 0, 70, 130, C("ffffff"), stroke=8, stroke_col=C("141414"))
    cv.restore()

def soul(cv, t, t0):
    q = (t - t0) / 1.2
    if not 0 <= q <= 1:
        return
    hip_y = M.SEAT - 18
    hx, hy = GX, hip_y - 240 - 28 - M.HEAD_R + 4 - 260 * q
    cv.save(); cv.saveLayerAlpha(None, int(180 * (1 - q)))
    cv.drawCircle(hx + 20 * math.sin(q * 8), hy, M.HEAD_R, P(C("eaf6ff")))
    cv.drawCircle(hx + 20 * math.sin(q * 8), hy, M.HEAD_R, P(C("9fc8e8"), stroke=6))
    for ex in (-1, 1):
        cv.drawLine(hx + ex * 36 - 12 + 20 * math.sin(q * 8), hy - 12, hx + ex * 36 + 12 + 20 * math.sin(q * 8), hy + 12, P(C("7fa8c8"), stroke=6))
        cv.drawLine(hx + ex * 36 + 12 + 20 * math.sin(q * 8), hy - 12, hx + ex * 36 - 12 + 20 * math.sin(q * 8), hy + 12, P(C("7fa8c8"), stroke=6))
    tail = poly([(hx - 60, hy + 70), (hx + 60, hy + 70), (hx + 10 * math.sin(q * 9), hy + 200)])
    cv.drawPath(tail, P(C("eaf6ff")))
    cv.restore(); cv.restore()

def tears(cv, t, t0):
    if t < t0:
        return
    hip_y = M.SEAT - 18
    hx, hy = GX, hip_y - 240 - 28 - M.HEAD_R + 4
    for ex in (-1, 1):
        for j in range(2):
            q = ((t - t0) * 1.4 + j * 0.5) % 1
            cx, cy = hx + ex * 36 + 12, hy + 20 + q * 90
            dp = skia.Path(); dp.moveTo(cx, cy - 14); dp.quadTo(cx + 10, cy + 4, cx, cy + 10); dp.quadTo(cx - 10, cy + 4, cx, cy - 14)
            cv.drawPath(dp, P(C("8fd8ff", 1 - q))); cv.drawPath(dp, P(INK, stroke=3))

def thwack(cv, t):
    q = (t - T_HIT - 0.25) / 0.6
    if not 0 <= q <= 1:
        return
    hip_y = M.SEAT - 18
    hx, hy = GX, hip_y - 240 - 28 - M.HEAD_R + 4
    for k in range(6):
        a = k * math.pi / 3
        r = 90 + 120 * q
        x, y = hx + math.cos(a) * r, hy + math.sin(a) * r
        star = skia.Path()
        for j in range(10):
            ang = -math.pi / 2 + j * math.pi / 5; rr = 26 if j % 2 == 0 else 11
            px, py = x + math.cos(ang) * rr, y + math.sin(ang) * rr
            star.moveTo(px, py) if j == 0 else star.lineTo(px, py)
        star.close()
        cv.drawPath(star, P(C("ffd23f", 1 - q))); cv.drawPath(star, P(C("141414", 1 - q), stroke=3))
    text(cv, "THWACK!", hx + 40, hy - 150, 70, C("ff5a4a", 1 - q), stroke=10, stroke_col=C("ffffff", 1 - q))

# ------------------------------------------------------------------ acting
def guy_state(t):
    st = dict(handL=(30, 150), handR=(-20, 150), look=(0.2, 0.5), brows=(0, 0), mouth="flat", grass="mouth", tilt=0, lean=-4)
    st["bob"] = 1.5 * math.sin(t * 1.3)
    st["look"] = (0.0, 0.3)  # watching the TV (towards us)
    if S(2) + 0.6 <= t < S(3):
        st["eyes"] = "wide"; st["mouth"] = "o"; st["brows"] = (20, 20); st["look"] = (0.6, 0); st["sweat"] = True
    if S(3) <= t < E(7) + 0.3:
        st["look"] = (1.0, -0.1); st["brows"] = (10, 10); st["sweat"] = True; st["lean"] = 0
        st["handR"] = (120, -30 + 15 * math.sin(t * 4))
    if S(5) <= t < E(5):
        st["look"] = (0.4, -0.8); st["handR"] = (-40, -120); st["tilt"] = -8           # scratching head
    if S(7) <= t < E(7):
        st["look"] = (0.3, -0.8); st["handR"] = (110, -60); st["tilt"] = 6
    if S(9) - 0.15 <= t < E(11):
        st["look"] = (1.0, -0.1); st["eyes"] = "n"; st["brows"] = (14, 14); st["sweat"] = False; st["lean"] = 6
        st["handR"] = (110, -170); st["bob"] = 14 * ss(S(9) - 0.15, S(9) + 0.1, t)      # sits up, finger raised
        st["mouth"] = "grin" if amp("G", t) < 0.06 else "flat"
    if E(11) <= t < S(14):
        st["look"] = (1.0, -0.1); st["brows"] = (6, 6); st["mouth"] = "smile"; st["lean"] = 0
        if S(12) <= t:
            st["eyes"] = "wide"; st["mouth"] = "o"; st["brows"] = (16, 16)
        if T_JERSEY + 0.4 <= t:
            st["eyes"] = "wide"; st["mouth"] = "o"; st["brows"] = (-10, 14)
    if S(14) - 0.2 <= t:
        st["look"] = (1.0, -0.1); st["eyes"] = "n"; st["mouth"] = "wobble"; st["brows"] = (-14, 10); st["handR"] = (40, -40); st["handL"] = (-40, -40)
    if T_HIT + 0.25 <= t:
        st["eyes"] = "closed"; st["mouth"] = "o"; st["tilt"] = -14; st["lean"] = -10
    st["amp"] = amp("G", t)
    st["blink"] = (t % 3.9) < 0.12
    return st

def girl_state(t):
    st = dict(handL=(-30, 180), handR=(40, 150), rise=1.0, look=(-1.0, 0.1), brows=(6, 6), mouth="smile", tilt=6, phone=False)
    if t < 1.2:
        st["walk"] = t * 9
    if S(0) <= t < E(1):
        st["eyes"] = "happy" if amp("H", t) < 0.06 else "n"; st["mouth"] = "grin"; st["tilt"] = 10
    if E(1) <= t < S(3):
        st["mouth"] = "flat"; st["brows"] = (2, 2); st["tilt"] = 0
    if S(3) <= t < S(8):
        st["brows"] = (-10, 10); st["mouth"] = "flat"; st["tilt"] = -4; st["handL"] = (60, 60)
    if S(8) <= t < E(11):
        st["brows"] = (-4, 4); st["mouth"] = "flat"; st["tilt"] = -6; st["handL"] = (60, 60)
    if E(11) <= t < S(12):
        st["brows"] = (-14, -14); st["mouth"] = "flat"; st["eyes"] = "n"; st["blink"] = False
    if S(12) <= t < T_JERSEY:
        st["brows"] = (-12, -12); st["mouth"] = "flat"; st["tilt"] = -8
    if T_JERSEY <= t:
        st["handR"] = (-60, -150); st["handL"] = (-150, -120); st["eyes"] = "happy"; st["mouth"] = "grin"; st["tilt"] = 10; st["brows"] = (8, 8)
    if S(14) <= t:
        st["eyes"] = "n"; st["mouth"] = "flat"; st["brows"] = (-10, -10); st["tilt"] = 0
    if T_HIT <= t:
        sw = ss(T_HIT, T_HIT + 0.3, t)
        st["handR"] = lerp2((-60, -150), (-230, -40), sw); st["handL"] = (-30, 180); st["mouth"] = "grin" if t > T_HIT + 0.6 else "flat"
    st["amp"] = amp("H", t)
    st.setdefault("blink", (t % 4.3) < 0.12)
    return st

def camera(t):
    girl_cu = (1.75, HX - 30, 1010)
    guy_cu = (1.8, GX + 30, 1010)
    shots = [
        (0, S(0), (1.0, 560, 1130)),
        (S(0), E(0) + 0.2, girl_cu), (S(1), E(1) + 0.3, guy_cu), (S(2), S(2) + 0.6, girl_cu),
        (S(2) + 0.6, S(3), (1.95, GX + 30, 900)), (S(3), E(3), guy_cu), (S(4), E(4), girl_cu),
        (S(5), E(5) + 0.2, guy_cu), (S(6), E(6), girl_cu), (S(7), E(7) + 0.3, guy_cu),
        (S(8), E(8), (1.5, HX - 60, 1040)), (S(9), E(9) + 0.1, (2.0, GX + 30, 990)), (S(10), E(10) + 0.1, girl_cu),
        (S(11), E(11), (2.0, GX + 30, 990)), (E(11), S(12), (2.0, HX - 30, 990)), (S(12), T_JERSEY, girl_cu),
        (T_JERSEY, S(14), (1.2, 590, 1070)), (S(14), T_HIT, (2.0, GX + 30, 990)),
    ]
    for a, b, c in shots:
        if a <= t < b:
            return c
    return (1.15, 560, 1100)

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
        if a <= t < b + 0.12:
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

TOP = ["He forgot your anniversary but remembers", "every footballer's birthday"]

def draw_top(cv, t):
    f = skia.Font(TF_B, 40)
    w = max(f.measureText(s) for s in TOP) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 284), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    for i, s in enumerate(TOP):
        text(cv, s, 540, 206 + i * 56, 40, C("111111"), tf=TF_B)
    te = T_HIT + 1.0
    if t > te:
        a, k = pop(t, te, 0.45)
        chip(cv, 540, 400, "TAG A FOOTBALL BOYFRIEND", a=a, scale=k, col="ffd23f", fg="1a1a1a", size=50)

def render_frame(cv, t):
    z, wx, wy = camera(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-wx, -wy)
    CO.draw_room(cv, t)
    CO.draw_couch_back(cv)
    CO.draw_couch_front(cv)
    gs = guy_state(t)
    M.draw_person(cv, t, gs, GX, "guy")
    scarf(cv, t, GX, gs.get("bob", 0))
    soul(cv, t, S(2) + 0.6)
    tears(cv, t, S(14) - 0.2)
    gx = girl_x(t)
    M.draw_person(cv, t, girl_state(t), gx, "girl")
    hip_g = M.SEAT - 18 - 200
    if t < T_JERSEY:
        gift_bag(cv, gx + 84 + 40, hip_g - 224 + 150 + 70, 0.9)
    else:
        q = ease_out_back((t - T_JERSEY) / 0.35, 1.8)
        if t < T_HIT:
            jersey(cv, gx - 40, 860, 1.0 * q)
            gift_bag(cv, gx + 160, 1560, 0.8)
        else:
            sw = ss(T_HIT, T_HIT + 0.3, t)
            jersey(cv, lerp(gx - 40, GX + 140, sw), lerp(860, 900, sw), 0.9, -60 * sw)
            gift_bag(cv, gx + 160, 1560, 0.8)
    thwack(cv, t)
    # TV glow flicker
    fl = 0.06 + 0.04 * math.sin(t * 11) * math.sin(t * 4.3)
    cv.drawRect(skia.Rect(-200, 900, W + 200, H), P(C("5ab0ff", fl)))
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.3)], [0.6, 1])))
    draw_top(cv, t)
    draw_caption(cv, t)
    fade = 1 - ss(TOTAL - 0.5, TOTAL, t)
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
        print("jersey", T_JERSEY, "hit", T_HIT, "total", TOTAL)
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
