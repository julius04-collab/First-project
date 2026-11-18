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
GX, HX0 = 330.0, 790.0
T_REW = (E(1) + 0.05, S(2))
TWITCH = (E(22) + 0.2, S(23))
BACK2SLEEP = E(24) + 0.5
ANGRY = (6, 12, 17, 23)

def tired(t):
    """0 fresh -> 1 asleep"""
    return ss(S(8), S(14) + 2.2, t)

def asleep(t):
    return S(14) + 2.2 <= t < S(17) or t < T_REW[0] or t >= BACK2SLEEP

def girl_x(t):
    if S(7) <= t < E(8):
        return HX0 - 120 + 120 * math.cos(2 * math.pi * (t - S(7)) / 4.2)
    if S(14) <= t < E(15) + 0.2:
        return lerp(HX0, 900, ss(S(14), S(14) + 1.6, t))
    if E(15) + 0.2 <= t < S(17):
        return 900
    if S(17) <= t < S(17) + 0.6:
        return lerp(900, HX0, ss(S(17), S(17) + 0.6, t))
    return HX0

def girl_vx(t):
    return (girl_x(t + 0.02) - girl_x(t - 0.02)) / 0.04

def zs(cv, t, x, y, a=1.0):
    for j in range(3):
        q = ((t * 0.7) + j / 3) % 1
        s = 40 + 40 * q
        f = skia.Font(TF_BLACK, s)
        al = a * min(1, q * 4) * (1 - q)
        cv.save(); cv.translate(x + 60 * q + 20 * math.sin(q * 6), y - 220 * q); cv.rotate(-12)
        cv.drawString("Z", 0, 0, f, P(C("ffffff", al), stroke=10)); cv.drawString("Z", 0, 0, f, P(C("3b6fd8", al)))
        cv.restore()

HIPS_L, HIPS_R = (-18, 168), (18, 168)
REST_L, REST_R = (-30, 175), (30, 175)

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, -0.25), brows=(4, 4), mouth="smirk", grass="mouth", tilt=0)
    k = tired(t)
    # heavy blinks as he gets tired
    if k > 0:
        per = lerp(3.0, 0.9, k); dur = lerp(0.15, 0.7, k)
        st["blink"] = ((t - S(8)) % per) < dur
    else:
        st["blink"] = (t % 3.7) < 0.12
    st["brows"] = (lerp(4, -2, k), lerp(4, -2, k))
    for i in (3,):
        if S(i) <= t < E(i) + 0.2:
            st.update(brows=(16, 16), mouth="flat", handL=(-140, -20), handR=(140, -20))
    if S(5) <= t < E(5) + 0.1:
        st.update(brows=(14, 14), mouth="smile", handR=(130, -60), tilt=6)
    for i in (6, 12):
        if S(i) <= t < E(i) + 0.4:
            st.update(eyes="wide", brows=(20, 20), mouth="flat", blink=False, tilt=-6)
    if S(9) <= t < E(9) + 0.1:
        st.update(mouth="smile", handR=(110, -110), blink=False)
    if S(11) <= t < E(11) + 0.1:
        st.update(look=(0.4, -0.9), brows=(16, 4), tilt=-8, mouth="flat", blink=False)
    if S(13) <= t < S(14) + 2.2:     # fighting the eyelids, head bobbing
        st["tilt"] = 6 + 8 * max(0, math.sin((t - S(13)) * 2.2)); st["lean"] = 3 * max(0, math.sin((t - S(13)) * 2.2))
    if asleep(t):
        st.update(eyes="closed", blink=False, brows=(0, 0), mouth="o", tilt=16, lean=4, look=(0.0, 0.3))
    if S(17) <= t < E(18) + 0.3:     # jolt awake
        j = max(0, 1 - (t - S(17)) / 0.5)
        st.update(eyes="wide", blink=False, brows=(22, 22), mouth="o", tilt=-6 * j, lean=0, bob=60 * j * (t >= E(17) - 0.05),
                  handL=(-130, -170), handR=(130, -170), sweat=True)
        if t > S(18) + 0.8:
            st.update(handL=(-120, -60), handR=(120, -60), mouth="flat")
    if S(19) <= t < S(22):
        st.update(brows=(12, 12), mouth="smile", handR=(-40, -150), tilt=6, sweat=True, look=(1.0, -0.25))
    if S(22) <= t < BACK2SLEEP:
        st.update(eyes="happy" if amp("G", t) < 0.05 else "n", mouth="smile", brows=(10, 10), tilt=6, handR=(140, -40), sweat=False, look=(1.0, -0.25))
        if E(22) <= t:
            st.update(handR=REST_R, eyes="n")
    if S(23) <= t < S(23) + 0.5:
        st.update(eyes="wide", brows=(20, 20), mouth="flat")
    if S(24) <= t < BACK2SLEEP:
        st.update(eyes="n", mouth="smile", brows=(14, 14), tilt=8, handL=(-60, 60), handR=(60, 60))
    if t >= BACK2SLEEP:
        st.update(mouth="smile", handL=(-60, 60), handR=(60, 60))
    if t < T_REW[0]:
        st["mouth"] = "o"
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    vx = girl_vx(t)
    st = dict(handL=HIPS_L, handR=HIPS_R, look=(-1.0, 0.0), brows=(-14, -14), mouth="flat", tilt=-4, rise=1.0)
    st["blink"] = (t % 4.1) < 0.12
    def rant(amt=1.0):
        st.update(handR=(-170, -80 + 18 * math.sin(t * 9)), brows=(-18, -18))
    if t < T_REW[0]:
        rant(); st["amp"] = 0.35 + 0.35 * math.sin(t * 17)
        return st
    if S(4) <= t < E(4):
        rant()
    if S(6) <= t < E(6) + 0.3 or S(12) <= t < E(12) + 0.3:
        st.update(handL=(-120, -190 + 10 * math.sin(t * 20)), handR=(120, -190 + 10 * math.cos(t * 20)), brows=(-22, -22), tilt=-8)
    if abs(vx) > 5:
        st["walk"] = (t * 9) % (2 * math.pi) * 1.0 + t * 9
        st["look"] = (1.0 if vx > 0 else -1.0, 0.0)
    if S(8) <= t < E(8):
        st.update(handL=(-110, -60 + 20 * math.sin(t * 6)), handR=(110, -60 + 20 * math.cos(t * 6)), brows=(-16, -16))
    if S(10) <= t < E(10) + 0.2:
        st.update(brows=(-12, 8), tilt=-10)
    if S(14) <= t < E(15) + 0.25:
        st.update(look=(1.0, -0.3), brows=(-10, -10), tilt=6, handR=(140, -120 + 20 * math.sin(t * 5)), handL=HIPS_L)
        if abs(vx) > 5:
            st["walk"] = t * 7
    if E(15) + 0.25 <= t < S(17):
        st.update(look=(-1.0, 0.0), brows=(6, 6), tilt=0, handL=HIPS_L, handR=HIPS_R)
        if t > S(16) + 0.9:
            st.update(brows=(-6, -6), eyes="wide")
    if S(17) <= t < E(17) + 0.4:
        st.update(handL=(-120, -190), handR=(120, -190), brows=(-24, -24), tilt=-8, look=(-1.0, 0.0))
    if S(19) <= t < E(19) + 0.2:
        rant()
    if S(21) <= t < E(21) + 0.3:
        st.update(handL=(-120, -190), handR=(120, -190), brows=(-22, -22))
    if S(22) <= t < TWITCH[0]:
        st.update(brows=(-16, -16), mouth="flat")
    if TWITCH[0] <= t < S(23):
        tw = (t * 9) % 1 < 0.45
        st.update(brows=(-16, 4 if tw else -16), blink=tw, look=(-1.0, 0.0), mouth="flat")
    if S(23) <= t < E(23) + 0.6:
        st.update(handR=(-200, -120), handL=HIPS_L, brows=(-26, -26), tilt=-10)
    if E(23) + 0.6 <= t:
        st.update(eyes="wide", brows=(18, 18), mouth="o", handL=HIPS_L, handR=HIPS_R, tilt=0)
    if t >= BACK2SLEEP + 0.6:
        st.update(look=(0.0, 0.0), eyes="n", brows=(-10, -10), mouth="flat")   # deadpan to camera
    st["amp"] = amp("H", t)
    return st

WIDE = (1.0, 560, 1130)
G_CU = (1.85, GX + 30, 990)
def H_CU(t, z=1.8):
    return (z, girl_x(t) - 10, 800)

def camera(t):
    if t < S(1):
        return (lerp(1.15, 1.25, t / S(1)), 590, 1000)
    if t < T_REW[0]:
        return (lerp(2.0, 2.3, (t - S(1)) / (T_REW[0] - S(1))), GX + 30, 985)
    if t < S(2) + 0.3:
        k = ss(T_REW[0], S(2) + 0.3, t)
        return (lerp(2.3, 1.0, k), lerp(GX + 30, 560, k), lerp(985, 1130, k))
    mid4 = (S(4) + E(4)) / 2; mid8 = (S(8) + E(8)) / 2
    shots = [
        (S(2), S(2) + 1.0, WIDE), (S(2) + 1.0, S(3), H_CU), (S(3), S(4), G_CU),
        (S(4), mid4, H_CU), (mid4, S(5), (1.25, 590, 1030)), (S(5), S(6), G_CU),
        (S(6), S(7), lambda t: H_CU(t, 2.2)), (S(7), mid8, WIDE), (mid8, S(9), G_CU),
        (S(9), S(10), G_CU), (S(10), S(11), H_CU), (S(11), S(12), G_CU), (S(12), S(13), lambda t: H_CU(t, 2.2)),
        (S(13), S(14), G_CU),
        (E(15), S(16), (1.15, 600, 1060)), (S(16), S(16) + 0.9, H_CU), (S(16) + 0.9, S(17), (2.1, GX + 30, 990)),
        (S(17), S(18), lambda t: H_CU(t, 2.3)), (S(18), S(19), G_CU), (S(19), S(20), H_CU), (S(20), S(21), G_CU),
        (S(21), S(22), lambda t: H_CU(t, 2.2)), (S(22), E(22), G_CU), (E(22), S(23), lambda t: H_CU(t, 2.2)),
        (S(23), S(24), lambda t: H_CU(t, 2.4)), (S(24), BACK2SLEEP, G_CU),
    ]
    if S(14) <= t < E(15):     # slow zoom on the boyfriend as he drifts off
        k = ss(S(14), E(15), t)
        return (lerp(1.15, 2.3, k), lerp(600, GX + 30, k), lerp(1060, 985, k))
    for a, b, c in shots:
        if a <= t < b:
            c = c(t) if callable(c) else c
            if b - a > 0.8 and c is not WIDE:
                q = (t - a) / (b - a); return (c[0] * (1 + 0.05 * q), c[1], c[2])
            return c
    return (lerp(1.1, 1.2, ss(BACK2SLEEP, TOTAL, t)), 590, 1080)

def shake(t):
    for i, amt in ((6, 10), (12, 10), (17, 18), (21, 8), (23, 16)):
        if S(i) <= t < S(i) + 0.4:
            d = 1 - (t - S(i)) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    return (0, 0)

HL = {0: {"FIVE": "b", "YELLED": "y"}, 1: {"TEN": "b", "HEARD": "y"}, 2: {"FORGOT": "y", "TODAY": "b"},
      3: {"DO?": "y"}, 4: {"DO?!": "b", "FOOD,": "y", "FOOTBALL,": "y", "DAY": "y"}, 5: {"CHICKEN.": "b"},
      6: {"POINT!": "b"}, 7: {"PACING.": "b"}, 8: {"NEVER": "b", "PHONE,": "y", "FOOTBALL,": "y"},
      9: {"LISTENING.": "y"}, 10: {"SAID.": "y"}, 11: {"CHICKEN?": "b"}, 12: {"SERIOUS": "b"},
      13: {"LIFE…": "y", "EYELIDS.": "b"}, 14: {"QUALITY": "y", "TIME": "y"}, 15: {"RELATIONSHIP,": "b"},
      16: {"BABE?": "y"}, 17: {"BABE!": "b"}, 18: {"LISTENING!": "b"}, 19: {"SLEEPING?!": "b"},
      20: {"CONCENTRATE.": "b"}, 21: {"FIVE": "b", "MINUTES?!": "b"}, 22: {"DREAMS": "b"},
      23: {"GET": "b", "OUT!": "b"}, 24: {"DREAM?": "b"}}
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


def battery(cv, t):
    a0, a1 = S(8), S(17)
    if not (a0 <= t < a1):
        return
    a, k = pop(t, a0, 0.35)
    lvl = 1 - tired(t) * 1.0
    cv.save(); cv.translate(180, 440); cv.scale(k, k)
    text(cv, "HIS FOCUS", 70, -40, 34, C("ffffff", a), tf=TF_BLACK, stroke=8, stroke_col=C("000000", a))
    body = skia.RRect.MakeRectXY(skia.Rect(-20, -18, 150, 52), 12, 12)
    cv.drawRRect(body, P(C("141414", a))); cv.drawRRect(body, P(C("ffffff", a), stroke=6))
    cv.drawRect(skia.Rect(150, 2, 162, 32), P(C("ffffff", a)))
    col = "3ccf5a" if lvl > 0.5 else ("ffb020" if lvl > 0.2 else "e8262a")
    blinkoff = lvl < 0.2 and (t * 4) % 1 < 0.4
    if lvl > 0.01 and not blinkoff:
        cv.drawRect(skia.Rect(-10, -8, -10 + 150 * lvl, 42), P(C(col, a)))
    text(cv, f"{int(round(lvl * 100))}%", 230, 32, 44, C("ffffff", a), tf=TF_BLACK, stroke=8, stroke_col=C("000000", a))
    cv.restore()

TOP = ["When he falls asleep DURING the argument…", "\"I WAS LISTENING!\""]

def draw_top(cv, t):
    f = skia.Font(TF_B, 44)
    w = max(f.measureText(TOP[0]), skia.Font(TF_BLACK, 48).measureText(TOP[1])) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 286), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    text(cv, TOP[0], 540, 208, 44, C("111111"), tf=TF_B)
    text(cv, TOP[1], 540, 264, 48, C("e74c3c"), tf=TF_BLACK)
    te = BACK2SLEEP + 0.4
    if t > te:
        a, k = pop(t, te, 0.45)
        chip(cv, 540, 420, "BRO HAD NO FEAR", a=a, scale=k, col="ffd23f", fg="1a1a1a", size=62)

def draw_rewind(cv, t):
    a0, a1 = T_REW
    if a0 <= t < a1 + 0.9:
        if t < a1:
            cv.drawRect(skia.Rect(0, 0, W, H), P(C("10131c", 0.35)))
            for j in range(9):
                y = (j * 233 + (t * 2400)) % H
                cv.drawRect(skia.Rect(0, y, W, y + 10 + 14 * (j % 3)), P(C("ffffff", 0.18)))
            cv.save(); cv.translate(540, 900)
            for dx in (-70, 10):
                cv.drawPath(poly([(dx + 60, -60), (dx + 60, 60), (dx - 20, 0)]), P(C("ffffff", 0.95)))
            cv.restore()
        tag(cv, t, a0 + 0.1, a1 + 0.9, "10 MINUTES EARLIER", 1100, col="ffffff", size=64)

def render_frame(cv, t):
    z, wx, wy = camera(t)
    sx, sy = shake(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2 + sx, H / 2 + sy); cv.scale(z, z); cv.translate(-wx, -wy)
    CO.draw_room(cv, t); CO.draw_couch_back(cv); CO.draw_couch_front(cv)
    gs = guy_state(t)
    M.draw_person(cv, t, gs, GX, "guy")
    M.draw_person(cv, t, girl_state(t), girl_x(t), "girl")
    if gs.get("eyes") == "closed":
        zs(cv, t, GX + 110, 820)
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    draw_top(cv, t)
    if t < T_REW[0]:
        tag(cv, t, 0.3, S(1), "5 MINUTES", 470, col="e8262a", fg="ffffff", size=64)
        tag(cv, t, S(1) + 0.1, T_REW[0], "HEARD: 10 SECONDS", 470, col="ffd23f", size=60)
    tag(cv, t, S(7), S(8) + 0.8, "IT GETS WORSE", 470, col="e8262a", fg="ffffff", size=60)
    battery(cv, t)
    tag(cv, t, S(16) + 0.9, S(17), "SNORE…", 470, col="3b6fd8", fg="ffffff", size=60)
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
