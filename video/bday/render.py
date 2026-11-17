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

CARD0, CARD1 = E(5) + 1.6, S(6) - 0.4
PART2 = CARD1

# ------------------------------------------------------------------ gift items
def boxers(cv, x, y, s=1.0):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    p = poly([(-70, -50), (70, -50), (80, 50), (10, 50), (0, 10), (-10, 50), (-80, 50)])
    cv.drawPath(p, P(C("e74c3c"))); cv.drawPath(p, P(INK, stroke=5))
    cv.drawRect(skia.Rect(-70, -56, 70, -38), P(C("ffffff"))); cv.drawRect(skia.Rect(-70, -56, 70, -38), P(INK, stroke=4))
    for (hx, hy) in ((-40, -10), (30, 0), (-50, 30), (50, 30)):
        M.heart(cv, hx, hy, 0.35, "ffffff")
    cv.restore()

def singlet(cv, x, y, s=1.0):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    p = skia.Path(); p.moveTo(-55, -70); p.lineTo(-30, -70); p.quadTo(0, -30, 30, -70); p.lineTo(55, -70)
    p.quadTo(50, -20, 65, 10); p.lineTo(60, 80); p.lineTo(-60, 80); p.lineTo(-65, 10); p.quadTo(-50, -20, -55, -70); p.close()
    cv.drawPath(p, P(C("ffffff"))); cv.drawPath(p, P(INK, stroke=5))
    cv.restore()

def belt(cv, x, y, s=1.0):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-90, -14, 90, 14), 6, 6), P(C("7a4a26"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-90, -14, 90, 14), 6, 6), P(INK, stroke=4))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-110, -24, -76, 24), 6, 6), P(C("e2c48a"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-110, -24, -76, 24), 6, 6), P(INK, stroke=4))
    for k in range(4):
        cv.drawCircle(-30 + k * 30, 0, 4, P(INK))
    cv.restore()

def hairties(cv, x, y, s=1.0):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    for k, c in enumerate(("ff6b8b", "5ab0ff", "ffd23f")):
        cv.drawCircle(-40 + k * 40, 0, 26, P(C(c), stroke=11)); cv.drawCircle(-40 + k * 40, 0, 26, P(INK, stroke=2))
    cv.restore()

def slippers(cv, x, y, s=1.0):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    for dx in (-36, 36):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(dx - 26, -60, dx + 26, 60), 26, 26), P(C("4a90e2"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(dx - 26, -60, dx + 26, 60), 26, 26), P(INK, stroke=4))
        cv.drawArc(skia.Rect(dx - 26, -40, dx + 26, 0), 180, 180, False, P(C("ffffff"), stroke=10))
    cv.restore()

def toothbrush(cv, x, y, s=1.0):
    cv.save(); cv.translate(x, y); cv.scale(s, s); cv.rotate(-30)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-80, -9, 70, 9), 8, 8), P(C("5ad17a"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-80, -9, 70, 9), 8, 8), P(INK, stroke=4))
    cv.drawRect(skia.Rect(40, -30, 70, -9), P(C("ffffff"))); cv.drawRect(skia.Rect(40, -30, 70, -9), P(INK, stroke=3))
    cv.restore()

ITEMS = [[boxers, singlet, belt], [hairties, slippers, toothbrush]]

def item_times(part):
    base = E(0) if part == 0 else E(6)
    return [base + 0.4 + k * 1.0 for k in range(3)]

def explain_index(part, t):
    ids = (2, 3, 4) if part == 0 else (8, 9, 10)
    idx = None
    for k, i in enumerate(ids):
        if S(i) <= t < (S(i + 1) if k < 2 else E(i + 1)):
            idx = k
    return idx

# ------------------------------------------------------------------ set
def draw_room(cv, t, part):
    cv.drawRect(skia.Rect(0, 0, W, 1420), P(C("f6e6d4")))
    for i in range(10):
        cv.drawRect(skia.Rect(i * 120 + 40, 0, i * 120 + 50, 1420), P(C("efdcc6")))
    # bunting
    cols = ["e74c3c", "f1c40f", "3b82c4", "27ae60", "e67e22", "9b59b6"]
    pts = [(x, 330 + 60 * math.sin(math.pi * x / W)) for x in range(0, W + 1, 90)]
    pth = skia.Path(); pth.moveTo(*pts[0])
    for p_ in pts[1:]:
        pth.lineTo(*p_)
    cv.drawPath(pth, P(INK, stroke=4))
    for k, (x, y) in enumerate(pts[:-1]):
        cv.drawPath(poly([(x + 8, y + 4), (x + 82, y + 4), (x + 45, y + 70)]), P(C(cols[k % 6])))
        cv.drawPath(poly([(x + 8, y + 4), (x + 82, y + 4), (x + 45, y + 70)]), P(INK, stroke=3))
    text(cv, "HAPPY BIRTHDAY!", 540, 560, 74, C("e74c3c"), stroke=10, stroke_col=C("ffffff"))
    # balloons
    bcol = ["4a90e2", "7fb8ff", "2f6fb0"] if part == 0 else ["ff6b8b", "ffb3c7", "e84a7a"]
    for side in (-1, 1):
        cx = 540 + side * 420
        for k in range(3):
            bx, by = cx + (k - 1) * 70, 760 + (k % 2) * 60 + 10 * math.sin(t * 1.5 + k)
            cv.drawLine(bx, by + 70, cx, 1150, P(INK, stroke=3))
            cv.drawOval(skia.Rect(bx - 55, by - 70, bx + 55, by + 70), P(C(bcol[k]))); cv.drawOval(skia.Rect(bx - 55, by - 70, bx + 55, by + 70), P(INK, stroke=5))
            cv.drawOval(skia.Rect(bx - 30, by - 50, bx - 12, by - 20), P(C("ffffff", 0.6)))
    # table with cake
    cv.drawRect(skia.Rect(360, 1240, 720, 1268), P(C("d18b4f"))); cv.drawRect(skia.Rect(360, 1240, 720, 1268), P(INK, stroke=5))
    for x in (380, 700):
        cv.drawRect(skia.Rect(x - 8, 1268, x + 8, 1420), P(C("8a5a2e")))
    cv.drawRect(skia.Rect(470, 1150, 610, 1240), P(C("ffb3c7" if part else "bfe0ff"))); cv.drawRect(skia.Rect(470, 1150, 610, 1240), P(INK, stroke=5))
    cv.drawRect(skia.Rect(470, 1150, 610, 1175), P(C("ffffff")))
    for k in range(3):
        cx = 500 + k * 40
        cv.drawRect(skia.Rect(cx - 5, 1110, cx + 5, 1150), P(C("ffd23f"))); cv.drawRect(skia.Rect(cx - 5, 1110, cx + 5, 1150), P(INK, stroke=2))
        fl = 1 + 0.15 * math.sin(t * 14 + k)
        cv.drawOval(skia.Rect(cx - 7, 1110 - 22 * fl, cx + 7, 1108), P(C("ff9a3a")))
    cv.drawRect(skia.Rect(0, 1420, W, H), P(C("c99260")))
    for i in range(8):
        cv.drawLine(0, 1460 + i * 64, W, 1460 + i * 64, P(C("b07c4c"), stroke=4))
    cv.drawOval(skia.Rect(80, 1640, 1000, 1900), P(C("e8d5b0"))); cv.drawOval(skia.Rect(80, 1640, 1000, 1900), P(INK, stroke=6))

def table_items(cv, t, part):
    times = item_times(part)
    hi = explain_index(part, t)
    for k, f in enumerate(ITEMS[part]):
        if t > times[k] + 0.9:
            bounce = 1.0 + (0.35 * abs(math.sin((t - S((2, 3, 4)[k] if part == 0 else (8, 9, 10)[k])) * 6)) if hi == k else 0)
            f(cv, 410 + k * 130, 1230 - 6, 0.55 * bounce)

def gift_bag(cv, x, y):
    p = poly([(-70, -100), (70, -100), (85, 60), (-85, 60)])
    cv.drawPath(p, P(C("9b59b6"))); cv.drawPath(p, P(INK, stroke=6))
    cv.drawArc(skia.Rect(-40, -150, 40, -60), 180, 180, False, P(INK, stroke=6))
    M.heart(cv, x - x, 0, 0.9, "ffd23f") if False else None
    cv.save(); cv.translate(x, y); cv.restore()

# ------------------------------------------------------------------ acting
GX, HX = 300.0, 790.0
REL_UP = (60, -130)

def hand_world(cx, kind, rel, rise=1.0):
    hip_y = M.SEAT - 18 - 200 * rise
    shx = cx + (84 if kind == "girl" else 94)
    return shx + rel[0], hip_y - 224 + rel[1]

def guy_state(t):
    part = 0 if t < PART2 else 1
    st = dict(handL=(-20, 180), handR=(20, 180), rise=1.0, look=(1.0, 0.0), brows=(0, 0), mouth="smile", grass="mouth", tilt=0)
    if part == 0:
        times = item_times(0)
        if S(0) <= t < times[0]:
            st["mouth"] = "grin"; st["eyes"] = "happy"
        for k, tk in enumerate(times):
            if tk <= t < tk + 0.9:
                st["handR"] = REL_UP; st["look"] = (0.6, -0.8); st["mouth"] = "flat"; st["eyes"] = "n"; st["brows"] = (2, 2)
        if times[2] + 0.9 <= t < S(1):
            st["mouth"] = "flat"; st["look"] = (0.0, 0.0)
        if S(1) <= t < S(2):
            st["handR"] = (140, -40); st["brows"] = (8, 14); st["mouth"] = "flat"; st["tilt"] = 6
        if S(2) <= t:
            st["mouth"] = "flat"; st["brows"] = (6, 6)
        if E(5) <= t:
            st["eyes"] = "wide"; st["brows"] = (16, 16); st["mouth"] = "o" if (t - E(5)) % 1.2 < 0.6 else "flat"
            st["blink"] = (t * 7) % 1 < 0.3
    else:
        times = item_times(1)
        st["mouth"] = "grin"; st["brows"] = (6, 6)
        if t < S(6):
            st["handR"] = (60, -60)
        if times[0] - 0.2 <= t < S(8):
            st["mouth"] = "smirk"; st["brows"] = (0, 14)
        if S(8) <= t < E(11):
            st["mouth"] = "smirk"; st["brows"] = (2, 12); st["handR"] = (120 + 20 * math.sin(t * 4), -40)
        if E(11) <= t < S(13):
            st["mouth"] = "smirk"; st["handR"] = (20, 180)
        if S(13) <= t:
            st["look"] = (0.0, 0.0); st["mouth"] = "flat"; st["brows"] = (0, 0)
    st["amp"] = amp("G", t)
    st.setdefault("blink", (t % 3.9) < 0.12)
    return st

def girl_state(t):
    part = 0 if t < PART2 else 1
    st = dict(handL=(-30, 180), handR=(-60, 60), rise=1.0, look=(-1.0, 0.0), brows=(6, 6), mouth="smile", tilt=6, phone=False)
    if part == 0:
        if t < E(0) + 0.3:
            st["handR"] = (-120, -40); st["eyes"] = "happy"; st["mouth"] = "grin"
        if S(2) <= t < E(5):
            st["handR"] = (-90 + 20 * math.sin(t * 3), -60); st["mouth"] = "smile"; st["brows"] = (4, 8); st["tilt"] = 4
        if S(5) <= t < E(5) + 2.2:
            st["eyes"] = "n"; st["mouth"] = "smirk" if amp("H", t) < 0.06 else "smile"; st["brows"] = (-2, 16); st["tilt"] = 10
    else:
        times = item_times(1)
        if t < times[0]:
            st["eyes"] = "happy"; st["mouth"] = "grin"
        for k, tk in enumerate(times):
            if tk <= t < tk + 0.9:
                st["handR"] = REL_UP; st["look"] = (0.6, -0.8); st["mouth"] = "flat"; st["eyes"] = "n"
        if times[2] + 0.9 <= t:
            st["mouth"] = "flat"; st["brows"] = (-6, 10); st["tilt"] = -4
        if S(7) <= t < E(7) + 0.3:
            st["handR"] = (-140, -40); st["brows"] = (10, 14)
        if S(8) <= t < E(11):
            st["mouth"] = "flat"; st["brows"] = (-10, -10); st["handR"] = (-40, 170); st["handL"] = (60, 60)
        if E(11) <= t:
            st["eyes"] = "wide"; st["mouth"] = "o"; st["brows"] = (20, 20); st["handR"] = (-60, -130); st["handL"] = (60, -130)
        if S(13) <= t:
            st["mouth"] = "o"
    st["amp"] = amp("H", t)
    st["blink"] = (t % 4.3) < 0.12
    return st

def camera(t):
    def wide():
        return (1.0, 560, 1130)
    if t < E(0) + 0.3 or (PART2 <= t < E(6) + 0.3):
        return wide()
    if t < S(1):
        return (1.6, GX + 60, 1000)          # him pulling out items
    if t < S(2):
        return (1.8, GX + 20, 1010)
    if t < S(5):
        return (1.55, HX - 40, 1020)
    if t < E(5):
        return (1.85, HX - 30, 1000)         # the belt line, close
    if t < CARD0:
        return (1.95, GX + 20, 990)          # his speechless twitch
    if t < S(7):
        return (1.6, HX - 60, 1000)          # her pulling out items
    if t < S(8):
        return (1.8, HX - 30, 1010)
    if t < S(11):
        return (1.55, GX + 40, 1020)
    if t < E(11):
        return (1.85, GX + 30, 1000)         # toothbrush line, close
    if t < S(13):
        return (1.95, HX - 30, 990)          # EXCUSE ME
    k = ss(S(13), S(13) + 0.4, t)
    return (lerp(1.95, 2.1, k), lerp(HX - 30, GX + 20, k), 990)  # "same energy" to camera

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
        if a <= t < b + 0.1:
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

TOP = ["Why girls ALWAYS buy boxers, singlet", "and belt for his birthday"]

def draw_top(cv, t):
    f = skia.Font(TF_B, 42)
    w = max(f.measureText(s) for s in TOP) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 286), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    for i, s in enumerate(TOP):
        text(cv, s, 540, 208 + i * 56, 42, C("111111"), tf=TF_B)
    te = E(13) + 0.6
    if t > te:
        a, k = pop(t, te, 0.45)
        chip(cv, 540, 400, "WHO WON?", a=a, scale=k, col="ffd23f", fg="1a1a1a", size=62)

def render_frame(cv, t):
    part = 0 if t < PART2 else 1
    z, wx, wy = camera(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-wx, -wy)
    draw_room(cv, t, part)
    table_items(cv, t, part)
    gs, hs = guy_state(t), girl_state(t)
    M.draw_person(cv, t, gs, GX, "guy")
    M.draw_person(cv, t, hs, HX, "girl")
    # the item currently being pulled out of the bag
    times = item_times(part)
    for k, tk in enumerate(times):
        if tk <= t < tk + 0.9:
            q = ease_out_back((t - tk) / 0.25, 1.8)
            cx, kind = (GX, "guy") if part == 0 else (HX, "girl")
            hx, hy = hand_world(cx, kind, REL_UP)
            ITEMS[part][k](cv, hx, hy - 40, 1.0 * q)
    # gift bag at the receiver's feet / in the giver's hand
    if (part == 0 and t < E(0) + 0.4) or (part == 1 and t < E(6) + 0.4):
        cx, kind = (HX, "girl") if part == 0 else (GX, "guy")
        hx, hy = hand_world(cx, kind, (-120, -40) if part == 0 else (60, -60))
        cv.save(); cv.translate(hx + (-40 if part == 0 else 40), hy + 90)
        p = poly([(-70, -100), (70, -100), (85, 60), (-85, 60)])
        cv.drawPath(p, P(C("9b59b6"))); cv.drawPath(p, P(INK, stroke=6))
        cv.drawArc(skia.Rect(-40, -150, 40, -60), 180, 180, False, P(INK, stroke=6))
        M.heart(cv, 0, -20, 0.9, "ffd23f")
        cv.restore()
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.3)], [0.6, 1])))
    draw_top(cv, t)
    if CARD0 <= t < CARD1:
        a = min(1, (t - CARD0) / 0.15, (CARD1 - t) / 0.15)
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("000000", a)))
        text(cv, "6 MONTHS LATER…", 540, 930, 80, C("ffffff", a), tf=TF_BLACK)
        text(cv, "HER BIRTHDAY", 540, 1040, 90, C("ff6b8b", a), tf=TF_BLACK)
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
        print("card", CARD0, CARD1, "total", TOTAL)
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
