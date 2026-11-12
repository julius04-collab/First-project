import json, math, os, subprocess, sys
import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
import render as R
from render import C, lerpc, clamp, ss, ease_out_back, P, lin, rad, poly, text, chip, pop, TF_BLACK, TF_XB

W, H, FPS = 1080, 1920, 30
LEAD, TAIL = 0.5, 2.0
SEGS = json.load(open(os.path.join(HERE, "vo.json")))
TOTAL = SEGS[-1]["end"] + LEAD + TAIL
BOUNDS = [0.0] + [SEGS[i]["start"] + LEAD - 0.15 for i in range(1, len(SEGS))] + [TOTAL]

# ---------------------------------------------------------------- captions (reuse stomach module's renderer)
R.SEGS = SEGS
R.LEAD = LEAD
R.DISPLAY = [
    "You've been brushing your teeth wrong your whole life. And mistake number one is something almost everybody does.",
    "Mistake one: you rinse. That foam you spit out is full of fluoride, the stuff that repairs and strengthens your enamel. Rinse with water, and you wash it straight down the sink.",
    "Spit. Don't rinse.",
    "Mistake two: you brush right after breakfast. Orange juice, Zobo, soft drinks. They soften your enamel for up to an hour.",
    "Brush then, and you're scrubbing away your own teeth. Brush before you eat, or wait an hour.",
    "Mistake three: you scrub like you're washing a pot. Hard back-and-forth strokes push your gums back and wear down your enamel.",
    "Tilt the brush toward your gums and use small, gentle circles.",
    "Mistake four: you're done in 45 seconds. The rule is 2 full minutes, twice a day.",
    "Mistake five: you skip your tongue. It's covered in bacteria, and it's a major cause of bad breath.",
    "Mistake six: you've had that toothbrush for a year. Change it every 3 months, or once the bristles start to spread.",
    "And the most important brush of the day? The one before bed. While you sleep, your mouth dries out, and bacteria have all night to attack.",
    "Be honest. How many of these are you guilty of? Drop the number in the comments.",
]
R.KEYS = {"wrong", "rinse.", "rinse", "fluoride,", "enamel.", "enamel", "spit.", "breakfast.", "zobo,", "hour.", "pot.", "gums", "circles.",
          "45", "seconds.", "2", "minutes,", "twice", "tongue.", "bacteria,", "breath.", "year.", "3", "months,", "bed.", "attack.", "guilty", "number", "comments."}
R.CAPS = R.build_captions()

# ---------------------------------------------------------------- helpers
RNG = np.random.default_rng(11)
BUBS = [(RNG.uniform(0, W), RNG.uniform(0, H), RNG.uniform(8, 40), RNG.uniform(0.15, 0.4), RNG.uniform(0, 6.28)) for _ in range(22)]

def bg(cv, t, night=0.0):
    top = lerpc("f2fffb", "0b1530", night)
    mid = lerpc("c9f2e6", "101e45", night)
    bot = lerpc("8fdcc6", "060b1c", night)
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=lin(0, 0, 0, H, [top, mid, bot], [0, 0.55, 1])))
    for (x, y, r, a, ph) in BUBS:
        yy = (y - t * 22 * (r / 20)) % (H + 80) - 40
        xx = x + 20 * math.sin(t * 0.5 + ph)
        cv.drawCircle(xx, yy, r, P(lerpc("ffffff", "7fa0ff", night, a * (1 - 0.5 * night)), stroke=3))
        cv.drawCircle(xx - r * 0.35, yy - r * 0.35, r * 0.18, P(C("ffffff", a)))

def closed_cr(pts, n=16):
    p = list(pts)
    ext = [p[-1]] + p + [p[0], p[1]]
    out = []
    for i in range(1, len(p) + 1):
        p0, p1, p2, p3 = map(np.array, (ext[i - 1], ext[i], ext[i + 1], ext[i + 2]))
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.array(out)

TOOTH_U = closed_cr([(-1.0, 0.25), (-1.07, -0.35), (-0.95, -0.85), (-0.6, -1.08), (-0.25, -0.95), (0, -0.82), (0.25, -0.95), (0.6, -1.08),
                     (0.95, -0.85), (1.07, -0.35), (1.0, 0.25), (0.85, 0.85), (0.72, 1.6), (0.55, 1.92), (0.38, 1.6), (0.22, 0.95), (0, 0.75),
                     (-0.22, 0.95), (-0.38, 1.6), (-0.55, 1.92), (-0.72, 1.6), (-0.85, 0.85)])
PITS = [(RNG.uniform(-0.85, 0.85), RNG.uniform(-0.85, 0.15), RNG.uniform(0.025, 0.06)) for _ in range(40)]

def tooth_path(cx, cy, s):
    return poly([(cx + x * s, cy + y * s) for x, y in TOOTH_U])

def draw_tooth(cv, cx, cy, s, dull=0.0, pits=0.0, shield=0.0, gloss=1.0, roots=True):
    tp = tooth_path(cx, cy, s)
    cv.drawPath(tp, P(lerpc("1d5a63", "000000", 0, 0.25), blur=0.12 * s))
    cv.drawPath(tp, P(0, shader=lin(cx - s, cy - s, cx + s, cy + s,
                                       [lerpc("ffffff", "f3ead2", dull), lerpc("eef7fb", "e6d9b8", dull), lerpc("b9d3e2", "c4b48e", dull)], [0, 0.5, 1])))
    cv.save()
    cv.clipPath(tp, skia.ClipOp.kIntersect, True)
    # root tone below neck
    if roots: cv.drawRect(skia.Rect(cx - 2 * s, cy + 0.35 * s, cx + 2 * s, cy + 2 * s), P(0, shader=lin(0, cy + 0.3 * s, 0, cy + 1.2 * s, [C("f2e2b6", 0.0), C("e8cf8f", 0.95)])))
    if pits > 0:
        for (px, py, pr) in PITS:
            cv.drawOval(skia.Rect(cx + (px - pr) * s, cy + (py - pr * 0.7) * s, cx + (px + pr) * s, cy + (py + pr * 0.7) * s), P(C("a8956a", 0.7 * pits)))
    g = gloss * (1 - dull)
    if g > 0:
        hp = skia.Path()
        hp.moveTo(cx - 0.72 * s, cy - 0.75 * s)
        hp.cubicTo(cx - 0.85 * s, cy - 0.3 * s, cx - 0.8 * s, cy + 0.05 * s, cx - 0.7 * s, cy + 0.2 * s)
        cv.drawPath(hp, P(C("ffffff", 0.95 * g), stroke=0.12 * s, blur=0.03 * s))
        cv.drawCircle(cx - 0.45 * s, cy - 0.82 * s, 0.07 * s, P(C("ffffff", 0.9 * g)))
    cv.restore()
    cv.drawPath(tp, P(lerpc("7fa6ba", "a08a5c", dull), stroke=0.03 * s))
    if shield > 0:
        cv.drawPath(tp, P(C("39c6ff", 0.55 * shield), stroke=0.12 * s, blur=0.08 * s))
        cv.drawPath(tp, P(C("8fe3ff", 0.9 * shield), stroke=0.03 * s))
    return tp

def draw_gum(cv, centers, cy, s, recede=0.0, x0=-40, x1=W + 40, bottom=H + 40, night=0.0):
    xs = np.linspace(x0, x1, 120)
    tops = []
    for x in xs:
        dx = min(abs(x - c) for c in centers) / s
        tops.append(cy + (0.32 + recede) * s - 0.24 * s * (1 - math.exp(-(dx / 0.95) ** 2)))
    pts = [(x0, bottom)] + list(zip(xs, tops)) + [(x1, bottom)]
    gp = poly(pts)
    cv.drawPath(gp, P(C("000000", 0.18), blur=14))
    cv.drawPath(gp, P(0, shader=lin(0, cy, 0, cy + 2.2 * s, [lerpc("ff9fb0", "7a5a8c", night), lerpc("f26d8a", "4a3060", night), lerpc("c9466a", "2a1a40", night)], [0, 0.4, 1])))
    cv.drawPath(poly(list(zip(xs, np.array(tops) + 10)), close=False), P(C("ffd0da", 0.7 * (1 - night * 0.6)), stroke=0.05 * s, blur=3))
    return gp

def bact(cv, x, y, ang, s, a=1.0, t=0.0, col="6bd16b"):
    if a <= 0.01:
        return
    cv.save(); cv.translate(x, y); cv.rotate(math.degrees(ang) + 12 * math.sin(t * 6 + x));
    w = s * (1 + 0.08 * math.sin(t * 9 + y))
    r = skia.RRect.MakeRectXY(skia.Rect(-w * 1.15, -s * 0.55, w * 1.15, s * 0.55), s * 0.55, s * 0.55)
    cv.drawRRect(r, P(C(col, a)))
    cv.drawRRect(r, P(C("2f7a3a", a), stroke=max(1.5, s * 0.12)))
    for e in (-0.35, 0.35):
        cv.drawCircle(w * 0.35 + e * s * 0.6, -s * 0.08, s * 0.2, P(C("ffffff", a)))
        cv.drawCircle(w * 0.38 + e * s * 0.6, -s * 0.06, s * 0.1, P(C("15301a", a)))
    cv.restore()

def draw_brush(cv, x, y, ang, sc=1.0, splay=0.0, dirty=0.0, t=0.0, col=("38d1c2", "1a9e93")):
    cv.save(); cv.translate(x, y); cv.rotate(ang); cv.scale(sc, sc)
    # handle
    hp = skia.Path()
    hp.moveTo(110, -36); hp.cubicTo(300, -40, 450, -30, 720, -52); hp.lineTo(724, -8); hp.cubicTo(450, 4, 300, 0, 110, -4); hp.close()
    cv.drawPath(hp, P(C("000000", 0.25), blur=12))
    cv.drawPath(hp, P(0, shader=lin(0, -50, 0, 0, [C(col[0]), C(col[1])])))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(380, -36, 600, -22), 7, 7), P(C("ffffff", 0.7)))
    head = skia.RRect.MakeRectXY(skia.Rect(-140, -46, 150, -2), 22, 22)
    cv.drawRRect(head, P(C("000000", 0.25), blur=10))
    cv.drawRRect(head, P(0, shader=lin(0, -46, 0, -2, [C(col[0]), C(col[1])])))
    cv.drawLine(-115, -34, 120, -34, P(C("ffffff", 0.45), stroke=6))
    rr = np.random.default_rng(4)
    for i in range(10):
        bx = -122 + i * 27
        a = splay * ((i - 4.5) * 9 + rr.uniform(-14, 14))
        cv.save(); cv.translate(bx, 0); cv.rotate(a)
        L = 82 - splay * rr.uniform(0, 18)
        tuft = skia.RRect.MakeRectXY(skia.Rect(-11, 0, 11, L), 8, 8)
        cc = ("ffffff", "d9f3ff") if i % 2 == 0 else ("8ad8ff", "4fb7ea")
        cv.drawRRect(tuft, P(0, shader=lin(0, 0, 0, L, [C(cc[1]), C(cc[0])])))
        if splay > 0.3:
            for k in range(3):
                cv.drawLine(-6 + k * 6, L * 0.4, -6 + k * 6 + (k - 1) * 10 * splay, L + 6, P(C(cc[0]), stroke=4))
        cv.restore()
    if dirty > 0:
        for j in range(16):
            bx = -120 + (j * 37) % 260
            by = 18 + ((j * 23 + t * 30 * (1 + j % 3)) % 60)
            bact(cv, bx, by, j, 12, a=dirty, t=t, col="9be36b" if j % 2 else "6bd16b")
    cv.restore()

def foam(cv, cx, cy, s, amount, t, seed=1, a=1.0, drift=0.0):
    rr = np.random.default_rng(seed)
    for i in range(int(46 * amount)):
        fx = cx + rr.uniform(-1.1, 1.1) * s + drift * (rr.uniform(0.6, 1.4))
        fy = cy + rr.uniform(-1.25, -0.25) * s + 6 * math.sin(t * 2 + i) + drift * 0.3 * rr.uniform(0, 1)
        r = rr.uniform(0.08, 0.2) * s
        cv.drawCircle(fx, fy, r, P(C("ffffff", 0.92 * a)))
        cv.drawCircle(fx, fy, r, P(C("b8dbe8", 0.8 * a), stroke=3))
        cv.drawCircle(fx - r * 0.35, fy - r * 0.35, r * 0.25, P(C("e8f8ff", a)))

def star(cv, x, y, r, a):
    if a <= 0:
        return
    p = skia.Path()
    for k in range(8):
        ang = k * math.pi / 4
        rr = r if k % 2 == 0 else r * 0.22
        px, py = x + math.cos(ang) * rr, y + math.sin(ang) * rr
        p.moveTo(px, py) if k == 0 else p.lineTo(px, py)
    p.close()
    cv.drawPath(p, P(C("ffffff", a * 0.6), blur=r * 0.25))
    cv.drawPath(p, P(C("ffffff", a)))

def icon(cv, x, y, kind, r=34):
    if kind == "x":
        cv.drawCircle(x, y, r, P(C("ff3b5c")))
        cv.drawLine(x - r * 0.4, y - r * 0.4, x + r * 0.4, y + r * 0.4, P(C("ffffff"), stroke=r * 0.25))
        cv.drawLine(x + r * 0.4, y - r * 0.4, x - r * 0.4, y + r * 0.4, P(C("ffffff"), stroke=r * 0.25))
    else:
        cv.drawCircle(x, y, r, P(C("18b26b")))
        pth = skia.Path(); pth.moveTo(x - r * 0.45, y + r * 0.02); pth.lineTo(x - r * 0.1, y + r * 0.38); pth.lineTo(x + r * 0.5, y - r * 0.35)
        cv.drawPath(pth, P(C("ffffff"), stroke=r * 0.25))

def card(cv, t, pill, lines, kind="x", night=0.0):
    a, k = pop(t, 0.05, 0.5)
    if a <= 0:
        return
    cv.save(); cv.translate(540, 300); cv.scale(k, k); cv.saveLayerAlpha(None, int(a * 255))
    y = -70
    if pill:
        f = skia.Font(TF_BLACK, 50)
        w = f.measureText(pill) + 130
        r = skia.RRect.MakeRectXY(skia.Rect(-w / 2, y - 48, w / 2, y + 48), 48, 48)
        cv.drawRRect(r, P(C("000000", 0.3), blur=12))
        cv.drawRRect(r, P(C("ff3b5c" if kind == "x" else "18b26b")))
        icon(cv, -w / 2 + 50, y, kind, 28) if False else None
        cv.drawCircle(-w / 2 + 48, y, 30, P(C("ffffff")))
        if kind == "x":
            cv.drawLine(-w / 2 + 37, y - 11, -w / 2 + 59, y + 11, P(C("ff3b5c"), stroke=8))
            cv.drawLine(-w / 2 + 59, y - 11, -w / 2 + 37, y + 11, P(C("ff3b5c"), stroke=8))
        else:
            pth = skia.Path(); pth.moveTo(-w / 2 + 35, y + 1); pth.lineTo(-w / 2 + 45, y + 11); pth.lineTo(-w / 2 + 62, y - 10)
            cv.drawPath(pth, P(C("18b26b"), stroke=8))
        text(cv, pill, 30, y + 18, 50, C("ffffff"))
        y += 135
    for i, ln in enumerate(lines):
        text(cv, ln, 0, y + i * 94, 80, C("ffffff"), stroke=12, stroke_col=C("0d2a2e"))
    cv.restore(); cv.restore()

# ---------------------------------------------------------------- scenes
TX, TY, TS = 540, 900, 230

def s1(cv, t, d):
    bg(cv, t)
    shake = 9 * math.sin(t * 37) * (1 - ss(d - 1, d, t))
    cv.save(); cv.translate(shake, 6 * math.cos(t * 29))
    draw_tooth(cv, TX, TY, TS)
    draw_gum(cv, [TX], TY, TS)
    foam(cv, TX, TY, TS * 0.9, ss(0.3, 2.5, t), t, seed=3)
    bx = TX + 150 * math.sin(t * 13)
    draw_brush(cv, bx - 40, TY - 1.05 * TS - 70, 0, 1.0, t=t)
    for i in range(8):
        q = (t * 2.5 + i / 8) % 1
        ang = -math.pi / 2 + (i - 3.5) * 0.35
        cv.drawCircle(bx + math.cos(ang) * 240 * q, TY - 1.0 * TS - 60 + math.sin(ang) * 240 * q + 300 * q * q, 14 * (1 - q) + 4, P(C("ffffff", 0.9 * (1 - q))))
    cv.restore()
    card(cv, t, None, ["YOU'RE DOING", "THIS WRONG"])

FL = [(RNG.uniform(-1.05, 1.05), RNG.uniform(-1.3, -0.3), RNG.uniform(0, 6.28)) for _ in range(34)]

def fluoride_dots(cv, cx, cy, s, t, a=1.0, drift=0.0, settle=0.0):
    for i, (fx, fy, ph) in enumerate(FL):
        x = cx + fx * s + 12 * math.sin(t * 2 + ph) + drift * (0.8 + 0.4 * math.sin(ph))
        y = cy + fy * s + 12 * math.cos(t * 1.7 + ph) + drift * 0.25
        if settle > 0:
            # settle onto the crown outline
            j = int((i / len(FL)) * 0.48 * len(TOOTH_U)) + int(0.02 * len(TOOTH_U))
            j = (j - int(0.05 * len(TOOTH_U))) % len(TOOTH_U)
            tx_, ty_ = cx + TOOTH_U[j][0] * s, cy + TOOTH_U[j][1] * s
            x, y = x + (tx_ - x) * settle, y + (ty_ - y) * settle
        cv.drawCircle(x, y, 22, P(C("39c6ff", 0.45 * a), blur=10))
        cv.drawCircle(x, y, 9, P(C("dff7ff", a)))

def s2(cv, t, d):
    bg(cv, t)
    draw_tooth(cv, TX, TY, TS)
    draw_gum(cv, [TX], TY, TS)
    wash = ss(d * 0.6, d * 0.95, t)
    front = -300 + 1700 * wash
    foam(cv, TX, TY, TS * 0.9, 1.0, t, seed=5, a=1 - ss(0.3, 0.9, wash), drift=900 * wash ** 1.5)
    fluoride_dots(cv, TX, TY, TS, t, a=1 - ss(0.35, 0.9, wash), drift=1000 * wash ** 1.5)
    if 0 < wash < 1:
        pts = [(-50, -50)]
        for y in np.linspace(-50, H + 50, 40):
            pts.append((front + 60 * math.sin(y * 0.012 + t * 6), y))
        pts.append((-50, H + 50))
        wp = poly(pts)
        cv.drawPath(wp, P(C("7fd3ff", 0.35)))
        cv.drawPath(poly(pts[1:-1], close=False), P(C("ffffff", 0.8), stroke=10))
        for i in range(14):
            yy = 340 + i * 85
            cv.drawCircle(front - 40 - (i * 53) % 260, yy + 20 * math.sin(t * 5 + i), 10 + i % 3 * 5, P(C("ffffff", 0.7), stroke=3))
    a, s_ = pop(t, 1.2)
    chip(cv, 820, 1290, "fluoride", a=a * (1 - wash), scale=s_, col="39c6ff", fg="05263a", size=40)
    card(cv, t, "MISTAKE #1", ["RINSING"])

def s3(cv, t, d):
    bg(cv, t)
    sh = ss(0.6, 1.6, t)
    draw_tooth(cv, TX, TY, TS, shield=sh)
    draw_gum(cv, [TX], TY, TS)
    fluoride_dots(cv, TX, TY - 260 * (1 - ss(0, 1.2, t)), TS, t, a=1 - 0.6 * sh, settle=ss(0.1, 1.3, t))
    for k in range(4):
        q = (t * 0.8 + k / 4) % 1
        star(cv, TX - 220 + k * 150, TY - 250 + 80 * math.sin(k * 2), 40 * math.sin(q * math.pi), sh * math.sin(q * math.pi))
    a, s_ = pop(t, 0.9)
    chip(cv, 540, 1310, "fluoride shield", a=a, scale=s_, col="39c6ff", fg="05263a", size=40)
    card(cv, t, "DO THIS", ["SPIT, DON'T RINSE"], kind="check")

def s4(cv, t, d):
    bg(cv, t)
    wave = ss(0.3, 2.3, t)
    dull = ss(1.2, d * 0.85, t)
    draw_tooth(cv, TX, TY, TS, dull=dull, pits=ss(1.6, d * 0.9, t))
    draw_gum(cv, [TX], TY, TS)
    front = -200 + 1600 * wave
    if wave > 0:
        pts = [(-60, -50)]
        for y in np.linspace(-50, H + 50, 40):
            pts.append((front + 70 * math.sin(y * 0.01 + t * 5), y))
        pts.append((-60, H + 50))
        cv.drawPath(poly(pts), P(C("ff9d1a", 0.42 * (1 - 0.5 * ss(2.3, d, t)))))
        cv.drawPath(poly(pts[1:-1], close=False), P(C("ffd27a", 0.9 * (1 - ss(2.0, 2.4, t))), stroke=12))
        for i in range(10):
            cv.drawCircle(min(front, 1100) - 50 - (i * 71) % 300, 300 + i * 110 + 15 * math.sin(t * 4 + i), 8 + i % 3 * 4, P(C("fff1c9", 0.8), stroke=3))
    for i, (lab, col, fg) in enumerate([("Orange juice", "ffb02e", "3a2000"), ("Zobo", "9b1d4a", "ffffff"), ("Soft drinks", "6b3a1f", "ffffff")]):
        a, s_ = pop(t, 1.4 + i * 0.55)
        chip(cv, 830 if i != 1 else 250, 600 + i * 120, lab, a=a, scale=s_, col=col, fg=fg, size=38)
    a, s_ = pop(t, d * 0.65)
    chip(cv, 540, 1310, "softened for up to 1 hour", a=a, scale=s_, col="ffffff", size=38)
    card(cv, t, "MISTAKE #2", ["BRUSHING AFTER", "BREAKFAST"])

def s5(cv, t, d):
    bg(cv, t)
    draw_tooth(cv, TX, TY, TS, dull=1, pits=1)
    draw_gum(cv, [TX], TY, TS)
    bx = TX + 130 * math.sin(t * 7)
    draw_brush(cv, bx - 40, TY - 1.05 * TS - 70, 0, 1.0, t=t)
    for i in range(18):
        q = (t * 1.3 + i / 18) % 1
        sx = TX + ((i * 97) % 300 - 150)
        x = sx + (i % 2 * 2 - 1) * 260 * q
        y = TY - 1.0 * TS - 10 - 260 * q + 520 * q * q
        cv.save(); cv.translate(x, y); cv.rotate(q * 400 + i * 30)
        cv.drawPath(poly([(-10, -6), (8, -9), (11, 5), (-6, 8)]), P(C("f6efdc", 1 - q)))
        cv.drawPath(poly([(-10, -6), (8, -9), (11, 5), (-6, 8)]), P(C("a8956a", 1 - q), stroke=2))
        cv.restore()
    a, s_ = pop(t, d * 0.5)
    chip(cv, 540, 1310, "brush BEFORE you eat", a=a, scale=s_, col="18b26b", fg="ffffff", size=40)
    card(cv, t, "DO THIS", ["WAIT 1 HOUR"], kind="check")

def s6(cv, t, d):
    bg(cv, t)
    rec = 0.42 * ss(0.8, d * 0.9, t)
    draw_tooth(cv, TX, TY, TS)
    draw_gum(cv, [TX], TY, TS, recede=rec)
    by = TY + (0.32 + rec * 0.5) * TS - 70
    bx = TX + 190 * math.sin(t * 9)
    draw_brush(cv, bx - 40, by - 20, 0, 1.0, t=t)
    for k in range(3):
        q = (t * 3 + k / 3) % 1
        cv.drawLine(bx - 300 - 60 * q, by - 60 + k * 40, bx - 200 - 60 * q, by - 60 + k * 40, P(C("ff3b5c", 0.8 * (1 - q)), stroke=8))
        cv.drawLine(bx + 360 + 60 * q, by - 60 + k * 40, bx + 460 + 60 * q, by - 60 + k * 40, P(C("ff3b5c", 0.8 * (1 - q)), stroke=8))
    a, s_ = pop(t, d * 0.45)
    chip(cv, 540, 1310, "gums pull back", a=a, scale=s_, col="ff3b5c", fg="ffffff", size=40)
    card(cv, t, "MISTAKE #3", ["SCRUBBING HARD"])

def s7(cv, t, d):
    bg(cv, t)
    s = 150
    cxs = [TX - 330, TX, TX + 330]
    cy = 930
    for c in cxs:
        draw_tooth(cv, c, cy, s)
    draw_gum(cv, cxs, cy, s)
    px = TX - 300 + 600 * ss(0, d, t)
    ox, oy = 24 * math.cos(t * 7), 24 * math.sin(t * 7)
    gy = cy + 0.32 * s
    draw_brush(cv, px + ox - 30, gy - 120 + oy, -30, 0.85, t=t, col=("7be0b0", "2fa36f"))
    # small circle trail
    cv.drawCircle(px + 20, gy - 30, 46, P(C("ffffff", 0.7), stroke=5))
    a, s_ = pop(t, 0.5)
    chip(cv, 820, 650, "45° to the gums", a=a, scale=s_, col="ffffff", size=38)
    for k in range(3):
        q = (t * 0.9 + k / 3) % 1
        star(cv, TX - 300 + k * 300, cy - 230, 34 * math.sin(q * math.pi), math.sin(q * math.pi))
    card(cv, t, "DO THIS", ["GENTLE CIRCLES"], kind="check")

def hourglass(cv, x, y, sc, prog, t):
    cv.save(); cv.translate(x, y); cv.scale(sc, sc)
    glass = skia.Path()
    glass.moveTo(-120, -230); glass.cubicTo(-120, -80, -18, -40, -18, 0); glass.cubicTo(-18, 40, -120, 80, -120, 230)
    glass.lineTo(120, 230); glass.cubicTo(120, 80, 18, 40, 18, 0); glass.cubicTo(18, -40, 120, -80, 120, -230); glass.close()
    cv.drawPath(glass, P(C("ffffff", 0.35)))
    cv.save(); cv.clipPath(glass, skia.ClipOp.kIntersect, True)
    top_lvl = -200 + 190 * prog
    cv.drawRect(skia.Rect(-130, top_lvl, 130, 0), P(0, shader=lin(0, -200, 0, 0, [C("ffd27a"), C("f0a830")])))
    pile = 225 - 170 * prog
    pp = skia.Path(); pp.moveTo(-130, 232); pp.lineTo(-130, 232 - (232 - pile) * 0.35); pp.quadTo(0, pile - 30, 130, 232 - (232 - pile) * 0.35); pp.lineTo(130, 232); pp.close()
    cv.drawPath(pp, P(0, shader=lin(0, pile, 0, 232, [C("ffd27a"), C("e09a20")])))
    if prog < 0.99:
        cv.drawLine(0, 0, 0, pile, P(C("f0a830"), stroke=7))
    cv.restore()
    cv.drawPath(glass, P(C("ffffff", 0.9), stroke=8))
    cv.drawLine(-70, -180, -40, -60, P(C("ffffff", 0.8), stroke=10))
    for yy in (-250, 250):
        r = skia.RRect.MakeRectXY(skia.Rect(-160, yy - 22, 160, yy + 22), 16, 16)
        cv.drawRRect(r, P(C("000000", 0.25), blur=8))
        cv.drawRRect(r, P(0, shader=lin(0, yy - 22, 0, yy + 22, [C("38d1c2"), C("1a9e93")])))
    for xx in (-140, 140):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(xx - 9, -240, xx + 9, 240), 9, 9), P(C("1a9e93")))
    cv.restore()

def s8(cv, t, d):
    bg(cv, t)
    hourglass(cv, 300, 900, 1.15, (t * 0.5) % 1, t)
    draw_tooth(cv, 760, 800, 150, roots=False)
    # 0:45 struck -> 2:00
    a1, s1_ = pop(t, 0.4)
    cv.save(); cv.translate(760, 1340); cv.scale(s1_, s1_); cv.saveLayerAlpha(None, int(a1 * 255 * (1 - ss(d * 0.55, d * 0.65, t))))
    text(cv, "0:45", 0, 30, 110, C("ff3b5c"), stroke=14, stroke_col=C("ffffff"))
    strike = ss(1.0, 1.5, t)
    cv.drawLine(-130, 0, -130 + 260 * strike, -10, P(C("0d2a2e"), stroke=14))
    cv.restore(); cv.restore()
    a2, s2_ = pop(t, d * 0.6)
    cv.save(); cv.translate(760, 1340); cv.scale(s2_, s2_); cv.saveLayerAlpha(None, int(a2 * 255))
    text(cv, "2:00", 0, 30, 130, C("18b26b"), stroke=14, stroke_col=C("ffffff"))
    cv.restore(); cv.restore()
    a3, s3_ = pop(t, d * 0.78)
    chip(cv, 760, 640, "2× a day", a=a3, scale=s3_, col="18b26b", fg="ffffff", size=42)
    card(cv, t, "MISTAKE #4", ["45 SEC → 2 MIN"])

PAP = []
for row in range(9):
    y = 760 + row * (40 + row * 9)
    r = 26 + row * 7
    for k in range(-1, int(W / (r * 1.9)) + 2):
        PAP.append((k * r * 1.9 + (row % 2) * r * 0.95, y, r))
BAC = [(RNG.uniform(0, W), RNG.uniform(780, 1700), RNG.uniform(0, 6.28), RNG.uniform(10, 22)) for _ in range(70)]

def s9(cv, t, d):
    bg(cv, t)
    cv.drawRect(skia.Rect(0, 700, W, H), P(0, shader=lin(0, 700, 0, H, [C("f7a3b4"), C("e26a88")])))
    for (x, y, r) in PAP:
        cv.drawCircle(x, y + r * 0.2, r, P(C("b8405f", 0.35), blur=r * 0.25))
        cv.drawCircle(x, y, r, P(0, shader=rad(x - r * 0.3, y - r * 0.4, r * 1.3, [C("ffd3dc"), C("f48aa2"), C("d75777")])))
    sweep = ss(d * 0.35, d * 0.9, t)
    bxp = -300 + 1700 * sweep
    for (x, y, ph, sz) in BAC:
        sc = (sz / 16) * (0.6 + 0.4 * (y - 700) / 1000)
        a = 1.0 if x > bxp - 60 else max(0.0, 1 - (bxp - 60 - x) / 120)
        dx = 0 if x > bxp - 60 else (bxp - x) * 0.4
        bact(cv, x + 6 * math.sin(t * 2 + ph) - dx, y - dx * 0.2, ph, 16 * sc, a=a, t=t, col="8fdc5a" if int(ph * 10) % 2 else "6bd16b")
    # stink lines
    stink = 1 - sweep
    for k in range(4):
        sp = skia.Path()
        x0 = 220 + k * 210
        q = (t * 0.6 + k * 0.25) % 1
        sp.moveTo(x0, 700 - q * 150)
        for j in range(1, 6):
            sp.lineTo(x0 + 22 * math.sin(j * 1.4 + t * 3), 700 - q * 150 - j * 40)
        cv.drawPath(sp, P(C("7dbb3a", 0.7 * stink * math.sin(q * math.pi)), stroke=10))
    if 0 < sweep < 1:
        draw_brush(cv, bxp, 980, 0, 1.2, t=t)
    a, s_ = pop(t, 1.0)
    chip(cv, 540, 580, "bad breath", a=a * stink, scale=s_, col="7dbb3a", fg="ffffff", size=40)
    card(cv, t, "MISTAKE #5", ["SKIPPING YOUR", "TONGUE"])

def s10(cv, t, d):
    bg(cv, t)
    swap = ss(d * 0.5, d * 0.7, t)
    zoom = 1.6 + 0.2 * ss(0, d * 0.45, t)
    draw_brush(cv, 300 - 2300 * swap, 900, 0, zoom, splay=1.0, dirty=1.0, t=t, col=("b7b29a", "8a856d"))
    if swap > 0:
        nx = 300 + 1100 * (1 - swap)
        draw_brush(cv, nx, 900, 0, 1.6, t=t)
        for k in range(4):
            q = (t * 1.2 + k / 4) % 1
            star(cv, nx - 150 + k * 100, 1040 + 30 * math.sin(k), 30 * math.sin(q * math.pi), swap * math.sin(q * math.pi))
    a, s_ = pop(t, 0.9)
    chip(cv, 540, 1270, "1 year old 🦠" if False else "1 year old", a=a * (1 - swap), scale=s_, col="8a856d", fg="ffffff", size=40)
    a, s_ = pop(t, d * 0.6)
    chip(cv, 540, 1270, "new one every 3 months", a=a, scale=s_, col="18b26b", fg="ffffff", size=40)
    card(cv, t, "MISTAKE #6", ["OLD TOOTHBRUSH"])

NB = [(RNG.uniform(0, 1), RNG.integers(0, 2), RNG.uniform(0, 6.28), RNG.uniform(0, 1)) for _ in range(60)]

def s11(cv, t, d):
    night = ss(0, 0.8, t)
    bg(cv, t, night=night)
    cv.drawCircle(860, 560, 70, P(C("dfe8ff", night), blur=2))
    cv.drawCircle(890, 540, 62, P(lerpc("f2fffb", "0b1530", night)))
    cv.drawCircle(860, 560, 140, P(C("9fb8ff", 0.25 * night), blur=40))
    s = 120
    cxs = [540 - 380, 540 - 127, 540 + 127, 540 + 380]
    upper_y, lower_y = 800, 1230
    dry = ss(0.8, d * 0.6, t)
    for (row_y, flip) in ((upper_y, True), (lower_y, False)):
        cv.save()
        if flip:
            cv.translate(0, row_y); cv.scale(1, -1); cv.translate(0, -row_y)
        for c in cxs:
            draw_tooth(cv, c, row_y, s, gloss=1 - dry * 0.8)
            tp = tooth_path(c, row_y, s)
            cv.drawPath(tp, P(C("7fa0ff", 0.22 * night)))
            cv.drawPath(tp, P(C("bfe0ff", 0.6 * (1 - dry)), stroke=10, blur=4))
        draw_gum(cv, cxs, row_y, s, x0=-40, x1=W + 40, bottom=row_y + 2.8 * s, night=night)
        cv.restore()
    swarm = ss(1.2, d * 0.9, t)
    for i, (u, row, ph, z) in enumerate(NB):
        if z > swarm:
            continue
        x = 40 + u * 1000 + 15 * math.sin(t * 2 + ph)
        gy = (upper_y - 0.32 * s) if row == 0 else (lower_y + 0.32 * s)
        gy += (-1 if row == 0 else 1) * 0 - (20 if row == 1 else -20) + 25 * math.sin(ph * 3)
        cv.drawCircle(x, gy, 30, P(C("7dff6b", 0.25), blur=12))
        bact(cv, x, gy, ph, 13, a=min(1, (swarm - z) * 5), t=t, col="7dff6b")
    a, s_ = pop(t, d * 0.35)
    chip(cv, 540, 1015, "saliva dries up overnight", a=a, scale=s_, col="dfe8ff", fg="0b1530", size=36)
    card(cv, t, "THE MOST IMPORTANT ONE", ["BRUSH BEFORE BED"], kind="check", night=night)

def s12(cv, t, d):
    bg(cv, t)
    k = math.cos(t * 1.4)
    sx = 0.82 + 0.18 * abs(k)
    cv.save(); cv.translate(TX, 860); cv.rotate(6 * math.sin(t * 1.1)); cv.scale(sx, 1); cv.translate(-TX, -860)
    draw_tooth(cv, TX, 860, 210, gloss=1.0, roots=False)
    cv.restore()
    for kk in range(5):
        q = (t * 0.9 + kk / 5) % 1
        star(cv, TX - 260 + (kk * 131) % 520, 600 + (kk * 97) % 420, 46 * math.sin(q * math.pi), math.sin(q * math.pi))
    # numbers 1..6
    for i in range(6):
        a, s_ = pop(t, 1.0 + i * 0.18)
        x = 540 + (i - 2.5) * 150
        cv.save(); cv.translate(x, 1330); cv.scale(s_, s_); cv.saveLayerAlpha(None, int(a * 255))
        cv.drawCircle(0, 0, 58, P(C("000000", 0.25), blur=10))
        cv.drawCircle(0, 0, 58, P(C("ff3b5c")))
        text(cv, str(i + 1), 0, 24, 66, C("ffffff"))
        cv.restore(); cv.restore()
    by = 1250 + 0 * t
    card(cv, t, None, ["HOW MANY ARE YOU", "GUILTY OF?"])
    ya = 520 + 18 * math.sin(t * 6)
    pth = skia.Path(); pth.moveTo(540, ya - 50); pth.lineTo(540, ya + 20); pth.moveTo(505, ya - 10); pth.lineTo(540, ya + 25); pth.lineTo(575, ya - 10)
    a, _ = pop(t, 0.6)
    cv.drawPath(pth, P(C("ff3b5c", a), stroke=16))

SCENES = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12]

def render_frame(cv, t):
    si = max(i for i in range(len(SCENES)) if BOUNDS[i] <= t)
    si = min(si, len(SCENES) - 1)
    SCENES[si](cv, t - BOUNDS[si], BOUNDS[si + 1] - BOUNDS[si])
    XF = 0.3
    if si > 0 and t < BOUNDS[si] + XF:
        a = 1 - (t - BOUNDS[si]) / XF
        cv.saveLayerAlpha(None, int(a * 255))
        SCENES[si - 1](cv, t - BOUNDS[si - 1], BOUNDS[si] - BOUNDS[si - 1])
        cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 900, 1350, [C("000000", 0), C("0d2a2e", 0.28)], [0.6, 1])))
    R.draw_caption(cv, t)
    cv.drawRect(skia.Rect(0, 0, W * t / TOTAL, 10), P(C("ff3b5c")))
    fade = 1 - ss(TOTAL - 0.6, TOTAL, t)
    if t < 0.25:
        fade = min(fade, t / 0.25)
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
        print("bounds", [round(b, 2) for b in BOUNDS])
    else:
        from multiprocessing import Pool
        N = int(math.ceil(TOTAL * FPS)); nw = 4; step = math.ceil(N / nw)
        jobs = [(k, k * step, min(N, (k + 1) * step), os.path.join(HERE, f"part{k}.mp4")) for k in range(nw)]
        with Pool(nw) as p:
            outs = p.map(worker, jobs)
        with open(os.path.join(HERE, "parts.txt"), "w") as f:
            for o in outs:
                f.write(f"file '{o}'\n")
        print("frames", N, "dur", TOTAL)
