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
T_LEAVE = E(2) + 0.1
T_TWITCH = T_LEAVE + 1.4
CARD1 = (T_TWITCH + 1.0, T_TWITCH + 2.2)        # 11:47 PM
T_ENTER = CARD1[1]
T_LAMP = S(3) - 0.5
CARD2 = (E(6) + 0.5, S(7) - 0.25)               # NEXT DAY
T_FREEZE = E(8) + 0.2
T_SIT = (E(8) + 1.1, E(8) + 2.6)

def phase(t):
    if t < CARD1[0]:
        return "evening"
    if t < CARD2[0]:
        return "night"
    return "day"

def guy_x(t):
    if t < T_LEAVE:
        return GX
    if t < CARD1[0]:
        return lerp(GX, -400, ss(T_LEAVE, T_LEAVE + 1.3, t))
    if t < CARD2[0]:
        return lerp(-300, GX, ss(T_ENTER, T_ENTER + 1.6, t))
    return GX

def keys(cv, x, y):
    cv.drawCircle(x, y, 16, P(C("c9a227"), stroke=5))
    for k in range(3):
        a = 0.7 + k * 0.45
        cv.drawLine(x + math.cos(a) * 14, y + math.sin(a) * 14, x + math.cos(a) * 48, y + math.sin(a) * 48, P(C("b8bec9"), stroke=9))
        cv.drawLine(x + math.cos(a) * 14, y + math.sin(a) * 14, x + math.cos(a) * 48, y + math.sin(a) * 48, P(INK, stroke=2))

def guy_state(t):
    ph = phase(t)
    st = dict(handL=(-20, 180), handR=(60, -60), rise=1.0, look=(1.0, 0.0), brows=(4, 4), mouth="smile", grass="mouth", tilt=0, keys=True)
    if ph == "evening":
        if S(0) <= t < E(0):
            st["mouth"] = "smile"; st["brows"] = (10, 10)
        if S(2) <= t:
            st["eyes"] = "happy"; st["mouth"] = "grin"
        if t >= T_LEAVE:
            st["walk"] = (t - T_LEAVE) * 10; st["look"] = (-1.0, 0.0)
    elif ph == "night":
        st["keys"] = False; st["handR"] = (60, -130); st["handL"] = (-60, -130)
        if t < T_ENTER + 1.6:
            st["walk"] = (t - T_ENTER) * 6; st["mouth"] = "o"; st["look"] = (1.0, -0.2); st["eyes"] = "n"
        if t >= T_LAMP:
            st["eyes"] = "wide"; st["mouth"] = "o"; st["brows"] = (18, 18); st["handR"] = (40, 160); st["handL"] = (-40, 160); st["sweat"] = True
        if S(4) <= t < E(4) + 0.2:
            st["handR"] = (140, -40); st["mouth"] = "flat"
        if S(6) - 0.3 <= t:
            st["look"] = (0.0, 0.0); st["eyes"] = "n"; st["brows"] = (14, -6); st["mouth"] = "flat"; st["tilt"] = 8; st["sweat"] = False
    else:
        st["mouth"] = "smile"
        if t >= T_FREEZE:
            st["eyes"] = "wide"; st["mouth"] = "flat"; st["brows"] = (20, 20); st["sweat"] = True; st["look"] = (1.0, 0.0)
        if t >= T_SIT[0]:
            k = ss(T_SIT[0], T_SIT[1], t)
            st["rise"] = 1 - k; st["keys"] = k < 0.7; st["handR"] = lerp2((60, -60), (-20, 160), k)
        if S(9) <= t:
            st["look"] = (1.0, 0.0); st["eyes"] = "n"; st["mouth"] = "flat"; st["brows"] = (10, 4); st["tilt"] = -4
    st["amp"] = amp("G", t)
    st.setdefault("blink", (t % 3.9) < 0.12)
    return st

def girl_state(t):
    ph = phase(t)
    st = dict(handL=(60, 60), handR=(-60, 60), look=(-1.0, 0.0), brows=(-6, -6), mouth="flat", tilt=-4)
    if ph == "evening":
        st["look"] = (0.4, 0.2) if t < S(1) else (-0.2, 0.2)
        if S(1) <= t:
            st["eyes"] = "n"; st["brows"] = (-10, -10)
        if T_TWITCH <= t:
            tw = (t * 9) % 1 < 0.45
            st["brows"] = (-14, 6 if tw else -14); st["blink"] = tw; st["look"] = (0, 0)
    elif ph == "night":
        st["brows"] = (-14, -14); st["look"] = (-1.0, 0.0); st["tilt"] = -6
        if S(5) <= t < E(5):
            st["handR"] = (-150, -100 + 15 * math.sin(t * 9)); st["handL"] = (60, 60); st["brows"] = (-18, -18)
    else:
        st["brows"] = (6, 6); st["mouth"] = "smile"; st["tilt"] = 8; st["look"] = (-1.0, 0.0); st["handR"] = (-30, 170)
        if S(8) <= t:
            st["eyes"] = "happy" if amp("H", t) < 0.06 else "n"; st["mouth"] = "smile"
    st["amp"] = amp("H", t)
    st.setdefault("blink", (t % 4.3) < 0.12)
    return st

def camera(t):
    guy_cu, girl_cu = (1.8, GX + 30, 1000), (1.8, HX - 20, 1050)
    shots = [
        (0, S(0), (1.0, 560, 1130)),
        (S(0), E(0) + 0.2, guy_cu), (S(1), E(1) + 0.3, girl_cu), (S(2), T_LEAVE, guy_cu),
        (T_LEAVE, T_TWITCH, (1.0, 560, 1130)), (T_TWITCH, CARD1[0], (2.2, HX - 10, 1010)),
        (CARD1[1], S(3), (1.0, 560, 1130)), (S(3), E(3) + 0.2, girl_cu), (S(4), E(4) + 0.1, guy_cu),
        (S(5), E(5), (1.6, HX - 60, 1060)), (S(6), CARD2[0], (2.0, GX + 30, 990)),
        (CARD2[1], S(8), (1.15, 560, 1110)), (S(8), T_FREEZE, girl_cu),
    ]
    for a, b, c in shots:
        if a <= t < b:
            return c
    if t < T_SIT[0]:
        k = ss(T_FREEZE, T_SIT[0], t)
        return (lerp(1.5, 2.2, k), GX + 30, lerp(1000, 960, k))
    return (lerp(1.6, 1.4, ss(T_SIT[0], T_SIT[1], t)), GX + 60, 1080)

def chunks():
    out = []
    for s in SEGS:
        words = s["text"].split()
        cs, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= 3 or w[-1] in ",.?!…\"—":
                cs.append(cur); cur = []
        if cur:
            cs.append(cur)
        wt = [sum(len(w) + 1 for w in c) for c in cs]; tot = sum(wt); acc = 0
        for c, x in zip(cs, wt):
            out.append((s["start"] + (s["end"] - s["start"]) * acc / tot, s["start"] + (s["end"] - s["start"]) * (acc + x) / tot, " ".join(c), s["who"], s["i"]))
            acc += x
    return out
CAPS = chunks()

def draw_caption(cv, t):
    for (a, b, txt, who, i) in CAPS:
        if a <= t < b + 0.12:
            k = ease_out_back((t - a) / 0.2, 2.0)
            s = txt.upper()
            big = i == 5
            f = skia.Font(TF_BLACK, 88 if big else 80); w = f.measureText(s)
            if w > 980:
                f = skia.Font(TF_BLACK, (88 if big else 80) * 980 / w); w = f.measureText(s)
            cv.save(); cv.translate(540 + (5 * math.sin(t * 50) if big else 0), 1745); cv.scale(k, k)
            col = C("ff5a4a") if big else (C("ffd23f") if who == "H" else C("ffffff"))
            cv.drawString(s, -w / 2, 28, f, P(C("000000"), stroke=16)); cv.drawString(s, -w / 2, 28, f, P(col))
            cv.restore()
            chip(cv, 540, 1640, "HER" if who == "H" else "HIM", a=0.95, col="ffd23f" if who == "H" else "ffffff", fg="1a1a1a", size=30)
            return

TOP = ["When she says \"Do whatever you want\"…", "DON'T"]

def draw_top(cv, t):
    f = skia.Font(TF_B, 44)
    w = max(f.measureText(s) for s in TOP) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 286), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    text(cv, TOP[0], 540, 208, 44, C("111111"), tf=TF_B)
    text(cv, TOP[1], 540, 264, 48, C("e74c3c"), tf=TF_BLACK)
    te = E(9) + 0.5
    if t > te:
        a, k = pop(t, te, 0.45)
        chip(cv, 540, 400, "GUYS, YOU KNOW", a=a, scale=k, col="ffd23f", fg="1a1a1a", size=62)

def card(cv, t, rng, l1, l2, c2):
    a = min(1, (t - rng[0]) / 0.15, (rng[1] - t) / 0.15)
    cv.drawRect(skia.Rect(0, 0, W, H), P(C("000000", a)))
    text(cv, l1, 540, 960, 110, C("ffffff", a), tf=TF_BLACK)
    if l2:
        text(cv, l2, 540, 1060, 60, C(c2, a), tf=TF_B)

def render_frame(cv, t):
    ph = phase(t)
    z, wx, wy = camera(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-wx, -wy)
    CO.draw_room(cv, t); CO.draw_couch_back(cv); CO.draw_couch_front(cv)
    M.draw_person(cv, t, girl_state(t), HX, "girl")
    gs = guy_state(t); gx = guy_x(t)
    if gx > -350:
        M.draw_person(cv, t, gs, gx, "guy")
        if gs.get("keys"):
            hip_y = M.SEAT - 18 - 200 * gs["rise"]
            keys(cv, gx + 94 + gs["handR"][0], hip_y - 224 + gs["handR"][1])
    if ph == "evening":
        cv.drawRect(skia.Rect(-200, -200, W + 200, H + 200), P(C("ff9a3a", 0.06)))
    if ph == "night":
        lamp = ss(T_LAMP, T_LAMP + 0.05, t)
        cv.drawRect(skia.Rect(-200, -200, W + 200, H + 200), P(C("05060f", 0.88 - 0.38 * lamp)))
        if lamp > 0:
            cv.drawCircle(955, 640, 520, P(C("ffcf7a", 0.22 * lamp), blur=90))
        if t < T_LAMP:  # moonlight sliver + his outline barely visible
            cv.drawRect(skia.Rect(-200, -200, W + 200, H + 200), P(C("2a3a7a", 0.10)))
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.3)], [0.6, 1])))
    draw_top(cv, t)
    if CARD1[0] <= t < CARD1[1]:
        card(cv, t, CARD1, "11:47 PM", "that night…", "8fd8ff")
    if CARD2[0] <= t < CARD2[1]:
        card(cv, t, CARD2, "NEXT DAY", None, "ffffff")
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
        print("leave", T_LEAVE, "card1", CARD1, "lamp", T_LAMP, "card2", CARD2, "sit", T_SIT, "total", TOTAL)
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
