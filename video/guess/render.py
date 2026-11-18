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

GX, HX = 330.0, 740.0
T_REW = (E(1) + 0.05, S(2))          # rewind transition
REVEAL = S(17) + 0.62 * (E(17) - S(17))   # "in 2019"
PHONE = (REVEAL - 0.1, E(17) + 1.0)
HOLD = (E(17), S(18))
REST_L, REST_R = (-30, 175), (30, 175)

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.0), brows=(4, 4), mouth="smile", grass="mouth", tilt=0)
    if t < T_REW[0]:                      # hook: flash-forward, cooked
        st.update(eyes="wide", brows=(18, 18), mouth="flat", sweat=True, tilt=-4 + 2 * math.sin(t * 20))
    else:
        if t < S(2) + 1.0:
            st.update(look=(0.2, 0.3), mouth="smile")
        if S(3) <= t:
            st.update(brows=(10, 10), mouth="flat")
        for i in (8, 10, 12):
            if S(i) <= t < E(i) + 0.05:
                st.update(brows=(16, 16), mouth="smile", handR=(130, -50), tilt=6)
        for i, sw in ((9, False), (11, True), (13, True)):
            if E(i) <= t:
                st["sweat"] = sw or st.get("sweat", False)
            if S(i) <= t < S(i + 1):
                st.update(eyes="wide", brows=(18, 18), mouth="o" if i == 13 else "flat")
        if S(14) <= t < S(15):
            st.update(look=(0.3, -0.9), handR=(-70, -60), brows=(14, 2), mouth="flat", tilt=-6)
        if S(15) <= t < S(16):
            st.update(handL=(-150, -10), handR=(150, -10), brows=(16, 16), mouth="flat", tilt=0)
        if S(16) <= t:
            st.update(look=(1.0, 0.0), brows=(12, 12), mouth="flat")
        if REVEAL <= t:
            q = min(1, (t - REVEAL - 0.3) / 0.8)
            st.update(eyes="wide", brows=(22, 22), mouth="o", sweat=True, grass=None, tilt=0)
            if q > 0 and q < 1:
                st["grass_fall"] = q
        if S(18) <= t:
            st.update(eyes="n", brows=(14, -6), mouth="flat", tilt=8, look=(1.0, 0.0))
        if S(19) <= t:
            st.update(look=(0.0, 0.2), brows=(10, 10), tilt=-4)
    st["amp"] = amp("G", t)
    st.setdefault("blink", (t % 3.7) < 0.12 and t < REVEAL)
    return st

CROSS_L, CROSS_R = (60, 60), (-60, 60)
def girl_state(t):
    st = dict(handL=CROSS_L, handR=CROSS_R, look=(-1.0, 0.0), brows=(-14, -14), mouth="flat", tilt=-4)
    if t < T_REW[0]:
        st.update(brows=(-18, -18), tilt=-6)
    else:
        if t < S(2) + 1.0:
            st.update(look=(-0.2, 0.3), brows=(2, 2), mouth="smile", tilt=0)
        elif t < S(6):
            st.update(look=(1.0, 0.1), brows=(-12, -12), tilt=8)     # turned away, silent
        if S(6) <= t < E(6) + 0.1:
            st.update(look=(-1.0, 0.0), handR=(-160, -90 + 12 * math.sin(t * 9)), handL=CROSS_L, brows=(-18, -18))
        if S(7) <= t < S(17):
            st.update(look=(1.0, 0.1), brows=(-12, -12), tilt=8)
        for i in (9, 11):
            if S(i) <= t < S(i + 1):
                st.update(look=(0.4, 0.1), brows=(-16, -16))
        if S(13) <= t < S(14):
            st.update(look=(-1.0, 0.0), brows=(-22, -22), handR=(-170, -60 + 15 * math.sin(t * 14)), tilt=-8)
        if S(16) <= t:
            st.update(look=(-1.0, 0.0), brows=(-16, -16), tilt=-6, mouth="flat")
        if S(17) <= t:
            st.update(handR=(-110, 40), phone=True, brows=(-20, -20))      # holds up the receipts
        if PHONE[1] <= t:
            st.update(phone=False, handR=CROSS_R)
        if S(19) <= t:
            st.update(mouth="smirk", brows=(-10, 4), tilt=-8)
    st["amp"] = amp("H", t)
    st.setdefault("blink", (t % 4.1) < 0.12)
    return st

WIDE = (1.0, 560, 1130)
G_CU, H_CU = (1.85, GX + 30, 990), (1.85, HX - 20, 1040)

def camera(t):
    if t < S(1):
        return (lerp(2.0, 2.25, t / S(1)), GX + 30, 985)
    if t < T_REW[0]:
        return (lerp(2.0, 2.3, (t - S(1)) / (T_REW[0] - S(1))), HX - 20, 1035)
    if t < S(2) + 0.3:
        k = ss(T_REW[0], S(2) + 0.3, t)
        return (lerp(2.3, 1.0, k), lerp(HX - 20, 560, k), lerp(1035, 1130, k))
    shots = [
        (S(2), S(2) + 1.0, WIDE), (S(2) + 1.0, S(3), (1.5, HX - 40, 1060)),
        (S(3), S(4), G_CU), (S(4), S(5), H_CU), (S(5), S(6), (1.15, 560, 1110)),
        (S(6), S(7), H_CU), (S(7), S(8), (1.3, 540, 1080)),
        (S(8), S(9), G_CU), (S(9), S(10), H_CU), (S(10), S(11), G_CU), (S(11), S(12), H_CU),
        (S(12), S(13), G_CU), (S(13), S(14), (2.4, HX - 20, 1010)),
        (S(14), S(15), (2.2, GX + 30, 970)), (S(15), S(16), (1.35, 540, 1080)),
        (S(16), S(17), H_CU), (S(17), REVEAL, (1.9, HX - 20, 1030)),
    ]
    for a, b, c in shots:
        if a <= t < b:
            if b - a > 0.6 and c not in (WIDE,):
                k = (t - a) / (b - a); return (c[0] * (1 + 0.06 * k), c[1], c[2])
            return c
    if t < S(18):
        k = ss(REVEAL, S(18), t); return (lerp(1.7, 2.5, k), GX + 30, lerp(1000, 960, k))
    if t < S(19):
        return (2.2, GX + 30, 975)
    return (lerp(1.15, 1.25, ss(S(19), TOTAL, t)), 540, 1100)

def shake(t):
    for i, amt in ((13, 14), (9, 4), (11, 6)):
        if S(i) <= t < S(i) + 0.35:
            d = 1 - (t - S(i)) / 0.35
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    if t < T_REW[0] and t < S(1):
        return (3 * math.sin(t * 40), 2 * math.cos(t * 33))
    return (0, 0)

# ---------------------------------------------------------------- captions
HL = {0: {"WRONG": "y", "THREE": "b"}, 1: {"ANSWER?": "y", "NOBODY": "b"}, 2: {"SUNDAY.": "y", "SILENT.": "b"},
      3: {"WRONG?": "y"}, 4: {"NOTHING.": "y"}, 5: {"RULE": "y", "NEVER": "b"}, 6: {"LOVED": "y", "KNOW": "b"},
      7: {"GUESSING.": "y"}, 8: {"HUNGRY?": "y"}, 9: {"NO.": "b"}, 10: {"MUM": "y"}, 11: {"NO.": "b"},
      12: {"TOILET": "y"}, 13: {"NO!": "b"}, 14: {"BROTHER": "y", "THINKS…": "y", "OPTIONS.": "b"},
      15: {"GIVE": "y", "UP.": "y"}, 16: {"BOMB.": "b"}, 17: {"PICTURE…": "y", "2019.": "b"},
      18: {"REMEMBER": "b"}, 19: {"EVERYTHING.": "b"}}

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
            cv.save(); cv.translate(540, CAP_Y); cv.scale(k, k)
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
                chip(cv, 540, CAP_Y - 128, "HER" if who == "H" else "HIM", a=0.95, col="ffd23f" if who == "H" else "ffffff", fg="1a1a1a", size=30)
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

def draw_phone_insert(cv, t):
    a0, a1 = PHONE
    if not (a0 <= t < a1):
        return
    k = ease_out_back(min(1, (t - a0) / 0.3), 1.8); a = min(1, (a1 - t) / 0.2)
    cv.save(); cv.translate(540, 800); cv.rotate(-6 + 2 * (1 - k)); cv.scale(k, k)
    body = skia.RRect.MakeRectXY(skia.Rect(-230, -400, 230, 400), 48, 48)
    cv.drawRRect(body, P(C("000000", 0.35 * a), blur=24)); cv.drawRRect(body, P(C("1d1d26", a))); cv.drawRRect(body, P(C("000000", a), stroke=8))
    scr = skia.Rect(-204, -360, 204, 360)
    cv.drawRRect(skia.RRect.MakeRectXY(scr, 28, 28), P(C("ffffff", a)))
    text(cv, "@gym_baddie_xo", -180, -310, 30, C("141414", a), tf=TF_B, align="l")
    ph = skia.Rect(-190, -280, 190, 120)
    cv.drawRect(ph, P(C("ffb3c7", a)))
    cv.drawCircle(0, -120, 70, P(C("ffffff", a))); cv.drawCircle(0, -120, 70, P(C("141414", a), stroke=6))
    cv.drawPath(poly([(-110, 120), (110, 120), (80, -40), (-80, -40)]), P(C("e8262a", a)))
    cv.drawLine(-60, -150, -40, -150, P(C("141414", a), stroke=8)); cv.drawLine(40, -150, 60, -150, P(C("141414", a), stroke=8))
    hk = 1 + 0.25 * max(0, math.sin((t - a0) * 10)) * (t - a0 < 0.6)
    M.heart(cv, -150, 190, 1.2 * hk)
    text(cv, "Liked by you", -110, 200, 34, C("141414", a), tf=TF_B, align="l")
    text(cv, "MARCH 14, 2019", -180, 280, 34, C("8a8a99", a), tf=TF_B, align="l")
    cv.restore()

def draw_think(cv, t):
    if not (S(14) <= t < S(15)):
        return
    a, k = pop(t, S(14), 0.4)
    for j, (x, y, r) in enumerate(((560, 640, 20), (610, 560, 30))):
        cv.drawCircle(x, y, r * k, P(C("ffffff", a))); cv.drawCircle(x, y, r * k, P(C("141414", a), stroke=6))
    rr = skia.RRect.MakeRectXY(skia.Rect(600, 300, 980, 520), 110, 110)
    cv.save(); cv.translate(790, 410); cv.scale(k, k); cv.translate(-790, -410)
    cv.drawRRect(rr, P(C("ffffff", a))); cv.drawRRect(rr, P(C("141414", a), stroke=7))
    for j in range(3):
        on = (t - S(14)) > 0.25 + j * 0.3
        if on:
            text(cv, "?", 700 + j * 90, 450 + 10 * math.sin(t * 8 + j), 120, C("e8262a", a), tf=TF_BLACK)
    cv.restore()

def draw_xs(cv, t):
    if t < T_REW[0]:   # hook stamps
        for j in range(3):
            t0 = 0.35 + j * 0.33
            if t >= t0:
                k = ease_out_back(min(1, (t - t0) / 0.18), 2.5)
                xmark(cv, 300 + j * 240, 1200, 80 * (1.6 - 0.6 * k))
        return
    n = sum(1 for i in (9, 11, 13) if t >= S(i))
    if n and t < S(15):
        for j in range(n):
            i = (9, 11, 13)[j]
            k = ease_out_back(min(1, (t - S(i)) / 0.2), 2.5)
            xmark(cv, 380 + j * 160, 1215, 52 * (1.8 - 0.8 * k))

TOP = ["She said \"Guess what I'm thinking\"…", "HE NEVER STOOD A CHANCE"]

def draw_top(cv, t):
    f = skia.Font(TF_B, 44)
    w = max(f.measureText(TOP[0]), skia.Font(TF_BLACK, 48).measureText(TOP[1])) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 286), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    text(cv, TOP[0], 540, 208, 44, C("111111"), tf=TF_B)
    text(cv, TOP[1], 540, 264, 48, C("e74c3c"), tf=TF_BLACK)
    te = S(19) + 0.6
    if t > te:
        a, k = pop(t, te, 0.45)
        chip(cv, 540, 420, "SHE NEVER FORGETS", a=a, scale=k, col="ffd23f", fg="1a1a1a", size=62)

def draw_rewind(cv, t):
    a0, a1 = T_REW
    if a0 <= t < a1 + 0.9:
        if t < a1:
            q = (t - a0) / (a1 - a0)
            cv.drawRect(skia.Rect(0, 0, W, H), P(C("10131c", 0.35)))
            for j in range(9):   # VHS streaks
                y = (j * 233 + (t * 2400)) % H
                cv.drawRect(skia.Rect(0, y, W, y + 10 + 14 * (j % 3)), P(C("ffffff", 0.18)))
            # rewind icon
            cv.save(); cv.translate(540, 900)
            for dx in (-70, 10):
                cv.drawPath(poly([(dx + 60, -60), (dx + 60, 60), (dx - 20, 0)]), P(C("ffffff", 0.95)))
            cv.restore()
        tag(cv, t, a0 + 0.1, a1 + 0.9, "1 HOUR EARLIER", 1100, col="ffffff", size=64)

def render_frame(cv, t):
    z, wx, wy = camera(t)
    sx, sy = shake(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2 + sx, H / 2 + sy); cv.scale(z, z); cv.translate(-wx, -wy)
    CO.draw_room(cv, t); CO.draw_couch_back(cv); CO.draw_couch_front(cv)
    M.draw_person(cv, t, girl_state(t), HX, "girl")
    M.draw_person(cv, t, guy_state(t), GX, "guy")
    if t < T_REW[0] or (HOLD[0] <= t < S(18)):
        cv.drawRect(skia.Rect(-200, -200, W + 200, H + 200), P(C("2a1030", 0.12)))
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    if S(17) <= t < REVEAL:   # punch-in flash on the bomb
        pass
    if abs(t - REVEAL) < 0.08:
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("ffffff", 0.6 * (1 - abs(t - REVEAL) / 0.08))))
    draw_top(cv, t)
    draw_xs(cv, t)
    tag(cv, t, S(5), S(6), "RULE #1", 470, col="e8262a", fg="ffffff", size=64)
    for n_, i in enumerate((8, 10, 12)):
        tag(cv, t, S(i), S(i + 1) + 0.25, f"GUESS #{n_ + 1}", 400, size=52)
    draw_think(cv, t)
    draw_phone_insert(cv, t)
    draw_rewind(cv, t)
    draw_caption(cv, t)
    fade = 1 - ss(TOTAL - 0.5, TOTAL, t)
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
        print("rew", T_REW, "reveal", REVEAL, "total", TOTAL)
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
