import json, math, os, subprocess, sys
import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from render import C, clamp, ss, ease_out_back, P, lin, rad, poly, text, chip, pop, TF_BLACK, TF_B

W, H, FPS = 1080, 1920, 30
D = json.load(open(os.path.join(HERE, "vo.json")))
SEGS, TOTAL = D["segs"], D["total"]
INK, WHITE = C("141414"), C("ffffff")

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

# ------------------------------------------------------------------ living room
def draw_room(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, 1420), P(C("f3d9b8")))
    for i in range(10):
        cv.drawRect(skia.Rect(i * 120 + 50, 0, i * 120 + 62, 1420), P(C("ebcda8")))
    # window with evening sky
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(90, 300, 470, 760), 10, 10), P(C("fff6ea")))
    cv.drawRect(skia.Rect(108, 318, 452, 742), P(0, shader=lin(0, 318, 0, 742, [C("3b2a6b"), C("e0708a"), C("ffb36b")])))
    cv.drawCircle(380, 680, 40, P(C("ffe9a8")))
    cv.drawLine(280, 318, 280, 742, P(C("fff6ea"), stroke=12)); cv.drawLine(108, 530, 452, 530, P(C("fff6ea"), stroke=12))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(90, 300, 470, 760), 10, 10), P(INK, stroke=7))
    # framed heart picture (cheeky)
    cv.drawRect(skia.Rect(640, 380, 860, 560), P(C("ffffff"))); cv.drawRect(skia.Rect(640, 380, 860, 560), P(INK, stroke=7))
    hp = skia.Path(); hp.moveTo(750, 520); hp.cubicTo(680, 470, 700, 410, 750, 450); hp.cubicTo(800, 410, 820, 470, 750, 520)
    cv.drawPath(hp, P(C("ff6b8b")))
    # floor lamp
    cv.drawRect(skia.Rect(948, 620, 960, 1420), P(C("3a3040")))
    cv.drawPath(poly([(890, 620), (1020, 620), (990, 520), (920, 520)]), P(C("ffe2a0")))
    cv.drawPath(poly([(890, 620), (1020, 620), (990, 520), (920, 520)]), P(INK, stroke=6))
    cv.drawCircle(955, 640, 240, P(C("ffe2a0", 0.25), blur=60))
    # plant
    cv.drawPath(poly([(40, 1300), (140, 1300), (125, 1420), (55, 1420)]), P(C("e2725b"))); cv.drawPath(poly([(40, 1300), (140, 1300), (125, 1420), (55, 1420)]), P(INK, stroke=5))
    for a in (-50, -20, 10, 40):
        cv.save(); cv.translate(90, 1300); cv.rotate(a)
        cv.drawOval(skia.Rect(-20, -150, 20, 0), P(C("3fa65a"))); cv.drawOval(skia.Rect(-20, -150, 20, 0), P(INK, stroke=4))
        cv.restore()
    # floor + rug
    cv.drawRect(skia.Rect(0, 1420, W, H), P(C("c99260")))
    for i in range(8):
        cv.drawLine(0, 1460 + i * 64, W, 1460 + i * 64, P(C("b07c4c"), stroke=4))
    cv.drawOval(skia.Rect(80, 1640, 1000, 1900), P(C("6aa1c9"))); cv.drawOval(skia.Rect(80, 1640, 1000, 1900), P(INK, stroke=6))
    cv.drawOval(skia.Rect(160, 1690, 920, 1850), P(C("88b8da")))

def draw_couch_back(cv):
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(90, 1000, 990, 1330), 60, 60), P(C("e46f4a")))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(90, 1000, 990, 1330), 60, 60), P(INK, stroke=7))
    cv.drawLine(540, 1030, 540, 1300, P(C("c9583a"), stroke=6))
    for (x, col) in ((200, "ffd36e"), (880, "7ec8a0")):
        cv.save(); cv.translate(x, 1180); cv.rotate(-8 if x < 540 else 8)
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-80, -80, 80, 80), 30, 30), P(C(col))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-80, -80, 80, 80), 30, 30), P(INK, stroke=6))
        cv.restore()

def draw_couch_front(cv):
    cv.drawOval(skia.Rect(70, 1590, 1010, 1660), P(C("000000", 0.25), blur=14))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(110, 1330, 970, 1440), 30, 30), P(C("f08560")))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(110, 1330, 970, 1440), 30, 30), P(INK, stroke=7))
    cv.drawLine(540, 1340, 540, 1430, P(C("c9583a"), stroke=5))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(90, 1430, 990, 1560), 24, 24), P(C("d4643f")))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(90, 1430, 990, 1560), 24, 24), P(INK, stroke=7))
    for x in (40, 960):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x, 1180, x + 90, 1560), 40, 40), P(C("e46f4a")))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x, 1180, x + 90, 1560), 40, 40), P(INK, stroke=7))
    for x in (130, 950):
        cv.drawRect(skia.Rect(x - 10, 1560, x + 10, 1610), P(C("5a3a24")))

# ------------------------------------------------------------------ characters (reference style)
UP, FO, HEAD_R = 104.0, 100.0, 98.0
SEAT = 1345.0

def ik(sx, sy, tx, ty, outward):
    dx, dy = tx - sx, ty - sy
    d = clamp(math.hypot(dx, dy), 10, UP + FO - 1)
    a = math.atan2(dy, dx)
    al = math.acos(clamp((UP * UP + d * d - FO * FO) / (2 * UP * d), -1, 1))
    c1 = (sx + UP * math.cos(a + al), sy + UP * math.sin(a + al))
    c2 = (sx + UP * math.cos(a - al), sy + UP * math.sin(a - al))
    e = c1 if (c1[0] - sx) * outward + (c1[1] - sy) * 0.3 > (c2[0] - sx) * outward + (c2[1] - sy) * 0.3 else c2
    return e, (sx + d * math.cos(a), sy + d * math.sin(a))

def limb(cv, pts_, w=12):
    pth = skia.Path(); pth.moveTo(*pts_[0])
    for p in pts_[1:]:
        pth.lineTo(*p)
    cv.drawPath(pth, P(INK, stroke=w + 9)); cv.drawPath(pth, P(WHITE, stroke=w))

def grass_blade(cv, x, y, ang, t, wig=1.0, sc=1.0):
    cv.save(); cv.translate(x, y); cv.rotate(ang + 6 * math.sin(t * 7) * wig); cv.scale(sc, sc)
    p = skia.Path(); p.moveTo(0, 0); p.cubicTo(40, -6, 90, -30, 150, -64); p.cubicTo(96, -22, 46, 8, 0, 8); p.close()
    cv.drawPath(p, P(C("6fbf4a"))); cv.drawPath(p, P(INK, stroke=4))
    cv.restore()

def heart(cv, x, y, s, col="ff4f7b"):
    p = skia.Path(); p.moveTo(x, y + 18 * s); p.cubicTo(x - 40 * s, y - 8 * s, x - 24 * s, y - 40 * s, x, y - 20 * s); p.cubicTo(x + 24 * s, y - 40 * s, x + 40 * s, y - 8 * s, x, y + 18 * s)
    cv.drawPath(p, P(C(col))); cv.drawPath(p, P(INK, stroke=4 * s))

def draw_person(cv, t, st, cx, kind):
    cv.save(); cv.translate(cx, 0)
    rise = st.get("rise", 0.0)
    hip_y = SEAT - 18 - st.get("bob", 0) - 200 * rise
    SEATL = hip_y + 18
    lean = math.radians(st.get("lean", 0))
    def rot(x, y):
        return (x * math.cos(lean) - y * math.sin(lean), hip_y + x * math.sin(lean) + y * math.cos(lean))
    girl = kind == "girl"
    wph = st.get("walk", None)
    for i, k in enumerate((-1, 1)):
        sw = math.sin(wph + i * math.pi) if wph is not None else 0.0
        lift = max(0.0, math.cos(wph + i * math.pi)) * 22 if wph is not None else 0.0
        foot = (k * lerp(72, 34, rise) + 46 * sw, 1600 - lift)
        knee = (lerp(k * 62, k * 30 + 26 * sw, rise), lerp(SEATL + 36, (hip_y + 1600) / 2 - lift * 0.5, rise))
        if rise > 0.02:
            limb(cv, [(k * 40, hip_y + 40), knee, foot], 12)
        else:
            limb(cv, [knee, foot], 12)
        sh = skia.RRect.MakeRectXY(skia.Rect(foot[0] - 50 + k * 10, foot[1] - 28, foot[0] + 50 + k * 10, foot[1] + 16), 20, 20)
        cv.drawRRect(sh, P(WHITE)); cv.drawRRect(sh, P(INK, stroke=6))
        cv.drawLine(foot[0] - 44 + k * 10, foot[1] + 4, foot[0] + 44 + k * 10, foot[1] + 4, P(INK, stroke=4))
    if girl:
        dress = poly([(-112, hip_y - 40), (112, hip_y - 40), (138, SEATL + 64 + 40 * rise), (-138, SEATL + 64 + 40 * rise)])
        cv.drawPath(dress, P(C("ffcf3f"))); cv.drawPath(dress, P(INK, stroke=6))
        top = poly([rot(-86, -240), rot(86, -240), rot(108, -10), rot(-108, -10)])
        cv.drawPath(top, P(C("ffcf3f"))); cv.drawPath(top, P(INK, stroke=6))
        for k in (-1, 1):
            a, b = rot(k * 40, -240), rot(k * 52, -290)
            cv.drawLine(a[0], a[1], b[0], b[1], P(INK, stroke=6))
        for (dx, dy) in ((-50, -150), (30, -90), (-20, -40), (60, -190), (70, -30)):
            p = rot(dx, dy); cv.drawCircle(p[0], p[1], 9, P(C("ffffff", 0.85)))
    else:
        shorts = poly([(-114, hip_y - 40), (114, hip_y - 40), (134, SEAT + 58), (8, SEAT + 62), (0, SEAT + 20), (-8, SEAT + 62), (-134, SEAT + 58)])
        cv.drawPath(shorts, P(C("4f7fb0"))); cv.drawPath(shorts, P(INK, stroke=6))
        for k in (-1, 1):
            cuff = poly([(k * 134, SEAT + 40), (k * 8, SEAT + 44), (k * 8, SEAT + 70), (k * 136, SEAT + 66)])
            cv.drawPath(cuff, P(C("6f9fcc"))); cv.drawPath(cuff, P(INK, stroke=5))
        tee = poly([rot(-96, -240), rot(96, -240), rot(114, -10), rot(120, 30), rot(-120, 30), rot(-114, -10)])
        cv.drawPath(tee, P(C("161616"))); cv.drawPath(tee, P(INK, stroke=6))
    shL, shR = rot(-(84 if girl else 94), -224), rot((84 if girl else 94), -224)
    def arm(sh, rel, outward):
        el, hd = ik(sh[0], sh[1], sh[0] + rel[0], sh[1] + rel[1], outward)
        limb(cv, [sh, el, hd], 12)
        if not girl:
            sx, sy = sh[0] + (el[0] - sh[0]) * 0.55, sh[1] + (el[1] - sh[1]) * 0.55
            cv.drawLine(sh[0], sh[1], sx, sy, P(INK, stroke=60)); cv.drawLine(sh[0], sh[1], sx, sy, P(C("161616"), stroke=50))
        cv.drawCircle(hd[0], hd[1], 16, P(WHITE)); cv.drawCircle(hd[0], hd[1], 16, P(INK, stroke=5))
        return hd
    hdL = arm(shL, st["handL"], -1)
    hdR = arm(shR, st["handR"], 1)
    if st.get("phone"):
        hx, hy = hdR if girl else hdL
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(hx - 24, hy - 76, hx + 24, hy + 10), 9, 9), P(C("2b2b38")))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(hx - 18, hy - 70, hx + 18, hy + 2), 5, 5), P(C("8fd3ff")))
        cv.drawCircle(hx, hy, 16, P(WHITE)); cv.drawCircle(hx, hy, 16, P(INK, stroke=5))
    if st.get("grass") == "hand":
        grass_blade(cv, hdR[0] - 6, hdR[1] - 6, -70, t, 0.3, 0.9)
    if st.get("heart"):
        mx, my = (hdL[0] + hdR[0]) / 2, (hdL[1] + hdR[1]) / 2 - 10
        heart(cv, mx, my, 1.1 + 0.1 * math.sin(t * 8))
    neck = rot(0, -240)
    hc = rot(0, -240 - 28 - HEAD_R)
    cv.drawLine(neck[0], neck[1], hc[0], hc[1] + HEAD_R, P(INK, stroke=28)); cv.drawLine(neck[0], neck[1], hc[0], hc[1] + HEAD_R, P(WHITE, stroke=18))
    cv.save(); cv.translate(*hc); cv.rotate(st.get("tilt", 0) + math.degrees(lean) * 0.5)
    if girl:
        pt = skia.Path(); pt.moveTo(40, -80); pt.cubicTo(150, -150, 190, -20, 150, 70 + 8 * math.sin(t * 3)); pt.cubicTo(140, 10, 110, -40, 60, -40); pt.close()
        cv.drawPath(pt, P(C("2a1a14"))); cv.drawPath(pt, P(INK, stroke=5))
    cv.drawCircle(0, 0, HEAD_R, P(WHITE)); cv.drawCircle(0, 0, HEAD_R, P(INK, stroke=8))
    if girl:
        hair = skia.Path(); hair.addArc(skia.Rect(-HEAD_R - 4, -HEAD_R - 6, HEAD_R + 4, HEAD_R), 180, 180)
        hair.lineTo(HEAD_R - 10, -26); hair.quadTo(10, -62, -HEAD_R + 8, -24); hair.close()
        cv.drawPath(hair, P(C("2a1a14"))); cv.drawPath(hair, P(INK, stroke=6))
        cv.drawCircle(52, -80, 16, P(C("ff6b8b"))); cv.drawCircle(52, -80, 16, P(INK, stroke=4))
    else:
        for (x0, c1, x1, y1) in ((-22, -40, -60, -150), (0, 0, 8, -160), (20, 40, 48, -148)):
            h = skia.Path(); h.moveTo(x0, -HEAD_R + 4); h.quadTo(c1, -HEAD_R - 40, x1, y1)
            cv.drawPath(h, P(INK, stroke=7))
    lx, ly = st.get("look", (0, 0))
    eyes = st.get("eyes", "n")
    for ex in (-1, 1):
        ecx, ecy = ex * 36 + lx * 14, -2 + ly * 10
        if st.get("blink") or eyes == "closed":
            cv.drawLine(ecx - 13, ecy, ecx + 13, ecy, P(INK, stroke=6))
        elif eyes == "happy":
            pth = skia.Path(); pth.moveTo(ecx - 16, ecy + 4); pth.quadTo(ecx, ecy - 16, ecx + 16, ecy + 4)
            cv.drawPath(pth, P(INK, stroke=6))
        elif eyes == "wide":
            cv.drawOval(skia.Rect(ecx - 16, ecy - 24, ecx + 16, ecy + 24), P(INK))
            cv.drawCircle(ecx - 4, ecy - 8, 5, P(WHITE))
        else:
            cv.drawOval(skia.Rect(ecx - 12, ecy - 18, ecx + 12, ecy + 18), P(INK))
        if girl and eyes not in ("closed", "happy"):
            for j in range(3):
                cv.drawLine(ecx + ex * (6 + j * 7), ecy - 18, ecx + ex * (10 + j * 9), ecy - 30, P(INK, stroke=4))
        br = st.get("brows", (0, 0))[0 if ex < 0 else 1]
        bp = skia.Path(); bp.moveTo(ecx - 24, ecy - 38 - br * 0.6); bp.quadTo(ecx, ecy - 50 - br, ecx + 24, ecy - 40 - br * 0.6)
        cv.drawPath(bp, P(INK, stroke=6))
    if girl:
        for ex in (-1, 1):
            cv.drawOval(skia.Rect(ex * 58 - 16, 26, ex * 58 + 16, 40), P(C("ff9db0", 0.7)))
    a_ = st.get("amp", 0)
    m = st.get("mouth", "smirk")
    mx, my = 6 + lx * 8, 50
    if a_ > 0.06:
        w, hh = 18 + 8 * a_, 6 + 30 * a_
        cv.drawOval(skia.Rect(mx - w, my - hh * 0.4, mx + w, my + hh * 0.7), P(C("3a0c10"))); cv.drawOval(skia.Rect(mx - w, my - hh * 0.4, mx + w, my + hh * 0.7), P(INK, stroke=5))
    elif m == "smirk":
        p = skia.Path(); p.moveTo(mx - 30, my + 4); p.quadTo(mx + 6, my + 22, mx + 40, my - 8); cv.drawPath(p, P(INK, stroke=6))
    elif m == "flat":
        cv.drawLine(mx - 22, my + 6, mx + 22, my + 6, P(INK, stroke=6))
    elif m == "smile":
        p = skia.Path(); p.moveTo(mx - 30, my); p.quadTo(mx, my + 28, mx + 30, my); cv.drawPath(p, P(INK, stroke=6))
    elif m == "grin":
        p = skia.Path(); p.moveTo(mx - 34, my - 4); p.quadTo(mx, my + 40, mx + 34, my - 4); p.close()
        cv.drawPath(p, P(WHITE)); cv.drawPath(p, P(INK, stroke=6))
    elif m == "o":
        cv.drawOval(skia.Rect(mx - 14, my - 10, mx + 14, my + 22), P(C("3a0c10"))); cv.drawOval(skia.Rect(mx - 14, my - 10, mx + 14, my + 22), P(INK, stroke=5))
    if st.get("grass") == "mouth":
        grass_blade(cv, mx + 30, my + 2, -18, t, 1.0)
    if st.get("grass_fall") is not None:
        q = st["grass_fall"]
        grass_blade(cv, mx + 30 + 40 * q, my + 2 + 600 * q * q, -18 + 200 * q, t, 0)
    if st.get("sweat"):
        dp = skia.Path(); dp.moveTo(104, -50); dp.quadTo(120, -24, 104, -14); dp.quadTo(88, -24, 104, -50)
        cv.drawPath(dp, P(C("8fd8ff"))); cv.drawPath(dp, P(INK, stroke=4))
    cv.restore()
    cv.restore()

# ------------------------------------------------------------------ acting
def guy_state(t):
    st = dict(handL=(-130, -20), handR=(20, 180), look=(0.9, 0.0), brows=(0, 0), mouth="smirk", grass="mouth", tilt=0, lean=0)
    st["bob"] = 2 * math.sin(t * 1.4)
    if t < S(1):
        st["look"] = (0.2, 0.0) if t < 2.2 else (0.9, 0.0)
        if t > 4.0:
            st["brows"] = (2, 12)
    if S(1) <= t < S(3):
        st["brows"] = (-6, 14); st["tilt"] = 6; st["look"] = (0.9, -0.1)
    if S(3) - 0.5 <= t:
        take = ss(S(3) - 0.5, S(3) - 0.15, t)
        st["grass"] = "hand" if t > S(3) - 0.3 else "mouth"
        st["handR"] = lerp2((20, 180), (-50, -120), take) if t < S(3) - 0.05 else (70, 60)
    if S(3) <= t < E(3) + 0.3:
        st["eyes"] = "wide"; st["brows"] = (18, 18); st["lean"] = -5; st["handR"] = (150, -60)
    if S(4) <= t < S(5):
        st["eyes"] = "wide" if t < S(4) + 2 else "n"; st["brows"] = (14, 14); st["lean"] = -8; st["look"] = (1.0, -0.1)
    if S(5) <= t < S(6):
        st["handR"] = (150 + 25 * math.sin(t * 5), -50); st["brows"] = (4, 10); st["tilt"] = 4; st["lean"] = 2
    if S(6) - 0.6 <= t < S(7):
        st["handR"] = (160, -110); st["brows"] = (8, 8); st["look"] = (0.4, 0.0); st["lean"] = -10; st["tilt"] = -6
        st["mouth"] = "flat"
    if S(7) <= t:
        st["handR"] = (70, 60); st["lean"] = 0; st["tilt"] = 0; st["mouth"] = "flat"; st["eyes"] = "n"
        st["look"] = (1.0, -0.2) if t < E(7) + 1.2 else (0.0, 0.0)
        st["brows"] = (16, 4)
    if t >= E(7) + 1.3:
        st["tilt"] = -8; st["brows"] = (2, 18); st["sweat"] = False
    st["amp"] = amp("G", t)
    st["blink"] = (t % 3.9) < 0.12 or (E(7) + 2.3 < t < E(7) + 2.5)
    return st

def girl_state(t):
    st = dict(handL=(-30, 180), handR=(40, 170), look=(-1.0, 0.0), brows=(0, 0), mouth="smile", tilt=0, lean=0, phone=False)
    st["bob"] = 2 * math.sin(t * 1.4 + 1)
    if t < S(1):
        st["handR"] = (-70, -60); st["handL"] = (-40, -60) if False else (-30, 180); st["brows"] = (8, 8); st["tilt"] = 6; st["look"] = (-1.0, -0.2)
    if S(2) <= t < E(2) + 0.4:
        st["handR"] = (-60, 60); st["handL"] = (60, 60); st["eyes"] = "n"; st["brows"] = (14, 2); st["tilt"] = 10; st["mouth"] = "smile"
    if S(3) <= t < S(4):
        st["brows"] = (6, 6); st["mouth"] = "flat"
    if S(4) <= t < S(5):
        k = t - S(4)
        st["brows"] = (-8, -8); st["lean"] = -4
        if k < 1.6:
            st["handR"] = (-70, -10)
        elif k < 3.4:
            st["handR"] = (170, -120 + 12 * math.sin(t * 9)); st["handL"] = (-150, -100)
        else:
            st["handR"] = (110, -150); st["handL"] = (-110, -150)
    if S(5) <= t < S(7):
        st["brows"] = (-10, -10); st["mouth"] = "flat"; st["handR"] = (40, 170)
    if S(6) + 0.8 <= t < S(7):
        st["eyes"] = "wide"; st["mouth"] = "o"; st["brows"] = (16, 16)
    if S(7) - 0.2 <= t:
        rise = ss(S(7) - 0.2, S(7) + 0.5, t)
        st["rise"] = rise; st["brows"] = (-12, -12); st["handR"] = (-80, 60); st["handL"] = (80, 60); st["mouth"] = "flat"; st["eyes"] = "n"
    if t >= E(7) + 0.2:
        st["walk"] = (t - E(7)) * 9
        st["look"] = (1.0, 0.0)
    st["amp"] = amp("H", t)
    st["blink"] = (t % 4.3) < 0.12
    return st

GX, GIRLX = 340.0, 740.0

def camera(t):
    if t < 1.0:
        return lerp(1.0, 1.05, t), 540, 1130
    if S(3) <= t < E(3) + 0.3:
        return 1.6, GX + 40, 1040
    if S(4) + 1.6 <= t < S(5):
        return 1.6, GIRLX - 40, 1040
    if S(6) <= t < S(7) - 0.2:
        return 1.75, GX + 30, 1020
    if S(7) - 0.2 <= t < E(7) + 1.3:
        return 1.1, 560, 1120
    if t >= E(7) + 1.3:
        return lerp(1.1, 1.9, ss(E(7) + 1.3, E(7) + 2.0, t)), lerp(560, GX + 20, ss(E(7) + 1.3, E(7) + 2.0, t)), 1010
    return 1.12, 540, 1120

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
            if w > 960:
                f = skia.Font(TF_BLACK, 80 * 960 / w); w = f.measureText(s)
            cv.save(); cv.translate(540, 1745); cv.scale(k, k)
            cv.drawString(s, -w / 2, 28, f, P(C("000000"), stroke=16))
            cv.drawString(s, -w / 2, 28, f, P(C("ffd23f") if who == "H" else C("ffffff")))
            cv.restore()
            chip(cv, 540, 1640, "HER" if who == "H" else "HIM", a=0.95, col="ffd23f" if who == "H" else "ffffff", fg="1a1a1a", size=30)
            return

def draw_top(cv, t):
    lines = ["When she's looking for trouble:", "\"If I go to hell, would you follow me?\""]
    f = skia.Font(TF_B, 44)
    w = max(f.measureText(s) for s in lines) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 300), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    for i, s in enumerate(lines):
        text(cv, s, 540, 212 + i * 60, 44, C("111111"), tf=TF_B)
    te = E(7) + 2.0
    if t > te:
        a, k = pop(t, te, 0.45)
        chip(cv, 540, 400, "WAS HE WRONG?", a=a, scale=k, col="ffd23f", fg="1a1a1a", size=60)

def render_frame(cv, t):
    z, wx, wy = camera(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-wx, -wy)
    draw_room(cv, t)
    draw_couch_back(cv)
    draw_couch_front(cv)
    gx = GIRLX + (700 * ss(E(7) + 0.2, E(7) + 1.6, t) if t > E(7) + 0.2 else 0)
    draw_person(cv, t, girl_state(t), gx, "girl")
    draw_person(cv, t, guy_state(t), GX, "guy")
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("2a1a10", 0.35)], [0.6, 1])))
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
