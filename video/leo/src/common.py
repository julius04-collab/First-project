"""Shared scene kit for the Leo series: 3D-style bedroom, flat 2D Leo, flat cast shadow, camera, renderer."""
import json, math, os, subprocess
import numpy as np
import skia

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
OUTLINE = skia.ColorSetARGB(255, 29, 29, 31)

def C(h, a=1.0):
    h = h.lstrip("#")
    return skia.ColorSetARGB(int(max(0, min(1, a)) * 255), int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def ss(a, b, x):
    t = clamp((x - a) / (b - a)) if b != a else float(x >= a)
    return t * t * (3 - 2 * t)

def lerp(a, b, t):
    return a + (b - a) * t

def lerp2(p, q, t):
    return (lerp(p[0], q[0], t), lerp(p[1], q[1], t))

def P(color, stroke=None, blur=None, shader=None, cap=skia.Paint.kRound_Cap):
    p = skia.Paint(AntiAlias=True)
    p.setColor(color)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        p.setStrokeCap(cap); p.setStrokeJoin(skia.Paint.kRound_Join)
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
    path.addPoly([skia.Point(float(x), float(y)) for x, y in pts], close)
    return path

# ================================================================== ROOM (stylized 3D, one-point perspective)
VP = (540.0, 820.0)
BACK = (120.0, 380.0, 960.0, 1250.0)   # back wall x0,y0,x1,y1

def ray(p, y):
    """point on the ray from VP through p, at screen height y"""
    t = (y - VP[1]) / (p[1] - VP[1])
    return (VP[0] + (p[0] - VP[0]) * t, y)

def depth_pt(x_back, y_back, s):
    """point with back-wall coords scaled toward viewer by depth factor s (1 = on back wall)"""
    return (VP[0] + (x_back - VP[0]) * s, VP[1] + (y_back - VP[1]) * s)

FLOOR_POLY = None

def draw_room_static(cv):
    global FLOOR_POLY
    x0, y0, x1, y1 = BACK
    # ceiling
    cl = ray((x0, y0), -10); cr = ray((x1, y0), -10)
    cv.drawPath(poly([(x0, y0), (x1, y0), cr, cl]), P(0, shader=lin(0, 0, 0, y0, [C("f7f1e6"), C("ece3d3")])))
    # side walls
    fl = ray((x0, y1), H + 10); fr = ray((x1, y1), H + 10)
    left_wall = poly([cl, (x0, y0), (x0, y1), fl, (-800, H + 10), (-800, -10)])
    right_wall = poly([cr, (x1, y0), (x1, y1), fr, (1900, H + 10), (1900, -10)])
    cv.drawPath(left_wall, P(0, shader=lin(-200, 0, x0, 0, [C("d9cdb8"), C("e6dbc8")])))
    cv.drawPath(right_wall, P(0, shader=lin(x1, 0, 1300, 0, [C("f3e9d6"), C("fbf2e0")])))
    # back wall
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(0, shader=lin(0, y0, 0, y1, [C("f4ecdd"), C("ebe0cc")])))
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(0, shader=lin(x0, 0, x1, 0, [C("fff6e0", 0.35), C("000000", 0.0), C("000000", 0.06)], [0, 0.5, 1])))
    # corner occlusion
    for (a, b) in (((x0, y0), (x0, y1)), ((x1, y0), (x1, y1))):
        cv.drawLine(a[0], a[1], b[0], b[1], P(C("8a7a60", 0.35), stroke=10, blur=8))
    cv.drawLine(x0, y0, x1, y0, P(C("8a7a60", 0.25), stroke=10, blur=8))
    # floor (wood planks converging to VP)
    FLOOR_POLY = poly([(x0, y1), (x1, y1), fr, fl])
    cv.save(); cv.clipPath(FLOOR_POLY, skia.ClipOp.kIntersect, True)
    cv.drawPath(FLOOR_POLY, P(C("b07c52")))
    rr = np.random.default_rng(12)
    step = 46
    xs = list(np.arange(x0 - 1400, x1 + 1400, step))
    tones = ["b98659", "a9744b", "c2905f", "b07a4f", "9f6b44", "bd8a5c"]
    for i in range(len(xs) - 1):
        a, b = xs[i], xs[i + 1]
        quad = [(a, y1), (b, y1), ray((b, y1), H + 10), ray((a, y1), H + 10)]
        cv.drawPath(poly(quad), P(C(tones[i % len(tones)])))
        # plank end seams at staggered depths
        for k in range(6):
            s = 1.0 + rr.uniform(0.05, 1.6)
            pa = depth_pt(a, y1, s); pb = depth_pt(b, y1, s)
            cv.drawLine(pa[0], pa[1], pb[0], pb[1], P(C("6e4a2e", 0.55), stroke=2.2 * s))
        # grain
        for k in range(3):
            u = rr.uniform(0.15, 0.85)
            pa = (lerp(a, b, u), y1); pb = ray(pa, H + 10)
            cv.drawLine(pa[0], pa[1], pb[0], pb[1], P(C("ffffff", 0.05), stroke=2))
        cv.drawLine(a, y1, *ray((a, y1), H + 10), P(C("5e3d24", 0.6), stroke=2.5))
    # floor shading: darker far, varnish sheen
    cv.drawRect(skia.Rect(-800, y1, 1900, H), P(0, shader=lin(0, y1, 0, H, [C("2a1608", 0.35), C("2a1608", 0.0), C("000000", 0.12)], [0, 0.45, 1])))
    cv.drawRect(skia.Rect(-800, y1, 1900, H), P(0, shader=rad(820, 1500, 700, [C("fff2d8", 0.10), C("fff2d8", 0)])))
    cv.restore()
    # baseboards
    cv.drawRect(skia.Rect(x0, y1 - 26, x1, y1), P(C("faf6ee")))
    cv.drawLine(x0, y1 - 26, x1, y1 - 26, P(C("cfc4b0"), stroke=2))
    for (wx, side) in ((x0, -1), (x1, 1)):
        top_far = (wx, y1 - 26); bot_far = (wx, y1)
        top_near = ray(top_far, H + 10) if False else depth_pt(wx, y1 - 26, 2.8)
        bot_near = depth_pt(wx, y1, 2.8)
        cv.drawPath(poly([top_far, top_near, bot_near, bot_far]), P(C("f2ece0")))
    cv.drawLine(x0, y1, x1, y1, P(C("3a2512", 0.45), stroke=8, blur=5))
    draw_window(cv)
    draw_wall_art(cv)
    draw_bedside(cv)
    draw_bed(cv)
    draw_wardrobe(cv)
    draw_sunlight(cv)

WIN = (175.0, 470.0, 470.0, 975.0)

def draw_window(cv):
    x0, y0, x1, y1 = WIN
    cv.drawRect(skia.Rect(x0 - 6, y0 - 6, x1 + 6, y1 + 18), P(C("6b5a40", 0.25), blur=10))
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(0, shader=lin(0, y0, 0, y1, [C("bfe2ff"), C("e6f4ff"), C("fff3d6")], [0, 0.6, 1])))
    cv.drawCircle(x0 + 60, y0 + 80, 160, P(C("fff6d8", 0.85), blur=50))
    cv.drawCircle(x0 + 60, y0 + 80, 40, P(C("fffbea")))
    # distant trees / rooftops
    rr = np.random.default_rng(4)
    for k in range(9):
        cx = x0 + k * 38 + rr.uniform(-10, 10)
        cv.drawCircle(cx, y1 - 40 + rr.uniform(-15, 15), rr.uniform(35, 60), P(C("8fbf8a", 0.9)))
    cv.drawRect(skia.Rect(x0, y1 - 40, x1, y1), P(C("7aae78")))
    # frame
    fr = C("fbfaf6")
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(fr, stroke=16))
    cv.drawLine((x0 + x1) / 2, y0, (x0 + x1) / 2, y1, P(fr, stroke=12))
    cv.drawLine(x0, (y0 + y1) / 2 + 30, x1, (y0 + y1) / 2 + 30, P(fr, stroke=12))
    cv.drawRect(skia.Rect(x0 - 20, y1, x1 + 20, y1 + 22), P(C("fbfaf6")))
    cv.drawRect(skia.Rect(x0 - 20, y1 + 22, x1 + 20, y1 + 30), P(C("bfb5a0", 0.6), blur=3))
    # curtains with soft folds
    cv.drawLine(x0 - 70, y0 - 40, x1 + 70, y0 - 40, P(C("6b5236"), stroke=8))
    for (cx0, cx1) in ((x0 - 70, x0 + 25), (x1 - 25, x1 + 70)):
        path = poly([(cx0, y0 - 40), (cx1, y0 - 40), (cx1 + (10 if cx0 < x0 else -10), 1200), (cx0 - (10 if cx0 < x0 else -10), 1200)])
        cv.drawPath(path, P(C("a9bfa6")))
        cv.save(); cv.clipPath(path, skia.ClipOp.kIntersect, True)
        n = 5
        for k in range(n):
            fx = cx0 + (cx1 - cx0) * (k + 0.5) / n
            cv.drawRect(skia.Rect(fx - 8, y0 - 40, fx + 8, 1210), P(C("7f9a7c", 0.45), blur=6))
            cv.drawRect(skia.Rect(fx + 6, y0 - 40, fx + 12, 1210), P(C("e3eedf", 0.4), blur=4))
        cv.restore()

def draw_wall_art(cv):
    x0, y0, x1, y1 = 690, 600, 870, 820
    cv.drawRect(skia.Rect(x0 + 6, y0 + 10, x1 + 6, y1 + 10), P(C("5a4a30", 0.3), blur=8))
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(C("3b3026")))
    cv.drawRect(skia.Rect(x0 + 14, y0 + 14, x1 - 14, y1 - 14), P(C("f6efe2")))
    cv.drawCircle(780, 690, 42, P(C("e8a75b")))
    cv.drawRect(skia.Rect(x0 + 30, 740, x1 - 30, 790), P(C("6f9a8e")))

def draw_bedside(cv):
    x0, x1 = 518.0, 598.0
    top = 1120.0; y1 = BACK[3]
    s = 1.12
    fl = depth_pt(x0, y1, s); fr = depth_pt(x1, y1, s); tl = depth_pt(x0, top, s); tr = depth_pt(x1, top, s)
    cv.drawPath(poly([fl, fr, (fr[0] + 30, fr[1] + 10), (fl[0] - 20, fl[1] + 10)]), P(C("2a1608", 0.35), blur=10))
    cv.drawPath(poly([(x0, top), (x1, top), tr, tl]), P(C("c99a6a")))
    cv.drawPath(poly([tl, tr, fr, fl]), P(0, shader=lin(0, tl[1], 0, fl[1], [C("b5835a"), C("9a6b45")])))
    cv.drawLine(tl[0] + 6, (tl[1] + fl[1]) / 2, tr[0] - 6, (tl[1] + fl[1]) / 2, P(C("6e4a2e"), stroke=3))
    cv.drawCircle((tl[0] + tr[0]) / 2, (tl[1] + fl[1]) / 2 + 22, 5, P(C("e9d3a0")))
    # lamp
    lx = (x0 + x1) / 2
    cv.drawRect(skia.Rect(lx - 5, top - 70, lx + 5, top), P(C("6b5a40")))
    cv.drawPath(poly([(lx - 34, top - 70), (lx + 34, top - 70), (lx + 22, top - 125), (lx - 22, top - 125)]), P(0, shader=lin(lx - 34, 0, lx + 34, 0, [C("f3e6c8"), C("dccaa2")])))
    cv.drawOval(skia.Rect(lx - 26, top - 8, lx + 26, top + 6), P(C("2a1608", 0.3), blur=4))

BED_BACK = (600.0, 940.0)
BED_S = 1.55
BED_H = 55.0

def bed_geom():
    y1 = BACK[3]
    bl, br = BED_BACK
    tbl = (bl, y1 - BED_H); tbr = (br, y1 - BED_H)
    fbl = depth_pt(bl, y1, BED_S); fbr = depth_pt(br, y1, BED_S)
    ftl = depth_pt(bl, y1 - BED_H, BED_S); ftr = depth_pt(br, y1 - BED_H, BED_S)
    return tbl, tbr, ftl, ftr, fbl, fbr

def draw_bed(cv):
    y1 = BACK[3]
    bl, br = BED_BACK
    tbl, tbr, ftl, ftr, fbl, fbr = bed_geom()
    # floor contact shadow
    cv.drawPath(poly([(bl - 20, y1), (br + 20, y1), (fbr[0] + 40, fbr[1] + 30), (fbl[0] - 40, fbl[1] + 30)]), P(C("2a1608", 0.4), blur=22))
    # headboard
    hb = skia.RRect.MakeRectXY(skia.Rect(bl - 10, 930, br + 10, y1 - 20), 26, 26)
    cv.drawRRect(hb, P(0, shader=lin(0, 930, 0, y1, [C("a87650"), C("8a5e3c")])))
    for k in range(1, 6):
        xx = bl - 10 + k * (br - bl + 20) / 6
        cv.drawLine(xx, 950, xx, y1 - 40, P(C("6e4a2e", 0.5), stroke=3))
    # left side face
    cv.drawPath(poly([tbl, ftl, fbl, (bl, y1)]), P(C("8d9fb3")))
    # front face (duvet drop + wooden frame)
    cv.drawPath(poly([ftl, ftr, fbr, fbl]), P(0, shader=lin(0, ftl[1], 0, fbl[1], [C("c9d6e3"), C("a7b8ca")])))
    cv.drawPath(poly([(fbl[0], fbl[1] - 34), (fbr[0], fbr[1] - 34), fbr, fbl]), P(C("8a5e3c")))
    # top (duvet)
    top = poly([tbl, tbr, ftr, ftl])
    cv.drawPath(top, P(0, shader=lin(0, tbl[1], 0, ftl[1], [C("eef3f8"), C("d6e1ec")])))
    cv.save(); cv.clipPath(top, skia.ClipOp.kIntersect, True)
    for k in range(5):
        u = 0.15 + k * 0.18
        a = lerp2(tbl, ftl, u); b = lerp2(tbr, ftr, u)
        cv.drawLine(a[0], a[1], b[0], b[1], P(C("a7b8ca", 0.35), stroke=6 + 6 * u, blur=6))
    # folded sheet band
    a = lerp2(tbl, ftl, 0.12); b = lerp2(tbr, ftr, 0.12); c = lerp2(tbr, ftr, 0.2); d = lerp2(tbl, ftl, 0.2)
    cv.drawPath(poly([a, b, c, d]), P(C("ffffff")))
    cv.restore()
    # pillows
    for px in (bl + 90, br - 90):
        r = skia.RRect.MakeRectXY(skia.Rect(px - 85, y1 - BED_H - 70, px + 85, y1 - BED_H + 12), 30, 30)
        cv.drawRRect(r, P(C("8d9fb3", 0.35), blur=8))
        cv.drawRRect(r, P(0, shader=lin(0, y1 - BED_H - 70, 0, y1 - BED_H + 12, [C("ffffff"), C("e4ebf2")])))
    # front edge highlight
    cv.drawLine(ftl[0], ftl[1], ftr[0], ftr[1], P(C("ffffff", 0.7), stroke=4))

def draw_wardrobe(cv):
    # tall box against the left side, front-left of room
    front = [(-30, 610), (210, 600), (210, 1452), (-30, 1475)]
    side = [(210, 600), (282, 660), (282, 1395), (210, 1452)]
    top = [(-30, 610), (210, 600), (282, 660), (40, 668)]
    cv.drawPath(poly([(-30, 1475), (210, 1452), (282, 1395), (330, 1420), (260, 1500), (-30, 1530)]), P(C("2a1608", 0.45), blur=18))
    cv.drawPath(poly(side), P(0, shader=lin(210, 0, 282, 0, [C("8b5d3b"), C("7a5032")])))
    cv.drawPath(poly(front), P(0, shader=lin(-30, 0, 210, 0, [C("a06d47"), C("b07b52")])))
    cv.drawPath(poly(top), P(C("c08e64")))
    cv.drawLine(90, 615, 90, 1462, P(C("5e3d24"), stroke=4))
    for hx in (72, 108):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(hx - 5, 960, hx + 5, 1060), 4, 4), P(C("e2c48a")))
    for k in range(2):
        yy = 1340 + k * 0
    cv.drawRect(skia.Rect(-30, 1400, 210, 1408), P(C("5e3d24", 0.6)))
    cv.drawPath(poly(front), P(C("4a2e18", 0.5), stroke=3))
    cv.drawLine(210, 600, 210, 1452, P(C("e8c49a", 0.5), stroke=3))

LIGHT_PATCH = [(250, 1330), (560, 1318), (790, 1660), (430, 1690)]

def draw_sunlight(cv):
    x0, y0, x1, y1 = WIN
    beam = poly([(x0, y0), (x1, y0), LIGHT_PATCH[2], LIGHT_PATCH[3], LIGHT_PATCH[0]])
    cv.drawPath(beam, P(0, shader=lin(x0, y0, 700, 1650, [C("fff4d0", 0.16), C("fff4d0", 0.03)]), blur=26))
    cv.save(); cv.clipPath(FLOOR_POLY, skia.ClipOp.kIntersect, True)
    cv.drawPath(poly(LIGHT_PATCH), P(C("ffe2a8", 0.38), blur=14))
    cv.drawPath(poly(LIGHT_PATCH), P(C("fff3d0", 0.22), blur=4))
    # window mullion shadows inside patch
    a = lerp2(LIGHT_PATCH[0], LIGHT_PATCH[1], 0.5); b = lerp2(LIGHT_PATCH[3], LIGHT_PATCH[2], 0.5)
    cv.drawLine(a[0], a[1], b[0], b[1], P(C("b07c52", 0.6), stroke=12, blur=3))
    a = lerp2(LIGHT_PATCH[0], LIGHT_PATCH[3], 0.55); b = lerp2(LIGHT_PATCH[1], LIGHT_PATCH[2], 0.55)
    cv.drawLine(a[0], a[1], b[0], b[1], P(C("b07c52", 0.6), stroke=12, blur=3))
    cv.restore()

ROOM_IMG = None
ROOM_SS = 2

def room_image():
    global ROOM_IMG
    if ROOM_IMG is None:
        surf = skia.Surface(W * ROOM_SS, H * ROOM_SS)
        cv = surf.getCanvas(); cv.scale(ROOM_SS, ROOM_SS)
        draw_room_static(cv)
        ROOM_IMG = surf.makeImageSnapshot()
    return ROOM_IMG

def draw_room(cv):
    img = room_image()
    cv.save(); cv.scale(1 / ROOM_SS, 1 / ROOM_SS)
    cv.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
    cv.restore()

def draw_dust(cv, t):
    x0, y0, x1, y1 = WIN
    rr = np.random.default_rng(9)
    beam = poly([(x0, y0), (x1, y0), LIGHT_PATCH[2], LIGHT_PATCH[3], LIGHT_PATCH[0]])
    cv.save(); cv.clipPath(beam, skia.ClipOp.kIntersect, True)
    for i in range(40):
        bx, by = rr.uniform(150, 800), rr.uniform(450, 1650)
        x = bx + 25 * math.sin(t * 0.4 + i)
        y = (by - t * 12 * rr.uniform(0.5, 1.5)) % 1300 + 420
        cv.drawCircle(x, y, rr.uniform(1.5, 3.2), P(C("fffbe8", 0.55 + 0.3 * math.sin(t * 2 + i))))
    cv.restore()

# ================================================================== LEO (flat 2D puppet)
LEO = dict(hair="4b2f20", jacket="e2a72e", tee="ffffff", pants="1f2a4a", face="ffffff")
S_LEO = 1.25           # world scale
UPPER, FORE = 78.0, 74.0
HEAD_R = 64.0
SH_HALF = 34.0
TORSO = 128.0

def ik(sx, sy, tx, ty, outward):
    dx, dy = tx - sx, ty - sy
    d = clamp(math.hypot(dx, dy), 10, UPPER + FORE - 1)
    a = math.atan2(dy, dx)
    al = math.acos(clamp((UPPER ** 2 + d * d - FORE ** 2) / (2 * UPPER * d), -1, 1))
    c1 = (sx + UPPER * math.cos(a + al), sy + UPPER * math.sin(a + al))
    c2 = (sx + UPPER * math.cos(a - al), sy + UPPER * math.sin(a - al))
    e = c1 if (c1[0] - sx) * outward + (c1[1] - sy) * 0.3 > (c2[0] - sx) * outward + (c2[1] - sy) * 0.3 else c2
    return e, (sx + d * math.cos(a), sy + d * math.sin(a))

def default_pose():
    return dict(
        hip_y=-210.0,          # hip height above feet (local units)
        sit=0.0,               # 0 standing .. 1 sitting
        lean=0.0,              # torso lean degrees
        bounce=0.0,
        handL=(-14.0, 150.0),  # viewer-left hand (Leo's RIGHT) relative to its shoulder
        handR=(14.0, 150.0),
        wave=0.0,
        tilt=0.0,              # head tilt degrees
        look=(0.0, 0.0),
        eyes="n",              # n, wide, closed, sleepy
        brows=(0.0, 0.0),      # (raise, inner tilt)
        mouth="smile",         # smile, flat, wobble, o, yawn
    )

def blend_pose(a, b, k):
    o = dict(b if k > 0.5 else a)
    for key in ("hip_y", "sit", "lean", "bounce", "wave", "tilt"):
        o[key] = lerp(a[key], b[key], k)
    for key in ("handL", "handR", "look", "brows"):
        o[key] = lerp2(a[key], b[key], k)
    return o

def hair_path():
    rr = np.random.default_rng(31)
    pts = []
    n = 15
    for i in range(n + 1):
        ang = math.radians(192 + i * (156 / n))
        rad_ = HEAD_R + (26 if i % 2 == 0 else 8) + rr.uniform(-4, 6)
        if i in (0, n):
            rad_ = HEAD_R - 2
        pts.append((math.cos(ang) * rad_, math.sin(ang) * rad_))
    # fringe along forehead (inside the face)
    fr = [(42, -36), (24, -24), (12, -38), (-6, -26), (-20, -40), (-38, -30), (-56, -24)]
    return poly(pts + fr)

HAIR = None

def draw_leo(cv, pose, x, y, silhouette=None):
    """x,y = world feet center. silhouette = color for flat shadow rendering (no features)."""
    global HAIR
    if HAIR is None:
        HAIR = hair_path()
    sil = silhouette is not None
    col = lambda h: silhouette if sil else C(h)
    ink = silhouette if sil else OUTLINE
    cv.save(); cv.translate(x, y); cv.scale(S_LEO, S_LEO)
    cv.translate(0, -pose["bounce"])
    sit = pose["sit"]
    hip = (0.0, pose["hip_y"])
    lean = math.radians(pose["lean"])
    def rot(px, py):  # relative to hip, rotated by lean
        return (hip[0] + px * math.cos(lean) - py * math.sin(lean), hip[1] + px * math.sin(lean) + py * math.cos(lean))
    # legs
    for k in (-1, 1):
        hp = (k * 13, hip[1] + 6)
        foot = (k * lerp(20, 34, sit), 0.0)
        knee = (k * lerp(15, 32, sit), lerp(hip[1] * 0.5, hip[1] + 46, sit))
        pth = skia.Path(); pth.moveTo(*hp); pth.lineTo(*knee); pth.lineTo(*foot)
        cv.drawPath(pth, P(col(LEO["pants"]), stroke=12 if sil else 9))
        cv.drawOval(skia.Rect(foot[0] - 15 + k * 6, -7, foot[0] + 15 + k * 6, 5), P(ink))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-24, hip[1] - 6, 24, hip[1] + 16), 8, 8), P(col(LEO["pants"])))
    # torso (jacket + tee)
    top = rot(0, -TORSO)
    shL, shR = rot(-SH_HALF, -TORSO + 4), rot(SH_HALF, -TORSO + 4)
    jacket = poly([rot(-SH_HALF - 4, -TORSO), rot(SH_HALF + 4, -TORSO), rot(38, -4), rot(-38, -4)])
    cv.drawPath(jacket, P(col(LEO["jacket"])))
    if not sil:
        cv.drawPath(poly([rot(-11, -TORSO + 2), rot(11, -TORSO + 2), rot(12, -6), rot(-12, -6)]), P(C(LEO["tee"])))
        cv.drawPath(jacket, P(ink, stroke=3))
        cv.drawLine(*rot(-11, -TORSO + 2), *rot(-12, -6), P(ink, stroke=2.5))
        cv.drawLine(*rot(11, -TORSO + 2), *rot(12, -6), P(ink, stroke=2.5))
    # arms
    def arm(sh, rel, outward):
        tx, ty = sh[0] + rel[0], sh[1] + rel[1]
        el, hd = ik(sh[0], sh[1], tx, ty, outward)
        sx_ = sh[0] + (el[0] - sh[0]) * 0.6; sy_ = sh[1] + (el[1] - sh[1]) * 0.6
        pth = skia.Path(); pth.moveTo(*sh); pth.lineTo(*el); pth.lineTo(*hd)
        cv.drawPath(pth, P(ink, stroke=9.0 if sil else 5.5))
        cv.drawLine(sh[0], sh[1], sx_, sy_, P(col(LEO["jacket"]), stroke=15))
        if not sil:
            cv.drawLine(sh[0], sh[1], sx_, sy_, P(ink, stroke=1.2))
        cv.drawCircle(hd[0], hd[1], 9.5, P(col(LEO["face"])))
        cv.drawCircle(hd[0], hd[1], 9.5, P(ink, stroke=3))
    hl = pose["handL"]
    if pose["wave"] > 0:
        hl = (hl[0] + 22 * math.sin(pose["wave"]), hl[1])
    arm(shL, hl, -1)
    arm(shR, pose["handR"], 1)
    # neck + head
    neck_top = rot(0, -TORSO - 14)
    cv.drawLine(*top, *neck_top, P(ink, stroke=6))
    hc = rot(0, -TORSO - 14 - HEAD_R + 4)
    cv.save(); cv.translate(*hc); cv.rotate(pose["tilt"] + math.degrees(lean) * 0.4)
    cv.drawCircle(0, 0, HEAD_R, P(col(LEO["face"])))
    if not sil:
        cv.drawPath(HAIR, P(C(LEO["hair"])))
        cv.drawCircle(0, 0, HEAD_R, P(ink, stroke=7))
        cv.drawPath(HAIR, P(ink, stroke=4))
        draw_face(cv, pose)
    else:
        cv.drawPath(HAIR, P(silhouette))
    cv.restore()
    cv.restore()

def draw_face(cv, pose):
    lx, ly = pose["look"]
    e = pose["eyes"]
    for ex in (-1, 1):
        cx, cy = ex * 22 + lx * 6, 4 + ly * 6
        if e == "closed":
            p = skia.Path(); p.moveTo(cx - 10, cy); p.quadTo(cx, cy + 7, cx + 10, cy)
            cv.drawPath(p, P(OUTLINE, stroke=4.5))
        elif e == "sleepy":
            cv.drawOval(skia.Rect(cx - 9, cy - 3, cx + 9, cy + 5), P(OUTLINE))
        else:
            rx, ry = (10.5, 15.5) if e == "wide" else (8, 12)
            cv.drawOval(skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry), P(OUTLINE))
    raise_, tilt = pose["brows"]
    for ex in (-1, 1):
        bx = ex * 22 + lx * 4
        by = -22 - raise_
        cv.drawLine(bx - 11, by + ex * tilt * -1 if False else by - tilt * (1 if ex < 0 else 1) * 0, bx + 11, by, P(OUTLINE, stroke=4.5)) if False else None
        inner = (bx - ex * 11, by + tilt)
        outer = (bx + ex * 11, by)
        cv.drawLine(inner[0], inner[1], outer[0], outer[1], P(OUTLINE, stroke=4.5))
    m = pose["mouth"]; my = 36
    if m == "smile":
        p = skia.Path(); p.moveTo(-13, my - 3); p.quadTo(0, my + 7, 13, my - 3); cv.drawPath(p, P(OUTLINE, stroke=4))
    elif m == "flat":
        cv.drawLine(-9, my, 9, my, P(OUTLINE, stroke=4))
    elif m == "wobble":
        p = skia.Path(); p.moveTo(-12, my)
        for k in range(1, 5):
            p.lineTo(-12 + k * 6, my + (3 if k % 2 else -1))
        cv.drawPath(p, P(OUTLINE, stroke=3.5))
    elif m == "o":
        cv.drawOval(skia.Rect(-6, my - 7, 6, my + 7), P(OUTLINE))
    elif m == "yawn":
        cv.drawOval(skia.Rect(-12, my - 14, 12, my + 14), P(OUTLINE))
        cv.drawOval(skia.Rect(-7, my + 2, 7, my + 11), P(C("c8505a")))

# shadow projection: local (scaled) char coords -> floor, stretching toward the wardrobe (upper-left)
SHADOW_COL = C("2b2a2e", 0.82)
SH_MAT = (0.5, 0.45)

def draw_shadow(cv, pose, fx, fy):
    kx, ky = SH_MAT
    m = skia.Matrix.MakeAll(1.0, kx, fx, 0.05, ky, fy, 0, 0, 1)
    cv.save(); cv.clipPath(FLOOR_POLY, skia.ClipOp.kIntersect, True)
    cv.concat(m)
    cv.saveLayerAlpha(None, 228)
    draw_leo(cv, pose, 0, 0, silhouette=C("26252a"))
    cv.restore()
    cv.restore()

def contact_shadow(cv, fx, fy):
    cv.drawOval(skia.Rect(fx - 70, fy - 14, fx + 70, fy + 14), P(C("1a1008", 0.35), blur=10))

# ================================================================== camera + render
def apply_camera(cv, cam):
    z, wx, wy = cam
    cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-wx, -wy)

def render_clip(name, frame_fn, seconds=10.0):
    room_image()
    N = int(round(seconds * FPS))
    out = os.path.join(HERE, f"{name}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
                          stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    last = None
    for fi in range(N):
        t = fi / FPS
        cv = surf.getCanvas(); cv.clear(C("000000"))
        frame_fn(cv, t)
        img = surf.makeImageSnapshot()
        ff.stdin.write(img.toarray().tobytes())
        last = img
    ff.stdin.close(); ff.wait()
    last.save(os.path.join(HERE, f"{name}_endframe.png"), skia.kPNG)
    return out
