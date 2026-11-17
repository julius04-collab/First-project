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

T_LATER = E(9) + 1.25          # "LATER…" card
T_NIGHT = T_LATER + 1.1

# ------------------------------------------------------------------ home office
def draw_room(cv, t, night):
    wall = "e9dcc8" if not night else "3a3f63"
    cv.drawRect(skia.Rect(0, 0, W, 1420), P(C(wall)))
    for i in range(9):
        cv.drawRect(skia.Rect(i * 130 + 60, 0, i * 130 + 70, 1420), P(C("ddcdb5" if not night else "33385a")))
    # window
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(70, 260, 420, 740), 10, 10), P(C("fff6ea" if not night else "5a5f85")))
    sky = [C("9fd8ff"), C("dff4ff")] if not night else [C("0e1838"), C("27305a")]
    cv.drawRect(skia.Rect(88, 278, 402, 722), P(0, shader=lin(0, 278, 0, 722, sky)))
    if night:
        cv.drawCircle(320, 380, 36, P(C("e9eefc")))
        for (sx, sy) in ((140, 330), (220, 420), (360, 520), (180, 600)):
            cv.drawCircle(sx, sy, 3, P(C("ffffff")))
    else:
        cv.drawCircle(330, 380, 44, P(C("ffe066")))
        cv.drawRect(skia.Rect(88, 600, 402, 722), P(C("9ad17f")))
    cv.drawLine(245, 278, 245, 722, P(C("fff6ea" if not night else "5a5f85"), stroke=12))
    cv.drawLine(88, 500, 402, 500, P(C("fff6ea" if not night else "5a5f85"), stroke=12))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(70, 260, 420, 740), 10, 10), P(INK, stroke=7))
    # bookshelf (right)
    cv.drawRect(skia.Rect(760, 360, 1060, 1420), P(C("b9773f" if not night else "4a3a40")))
    cv.drawRect(skia.Rect(760, 360, 1060, 1420), P(INK, stroke=7))
    for k, y in enumerate((560, 760, 960, 1160)):
        cv.drawRect(skia.Rect(760, y, 1060, y + 18), P(C("8a5a2e" if not night else "35282e"))); cv.drawLine(760, y, 1060, y, P(INK, stroke=5))
        x = 780
        rr = np.random.default_rng(k)
        while x < 1030:
            bw = rr.integers(22, 40); bh = rr.integers(110, 170)
            col = rr.choice(["e74c3c", "3b82c4", "27ae60", "f1c40f", "8e44ad", "e67e22"])
            cv.drawRect(skia.Rect(x, y - bh, x + bw, y), P(C(col) if not night else C(col, 0.5)))
            cv.drawRect(skia.Rect(x, y - bh, x + bw, y), P(INK, stroke=3))
            x += bw + 4
    # wall shelf with the router (behind him)
    cv.drawRect(skia.Rect(470, 820, 720, 842), P(C("8a5a2e"))); cv.drawRect(skia.Rect(470, 820, 720, 842), P(INK, stroke=5))
    router(cv, 595, 820, t, night)
    # frame
    cv.drawRect(skia.Rect(480, 420, 680, 580), P(C("ffffff" if not night else "8a8fb0"))); cv.drawRect(skia.Rect(480, 420, 680, 580), P(INK, stroke=6))
    cv.drawPath(poly([(500, 560), (560, 470), (610, 530), (640, 500), (665, 560)]), P(C("6cc08a" if not night else "3a5a6a")))
    # floor
    cv.drawRect(skia.Rect(0, 1420, W, H), P(C("c99260" if not night else "3a3350")))
    for i in range(8):
        cv.drawLine(0, 1460 + i * 64, W, 1460 + i * 64, P(C("b07c4c" if not night else "302a45"), stroke=4))

def router(cv, x, y, t, night=False, sc=1.0):
    cv.save(); cv.translate(x, y); cv.scale(sc, sc)
    for ax in (-70, 70):
        cv.drawLine(ax, -40, ax + (8 if ax > 0 else -8), -150, P(INK, stroke=12))
        cv.drawLine(ax, -40, ax + (8 if ax > 0 else -8), -150, P(C("2b2b38"), stroke=6))
    box = skia.RRect.MakeRectXY(skia.Rect(-100, -60, 100, 0), 14, 14)
    cv.drawRRect(box, P(C("f4f4f8"))); cv.drawRRect(box, P(INK, stroke=6))
    for k in range(4):
        on = math.sin(t * (6 + k * 3) + k) > -0.2
        cv.drawCircle(-54 + k * 36, -26, 9, P(C("5ad17a" if on else "1f5a2f")))
        if on:
            cv.drawCircle(-54 + k * 36, -26, 16, P(C("5ad17a", 0.35), blur=6))
    cv.restore()

def draw_desk(cv, t, night):
    cv.drawOval(skia.Rect(80, 1590, 760, 1650), P(C("000000", 0.25), blur=12))
    cv.drawRect(skia.Rect(100, 1330, 740, 1360), P(C("d18b4f" if not night else "6a4a40"))); cv.drawRect(skia.Rect(100, 1330, 740, 1360), P(INK, stroke=6))
    cv.drawRect(skia.Rect(120, 1360, 720, 1600), P(C("b9773f" if not night else "54393a"))); cv.drawRect(skia.Rect(120, 1360, 720, 1600), P(INK, stroke=6))
    for y in (1420, 1500):
        cv.drawLine(480, y, 720, y, P(INK, stroke=5)); cv.drawCircle(600, y + 38, 8, P(INK))
    cv.drawLine(480, 1360, 480, 1600, P(INK, stroke=5))
    # laptop (back facing us), to the side so we still see him
    cv.drawPath(poly([(470, 1330), (690, 1330), (680, 1180), (480, 1180)]), P(C("c9ced6"))); cv.drawPath(poly([(470, 1330), (690, 1330), (680, 1180), (480, 1180)]), P(INK, stroke=6))
    cv.drawCircle(580, 1255, 18, P(C("ffffff", 0.8)))
    if night:
        cv.drawPath(poly([(480, 1180), (300, 900), (860, 900), (680, 1180)]), P(C("8fd3ff", 0.10)))
    # mug
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(160, 1270, 220, 1330), 8, 8), P(C("e74c3c"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(160, 1270, 220, 1330), 8, 8), P(INK, stroke=5))
    # desk lamp at night
    if night:
        cv.drawCircle(150, 1200, 220, P(C("ffe2a0", 0.25), blur=50))

# ------------------------------------------------------------------ acting
GX, GIRL_X0 = 330.0, 860.0
TYPE_L, TYPE_R = (40, 150), (-30, 150)

def guy_state(t):
    st = dict(handL=TYPE_L, handR=TYPE_R, look=(0.3, 0.3), brows=(0, 0), mouth="smirk", grass="mouth", tilt=0, lean=0)
    typing = t < S(0) - 0.2 or (T_NIGHT <= t < S(10))
    st["bob"] = 2 * math.sin(t * 1.4)
    if typing:
        st["handL"] = (40, 150 + 10 * math.sin(t * 20)); st["handR"] = (-30, 150 + 10 * math.sin(t * 23))
    if S(0) <= t < T_LATER:
        st["look"] = (1.0, -0.1)
    if S(1) <= t < E(1) + 0.3 or S(4) <= t < E(4) + 0.3:
        st["mouth"] = "smirk"; st["brows"] = (2, 10)
    if S(5) <= t < S(7):
        st["mouth"] = "flat"; st["brows"] = (0, 0); st["blink"] = (t % 1.6) < 0.25
    if E(6) <= t < E(7) + 0.5:
        take = ss(E(6) + 0.4, E(6) + 0.8, t)
        st["grass"] = "hand" if t > E(6) + 0.6 else "mouth"
        st["handR"] = lerp2(TYPE_R, (-50, -110), take) if t < E(6) + 0.9 else (70, 60)
        st["mouth"] = "flat"; st["brows"] = (4, 4)
    if E(7) + 0.5 <= t < T_LATER:
        put = ss(E(9) + 0.3, E(9) + 0.7, t)
        st["grass"] = "hand" if put < 0.6 else "mouth"
        st["handR"] = (70, 60) if put < 0.05 else lerp2((70, 60), (-50, -110), math.sin(math.pi * put))
        st["mouth"] = "smirk"; st["brows"] = (0, 14)
        st["look"] = (1.0, -0.1) if t < E(9) + 0.8 else (0.0, 0.0)
    if T_NIGHT <= t:
        st["look"] = (0.0, 0.3) if t < S(10) else (0.9, -0.2)
        if S(10) <= t:
            st["handL"] = (40, 150); st["handR"] = (-30, 150); st["brows"] = (6, 6)
        if S(12) <= t:
            st["brows"] = (16, 16); st["mouth"] = "flat"
        if E(13) <= t:
            st["look"] = (0.0, 0.0); st["brows"] = (2, 2); st["mouth"] = "flat"
    st["amp"] = amp("G", t)
    st.setdefault("blink", (t % 3.9) < 0.12)
    return st

def girl_state(t):
    st = dict(handL=(-30, 180), handR=(60, -110), rise=1.0, look=(-1.0, 0.1), brows=(4, 4), mouth="smile", tilt=4, lean=0, phone=True)
    if t < 1.2:
        st["walk"] = t * 9
    if S(2) <= t < S(3):
        st["phone"] = False; st["handR"] = (-40, 170); st["handL"] = (60, 60); st["brows"] = (-10, -10); st["mouth"] = "flat"; st["tilt"] = -8
    if S(3) <= t < S(5):
        st["phone"] = False; st["handR"] = (-60, 60); st["handL"] = (60, 60); st["eyes"] = "happy"; st["mouth"] = "grin"; st["tilt"] = 12; st["brows"] = (10, 10)
        if S(4) <= t:
            st["eyes"] = "n"; st["mouth"] = "flat"; st["brows"] = (-6, -6); st["tilt"] = 0
    if S(5) <= t < E(6) + 0.2:
        st["phone"] = False; st["brows"] = (-16, -16); st["tilt"] = 0
        w = math.sin(t * 9)
        st["handR"] = (150 + 30 * w, -130 - 20 * w); st["handL"] = (-150 - 30 * w, -130 + 20 * w)
        st["lean"] = 4 * math.sin(t * 6)
    if E(6) + 0.2 <= t < S(8):
        st["phone"] = True; st["handR"] = (60, -110); st["brows"] = (-12, -12); st["mouth"] = "flat"; st["look"] = (-1.0, 0.4)
    if S(8) <= t < S(9):
        st["phone"] = True; st["eyes"] = "wide"; st["mouth"] = "o"; st["brows"] = (16, 16)
    if S(9) <= t:
        st["phone"] = True; st["eyes"] = "n"; st["mouth"] = "flat"; st["brows"] = (-6, 10); st["look"] = (1.0, -0.2); st["tilt"] = 10
    if E(9) + 0.2 <= t:
        st["walk"] = (t - E(9)) * 9
    st["amp"] = amp("H", t)
    st["blink"] = (t % 4.3) < 0.12
    return st

def girl_x(t):
    x = lerp(1250, GIRL_X0, ss(0, 1.2, t))
    if t >= E(9) + 0.2:
        x += 700 * ss(E(9) + 0.2, E(9) + 1.4, t)
    return x

def camera(t):
    shake = (0, 0)
    if S(5) <= t < E(6):
        a = 7 if t < S(6) else 10
        shake = (a * math.sin(t * 47), a * math.cos(t * 39))
    if t < S(0):
        c = (1.0, 560, 1130)
    elif t < S(1):
        c = (1.45, 800, 1060)
    elif t < S(2):
        c = (1.8, GX + 20, 1010)
    elif t < S(4):
        c = (1.65, GIRL_X0 - 30, 1020)
    elif t < S(5):
        c = (1.8, GX + 20, 1010)
    elif t < S(6):
        c = (1.75, GIRL_X0 - 30, 1020)
    elif t < E(6):
        k = ss(S(6), E(6), t); c = (lerp(1.3, 1.85, k), lerp(700, GIRL_X0 - 30, k), lerp(1080, 1010, k))
    elif t < E(7) + 0.2:
        c = (1.9, GX + 20, 1000)
    elif t < S(9) + 0.6:
        c = (1.75, GIRL_X0 - 30, 1010)
    elif t < T_NIGHT:
        c = (1.1, 560, 1120)
    elif t < S(13):
        c = (1.4, GX + 120, 1060)
    else:
        k = ss(S(13), E(13) + 0.6, t); c = (lerp(1.4, 2.1, k), lerp(GX + 120, GX + 20, k), lerp(1060, 990, k))
    return c[0], c[1] + shake[0], c[2] + shake[1]

def chunks():
    out = []
    for s in SEGS:
        words = s["text"].split()
        cs, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= 3 or w[-1] in ",.?!…\"":
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
        if a <= t < b + 0.1:
            k = ease_out_back((t - a) / 0.2, 2.0)
            s = txt.upper()
            angry = i in (5, 6)
            f = skia.Font(TF_BLACK, 92 if angry else 80); w = f.measureText(s)
            if w > 980:
                f = skia.Font(TF_BLACK, (92 if angry else 80) * 980 / w); w = f.measureText(s)
            cv.save(); cv.translate(540 + (6 * math.sin(t * 50) if angry else 0), 1745); cv.scale(k, k)
            col = C("ffd23f") if who == "H" else C("ffffff")
            if angry:
                col = C("ff5a4a")
            cv.drawString(s, -w / 2, 28, f, P(C("000000"), stroke=16)); cv.drawString(s, -w / 2, 28, f, P(col))
            cv.restore()
            chip(cv, 540, 1640, "HER" if who == "H" else "HIM", a=0.95, col="ffd23f" if who == "H" else "ffffff", fg="1a1a1a", size=30)
            return

def phone_ui(cv, t, mode, k):
    cv.save(); cv.translate(540, 960); cv.scale(k, k)
    r = skia.RRect.MakeRectXY(skia.Rect(-220, -400, 220, 400), 50, 50)
    cv.drawRRect(r, P(C("000000", 0.4), blur=20)); cv.drawRRect(r, P(C("2b2b38"))); cv.drawRRect(r, P(INK, stroke=8))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-196, -370, 196, 370), 30, 30), P(C("f4f6fb")))
    text(cv, "Wi-Fi", -160, -290, 50, C("111111"), tf=TF_BLACK, align="l")
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-170, -240, 170, -150), 18, 18), P(C("ffffff"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-170, -240, 170, -150), 18, 18), P(C("c9ced6"), stroke=3))
    text(cv, "HOME_WIFI", -140, -182, 36, C("111111"), tf=TF_B, align="l")
    for j in range(3):
        cv.drawArc(skia.Rect(108 - j * 14, -210 - j * 14, 148 + j * 14, -170 + j * 14), 225, 90, False, P(C("3b82c4"), stroke=5))
    text(cv, "Enter password", -160, -80, 36, C("555555"), tf=TF_B, align="l")
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-170, -50, 170, 30), 14, 14), P(C("ffffff"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-170, -50, 170, 30), 14, 14), P(C("3b82c4"), stroke=4))
    if mode == "type":
        word = "asknicely"
        n = int(clamp((t) / 1.1) * len(word))
        text(cv, word[:n] + ("|" if int(t * 4) % 2 == 0 and n < len(word) else ""), -150, 6, 44, C("111111"), tf=TF_B, align="l")
        if t > 1.35:
            q = ease_out_back((t - 1.35) / 0.3, 2.0)
            cv.save(); cv.translate(0, 180); cv.scale(q, q)
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-170, -60, 170, 60), 30, 30), P(C("5ad17a")))
            text(cv, "✓ Connected", 0, 16, 46, C("ffffff"), tf=TF_BLACK)
            cv.restore()
    else:
        if int(t * 2.5) % 2 == 0:
            cv.drawLine(-150, -32, -150, 14, P(C("111111"), stroke=4))
    cv.restore()

TOP = ["When she asks for the Wi-Fi password", "and takes it personally"]

def draw_top(cv, t):
    f = skia.Font(TF_B, 44)
    w = max(f.measureText(s) for s in TOP) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 290), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    for i, s in enumerate(TOP):
        text(cv, s, 540, 210 + i * 58, 44, C("111111"), tf=TF_B)
    te = E(13) + 0.8
    if t > te:
        a, k = pop(t, te, 0.45)
        chip(cv, 540, 400, "WHO WON?", a=a, scale=k, col="ffd23f", fg="1a1a1a", size=62)

def render_frame(cv, t):
    night = t >= T_NIGHT
    z, wx, wy = camera(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-wx, -wy)
    draw_room(cv, t, night)
    M.draw_person(cv, t, guy_state(t), GX, "guy")
    draw_desk(cv, t, night)
    gx = girl_x(t)
    if not night and gx < 1500:
        M.draw_person(cv, t, girl_state(t), gx, "girl")
    cv.restore()
    if S(5) <= t < E(6):
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("ff2a2a", 0.06 + 0.04 * math.sin(t * 12))))
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    draw_top(cv, t)
    if 1.9 <= t < S(1) - 0.1:
        phone_ui(cv, t - 1.9, "wait", ease_out_back((t - 1.9) / 0.3, 1.5))
    if E(7) + 0.2 <= t < S(8) - 0.1:
        tt = t - E(7) - 0.2
        phone_ui(cv, tt, "type", ease_out_back(tt / 0.3, 1.5))
    if T_LATER <= t < T_NIGHT:
        a = min(1, (t - T_LATER) / 0.15, (T_NIGHT - t) / 0.15)
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("000000", a)))
        text(cv, "LATER…", 540, 990, 120, C("ffffff", a), tf=TF_BLACK)
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
        print("later", T_LATER, "night", T_NIGHT, "total", TOTAL)
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
