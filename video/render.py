import json, math, os, subprocess, sys
import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
LEAD = 0.5
SEGS = json.load(open(os.path.join(HERE, "..", "tts", "vo_af_heart.json")))
TAIL = 2.2
TOTAL = SEGS[-1]["end"] + LEAD + TAIL

FONT_DIR = "/usr/share/fonts/opentype/inter/"
TF_BLACK = skia.Typeface.MakeFromFile(FONT_DIR + "Inter-Black.otf")
TF_XB = skia.Typeface.MakeFromFile(FONT_DIR + "Inter-ExtraBold.otf")
TF_B = skia.Typeface.MakeFromFile(FONT_DIR + "Inter-Bold.otf")

# ---------------------------------------------------------------- helpers
def C(h, a=1.0):
    h = h.lstrip("#")
    return skia.ColorSetARGB(int(max(0, min(1, a)) * 255), int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

def lerpc(h1, h2, t, a=1.0):
    h1, h2 = h1.lstrip("#"), h2.lstrip("#")
    c = [int(int(h1[i:i+2], 16) * (1 - t) + int(h2[i:i+2], 16) * t) for i in (0, 2, 4)]
    return skia.ColorSetARGB(int(a * 255), *c)

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def ss(a, b, x):
    t = clamp((x - a) / (b - a)) if b != a else float(x >= a)
    return t * t * (3 - 2 * t)

def ease_out_back(t, k=1.7):
    t = clamp(t) - 1
    return 1 + t * t * ((k + 1) * t + k)

def P(color, stroke=None, blur=None, shader=None, cap=skia.Paint.kRound_Cap):
    p = skia.Paint(AntiAlias=True)
    p.setColor(color)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if shader is not None:
        if color == 0:
            p.setColor(skia.ColorSetARGB(255, 255, 255, 255))
        p.setShader(shader)
    return p

def lin(x0, y0, x1, y1, cols, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], cols, pos)

def rad(x, y, r, cols, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(x, y), max(r, 0.01), cols, pos)

def poly(pts, close=True):
    path = skia.Path()
    pts = [skia.Point(float(x), float(y)) for x, y in pts]
    if len(pts) > 1:
        path.addPoly(pts, close)
    return path

def text(cv, s, x, y, size, color, tf=TF_BLACK, align="c", stroke=0, stroke_col=None, alpha=1.0):
    f = skia.Font(tf, size)
    w = f.measureText(s)
    if align == "c":
        x -= w / 2
    elif align == "r":
        x -= w
    if stroke:
        cv.drawString(s, x, y, f, P(stroke_col if stroke_col is not None else C("000000", alpha), stroke=stroke))
    cv.drawString(s, x, y, f, P(color))
    return w

def crsample(pts, n=30):
    p = np.array(pts, float)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    ts = np.linspace(0, 1, n, endpoint=False)
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in ts:
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(p[-2])
    return np.array(out)

class Tube:
    def __init__(self, pts, n=30):
        self.c = crsample(pts, n)
        d = np.linalg.norm(np.diff(self.c, axis=0), axis=1)
        self.length = d.sum()
        self.s = np.concatenate([[0], np.cumsum(d)]) / self.length
        tg = np.gradient(self.c, axis=0)
        tg /= np.linalg.norm(tg, axis=1)[:, None]
        self.t = tg
        self.n = np.stack([-tg[:, 1], tg[:, 0]], 1)

    def prof(self, ss_, vals):
        return np.interp(self.s, ss_, vals)

    def outline(self, wl, wr, a=0.0, b=1.0):
        m = (self.s >= a) & (self.s <= b)
        L = self.c[m] + self.n[m] * wl[m][:, None]
        R = self.c[m] - self.n[m] * wr[m][:, None]
        return poly(np.vstack([L, R[::-1]]))

    def at(self, s):
        x = np.interp(s, self.s, self.c[:, 0])
        y = np.interp(s, self.s, self.c[:, 1])
        i = int(np.clip(np.searchsorted(self.s, s), 0, len(self.s) - 1))
        return x, y, self.t[i], self.n[i]

    def line(self, a, b, off=None):
        m = (self.s >= a) & (self.s <= b)
        pts = self.c[m]
        if off is not None:
            pts = pts + self.n[m] * off[m][:, None]
        return poly(pts, close=False)

def gauss(x, s):
    return np.exp(-(x / s) ** 2)

RNG = np.random.default_rng(7)
BOKEH = [(RNG.uniform(0, W), RNG.uniform(0, H), RNG.uniform(6, 26), RNG.uniform(0.03, 0.10), RNG.uniform(0, 6.28)) for _ in range(28)]

def bg(cv, t, warm=0.0):
    c1 = lerpc("3b1642", "5a2236", warm)
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 820, 1250, [c1, C("1a0b26"), C("0c0616")], [0, 0.6, 1])))
    for (x, y, r, a, ph) in BOKEH:
        yy = (y - t * 14 * (r / 15)) % (H + 60) - 30
        xx = x + 18 * math.sin(t * 0.4 + ph)
        cv.drawCircle(xx, yy, r, P(C("ffc2d6", a), blur=r * 0.5))

# --------------------------------------------------------------- stomach
ST_PTS = [(0.10, -3.9), (0.12, -2.9), (0.55, -1.75), (0.9, -0.45), (0.7, 0.75), (0.0, 1.4),
          (-0.9, 1.45), (-1.65, 1.05), (-2.15, 0.8), (-2.6, 1.0), (-2.8, 1.8)]
ST_S = [0.00, 0.10, 0.17, 0.27, 0.42, 0.58, 0.70, 0.78, 0.84, 1.00]
ST_WO = [0.30, 0.32, 1.05, 1.45, 1.40, 1.18, 0.78, 0.36, 0.30, 0.30]
ST_WI = [0.30, 0.30, 0.32, 0.50, 0.78, 0.85, 0.62, 0.36, 0.30, 0.30]

def make_stomach(ox, oy, S):
    return Tube([(ox + x * S, oy + y * S) for x, y in ST_PTS], 30)

def stomach_widths(tb, S, inflate=1.0, waves=()):
    m = tb.prof([0, 0.12, 0.2, 0.74, 0.82, 1], [0, 0, 1, 1, 0, 0])
    f = 1 - (1 - inflate) * m
    wo = tb.prof(ST_S, ST_WO) * S * f
    wi = tb.prof(ST_S, ST_WI) * S * f
    for (pos, amp) in waves:
        k = 1 - amp * gauss(tb.s - pos, 0.045) * m
        wo, wi = wo * k, wi * k
    return wo, wi

def draw_stomach(cv, tb, S, inflate=1.0, rugae=1.0, waves=(), content=None, alpha=1.0, glow=0.0, t=0.0):
    wo, wi = stomach_widths(tb, S, inflate, waves)
    th = 0.17 * S
    outer = tb.outline(wi, wo)
    li, lo = np.maximum(wi - th, 2.0), np.maximum(wo - th, 2.0)
    lumen = tb.outline(li, lo)
    xs, ys = tb.c[:, 0], tb.c[:, 1]
    x0, x1, y0, y1 = xs.min() - 2 * S, xs.max() + 2 * S, ys.min(), ys.max() + 1.5 * S
    if alpha < 1:
        cv.saveLayerAlpha(None, int(alpha * 255))
    cv.drawPath(outer, P(C("05010a", 0.55), blur=0.35 * S))
    if glow > 0:
        cv.drawPath(outer, P(C("ffd36e", 0.5 * glow), blur=0.4 * S))
    cv.drawPath(outer, P(0, shader=lin(x0, y0, x1, y1, [C("ff9a86"), C("f0607a"), C("c23b62")], [0, 0.55, 1])))
    cv.drawPath(lumen, P(0, shader=lin(x0, y0, x1, y1, [C("7a1f45"), C("4e1032")])))
    cv.save()
    cv.clipPath(lumen, skia.ClipOp.kIntersect, True)
    if rugae > 0.02:
        for k, u in enumerate((0.22, 0.5, 0.78)):
            off = li - u * (li + lo)
            zig = rugae * 0.11 * S * np.sin(tb.s * 70 + k * 1.7)
            cv.drawPath(tb.line(0.18, 0.79, off + zig), P(C("c94a72", 0.55 * min(1, rugae + 0.3)), stroke=0.07 * S))
    if content:
        content(cv, tb, lumen, (x0, x1, y0, y1), li, lo)
    cv.restore()
    cv.drawPath(lumen, P(C("ffb0bd", 0.45), stroke=0.035 * S))
    hl = -wo * 0.62
    cv.drawPath(tb.line(0.2, 0.5, hl), P(C("ffffff", 0.33), stroke=0.09 * S, blur=0.03 * S))
    cv.drawPath(outer, P(C("8f2448", 0.9), stroke=0.045 * S))
    if alpha < 1:
        cv.restore()
    return lumen, li, lo

GRAINS = [(RNG.uniform(-1, 1), RNG.uniform(-1, 1), RNG.uniform(0, 3.14), RNG.choice(["ffb347", "ff9a3c", "ffd27a", "e8692e"]), RNG.uniform(0.7, 1.2)) for _ in range(140)]
CHUNKS = [(RNG.uniform(-1, 1), RNG.uniform(-1, 1), RNG.uniform(0, 3.14), RNG.uniform(0.8, 1.3)) for _ in range(14)]

def draw_grain(cv, x, y, ang, col, L, a=1.0):
    cv.save()
    cv.translate(x, y)
    cv.rotate(math.degrees(ang))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-L, -L * 0.36, L, L * 0.36), L * 0.36, L * 0.36), P(C(col, a)))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-L * 0.6, -L * 0.25, L * 0.2, -L * 0.05), L * 0.1, L * 0.1), P(C("ffffff", 0.35 * a)))
    cv.restore()

def draw_chicken(cv, x, y, ang, sz, a=1.0):
    cv.save()
    cv.translate(x, y)
    cv.rotate(math.degrees(ang))
    r = skia.Rect(-sz, -sz * 0.62, sz, sz * 0.62)
    cv.drawRRect(skia.RRect.MakeRectXY(r, sz * 0.5, sz * 0.5), P(0, shader=lin(0, -sz, 0, sz, [C("d9965a", a), C("9c5a2c", a)])))
    for k in (-0.45, 0.0, 0.45):
        cv.drawLine(k * sz - 0.2 * sz, -0.4 * sz, k * sz + 0.2 * sz, 0.4 * sz, P(C("5a2e14", 0.75 * a), stroke=sz * 0.13))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-sz * 0.7, -sz * 0.5, sz * 0.1, -sz * 0.3), sz * 0.1, sz * 0.1), P(C("ffe2b8", 0.45 * a)))
    cv.restore()

def food_content(level, t, chunk=1.0, paste=0.0, jitter=0.0, S=150):
    """level: 0..1 fill height of stomach bounding box (from bottom)."""
    def fn(cv, tb, lumen, box, li, lo):
        x0, x1, y0, y1 = box
        bottom = tb.c[:, 1].max() + 1.2 * S
        top = bottom - level * (bottom - (tb.c[:, 1].min() + 2.3 * S))
        pts = [(x0, bottom + 50)]
        for x in np.linspace(x0, x1, 40):
            pts.append((x, top + 9 * math.sin(x * 0.02 + t * 3) * (1 + jitter * 2)))
        pts.append((x1, bottom + 50))
        surf = poly(pts)
        cv.drawPath(surf, P(0, shader=lin(0, top, 0, bottom, [lerpc("d9531f", "ff8c2e", paste), lerpc("8a2a12", "e8681e", paste)])))
        cv.save()
        cv.clipPath(surf, skia.ClipOp.kIntersect, True)
        cx, cy, sw, sh = (x0 + x1) / 2, (top + bottom) / 2, (x1 - x0) / 2, max(20, (bottom - top) / 2)
        if chunk > 0.02:
            for i, (gx, gy, ga, col, gl) in enumerate(GRAINS):
                jx = jitter * 22 * math.sin(t * 5 + i)
                jy = jitter * 22 * math.cos(t * 4.3 + i * 1.3)
                draw_grain(cv, cx + gx * sw + jx, cy + gy * sh + jy, ga + jitter * t * (i % 3 - 1), col, 0.12 * S * gl * chunk, a=min(1, chunk * 1.4))
            for i, (gx, gy, ga, gs) in enumerate(CHUNKS):
                jx = jitter * 30 * math.sin(t * 3.5 + i * 2)
                jy = jitter * 30 * math.cos(t * 3.1 + i)
                draw_chicken(cv, cx + gx * sw * 0.8 + jx, cy + gy * sh * 0.8 + jy, ga + jitter * t * 0.7, 0.2 * S * gs * chunk, a=min(1, chunk * 1.4))
        if paste > 0:
            cv.drawPath(surf, P(C("ff9a3a", paste * 0.85)))
            for i in range(10):
                bx = cx + sw * math.sin(i * 2.3 + t * 0.7) * 0.8
                by = cy + sh * math.cos(i * 1.7 + t * 0.6) * 0.6
                cv.drawCircle(bx, by, 0.06 * S, P(C("ffd08a", 0.35 * paste), blur=4))
        cv.restore()
        cv.drawPath(poly(pts[1:-1], close=False), P(C("ffd08a", 0.6), stroke=4))
    return fn

# --------------------------------------------------------------- UI chips
def chip(cv, x, y, label, a=1.0, scale=1.0, col="ffffff", fg="2a0f2e", size=40):
    if a <= 0.01:
        return
    f = skia.Font(TF_XB, size)
    w = f.measureText(label) + 56
    h = size * 1.75
    cv.save()
    cv.translate(x, y)
    cv.scale(scale, scale)
    cv.saveLayerAlpha(None, int(a * 255))
    r = skia.RRect.MakeRectXY(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), h / 2, h / 2)
    cv.drawRRect(r, P(C("000000", 0.35), blur=10))
    cv.drawRRect(r, P(C(col)))
    text(cv, label, 0, size * 0.36, size, C(fg), tf=TF_XB)
    cv.restore()
    cv.restore()

def pop(t, t0, dur=0.45):
    if t < t0:
        return 0.0, 0.0
    return clamp((t - t0) / 0.18), ease_out_back((t - t0) / dur)

# --------------------------------------------------------------- scenes
def scene1(cv, t, d):
    # spoon approach then oesophagus tunnel
    split = d * 0.42
    if t < split + 0.5:
        bg(cv, t, warm=1.0)
        u = ss(0, split, t)
        sc = 1.0 + 2.2 * u ** 2.2
        cx, cy = 540, 980 - 60 * u
        cv.save()
        cv.translate(cx, cy)
        cv.scale(sc, sc)
        cv.rotate(-12 + 6 * u)
        # handle
        hp = skia.Path()
        hp.moveTo(60, 80); hp.cubicTo(140, 260, 200, 420, 240, 760)
        cv.drawPath(hp, P(C("000000", 0.35), stroke=58, blur=14))
        cv.drawPath(hp, P(0, stroke=46, shader=lin(0, 80, 240, 760, [C("eef1f7"), C("8f97a8"), C("d9dde6")])))
        cv.drawOval(skia.Rect(-215, -40, 215, 150), P(C("000000", 0.4), blur=18))
        cv.drawOval(skia.Rect(-210, -50, 210, 140), P(0, shader=lin(-210, -50, 210, 140, [C("ffffff"), C("a9b0bf"), C("e6e9ef")])))
        cv.drawOval(skia.Rect(-185, -35, 185, 120), P(0, shader=lin(0, -35, 0, 120, [C("7d8596"), C("cfd4dd")])))
        # rice mound
        mound = skia.Path(); mound.addOval(skia.Rect(-185, -150, 185, 95))
        cv.save(); cv.clipPath(mound, skia.ClipOp.kIntersect, True)
        cv.drawOval(skia.Rect(-185, -150, 185, 95), P(0, shader=lin(0, -150, 0, 95, [C("f2862e"), C("c4451c")])))
        rr = np.random.default_rng(3)
        for i in range(120):
            gx, gy = rr.uniform(-180, 180), rr.uniform(-150, 90)
            draw_grain(cv, gx, gy, rr.uniform(0, 3.14), rr.choice(["ffb347", "ff9a3c", "ffcf75", "e8692e", "d9481c"]), 17)
        cv.restore()
        draw_chicken(cv, 55, -95, -0.35, 92)
        cv.drawCircle(-90, -60, 9, P(C("3fa34d")))
        cv.drawCircle(-40, -120, 7, P(C("3fa34d")))
        # steam
        for k in range(3):
            sp = skia.Path()
            bx = -70 + k * 70
            ph = t * 2 + k
            sp.moveTo(bx, -170)
            for j in range(1, 8):
                sp.lineTo(bx + 18 * math.sin(ph + j * 0.9), -170 - j * 32)
            cv.drawPath(sp, P(C("ffffff", 0.22 * (1 - u)), stroke=12, blur=5))
        cv.restore()
    if t > split - 0.1:
        # iris into tunnel
        k = ss(split - 0.1, split + 0.5, t)
        R = 1300 * k
        clip = skia.Path(); clip.addCircle(540, 900, max(1, R))
        cv.save(); cv.clipPath(clip, skia.ClipOp.kIntersect, True)
        tt = t - split
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("2a0618")))
        speed = 1.6
        rings = []
        for i in range(26):
            z = ((i * 0.35 - tt * speed) % (26 * 0.35)) + 0.25
            rings.append(z)
        # actual draw: farthest (largest z) last so small rings sit on top
        for z in sorted(rings):
            r = 520 / z
            if r > 2400:
                continue
            ox = 540 + 30 * math.sin(z * 1.3 + tt * 2)
            oy = 900 + 24 * math.cos(z * 1.1 + tt * 1.7)
            depth = clamp((z - 0.25) / 8.5)
            col = lerpc("ff8c8f", "3a0820", depth ** 0.6)
            dark = lerpc("c9405f", "22030f", depth ** 0.6)
            cv.drawCircle(ox, oy, r, P(0, shader=rad(ox, oy - r * 0.1, r, [dark, col], [0.82, 1.0])))
        # bolus ahead
        bz = 2.6 + 0.4 * math.sin(tt * 1.5)
        br = 520 / bz * 0.32
        bx, by = 540 + 10 * math.sin(tt * 2), 930
        cv.drawCircle(bx, by + br * 0.2, br * 1.1, P(C("000000", 0.4), blur=br * 0.3))
        cv.drawCircle(bx, by, br, P(0, shader=rad(bx - br * 0.3, by - br * 0.4, br * 1.4, [C("ffb04a"), C("e0571d"), C("8c2a10")])))
        rr = np.random.default_rng(5)
        for i in range(26):
            a_ = rr.uniform(0, 6.28); d_ = rr.uniform(0, 0.85) * br
            draw_grain(cv, bx + math.cos(a_) * d_, by + math.sin(a_) * d_, rr.uniform(0, 3), rr.choice(["ffcf75", "ffb347"]), br * 0.09)
        cv.drawCircle(bx - br * 0.35, by - br * 0.4, br * 0.22, P(C("ffffff", 0.35), blur=br * 0.08))
        cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 900, 1100, [C("000000", 0), C("000000", 0.55)], [0.5, 1])))
        cv.restore()

def scene2(cv, t, d):
    bg(cv, t)
    S = 150
    tb = make_stomach(560, 960, S)
    drop = ss(0.2, 1.6, t)
    infl = 0.62 + 0.38 * ss(1.4, d * 0.85, t)
    level = 0.12 + 0.5 * ss(1.5, d * 0.85, t)
    content = food_content(level * ss(1.3, 1.8, t), t, chunk=1.0, S=S) if t > 1.3 else None
    lumen, li, lo = draw_stomach(cv, tb, S, inflate=infl, rugae=1.25 - infl, content=content, t=t)
    if t < 1.9:
        s = 0.02 + 0.5 * drop ** 1.6
        x, y, tg, n = tb.at(s)
        cv.save()
        cv.clipPath(lumen, skia.ClipOp.kIntersect, True)
        r = 0.32 * S * (1 + 0.4 * ss(0.4, 1.0, drop))
        cv.drawCircle(x, y, r, P(0, shader=rad(x - r * 0.3, y - r * 0.4, r * 1.4, [C("ffb04a"), C("e0571d"), C("8c2a10")])))
        draw_chicken(cv, x + r * 0.2, y - r * 0.1, 0.4, r * 0.45)
        cv.restore()
    # size chips
    a1, s1 = pop(t, 1.2)
    a2, s2 = pop(t, d * 0.55)
    chip(cv, 300, 520, "✊ fist-sized", a=a1 * (1 - ss(d * 0.5, d * 0.55, t)), scale=s1, size=42)
    chip(cv, 300, 520, "stretches to 1 L+", a=a2, scale=s2, col="ffd36e", size=42)

PITS = np.linspace(80, 1000, 9)

def scene3(cv, t, d):
    bg(cv, t)
    surf_y = 1080
    ph1, ph2, ph3 = d * 0.30, d * 0.62, d
    # liquid region tint
    cv.drawRect(skia.Rect(0, 0, W, surf_y), P(0, shader=lin(0, 300, 0, surf_y, [C("5a1a2c", 0.0), C("ffb347", 0.10)])))
    # floating rice
    for i, (gx, gy, ga, col, gl) in enumerate(GRAINS[:22]):
        x = 540 + gx * 470 + 20 * math.sin(t * 0.8 + i)
        y = 640 + gy * 260 + 15 * math.cos(t * 0.6 + i)
        draw_grain(cv, x, y, ga + t * 0.2 * (i % 2 - 0.5), col, 26 * gl)
    # acid droplets rising from pits
    acid_on = ss(0.3, 1.2, t)
    for k, px in enumerate(PITS):
        for j in range(3):
            cyc = ((t * 0.45 + k * 0.37 + j / 3) % 1.0)
            if t < 0.3 + j * 0.4:
                continue
            y = surf_y - 20 - cyc * 520
            x = px + 30 * math.sin(cyc * 6 + k)
            r = 13 + 9 * math.sin(k + j)
            mucus_hit = 0
            a = acid_on * (1 - cyc) ** 0.5 * (1 - 0.6 * ss(ph1, ph1 + 1, t))
            cv.drawCircle(x, y, r * 1.9, P(C("d8ff4a", 0.25 * a), blur=10))
            cv.drawCircle(x, y, r, P(C("d8ff4a", 0.9 * a)))
            cv.drawCircle(x - r * 0.3, y - r * 0.35, r * 0.3, P(C("ffffff", 0.7 * a)))
    # acid pool glow around rice
    cv.drawRect(skia.Rect(0, surf_y - 260, W, surf_y), P(0, shader=lin(0, surf_y - 260, 0, surf_y, [C("c8f03c", 0), C("c8f03c", 0.22 * acid_on)])))
    # tissue with cells
    regen = ss(ph2, ph3 - 0.6, t)
    cells = 14
    cw = W / (cells - 1)
    tis = skia.Path()
    tis.moveTo(-20, H)
    tis.lineTo(-20, surf_y)
    for i in range(cells):
        cx = i * cw
        local = clamp((regen * (cells + 3) - i) / 3)
        sc = 1 - 0.55 * math.sin(local * math.pi)
        tis.quadTo(cx - cw / 2, surf_y - 70 * sc, cx, surf_y)
    tis.lineTo(W + 20, surf_y); tis.lineTo(W + 20, H); tis.close()
    cv.drawPath(tis, P(C("000000", 0.4), blur=20))
    cv.drawPath(tis, P(0, shader=lin(0, surf_y - 80, 0, H, [C("ff9a9a"), C("e05272"), C("8e2148")], [0, 0.3, 1])))
    for i in range(cells):
        cx = i * cw - cw / 2
        local = clamp((regen * (cells + 3) - i) / 3)
        flash = math.sin(local * math.pi)
        cv.drawCircle(cx, surf_y - 10, 18, P(C("8e2148", 0.55)))
        if flash > 0.01:
            cv.drawCircle(cx, surf_y - 25, 60, P(C("fff2a8", 0.6 * flash), blur=22))
    # pits
    for px in PITS:
        cv.drawOval(skia.Rect(px - 26, surf_y + 20, px + 26, surf_y + 52), P(C("4a0b26")))
        cv.drawOval(skia.Rect(px - 26, surf_y + 20, px + 26, surf_y + 52), P(C("ffb0bd", 0.5), stroke=3))
    # deeper cell texture
    for i in range(40):
        x = (i * 137) % W
        y = surf_y + 120 + (i * 71) % 600
        cv.drawCircle(x, y, 30 + (i % 4) * 6, P(C("ffb0c0", 0.10), stroke=4))
    # mucus layer
    mu = ss(ph1, ph1 + 1.4, t)
    if mu > 0:
        th = 95 * mu
        mp = skia.Path()
        mp.moveTo(-20, surf_y + 30)
        for x in np.linspace(-20, W + 20, 30):
            mp.lineTo(x, surf_y - 60 - th + 10 * math.sin(x * 0.012 + t * 1.5))
        mp.lineTo(W + 20, surf_y + 30); mp.close()
        cv.drawPath(mp, P(0, shader=lin(0, surf_y - 60 - th, 0, surf_y, [C("dff6ff", 0.55 * mu), C("9fd8ff", 0.25 * mu)])))
        hp = skia.Path()
        for i, x in enumerate(np.linspace(-20, W + 20, 30)):
            y = surf_y - 60 - th + 10 * math.sin(x * 0.012 + t * 1.5) + 14
            hp.moveTo(x, y) if i == 0 else hp.lineTo(x, y)
        cv.drawPath(hp, P(C("ffffff", 0.75 * mu), stroke=7, blur=1.5))
        # acid beads bouncing off
        if t > ph1 + 0.8:
            for k in range(6):
                cyc = ((t - ph1) * 0.7 + k / 6) % 1.0
                x0 = 120 + k * 170
                top = surf_y - 60 - th - 12
                if cyc < 0.5:
                    y = 420 + (top - 420) * (cyc / 0.5) ** 2
                    x = x0
                else:
                    q = (cyc - 0.5) / 0.5
                    y = top - 160 * math.sin(q * math.pi) * (1 - q * 0.5)
                    x = x0 + 120 * q
                a = mu * (1 - ss(ph2, ph2 + 0.8, t))
                cv.drawCircle(x, y, 26, P(C("d8ff4a", 0.25 * a), blur=10))
                cv.drawCircle(x, y, 15, P(C("d8ff4a", 0.95 * a)))
                if abs(cyc - 0.5) < 0.06:
                    cv.drawCircle(x, top + 5, 40, P(C("ffffff", 0.5 * a), stroke=4))
    # metal bolt dissolving (phase 1)
    ba = ss(0.8, 1.3, t) * (1 - ss(ph1 + 0.2, ph1 + 0.8, t))
    if ba > 0:
        dis = ss(1.2, ph1 + 0.3, t)
        cv.save(); cv.translate(820, 380); cv.saveLayerAlpha(None, int(ba * 255))
        cv.drawCircle(0, 0, 150, P(C("d8ff4a", 0.12), blur=30))
        cut = skia.Path(); cut.addRect(skia.Rect(-200, -200 + 330 * dis, 200, 200))
        cv.save(); cv.clipPath(cut, skia.ClipOp.kIntersect, True)
        cv.rotate(20)
        cv.drawRect(skia.Rect(-18, -40, 18, 120), P(0, shader=lin(-18, 0, 18, 0, [C("c7ccd6"), C("6f7684"), C("b8beca")])))
        for k in range(7):
            cv.drawLine(-18, -20 + k * 19, 18, -12 + k * 19, P(C("4a505c"), stroke=4))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-55, -85, 55, -40), 8, 8), P(0, shader=lin(0, -85, 0, -40, [C("e3e7ee"), C("7c8392")])))
        cv.restore()
        for k in range(8):
            yy = -40 + 330 * dis - 160 - ((t * 120 + k * 40) % 160)
            cv.drawCircle(-40 + k * 11, yy, 6 + k % 3 * 2, P(C("d8ff4a", 0.6)))
        cv.restore(); cv.restore()
        a, s = pop(t, 1.0)
        chip(cv, 820, 590, "pH 1.5 – 3.5", a=a * ba, scale=s, col="d8ff4a", size=38)
    a, s = pop(t, ph1 + 0.6)
    chip(cv, 540, 470, "protective mucus", a=a * (1 - ss(ph2 - 0.2, ph2 + 0.2, t)), scale=s, col="dff6ff", size=42)
    a, s = pop(t, ph2 + 0.4)
    chip(cv, 540, 470, "↻ new lining every few days", a=a, scale=s, col="fff2a8", size=40)

FIB_CUTS = [-270, -90, 90, 270]

def scene4(cv, t, d):
    bg(cv, t)
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 900, 900, [C("ff9a3c", 0.12), C("ff9a3c", 0)])))
    for i in range(16):
        x = (i * 211) % W + 20 * math.sin(t + i)
        y = (1500 - (t * 60 + i * 117) % 1300)
        cv.drawCircle(x, y, 8 + i % 4 * 5, P(C("ffffff", 0.18), stroke=3))
    cy = 900
    edges = [-430] + FIB_CUTS + [430]
    cut_t = [0.9 + 0.55 * i for i in range(4)]
    for si in range(5):
        a_, b_ = edges[si], edges[si + 1]
        mid = (a_ + b_) / 2
        sep = 0.0
        for ci, cx in enumerate(FIB_CUTS):
            prog = ss(cut_t[ci] + 0.15, cut_t[ci] + 1.4, t)
            sep += (1 if mid > cx else -1) * 34 * prog
        lift = 0
        rot = 0
        if t > cut_t[-1] + 0.3:
            q = t - cut_t[-1] - 0.3
            lift = 40 * math.sin(q * 1.2 + si * 1.7) * ss(0, 1.5, q)
            rot = 9 * math.sin(q * 0.9 + si) * ss(0, 1.5, q)
        cv.save()
        cv.translate(540 + mid + sep, cy + lift + 12 * math.sin(t * 1.3 + si * 0.3))
        cv.rotate(rot)
        hw = (b_ - a_) / 2 - 6
        for k, (dy, hh, colA, colB) in enumerate([(-38, 30, "f2b49a", "c9705c"), (0, 34, "f6c1a8", "d07f68"), (38, 30, "eaa38a", "b8604f")]):
            r = skia.RRect.MakeRectXY(skia.Rect(-hw, dy - hh, hw, dy + hh), hh, hh)
            cv.drawRRect(r, P(C("000000", 0.3), blur=8))
            cv.drawRRect(r, P(0, shader=lin(0, dy - hh, 0, dy + hh, [C(colA), C(colB)])))
            for xx in np.arange(-hw + 16, hw - 8, 22):
                cv.drawLine(xx, dy - hh * 0.75, xx, dy + hh * 0.75, P(C("9a4a3c", 0.45), stroke=4))
            cv.drawLine(-hw + 20, dy - hh * 0.5, hw - 20, dy - hh * 0.5, P(C("ffffff", 0.3), stroke=5))
        cv.restore()
    # pepsin particles
    for ci, cx in enumerate(FIB_CUTS):
        t0 = cut_t[ci]
        ang = [2.4, -2.2, 2.0, -2.5][ci]
        sx, sy = 540 + cx + math.cos(ang) * 900, cy - abs(math.sin(ang)) * 900 * (1 if ci % 2 == 0 else -1)
        tx_, ty_ = 540 + cx, cy - 110 if ci % 2 == 0 else cy + 110
        u = ss(t0 - 0.9, t0, t)
        x = sx + (tx_ - sx) * u
        y = sy + (ty_ - sy) * u
        if t > t0:
            q = t - t0
            x += 60 * q * (1 if ci % 2 else -1)
            y += -70 * q if ci % 2 == 0 else 70 * q
        r = 30
        cv.drawCircle(x, y, r * 2.6, P(C("4fc3ff", 0.35), blur=22))
        mouth = 25 + 20 * abs(math.sin(t * 9 + ci))
        pm = skia.Path()
        pm.moveTo(x, y)
        start = 90 + mouth if ci % 2 == 0 else -90 + mouth
        pm.arcTo(skia.Rect(x - r, y - r, x + r, y + r), start, 360 - 2 * mouth, False)
        pm.close()
        cv.drawPath(pm, P(0, shader=rad(x - 8, y - 8, r * 1.3, [C("e6f8ff"), C("4fc3ff"), C("1a7fd1")])))
        if t0 < t < t0 + 0.35:
            k = (t - t0) / 0.35
            cv.drawCircle(540 + cx, cy, 40 + 120 * k, P(C("bfeaff", 1 - k), stroke=8))
            cv.drawCircle(540 + cx, cy, 70, P(C("ffffff", 0.6 * (1 - k)), blur=20))
    a, s = pop(t, 0.6)
    chip(cv, 300, 560, "PEPSIN", a=a, scale=s, col="4fc3ff", fg="06223a", size=44)
    a, s = pop(t, 0.3)
    chip(cv, 760, 1180, "chicken protein", a=a, scale=s, col="f6c1a8", size=38)

def scene5(cv, t, d):
    bg(cv, t)
    S = 150
    tb = make_stomach(560, 960, S)
    period = d / 3.2
    waves = []
    for k in range(4):
        ph = (t / period - k) % 4
        if t / period - k >= 0 and ph < 1:
            waves.append((0.25 + 0.6 * ph, 0.28 * math.sin(ph * math.pi) ** 0.6))
    prog = ss(0.5, d * 0.9, t)
    content = food_content(0.62, t, chunk=1 - prog, paste=prog, jitter=0.6 * (1 - prog * 0.6), S=S)
    draw_stomach(cv, tb, S, inflate=1.0, rugae=0.15, waves=waves, content=content, t=t)
    for (pos, amp) in waves:
        x, y, tg, n = tb.at(pos)
        wo, wi = stomach_widths(tb, S)
        i = int(np.searchsorted(tb.s, pos))
        for side in (1, -1):
            w = (wi[i] if side > 0 else wo[i]) + 30
            px, py = x + n[0] * w * side, y + n[1] * w * side
            cv.drawCircle(px, py, 34, P(C("ffd36e", 0.5 * amp / 0.28), blur=14))
    a, s = pop(t, 0.6)
    chip(cv, 300, 470, "3 waves / minute", a=a * (1 - ss(d * 0.72, d * 0.78, t)), scale=s, col="ffffff", size=40)
    a, s = pop(t, d * 0.75)
    chip(cv, 300, 470, "CHYME", a=a, scale=s, col="ff9a3a", fg="3a1206", size=48)

def body_path():
    p = skia.Path()
    p.moveTo(470, 610); p.lineTo(470, 660)
    p.cubicTo(380, 680, 300, 700, 270, 760)
    p.cubicTo(240, 830, 250, 1000, 300, 1180)
    p.cubicTo(320, 1280, 300, 1380, 290, 1500)
    p.cubicTo(280, 1650, 300, 1800, 320, 2000)
    p.lineTo(760, 2000)
    p.cubicTo(780, 1800, 800, 1650, 790, 1500)
    p.cubicTo(780, 1380, 760, 1280, 780, 1180)
    p.cubicTo(830, 1000, 840, 830, 810, 760)
    p.cubicTo(780, 700, 700, 680, 610, 660)
    p.lineTo(610, 610)
    p.close()
    return p

BRAIN = []
for th in np.linspace(0, 2 * math.pi, 120, endpoint=False):
    r = 1 + 0.05 * math.sin(th * 11)
    BRAIN.append((540 + math.cos(th) * 150 * r, 455 + math.sin(th) * 112 * r * (1 if math.sin(th) < 0 else 0.85)))

NERVE = Tube([(520, 1000), (470, 900), (455, 780), (500, 650), (520, 560), (535, 520)], 30)

def scene6(cv, t, d):
    bg(cv, t)
    bp = body_path()
    cv.drawPath(bp, P(C("c9a7ff", 0.10)))
    cv.drawPath(bp, P(C("e7d6ff", 0.45), stroke=5))
    cv.drawCircle(540, 450, 205, P(C("c9a7ff", 0.10)))
    cv.drawCircle(540, 450, 205, P(C("e7d6ff", 0.45), stroke=5))
    S = 62
    tb = make_stomach(565, 1180, S)
    arrive = 0.6 + d * 0.45
    lit = ss(arrive, arrive + 0.35, t)
    draw_stomach(cv, tb, S, inflate=1.0, rugae=0.1, content=food_content(0.6, t, chunk=0.6, paste=0.4, S=S), glow=0.5 + 0.5 * math.sin(t * 6) if t < arrive else 0.2, t=t)
    # brain
    bpth = poly(BRAIN)
    if lit > 0:
        cv.drawCircle(540, 455, 260, P(C("ffd36e", 0.45 * lit), blur=60))
    cv.drawPath(bpth, P(0, shader=rad(500, 400, 220, [lerpc("ffc4d6", "fff1b8", lit), lerpc("e88aa8", "ffb36b", lit)])))
    for k in range(5):
        sp = skia.Path()
        x0 = 430 + k * 45
        sp.moveTo(x0, 370 + (k % 2) * 20)
        sp.cubicTo(x0 + 30, 420, x0 - 25, 470, x0 + 15, 540 - (k % 3) * 20)
        cv.drawPath(sp, P(lerpc("c25f83", "e08a3a", lit), stroke=6))
    cv.drawLine(540, 350, 540, 555, P(lerpc("c25f83", "e08a3a", lit), stroke=6))
    cv.drawPath(bpth, P(C("ffffff", 0.35), stroke=4))
    # nerve
    cv.drawPath(NERVE.line(0, 1), P(C("ffe08a", 0.35), stroke=7))
    u = ss(0.6, arrive, t)
    if 0 < u < 1 or (t < arrive and t > 0.6):
        cv.drawPath(NERVE.line(max(0, u - 0.25), u), P(C("fff2a8", 0.9), stroke=12, blur=4))
        x, y, _, _ = NERVE.at(u)
        cv.drawCircle(x, y, 48, P(C("ffe066", 0.6), blur=20))
        cv.drawCircle(x, y, 18, P(C("ffffff")))
    if lit > 0:
        for k in range(3):
            q = (t - arrive - k * 0.3)
            if 0 < q < 1.2:
                cv.drawCircle(540, 455, 170 + q * 220, P(C("ffe08a", 0.6 * (1 - q / 1.2)), stroke=6))
    a, s = pop(t, arrive + 0.15)
    chip(cv, 830, 390, "I'M FULL!", a=a, scale=s, col="ffd36e", fg="3a1206", size=50)

VALVE_PTS = [(1250, 80), (1050, 380), (820, 650), (620, 820), (470, 900), (350, 960), (250, 1080), (260, 1230),
             (420, 1290), (600, 1240), (760, 1300), (790, 1460), (650, 1560), (450, 1560), (300, 1660), (330, 1820), (520, 1880), (760, 1860), (1000, 1900), (1200, 1950)]
VT = Tube(VALVE_PTS, 30)
SV = float(VT.s[np.argmin(np.linalg.norm(VT.c - np.array([470, 900]), axis=1))])

def valve_scene(cv, t, open_amt, squirt, zoom, blobs=()):
    w = VT.prof([0, SV - 0.12, SV - 0.025, SV, SV + 0.03, 1], [330, 230, 80, 60, 56, 56])
    th = VT.prof([0, SV - 0.1, SV, 1], [44, 34, 22, 20])
    gate = gauss(VT.s - SV, 0.008)
    lw = np.maximum((w - th) * (1 - gate * (1 - (0.18 + 0.82 * open_amt))), 3)
    lw = np.maximum(lw - gate * (w - th) * (1 - open_amt) * 0.97, 2.5)
    cv.save()
    cv.translate(470, 900)
    cv.scale(zoom, zoom)
    cv.translate(-470, -900)
    outer = VT.outline(w, w)
    lumen = VT.outline(lw, lw)
    cv.drawPath(outer, P(C("05010a", 0.55), blur=30))
    cv.drawPath(outer, P(0, shader=lin(200, 100, 1000, 1900, [C("ff9a86"), C("f0607a"), C("c23b62")])))
    cv.drawPath(lumen, P(0, shader=lin(200, 100, 1000, 1900, [C("7a1f45"), C("4e1032")])))
    # stomach contents up to valve
    cv.save(); cv.clipPath(lumen, skia.ClipOp.kIntersect, True)
    paste_out = VT.outline(lw, lw, 0, SV - 0.004)
    cv.drawPath(paste_out, P(0, shader=lin(1100, 100, 470, 900, [C("ff8c2e"), C("e8681e")])))
    for i in range(14):
        sx = 0.05 + (i / 14) * (SV - 0.1)
        x, y, _, n = VT.at(sx + 0.01 * math.sin(t + i))
        cv.drawCircle(x + n[0] * 40 * math.sin(i * 2.1), y + n[1] * 40 * math.sin(i * 2.1), 14, P(C("ffd08a", 0.35), blur=4))
    # villi in intestine
    for sx in np.linspace(SV + 0.03, 1, 90):
        x, y, tg, n = VT.at(sx)
        for side in (1, -1):
            cv.drawCircle(x + n[0] * 50 * side, y + n[1] * 50 * side, 9, P(C("e0607e", 0.55)))
    for p in ([squirt] if squirt is not None else []) + list(blobs):
        if p is None:
            continue
        a_, b_ = p - 0.035, p
        seg = VT.outline(lw * 0.92, lw * 0.92, max(a_, SV - 0.004), b_)
        cv.drawPath(seg, P(C("ff9a3a")))
        x, y, _, _ = VT.at(b_)
        cv.drawCircle(x, y, 26, P(C("ffb04a", 0.6), blur=10))
    cv.restore()
    cv.drawPath(lumen, P(C("ffb0bd", 0.45), stroke=4))
    # valve ring
    x, y, tg, n = VT.at(SV)
    ang = math.degrees(math.atan2(tg[1], tg[0]))
    cv.save(); cv.translate(x, y); cv.rotate(ang)
    gap = 3 + 50 * open_amt
    for side in (1, -1):
        r = skia.Rect(-34, side * gap if side > 0 else -gap - 105, 34, gap + 105 if side > 0 else -gap)
        cv.drawRRect(skia.RRect.MakeRectXY(r, 30, 30), P(C("000000", 0.35), blur=10))
        cv.drawRRect(skia.RRect.MakeRectXY(r, 30, 30), P(0, shader=lin(-34, 0, 34, 0, [C("e0506e"), C("ffa0a8"), C("b8345a")])))
        for k in range(5):
            yy = (gap + 18 + k * 19) * side
            cv.drawLine(-26, yy, 26, yy, P(C("8f2448", 0.6), stroke=4))
    cv.restore()
    cv.drawPath(outer, P(C("8f2448", 0.9), stroke=6))
    cv.restore()

def scene7(cv, t, d):
    bg(cv, t)
    open_amt = ss(1.2, 2.2, t) * (1 - ss(d * 0.72, d * 0.85, t))
    sq = None
    if t > 1.8:
        sq = SV + 0.003 + ss(1.8, d * 0.9, t) * 0.25
    zoom = 1.75 - 0.75 * ss(d * 0.55, d, t)
    valve_scene(cv, t, open_amt, sq, zoom)
    a, s = pop(t, 0.7)
    chip(cv, 760, 560, "pyloric valve", a=a * (1 - ss(d * 0.55, d * 0.65, t)), scale=s, col="ffffff", size=40)
    a, s = pop(t, d * 0.68)
    chip(cv, 760, 560, "small intestine →", a=a, scale=s, col="ff9a3a", fg="3a1206", size=40)

def scene8(cv, t, d):
    bg(cv, t)
    base = SV + 0.003 + 0.25 + t * 0.12
    blobs = [base, base - 0.17 + 0.0 * t, base - 0.34]
    blobs = [b for b in blobs if SV < b < 1.04]
    valve_scene(cv, t, 0.15 + 0.35 * abs(math.sin(t * 1.3)), None, 1.0 - 0.05 * ss(0, d, t), blobs=blobs)
    cv.drawRect(skia.Rect(0, 0, W, H), P(C("0c0616", 0.45 * ss(d - 1.6, d - 0.2, t))))
    a, s = pop(t, 0.4)
    cv.save(); cv.saveLayerAlpha(None, int(a * 255))
    text(cv, "THE JOURNEY", 540, 420, 96, C("ffffff"), stroke=16, stroke_col=C("1a0b26"))
    text(cv, "CONTINUES…", 540, 530, 96, C("ffb04a"), stroke=16, stroke_col=C("1a0b26"))
    cv.restore(); cv.restore()

SCENES = [scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8]
TIMERS = ["00:00", "00:08", "00:30", "5 MIN", "10 MIN", "20 MIN", "60 MIN", "60 MIN"]

BOUNDS = [0.0] + [SEGS[i]["start"] + LEAD - 0.15 for i in range(1, len(SEGS))] + [TOTAL]

# --------------------------------------------------------------- captions
DISPLAY = [
    "You just swallowed a bite of jollof rice. Here's what happens in the next 60 minutes.",
    "8 seconds later, it drops into your stomach, a bag about the size of your fist that stretches to hold over a litre.",
    "Right away, the walls start pouring in acid. It's strong enough to dissolve metal, so your stomach coats itself in thick mucus to keep from digesting itself. It even replaces its inner lining every few days.",
    "Next, an enzyme called pepsin starts cutting the chicken's protein into smaller pieces.",
    "Around minute 10, the muscles start squeezing, 3 waves every minute, mashing everything into a thick paste called chyme.",
    "At 20 minutes, your brain finally gets the \"I'm full\" signal.",
    "And by the hour mark, a tiny valve opens, letting the first spoonfuls into your small intestine.",
    "The real journey has just started.",
]
KEYS = {"jollof", "60", "stomach,", "stomach", "fist", "litre.", "acid.", "metal,", "mucus", "lining", "pepsin", "protein", "3", "waves", "chyme.", "brain", "full\"", "\"i'm", "valve", "intestine.", "journey"}

def build_captions():
    caps = []
    for seg, disp in zip(SEGS, DISPLAY):
        words = disp.split()
        chunks, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= 3 or w[-1] in ",.!?" and len(cur) >= 1:
                chunks.append(cur); cur = []
        if cur:
            chunks.append(cur)
        # merge 1-word chunks into previous where possible
        merged = []
        for c in chunks:
            if merged and len(c) == 1 and len(merged[-1]) < 4 and merged[-1][-1][-1] not in ".":
                merged[-1] += c
            else:
                merged.append(c)
        weights = [sum(len(w) + 1 for w in c) + (6 if c[-1][-1] in ",." else 0) for c in merged]
        tot = sum(weights)
        t0, dur = seg["start"] + LEAD, seg["end"] - seg["start"]
        acc = 0
        for c, wgt in zip(merged, weights):
            caps.append((t0 + dur * acc / tot, t0 + dur * (acc + wgt) / tot, c))
            acc += wgt
    return caps

CAPS = build_captions()

def draw_caption(cv, t):
    for (a, b, words) in CAPS:
        if a <= t < b + 0.05:
            k = ease_out_back((t - a) / 0.22, 2.2)
            size = 82
            f = skia.Font(TF_BLACK, size)
            parts = [w.upper() for w in words]
            widths = [f.measureText(p) for p in parts]
            space = f.measureText(" ")
            total = sum(widths) + space * (len(parts) - 1)
            lines = [list(range(len(parts)))]
            if total > 940:
                cut = len(parts) // 2 + (len(parts) % 2)
                lines = [list(range(cut)), list(range(cut, len(parts)))]
            cv.save()
            cy = 1500
            cv.translate(540, cy); cv.scale(k, k); cv.translate(-540, -cy)
            for li, idxs in enumerate(lines):
                lw = sum(widths[i] for i in idxs) + space * (len(idxs) - 1)
                x = 540 - lw / 2
                y = cy + (li - (len(lines) - 1) / 2) * 96 + 30
                for i in idxs:
                    key = words[i].lower().strip(".,") in {k_.strip(".,\"") for k_ in KEYS} or words[i].lower() in KEYS
                    cv.drawString(parts[i], x, y + 6, f, P(C("000000", 0.5), stroke=18, blur=6))
                    cv.drawString(parts[i], x, y, f, P(C("000000"), stroke=16))
                    cv.drawString(parts[i], x, y, f, P(C("ffd23f") if key else C("ffffff")))
                    x += widths[i] + space
            cv.restore()
            break

def draw_timer(cv, t, si):
    label = TIMERS[si]
    t0 = BOUNDS[si]
    a, s = (1.0, ease_out_back((t - t0) / 0.4)) if si > 0 else (ss(4.2, 4.6, t), ease_out_back((t - 4.2) / 0.4))
    if a <= 0:
        return
    f = skia.Font(TF_BLACK, 58)
    tw = f.measureText(label)
    w, h = tw + 150, 104
    cv.save(); cv.translate(540, 215); cv.scale(s, s)
    cv.saveLayerAlpha(None, int(a * 255))
    r = skia.RRect.MakeRectXY(skia.Rect(-w / 2, -h / 2, w / 2, h / 2), h / 2, h / 2)
    cv.drawRRect(r, P(C("000000", 0.45), blur=14))
    cv.drawRRect(r, P(C("ffffff")))
    ix = -w / 2 + 62
    cv.drawCircle(ix, 4, 26, P(C("e8475f"), stroke=8))
    cv.drawLine(ix, -30, ix, -24, P(C("e8475f"), stroke=8))
    hand = t * 4
    cv.drawLine(ix, 4, ix + 15 * math.sin(hand), 4 - 15 * math.cos(hand), P(C("2a0f2e"), stroke=6))
    cv.drawString(label, ix + 48, 22, f, P(C("2a0f2e")))
    cv.restore(); cv.restore()

def draw_title(cv, t):
    a = ss(0.2, 0.6, t) * (1 - ss(3.9, 4.3, t))
    if a <= 0:
        return
    k = ease_out_back((t - 0.2) / 0.5)
    cv.save(); cv.translate(540, 260); cv.scale(k, k)
    cv.saveLayerAlpha(None, int(a * 255))
    text(cv, "WHAT HAPPENS TO FOOD", 0, -40, 72, C("ffffff"), stroke=14, stroke_col=C("1a0b26"))
    text(cv, "IN YOUR STOMACH?", 0, 50, 72, C("ffffff"), stroke=14, stroke_col=C("1a0b26"))
    chip(cv, 0, 140, "the first 60 minutes", size=40, col="ffb04a", fg="3a1206")
    cv.restore(); cv.restore()

def render_frame(cv, t):
    si = max(i for i in range(len(SCENES)) if BOUNDS[i] <= t) if t < TOTAL else len(SCENES) - 1
    si = min(si, len(SCENES) - 1)
    SCENES[si](cv, t - BOUNDS[si], BOUNDS[si + 1] - BOUNDS[si])
    XF = 0.35
    if si + 1 < len(SCENES) and t > BOUNDS[si + 1] - XF:
        pass
    if si > 0 and t < BOUNDS[si] + XF:
        a = 1 - (t - BOUNDS[si]) / XF
        cv.saveLayerAlpha(None, int(a * 255))
        SCENES[si - 1](cv, t - BOUNDS[si - 1], BOUNDS[si] - BOUNDS[si - 1])
        cv.restore()
    # vignette
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 900, 1300, [C("000000", 0), C("000000", 0.45)], [0.55, 1])))
    draw_title(cv, t)
    draw_timer(cv, t, si)
    draw_caption(cv, t)
    # progress bar
    cv.drawRect(skia.Rect(0, 0, W * t / TOTAL, 10), P(C("ffb04a")))
    fade = 1 - ss(TOTAL - 0.6, TOTAL, t)
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
        cv = surf.getCanvas()
        cv.clear(C("000000"))
        render_frame(cv, fi / FPS)
        ff.stdin.write(surf.makeImageSnapshot().toarray().tobytes())
    ff.stdin.close(); ff.wait()
    return out

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        surf = skia.Surface(W, H)
        for ts in sys.argv[2:]:
            cv = surf.getCanvas(); cv.clear(C("000000"))
            render_frame(cv, float(ts))
            surf.makeImageSnapshot().save(os.path.join(HERE, f"still_{ts}.png"), skia.kPNG)
        print("bounds", [round(b, 2) for b in BOUNDS])
    else:
        from multiprocessing import Pool
        N = int(math.ceil(TOTAL * FPS))
        nw = 4
        step = math.ceil(N / nw)
        jobs = [(k, k * step, min(N, (k + 1) * step), os.path.join(HERE, f"part{k}.mp4")) for k in range(nw)]
        with Pool(nw) as p:
            outs = p.map(worker, jobs)
        with open(os.path.join(HERE, "parts.txt"), "w") as f:
            for o in outs:
                f.write(f"file '{o}'\n")
        print("frames", N, "dur", TOTAL)
