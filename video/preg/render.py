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
GX, HDOOR, HNEAR = 330.0, 910.0, 700.0
BRAIN = (E(4) + 0.3, S(5) - 0.2)
END = E(8) + 0.2
BLACK = TOTAL - 0.25
ANGRY = ()

def girl_x(t):
    return lerp(HDOOR, HNEAR, ss(S(2), E(2), t))

REST_L, REST_R = (-30, 175), (30, 175)
HIPS_L, HIPS_R = (-18, 168), (18, 168)
CLASP_L, CLASP_R = (60, 60), (-60, 60)

def guy_state(t):
    st = dict(handL=(-60, -200), handR=(60, -200), look=(0.3, -0.2), brows=(4, 4), mouth="smirk", grass="mouth", tilt=-6, rise=0.0, lean=-6)
    st["blink"] = (t % 3.7) < 0.12
    if S(1) <= t < E(1): st.update(eyes="happy" if amp("G", t) < 0.05 else "n", look=(1.0, -0.2))
    if S(2) <= t: st.update(handL=REST_L, handR=REST_R, look=(1.0, -0.2), lean=0, tilt=0)
    if S(3) <= t: st.update(brows=(12, 12), mouth="flat")
    if E(4) <= t < S(5):     # processing... last brain cell leaves
        st.update(eyes="wide", brows=(22, 22), mouth="o", grass=None, look=(0.0, 0.0))
        q = (t - E(4) - 0.15) / 0.8
        if 0 < q < 1: st["grass_fall"] = q
    if S(5) <= t:
        st.update(grass=None, eyes="n", brows=(16, 16), mouth="flat", tilt=8, look=(1.0, -0.2))
    if S(6) <= t: st.update(brows=(14, 14), tilt=-6)
    if S(7) <= t: st.update(mouth="smile", brows=(18, 18), handR=(-60, 60), tilt=8)          # hopeful, touches belly
    if S(8) <= t: st.update(eyes="happy", mouth="smile", handL=(60, 70), handR=(-60, 70), brows=(20, 20), tilt=10)
    if END <= t: st.update(look=(0.0, 0.0), eyes="n", mouth="smile", handL=(70, 80), handR=(-70, 80))   # proud
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=HIPS_L, handR=HIPS_R, look=(-1.0, 0.0), brows=(10, 10), mouth="smile", tilt=-4, rise=1.0)
    st["blink"] = (t % 4.1) < 0.12
    if S(0) <= t < E(0): st.update(handR=(-150, -120 + 20 * math.sin(t * 7)))
    if S(2) <= t < E(2): st["walk"] = t * 8
    if S(2) <= t: st.update(brows=(-6, -6), mouth="flat")
    if S(4) <= t < E(4) + 0.5: st.update(handL=(60, 70), handR=(-60, 70), brows=(14, 14), mouth="smile", tilt=8)   # hands on belly
    if E(4) + 0.5 <= t: st.update(brows=(4, 4), mouth="flat", tilt=0, handL=(60, 70), handR=(-60, 70))
    if S(5) <= t: st.update(brows=(-10, 14), mouth="flat", handL=HIPS_L, handR=HIPS_R)
    if S(6) <= t: st.update(brows=(-14, -14), tilt=-6)
    if E(7) <= t: st.update(eyes="n", brows=(0, 0), mouth="flat", tilt=0, look=(-1.0, 0.0))
    if S(8) <= t: st.update(eyes="closed" if (t - S(8)) % 2 < 1.3 else "n", brows=(-4, -4))
    if END <= t: st.update(eyes="n", look=(0.0, 0.0), brows=(-6, -6), handR=(-40, -175), tilt=-8)   # facepalm, deadpan at camera
    st["amp"] = amp("H", t)
    return st

def draw_garden(cv, t):
    cv.drawRect(skia.Rect(-200, -600, W + 200, 1100), P(0, shader=lin(0, -600, 0, 1100, [C("3b2a6b"), C("e0708a"), C("ffc178")], [0, 0.55, 1])))
    cv.drawCircle(300, 820, 90, P(C("ffe9a8"))); cv.drawCircle(300, 820, 160, P(C("ffe9a8", 0.25), blur=40))
    # bushes
    for i in range(10):
        x = -60 + i * 120; r = 110 + 30 * math.sin(i * 1.7)
        cv.drawCircle(x, 1080, r, P(C("3f8f4a"))); cv.drawCircle(x, 1080, r, P(INK, stroke=6))
    cv.drawRect(skia.Rect(-200, 1080, W + 200, H + 200), P(C("5aa84f")))
    for i in range(30):
        x = (i * 97) % 1100; y = 1200 + (i * 53) % 600
        cv.drawLine(x, y, x - 6, y - 22, P(C("4a9643"), stroke=5)); cv.drawLine(x, y, x + 8, y - 20, P(C("4a9643"), stroke=5))
    # house wall + door (right)
    cv.drawRect(skia.Rect(760, 300, W + 200, 1420), P(C("f1e2c6"))); cv.drawRect(skia.Rect(760, 300, W + 200, 1420), P(INK, stroke=7))
    for y in range(340, 1420, 60):
        cv.drawLine(760, y, W + 200, y, P(C("e2cfab"), stroke=4))
    cv.drawRect(skia.Rect(830, 700, 1000, 1420), P(C("ffcf7a"))); cv.drawRect(skia.Rect(830, 700, 1000, 1420), P(INK, stroke=7))
    cv.drawRect(skia.Rect(750, 1420, W + 200, 1470), P(C("c9a26a"))); cv.drawRect(skia.Rect(750, 1420, W + 200, 1470), P(INK, stroke=6))
    cv.drawCircle(915, 640, 30, P(C("fff3b0"))); cv.drawCircle(915, 640, 70, P(C("fff3b0", 0.3), blur=30))
    # bench
    wood, dk = C("b9773f"), C("8a5426")
    for y in (1090, 1170, 1250):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(110, y, 560, y + 50), 12, 12), P(wood)); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(110, y, 560, y + 50), 12, 12), P(INK, stroke=6))
    cv.drawRect(skia.Rect(100, 1340, 570, 1400), P(dk)); cv.drawRect(skia.Rect(100, 1340, 570, 1400), P(INK, stroke=6))
    for x in (130, 520):
        cv.drawRect(skia.Rect(x, 1400, x + 24, 1600), P(dk)); cv.drawRect(skia.Rect(x, 1400, x + 24, 1600), P(INK, stroke=5))

def draw_brain(cv, t, gx):
    if not (BRAIN[0] <= t < BRAIN[1] + 0.1):
        return
    q = (t - BRAIN[0]) / (BRAIN[1] - BRAIN[0])
    hy = M.SEAT - 18 - 366
    if q < 0.2:
        x, y, s = gx, hy - 60 - 300 * q, q / 0.2
    else:
        k = (q - 0.2) / 0.8
        x, y, s = gx + 900 * k, hy - 120 - 40 * math.sin(k * 12), 1
    cv.save(); cv.translate(x, y); cv.scale(0.9 * s, 0.9 * s)
    for dx in (-14, 14):     # tiny walking legs
        sw = 10 * math.sin(t * 25 + (0 if dx < 0 else math.pi))
        cv.drawLine(dx, 30, dx + sw, 64, P(INK, stroke=6))
    br = skia.Path(); br.addOval(skia.Rect(-46, -34, 46, 36))
    cv.drawPath(br, P(C("ff9ec4"))); cv.drawPath(br, P(INK, stroke=6))
    cv.drawLine(0, -32, 0, 34, P(C("d9608f"), stroke=4))
    for (a, b, c, d) in ((-34, -8, -14, -18), (-30, 14, -10, 8), (12, -20, 34, -4), (10, 10, 32, 18)):
        cv.drawLine(a, b, c, d, P(C("d9608f"), stroke=4))
    cv.drawLine(40, -4, 64, -30 + 10 * math.sin(t * 20), P(INK, stroke=5))     # waving bye
    cv.restore()
    if q > 0.25:
        chip(cv, x, y - 90, "BYE", a=min(1, (q - 0.25) * 5), col="ffffff", fg="141414", size=34)

def G_CU(t, z=1.85):
    return (z, GX + 30, 990)
def H_CU(t, z=1.85):
    return (z, girl_x(t) - 10, 805)
WIDE = (1.0, 560, 1130)
TWO = (1.25, 520, 1040)

def camera(t):
    if t < S(1): return WIDE
    if BRAIN[0] - 0.3 <= t < S(5):
        k = (t - E(4)) / (S(5) - E(4)); return (lerp(1.5, 1.6, k), GX + 250, 960)
    if t >= END:
        k = ss(END, END + 0.5, t); return (lerp(1.25, 1.15, k), 520, 1060)
    shots = [(1, G_CU), (2, TWO), (3, G_CU), (4, H_CU), (5, lambda t: G_CU(t, 2.0)), (6, lambda t: H_CU(t, 2.0)),
             (7, lambda t: G_CU(t, 2.1)), (8, lambda t: H_CU(t, 2.2))]
    cur = None
    for i, c in shots:
        if S(i) <= t: cur = (i, c)
    i, c = cur
    c = c(t) if callable(c) else c
    nx = [S(j) for j, _ in shots if S(j) > S(i)]
    b = nx[0] if nx else END
    q = (t - S(i)) / max(0.1, b - S(i))
    return (c[0] * (1 + 0.06 * q), c[1], c[2])

HL = {0: {"INSIDE.": "y", "SOMETHING.": "b"}, 1: {"OUTSIDE.": "y", "BREEZE": "y"}, 2: {"NEED": "y", "INSIDE": "b"},
      3: {"HAPPENED?": "y"}, 4: {"FATHER.": "b"}, 5: {"I": "y", "PREGNANT?": "b"}, 6: {"I'M": "b", "PREGNANT.": "y"},
      7: {"PREGNANT": "y", "TOO?": "b"}, 8: {"WE'RE": "b", "PREGNANT.": "b"}}
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





TOP = ["When his last brain cell leaves the room…", "\"AM I PREGNANT TOO?\""]

def draw_top(cv, t):
    f = skia.Font(TF_B, 44)
    w = max(f.measureText(TOP[0]), skia.Font(TF_BLACK, 48).measureText(TOP[1])) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 286), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    text(cv, TOP[0], 540, 208, 44, C("111111"), tf=TF_B)
    text(cv, TOP[1], 540, 264, 48, C("e74c3c"), tf=TF_BLACK)
    if t > END + 0.2:
        a, k = pop(t, END + 0.2, 0.45)
        chip(cv, 540, 420, "BRAIN CELLS: 0", a=a, scale=k, col="ff9ec4", fg="1a1a1a", size=62)

def render_frame(cv, t):
    z, wx, wy = camera(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-wx, -wy)
    draw_garden(cv, t)
    M.draw_person(cv, t, guy_state(t), GX, "guy")
    M.draw_person(cv, t, girl_state(t), girl_x(t), "girl")
    draw_brain(cv, t, GX)
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.3)], [0.6, 1])))
    draw_top(cv, t)
    tag(cv, t, BRAIN[0] + 0.1, BRAIN[1], "LOADING…", 1250, col="ffffff", size=56)
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
