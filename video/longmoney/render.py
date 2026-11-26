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
W, H, FPS = 1920, 1080, 30
D = json.load(open(os.path.join(HERE, "vo.json")))
SEGS, TOTAL = D["segs"], D["total"]
INK = C("141414")
def lerp(a, b, t): return a + (b - a) * t
def S(i): return SEGS[i]["start"]
def E(i): return SEGS[i]["end"]
def amp(who, t):
    for s in SEGS:
        if s["who"] == who and s["start"] <= t < s["end"]:
            j = int((t - s["start"]) * FPS)
            if j < len(s["env"]): return s["env"][j]
    return 0.0
def seg_at(t):
    cur = 0
    for s in SEGS:
        if s["start"] <= t: cur = s["i"]
    return cur

# ---------------------------------------------------------------- timeline
REWIND = (E(0) + 1.0, E(0) + 2.0)
CARD0 = (E(0) + 2.0, S(1) - 0.6)
CARD1 = (E(12) + 1.3, E(12) + 2.9)
DING2 = S(13) - 1.1
CARD2 = (E(23) + 1.3, E(23) + 2.9)
JACKET = (CARD2[1] + 0.3, S(24) - 0.2)
DAN_IN = (E(26) + 0.05, S(27) + 0.2)
TRAY_DOWN = E(29) + 0.1
SITDOWN = (E(50) + 0.3, S(51) - 0.2)
HUG = E(68) + 0.05
BUZZ = E(68) + 0.9
GRAB = E(72) + 0.05
RUN0 = GRAB + 0.35
BLACK = E(73) + 0.5
ENDCARD = BLACK + 0.3
ANGRY = (26, 28, 36, 45, 69, 71, 72, 73)

def location(t):
    if t < CARD0[0]: return "bed"
    if CARD1[1] <= t < CARD2[0] + 0.8: return "bed"
    return "living"

# ---------------------------------------------------------------- world: living room
OFF = 460.0
SEAT_G, SEAT_H = OFF + 330, OFF + 740
WWORLD = 2000.0

def living_room(cv, t):
    cv.drawRect(skia.Rect(-400, -900, WWORLD + 400, 1420), P(C("f3d9b8")))
    for k in range(-4, 22):
        x = 50 + OFF + 120 * k - 120 * 4
        cv.drawRect(skia.Rect(x, -900, x + 12, 1420), P(C("ebcda8")))
    cv.drawRect(skia.Rect(-400, 1420, WWORLD + 400, 2700), P(C("c99260")))
    for i in range(20):
        cv.drawLine(-400, 1460 + i * 64, WWORLD + 400, 1460 + i * 64, P(C("b07c4c"), stroke=4))
    cv.save(); cv.translate(OFF, 0); CO.draw_room(cv, t); CO.draw_couch_back(cv); CO.draw_couch_front(cv); cv.restore()
    # TV corner (left)
    cv.drawRect(skia.Rect(20, 1200, 300, 1420), P(C("8a5a3a"))); cv.drawRect(skia.Rect(20, 1200, 300, 1420), P(INK, stroke=7))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(30, 900, 290, 1120), 12, 12), P(C("1b1b22"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(30, 900, 290, 1120), 12, 12), P(INK, stroke=7))
    cv.drawRect(skia.Rect(46, 916, 274, 1104), P(C("2c3e66")))
    cv.drawLine(160, 1120, 160, 1200, P(INK, stroke=12))
    # side table (left of couch)
    cv.drawRect(skia.Rect(340, 1330, 470, 1350), P(C("8a5a3a"))); cv.drawRect(skia.Rect(340, 1330, 470, 1350), P(INK, stroke=5))
    for x in (350, 450): cv.drawRect(skia.Rect(x, 1350, x + 12, 1600), P(C("8a5a3a")))
    # bookshelf + plant (right)
    cv.drawRect(skia.Rect(1640, 820, 1900, 1420), P(C("a0683f"))); cv.drawRect(skia.Rect(1640, 820, 1900, 1420), P(INK, stroke=7))
    for j in range(4):
        y = 900 + j * 130
        cv.drawLine(1640, y + 100, 1900, y + 100, P(INK, stroke=6))
        for b in range(5):
            cv.drawRect(skia.Rect(1660 + b * 46, y + 20 + (b % 2) * 14, 1696 + b * 46, y + 100), P(C(["e8424a", "3a7bd5", "f2c230", "3ccf5a", "9b59b6"][(b + j) % 5])))
    cv.drawPath(poly([(1930, 1300), (2030, 1300), (2015, 1420), (1945, 1420)]), P(C("e2725b"))); cv.drawPath(poly([(1930, 1300), (2030, 1300), (2015, 1420), (1945, 1420)]), P(INK, stroke=5))
    for a in (-40, -10, 20, 45):
        cv.save(); cv.translate(1980, 1300); cv.rotate(a)
        cv.drawOval(skia.Rect(-22, -170, 22, 0), P(C("3fa65a"))); cv.drawOval(skia.Rect(-22, -170, 22, 0), P(INK, stroke=4)); cv.restore()

# ---------------------------------------------------------------- world: bedroom (evening)
BED_SEAT = 900.0
def bedroom(cv, t):
    cv.drawRect(skia.Rect(-400, -900, WWORLD + 400, 1420), P(C("cdbfe0")))
    for k in range(-2, 22):
        cv.drawRect(skia.Rect(k * 120 + 30, -900, k * 120 + 42, 1420), P(C("c3b4d8")))
    cv.drawRect(skia.Rect(-400, 1420, WWORLD + 400, 2700), P(C("8a6a5a")))
    for i in range(20):
        cv.drawLine(-400, 1460 + i * 64, WWORLD + 400, 1460 + i * 64, P(C("7a5c4c"), stroke=4))
    # window (evening)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(160, 380, 520, 820), 10, 10), P(C("fff6ea")))
    cv.drawRect(skia.Rect(176, 396, 504, 804), P(0, shader=lin(0, 396, 0, 804, [C("2a2a6b"), C("b0507a"), C("ff9a5a")])))
    cv.drawLine(340, 396, 340, 804, P(C("fff6ea"), stroke=10)); cv.drawLine(176, 600, 504, 600, P(C("fff6ea"), stroke=10))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(160, 380, 520, 820), 10, 10), P(INK, stroke=7))
    # picture
    cv.drawRect(skia.Rect(760, 480, 1000, 660), P(C("ffffff"))); cv.drawRect(skia.Rect(760, 480, 1000, 660), P(INK, stroke=7))
    cv.drawPath(poly([(790, 640), (860, 540), (920, 610), (960, 570), (980, 640)]), P(C("6fb07a")))
    # nightstand + lamp
    cv.drawRect(skia.Rect(1340, 1220, 1500, 1420), P(C("8a5a3a"))); cv.drawRect(skia.Rect(1340, 1220, 1500, 1420), P(INK, stroke=6))
    cv.drawLine(1420, 1220, 1420, 1120, P(INK, stroke=8))
    cv.drawPath(poly([(1360, 1120), (1480, 1120), (1455, 1030), (1385, 1030)]), P(C("ffe2a0"))); cv.drawPath(poly([(1360, 1120), (1480, 1120), (1455, 1030), (1385, 1030)]), P(INK, stroke=5))
    cv.drawCircle(1420, 1100, 260, P(C("ffe2a0", 0.25), blur=60))
    # door (right)
    k = ss(S(14) - 1.6, S(14) - 1.2, t) if t > CARD1[0] else 0
    cv.drawRect(skia.Rect(1600, 640, 1840, 1420), P(C("6a4a3a"))); cv.drawRect(skia.Rect(1600, 640, 1840, 1420), P(INK, stroke=7))
    w = 240 * (1 - 0.8 * k)
    cv.drawRect(skia.Rect(1600, 640, 1600 + w, 1420), P(C("c08a5a"))); cv.drawRect(skia.Rect(1600, 640, 1600 + w, 1420), P(INK, stroke=6))
    # bed
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(440, 1000, 520, 1600), 20, 20), P(C("7a4a3a"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(440, 1000, 520, 1600), 20, 20), P(INK, stroke=7))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(500, 1240, 1280, 1340), 24, 24), P(C("f1f1f8"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(500, 1240, 1280, 1340), 24, 24), P(INK, stroke=6))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(520, 1180, 700, 1270), 40, 40), P(C("ffffff"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(520, 1180, 700, 1270), 40, 40), P(INK, stroke=5))
    cv.drawRect(skia.Rect(700, 1250, 1280, 1340), P(C("6a8fd0")))

def bed_front(cv):
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(500, 1330, 1290, 1450), 20, 20), P(C("6a8fd0"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(500, 1330, 1290, 1450), 20, 20), P(INK, stroke=7))
    cv.drawRect(skia.Rect(500, 1450, 1290, 1520), P(C("7a4a3a"))); cv.drawRect(skia.Rect(500, 1450, 1290, 1520), P(INK, stroke=6))
    for x in (520, 1250): cv.drawRect(skia.Rect(x, 1520, x + 24, 1600), P(C("5a3a24")))

# ---------------------------------------------------------------- acting
REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
CLASP_L, CLASP_R = (60, 60), (-60, 60)
HIPS_L, HIPS_R = (-18, 168), (18, 168)
PRE = {
    "neutral": dict(brows=(6, 6), mouth="flat"), "smile": dict(brows=(10, 10), mouth="smile"), "happy": dict(brows=(14, 14), mouth="smile", eyes="happy"),
    "worried": dict(brows=(16, 16), mouth="flat", tilt=6), "sus": dict(brows=(-12, 14), mouth="flat", tilt=-6), "annoyed": dict(brows=(-14, -14), mouth="flat"),
    "angry": dict(brows=(-22, -22), mouth="flat", tilt=-6), "shock": dict(brows=(22, 22), mouth="o", eyes="wide"), "nervous": dict(brows=(16, 16), mouth="smile", sweat=True),
    "smug": dict(brows=(-6, 12), mouth="smirk", tilt=8), "sad": dict(brows=(14, 14), mouth="flat", tilt=-4), "soft": dict(brows=(10, 10), mouth="smile", tilt=6),
    "proud": dict(brows=(12, 4), mouth="smile", tilt=6), "offended": dict(brows=(-12, -12), mouth="flat", tilt=-8), "terrified": dict(brows=(26, 26), mouth="o", eyes="wide", sweat=True),
    "sheepish": dict(brows=(16, 16), mouth="smile", tilt=8), "serious": dict(brows=(2, 2), mouth="flat"), "thinking": dict(brows=(14, 2), mouth="flat", tilt=-6),
}
# (guy emotion, girl emotion) per line
EMO = ["happy|neutral", "worried|neutral", "worried|smile", "nervous|sus", "nervous|smile", "worried|sus", "worried|annoyed", "serious|annoyed",
       "nervous|sus", "proud|sus", "smile|sus", "happy|annoyed", "nervous|angry",
       "happy|neutral", "shock|sus", "nervous|sus", "nervous|sus", "nervous|sus", "nervous|sus", "nervous|sus", "nervous|annoyed", "serious|sus", "nervous|annoyed", "sheepish|sus",
       "neutral|sus", "neutral|shock", "neutral|angry", "happy|angry", "terrified|angry", "terrified|angry", "shock|angry", "shock|smug", "offended|smug", "nervous|angry",
       "serious|annoyed", "terrified|angry",
       "serious|angry", "serious|angry", "serious|angry", "proud|angry", "nervous|angry", "serious|annoyed", "offended|angry", "serious|angry", "offended|angry",
       "worried|angry", "worried|annoyed", "worried|angry", "sad|annoyed", "sad|soft",
       "sad|soft", "sad|serious", "sad|serious", "sad|soft", "sad|serious", "soft|soft", "soft|serious", "smile|shock", "soft|soft", "soft|soft", "sad|soft", "soft|happy",
       "smile|soft", "proud|shock", "happy|happy", "happy|happy", "happy|happy", "shock|shock", "sheepish|angry", "terrified|angry", "terrified|angry", "terrified|angry"]

def emo(t, who):
    i = seg_at(t)
    g, h = EMO[min(i, len(EMO) - 1)].split("|")
    return dict(PRE[g if who == "G" else h])

def talk_gesture(st, t, who, standing):
    a = amp(who, t)
    if a > 0.02:
        w = math.sin(t * 7 + (0 if who == "G" else 1.5))
        if who == "G": st["handR"] = (130, -80 + 30 * w)
        else: st["handR"] = (-150, -60 + 30 * w)

# ---------------------------------------------------------------- positions
def guy_pos(t):
    loc = location(t)
    if loc == "bed": return BED_SEAT, 0.0
    if t < JACKET[0]: return SEAT_G, 0.0
    if t < DAN_IN[0]: return -400, 1.0
    if t < SITDOWN[0]: return lerp(-300, 760, ss(DAN_IN[0], DAN_IN[1], t)), 1.0
    if t < RUN0:
        x = lerp(760, SEAT_G, ss(SITDOWN[0], SITDOWN[0] + 0.6, t))
        r = 1 - ss(SITDOWN[0] + 0.6, SITDOWN[1], t)
        if GRAB <= t: r = ss(GRAB, RUN0, t)
        return x, r
    return SEAT_G - 900 * (t - RUN0), 1.0

def girl_pos(t):
    loc = location(t)
    if loc == "bed":
        if t < CARD0[0]: return None
        return lerp(2150, 1380, ss(S(14) - 1.5, S(14) + 0.2, t)), 1.0
    if t < CARD1[0]:
        if t < S(1) + 0.5: return None
        return lerp(2150, 1380, ss(S(1) + 0.5, S(2) + 0.2, t)), 1.0
    if t < SITDOWN[0]: return 1320, 1.0
    if t < GRAB:
        x = lerp(1320, SEAT_H, ss(SITDOWN[0], SITDOWN[0] + 0.6, t))
        x = lerp(x, 1060, ss(HUG - 0.1, HUG + 0.5, t)) if t < BUZZ + 1.4 else lerp(1060, SEAT_H, ss(BUZZ + 1.4, BUZZ + 1.9, t))
        return x, 1 - ss(SITDOWN[0] + 0.6, SITDOWN[1], t)
    return max(SEAT_G + 200 - 900 * max(0, t - RUN0 - 0.3), lerp(SEAT_H, 1100, ss(GRAB, RUN0, t)) - 700 * max(0, t - RUN0 - 0.3)), ss(GRAB, RUN0, t)

def moving(fn, t):
    a, b = fn(t - 0.03), fn(t + 0.03)
    return a is not None and b is not None and abs(a[0] - b[0]) > 2

def guy_state(t):
    x, rise = guy_pos(t)
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.0), brows=(8, 8), mouth="smirk", grass="mouth", tilt=0, rise=rise)
    st["blink"] = (t % 3.7) < 0.12
    st.update(emo(t, "G"))
    talk_gesture(st, t, "G", rise > 0.5)
    loc = location(t)
    if loc == "bed":
        st.update(phone=True, handL=(80, -40), look=(0.5, 0.6))
        if t < E(0) + 1.0: st.update(eyes="happy", mouth="smile", brows=(16, 16))
        if CARD1[1] <= t:
            st.update(look=(0.5, 0.6))
            if S(13) <= t < E(13): st.update(eyes="happy", mouth="smile", handR=(130, -150))
            if E(13) <= t < S(14): st.update(look=(-1.0 if (t * 2) % 1 < 0.5 else 1.0, 0.0), eyes="wide")   # looks around
            if S(14) <= t: st.update(look=(1.0, 0.0), handL=(80, 40))
    else:
        if t < JACKET[0]:
            st.update(phone=True, handL=(90, 40), look=(0.4, 0.7) if t < S(2) else (1.0, -0.1), lean=-6)
            if S(3) <= t: st.update(handL=(90, 90))
        if DAN_IN[0] <= t < TRAY_DOWN: st.update(handL=(150, 20), handR=(60, 20), tray=True)
        if S(28) <= t < TRAY_DOWN: st.update(tilt=6 * math.sin(t * 25))
        if SITDOWN[0] <= t < S(51): st.update(look=(0.2, 0.5), brows=(14, 14), mouth="flat")
        if S(57) <= t < S(58) and t > E(57) + 0.4: st.update(look=(0.2, 0.6), mouth="smile")                  # looks down, then smiles
        if HUG <= t < BUZZ + 1.4: st.update(handR=(170, -70), eyes="happy", mouth="smile")
        if BUZZ <= t < GRAB: st.update(phone=True, handL=(90, 40))
        if BUZZ + 0.3 <= t < S(70): st.update(eyes="wide", mouth="flat", brows=(20, 20), sweat=True, handR=REST_R)
        if S(70) <= t < S(71): st.update(look=(0.0, 0.0), mouth="smile", brows=(16, 16), sweat=True)      # slowly looks away
        if GRAB <= t: st.update(phone=False, handL=UP_L, handR=UP_R, eyes="wide", mouth="o", brows=(24, 24), sweat=True, look=(-1.0, 0.0) if t >= RUN0 else (1.0, 0.0))
    if moving(guy_pos, t): st["walk"] = t * (16 if t >= RUN0 else 9)
    if DAN_IN[0] <= t < DAN_IN[1] or t >= RUN0: st["look"] = (1.0, 0.0) if t < RUN0 else (-1.0, 0.0)
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    p = girl_pos(t)
    x, rise = p if p else (0, 1)
    st = dict(handL=HIPS_L, handR=HIPS_R, look=(-1.0, 0.0), brows=(6, 6), mouth="smile", tilt=-4, rise=rise)
    st["blink"] = (t % 4.1) < 0.12
    st.update(emo(t, "H"))
    talk_gesture(st, t, "H", rise > 0.5)
    i = seg_at(t)
    if i in ANGRY and S(i) <= t < E(i) + 0.2:
        st.update(handL=(-120, -190 + 10 * math.sin(t * 20)), handR=(120, -190 + 10 * math.cos(t * 20)))
    if location(t) == "living":
        if JACKET[0] <= t < JACKET[0] + 0.8: st.update(handR=(-170, 120), lean=10, look=(-0.6, 0.6))
        if JACKET[1] - 0.6 <= t < S(24) + 0.1: st.update(lean=12, handR=(-120, 160), look=(-0.4, 0.8))
        if S(24) <= t < SITDOWN[0]: st.update(paper=True, handR=(-110, 30), handL=(-60, 30))
        if S(24) <= t < S(26): st.update(look=(-0.3, 0.6))
        if rise < 0.5 and not (i in ANGRY and S(i) <= t < E(i) + 0.2) and amp("H", t) < 0.02: st.update(handL=CLASP_L, handR=CLASP_R)
        if HUG <= t < BUZZ + 1.4: st.update(handL=(-190, -60), handR=CLASP_R, eyes="happy", mouth="smile", tilt=-10, look=(-1.0, 0.0))
        if BUZZ + 0.4 <= t < S(69): st.update(look=(-0.6, 0.6), eyes="wide", mouth="o", brows=(-6, 18))
        if GRAB <= t: st.update(handR=(30, -230), handL=(-120, -60), brows=(-28, -28), mouth="o", pillow=True, tilt=-8)
    if moving(girl_pos, t):
        st["walk"] = t * 9
        a, b = girl_pos(t - 0.03), girl_pos(t + 0.03)
        st["look"] = (1.0 if b[0] > a[0] else -1.0, 0.0)
    st["amp"] = amp("H", t)
    return st

# ---------------------------------------------------------------- props
def hand_pos(x, st, side, girl=False):
    hip = M.SEAT - 18 - 200 * st["rise"] - st.get("bob", 0)
    sh = (84 if girl else 94) * (1 if side == "R" else -1)
    rel = st["handR" if side == "R" else "handL"]
    return x + sh + rel[0], hip - 224 + rel[1]

def headphones(cv, x, st):
    hip = M.SEAT - 18 - 200 * st["rise"] - st.get("bob", 0)
    y = hip - 262
    band = skia.Path(); band.moveTo(x - 72, y); band.quadTo(x, y + 70, x + 72, y)
    cv.drawPath(band, P(INK, stroke=14)); cv.drawPath(band, P(C("3a3f4a"), stroke=8))
    for dx in (-78, 78):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x + dx - 22, y - 34, x + dx + 22, y + 30), 14, 14), P(C("e8424a")))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x + dx - 22, y - 34, x + dx + 22, y + 30), 14, 14), P(INK, stroke=5))

def tray(cv, x, st, t):
    lx, ly = hand_pos(x, st, "L"); rx, ry = hand_pos(x, st, "R")
    cx, cy = (lx + rx) / 2, (ly + ry) / 2
    cv.save(); cv.translate(cx, cy - 14); cv.rotate(st.get("tilt", 0) * 1.5)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-110, -10, 110, 12), 6, 6), P(C("c0c4cc"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-110, -10, 110, 12), 6, 6), P(INK, stroke=5))
    cv.drawOval(skia.Rect(-90, -34, 10, -8), P(C("ffffff"))); cv.drawOval(skia.Rect(-90, -34, 10, -8), P(INK, stroke=4))
    cv.drawCircle(-55, -26, 14, P(C("ffd21f"))); cv.drawCircle(-55, -26, 6, P(C("ff9a1f")))
    cv.drawRect(skia.Rect(40, -60, 80, -10), P(C("ffffff"))); cv.drawRect(skia.Rect(40, -60, 80, -10), P(INK, stroke=4))
    cv.restore()
    for (hx, hy) in ((lx, ly), (rx, ry)):
        cv.drawCircle(hx, hy, 16, P(C("ffffff"))); cv.drawCircle(hx, hy, 16, P(INK, stroke=5))

def jacket_obj(cv, x, y, rot):
    cv.save(); cv.translate(x, y); cv.rotate(rot)
    jp = poly([(-110, -60), (110, -60), (120, 60), (-120, 60)])
    cv.drawPath(jp, P(C("3b5a8a"))); cv.drawPath(jp, P(INK, stroke=6))
    cv.drawLine(0, -60, 0, 60, P(INK, stroke=4))
    cv.restore()

def props(cv, t):
    if location(t) != "living": return
    if CARD2[1] <= t < SITDOWN[0]:
        if t < JACKET[0] or t > JACKET[0] + 0.8:
            jacket_obj(cv, 1010, 1300, -8)
        else:
            gs = girl_state(t); x = girl_pos(t)[0]; hx, hy = hand_pos(x, gs, "R", True)
            jacket_obj(cv, hx, hy + 20, 60)
        ef = JACKET[0] + 0.5
        if ef <= t < JACKET[1] - 0.2:      # envelope falls
            q = min(1, (t - ef) / 0.45)
            ex, ey = 1110, lerp(1180, 1585, q * q)
            cv.save(); cv.translate(ex, ey); cv.rotate(300 * q if q < 1 else 15)
            cv.drawRect(skia.Rect(-45, -28, 45, 28), P(C("f5ecd2"))); cv.drawRect(skia.Rect(-45, -28, 45, 28), P(INK, stroke=4))
            cv.drawPath(poly([(-45, -28), (0, 4), (45, -28)], close=False), P(INK, stroke=3))
            cv.restore()
    if TRAY_DOWN <= t:
        cv.drawRect(skia.Rect(360, 1300, 450, 1330), P(C("c0c4cc"))); cv.drawRect(skia.Rect(360, 1300, 450, 1330), P(INK, stroke=4))

# ---------------------------------------------------------------- overlays
def banner(cv, t, t0, dur, title, l1, l2=None, col="3ccf5a"):
    if not (t0 <= t < t0 + dur): return
    q = min(1, (t - t0) / 0.25, (t0 + dur - t) / 0.25)
    y = lerp(-120, 150, ease_out_back(min(1, (t - t0) / 0.3), 1.4))
    a = q
    r = skia.RRect.MakeRectXY(skia.Rect(460, y - 90, 1460, y + 110), 36, 36)
    cv.drawRRect(r, P(C("000000", 0.35 * a), blur=16)); cv.drawRRect(r, P(C("f4f6fa", 0.97 * a))); cv.drawRRect(r, P(INK, stroke=4))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(490, y - 60, 590, y + 40), 22, 22), P(C(col, a)))
    text(cv, "$", 540, y + 20, 64, C("ffffff", a), tf=TF_BLACK)
    text(cv, title, 620, y - 26, 38, C("141414", a), tf=TF_BLACK, align="l")
    text(cv, l1, 620, y + 26, 36, C("333333", a), tf=TF_B, align="l")
    if l2: text(cv, l2, 620, y + 72, 40, C("e8262a" if col != "3ccf5a" else "2e7d4a", a), tf=TF_BLACK, align="l")
    text(cv, "now", 1430, y - 26, 28, C("8a8f99", a), tf=TF_B, align="r")

def statement(cv, t):
    a0, a1 = S(24) + 0.5, E(26) + 0.4
    if not (a0 <= t < a1): return
    k = ease_out_back(min(1, (t - a0) / 0.3), 1.6); a = min(1, (a1 - t) / 0.2)
    cv.save(); cv.translate(960, 500); cv.rotate(-3); cv.scale(k, k)
    page = skia.RRect.MakeRectXY(skia.Rect(-380, -330, 380, 330), 14, 14)
    cv.drawRRect(page, P(C("000000", 0.35 * a), blur=22)); cv.drawRRect(page, P(C("ffffff", a))); cv.drawRRect(page, P(INK, stroke=6))
    cv.drawRect(skia.Rect(-380, -330, 380, -230), P(C("1f4f88", a)))
    text(cv, "SAVINGS STATEMENT", 0, -265, 46, C("ffffff", a), tf=TF_BLACK)
    hl = t >= S(26)
    if hl: cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-340, -190, 340, -120), 14, 14), P(C("fff3a0", a)))
    text(cv, "Account holder:  DANIEL", -320, -140, 40, C("141414", a), tf=TF_BLACK if hl else TF_B, align="l")
    text(cv, "Account type:  Savings", -320, -70, 36, C("555555", a), tf=TF_B, align="l")
    rq = ss(S(25) - 0.1, S(25) + 0.3, t)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-340, 0, 340, 150), 18, 18), P(C("eef6ee", a)))
    text(cv, "BALANCE", 0, 50, 34, C("2e7d4a", a), tf=TF_BLACK)
    cv.save(); cv.translate(0, 125); cv.scale(0.7 + 0.3 * rq, 0.7 + 0.3 * rq)
    text(cv, "$8,000.00", 0, 0, 80, C("2e7d4a", a), tf=TF_BLACK); cv.restore()
    text(cv, "Monthly deposits: 12 • Withdrawals: 0", 0, 230, 30, C("8a8f99", a), tf=TF_B)
    cv.restore()

def card(cv, t, rng, l1, l2=None, big=False):
    if not (rng[0] <= t < rng[1]): return
    a = min(1, (t - rng[0]) / 0.25, (rng[1] - t) / 0.25)
    cv.drawRect(skia.Rect(0, 0, W, H), P(C("101018", a)))
    if big:
        text(cv, "WHEN YOUR BOYFRIEND", 960, 470, 92, C("ffffff", a), tf=TF_BLACK)
        text(cv, "HIDES HIS MONEY", 960, 580, 110, C("ffd21f", a), tf=TF_BLACK)
        if l1: text(cv, l1, 960, 690, 46, C("8fd8ff", a), tf=TF_B)
    else:
        text(cv, l1, 960, 560, 96, C("ffffff", a), tf=TF_BLACK)

def rewind(cv, t):
    if not (REWIND[0] <= t < REWIND[1]): return
    cv.drawRect(skia.Rect(0, 0, W, H), P(C("10131c", 0.35)))
    for j in range(8):
        y = (j * 151 + t * 1800) % H
        cv.drawRect(skia.Rect(0, y, W, y + 8 + 10 * (j % 3)), P(C("ffffff", 0.18)))
    for dx in (-80, 10):
        cv.drawPath(poly([(960 + dx + 70, 470), (960 + dx + 70, 610), (960 + dx - 20, 540)]), P(C("ffffff", 0.95)))

def endcard(cv, t):
    if t < ENDCARD: return
    a = min(1, (t - ENDCARD) / 0.6)
    cv.drawRect(skia.Rect(0, 0, W, H), P(C("0d0f1a")))
    text(cv, "Saving money is wise.", 960, 380, 80, C("ffffff", a), tf=TF_BLACK)
    a2 = min(1, max(0, (t - ENDCARD - 1.2) / 0.6))
    text(cv, "Being honest about your finances is wiser.", 960, 500, 64, C("ffd21f", a2), tf=TF_BLACK)
    a3 = min(1, max(0, (t - ENDCARD - 2.8) / 0.5))
    k = ease_out_back(min(1, max(0, (t - ENDCARD - 2.8) / 0.4)), 2.0)
    cv.save(); cv.translate(960, 700); cv.scale(k, k)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-210, -50, 210, 50), 14, 14), P(C("e8262a", a3)))
    text(cv, "SUBSCRIBE", 0, 20, 52, C("ffffff", a3), tf=TF_BLACK)
    cv.restore()
    text(cv, "for more funny stories with lessons worth remembering", 960, 820, 38, C("c9cbe0", a3), tf=TF_B)

# ---------------------------------------------------------------- captions (landscape)
CAP_Y = 975
def chunks():
    out = []
    for s in SEGS:
        words = s["text"].replace('"', "").split()
        cs, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= 4 or w[-1] in ",.?!…:—":
                cs.append(cur); cur = []
        if cur: cs.append(cur)
        wt = [sum(len(w) + 2 for w in c) for c in cs]; tot = sum(wt); acc = 0
        for c, x in zip(cs, wt):
            out.append((s["start"] + (s["end"] - s["start"]) * acc / tot, s["start"] + (s["end"] - s["start"]) * (acc + x) / tot, c, s["who"], s["i"]))
            acc += x
    return out
CAPS = chunks()
KEY = {"$8,000!", "$8,000?!", "$8,000", "BROKE.", "INVESTMENT.", "WITHDRAW.", "SHY.", "CONFESSED.", "JACKET!", "DANIEL!", "DANIEL?!", "HEADPHONES?", "HEADPHONES.",
       "LIED", "HONEST", "BUSINESS.", "BUSINESS?", "DREAMS", "CREDIT?!", "JOURNEY.", "LEARNING!", "SAFETY", "SAVINGS", "NOTHING?", "SPENDING.", "FUTURE.", "NECESSARY.",
       "EMPTY", "SELFISH.", "SELFISH?", "COMMUNICATE", "AFFORD.", "SURPRISE", "PROUD", "RESPONSIBLE", "MONEY?", "EXPENSE!", "MONTHS.", "TRIP?", "TREES."}
def draw_caption(cv, t):
    for n, (a, b, words, who, i) in enumerate(CAPS):
        nxt = CAPS[n + 1][0] if n + 1 < len(CAPS) else b + 0.4
        if a <= t < min(b + 0.35, nxt):
            k = ease_out_back(min(1, (t - a) / 0.16), 2.2)
            ws = [w.upper() for w in words]
            size = 76; f = skia.Font(TF_BLACK, size); gap = 22
            wid = lambda: sum(f.measureText(w) for w in ws) + gap * (len(ws) - 1)
            if wid() > 1700: size *= 1700 / wid(); f = skia.Font(TF_BLACK, size); gap *= size / 76
            tw = wid()
            jx = 5 * math.sin(t * 50) if i in ANGRY else 0
            cv.save(); cv.translate(960 + jx, CAP_Y); cv.scale(k, k)
            x = -tw / 2
            for w in ws:
                ww = f.measureText(w)
                if w in KEY:
                    r = skia.RRect.MakeRectXY(skia.Rect(x - 10, -size * 0.78, x + ww + 10, size * 0.2), 12, 12)
                    cv.drawRRect(r, P(C("000000"), stroke=10)); cv.drawRRect(r, P(C("e8262a"))); cv.drawString(w, x, 0, f, P(C("ffffff")))
                else:
                    cv.drawString(w, x, 0, f, P(C("000000"), stroke=16))
                    cv.drawString(w, x, 0, f, P(C("ffd21f") if who == "H" else C("ffffff")))
                x += ww + gap
            cv.restore()
            chip(cv, 960, CAP_Y - 110, "SOPHIA" if who == "H" else "DANIEL", a=0.95, col="ffd23f" if who == "H" else "ffffff", fg="1a1a1a", size=28)
            return

# ---------------------------------------------------------------- camera
WIDE_BED = (0.95, 1000, 1080)
WIDE_LIV = (0.95, 1000, 1080)
def cu(x, rise, z=1.7):
    return (z, x + 20, 1000 - 190 * rise)
def G_CU(t, z=1.7):
    x, r = guy_pos(t); return cu(x, r, z)
def H_CU(t, z=1.7):
    p = girl_pos(t); x, r = p if p else (1380, 1); return cu(x, r, z)
def TWO(t, z=1.25):
    gx, gr = guy_pos(t); p = girl_pos(t); hx, hr = p if p else (gx + 400, 1)
    return (z, (gx + hx) / 2, 1060 - 120 * max(gr, hr))
WIDE_LINES = {2, 13, 27, 37, 51, 64}
TWO_LINES = {4, 10, 12, 14, 22, 34, 36, 47, 49, 53, 55, 57, 59, 63, 65, 67, 68, 71, 72}
BIG = {11: 2.0, 12: 2.0, 23: 2.0, 25: 2.0, 26: 2.1, 28: 2.1, 33: 1.9, 43: 1.9, 45: 2.0, 50: 1.9, 58: 1.9, 63: 1.8, 69: 2.1, 70: 1.9}

def camera(t):
    loc = location(t)
    if t < REWIND[0]:
        k = t / REWIND[0]; return (lerp(1.7, 2.1, k), BED_SEAT + 60, 990)
    if CARD0[1] - 0.3 <= t < S(2) - 0.4:
        return WIDE_LIV if t > S(1) else (lerp(0.95, 1.4, ss(CARD0[1], S(1), t)), SEAT_G + 100, 1030)
    if CARD1[1] - 0.2 <= t < S(13): return G_CU(t, 1.8)
    if S(13) <= t < E(13) + 0.9: return G_CU(t, 2.0)
    if CARD2[1] - 0.2 <= t < S(24): return (1.15, 1150, 1080)
    if E(26) <= t < S(27) + 0.2: return WIDE_LIV
    if E(28) <= t < S(29): return G_CU(t, 2.1)
    if SITDOWN[0] <= t < S(51): return (lerp(1.0, 1.3, ss(SITDOWN[0], SITDOWN[1], t)), 1000, 1060)
    if E(57) <= t < S(58): return G_CU(t, lerp(1.7, 2.0, ss(E(57), S(58), t)))
    if HUG - 0.1 <= t < S(69): return TWO(t, 1.5) if t < BUZZ else (2.0, (guy_pos(t)[0] + girl_pos(t)[0]) / 2, 1080)
    if GRAB <= t: return (0.95, 900, 1080)
    i = seg_at(t)
    who = SEGS[i]["who"]
    if i in WIDE_LINES: c = WIDE_LIV if loc == "living" else WIDE_BED
    elif i in TWO_LINES: c = TWO(t)
    else: c = G_CU(t, BIG.get(i, 1.7)) if who == "G" else H_CU(t, BIG.get(i, 1.7))
    q = (t - S(i)) / max(0.1, (S(i + 1) if i + 1 < len(SEGS) else TOTAL) - S(i))
    return (c[0] * (1 + 0.04 * q), c[1], c[2])

def shake(t):
    for i, amt in ((25, 10), (26, 12), (28, 16), (36, 14), (45, 8), (69, 14), (71, 16)):
        if S(i) <= t < S(i) + 0.4:
            d = 1 - (t - S(i)) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    return (0, 0)

def pillow_shape(cv, x, y, rot):
    cv.save(); cv.translate(x, y); cv.rotate(rot)
    r = skia.RRect.MakeRectXY(skia.Rect(-70, -70, 70, 70), 26, 26)
    cv.drawRRect(r, P(C("7ec8a0"))); cv.drawRRect(r, P(INK, stroke=6))
    cv.restore()

def render_frame(cv, t):
    if t >= ENDCARD:
        endcard(cv, t); return
    z, wx, wy = camera(t)
    sx, sy = shake(t)
    wx = min(max(wx, W / 2 / z - 300), WWORLD + 300 - W / 2 / z)
    wy = min(max(wy, H / 2 / z - 800), 2600 - H / 2 / z)
    cv.save(); cv.translate(W / 2 + sx, H / 2 + sy); cv.scale(z, z); cv.translate(-wx, -wy)
    loc = location(t)
    if loc == "bed": bedroom(cv, t)
    else: living_room(cv, t)
    props(cv, t)
    gp = girl_pos(t)
    gx, _ = guy_pos(t)
    us = guy_state(t)
    if gx > -380:
        M.draw_person(cv, t, us, gx, "guy")
        headphones(cv, gx, us)
        if us.get("tray"): tray(cv, gx, us, t)
    if loc == "bed": bed_front(cv); M.draw_person(cv, t, us, gx, "guy"); headphones(cv, gx, us)
    if gp and gp[0] < 2100:
        gs = girl_state(t)
        M.draw_person(cv, t, gs, gp[0], "girl")
        if gs.get("paper"):
            hx, hy = hand_pos(gp[0], gs, "R", True)
            cv.save(); cv.translate(hx - 20, hy - 40); cv.rotate(-8)
            cv.drawRect(skia.Rect(-45, -60, 45, 60), P(C("ffffff"))); cv.drawRect(skia.Rect(-45, -60, 45, 60), P(INK, stroke=4))
            cv.drawRect(skia.Rect(-45, -60, 45, -35), P(C("1f4f88"))); cv.restore()
        if gs.get("pillow"):
            hx, hy = hand_pos(gp[0], gs, "R", True); pillow_shape(cv, hx, hy - 40, 15 * math.sin(t * 12))
    if loc == "bed" and t < E(0) + 1.0 or (CARD1[1] <= t < S(14) and loc == "bed"):
        hx, hy = hand_pos(gx, us, "L")
        cv.drawCircle(hx, hy - 40, 90, P(C("8fd3ff", 0.18), blur=30))
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(960, 540, 1250, [C("000000", 0), C("1a1010", 0.3)], [0.6, 1])))
    # overlays
    banner(cv, t, 0.6, 2.4, "Savings Account", "Congratulations! Your savings", "balance has reached $8,000")
    if t < REWIND[0]:
        a = min(1, max(0, (t - 0.9) / 0.3)) * min(1, (REWIND[0] - t) / 0.2)
        text(cv, "He told her he was BROKE…", 960, 420, 70, C("ffffff", a), tf=TF_BLACK, stroke=12, stroke_col=C("000000", a))
    banner(cv, t, DING2, 3.2, "Savings Account", "Congratulations! Your savings", "balance has reached $8,000")
    banner(cv, t, BUZZ, 3.2, "Payment Reminder", "Your HEADPHONES payment ($450)", "is due TOMORROW", col="e8262a")
    statement(cv, t)
    rewind(cv, t)
    card(cv, t, CARD0, "Earlier that day…", big=True)
    card(cv, t, CARD1, "LATER THAT EVENING")
    card(cv, t, CARD2, "THE NEXT MORNING")
    if not (CARD0[0] <= t < CARD0[1] or CARD1[0] <= t < CARD1[1] or CARD2[0] <= t < CARD2[1]):
        draw_caption(cv, t)
    if BLACK <= t: cv.drawRect(skia.Rect(0, 0, W, H), P(C("000000")))
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
