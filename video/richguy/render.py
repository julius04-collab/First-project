import json, math, os, subprocess, sys
import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from render import C, lerpc, clamp, ss, ease_out_back, P, lin, rad, poly, text, chip, pop, TF_BLACK, TF_B

W, H, FPS = 1080, 1920, 30
TOTAL = 30.0
SEGS = json.load(open(os.path.join(HERE, "vo.json")))
INK = C("141414")
WHITE = C("ffffff")

def lerp(a, b, t):
    return a + (b - a) * t

def lerp2(p, q, t):
    return (lerp(p[0], q[0], t), lerp(p[1], q[1], t))

def seg_t(i):
    return SEGS[i]["start"]

def amp(t):
    for s in SEGS:
        if s["start"] <= t < s["end"]:
            j = int((t - s["start"]) * FPS)
            if j < len(s["env"]):
                return s["env"][j]
    return 0.0

# ------------------------------------------------------------------ park at sunset
RNG = np.random.default_rng(4)

def draw_park(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, 1250), P(0, shader=lin(0, 0, 0, 1250, [C("3b2a6b"), C("b5508a"), C("f78c55"), C("ffcf7a")], [0, 0.35, 0.7, 1])))
    # sun
    cv.drawCircle(560, 1080, 230, P(C("ffe9a8", 0.35), blur=60))
    cv.drawCircle(560, 1080, 120, P(C("fff1c4")))
    # soft clouds
    for (cx, cy, s) in ((200, 380, 1.0), (820, 520, 0.8), (480, 700, 0.6)):
        for k in range(4):
            cv.drawOval(skia.Rect(cx + k * 70 * s - 100 * s, cy - 30 * s + (k % 2) * 14, cx + k * 70 * s + 60 * s, cy + 30 * s + (k % 2) * 14), P(C("ffb08a", 0.55)))
    # distant hills + tree silhouettes
    hill = skia.Path(); hill.moveTo(0, 1180)
    for x in range(0, W + 60, 60):
        hill.lineTo(x, 1150 + 30 * math.sin(x * 0.008) + 20 * math.sin(x * 0.021))
    hill.lineTo(W, 1300); hill.lineTo(0, 1300); hill.close()
    cv.drawPath(hill, P(C("7a3a6a")))
    for tx, sc in ((90, 1.2), (250, 0.8), (870, 1.1), (1010, 0.9), (720, 0.6)):
        base = 1200
        cv.drawRect(skia.Rect(tx - 10 * sc, base - 200 * sc, tx + 10 * sc, base), P(C("4a2448")))
        for k in range(5):
            cv.drawCircle(tx + (k - 2) * 40 * sc, base - 230 * sc - (k % 2) * 50 * sc, 70 * sc, P(C("5a2a55")))
    # grass field
    cv.drawRect(skia.Rect(0, 1250, W, H), P(0, shader=lin(0, 1250, 0, H, [C("c2803f"), C("7e8a3c"), C("4f6a2c")], [0, 0.35, 1])))
    cv.drawRect(skia.Rect(0, 1250, W, 1290), P(C("ffcf7a", 0.25)))
    # path
    pth = poly([(470, 1250), (610, 1250), (900, H), (180, H)])
    cv.drawPath(pth, P(0, shader=lin(0, 1250, 0, H, [C("e8b07a"), C("b98a5e")])))
    # grass tufts
    for i in range(70):
        x, y = RNG.uniform(0, W), RNG.uniform(1300, H)
        if 300 < x < 780 and y < 1500:
            continue
        h = 14 + (y - 1300) * 0.05
        sw = 4 * math.sin(t * 1.3 + i)
        for d in (-8, 0, 8):
            cv.drawLine(x + d, y, x + d * 1.4 + sw, y - h, P(C("3f5a24", 0.8), stroke=4))
    # lamp post (right)
    cv.drawRect(skia.Rect(930, 640, 946, 1460), P(C("2a2030")))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(904, 590, 972, 660), 14, 14), P(C("2a2030")))
    cv.drawCircle(938, 630, 70, P(C("ffe9a8", 0.25), blur=20))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(914, 604, 962, 650), 8, 8), P(C("fff1c4")))
    # birds
    for k in range(3):
        bx = (150 + t * 40 + k * 120) % (W + 200) - 100
        by = 300 + k * 50 + 10 * math.sin(t * 3 + k)
        fl = 10 * math.sin(t * 9 + k)
        b = skia.Path(); b.moveTo(bx - 22, by - fl); b.quadTo(bx - 10, by - 6, bx, by); b.quadTo(bx + 10, by - 6, bx + 22, by - fl)
        cv.drawPath(b, P(C("3a2440"), stroke=5))

def draw_bench_back(cv):
    # backrest behind the guy
    for k in range(3):
        y = 1150 + k * 58
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(170, y, 910, y + 42), 10, 10), P(C("a8642e")))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(170, y, 910, y + 42), 10, 10), P(INK, stroke=6))
        cv.drawLine(190, y + 14, 890, y + 14, P(C("c98a4e"), stroke=4))
    for x in (230, 850):
        cv.drawRect(skia.Rect(x - 14, 1120, x + 14, 1420), P(C("2a2030")))
        cv.drawRect(skia.Rect(x - 14, 1120, x + 14, 1420), P(INK, stroke=5))

def draw_bench_front(cv):
    cv.drawOval(skia.Rect(150, 1610, 930, 1680), P(C("1a1020", 0.35), blur=14))
    # seat slats
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(150, 1400, 930, 1446), 10, 10), P(C("b8733a")))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(150, 1400, 930, 1446), 10, 10), P(INK, stroke=6))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(140, 1440, 940, 1476), 10, 10), P(C("9a5a26")))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(140, 1440, 940, 1476), 10, 10), P(INK, stroke=6))
    for x in (200, 880):
        leg = poly([(x - 18, 1476), (x + 18, 1476), (x + 26, 1640), (x - 26, 1640)])
        cv.drawPath(leg, P(C("2a2030"))); cv.drawPath(leg, P(INK, stroke=5))
        cv.drawRect(skia.Rect(x - 40, 1630, x + 40, 1648), P(C("2a2030")))

# ------------------------------------------------------------------ the guy (reference style)
UP, FO = 112.0, 108.0
HEAD_R = 105.0

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
    cv.drawPath(pth, P(INK, stroke=w + 9))
    cv.drawPath(pth, P(WHITE, stroke=w))

def grass_blade(cv, x, y, ang, t, wig=1.0):
    cv.save(); cv.translate(x, y); cv.rotate(ang + 6 * math.sin(t * 7) * wig)
    p = skia.Path(); p.moveTo(0, 0); p.cubicTo(40, -6, 90, -30, 150, -64); p.cubicTo(96, -22, 46, 8, 0, 8); p.close()
    cv.drawPath(p, P(C("6fbf4a"))); cv.drawPath(p, P(INK, stroke=4))
    cv.drawLine(10, 3, 120, -46, P(C("9be07a"), stroke=3))
    cv.restore()

def draw_guy(cv, t, st):
    """st: dict with handL, handR (rel to shoulders), look, brows (L,R raise), mouth, tilt, lean, grass ('mouth'|'hand'|None), blink"""
    cv.save(); cv.translate(540, 0)
    seat = 1405.0
    hip_y = seat - 20
    lean = math.radians(st.get("lean", 0))
    bob = st.get("bob", 0)
    def rot(x, y):  # y relative to hip, up negative
        return (x * math.cos(lean) - y * math.sin(lean), hip_y - bob + x * math.sin(lean) + y * math.cos(lean))
    # legs (sitting, front view): shorts over thighs, shins to the ground
    for k in (-1, 1):
        knee = (k * 70, seat + 30)
        foot = (k * 82, 1640)
        limb(cv, [knee, foot], 13)
        sh = skia.RRect.MakeRectXY(skia.Rect(foot[0] - 56 + k * 10, foot[1] - 30, foot[0] + 56 + k * 10, foot[1] + 18), 22, 22)
        cv.drawRRect(sh, P(WHITE)); cv.drawRRect(sh, P(INK, stroke=6))
        cv.drawLine(foot[0] - 50 + k * 10, foot[1] + 6, foot[0] + 50 + k * 10, foot[1] + 6, P(INK, stroke=4))
        for j in range(3):
            cv.drawLine(foot[0] - 12 + j * 10 + k * 10, foot[1] - 28, foot[0] - 4 + j * 10 + k * 10, foot[1] - 14, P(INK, stroke=3))
    shorts = poly([(-120, hip_y - 40), (120, hip_y - 40), (140, seat + 58), (8, seat + 62), (0, seat + 20), (-8, seat + 62), (-140, seat + 58)])
    cv.drawPath(shorts, P(C("4f7fb0"))); cv.drawPath(shorts, P(INK, stroke=6))
    for k in (-1, 1):
        cuff = poly([(k * 140, seat + 40), (k * 8, seat + 44), (k * 8, seat + 70), (k * 142, seat + 66)])
        cv.drawPath(cuff, P(C("6f9fcc"))); cv.drawPath(cuff, P(INK, stroke=5))
    cv.drawLine(0, hip_y - 40, 0, seat + 20, P(C("3a6290"), stroke=4))
    # torso: oversized black tee
    tee = poly([rot(-100, -250), rot(100, -250), rot(120, -10), rot(125, 30), rot(-125, 30), rot(-120, -10)])
    cv.drawPath(tee, P(C("161616"))); cv.drawPath(tee, P(INK, stroke=6))
    nk = rot(0, -250)
    cv.drawArc(skia.Rect(nk[0] - 34, nk[1] - 22, nk[0] + 34, nk[1] + 22), 0, 180, False, P(C("3a3a3a"), stroke=6))
    shL, shR = rot(-98, -232), rot(98, -232)
    def arm(sh, rel, outward):
        el, hd = ik(sh[0], sh[1], sh[0] + rel[0], sh[1] + rel[1], outward)
        limb(cv, [sh, el, hd], 13)
        # oversized sleeve
        sx, sy = sh[0] + (el[0] - sh[0]) * 0.55, sh[1] + (el[1] - sh[1]) * 0.55
        cv.drawLine(sh[0], sh[1], sx, sy, P(INK, stroke=62))
        cv.drawLine(sh[0], sh[1], sx, sy, P(C("161616"), stroke=52))
        cv.drawCircle(hd[0], hd[1], 17, P(WHITE)); cv.drawCircle(hd[0], hd[1], 17, P(INK, stroke=5))
        return hd
    hdL = arm(shL, st["handL"], -1)
    hdR = arm(shR, st["handR"], 1)
    if st.get("grass") == "hand":
        grass_blade(cv, hdR[0] - 6, hdR[1] - 6, -70, t, 0.3)
    if st.get("heart"):
        pass
    # neck + head
    neck = rot(0, -250)
    hc = rot(0, -250 - 30 - HEAD_R)
    cv.drawLine(neck[0], neck[1], hc[0], hc[1] + HEAD_R, P(INK, stroke=30))
    cv.drawLine(neck[0], neck[1], hc[0], hc[1] + HEAD_R, P(WHITE, stroke=20))
    cv.save(); cv.translate(*hc); cv.rotate(st.get("tilt", 0) + math.degrees(lean) * 0.5)
    cv.drawCircle(0, 0, HEAD_R, P(WHITE)); cv.drawCircle(0, 0, HEAD_R, P(INK, stroke=8))
    for (x0, c1, x1, y1) in ((-22, -40, -60, -150), (0, 0, 8, -160), (20, 40, 48, -148)):
        h = skia.Path(); h.moveTo(x0, -HEAD_R + 4); h.quadTo(c1, -HEAD_R - 40, x1, y1 + 20 * math.sin(t * 2 + x0) * 0.1)
        cv.drawPath(h, P(INK, stroke=7))
    lx, ly = st.get("look", (0, 0))
    blink = st.get("blink", 0)
    for ex in (-1, 1):
        cx, cy = ex * 38 + lx * 14, -2 + ly * 10
        if blink > 0.5:
            cv.drawLine(cx - 13, cy, cx + 13, cy, P(INK, stroke=6))
        else:
            cv.drawOval(skia.Rect(cx - 12, cy - 18, cx + 12, cy + 18), P(INK))
        br = st.get("brows", (0, 0))[0 if ex < 0 else 1]
        bp = skia.Path(); bp.moveTo(cx - 24, cy - 38 - br * 0.6); bp.quadTo(cx, cy - 50 - br, cx + 24, cy - 40 - br * 0.6 + ex * 2)
        cv.drawPath(bp, P(INK, stroke=6))
    a_ = st.get("amp", 0)
    m = st.get("mouth", "smirk")
    mx, my = 10 + lx * 8, 50
    if a_ > 0.06:
        w, hh = 18 + 8 * a_, 6 + 30 * a_
        cv.drawOval(skia.Rect(mx - w, my - hh * 0.4, mx + w, my + hh * 0.7), P(C("3a0c10")))
        cv.drawOval(skia.Rect(mx - w, my - hh * 0.4, mx + w, my + hh * 0.7), P(INK, stroke=5))
    elif m == "smirk":
        p = skia.Path(); p.moveTo(mx - 30, my + 4); p.quadTo(mx + 6, my + 22, mx + 40, my - 8)
        cv.drawPath(p, P(INK, stroke=6))
    elif m == "flat":
        cv.drawLine(mx - 22, my + 6, mx + 22, my + 6, P(INK, stroke=6))
    elif m == "smile":
        p = skia.Path(); p.moveTo(mx - 30, my); p.quadTo(mx, my + 26, mx + 30, my)
        cv.drawPath(p, P(INK, stroke=6))
    if st.get("grass") == "mouth":
        grass_blade(cv, mx + 30, my + 2, -18, t, 1.0)
    cv.restore()
    cv.restore()
    return hdL, hdR

# ------------------------------------------------------------------ acting timeline
def acting(t):
    s = [seg_t(i) for i in range(9)]
    st = dict(handL=(40, 210), handR=(-40, 210), look=(-0.8, -0.2), brows=(0, 0), mouth="smirk", tilt=0, lean=0, grass="mouth")
    # resting: left arm on the bench back, right hand on knee
    st["handL"] = (-120, -10)
    st["handR"] = (-10, 200)
    st["bob"] = 2 * math.sin(t * 1.5)
    if t > 1.6:
        st["look"] = lerp2((-0.8, -0.2), (0, 0), ss(1.6, 2.1, t)); st["brows"] = (0, 14 * ss(1.8, 2.2, t))
    # take the grass out (2.3-2.9)
    take = ss(2.2, 2.6, t) * (1 - ss(26.9, 27.3, t + 0) if False else 1)
    if 2.2 <= t < 27.7:
        st["grass"] = "hand" if t > 2.55 else "mouth"
        st["handR"] = lerp2((-10, 200), (-60, -130), ss(2.2, 2.5, t)) if t < 2.8 else st["handR"]
        if t >= 2.8:
            st["handR"] = (60, 40)  # holding grass casually
    gest = None
    def k(a, d=0.3):
        return ss(a, a + d, t)
    if s[0] <= t < s[1]:
        st["handR"] = lerp2((60, 40), (150, -60), k(s[0])); st["brows"] = (8, 14); st["tilt"] = 4
    if s[1] <= t < s[2]:
        st["handR"] = (-70, -10); st["tilt"] = -4; st["brows"] = (2, 6)
    if s[2] <= t < s[3]:
        st["handR"] = (110, -130 + 10 * math.sin(t * 6)); st["tilt"] = 6 * math.sin(t * 3); st["brows"] = (6, 6)
    if s[3] <= t < s[4]:
        st["handR"] = (40, 60); st["look"] = (0.2, -0.6); st["mouth"] = "smile"; st["brows"] = (10, 10)
    if s[4] <= t < s[5]:
        st["handR"] = (150, -20); st["handL"] = (-120, -10); st["brows"] = (2, 18); st["mouth"] = "smirk"; st["lean"] = -3
    if s[5] <= t < s[6]:
        st["handR"] = (170, -60); st["handL"] = (-150, -60) if t > s[5] + 0.4 else st["handL"]; st["tilt"] = 10; st["brows"] = (16, 4); st["lean"] = 3
    if s[6] <= t < s[7]:
        o = math.sin(min(1, (t - s[6]) / 0.4) * math.pi / 2)
        st["handR"] = lerp2((60, 40), (190, -110), o); st["handL"] = lerp2((-120, -10), (-190, -110), o); st["brows"] = (14, 14); st["tilt"] = -6
    if s[7] <= t < s[8] - 0.3:
        st["handR"] = (150 + 30 * math.sin(t * 8), -80); st["handL"] = (-150, -60); st["brows"] = (10, 2); st["tilt"] = 8
    if t >= s[8] - 0.3:
        st["handR"] = (60, 40); st["handL"] = (-120, -10); st["brows"] = (2, 16); st["tilt"] = -8; st["mouth"] = "flat"; st["look"] = (0, 0)
    if t >= 27.7:
        put = ss(27.7, 28.1, t)
        st["handR"] = lerp2((60, 40), (-60, -130), math.sin(math.pi * put)) if put < 1 else (-10, 200)
        st["grass"] = "mouth" if t > 27.95 else "hand"
        st["mouth"] = "flat"; st["brows"] = (0, 12); st["tilt"] = -8; st["look"] = (0, 0)
    # blinks
    st["blink"] = 1.0 if (t % 3.7) < 0.12 or (28.6 < t < 28.9) else 0.0
    st["amp"] = amp(t)
    return st

def camera(t):
    s8 = seg_t(8)
    if t < 2.0:
        z = lerp(1.0, 1.06, ss(0, 2.0, t)); return z, 540, 1100
    if t >= s8 - 0.1:
        return 2.05, 540, 1020
    if seg_t(5) <= t < seg_t(6):
        return 1.45, 540, 1130
    z = 1.12 + 0.05 * ss(2.0, s8, t)
    return z, 540, 1150

CAP_CHUNKS = []
for s in SEGS:
    words = s["text"].split()
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 3 or w[-1] in ",.?!…":
            chunks.append(cur); cur = []
    if cur:
        chunks.append(cur)
    wt = [sum(len(w) + 1 for w in c) for c in chunks]; tot = sum(wt); acc = 0
    for c, x in zip(chunks, wt):
        CAP_CHUNKS.append((s["start"] + (s["end"] - s["start"]) * acc / tot, s["start"] + (s["end"] - s["start"]) * (acc + x) / tot, " ".join(c)))
        acc += x

def draw_caption(cv, t):
    for (a, b, txt) in CAP_CHUNKS:
        if a <= t < b + 0.1:
            k = ease_out_back((t - a) / 0.2, 2.0)
            s = txt.upper()
            f = skia.Font(TF_BLACK, 80); w = f.measureText(s)
            if w > 960:
                f = skia.Font(TF_BLACK, 80 * 960 / w); w = f.measureText(s)
            cv.save(); cv.translate(540, 1740); cv.scale(k, k)
            cv.drawString(s, -w / 2, 28, f, P(C("000000"), stroke=16))
            cv.drawString(s, -w / 2, 28, f, P(C("ffffff")))
            cv.restore()
            return

EMOJI = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf") if os.path.exists("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf") else None

def draw_top(cv, t):
    lines = ["POV: You found out", "he's actually rich"]
    f = skia.Font(TF_B, 50)
    w = max(f.measureText(s) for s in lines) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 300), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    for i, s in enumerate(lines):
        text(cv, s, 540, 214 + i * 62, 50, C("111111"), tf=TF_B)
    if t > 27.9:
        a, k = pop(t, 27.9, 0.45)
        chip(cv, 540, 400, "WHO'S WRONG HERE?", a=a, scale=k, col="ffd23f", fg="1a1a1a", size=58)

def render_frame(cv, t):
    z, wx, wy = camera(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-wx, -wy)
    draw_park(cv, t)
    draw_bench_back(cv)
    draw_bench_front(cv)
    draw_guy(cv, t, acting(t))
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("2a0a20", 0.4)], [0.6, 1])))
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
