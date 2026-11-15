"""What If Your Shadow Started Living Its Own Life? — full 120 s render (12 x 10 s clips)."""
import math, os, subprocess, sys
import numpy as np
import skia
import common as K
from common import C, P, lin, rad, poly, ss, lerp, lerp2, clamp, OUTLINE, W, H, FPS, HERE
import clip1 as C1

# ================================================================== generic flat person
CFG_LEO = dict(hair="messy", hair_col="4b2f20", top="jacket", top_col="e2a72e", tee="ffffff", pants="1f2a4a")
CFG_GIRL = dict(hair="pigtails", hair_col="1d1d1f", top="dress", top_col="f48fb1", tee=None, pants="1d1d1f")
CFG_SHOP = dict(hair="short", hair_col="a3a3a3", top="shirt", top_col="3a9d5d", tee=None, pants="6b4a2b")
CFG_CYCL = dict(hair="short", hair_col="e8742a", top="shirt", top_col="d64541", tee=None, pants="2b2d42")
UPPER, FORE, HEAD_R, SH_HALF, TORSO = K.UPPER, K.FORE, K.HEAD_R, K.SH_HALF, K.TORSO

def pose0(**kw):
    p = K.default_pose()
    p.update(dict(stride=0.0, phase=0.0, back=False, jump=0.0, point=None))
    p.update(kw)
    return p

_HAIR = {}

def hair_shape(kind):
    if kind in _HAIR:
        return _HAIR[kind]
    if kind == "messy":
        pth = K.hair_path()
    elif kind == "short":
        pth = skia.Path()
        pth.addArc(skia.Rect(-HEAD_R - 6, -HEAD_R - 10, HEAD_R + 6, HEAD_R + 2), 180, 180)
        pth.lineTo(HEAD_R - 4, -20); pth.quadTo(20, -44, 0, -30); pth.quadTo(-30, -46, -HEAD_R + 4, -18); pth.close()
    else:  # pigtails
        pth = skia.Path()
        pth.addArc(skia.Rect(-HEAD_R - 4, -HEAD_R - 6, HEAD_R + 4, HEAD_R), 180, 180)
        pth.lineTo(HEAD_R - 6, -22); pth.quadTo(0, -40, -HEAD_R + 6, -22); pth.close()
    _HAIR[kind] = pth
    return pth

def draw_person(cv, pose, x, y, cfg, sc, silhouette=None):
    sil = silhouette is not None
    col = lambda h: silhouette if sil else C(h)
    ink = silhouette if sil else OUTLINE
    cv.save(); cv.translate(x, y - pose.get("jump", 0.0)); cv.scale(sc, sc)
    cv.translate(0, -pose["bounce"])
    sit = pose["sit"]
    hip = (0.0, pose["hip_y"])
    lean = math.radians(pose["lean"])
    def rot(px, py):
        return (hip[0] + px * math.cos(lean) - py * math.sin(lean), hip[1] + px * math.sin(lean) + py * math.cos(lean))
    st, ph = pose.get("stride", 0.0), pose.get("phase", 0.0)
    dress = cfg["top"] == "dress"
    # legs
    for i, k in enumerate((-1, 1)):
        sw = math.sin(ph + i * math.pi)
        lift = max(0.0, math.cos(ph + i * math.pi)) * 18 * st
        hp = (k * 13, hip[1] + 6)
        foot = (k * lerp(20, 34, sit) + 38 * st * sw, -lift)
        knee = (k * lerp(15, 32, sit) + 26 * st * sw, lerp(hip[1] * 0.5, hip[1] + 46, sit) - lift * 0.6)
        pth = skia.Path(); pth.moveTo(*hp); pth.lineTo(*knee); pth.lineTo(*foot)
        if dress:
            cv.drawPath(pth, P(ink, stroke=6))
        else:
            cv.drawPath(pth, P(col(cfg["pants"]), stroke=12 if sil else 9))
        cv.drawOval(skia.Rect(foot[0] - 15 + k * 6, foot[1] - 7, foot[0] + 15 + k * 6, foot[1] + 5), P(ink))
    if not dress:
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-24, hip[1] - 6, 24, hip[1] + 16), 8, 8), P(col(cfg["pants"])))
    top = rot(0, -TORSO)
    shL, shR = rot(-SH_HALF, -TORSO + 4), rot(SH_HALF, -TORSO + 4)
    if dress:
        body = poly([rot(-SH_HALF + 2, -TORSO), rot(SH_HALF - 2, -TORSO), rot(58, 40), rot(-58, 40)])
    else:
        body = poly([rot(-SH_HALF - 4, -TORSO), rot(SH_HALF + 4, -TORSO), rot(38, -4), rot(-38, -4)])
    cv.drawPath(body, P(col(cfg["top_col"])))
    if not sil:
        if cfg.get("tee") and not pose.get("back"):
            cv.drawPath(poly([rot(-11, -TORSO + 2), rot(11, -TORSO + 2), rot(12, -6), rot(-12, -6)]), P(C(cfg["tee"])))
            cv.drawLine(*rot(-11, -TORSO + 2), *rot(-12, -6), P(ink, stroke=2.5))
            cv.drawLine(*rot(11, -TORSO + 2), *rot(12, -6), P(ink, stroke=2.5))
        cv.drawPath(body, P(ink, stroke=3))
    def arm(sh, rel, outward):
        tx, ty = sh[0] + rel[0], sh[1] + rel[1]
        el, hd = K.ik(sh[0], sh[1], tx, ty, outward)
        sx_, sy_ = sh[0] + (el[0] - sh[0]) * 0.6, sh[1] + (el[1] - sh[1]) * 0.6
        pth = skia.Path(); pth.moveTo(*sh); pth.lineTo(*el); pth.lineTo(*hd)
        cv.drawPath(pth, P(ink, stroke=9.0 if sil else 5.5))
        if not dress:
            cv.drawLine(sh[0], sh[1], sx_, sy_, P(col(cfg["top_col"]), stroke=15))
        cv.drawCircle(hd[0], hd[1], 9.5, P(col("ffffff")))
        cv.drawCircle(hd[0], hd[1], 9.5, P(ink, stroke=3))
    hl = pose["handL"]
    if pose["wave"] > 0:
        hl = (hl[0] + 22 * math.sin(pose["wave"]), hl[1])
    arm(shL, hl, -1)
    hr = pose["handR"]
    if pose.get("waveR", 0) > 0:
        hr = (hr[0] + 22 * math.sin(pose["waveR"]), hr[1])
    arm(shR, hr, 1)
    neck_top = rot(0, -TORSO - 14)
    cv.drawLine(*top, *neck_top, P(ink, stroke=6))
    hc = rot(0, -TORSO - 14 - HEAD_R + 4)
    cv.save(); cv.translate(*hc); cv.rotate(pose["tilt"] + math.degrees(lean) * 0.4)
    hs = hair_shape(cfg["hair"])
    if cfg["hair"] == "pigtails":
        for sx in (-1, 1):
            cv.drawCircle(sx * (HEAD_R + 12), -18, 20, P(col(cfg["hair_col"])))
            if not sil:
                cv.drawCircle(sx * (HEAD_R + 12), -18, 20, P(ink, stroke=3))
                cv.drawCircle(sx * (HEAD_R - 2), -22, 6, P(C("f06292")))
    if sil:
        cv.drawCircle(0, 0, HEAD_R, P(silhouette)); cv.drawPath(hs, P(silhouette))
    elif pose.get("back"):
        cv.drawCircle(0, 0, HEAD_R, P(C(cfg["hair_col"])))
        cv.drawPath(hs, P(C(cfg["hair_col"])))
        cv.drawCircle(0, 0, HEAD_R, P(ink, stroke=7)); cv.drawPath(hs, P(ink, stroke=4))
    else:
        cv.drawCircle(0, 0, HEAD_R, P(C("ffffff")))
        cv.drawPath(hs, P(C(cfg["hair_col"])))
        cv.drawCircle(0, 0, HEAD_R, P(ink, stroke=7))
        cv.drawPath(hs, P(ink, stroke=4))
        K.draw_face(cv, pose)
    cv.restore()
    cv.restore()

def draw_shadow(cv, pose, fx, fy, cfg, sc, mat, clip=None, alpha=226, stretch=1.0):
    a, b, c, d = mat
    m = skia.Matrix.MakeAll(a, b * stretch, fx, c, d * stretch, fy, 0, 0, 1)
    cv.save()
    if clip is not None:
        cv.clipPath(clip, skia.ClipOp.kIntersect, True)
    cv.concat(m)
    cv.saveLayerAlpha(None, alpha)
    sp = dict(pose); sp["jump"] = 0.0
    draw_person(cv, sp, 0, 0, cfg, sc, silhouette=C("26252a"))
    cv.restore(); cv.restore()

def point_rel(mat, dirx, diry, reach=146.0):
    """hand offset (local, from shoulder) that makes the SHADOW arm point along world direction (dirx, diry)"""
    a, b, c, d = mat
    det = a * d - b * c
    lx = (d * dirx - b * diry) / det
    ly = (-c * dirx + a * diry) / det
    n = math.hypot(lx, ly) or 1
    return (lx / n * reach, ly / n * reach)

def contact(cv, x, y, sc=1.0):
    cv.drawOval(skia.Rect(x - 70 * sc, y - 14 * sc, x + 70 * sc, y + 14 * sc), P(C("1a1008", 0.32), blur=10 * sc))

def walk(t, t0, t1, speed=7.0, amt=0.8):
    if t0 <= t < t1:
        return amt * min(ss(t0, t0 + 0.2, t), 1 - ss(t1 - 0.2, t1, t)), (t - t0) * speed
    return 0.0, 0.0

# ================================================================== camera
CUR_WORLD = [W, H]

def cam(cv, z, wx, wy):
    ww, wh = CUR_WORLD
    hw, hh = W / 2 / z, H / 2 / z
    wx = clamp(wx, hw, max(hw, ww - hw)); wy = clamp(wy, hh, max(hh, wh - hh))
    cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-wx, -wy)

def draw_img(cv, img, ssf):
    cv.save(); cv.scale(1 / ssf, 1 / ssf)
    cv.drawImage(img, 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
    cv.restore()

_IMG = {}

def env_image(name, w, h, fn, ssf=1.6):
    if name not in _IMG:
        surf = skia.Surface(int(w * ssf), int(h * ssf))
        c = surf.getCanvas(); c.scale(ssf, ssf); fn(c)
        _IMG[name] = (surf.makeImageSnapshot(), ssf)
    return _IMG[name]

def box(cv, front, side=None, top=None, cf=("b07b52", "9a6b45"), cs="7a5032", ct="c99a6a"):
    if side:
        cv.drawPath(poly(side), P(C(cs)))
    if top:
        cv.drawPath(poly(top), P(C(ct)))
    ys = [p[1] for p in front]
    cv.drawPath(poly(front), P(0, shader=lin(0, min(ys), 0, max(ys), [C(cf[0]), C(cf[1])])))

# ================================================================== BEDROOM extras (front door on right wall)
def bedroom_door(cv):
    ss_ = (1.07, 1.27)
    pts = [K.depth_pt(960, 640, ss_[0]), K.depth_pt(960, 640, ss_[1]), K.depth_pt(960, 1250, ss_[1]), K.depth_pt(960, 1250, ss_[0])]
    cv.drawPath(poly(pts), P(0, shader=lin(pts[0][0], 0, pts[1][0], 0, [C("9a6a44"), C("b5835a")])))
    cv.drawPath(poly(pts), P(C("f6f0e4"), stroke=10))
    kx, ky = K.depth_pt(960, 960, ss_[0] + 0.03)
    cv.drawCircle(kx, ky, 7, P(C("e2c48a")))
    for f in (0.25, 0.65):
        a = lerp2(pts[0], pts[3], f); b = lerp2(pts[1], pts[2], f)
        cv.drawLine(a[0] + 8, a[1], b[0] - 8, b[1], P(C("6e4a2e", 0.5), stroke=3))
DOOR_PT = K.depth_pt(960, 1000, 1.17)

def bedroom_base(cv, t):
    K.draw_room(cv)
    bedroom_door(cv)

# ================================================================== HALLWAY
HVP = (540.0, 860.0)
HB = (300.0, 520.0, 780.0, 1180.0)

def hray(p, y):
    t_ = (y - HVP[1]) / (p[1] - HVP[1]); return (HVP[0] + (p[0] - HVP[0]) * t_, y)

def hdp(x, y, s):
    return (HVP[0] + (x - HVP[0]) * s, HVP[1] + (y - HVP[1]) * s)

HALL_FLOOR = None
HALL_SHELF_POT = (972.0, 640.0)
HALL_POT_LAND = (930.0, 1490.0)

def hall_static(cv):
    global HALL_FLOOR
    x0, y0, x1, y1 = HB
    cl, cr = hray((x0, y0), -10), hray((x1, y0), -10)
    fl, fr = hray((x0, y1), H + 10), hray((x1, y1), H + 10)
    cv.drawPath(poly([(x0, y0), (x1, y0), cr, cl]), P(C("f3ecdf")))
    cv.drawPath(poly([cl, (x0, y0), (x0, y1), fl, (-900, H + 10), (-900, -10)]), P(0, shader=lin(-300, 0, x0, 0, [C("dccfb9"), C("e9dfcc")])))
    cv.drawPath(poly([cr, (x1, y0), (x1, y1), fr, (2000, H + 10), (2000, -10)]), P(0, shader=lin(x1, 0, 1300, 0, [C("efe5d1"), C("f8eedb")])))
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(0, shader=lin(0, y0, 0, y1, [C("f1e8d7"), C("e7dcc6")])))
    HALL_FLOOR = poly([(x0, y1), (x1, y1), fr, fl])
    cv.save(); cv.clipPath(HALL_FLOOR, skia.ClipOp.kIntersect, True)
    tones = ["b98659", "a9744b", "c2905f", "b07a4f", "9f6b44", "bd8a5c"]
    rr = np.random.default_rng(3)
    xs = list(np.arange(x0 - 900, x1 + 900, 30))
    for i in range(len(xs) - 1):
        a, b = xs[i], xs[i + 1]
        cv.drawPath(poly([(a, y1), (b, y1), hray((b, y1), H + 10), hray((a, y1), H + 10)]), P(C(tones[i % 6])))
        for k in range(6):
            s = 1 + rr.uniform(0.1, 2.0)
            pa, pb = hdp(a, y1, s), hdp(b, y1, s)
            cv.drawLine(pa[0], pa[1], pb[0], pb[1], P(C("6e4a2e", 0.5), stroke=1.6 * s))
        cv.drawLine(a, y1, *hray((a, y1), H + 10), P(C("5e3d24", 0.55), stroke=2))
    cv.drawRect(skia.Rect(-900, y1, 2000, H), P(0, shader=lin(0, y1, 0, H, [C("2a1608", 0.3), C("2a1608", 0), C("000000", 0.1)], [0, 0.5, 1])))
    # light from door spilling forward
    cv.drawPath(poly([(440, y1), (650, y1), (900, H), (240, H)]), P(C("fff0c8", 0.22), blur=30))
    cv.restore()
    for (a, b) in (((x0, y0), (x0, y1)), ((x1, y0), (x1, y1))):
        cv.drawLine(a[0], a[1], b[0], b[1], P(C("8a7a60", 0.3), stroke=10, blur=8))
    cv.drawRect(skia.Rect(x0, y1 - 20, x1, y1), P(C("faf6ee")))
    # front door (open) with bright exterior
    dx0, dx1, dy0 = 430.0, 650.0, 660.0
    cv.drawRect(skia.Rect(dx0, dy0, dx1, y1), P(0, shader=lin(0, dy0, 0, y1, [C("bfe3ff"), C("e9f6ff")])))
    cv.drawRect(skia.Rect(dx0, 860, dx1, 1110), P(C("f4b393")))
    for k in range(3):
        cv.drawRect(skia.Rect(dx0 + 20 + k * 70, 900, dx0 + 60 + k * 70, 960), P(C("8fd3e8")))
    cv.drawRect(skia.Rect(dx0, 1110, dx1, y1), P(C("e9dcc0")))
    cv.drawRect(skia.Rect(dx0, dy0, dx1, y1), P(C("fff8e6", 0.25)))
    leaf = [(dx0, dy0), hdp(dx0, dy0, 1.3), hdp(dx0, y1, 1.3), (dx0, y1)]
    cv.drawPath(poly(leaf), P(0, shader=lin(leaf[1][0], 0, dx0, 0, [C("8a5d3e"), C("a87650")])))
    cv.drawCircle(lerp(dx0, leaf[1][0], 0.7), 930, 6, P(C("e2c48a")))
    cv.drawRect(skia.Rect(dx0 - 14, dy0 - 14, dx1 + 14, y1), P(C("f6f0e4"), stroke=14))
    # entrance table on left wall + green plant
    def lw(s, frac):  # point on left wall: frac = height fraction from floor
        fy = HVP[1] + (y1 - HVP[1]) * s; cy = HVP[1] + (y0 - HVP[1]) * s; xw = HVP[0] + (x0 - HVP[0]) * s
        return (xw, fy - (fy - cy) * frac)
    s1, s2 = 1.35, 1.75
    a1, a2 = lw(s1, 0.28), lw(s2, 0.28)
    w1, w2 = 80 * s1, 80 * s2
    top = [a1, (a1[0] + w1, a1[1] + 6), (a2[0] + w2, a2[1] + 8), a2]
    f1, f2 = lw(s1, 0.0), lw(s2, 0.0)
    side = [(a1[0] + w1, a1[1] + 6), (a2[0] + w2, a2[1] + 8), (f2[0] + w2, f2[1]), (f1[0] + w1, f1[1])]
    cv.drawPath(poly([(f1[0] + w1, f1[1]), (f2[0] + w2 + 30, f2[1] + 10), (f2[0], f2[1] + 10)]), P(C("2a1608", 0.35), blur=14))
    cv.drawPath(poly(side), P(0, shader=lin(0, a1[1], 0, f2[1], [C("a87650"), C("8a5e3c")])))
    cv.drawPath(poly(top), P(C("c79a6c")))
    px, py = lerp(a1[0], a2[0] + w2, 0.55), lerp(a1[1], a2[1], 0.5)
    cv.drawPath(poly([(px - 34, py - 4), (px + 34, py - 4), (px + 26, py + 48), (px - 26, py + 48)]), P(0, shader=lin(px - 34, 0, px + 34, 0, [C("e8e2d6"), C("bdb4a3")])))
    for k in range(9):
        ang = math.radians(-160 + k * 18)
        ex, ey = px + math.cos(ang) * 95, py - 6 + math.sin(ang) * 120
        cv.drawPath(poly([(px, py - 4), (ex - 14, ey), (ex + 14, ey)]), P(C("3f8a4c" if k % 2 else "2f6b3c")))
    # high shelf on right wall
    sh = [(905, 700), (1060, 690), (1060, 716), (905, 724)]
    cv.drawPath(poly([(905, 724), (1060, 716), (1060, 760), (930, 770)]), P(C("6b5a40", 0.25), blur=10))
    cv.drawPath(poly(sh), P(0, shader=lin(0, 690, 0, 724, [C("c79a6c"), C("8a5e3c")])))

def pot_shape(cv, x, y, sc=1.0, rot=0.0):
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(sc, sc)
    for k in range(7):
        ang = math.radians(-150 + k * 20)
        cv.drawPath(poly([(0, -50), (math.cos(ang) * 70 - 9, -50 + math.sin(ang) * 80), (math.cos(ang) * 70 + 9, -50 + math.sin(ang) * 80)]), P(C("3f8a4c" if k % 2 else "2f6b3c")))
    body = poly([(-40, -55), (40, -55), (30, 30), (-30, 30)])
    cv.drawPath(body, P(0, shader=lin(-40, 0, 40, 0, [C("6fa8c9"), C("3c7aa0"), C("2a5d7d")], [0, 0.5, 1])))
    cv.drawRect(skia.Rect(-44, -62, 44, -48), P(C("4f8db2")))
    cv.drawLine(-22, -40, -18, 20, P(C("ffffff", 0.45), stroke=6))
    cv.restore()

SHARDS = [(np.cos(a) * r, np.sin(a) * r * 0.35, a * 40, s) for a, r, s in zip(np.linspace(0, 6.2, 11), [70, 110, 60, 130, 90, 40, 120, 80, 100, 55, 75], [1, .8, 1.2, .7, .9, 1.1, .6, .8, 1, .9, .7])]

def shards(cv, x, y, k, sc=1.0):
    cv.drawOval(skia.Rect(x - 60 * sc, y - 14 * sc, x + 60 * sc, y + 14 * sc), P(C("5a3a20", 0.5 * k), blur=6))
    for (dx, dy, a, s) in SHARDS:
        px, py = x + dx * k * sc, y + dy * k * sc
        cv.save(); cv.translate(px, py); cv.rotate(a); cv.scale(s * sc, s * sc)
        cv.drawPath(poly([(-14, -8), (16, -10), (10, 9), (-12, 7)]), P(C("3c7aa0")))
        cv.drawLine(-10, -6, 12, -8, P(C("8fc2de"), stroke=3))
        cv.restore()
    for k2 in range(5):
        cv.drawCircle(x - 40 * sc + k2 * 20 * sc, y + 4 * sc, 8 * sc, P(C("4a3524", 0.8)))
    cv.drawPath(poly([(x - 20 * sc, y), (x + 30 * sc, y - 30 * sc), (x + 40 * sc, y - 24 * sc), (x - 10 * sc, y + 6 * sc)]), P(C("2f6b3c")))

def hall_scale(fy):
    return 0.00149 * (fy - HVP[1])

# ================================================================== STREET (long panorama)
SW, SH_ = 4000, 2100
FACADE_Y, CURB_Y = 1180.0, 1560.0
STREET_FLOOR = poly([(0, FACADE_Y), (SW, FACADE_Y), (SW, SH_), (0, SH_)])
ALLEY = (2350.0, 2650.0)
ALLEY_FLOOR = poly([(2350.0, FACADE_Y), (2460.0, 1010.0), (2540.0, 1010.0), (2650.0, FACADE_Y)])
STREET_FLOOR_A = skia.Op(STREET_FLOOR, ALLEY_FLOOR, skia.PathOp.kUnion_PathOp)
POTHOLE = (1830.0, 1690.0)

def awning(cv, x0, x1, y, col1, col2):
    depth = 70
    front = [(x0 - 10, y + depth), (x1 + 10, y + depth), (x1 + 10, y + depth + 40), (x0 - 10, y + depth + 40)]
    topq = [(x0, y), (x1, y), (x1 + 10, y + depth), (x0 - 10, y + depth)]
    cv.drawPath(poly([(x0, y + depth + 40), (x1, y + depth + 40), (x1 + 20, y + depth + 110), (x0 + 20, y + depth + 110)]), P(C("000000", 0.18), blur=14))
    n = int((x1 - x0) / 50)
    for k in range(n):
        a = x0 + k * (x1 - x0) / n; b = x0 + (k + 1) * (x1 - x0) / n
        cc = col1 if k % 2 == 0 else col2
        cv.drawPath(poly([(a, y), (b, y), (b + 10 * (b - (x0 + x1) / 2) / (x1 - x0), y + depth), (a + 10 * (a - (x0 + x1) / 2) / (x1 - x0), y + depth)]), P(C(cc)))
    cv.drawPath(poly(topq), P(0, shader=lin(0, y, 0, y + depth, [C("ffffff", 0.15), C("000000", 0.12)])))
    for k in range(n):
        a = x0 - 10 + k * (x1 - x0 + 20) / n
        cv.drawPath(poly([(a, y + depth), (a + (x1 - x0 + 20) / n, y + depth), (a + (x1 - x0 + 20) / n - 12, y + depth + 40), (a + 12, y + depth + 40)]) if False else
                    poly([(a, y + depth), (a + (x1 - x0 + 20) / n, y + depth), (a + (x1 - x0 + 20) / n, y + depth + 36), (a, y + depth + 36)]), P(C(col1 if k % 2 == 0 else col2)))
    cv.drawRect(skia.Rect(x0 - 10, y + depth + 30, x1 + 10, y + depth + 40), P(C("000000", 0.15)))

def window(cv, x0, y0, x1, y1, frame="ffffff"):
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(0, shader=lin(x0, y0, x1, y1, [C("bfe6f5"), C("6fa9c2")])))
    cv.drawRect(skia.Rect(x0, y0, x1, y0 + 14), P(C("000000", 0.22)))
    cv.drawRect(skia.Rect(x0, y0, x0 + 10, y1), P(C("000000", 0.15)))
    cv.drawPath(poly([(x0 + 10, y1), (x0 + 0.45 * (x1 - x0), y0 + 14), (x0 + 0.6 * (x1 - x0), y0 + 14), (x0 + 25, y1)]), P(C("ffffff", 0.25)))
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(C(frame), stroke=8))
    cv.drawRect(skia.Rect(x0 - 8, y1, x1 + 8, y1 + 12), P(C(frame)))
    cv.drawRect(skia.Rect(x0 - 8, y1 + 12, x1 + 8, y1 + 18), P(C("000000", 0.15)))

def tree(cv, x, base):
    cv.drawOval(skia.Rect(x - 90, base - 18, x + 140, base + 22), P(C("1a1008", 0.3), blur=12))
    cv.drawRect(skia.Rect(x - 14, base - 330, x + 14, base), P(0, shader=lin(x - 14, 0, x + 14, 0, [C("7a5232"), C("5a3a22")])))
    rr = np.random.default_rng(int(x))
    for k in range(14):
        cx, cy, r = x + rr.uniform(-110, 110), base - 420 + rr.uniform(-110, 90), rr.uniform(60, 95)
        cv.drawCircle(cx, cy, r, P(0, shader=rad(cx - r * 0.4, cy - r * 0.5, r * 1.4, [C("7cc26e"), C("3f8a4c"), C("2b6a38")], [0, 0.6, 1])))
    cv.drawRect(skia.Rect(x - 50, base - 10, x + 50, base + 6), P(C("7a6a55", 0.6)))

def bench(cv, x, base):
    cv.drawOval(skia.Rect(x - 130, base - 10, x + 150, base + 16), P(C("1a1008", 0.3), blur=8))
    for lx in (x - 100, x + 100):
        cv.drawRect(skia.Rect(lx - 8, base - 90, lx + 8, base), P(C("3a3a3a")))
    for k in range(3):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x - 130, base - 100 - k * 34, x + 130, base - 80 - k * 34), 4, 4), P(0, shader=lin(0, base - 100 - k * 34, 0, base - 80 - k * 34, [C("c08a5a"), C("8a5e3c")])))

def bicycle(cv, x, base, frame="2f6fb0", sc=1.0, rider=False, wob=0.0):
    cv.save(); cv.translate(x, base); cv.scale(sc, sc); cv.rotate(wob)
    for wx in (-70, 70):
        cv.drawCircle(wx, -48, 46, P(C("222222"), stroke=8))
        cv.drawCircle(wx, -48, 36, P(C("9a9a9a", 0.6), stroke=2))
        cv.drawCircle(wx, -48, 6, P(C("777777")))
    pts = [(-70, -48), (-10, -48), (40, -110), (-30, -110), (-70, -48)]
    cv.drawPath(poly(pts, close=False), P(0, stroke=9, shader=lin(-70, -110, 70, -48, [C(frame), C("1d4a7a")])))
    cv.drawLine(-10, -48, -40, -125, P(C(frame), stroke=8))
    cv.drawLine(40, -110, 70, -48, P(C(frame), stroke=8))
    cv.drawLine(40, -110, 48, -150, P(C("333333"), stroke=7))
    cv.drawLine(36, -150, 66, -152, P(C("333333"), stroke=7))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-62, -136, -22, -124), 6, 6), P(C("2b2b2b")))
    cv.restore()

def food_stand(cv, x, base):
    cv.drawOval(skia.Rect(x - 140, base - 14, x + 170, base + 20), P(C("1a1008", 0.3), blur=10))
    box(cv, [(x - 120, base - 200), (x + 120, base - 200), (x + 120, base - 30), (x - 120, base - 30)],
        side=[(x + 120, base - 200), (x + 150, base - 220), (x + 150, base - 50), (x + 120, base - 30)],
        top=[(x - 120, base - 200), (x + 120, base - 200), (x + 150, base - 220), (x - 90, base - 220)], cf=("f2c14e", "d9a32a"), cs="b8861c", ct="fbe3a0")
    for wx in (x - 80, x + 80):
        cv.drawCircle(wx, base - 26, 24, P(C("333333"))); cv.drawCircle(wx, base - 26, 9, P(C("aaaaaa")))
    cv.drawLine(x, base - 220, x, base - 420, P(C("6b5a40"), stroke=8))
    for k in range(8):
        a0 = math.pi + k * math.pi / 8; a1 = math.pi + (k + 1) * math.pi / 8
        cv.drawPath(poly([(x, base - 470), (x + math.cos(a0) * 190, base - 400 + math.sin(a0) * -10), (x + math.cos(a1) * 190, base - 400 + math.sin(a1) * -10)]), P(C("e74c3c" if k % 2 else "ffffff")))
    text_ = skia.Font(K_TF, 34)
    cv.drawString("SNACKS", x - 70, base - 110, text_, P(C("7a4a10")))

K_TF = skia.Typeface.MakeFromFile("/usr/share/fonts/opentype/inter/Inter-Black.otf")

def storefront(cv, x0, x1, top, col, trim, kind="shop", seed=1):
    cv.drawRect(skia.Rect(x0, top, x1, FACADE_Y), P(0, shader=lin(x0, 0, x1, 0, [C(col), C(col)])))
    cv.drawRect(skia.Rect(x0, top, x1, FACADE_Y), P(0, shader=lin(0, top, 0, FACADE_Y, [C("ffffff", 0.12), C("000000", 0.08)])))
    cv.drawRect(skia.Rect(x0 - 8, top - 26, x1 + 8, top), P(C(trim)))
    cv.drawRect(skia.Rect(x0 - 8, top, x1 + 8, top + 10), P(C("000000", 0.15)))
    cv.drawLine(x1, top, x1, FACADE_Y, P(C("000000", 0.18), stroke=6))
    rr = np.random.default_rng(seed)
    ww = x1 - x0
    nw = max(2, int(ww / 210))
    for row, (wy0, wy1) in enumerate(((top + 70, top + 250),)):
        for k in range(nw):
            cx = x0 + (k + 0.5) * ww / nw
            window(cv, cx - 55, wy0, cx + 55, wy1)
    if kind == "shop":
        sy = top + 330
        awning(cv, x0 + 30, x1 - 30, sy, trim, "ffffff")
        cv.drawRect(skia.Rect(x0 + 40, sy + 150, x1 - 40, FACADE_Y - 10), P(C("3d3a36")))
        cv.drawRect(skia.Rect(x0 + 50, sy + 160, x1 - 50, FACADE_Y - 20), P(0, shader=lin(x0, sy, x1, FACADE_Y, [C("a8d8ea"), C("5a8fa6")])))
        for k in range(3):
            cv.drawPath(poly([(x0 + 80 + k * 200, FACADE_Y - 20), (x0 + 180 + k * 200, sy + 160), (x0 + 220 + k * 200, sy + 160), (x0 + 120 + k * 200, FACADE_Y - 20)]), P(C("ffffff", 0.18)))
        dx = x0 + ww * 0.7
        cv.drawRect(skia.Rect(dx - 60, sy + 170, dx + 60, FACADE_Y - 10), P(C("6b4a2e")))
        cv.drawRect(skia.Rect(dx - 48, sy + 190, dx + 48, sy + 330), P(C("bfe6f5", 0.8)))
        cv.drawCircle(dx + 38, sy + 400, 6, P(C("e2c48a")))
    cv.drawRect(skia.Rect(x0, FACADE_Y - 14, x1, FACADE_Y), P(C("000000", 0.18)))

def pavement(cv, x0, x1):
    cv.drawRect(skia.Rect(x0, FACADE_Y, x1, CURB_Y), P(0, shader=lin(0, FACADE_Y, 0, CURB_Y, [C("e6d6b8"), C("d9c7a5")])))
    for yy in np.arange(FACADE_Y + 60, CURB_Y, 75):
        cv.drawLine(x0, yy, x1, yy, P(C("b8a582", 0.7), stroke=2.5))
    for xx in np.arange(x0 - 400, x1 + 400, 110):
        cv.drawLine(xx, FACADE_Y, xx - 0.32 * (CURB_Y - FACADE_Y), CURB_Y, P(C("b8a582", 0.7), stroke=2.5))
    cv.drawRect(skia.Rect(x0, FACADE_Y, x1, FACADE_Y + 40), P(0, shader=lin(0, FACADE_Y, 0, FACADE_Y + 40, [C("5a4a30", 0.25), C("5a4a30", 0)])))
    cv.drawRect(skia.Rect(x0, CURB_Y, x1, CURB_Y + 26), P(0, shader=lin(0, CURB_Y, 0, CURB_Y + 26, [C("f0e6d2"), C("a89c86")])))
    cv.drawRect(skia.Rect(x0, CURB_Y + 26, x1, 4000), P(0, shader=lin(0, CURB_Y + 26, 0, 2100, [C("55585e"), C("44474c")])))
    rr = np.random.default_rng(5)
    for k in range(int((x1 - x0) / 6)):
        px, py = rr.uniform(x0, x1), rr.uniform(CURB_Y + 30, 2100)
        cv.drawCircle(px, py, rr.uniform(1, 2.5), P(C("6a6d73" if k % 2 else "3a3c40", 0.6)))
    cv.drawRect(skia.Rect(x0, CURB_Y + 26, x1, CURB_Y + 50), P(C("000000", 0.2), blur=6))

def street_static(cv):
    cv.drawRect(skia.Rect(0, 0, SW, FACADE_Y), P(0, shader=lin(0, 0, 0, 700, [C("6fb7ef"), C("bfe3ff")])))
    for k in range(6):
        cx = 300 + k * 700; cy = 160 + (k % 2) * 60
        for j in range(4):
            cv.drawCircle(cx + j * 50, cy + (j % 2) * -20, 50, P(C("ffffff", 0.9)))
    pavement(cv, 0, SW)
    # buildings
    storefront(cv, 0, 760, 260, "f1e4cc", "c9b38c", kind="home", seed=1)
    # apartment entrance (open door, interior glimpse with shards)
    dx0, dx1, dy0 = 300.0, 480.0, 820.0
    cv.drawRect(skia.Rect(dx0 - 20, dy0 - 20, dx1 + 20, FACADE_Y), P(C("faf6ee")))
    cv.drawRect(skia.Rect(dx0, dy0, dx1, FACADE_Y), P(0, shader=lin(0, dy0, 0, FACADE_Y, [C("e9dfcc"), C("c9b89c")])))
    cv.drawPath(poly([(dx0, 1080), (dx1, 1080), (dx1, FACADE_Y), (dx0, FACADE_Y)]), P(C("b07c52")))
    shards(cv, 410, 1120, 1.0, sc=0.28)
    cv.drawPath(poly([(dx0, dy0), (dx0 - 60, dy0 + 30), (dx0 - 60, FACADE_Y + 20), (dx0, FACADE_Y)]), P(C("8a5d3e")))
    cv.drawRect(skia.Rect(dx0 - 40, FACADE_Y - 6, dx1 + 40, FACADE_Y + 18), P(C("d9cfbd")))
    storefront(cv, 760, 1450, 300, "f4b393", "e07a5f", seed=2)
    storefront(cv, 1450, 2350, 240, "3fb8af", "2a8a83", seed=3)
    # alley between storefronts (perspective)
    a0, a1 = ALLEY
    vp = ((a0 + a1) / 2, 880)
    cv.drawRect(skia.Rect(a0, 300, a1, FACADE_Y), P(C("cfe9f7")))
    cv.drawPath(poly([(a0, 300), (vp[0] - 40, 760), (vp[0] - 40, 1010), (a0, FACADE_Y)]), P(0, shader=lin(a0, 0, vp[0], 0, [C("e89f7e"), C("c9846a")])))
    cv.drawPath(poly([(a1, 300), (vp[0] + 40, 760), (vp[0] + 40, 1010), (a1, FACADE_Y)]), P(0, shader=lin(a1, 0, vp[0], 0, [C("38a39b"), C("2b807a")])))
    cv.drawPath(poly([(a0, FACADE_Y), (vp[0] - 40, 1010), (vp[0] + 40, 1010), (a1, FACADE_Y)]), P(C("d8c6a2")))
    cv.drawRect(skia.Rect(vp[0] - 40, 760, vp[0] + 40, 1010), P(C("fff4d6")))
    for k in range(4):
        u = k / 4
        cv.drawLine(lerp(a0, vp[0] - 40, u), lerp(FACADE_Y, 1010, u), lerp(a1, vp[0] + 40, u), lerp(FACADE_Y, 1010, u), P(C("b8a582", 0.7), stroke=2))
    storefront(cv, 2650, 3300, 280, "f4b393", "e07a5f", seed=4)
    storefront(cv, 3300, 4000, 230, "3fb8af", "2a8a83", seed=5)
    # props
    tree(cv, 1150, 1500); tree(cv, 2200, 1500); tree(cv, 3050, 1500)
    bench(cv, 980, 1300)
    bicycle(cv, 1850, 1260, frame="e07a5f", sc=0.9); bicycle(cv, 1990, 1260, frame="2f6fb0", sc=0.9)
    food_stand(cv, 3450, 1330)
    # pothole
    px, py = POTHOLE
    cv.drawOval(skia.Rect(px - 60, py - 16, px + 60, py + 16), P(C("2a2b2e")))
    cv.drawOval(skia.Rect(px - 60, py - 16, px + 60, py + 16), P(C("6a6d73"), stroke=4))
    for xx in np.arange(0, SW, 260):
        cv.drawRect(skia.Rect(xx, 1890, xx + 150, 1904), P(C("f2f2f2", 0.85)))

# ================================================================== SHOP / INTERSECTION
SHW, SHH = 2400, 2300
SIGN_C = (600.0, 610.0)
SIGN_W, SIGN_H = 520.0, 150.0
SHOP_DOOR = (780.0, 940.0)
SHOP_FLOOR = poly([(0, FACADE_Y), (SHW, FACADE_Y), (SHW, SHH), (0, SHH)])

def shop_static(cv):
    cv.drawRect(skia.Rect(0, 0, SHW, FACADE_Y), P(0, shader=lin(0, 0, 0, 700, [C("6fb7ef"), C("bfe3ff")])))
    for k in range(4):
        cx = 200 + k * 650
        for j in range(4):
            cv.drawCircle(cx + j * 50, 170 + (j % 2) * -20, 50, P(C("ffffff", 0.9)))
    pavement(cv, 0, SHW)
    # main shop: turquoise + peach
    x0, x1, top = 100.0, 1100.0, 300.0
    cv.drawRect(skia.Rect(x0, top, x1, FACADE_Y), P(C("3fb8af")))
    cv.drawRect(skia.Rect(x0, 820, x1, FACADE_Y), P(C("f4b393")))
    cv.drawRect(skia.Rect(x0, top, x1, FACADE_Y), P(0, shader=lin(0, top, 0, FACADE_Y, [C("ffffff", 0.12), C("000000", 0.08)])))
    cv.drawRect(skia.Rect(x0 - 10, top - 28, x1 + 10, top), P(C("2a8a83")))
    cv.drawRect(skia.Rect(x0 - 10, 812, x1 + 10, 826), P(C("e07a5f")))
    for cx in (230, 980):
        window(cv, cx - 60, 380, cx + 60, 520)
    # display window + door
    cv.drawRect(skia.Rect(160, 860, 700, FACADE_Y - 16), P(C("3d3a36")))
    cv.drawRect(skia.Rect(172, 872, 688, FACADE_Y - 26), P(0, shader=lin(160, 860, 700, FACADE_Y, [C("a8d8ea"), C("5a8fa6")])))
    for k in range(3):
        cv.drawPath(poly([(200 + k * 170, FACADE_Y - 26), (290 + k * 170, 872), (330 + k * 170, 872), (240 + k * 170, FACADE_Y - 26)]), P(C("ffffff", 0.18)))
    d0, d1 = SHOP_DOOR
    cv.drawRect(skia.Rect(d0 - 14, 846, d1 + 14, FACADE_Y), P(C("2a8a83")))
    cv.drawRect(skia.Rect(d0, 860, d1, FACADE_Y), P(C("3a2a20")))
    cv.drawRect(skia.Rect(d0, 860, d1, FACADE_Y), P(0, shader=lin(d0, 0, d1, 0, [C("5a4535"), C("2a1e16")])))
    cv.drawRect(skia.Rect(x1 - 120, 860, x1 - 30, FACADE_Y - 16), P(0, shader=lin(0, 860, 0, FACADE_Y, [C("a8d8ea"), C("5a8fa6")])))
    cv.drawRect(skia.Rect(x0, FACADE_Y - 14, x1, FACADE_Y), P(C("000000", 0.18)))
    # neighbours + cross street
    storefront(cv, 1100, 1560, 260, "f4b393", "e07a5f", kind="home", seed=7)
    cvp = (1730, 900)
    cv.drawRect(skia.Rect(1560, 300, 1900, FACADE_Y), P(C("cfe9f7")))
    cv.drawPath(poly([(1560, FACADE_Y), (1700, 1000), (1760, 1000), (1900, FACADE_Y)]), P(C("55585e")))
    cv.drawPath(poly([(1560, 330), (1700, 760), (1700, 1000), (1560, FACADE_Y)]), P(C("e8a582")))
    cv.drawPath(poly([(1900, 330), (1760, 760), (1760, 1000), (1900, FACADE_Y)]), P(C("38a39b")))
    storefront(cv, 1900, 2400, 280, "3fb8af", "2a8a83", kind="home", seed=8)
    tree(cv, 1250, 1500)
    # zebra crossing on the road
    for k in range(7):
        xx = 1240 + k * 70
        cv.drawPath(poly([(xx, 1600), (xx + 40, 1600), (xx + 10, 2100), (xx - 30, 2100)]), P(C("f2f2f2", 0.9)))
    for xx in np.arange(0, 1200, 260):
        cv.drawRect(skia.Rect(xx, 1890, xx + 150, 1904), P(C("f2f2f2", 0.85)))
    for xx in np.arange(1750, SHW, 260):
        cv.drawRect(skia.Rect(xx, 1890, xx + 150, 1904), P(C("f2f2f2", 0.85)))
    # brackets
    for bx in (SIGN_C[0] - SIGN_W / 2 + 50, SIGN_C[0] + SIGN_W / 2 - 50):
        cv.drawRect(skia.Rect(bx - 10, 470, bx + 10, 545), P(C("4a4f55")))
        cv.drawRect(skia.Rect(bx - 22, 462, bx + 22, 480), P(C("6a7078")))

def sign(cv, t_state, cx=SIGN_C[0], cy=SIGN_C[1], ang=0.0, drop=0.0, vib=0.0):
    """large dimensional metal sign; ang rotates around left bracket."""
    lx = cx - SIGN_W / 2 + 50
    cv.save()
    cv.translate(lx, cy - SIGN_H / 2 + drop)
    cv.rotate(ang + vib)
    x0, y0 = -50.0, 0.0
    x1, y1 = SIGN_W - 50.0, SIGN_H
    cv.drawRect(skia.Rect(x0 + 10, y0 + 14, x1 + 10, y1 + 18), P(C("000000", 0.25), blur=10))
    cv.drawPath(poly([(x0, y1), (x1, y1), (x1 + 16, y1 - 14), (x0 + 16, y1 - 14)]) if False else poly([(x1, y0), (x1 + 18, y0 - 14), (x1 + 18, y1 - 14), (x1, y1)]), P(C("5a6068")))
    cv.drawPath(poly([(x0, y0), (x1, y0), (x1 + 18, y0 - 14), (x0 + 18, y0 - 14)]), P(C("c8ced6")))
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(0, shader=lin(0, y0, 0, y1, [C("e6ebf0"), C("9aa3ad"), C("c5ccd4")], [0, 0.55, 1])))
    cv.drawRect(skia.Rect(x0 + 14, y0 + 14, x1 - 14, y1 - 14), P(C("2a8a83")))
    f = skia.Font(K_TF, 70)
    w = f.measureText("CORNER SHOP")
    cv.drawString("CORNER SHOP", (x0 + x1) / 2 - w / 2, y1 / 2 + 25, f, P(C("fbe3a0")))
    for bx in (x0 + 24, x1 - 24):
        for by in (y0 + 24, y1 - 24):
            cv.drawCircle(bx, by, 6, P(C("7a828c")))
    cv.restore()

def car(cv, x, base, sc=1.0):
    cv.save(); cv.translate(x, base); cv.scale(sc, sc)
    cv.drawOval(skia.Rect(-230, -14, 230, 18), P(C("000000", 0.35), blur=12))
    body = skia.Path()
    body.moveTo(-220, -40); body.lineTo(-220, -110); body.cubicTo(-200, -130, -150, -135, -120, -140)
    body.cubicTo(-80, -210, 60, -215, 110, -150); body.lineTo(200, -135); body.cubicTo(225, -128, 228, -100, 225, -40); body.close()
    cv.drawPath(body, P(0, shader=lin(0, -215, 0, -40, [C("6aa8e8"), C("2f6fb0"), C("1d4a7a")], [0, 0.5, 1])))
    win = skia.Path(); win.moveTo(-100, -145); win.cubicTo(-70, -195, 40, -198, 85, -150); win.close()
    cv.drawPath(win, P(0, shader=lin(-100, -195, 85, -145, [C("d8eefa"), C("7fa8c2")])))
    cv.drawLine(-10, -195, -10, -145, P(C("1d4a7a"), stroke=8))
    cv.drawLine(-200, -105, 200, -105, P(C("ffffff", 0.35), stroke=5))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-226, -100, -205, -82), 5, 5), P(C("fff4b0")))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(205, -100, 226, -82), 5, 5), P(C("e74c3c")))
    for wx in (-130, 130):
        cv.drawCircle(wx, -38, 40, P(C("1e1e1e"))); cv.drawCircle(wx, -38, 20, P(0, shader=rad(wx - 5, -43, 22, [C("e0e0e0"), C("8a8a8a")])))
    cv.restore()

def ball(cv, x, y, r=22, rot=0.0):
    cv.drawOval(skia.Rect(x - r, y + r - 6, x + r, y + r + 6), P(C("000000", 0.3), blur=4))
    cv.save(); cv.translate(x, y); cv.rotate(rot)
    cv.drawCircle(0, 0, r, P(0, shader=rad(-r * 0.3, -r * 0.4, r * 1.4, [C("ff8a80"), C("e53935")])))
    cv.drawLine(-r, 0, r, 0, P(C("ffffff"), stroke=5))
    cv.restore()

# ================================================================== shadow matrices
M_BED = (1.0, 0.5, 0.05, 0.45)
M_HALL = (1.0, -0.55, 0.02, 0.28)
M_ST = (1.0, -0.62, 0.02, 0.24)
M_ALLEY = (1.0, -0.42, 0.0, 0.45)

def mat_lerp(a, b, k):
    return tuple(lerp(x, y, k) for x, y in zip(a, b))

# ================================================================== CLIPS
LEO_S_ST = 1.0   # Leo scale on street sets

def clip01(cv, t):
    CUR_WORLD[:] = [W, H]
    z, wx, wy = C1.camera(t)
    cv.save(); cam(cv, z, wx, wy)
    bedroom_base(cv, t)
    lp, sp = C1.leo_pose(t), C1.shadow_pose(t)
    for p in (lp, sp):
        p.update(stride=0, phase=0, back=False, jump=0)
    draw_shadow(cv, sp, *C1.FEET, CFG_LEO, K.S_LEO, M_BED, K.FLOOR_POLY)
    contact(cv, *C1.FEET, 1.0)
    K.draw_dust(cv, t)
    draw_person(cv, lp, *C1.FEET, CFG_LEO, K.S_LEO)
    cv.restore()

def leo_end1():
    p = C1.leo_pose(9.999); p.update(stride=0, phase=0, back=False, jump=0); return p

def shadow_end1():
    p = C1.shadow_pose(9.999); p.update(stride=0, phase=0, back=False, jump=0); return p

def clip02(cv, t):
    CUR_WORLD[:] = [W, H]
    feet0 = C1.FEET
    sp = shadow_end1(); lp = leo_end1()
    # 0-3 Leo slowly raises both arms; shadow still
    up = ss(0.3, 2.4, t) * (1 - ss(3.0, 3.4, t))
    lp["handL"] = lerp2(lp["handL"], (-60.0, -125.0), up); lp["handR"] = lerp2(lp["handR"], (60.0, -125.0), up)
    lp["brows"] = (16, -2); lp["eyes"] = "wide"; lp["mouth"] = "o" if t < 3 else "flat"
    # 3-5 two small steps right; shadow anchor stays
    stepk = ss(3.2, 4.8, t)
    fx = lerp(feet0[0], feet0[0] + 120, stepk)
    st, ph = walk(t, 3.2, 4.8, 8.0, 0.45)
    lp["stride"], lp["phase"] = st, ph
    if t >= 3.0:
        lp["look"] = (-0.7, 0.9); lp["eyes"] = "n"
    # 5-7 frown, look from feet to shadow
    if t >= 5.0:
        lp["tilt"] = 10 * ss(5.0, 5.5, t)
        lp["brows"] = (6, 8); lp["mouth"] = "wobble"
        lp["look"] = (-0.3, 1.0) if (t - 5.0) % 1.2 < 0.6 else (-0.9, 0.7)
    # 7-9.5 shadow points at door; Leo turns head toward it
    pk = ss(7.0, 7.6, t)
    tgt = DOOR_PT
    sp_shoulder = (feet0[0] - 0.0, feet0[1])
    dirx, diry = tgt[0] - (feet0[0] - 300), tgt[1] - (feet0[1] - 160)
    sp["handR"] = lerp2(sp["handR"], point_rel(M_BED, dirx, diry), pk)
    sp["handL"] = lerp2(sp["handL"], (-14.0, 150.0), pk)
    if t >= 7.6:
        lp["look"] = (1.0, -0.2); lp["tilt"] = -6; lp["brows"] = (14, -2); lp["eyes"] = "wide"; lp["mouth"] = "o"
    # camera
    if t < 3.0:
        z, wx, wy = 1.42 - 0.04 * ss(0, 3, t), 545 + 20 * ss(0, 3, t), 1240
    elif t < 5.0:
        z, wx, wy = 1.75, 640, 1340
    elif t < 7.0:
        z, wx, wy = 2.3, fx, 1070
    elif t < 9.5:
        z, wx, wy = 1.05, 640, 1150
    else:
        k = ss(9.5, 10, t); z, wx, wy = lerp(1.05, 1.15, k), lerp(640, 680, k), 1150
    cv.save(); cam(cv, z, wx, wy)
    bedroom_base(cv, t)
    draw_shadow(cv, sp, *feet0, CFG_LEO, K.S_LEO, M_BED, K.FLOOR_POLY)
    contact(cv, fx, feet0[1])
    K.draw_dust(cv, t)
    draw_person(cv, lp, fx, feet0[1], CFG_LEO, K.S_LEO)
    if 7.0 <= t:
        g = ss(7.6, 8.2, t)
        cv.drawCircle(DOOR_PT[0], DOOR_PT[1], 70, P(C("fff4d0", 0.25 * g), blur=30))
    cv.restore()

POT_FALL = (7.55, 7.95)

def hall_draw(cv, t, gt, leo, lx, ly, shadow, sx, sy, smat, pot_state):
    img, sf = env_image("hall", W, H, hall_static)
    draw_img(cv, img, sf)
    # pot
    phase, k = pot_state
    if phase == "shelf":
        wob = 3 * math.sin(gt * 30) * k
        pot_shape(cv, HALL_SHELF_POT[0] - 40 * k, HALL_SHELF_POT[1], 0.85, wob)
    elif phase == "fall":
        px = lerp(HALL_SHELF_POT[0] - 40, HALL_POT_LAND[0], k)
        py = lerp(HALL_SHELF_POT[1], HALL_POT_LAND[1] - 20, k * k)
        pot_shape(cv, px, py, 0.85 + 0.25 * k, 40 * k)
    else:
        shards(cv, HALL_POT_LAND[0], HALL_POT_LAND[1], k, sc=0.9)
    sc = hall_scale(ly)
    draw_shadow(cv, shadow, sx, sy, CFG_LEO, hall_scale(sy), smat, HALL_FLOOR)
    contact(cv, lx, ly, sc / 1.25)
    draw_person(cv, leo, lx, ly, CFG_LEO, sc)

def clip03(cv, t):
    CUR_WORLD[:] = [W, H]
    gt = 20 + t
    # 0-3 walk toward shelf (back view)
    k = ss(0.0, 3.0, t)
    lx, ly = lerp(560, 905, k), lerp(1800, 1520, k)
    if t >= 5.4:
        b = ss(5.4, 6.6, t); lx, ly = lerp(905, 760, b), lerp(1520, 1640, b)
    if t >= 7.95:
        r = ss(7.95, 8.4, t); lx, ly = lerp(760, 700, r), lerp(1640, 1680, r)
    lp = pose0()
    st, ph = walk(t, 0.0, 3.0, 7.0, 0.7)
    st2, ph2 = walk(t, 5.4, 6.6, 7.0, 0.5)
    lp["stride"], lp["phase"] = st + st2, ph + ph2
    lp["back"] = t < 3.0
    lp["mouth"] = "flat"
    if 3.0 <= t:
        lp["look"] = (0.6, -1.0); lp["tilt"] = -8; lp["brows"] = (12, -2)
    if 5.0 <= t:
        lp["eyes"] = "wide"; lp["mouth"] = "o"; lp["brows"] = (16, -2)
    if 7.95 <= t < 9.5:
        lp["handL"] = (-70, -60); lp["handR"] = (70, -60); lp["lean"] = -8 * ss(7.95, 8.2, t); lp["look"] = (0.5, 0.8); lp["bounce"] = 6 * math.sin(min(1, (t - 7.95) / 0.4) * math.pi)
    if t >= 9.5:
        lp["look"] = (-0.4, 1.0) if t < 9.75 else (0.6, 0.7); lp["handL"] = (-40, 60); lp["handR"] = (40, 60)
    # shadow: stretches ahead, points up at shelf from ~2s, toward debris at end
    sp = pose0(); sp.update(stride=lp["stride"], phase=lp["phase"])
    ang = ss(1.6, 2.4, t) * (1 - ss(7.9, 8.3, t))
    sp["handR"] = lerp2(sp["handR"], point_rel(M_HALL, 0.25, -1.0), ang)
    stretch = 1.0 + 0.35 * ss(0.5, 2.0, t) * (1 - ss(8.0, 8.5, t))
    if t >= 9.0:
        sp["handR"] = lerp2(sp["handR"], point_rel(M_HALL, 0.6, -0.4), ss(9.0, 9.4, t))
    if t < 3.5:
        pot = ("shelf", 0.0)
    elif t < 7.55:
        pot = ("shelf", ss(5.0, 7.5, t))
    elif t < 7.95:
        pot = ("fall", ss(7.55, 7.95, t))
    else:
        pot = ("broken", ss(7.95, 8.25, t))
    if t < 3.0:
        z, wx, wy = lerp(1.25, 1.12, ss(0, 3, t)), lerp(600, 760, ss(0, 3, t)), 1320
    elif t < 5.0:
        z, wx, wy = 1.6, 870, 1040
    elif t < 7.5:
        z, wx, wy = 2.2, 960, 760 + 120 * ss(5.0, 7.4, t)
    elif t < 9.5:
        z, wx, wy = 1.2, 820, 1280
    else:
        z, wx, wy = 1.7, 760, 1300
    cv.save(); cam(cv, z, wx, wy)
    hall_draw(cv, t, gt, lp, lx, ly, sp, lx, ly, M_HALL if stretch == 1 else (M_HALL[0], M_HALL[1] * stretch, M_HALL[2], M_HALL[3] * stretch), pot)
    if pot[0] == "broken" and pot[1] < 1:
        for i in range(10):
            a = i * 0.63
            q = pot[1]
            cv.drawCircle(HALL_POT_LAND[0] + math.cos(a) * 140 * q, HALL_POT_LAND[1] - 30 - math.sin(a) * 60 * q, 10 * (1 - q), P(C("d8c6a2", 0.8 * (1 - q))))
    cv.restore()

def clip04(cv, t):
    gt = 30 + t
    if t < 7.5:
        CUR_WORLD[:] = [W, H]
        lx, ly = 700.0, 1680.0
        lp = pose0(); lp["look"] = (0.4, 0.7); lp["mouth"] = "flat"; lp["brows"] = (8, 4)
        sp = pose0()
        g = ss(0.4, 0.8, t) * (1 - ss(2.6, 3.0, t))
        gest = 0.5 + 0.5 * math.sin((t - 0.8) * 9) if 0.8 < t < 2.6 else 0.5
        door_dir = (540 - lx, 1100 - ly)
        sp["handR"] = lerp2((14.0, 150.0), point_rel(M_HALL, *door_dir, reach=110 + 36 * gest), g)
        if t >= 3.0:
            lp["look"] = (-0.5, -0.6); lp["brows"] = (4, 2)
        if t >= 4.0:
            lp["bounce"] = 6 * abs(math.sin((t - 4.0) * 9)) * (1 - ss(4.4, 4.7, t)); lp["mouth"] = "smile"; lp["brows"] = (2, -4)
        if t >= 5.0:
            k = ss(5.0, 7.5, t)
            lx, ly = lerp(700, 545, k), lerp(1680, 1215, k)
            st, ph = walk(t, 5.0, 7.5, 7.0, 0.6)
            lp.update(stride=st, phase=ph, back=True)
        if t < 3.0:
            z, wx, wy = 1.5, 760, 1350
        elif t < 5.0:
            z, wx, wy = 2.1, 700, 1140
        else:
            k = ss(5.0, 7.5, t); z, wx, wy = lerp(1.25, 2.4, k), lerp(640, 540, k), lerp(1360, 960, k)
        cv.save(); cam(cv, z, wx, wy)
        hall_draw(cv, t, gt, lp, lx, ly, sp, lx, ly, M_HALL, ("broken", 1.0))
        cv.restore()
        return
    CUR_WORLD[:] = [SW, SH_]
    k = ss(7.5, 9.0, t)
    lx, ly = lerp(390, 420, k), lerp(1200, 1400, k)
    if t >= 9.5:
        lx = lerp(420, 470, ss(9.5, 10, t))
    lp = pose0(); st, ph = walk(t, 7.5, 9.0, 7.0, 0.6); st2, ph2 = walk(t, 9.5, 10.2, 6, 0.4)
    lp.update(stride=st + st2, phase=ph + ph2)
    lp["look"] = (0.6, 0.9) if t > 8.6 else (0.2, 0.2); lp["brows"] = (8, 0); lp["mouth"] = "flat"
    sp = pose0(); sp.update(stride=lp["stride"], phase=lp["phase"])
    pk = ss(8.6, 9.2, t)
    sp["handR"] = lerp2(sp["handR"], point_rel(M_ST, 1.0, 0.0), pk)
    stretch = 1 + 0.35 * pk
    z, wx, wy = 1.0, 520 + 30 * ss(9.5, 10, t), 1150
    cv.save(); cam(cv, z, wx, wy)
    img, sf = env_image("street", SW, SH_, street_static, 1.4)
    draw_img(cv, img, sf)
    draw_shadow(cv, sp, lx, ly, CFG_LEO, LEO_S_ST, M_ST, STREET_FLOOR, stretch=stretch)
    contact(cv, lx, ly, 0.8)
    draw_person(cv, lp, lx, ly, CFG_LEO, LEO_S_ST)
    cv.restore()

def street_draw(cv, z, wx, wy, actors):
    CUR_WORLD[:] = [SW, SH_]
    cv.save(); cam(cv, z, wx, wy)
    img, sf = env_image("street", SW, SH_, street_static, 1.4)
    draw_img(cv, img, sf)
    for a in actors:
        a(cv)
    cv.restore()

def cyclist_draw(cv, x, y, t, wob=0.0, scale=1.0, flip=True):
    cv.save()
    if flip:
        cv.translate(x, 0); cv.scale(-1, 1); cv.translate(-x, 0)
    bicycle(cv, x, y, frame="d64541", sc=scale, wob=wob)
    p = pose0(sit=0.7, hip_y=-165, handL=(100, 95), handR=(116, 95), lean=10, mouth="smile", look=(-1.0, 0.0))
    if abs(wob) > 1:
        p.update(eyes="wide", mouth="o", brows=(14, -2))
    cv.translate(x, y); cv.rotate(wob); cv.translate(-x, -y)
    draw_person(cv, p, x - 30 * scale, y - 6 * scale, CFG_CYCL, 0.75 * scale)
    cv.restore()

def clip05(cv, t):
    # Leo walks right; cyclist from the right hits pothole, swerves, Leo jumps back
    if t < 3.2:
        lx = lerp(470, 1650, ss(0, 3.2, t))
    else:
        lx = 1650.0
    if t >= 7.6:
        lx = lerp(1650, 1480, ss(7.6, 8.0, t))
    ly = 1400.0
    lp = pose0(); st, ph = walk(t, 0, 3.2, 8, 0.7); lp.update(stride=st, phase=ph)
    lp["look"] = (0.5, 0.8) if (t % 1.6) < 0.5 and t < 3.0 else (0.3, 0.0)
    lp["mouth"] = "flat"
    if t >= 3.4:
        lp["look"] = (0.7, 0.4); lp["brows"] = (10, 0)
    jump = 0.0
    if 7.6 <= t < 8.0:
        jump = 70 * math.sin(math.pi * ss(7.6, 8.0, t)); lp.update(eyes="wide", mouth="o", brows=(16, -2), handL=(-80, -60), handR=(80, -60))
    if t >= 8.0:
        lp.update(eyes="wide", mouth="o", brows=(16, -2))
        lp["look"] = (-0.9, 0.0) if t < 9.5 else (0.4, 0.9)
    lp["jump"] = jump
    sp = pose0(); sp.update(stride=lp["stride"], phase=lp["phase"])
    pk = ss(3.0, 3.4, t)
    sp["handR"] = lerp2(sp["handR"], point_rel(M_ST, 0.25, 1.0), pk * (1 - ss(8.6, 9.0, t)))
    # cyclist path
    if t < 6.2:
        cx, cy, wob = lerp(2650, POTHOLE[0] + 20, ss(4.4, 6.2, t)) if t >= 4.4 else 2900, 1720, 0.0
    elif t < 7.0:
        cx, cy = lerp(POTHOLE[0] + 20, 1760, ss(6.2, 7.0, t)), 1720
        wob = 9 * math.sin((t - 6.2) * 28)
    elif t < 8.2:
        k = ss(7.0, 8.2, t)
        cx, cy = lerp(1760, 1420, k), lerp(1720, 1530, math.sin(math.pi * k * 0.9))
        wob = -12 * math.sin(math.pi * k)
    else:
        k = ss(8.2, 10, t)
        cx, cy = lerp(1420, 1150, k), lerp(1560, 1700, k); wob = 4 * math.sin((t - 8.2) * 10) * (1 - k)
    pk2 = ss(9.5, 9.8, t)
    if t >= 9.5:
        sp["handR"] = lerp2(sp["handR"], point_rel(M_ST, cx - lx, cy - ly), pk2)
    if t < 3.0:
        z, wx, wy = 1.0, lx + 80, 1150
    elif t < 5.0:
        z, wx, wy = 1.25, 1760, 1330
    elif t < 7.0:
        z, wx, wy = 1.7, lerp(2000, 1850, ss(5.0, 7.0, t)), 1580
    elif t < 9.5:
        z, wx, wy = 1.0, 1600, 1250
    else:
        z, wx, wy = 1.0, 1560, 1250
    def actors(cv):
        draw_shadow(cv, sp, lx, ly, CFG_LEO, LEO_S_ST, M_ST, STREET_FLOOR, stretch=1 + 0.3 * pk)
        contact(cv, lx, ly, 0.8)
        draw_person(cv, lp, lx, ly, CFG_LEO, LEO_S_ST)
        cv.drawOval(skia.Rect(cx - 90, cy - 10, cx + 90, cy + 14), P(C("000000", 0.3), blur=8))
        cyclist_draw(cv, cx, cy, t, wob)
    street_draw(cv, z, wx, wy, [actors])

def clip06(cv, t):
    lx, ly = 1480.0, 1400.0
    lp = pose0(); lp.update(eyes="wide", mouth="o", brows=(16, -2), look=(0.4, 0.9))
    if t >= 1.0:
        lp["look"] = (-0.9, 0.0) if t < 2.0 else (0.5, 0.9)
        lp.update(eyes="n", mouth="flat", brows=(4, 6))
    cxp = lerp(1150, 700, ss(0, 10, t))
    sp = pose0()
    sp["handR"] = point_rel(M_ST, cxp - lx, 1700 - ly)
    mat = M_ST
    stretch = 1.0
    a0, a1 = ALLEY
    if t >= 3.0:
        k = ss(3.0, 3.8, t)
        sp["handR"] = lerp2(sp["handR"], point_rel(M_ST, (a0 + a1) / 2 - lx, 1150 - ly), k)
        lp["look"] = (0.9, -0.1)
    if t >= 5.0:
        k = ss(5.0, 7.5, t)
        lx = lerp(1480, 2370, k); ly = 1400.0
        st, ph = walk(t, 5.0, 7.5, 7.5, 0.65); lp.update(stride=st, phase=ph, sp=0)
        sp.update(stride=st, phase=ph)
        lp["look"] = (0.6, 0.3)
    if t >= 7.5:
        k = ss(7.5, 8.2, t)
        mat = mat_lerp(M_ST, M_ALLEY, k)
        stretch = 1 + 0.45 * k
        sp["handR"] = lerp2(sp["handR"], point_rel(M_ALLEY, 2500 - lx, 1010 - ly), k)
        sp["handL"] = (-14.0, 150.0)
        lp.update(look=(0.0, 1.0), tilt=-8, brows=(12, -4), mouth="wobble")
    if t < 3.0:
        z, wx, wy = 1.5, 1480, 1080
    elif t < 5.0:
        z, wx, wy = 1.05, 1900, 1200
    elif t < 7.5:
        z, wx, wy = 1.0, lx + 60, 1150
    elif t < 9.5:
        z, wx, wy = 1.2, 2470, 1130
    else:
        k = ss(9.5, 10, t); z, wx, wy = lerp(1.2, 1.32, k), 2450, lerp(1130, 1100, k)
    def actors(cv):
        draw_shadow(cv, sp, lx, ly, CFG_LEO, LEO_S_ST, mat, STREET_FLOOR_A, stretch=stretch)
        contact(cv, lx, ly, 0.8)
        draw_person(cv, lp, lx, ly, CFG_LEO, LEO_S_ST)
        if cxp < 1600:
            cv.drawOval(skia.Rect(cxp - 90, 1690, cxp + 90, 1714), P(C("000000", 0.3), blur=8))
            cyclist_draw(cv, cxp, 1700, t)
    street_draw(cv, z, wx, wy, [actors])

# --- shop / intersection actors
def shop_draw(cv, z, wx, wy, actors, t_glob, sign_state=None):
    CUR_WORLD[:] = [SHW, SHH]
    cv.save(); cam(cv, z, wx, wy)
    img, sf = env_image("shop", SHW, SHH, shop_static, 1.4)
    draw_img(cv, img, sf)
    if sign_state is None:
        sign_state = dict()
    if not sign_state.get("fallen"):
        sign(cv, None, **{k: v for k, v in sign_state.items() if k in ("ang", "drop", "vib")})
    for a in actors:
        a(cv)
    cv.restore()

GIRL_S = 0.72

def clip07(cv, t):
    if t < 5.0:
        # inside the alley on the street set: Leo walks into it (back view), girl tiny at the far end
        a0, a1 = ALLEY
        vpx = (a0 + a1) / 2
        k = ss(0, 3.0, t)
        ly = lerp(1400, 1110, k); lx = lerp(2370, vpx, k) + 6 * math.sin(t * 2)
        sc = lerp(1.0, 0.55, k)
        lp = pose0(); st, ph = walk(t, 0, 3.0, 6.5, 0.6); lp.update(stride=st, phase=ph, back=True)
        sp = pose0(); sp.update(stride=st, phase=ph)
        mat = mat_lerp(M_ALLEY, (1.0, 0.0, 0.0, 0.42), k)
        sp["handR"] = point_rel(mat, vpx - lx, 1010 - ly)
        if t >= 3.0:
            lp = pose0(eyes="wide", mouth="o", brows=(16, -2), look=(0.0, -0.6), handL=(-60, 40), handR=(60, 40))
            sp["handR"] = point_rel(mat, 0.3, -1.0)
        def actors(cv):
            cv.save(); cv.clipPath(STREET_FLOOR_A, skia.ClipOp.kIntersect, True)
            draw_shadow(cv, sp, lx, ly, CFG_LEO, sc, mat, None, stretch=1.45)
            cv.restore()
            gx = vpx + 10 + 6 * math.sin(t * 3)
            draw_person(cv, pose0(stride=0.4, phase=t * 6), gx, 1008, CFG_GIRL, 0.12)
            contact(cv, lx, ly, sc * 0.8)
            draw_person(cv, lp, lx, ly, CFG_LEO, sc)
        if t < 3.0:
            z, wx, wy = lerp(1.15, 1.6, k), vpx, lerp(1000, 940, k)
        else:
            z, wx, wy = 1.6, vpx, 950
        street_draw(cv, z, wx, wy, [actors])
        return
    # intersection set
    gx, gy = 1180.0, 1500.0
    bx = lerp(1210, 1330, ss(5.0, 6.0, t)); by = lerp(1520, 1700, ss(5.0, 6.0, t))
    gp = pose0(stride=0.4 if t < 6.4 else 0, phase=t * 6, look=(0.8, 0.6), mouth="smile", handR=(60, 60))
    if t >= 6.0:
        gx = lerp(1180, 1240, ss(6.0, 6.8, t))
    lx, ly = 450.0, 1480.0
    lp = pose0(eyes="wide", mouth="o", brows=(16, -2), look=(1.0, 0.2))
    st, ph = 0.0, 0.0
    if t >= 7.6:
        lp["look"] = (1.0, -0.1); lp["lean"] = 10 * ss(7.6, 8.4, t)
    if t >= 8.6:
        st, ph = walk(t, 8.6, 10.5, 10, 1.2); lp.update(stride=st, phase=ph, handL=(-60, 40), handR=(80, -40))
        lx = lerp(450, 510, ss(8.6, 10, t))
    carx = lerp(2400, 1700, ss(7.0, 10, t))
    sp = pose0(); sp.update(stride=st, phase=ph)
    sp["handR"] = point_rel(M_ST, gx - lx, gy - ly)
    stretch = 1.0 + 0.6 * ss(9.5, 9.9, t)
    if t < 7.0:
        z, wx, wy = 1.6, 1250, 1360
    else:
        z, wx, wy = 0.85, 1000, 1300
    def actors(cv):
        draw_shadow(cv, sp, lx, ly, CFG_LEO, LEO_S_ST, M_ST, SHOP_FLOOR, stretch=stretch)
        ball(cv, bx, by, rot=t * 300)
        contact(cv, gx, gy, 0.6)
        draw_person(cv, gp, gx, gy, CFG_GIRL, GIRL_S)
        car(cv, carx, 1830, 1.0)
        contact(cv, lx, ly, 0.8)
        draw_person(cv, lp, lx, ly, CFG_LEO, LEO_S_ST)
    shop_draw(cv, z, wx, wy, [actors], 60 + t)

def clip08(cv, t):
    gx, gy = 1240.0, 1500.0
    lx = lerp(510, 1150, ss(0, 3.2, t)); ly = 1480.0
    lp = pose0(eyes="wide", mouth="o", brows=(16, -2), look=(1.0, 0.0))
    st, ph = walk(t, 0, 3.2, 10, 1.2); lp.update(stride=st, phase=ph, lean=10 * st, handL=(-60, 40), handR=(80, -40))
    gp = pose0(look=(0.8, 0.6), mouth="smile")
    if 3.2 <= t:
        k = ss(3.3, 5.3, t)
        lx = lerp(1150, 1000, k); gx = lerp(1240, 1090, k); gy = lerp(1500, 1380, k); ly = lerp(1480, 1380, k)
        st2, ph2 = walk(t, 3.3, 5.3, 6, 0.4)
        lp.update(stride=st2, phase=ph2, lean=0, handR=(60, 70), mouth="flat", look=(0.6, 0.4))
        gp.update(stride=st2, phase=ph2, handL=(-60, -20), look=(-0.8, -0.4), eyes="wide", mouth="o")
    if t >= 7.5:
        gp.update(look=(-0.6, -0.8), eyes="wide", mouth="smile", brows=(10, -2), stride=0)
        lp.update(mouth="smile", look=(-0.6, 0.0), brows=(4, 0), stride=0)
    if t >= 8.6:
        lp.update(look=(0.4, 0.9))
    carx = lerp(1700, 1580, ss(0, 5.5, t)) if t < 5.5 else lerp(1580, -600, ss(5.5, 7.6, t))
    sp = pose0(); sp.update(stride=lp["stride"], phase=lp["phase"])
    sp["handR"] = point_rel(M_ST, gx - lx, gy - ly)
    if t >= 9.5:
        sp["handR"] = lerp2(sp["handR"], point_rel(M_ST, 0.0, -1.0, reach=120), ss(9.5, 9.8, t))
    if t < 3.0:
        z, wx, wy = lerp(0.85, 1.0, ss(0, 3, t)), lerp(1000, lx + 250, ss(0, 1, t)), 1300
    elif t < 5.5:
        z, wx, wy = 1.35, 1150, 1300
    elif t < 7.5:
        z, wx, wy = 1.6, 1300, 1620
    else:
        z, wx, wy = 1.5, 1060, 1180
    def actors(cv):
        draw_shadow(cv, sp, lx, ly, CFG_LEO, LEO_S_ST, M_ST, SHOP_FLOOR)
        ball(cv, 1330, 1700)
        contact(cv, gx, gy, 0.6)
        draw_person(cv, gp, gx, gy, CFG_GIRL, GIRL_S)
        contact(cv, lx, ly, 0.8)
        draw_person(cv, lp, lx, ly, CFG_LEO, LEO_S_ST)
        if -500 < carx < 2700:
            car(cv, carx, 1830, 1.0)
            if 5.5 < t < 7.6:
                for k in range(4):
                    cv.drawLine(carx + 240 + k * 30, 1700 + k * 25, carx + 380 + k * 30, 1700 + k * 25, P(C("ffffff", 0.5), stroke=4))
    shop_draw(cv, z, wx, wy, [actors], 70 + t)

def clip09(cv, t):
    lx, ly = 1000.0, 1380.0
    gx, gy = 1090.0, 1380.0
    lp = pose0(mouth="smile", look=(0.4, 0.9), brows=(4, 0))
    gp = pose0(look=(-0.6, -0.8), mouth="smile")
    has_ball = False
    if t < 1.6:
        k = ss(0.1, 0.8, t) * (1 - ss(0.9, 1.5, t))
        lx = lerp(1000, 1200, k); ly = lerp(1380, 1520, k)
        lp.update(stride=0.4 * (k > 0.05 and k < 0.95), phase=t * 7, look=(0.8, 0.9))
        has_ball = t > 0.8
    else:
        has_ball = True
    bpos = (1330, 1700) if not has_ball else None
    if t >= 1.6:
        k = ss(1.6, 3.0, t)
        gp.update(waveR=(t - 1.6) * 12 if t < 2.3 else 0, handR=(70, -120) if t < 2.3 else (40, -20), eyes="happy" if t < 2.3 else "n")
        gx = lerp(1090, 1700, ss(2.3, 3.6, t)); gp.update(stride=0.5 if 2.3 < t < 3.6 else 0, phase=t * 7)
        lp.update(look=(0.8, -0.2), handL=(-60, -100) if t < 2.3 else (-14, 150), waveR=0)
    if t >= 3.0:
        k = ss(3.0, 4.8, t)
        lx = lerp(1000, 600, k); ly = lerp(1380, 1330, k)
        st, ph = walk(t, 3.0, 4.8, 7, 0.6); lp.update(stride=st, phase=ph, look=(-0.6, 0.0), mouth="smile")
    sp = pose0(); sp.update(stride=lp["stride"], phase=lp["phase"])
    if t >= 4.0:
        sp["handR"] = lerp2(sp["handR"], point_rel(M_ST, 0.0, -1.0), ss(4.0, 4.5, t))
        sp.update(stride=0)
    if t >= 5.0:
        lp.update(mouth="flat", look=(0.2, -1.0), brows=(10, 0), tilt=-6)
    if t >= 6.0:
        lp.update(eyes="wide", mouth="o", brows=(16, -2))
    vib = 0.6 * math.sin((60 + 20 + t) * 40) * ss(6.5, 7.0, t)
    ang = 2.5 * ss(8.2, 9.3, t)
    if t < 3.0:
        z, wx, wy = 1.3, 1150, 1180
    elif t < 5.0:
        z, wx, wy = 1.05, 800, 1150
    elif t < 7.0:
        z, wx, wy = 2.3, lx, 1000
    elif t < 9.5:
        z, wx, wy = 1.8, 760, 620
    else:
        z, wx, wy = 1.0, 620, 1100
    def actors(cv):
        draw_shadow(cv, sp, lx, ly, CFG_LEO, LEO_S_ST, M_ST, SHOP_FLOOR, stretch=1 + 0.35 * ss(4.0, 4.5, t))
        if bpos:
            ball(cv, *bpos)
        if gx < 1900:
            contact(cv, gx, gy, 0.6)
            draw_person(cv, gp, gx, gy, CFG_GIRL, GIRL_S)
            if has_ball:
                ball(cv, gx + 6, gy - 150, 20)
        contact(cv, lx, ly, 0.8)
        draw_person(cv, lp, lx, ly, CFG_LEO, LEO_S_ST)
        if 7.0 <= t < 9.5:
            bx = SIGN_C[0] + SIGN_W / 2 - 50
            sy = 520 + 40 * ss(7.3, 9.3, t)
            cv.drawRect(skia.Rect(bx - 5, sy, bx + 5, sy + 26), P(C("9aa3ad")))
            cv.drawCircle(bx, sy, 8, P(C("6a7078")))
    shop_draw(cv, z, wx, wy, [actors], 80 + t, dict(ang=ang, vib=vib))

def clip10(cv, t):
    lx, ly = 600.0, 1330.0
    if t < 3.0:
        k = ss(0.2, 2.6, t); ly = lerp(1330, 1270, k); lx = lerp(600, 640, k)
    else:
        lx, ly = 640.0, 1270.0
    lp = pose0(eyes="wide", mouth="o", brows=(16, -2), look=(0.2, -1.0), tilt=-6)
    if t < 3.0:
        st, ph = walk(t, 0.2, 2.6, 5, 0.35); lp.update(stride=st, phase=ph, look=(0.4 * math.sin(t * 2), -1.0))
    sp = pose0(); sp["handR"] = point_rel(M_ST, 0.0, -1.0)
    stretch = 1.35
    shopx, shopy = (SHOP_DOOR[0] + SHOP_DOOR[1]) / 2, 1190.0
    shop_vis = ss(5.0, 5.6, t)
    kp = pose0(look=(-0.6, -0.8), mouth="o", eyes="wide", brows=(16, -2))
    if t >= 5.6:
        kp.update(handL=(-70, -130), handR=(70, -130))
    if t >= 7.0:
        k = ss(7.0, 7.6, t)
        sweep = math.sin(min(1, (t - 7.6) / 1.4) * math.pi * 2) if t > 7.6 else 0
        sp["handR"] = lerp2(sp["handR"], point_rel(M_ST, -1.0, 0.25 + 0.3 * sweep), k)
        stretch = 1.35 + 0.4 * k
        if t >= 8.6:
            lp.update(look=(-0.8, 0.6), tilt=0, lean=-6 * ss(8.6, 9.4, t))
    ang = 2.5 + 3.5 * ss(3.0, 5.0, t) + 6 * ss(9.5, 10.0, t)
    drop = 30 * ss(9.5, 10.0, t)
    vib = 0.8 * math.sin((90 + t) * 45)
    if t < 3.0:
        z, wx, wy = lerp(1.2, 1.4, ss(0, 3, t)), 640, lerp(1150, 900, ss(0, 3, t))
    elif t < 5.0:
        z, wx, wy = 2.4, SIGN_C[0] + SIGN_W / 2 - 60, 560
    elif t < 7.0:
        z, wx, wy = 1.5, 760, 1000
    elif t < 9.5:
        z, wx, wy = 1.1, 620, 1150
    else:
        z, wx, wy = 1.25, 620, 1000
    def actors(cv):
        if shop_vis > 0:
            cv.save(); cv.saveLayerAlpha(None, int(255 * shop_vis))
            draw_person(cv, kp, shopx, shopy, CFG_SHOP, 0.95)
            cv.restore(); cv.restore()
        draw_shadow(cv, sp, lx, ly, CFG_LEO, LEO_S_ST, M_ST, SHOP_FLOOR, stretch=stretch)
        contact(cv, lx, ly, 0.8)
        draw_person(cv, lp, lx, ly, CFG_LEO, LEO_S_ST)
        if 3.0 <= t < 5.0:
            bx = SIGN_C[0] + SIGN_W / 2 - 50
            sy = 560 + 30 * ss(3.2, 4.8, t)
            cv.drawRect(skia.Rect(bx - 5, sy, bx + 5, sy + 26), P(C("9aa3ad")))
    shop_draw(cv, z, wx, wy, [actors], 90 + t, dict(ang=ang, drop=drop, vib=vib))

def clip11(cv, t):
    lx, ly = 640.0, 1270.0
    shopx, shopy = (SHOP_DOOR[0] + SHOP_DOOR[1]) / 2, 1190.0
    lp = pose0(eyes="wide", mouth="o", brows=(18, -2), look=(0.0, -1.0))
    sp = pose0(); sp["handR"] = point_rel(M_ST, -1.0, 0.25)
    stretch = 1.75
    jump = 0.0
    # 2-4.5 shadow yanks left, Leo jumps
    if t >= 2.0:
        k = ss(2.0, 2.6, t)
        stretch = 1.75 + 0.9 * k
        sp["handR"] = point_rel(M_ST, -1.0, 0.1)
        sp["handL"] = point_rel(M_ST, -1.0, 0.0)
    if t >= 2.6:
        k = ss(2.6, 4.2, t)
        lx = lerp(640, 300, k); ly = lerp(1270, 1350, k)
        jump = 160 * math.sin(math.pi * k)
        lp.update(handL=(-120, -60), handR=(120, -90), lean=-14 * math.sin(math.pi * k), eyes="closed" if k < 0.6 else "wide", mouth="o")
        stretch = lerp(2.65, 1.2, ss(3.2, 4.4, t))
    if t >= 4.2:
        lp.update(handL=(-50, 60), handR=(50, 60), lean=0)
    # sign
    if t < 2.0:
        ang = 12 + 20 * ss(0.0, 2.0, t); drop = 30 + 60 * ss(0.5, 2.0, t)
    else:
        ang = 32 + 40 * ss(2.0, 4.8, t); drop = 90 + 600 * ss(3.0, 4.9, t) ** 1.6
    fallen = t >= 4.9
    if t >= 6.5:
        lp.update(look=(1.0, 0.1) if t < 7.3 else (0.5, 0.9), brows=(16, -2), mouth="o" if t < 7.3 else "wobble",
                  bounce=4 * abs(math.sin(t * 7)))
    kp = pose0(look=(-0.6, -0.8), mouth="o", eyes="wide", brows=(16, -2), handL=(-70, -130), handR=(70, -130))
    kx, ky = shopx, shopy
    if t >= 6.5:
        k = ss(6.5, 8.0, t); kx = lerp(shopx, 500, k); ky = lerp(shopy, 1300, k)
        st, ph = walk(t, 6.5, 8.0, 8, 0.6); kp.update(stride=st, phase=ph, handL=(-80, -40), handR=(80, -40), mouth="smile" if t > 7.6 else "o")
    if t >= 8.5:
        lp.update(look=(0.4, 0.9), mouth="smile", eyes="wide", brows=(12, -4), bounce=0)
        stretch = lerp(1.2, 1.0, ss(8.5, 9.6, t))
        sp["handR"] = lerp2(sp["handR"], (14.0, 150.0), ss(8.5, 9.6, t))
        sp["handL"] = lerp2(sp["handL"], (-14.0, 150.0), ss(8.5, 9.6, t))
        stretch = lerp(stretch, 1.25, 0)
    lp["jump"] = jump
    if t < 2.0:
        z, wx, wy = lerp(1.6, 1.15, ss(0, 2, t)), 640, lerp(800, 1000, ss(0, 2, t))
    elif t < 4.5:
        z, wx, wy = 1.0, 560, 1150
    elif t < 6.5:
        z, wx, wy = 1.4, 560, 1200
    elif t < 8.5:
        z, wx, wy = 1.15, 520, 1150
    else:
        z, wx, wy = 1.25, 480, 1150
    def actors(cv):
        if not (6.5 <= t):
            draw_person(cv, kp, kx, ky, CFG_SHOP, 0.95)
        draw_shadow(cv, sp, lx, ly, CFG_LEO, LEO_S_ST, M_ST, SHOP_FLOOR, stretch=stretch)
        if 2.0 <= t < 3.2:
            q = ss(2.0, 3.2, t)
            for k in range(5):
                yy = ly - 60 + k * 20
                cv.drawLine(lx - 80 - 300 * q, yy, lx - 80 - 300 * q + 160, yy, P(C("26252a", 0.6 * (1 - q)), stroke=6))
        if fallen:
            fallen_sign(cv, t - 4.9)
        if 6.5 <= t:
            contact(cv, kx, ky, 0.8)
            draw_person(cv, kp, kx, ky, CFG_SHOP, 0.95)
        contact(cv, lx, ly, 0.8 * (1 - 0.5 * min(1, jump / 160)))
        draw_person(cv, lp, lx, ly, CFG_LEO, LEO_S_ST)
        if fallen and t - 4.9 < 2.0:
            q = (t - 4.9) / 2.0
            for i in range(26):
                a = i * 0.9
                cv.drawCircle(640 + math.cos(a) * 260 * q, 1250 - abs(math.sin(a)) * 160 * q, 30 * (1 - q) + 8, P(C("d8c6a2", 0.6 * (1 - q)), blur=6))
    shop_draw(cv, z, wx, wy, [actors], 100 + t, dict(ang=ang, drop=drop, fallen=fallen))

def fallen_sign(cv, dt):
    bounce = 18 * math.exp(-dt * 6) * abs(math.sin(dt * 18))
    cv.save(); cv.translate(640, 1290 - bounce); cv.rotate(-6)
    x0, x1, y0, y1 = -270, 250, -40, 40
    cv.drawOval(skia.Rect(x0 - 20, y1 - 10, x1 + 30, y1 + 30), P(C("000000", 0.35), blur=12))
    cv.drawPath(poly([(x0, y0), (x1, y0), (x1 + 20, y0 - 50), (x0 + 20, y0 - 50)]), P(0, shader=lin(0, y0 - 50, 0, y0, [C("2a8a83"), C("1f6b65")])))
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(0, shader=lin(0, y0, 0, y1, [C("c5ccd4"), C("7a828c")])))
    cv.drawLine(x0 + 60, y0 - 10, x0 + 140, y0 - 40, P(C("1a1a1a", 0.6), stroke=4))
    cv.drawLine(x1 - 40, y0 - 20, x1 - 120, y0 - 35, P(C("1a1a1a", 0.6), stroke=3))
    cv.restore()
    for (dx, dy, r) in ((-330, 1300, 10), (-290, 1320, 7), (300, 1310, 9), (340, 1290, 6), (260, 1330, 8)):
        cv.drawCircle(640 + dx * 0.9 + 0 * dt, dy, r, P(C("8a8f96")))

def clip12(cv, t):
    lx, ly = 300.0, 1350.0
    lp = pose0(look=(0.4, 0.9), mouth="smile", eyes="wide" if t < 2.0 else "n", brows=(12, -4) if t < 2.0 else (6, 0))
    sp = pose0()
    stretch = lerp(1.0, 1.0, 0)
    # 0-3: shadow already settled (end of clip 11) – Leo watches it, softening
    if t >= 3.0:
        r = ss(3.0, 3.6, t) * (1 - ss(4.6, 5.0, t))
        lp["handR"] = lerp2((14.0, 150.0), (70.0, -110.0), r); sp["handR"] = lp["handR"]
    kp = pose0(look=(-0.8, 0.0), mouth="smile")
    kx, ky = 500.0, 1300.0
    if t >= 5.0:
        kp.update(handL=(-60, -110), handR=(60, -110), waveR=(t - 5.0) * 8 if t < 6.5 else 0, eyes="happy")
        lp.update(look=(0.9, 0.0), bounce=4 * abs(math.sin((t - 5.6) * 6)) if 5.6 < t < 6.2 else 0)
    if t >= 6.5:
        k = ss(6.5, 8.0, t); kx, ky = lerp(500, 860, k), lerp(1300, 1190, k)
        kp.update(stride=0.5 if t < 8.0 else 0, phase=t * 7, handL=(-14, 150), handR=(14, 150), waveR=0)
    # Leo walks right along the front of the pavement, in front of the fallen sign
    def pos(tt):
        if tt < 6.6:
            return 300.0, 1350.0
        d = min(tt, 8.5) - 6.6 + max(0.0, tt - 9.1)
        return 300 + 150 * d, min(1460.0, 1350 + 110 * min(1, (tt - 6.6) / 1.2))
    lx, ly = pos(t)
    walking = t >= 6.6 and not (8.5 <= t < 9.1)
    if walking:
        lp.update(stride=0.7, phase=(t - 6.6) * 7, look=(0.8, 0.0), mouth="smile")
        sp.update(stride=0.7, phase=(t - 6.6) * 7)
    sx, sy = lx, ly
    # shadow lingers, then the secret wave (7.0-8.4)
    if 7.0 <= t < 8.5:
        if t < 8.35:
            sx, sy = pos(7.0)
            sp.update(stride=0)
        if 7.35 <= t < 8.3:
            sp.update(handR=point_rel(M_ST, 0.2, -1.0, reach=120), waveR=(t - 7.35) * 14)
    if 8.5 <= t < 9.1:
        lp.update(look=(-1.0, 0.0), tilt=-8, stride=0)
        sp.update(stride=0, handR=(14.0, 150.0), waveR=0)
    if t >= 9.1:
        lp.update(look=(0.8, 0.0), tilt=0, mouth="smile")
    if t < 3.0:
        z, wx, wy = 1.25, 480, 1150
    elif t < 5.0:
        z, wx, wy = 1.6, 360, 1100
    elif t < 7.0:
        z, wx, wy = 1.15, 480, 1150
    elif t < 8.5:
        z, wx, wy = 1.7, 620, 1360
    else:
        k = ss(8.5, 10, t); z, wx, wy = lerp(1.15, 0.95, k), lerp(700, 860, k), 1180
    def actors(cv):
        fallen_sign(cv, 5.0)
        contact(cv, kx, ky, 0.8)
        draw_person(cv, kp, kx, ky, CFG_SHOP, 0.95)
        draw_shadow(cv, sp, sx, sy, CFG_LEO, LEO_S_ST, M_ST, SHOP_FLOOR)
        contact(cv, lx, ly, 0.8)
        draw_person(cv, lp, lx, ly, CFG_LEO, LEO_S_ST)
    shop_draw(cv, z, wx, wy, [actors], 110 + t, dict(fallen=True))

CLIPS = [clip01, clip02, clip03, clip04, clip05, clip06, clip07, clip08, clip09, clip10, clip11, clip12]

def frame(cv, t):
    i = min(11, int(t // 10))
    cv.save()
    CLIPS[i](cv, t - i * 10)
    cv.restore()

def worker(args):
    k, f0, f1, out = args
    K.room_image()
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    for fi in range(f0, f1):
        cv = surf.getCanvas(); cv.clear(C("000000"))
        frame(cv, fi / FPS)
        ff.stdin.write(surf.makeImageSnapshot().toarray().tobytes())
    ff.stdin.close(); ff.wait()
    return out

if __name__ == "__main__":
    if sys.argv[1] == "still":
        K.room_image()
        surf = skia.Surface(W, H)
        for ts in sys.argv[2:]:
            cv = surf.getCanvas(); cv.clear(C("000000")); frame(cv, float(ts))
            surf.makeImageSnapshot().save(f"{HERE}/st_{ts}.png", skia.kPNG)
    else:
        from multiprocessing import Pool
        N = 120 * FPS; nw = 4; step = N // nw
        jobs = [(k, k * step, (k + 1) * step, f"{HERE}/story_part{k}.mp4") for k in range(nw)]
        with Pool(nw) as p:
            outs = p.map(worker, jobs)
        with open(f"{HERE}/story_parts.txt", "w") as f:
            for o in outs:
                f.write(f"file '{o}'\n")
        print("done", N)
