import json, math, os, subprocess, sys
import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from render import C, lerpc, clamp, ss, ease_out_back, P, lin, rad, poly, text, chip, pop, TF_BLACK, TF_XB, TF_B

W, H, FPS = 1080, 1920, 30
LEAD, TAIL = 0.5, 3.4
SEGS = json.load(open(os.path.join(HERE, "vo.json")))
for s in SEGS:
    s["s"] = s["start"] + LEAD
    s["e"] = s["end"] + LEAD
TOTAL = SEGS[-1]["e"] + TAIL
TAIL_T = SEGS[-1]["e"] + 0.25

INK = C("15110f")
SKIN = {"A": "8a5534", "T": "5e3822"}

def lerp(a, b, t):
    return a + (b - a) * t

def lerp2(p, q, t):
    return (lerp(p[0], q[0], t), lerp(p[1], q[1], t))

# ------------------------------------------------------------------ scene states
# pose, expression, look, shot
STATES = [
    dict(A=("phone", "sus", "T"), T=("rest", "smile", "A"), shot="A"),
    dict(A=("rest", "smirk", "T"), T=("hands_up", "grin", "A"), shot="two"),
    dict(A=("fold", "smirk", "T"), T=("rest", "smile", "A"), shot="two"),
    dict(A=("fold", "brow", "T"), T=("temple", "confident", "A"), shot="T"),
    dict(A=("chest", "wide", "T"), T=("rest", "smile", "A"), shot="A"),
    dict(A=("chest", "wide", "T"), T=("explain", "confident", "A"), shot="two"),
    dict(A=("braid", "shy", "down"), T=("rest", "smile", "A"), shot="A"),
    dict(A=("braid", "shy", "T"), T=("explain", "smile", "A"), shot="T"),
    dict(A=("wipe", "nervous", "T"), T=("rest", "smile", "A"), shot="two"),
    dict(A=("wipe", "nervous", "T"), T=("explain", "confident", "A"), shot="T"),
    dict(A=("rest", "sus", "T"), T=("rest", "grin", "A"), shot="two"),
    dict(A=("rest", "sus", "T"), T=("lean_in", "serious", "A"), shot="T"),
    dict(A=("shrug", "flat", "T"), T=("rest", "smile", "A"), shot="two"),
    dict(A=("rest", "flat", "T"), T=("finger", "brow", "A"), shot="two"),
    dict(A=("shock", "shock", "T"), T=("rest", "smile", "A"), shot="A"),
    dict(A=("rest", "soft", "T"), T=("arm_around", "smile", "A"), shot="two"),
    dict(A=("head_on", "tease", "T"), T=("arm_around", "smile", "A"), shot="two"),
    dict(A=("head_on", "soft", "T"), T=("arm_around", "smirk", "cam"), shot="punch"),
]
TAIL_STATE = dict(A=("slap", "laugh", "T"), T=("arm_around", "grin", "A"), shot="two")

CUTS = []  # (start, end, kind)
for li, kind, frac in [(3, "dopamine", 0.42), (7, "serotonin", 0.38), (9, "heart", 0.3), (11, "blind", 0.4)]:
    s = SEGS[li]
    CUTS.append((s["s"] + (s["e"] - s["s"]) * frac, SEGS[li + 1]["s"] - 0.05, kind))

CARDS = [  # (start, end, label, bg, fg)
    (SEGS[3]["s"] + 2.6, SEGS[4]["s"], "DOPAMINE", "ffc93c", "3a2400"),
    (SEGS[7]["s"] + 1.0, SEGS[8]["s"], "SEROTONIN ↓", "5ab8ff", "05223a"),
    (SEGS[9]["s"] + 0.2, SEGS[10]["s"], "NOREPINEPHRINE", "ff5a3c", "ffffff"),
    (SEGS[11]["s"] + 2.4, SEGS[12]["s"], "LOVE IS BLIND", "ff6fae", "ffffff"),
    (SEGS[13]["s"] + 2.8, SEGS[14]["e"] + 0.2, "2 YEARS?", "ffffff", "2a0f2e"),
    (SEGS[15]["s"] + 0.4, SEGS[16]["s"], "OXYTOCIN", "ff4f7b", "ffffff"),
]

def line_at(t):
    li = 0
    for i, s in enumerate(SEGS):
        if s["s"] <= t:
            li = i
    return li

def state_at(t):
    if t >= TAIL_T:
        return TAIL_STATE, STATES[-1], ss(TAIL_T, TAIL_T + 0.3, t)
    li = line_at(t)
    prev = STATES[li - 1] if li > 0 else STATES[0]
    return STATES[li], prev, ss(SEGS[li]["s"] - 0.12, SEGS[li]["s"] + 0.22, t)

def amp_for(who, t):
    for s in SEGS:
        if s["who"] == who and s["s"] <= t < s["e"]:
            i = int((t - s["s"]) * FPS)
            env = s["env"]
            if 0 <= i < len(env):
                return env[i]
    return 0.0

# ------------------------------------------------------------------ character rig
HEAD_R = 80
SH_Y = -232
SH_X = 50
L1, L2 = 108, 102

def pose_targets(name, side, t, amp):
    """side=+1 if partner is to the right. returns dict with hands (outer, inner) rel to hip, lean deg, flags."""
    s = side
    d = dict(o=(-s * 34, -30), i=(s * 34, -30), lean=0.0, sh=0.0, flags=set())
    wob = math.sin(t * 7)
    if name == "phone":
        d["i"] = (s * 30, -205); d["flags"].add("phone")
    elif name == "hands_up":
        d["o"] = (-s * 125, -330); d["i"] = (s * 125, -330); d["flags"].add("palms")
    elif name == "fold":
        d["o"] = (s * 52, -150); d["i"] = (-s * 52, -142); d["flags"].add("fold")
    elif name == "temple":
        tap = 6 * math.sin(t * 9)
        d["o"] = (-s * 92, -350 + tap)
        d["flags"].add("finger_o")
    elif name == "chest":
        d["o"] = (-s * 24, -185); d["i"] = (s * 24, -175)
    elif name == "explain":
        d["i"] = (s * (105 + 18 * math.sin(t * 3.1)), -175 - 25 * amp - 10 * math.sin(t * 2.3))
        d["flags"].add("palms")
    elif name == "braid":
        d["o"] = (-s * (88 + 6 * wob), -300 + 8 * math.cos(t * 7)); d["lean"] = 3 * s
    elif name == "wipe":
        d["o"] = (-s * (40 + 22 * math.sin(t * 6)), -25); d["i"] = (s * (40 + 22 * math.sin(t * 6 + 1)), -25)
    elif name == "lean_in":
        d["lean"] = 10 * s
        d["i"] = (s * 100, -190 - 15 * amp); d["flags"].add("palms")
    elif name == "shrug":
        d["o"] = (-s * 130, -140); d["i"] = (s * 130, -140); d["sh"] = 18; d["flags"].add("palms")
    elif name == "finger":
        d["i"] = (s * 95, -330); d["flags"].add("finger_i")
    elif name == "shock":
        d["o"] = (-s * 22, -190); d["i"] = (s * 22, -182); d["sh"] = 10; d["lean"] = -4 * s
    elif name == "arm_around":
        d["flags"].add("around")
        d["i"] = (s * 230, -240)
    elif name == "head_on":
        d["lean"] = 24 * s
        d["i"] = (s * 40, -40)
    elif name == "slap":
        hit = abs(math.sin(t * 7))
        d["lean"] = 10 * s * (0.5 + 0.5 * math.sin(t * 9))
        d["i"] = (s * (110 + 110 * hit), -170 - 20 * hit)
        d["o"] = (-s * 30, -160)
    return d

def blend_pose(a, b, k):
    return dict(o=lerp2(a["o"], b["o"], k), i=lerp2(a["i"], b["i"], k), lean=lerp(a["lean"], b["lean"], k),
                sh=lerp(a["sh"], b["sh"], k), flags=b["flags"] if k > 0.5 else a["flags"])

def ik(sx, sy, tx, ty, outward_x):
    dx, dy = tx - sx, ty - sy
    d = math.hypot(dx, dy)
    d = clamp(d, 20, L1 + L2 - 2)
    a = math.atan2(dy, dx)
    al = math.acos(clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1))
    c1 = (sx + L1 * math.cos(a + al), sy + L1 * math.sin(a + al))
    c2 = (sx + L1 * math.cos(a - al), sy + L1 * math.sin(a - al))
    hx, hy = sx + d * math.cos(a), sy + d * math.sin(a)
    e = c1 if (c1[0] - sx) * outward_x + (c1[1] - sy) * 0.6 > (c2[0] - sx) * outward_x + (c2[1] - sy) * 0.6 else c2
    return e, (hx, hy)

EXPR = {
    # brows: (inner_dy, outer_dy) per brow ; eyes: scale ; mouth
    "smile": dict(brow=(0, 0), eye="n", mouth="smile"),
    "grin": dict(brow=(-6, 0), eye="n", mouth="grin"),
    "smirk": dict(brow=(4, -8), eye="half", mouth="smirk"),
    "sus": dict(brow=(8, -2), eye="half", mouth="smirk"),
    "brow": dict(brow=(0, -14), eye="n", mouth="neutral", one_brow=True),
    "confident": dict(brow=(-4, -8), eye="n", mouth="smirk"),
    "wide": dict(brow=(-16, -16), eye="wide", mouth="o"),
    "shy": dict(brow=(-6, 2), eye="n", mouth="smile"),
    "nervous": dict(brow=(-12, 4), eye="n", mouth="wobble"),
    "serious": dict(brow=(6, 0), eye="n", mouth="neutral"),
    "flat": dict(brow=(4, 4), eye="half", mouth="flat"),
    "shock": dict(brow=(-22, -22), eye="wide", mouth="shock"),
    "soft": dict(brow=(-3, 0), eye="n", mouth="smile"),
    "tease": dict(brow=(4, -10), eye="half", mouth="smirk"),
    "laugh": dict(brow=(-8, -2), eye="happy", mouth="laugh"),
}

def blink_amt(t, seed):
    p = (t + seed * 1.37) % 3.7
    return 1.0 if p < 0.12 else 0.0

def draw_head(cv, who, hx, hy, tilt, expr, look, amp, t, side):
    e = EXPR[expr]
    skin = C(SKIN[who])
    cv.save(); cv.translate(hx, hy); cv.rotate(tilt)
    R = HEAD_R
    if who == "A":
        # braids behind head
        for k in range(16):
            u = k / 15
            ang = math.radians(150 + u * 240) if False else None
            sx = -R * 0.98 + u * R * 1.96
            top_y = -math.sqrt(max(0, R * R - sx * sx)) * 0.4
            sway = 5 * math.sin(t * 2 + k)
            end_x = sx * 1.25 + sway
            if abs(sx) < R * 0.55:
                continue
            p = skia.Path(); p.moveTo(sx, top_y); p.quadTo(sx * 1.2, R * 0.6, end_x, R * 1.45)
            cv.drawPath(p, P(C("1c120d"), stroke=17))
            for j in range(6):
                q = 0.2 + j * 0.14
                bx = lerp(sx, end_x, q) + (sx * 0.2) * math.sin(q * math.pi)
                by = lerp(top_y, R * 1.45, q)
                cv.drawLine(bx - 7, by - 3, bx + 7, by + 3, P(C("4a3226"), stroke=3))
    head = skia.Rect(-R, -R, R, R)
    cv.drawOval(head, P(skin))
    # face shading
    cv.drawOval(head, P(0, shader=rad(-R * 0.35, -R * 0.4, R * 1.6, [C("ffffff", 0.18), C("000000", 0.0), C("000000", 0.18)], [0, 0.6, 1])))
    if who == "T":
        # low cut hair
        cv.save(); cp = skia.Path(); cp.addRect(skia.Rect(-R - 5, -R - 5, R + 5, -R * 0.42)); cv.clipPath(cp, skia.ClipOp.kIntersect, True)
        cv.drawOval(skia.Rect(-R - 3, -R - 4, R + 3, R + 2), P(C("17100b")))
        cv.restore()
        # beard band along jaw + moustache
        cv.save(); oc = skia.Path(); oc.addOval(head); cv.clipPath(oc, skia.ClipOp.kIntersect, True)
        bp = skia.Path(); bp.addOval(skia.Rect(-R * 1.05, -R * 0.15, R * 1.05, R * 1.35))
        inner = skia.Path(); inner.addOval(skia.Rect(-R * 0.62, -R * 0.05, R * 0.62, R * 0.62))
        beard = skia.Op(bp, inner, skia.PathOp.kDifference_PathOp)
        cv.drawPath(beard, P(C("17100b")))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-R * 0.36, R * 0.26, R * 0.36, R * 0.38), 8, 8), P(C("17100b")))
        cv.drawRect(skia.Rect(-R, -R * 0.1, -R * 0.82, R * 0.4), P(C("17100b")))
        cv.drawRect(skia.Rect(R * 0.82, -R * 0.1, R, R * 0.4), P(C("17100b")))
        cv.restore()
    else:
        cv.save(); cp = skia.Path(); cp.addRect(skia.Rect(-R - 8, -R - 8, R + 8, -R * 0.38)); cv.clipPath(cp, skia.ClipOp.kIntersect, True)
        cv.drawOval(skia.Rect(-R - 5, -R - 6, R + 5, R + 4), P(C("1c120d")))
        cv.restore()
        for k in range(7):
            x = -R * 0.6 + k * R * 0.2
            cv.drawLine(x, -R * 0.95 + abs(x) * 0.25, x * 1.05, -R * 0.45, P(C("3a271c"), stroke=3))
    cv.drawOval(head, P(INK, stroke=6))
    if who == "A":
        for sx_ in (-1, 1):
            cv.drawCircle(sx_ * R * 0.98, R * 0.35, 13, P(C("f2c14e"), stroke=5))
    # eyes
    lx, ly = {"T": (side, 0), "A": (side, 0), "cam": (0, 0), "down": (0.3 * side, 0.8)}.get(look, (0, 0))
    bl = blink_amt(t, 0 if who == "A" else 1.9)
    for ex in (-1, 1):
        cx, cy = ex * 33, -14
        rx, ry = 29, 36
        if e["eye"] == "wide":
            rx, ry = 33, 42
        eye = skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry)
        if e["eye"] == "happy" or bl > 0.5:
            pth = skia.Path(); pth.moveTo(cx - 20, cy + 4); pth.quadTo(cx, cy - 18 if e["eye"] == "happy" else cy + 10, cx + 20, cy + 4)
            cv.drawPath(pth, P(INK, stroke=6))
            continue
        cv.drawOval(eye, P(C("ffffff")))
        pr = 11 if e["eye"] != "wide" else 9
        cv.drawCircle(cx + lx * 11, cy + 4 + ly * 12, pr, P(INK))
        cv.drawCircle(cx + lx * 11 - 3, cy + ly * 12, 3, P(C("ffffff")))
        if e["eye"] == "half":
            lid = skia.Path(); lid.addRect(skia.Rect(cx - rx - 2, cy - ry - 2, cx + rx + 2, cy - ry * 0.05))
            cv.save(); ec = skia.Path(); ec.addOval(eye); cv.clipPath(ec, skia.ClipOp.kIntersect, True)
            cv.drawPath(lid, P(skin)); cv.restore()
            cv.drawLine(cx - rx, cy - ry * 0.05, cx + rx, cy - ry * 0.05, P(INK, stroke=5))
        cv.drawOval(eye, P(INK, stroke=5))
    # brows
    bi, bo = e["brow"]
    for ex in (-1, 1):
        ib, ob = bi, bo
        if e.get("one_brow") and ex == -side:
            ib, ob = 0, 0
        x_in, x_out = ex * 12, ex * 52
        cv.drawLine(x_in, -62 + ib, x_out, -60 + ob, P(INK, stroke=7))
    # mouth
    my = R * 0.42
    mc = INK if who == "A" else C("c99073")
    if amp > 0.07 or e["mouth"] in ("laugh", "shock", "o"):
        op = max(amp, {"laugh": 0.75 + 0.25 * math.sin(t * 20), "shock": 0.8, "o": 0.45}.get(e["mouth"], 0))
        if e["mouth"] == "laugh" and amp < 0.07:
            op = 0.6 + 0.3 * abs(math.sin(t * 14))
        w = 18 + 8 * op if e["mouth"] in ("o", "shock") else 24 + 6 * op
        hgt = 5 + 26 * op
        r = skia.Rect(-w, my - hgt * 0.5, w, my + hgt * 0.7)
        cv.drawOval(r, P(C("3a0c10")))
        cv.save(); oc = skia.Path(); oc.addOval(r); cv.clipPath(oc, skia.ClipOp.kIntersect, True)
        cv.drawOval(skia.Rect(-w * 0.6, my + hgt * 0.2, w * 0.6, my + hgt), P(C("d9536a")))
        cv.drawRect(skia.Rect(-w, my - hgt * 0.5 - 2, w, my - hgt * 0.5 + 6), P(C("ffffff")))
        cv.restore()
        cv.drawOval(r, P(mc, stroke=4))
    else:
        m = e["mouth"]
        p = skia.Path()
        if m in ("smile", "grin"):
            p.moveTo(-24, my - 4); p.quadTo(0, my + (16 if m == "smile" else 22), 24, my - 4)
        elif m == "smirk":
            p.moveTo(-18 * side, my + 4); p.quadTo(4 * side, my + 10, 24 * side, my - 8)
        elif m == "wobble":
            p.moveTo(-20, my + 4)
            for k in range(1, 6):
                p.lineTo(-20 + k * 8, my + (4 if k % 2 == 0 else -2))
        elif m == "flat":
            p.moveTo(-18, my + 2); p.lineTo(18, my + 2)
        else:
            p.moveTo(-14, my + 2); p.quadTo(0, my + 6, 14, my + 2)
        cv.drawPath(p, P(mc, stroke=5))
    cv.restore()

def draw_char(cv, who, x, y, pose, expr, look, amp, t, side, arm_layer="all"):
    """x,y = hip center. side = +1 if partner to the right."""
    lean = math.radians(pose["lean"])
    bob = -5 * amp * math.sin(t * 18) - 2 * math.sin(t * 1.6 + (0 if who == "A" else 1))
    def rot(px, py):
        return (x + px * math.cos(lean) - py * math.sin(lean), y + px * math.sin(lean) + py * math.cos(lean))
    sh_y = SH_Y - pose["sh"] + bob
    sho = rot(-side * SH_X, sh_y)   # outer shoulder
    shi = rot(side * SH_X, sh_y)    # inner shoulder
    neck = rot(0, sh_y - 10)
    head = rot(0, sh_y - 30 - HEAD_R)
    if arm_layer in ("all", "body"):
        # legs
        for k in (-1, 1):
            hip = (x + k * 26, y)
            knee = (x + k * 44, y + 46)
            foot = (x + k * 52, y + 285)
            if who == "T":
                pth = skia.Path(); pth.moveTo(*hip); pth.lineTo(*knee); pth.lineTo(*foot)
                cv.drawPath(pth, P(C("23263a"), stroke=26))
                cv.drawOval(skia.Rect(foot[0] - 30 + k * 8, foot[1] - 6, foot[0] + 30 + k * 8, foot[1] + 18), P(C("f2f2f2")))
                cv.drawOval(skia.Rect(foot[0] - 30 + k * 8, foot[1] - 6, foot[0] + 30 + k * 8, foot[1] + 18), P(INK, stroke=4))
            else:
                pth = skia.Path(); pth.moveTo(*knee); pth.lineTo(*foot)
                cv.drawPath(pth, P(INK, stroke=9))
                cv.drawOval(skia.Rect(foot[0] - 24 + k * 8, foot[1] - 4, foot[0] + 24 + k * 8, foot[1] + 12), P(C("c8792a")))
        # torso
        if who == "A":
            body = poly([rot(-46, sh_y + 4), rot(46, sh_y + 4), rot(78, 30), rot(92, 78), rot(-92, 78), rot(-78, 30)])
            cv.drawPath(body, P(0, shader=lin(x, y + sh_y, x, y + 80, [C("f2b43a"), C("d8941c")])))
            cv.drawPath(body, P(INK, stroke=5))
            cv.drawPath(poly([rot(-40, sh_y + 4), rot(0, sh_y + 46), rot(40, sh_y + 4)], close=False), P(C(SKIN["A"]), stroke=0.1))
            v = poly([rot(-26, sh_y + 4), rot(0, sh_y + 40), rot(26, sh_y + 4)])
            cv.drawPath(v, P(C(SKIN["A"])))
            cv.drawPath(poly([rot(-26, sh_y + 4), rot(0, sh_y + 40), rot(26, sh_y + 4)], close=False), P(INK, stroke=4))
        else:
            body = poly([rot(-58, sh_y + 2), rot(58, sh_y + 2), rot(52, 6), rot(-52, 6)])
            cv.drawPath(body, P(0, shader=lin(x, y + sh_y, x, y, [C("f4ead2"), C("ddd0b2")])))
            for k in range(6):
                yy = sh_y + 40 + k * 32
                cv.drawPath(poly([rot(-50, yy), rot(50, yy)], close=False), P(C("c9b994", 0.6), stroke=3))
            cv.drawPath(body, P(INK, stroke=5))
            cv.drawPath(poly([rot(-20, sh_y + 2), rot(0, sh_y + 26), rot(20, sh_y + 2)], close=False), P(INK, stroke=4))
        cv.drawLine(neck[0], neck[1], head[0], head[1] + HEAD_R - 4, P(INK, stroke=9))
    # arms
    def arm(sh, target, outward, is_inner):
        tx, ty = rot(*target) if not (is_inner and "around" in pose["flags"]) else (x + target[0], y + target[1])
        el, hd = ik(sh[0], sh[1], tx, ty, outward)
        if who == "T":
            # short sleeve
            sx = sh[0] + (el[0] - sh[0]) * 0.42; sy = sh[1] + (el[1] - sh[1]) * 0.42
            cv.drawLine(sh[0], sh[1], sx, sy, P(C("e9dcbd"), stroke=34, cap=skia.Paint.kButt_Cap))
        pth = skia.Path(); pth.moveTo(*sh); pth.lineTo(*el); pth.lineTo(*hd)
        cv.drawPath(pth, P(INK, stroke=9))
        if who == "T":
            sx = sh[0] + (el[0] - sh[0]) * 0.42; sy = sh[1] + (el[1] - sh[1]) * 0.42
            cv.drawLine(sh[0], sh[1], sx, sy, P(C("e9dcbd"), stroke=30, cap=skia.Paint.kButt_Cap))
        cv.drawCircle(hd[0], hd[1], 15, P(C(SKIN[who])))
        cv.drawCircle(hd[0], hd[1], 15, P(INK, stroke=4))
        if ("finger_o" in pose["flags"] and not is_inner) or ("finger_i" in pose["flags"] and is_inner):
            cv.drawLine(hd[0], hd[1] - 10, hd[0], hd[1] - 36, P(INK, stroke=7))
        if "phone" in pose["flags"] and is_inner:
            r = skia.RRect.MakeRectXY(skia.Rect(hd[0] - 26, hd[1] - 66, hd[0] + 22, hd[1] + 14), 8, 8)
            cv.drawRRect(r, P(C("2b2b35")))
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(hd[0] - 21, hd[1] - 60, hd[0] + 17, hd[1] + 8), 5, 5), P(C("8fd3ff")))
            cv.drawCircle(hd[0] - 2, hd[1] - 30, 9, P(C("ff4f7b")))
            cv.drawCircle(hd[0], hd[1], 15, P(C(SKIN[who])))
            cv.drawCircle(hd[0], hd[1], 15, P(INK, stroke=4))
    if arm_layer in ("all", "body"):
        arm(sho, pose["o"], -side, False)
        if not ("around" in pose["flags"] and arm_layer == "body"):
            arm(shi, pose["i"], side, True)
        draw_head(cv, who, head[0], head[1], math.degrees(lean) * 0.6 + 3 * amp * math.sin(t * 9), expr, look, amp, t, side)
        if "fold" in pose["flags"]:
            # redraw outer forearm on top for crossed look
            tx, ty = rot(*pose["o"])
            el, hd = ik(sho[0], sho[1], tx, ty, -side)
            cv.drawLine(el[0], el[1], hd[0], hd[1], P(INK, stroke=9))
            cv.drawCircle(hd[0], hd[1], 15, P(C(SKIN[who]))); cv.drawCircle(hd[0], hd[1], 15, P(INK, stroke=4))
    if arm_layer == "inner_arm":
        arm(shi, pose["i"], side, True)

# ------------------------------------------------------------------ background
RNG = np.random.default_rng(21)
BUILD = []
x = -40
while x < W + 40:
    w = RNG.uniform(70, 160); h = RNG.uniform(120, 420)
    BUILD.append((x, w, h, RNG.integers(0, 10 ** 6)))
    x += w + RNG.uniform(-10, 20)
BOKEH = [(RNG.uniform(0, W), RNG.uniform(700, 1000), RNG.uniform(6, 22), RNG.choice(["ffd68a", "ff9a6b", "9fd0ff", "ffffff"]), RNG.uniform(0, 6)) for _ in range(40)]

def draw_bg(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=lin(0, 0, 0, 1000, [C("0b0d2b"), C("251542"), C("5a2a52")], [0, 0.6, 1])))
    for i in range(60):
        sx = (i * 173) % W; sy = (i * 97) % 650
        cv.drawCircle(sx, sy, 1.6 + (i % 3) * 0.6, P(C("ffffff", 0.35 + 0.3 * math.sin(t * 2 + i))))
    cv.drawCircle(870, 330, 46, P(C("fff4d6"), blur=1))
    cv.drawCircle(870, 330, 120, P(C("fff4d6", 0.18), blur=40))
    # skyline (blurred)
    base = 1000
    for (bx, bw, bh, seed) in BUILD:
        r = skia.Rect(bx, base - bh, bx + bw, base + 10)
        cv.drawRect(r, P(C("1a1233"), blur=3))
        rr = np.random.default_rng(seed)
        for wy in np.arange(base - bh + 16, base - 10, 26):
            for wx in np.arange(bx + 10, bx + bw - 10, 22):
                if rr.random() < 0.35:
                    cv.drawRect(skia.Rect(wx, wy, wx + 10, wy + 12), P(C(rr.choice(["ffd68a", "ffe9b0", "9fd0ff"]), 0.75), blur=2.5))
    for (bx, by, r, col, ph) in BOKEH:
        cv.drawCircle(bx, by, r, P(C(col, 0.28 + 0.1 * math.sin(t + ph)), blur=r * 0.4))
    # parapet
    cv.drawRect(skia.Rect(0, 980, W, 1110), P(0, shader=lin(0, 980, 0, 1110, [C("6a4a48"), C("3e2a2c")])))
    cv.drawRect(skia.Rect(0, 972, W, 990), P(C("8a6460")))
    # deck floor
    cv.drawRect(skia.Rect(0, 1110, W, H), P(0, shader=lin(0, 1110, 0, H, [C("4a3028"), C("2a1a17")])))
    for k in range(-8, 12):
        cv.drawLine(540 + k * 40, 1110, 540 + k * 170, H, P(C("1e1210", 0.6), stroke=4))
    # warm floor glow
    cv.drawOval(skia.Rect(80, 1300, 1000, 1800), P(C("ffb36b", 0.10), blur=80))
    # plants
    for px, flip in ((70, 1), (1010, -1)):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(px - 60, 1420, px + 60, 1600), 14, 14), P(C("b5643c")))
        for k in range(9):
            a = math.radians(-150 + k * 15 + 4 * math.sin(t * 0.8 + k))
            L = 300 + (k % 3) * 60
            ex, ey = px + math.cos(a) * L * 0.8, 1420 + math.sin(a) * L
            pth = skia.Path(); pth.moveTo(px, 1420); pth.quadTo(px + (ex - px) * 0.4, 1420 + (ey - 1420) * 0.8, ex, ey)
            cv.drawPath(pth, P(C("2f6b3c" if k % 2 else "3f8a4c"), stroke=22))
    # string lights
    for (y0, sag, n, ph) in ((470, 140, 11, 0), (560, 170, 13, 1.3)):
        pts = [(x_, y0 + sag * (1 - ((x_ - 540) / 600) ** 2)) for x_ in np.linspace(-60, W + 60, 40)]
        cv.drawPath(poly(pts, close=False), P(C("1a1414"), stroke=3))
        for k in range(n):
            x_ = -20 + k * (W + 40) / (n - 1)
            y_ = y0 + sag * (1 - ((x_ - 540) / 600) ** 2) + 14
            fl = 0.8 + 0.2 * math.sin(t * 3 + k * 1.7 + ph)
            cv.drawCircle(x_, y_, 34, P(C("ffcf7a", 0.35 * fl), blur=16))
            cv.drawCircle(x_, y_, 10, P(C("fff1c4", fl)))

def draw_couch(cv):
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(110, 1000, 970, 1290), 50, 50), P(C("000000", 0.35), blur=20))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(120, 1010, 960, 1290), 46, 46), P(0, shader=lin(0, 1010, 0, 1290, [C("2f7a78"), C("1f5554")])))
    cv.drawLine(540, 1040, 540, 1260, P(C("17403f"), stroke=5))
    for px, col, ang in ((205, "f2b43a", -8), (875, "c8553d", 8)):
        cv.save(); cv.translate(px, 1170); cv.rotate(ang)
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-70, -70, 70, 70), 30, 30), P(C(col)))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-70, -70, 70, 70), 30, 30), P(C("000000", 0.25), stroke=4))
        cv.restore()
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(100, 1250, 980, 1340), 30, 30), P(0, shader=lin(0, 1250, 0, 1340, [C("3a908c"), C("246462")])))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(90, 1320, 990, 1420), 26, 26), P(C("1b4c4b")))
    for ax in (70, 1010):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(ax - 50, 1110, ax + 50, 1420), 40, 40), P(0, shader=lin(ax - 50, 0, ax + 50, 0, [C("2f7a78"), C("1f5554")])))
    for fx in (140, 940):
        cv.drawRect(skia.Rect(fx - 12, 1420, fx + 12, 1470), P(C("1a120f")))

HEARTS = [(RNG.uniform(250, 830), RNG.uniform(0, 1), RNG.uniform(0, 6.28), RNG.uniform(16, 34)) for _ in range(14)]

def heart_path(x, y, s):
    p = skia.Path()
    p.moveTo(x, y + s * 0.9)
    p.cubicTo(x - s * 1.6, y - s * 0.1, x - s * 0.8, y - s * 1.2, x, y - s * 0.4)
    p.cubicTo(x + s * 0.8, y - s * 1.2, x + s * 1.6, y - s * 0.1, x, y + s * 0.9)
    return p

def draw_world(cv, t):
    draw_bg(cv, t)
    draw_couch(cv)
    cur, prev, k = state_at(t)
    close = ss(SEGS[15]["s"] - 0.2, SEGS[15]["s"] + 0.5, t)
    ax = lerp(370, 395, close); tx = lerp(710, 705, close)
    hip_y = 1285
    pa = blend_pose(pose_targets(prev["A"][0], 1, t, 0), pose_targets(cur["A"][0], 1, t, amp_for("A", t)), k)
    pt = blend_pose(pose_targets(prev["T"][0], -1, t, 0), pose_targets(cur["T"][0], -1, t, amp_for("T", t)), k)
    if "around" in pt["flags"]:
        # aim inner hand at Amaka's near shoulder (absolute, relative to Tayo hip)
        pt["i"] = lerp2(pt["i"], (ax - tx + 40, SH_Y + 6), 1.0)
    if cur["A"][0] == "slap":
        hit = abs(math.sin(t * 7))
        pa["i"] = (tx - ax - 30 - 60 * (1 - hit), -175 - 15 * hit)
    ea = cur["A"][1] if k > 0.5 else prev["A"][1]
    et = cur["T"][1] if k > 0.5 else prev["T"][1]
    la = cur["A"][2] if k > 0.5 else prev["A"][2]
    lt = cur["T"][2] if k > 0.5 else prev["T"][2]
    draw_char(cv, "T", tx, hip_y, pt, et, lt, amp_for("T", t), t, -1, arm_layer="body")
    draw_char(cv, "A", ax, hip_y, pa, ea, la, amp_for("A", t), t, 1)
    if "around" in pt["flags"]:
        draw_char(cv, "T", tx, hip_y, pt, et, lt, amp_for("T", t), t, -1, arm_layer="inner_arm")
    # oxytocin / ending hearts
    ha = ss(SEGS[15]["s"], SEGS[15]["s"] + 1.0, t) * (1 - ss(SEGS[16]["e"], SEGS[16]["e"] + 0.4, t)) + ss(TAIL_T, TAIL_T + 0.5, t)
    if ha > 0:
        for (hx, ph0, ph, s) in HEARTS:
            q = (t * 0.25 + ph0) % 1
            y = 1150 - q * 650
            cv.drawPath(heart_path(hx + 30 * math.sin(t + ph), y, s), P(C("ff4f7b", ha * math.sin(q * math.pi) * 0.9)))
    return ax, tx

SHOT = {"two": (1.0, 540, 1150, 540, 1150), "A": (1.75, None, 960, 540, 930), "T": (1.75, None, 960, 540, 930), "punch": (2.7, None, 935, 540, 900)}

def camera(t):
    cur, prev, k = state_at(t)
    shot = cur["shot"]
    if t >= SEGS[16]["e"] + 0.15 and t < TAIL_T:
        shot = "punch"
    close = ss(SEGS[15]["s"] - 0.2, SEGS[15]["s"] + 0.5, t)
    ax = lerp(370, 395, close); tx = lerp(710, 705, close)
    z, wx, wy, sx, sy = SHOT[shot]
    if shot == "A":
        wx = ax
    elif shot in ("T", "punch"):
        wx = tx
    # gentle drift
    li = line_at(t)
    st = SEGS[li]["s"]
    z *= 1 + 0.03 * ss(st, st + 6, t)
    if shot == "punch":
        z *= 1 + 0.08 * ss(SEGS[16]["e"] + 0.15, SEGS[17]["s"] + 0.3, t)
    return z, wx, wy, sx, sy

# ------------------------------------------------------------------ brain cutaways
def closed_cr(pts, n=14):
    p = list(pts); ext = [p[-1]] + p + [p[0], p[1]]; out = []
    for i in range(1, len(p) + 1):
        p0, p1, p2, p3 = map(np.array, (ext[i - 1], ext[i], ext[i + 1], ext[i + 2]))
        for tt in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * tt + (2 * p0 - 5 * p1 + 4 * p2 - p3) * tt * tt + (-p0 + 3 * p1 - 3 * p2 + p3) * tt ** 3))
    return np.array(out)

BRAIN_U = closed_cr([(-1.2, 0.0), (-1.15, -0.45), (-0.8, -0.85), (-0.2, -1.0), (0.45, -0.9), (0.95, -0.55), (1.2, -0.05), (1.1, 0.35),
                     (0.8, 0.5), (0.35, 0.45), (0.1, 0.58), (-0.35, 0.6), (-0.75, 0.48), (-1.05, 0.3)])
GYRI = []
for i in range(26):
    cx, cy = RNG.uniform(-1.0, 1.0), RNG.uniform(-0.85, 0.4)
    pts = [(cx, cy)]
    a = RNG.uniform(0, 6.28)
    for j in range(5):
        a += RNG.uniform(-1.6, 1.6)
        pts.append((pts[-1][0] + 0.12 * math.cos(a), pts[-1][1] + 0.12 * math.sin(a)))
    GYRI.append(pts)
BX, BY, BS = 540, 1000, 340

def bp(u, v):
    return (BX + u * BS, BY + v * BS)

def brain_bg(cv, t, col="2a0a3a"):
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 1000, 1200, [C(col), C("0a0312")])))
    for i in range(40):
        x = (i * 211 + t * 10 * (i % 3)) % W; y = (i * 137) % H
        cv.drawCircle(x, y, 2 + i % 3, P(C("ffffff", 0.15)))

def draw_brain(cv, t, glow="ff7eb6", dim_front=0.0, tint=1.0):
    path = poly([bp(u, v) for u, v in BRAIN_U])
    cb = skia.Rect(*bp(0.42, 0.42), *bp(1.12, 0.82))
    stem = skia.Path(); stem.moveTo(*bp(0.2, 0.45)); stem.cubicTo(*bp(0.28, 0.8), *bp(0.33, 1.0), *bp(0.36, 1.3))
    cv.drawPath(stem, P(C("c25a9a", 0.7), stroke=0.2 * BS))
    cv.drawOval(cb, P(C("c25a9a", 0.75)))
    cv.drawPath(path, P(C(glow, 0.4), blur=50))
    cv.drawPath(path, P(0, shader=lin(BX - BS, BY - BS, BX + BS, BY + BS, [C("ff9fd0", 0.75 * tint), C("a3489a", 0.75 * tint)])))
    cv.save(); cv.clipPath(path, skia.ClipOp.kIntersect, True)
    for g in GYRI:
        cv.drawPath(poly([bp(u, v) for u, v in g], close=False), P(C("ffd3ea", 0.45), stroke=7))
    if dim_front > 0:
        cv.drawRect(skia.Rect(0, 0, BX - 0.35 * BS, H), P(0, shader=lin(BX - 1.2 * BS, 0, BX - 0.3 * BS, 0, [C("0a0312", 0.75 * dim_front), C("0a0312", 0)])))
    cv.restore()
    cv.drawPath(path, P(C("ffd3ea", 0.9), stroke=5))
    return path

VTA = (0.15, 0.3)
TARGETS = [(-0.95, -0.25), (-0.4, 0.12), (-0.7, -0.6), (-1.0, 0.1)]

def cut_dopamine(cv, t, d):
    brain_bg(cv, t, "3a1a0a")
    draw_brain(cv, t, glow="ffc93c")
    vx, vy = bp(*VTA)
    pulse = 1 + 0.2 * math.sin(t * 8)
    cv.drawCircle(vx, vy, 90 * pulse, P(C("ffc93c", 0.45), blur=30))
    cv.drawCircle(vx, vy, 34 * pulse, P(C("fff1a8")))
    for i in range(70):
        q = ((t * 0.7 + i / 70) % 1)
        if t < 0.3 + (i / 70) * 0.8:
            continue
        tg = TARGETS[i % 4]
        cx_, cy_ = bp((VTA[0] + tg[0]) / 2, min(VTA[1], tg[1]) - 0.35 - 0.1 * (i % 3))
        tx_, ty_ = bp(*tg)
        x = (1 - q) ** 2 * vx + 2 * (1 - q) * q * cx_ + q * q * tx_
        y = (1 - q) ** 2 * vy + 2 * (1 - q) * q * cy_ + q * q * ty_
        cv.drawCircle(x, y, 22, P(C("ffc93c", 0.35), blur=8))
        cv.drawCircle(x, y, 8, P(C("fff4c2")))
    for tg in TARGETS[:2]:
        tx_, ty_ = bp(*tg)
        cv.drawCircle(tx_, ty_, 70 + 10 * math.sin(t * 6), P(C("ffc93c", 0.3 * ss(0.8, 1.5, t)), blur=25))
    a, s = pop(t, 0.3)
    chip(cv, vx + 120, vy + 200, "VTA", a=a, scale=s, col="ffc93c", fg="3a2400", size=40)
    a, s = pop(t, 1.0)
    chip(cv, 260, 700, "reward!", a=a, scale=s, col="ffffff", size=40)

def cut_serotonin(cv, t, d):
    brain_bg(cv, t, "0a1a3a")
    draw_brain(cv, t, glow="5ab8ff", tint=0.85)
    drain = ss(0.2, d * 0.8, t)
    rr = np.random.default_rng(9)
    for i in range(60):
        u, v = rr.uniform(-1.0, 1.0), rr.uniform(-0.8, 0.4)
        x, y = bp(u, v)
        y += drain * rr.uniform(150, 600)
        a = 1 - ss(0.2 + rr.uniform(0, 0.5), 0.9, drain)
        cv.drawCircle(x, y, 18, P(C("5ab8ff", 0.4 * a), blur=8))
        cv.drawCircle(x, y, 7, P(C("dff2ff", a)))
    # looping thought
    for j in range(26):
        ang = t * 3.2 - j * 0.09
        x = BX + math.cos(ang) * BS * 1.35
        y = BY - 80 + math.sin(ang) * BS * 0.75
        cv.drawCircle(x, y, 24 * (1 - j / 26) + 3, P(C("ff6fae", 0.9 * (1 - j / 26)), blur=3 if j else 0))
    ang = t * 3.2
    hx, hy = BX + math.cos(ang) * BS * 1.35, BY - 80 + math.sin(ang) * BS * 0.75
    cv.drawPath(heart_path(hx, hy, 22), P(C("ffffff")))
    # meter
    mx, my = 140, 1380
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(mx, my, mx + 800, my + 40), 20, 20), P(C("ffffff", 0.2)))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(mx, my, mx + 800 * (1 - 0.7 * drain), my + 40), 20, 20), P(C("5ab8ff")))
    text(cv, "SEROTONIN", mx, my - 16, 36, C("ffffff"), tf=TF_XB, align="l")
    a, s = pop(t, 0.8)
    chip(cv, 540, 560, "thinking about him… again", a=a, scale=s, col="ff6fae", fg="ffffff", size=38)

def cut_heart(cv, t, d):
    brain_bg(cv, t, "3a0a12")
    body = skia.Path()
    body.addCircle(540, 560, 150)
    torso = skia.Path()
    torso.moveTo(470, 700); torso.lineTo(470, 740); torso.cubicTo(330, 760, 250, 800, 240, 900)
    torso.cubicTo(230, 1100, 280, 1300, 300, 1500); torso.lineTo(780, 1500)
    torso.cubicTo(800, 1300, 850, 1100, 840, 900); torso.cubicTo(830, 800, 750, 760, 610, 740); torso.lineTo(610, 700); torso.close()
    for pth in (body, torso):
        cv.drawPath(pth, P(C("ff8a6b", 0.12)))
        cv.drawPath(pth, P(C("ffc2b0", 0.6), stroke=5))
    cv.drawOval(skia.Rect(440, 480, 640, 620), P(C("ff9fd0", 0.8)))
    cv.drawCircle(540, 550, 120, P(C("ff9fd0", 0.3), blur=30))
    # spine with pulses
    cv.drawLine(540, 640, 540, 1420, P(C("ffd0c0", 0.5), stroke=10))
    for k in range(6):
        q = (t * 1.8 + k / 6) % 1
        y = 640 + q * 780
        cv.drawCircle(540, y, 26, P(C("ffe066", 0.6), blur=10)); cv.drawCircle(540, y, 9, P(C("ffffff")))
        for side in (-1, 1):
            cv.drawLine(540, y, 540 + side * 160 * q, y + 60 * q, P(C("ffe066", 0.5 * (1 - q)), stroke=4))
    # heart pounding
    beat = abs(math.sin(t * 7.5)) ** 4
    s = 58 * (1 + 0.25 * beat)
    hx, hy = 600, 900
    cv.drawPath(heart_path(hx, hy, s * 1.2), P(C("ff3b3b", 0.5), blur=30))
    cv.drawPath(heart_path(hx, hy, s), P(0, shader=rad(hx - 20, hy - 30, s * 1.6, [C("ff8080"), C("d61a2a")])))
    cv.drawCircle(hx, hy, 80 + 150 * ((t * 1.2) % 1), P(C("ff5a5a", 0.6 * (1 - (t * 1.2) % 1)), stroke=6))
    # stomach: light pulsing away
    sx, sy = 520, 1180
    for k in range(3):
        q = (t * 0.9 + k / 3) % 1
        cv.drawOval(skia.Rect(sx - 90 - 160 * q, sy - 60 - 100 * q, sx + 90 + 160 * q, sy + 60 + 100 * q), P(C("ffb36b", 0.5 * (1 - q)), stroke=5))
    cv.drawOval(skia.Rect(sx - 80, sy - 50, sx + 80, sy + 50), P(C("ffb36b", 0.25)))
    for k in range(5):
        q = (t * 1.4 + k / 5) % 1
        cv.drawPath(heart_path(sx - 60 + k * 30, sy - q * 160, 10), P(C("ffd1dc", 1 - q)))
    a, s_ = pop(t, 0.3)
    chip(cv, 820, 860, "♥ racing", a=a, scale=s_, col="ff3b3b", fg="ffffff", size=38)
    a, s_ = pop(t, 0.9)
    chip(cv, 260, 1180, "butterflies", a=a, scale=s_, col="ffb36b", fg="3a1206", size=38)

PFC_WIN = [(RNG.uniform(-1.12, -0.45), RNG.uniform(-0.75, 0.25), RNG.uniform(0, 1)) for _ in range(40)]

def cut_blind(cv, t, d):
    brain_bg(cv, t, "2a0a2a")
    off = ss(0.3, d * 0.75, t)
    path = draw_brain(cv, t, glow="ff6fae", dim_front=off)
    cv.save(); cv.clipPath(path, skia.ClipOp.kIntersect, True)
    lx, ly = bp(0.0, 0.15)
    cv.drawCircle(lx, ly, 220, P(C("ff6fae", 0.55 + 0.15 * math.sin(t * 4)), blur=60))
    for (u, v, z) in PFC_WIN:
        on = 1.0 if off < z else 0.0
        x, y = bp(u, v)
        cv.drawRect(skia.Rect(x - 12, y - 9, x + 12, y + 9), P(C("ffffff", 0.9 * on + 0.08)))
        if on:
            cv.drawRect(skia.Rect(x - 16, y - 13, x + 16, y + 13), P(C("ffffff", 0.35), blur=8))
    cv.restore()
    a, s = pop(t, 0.4)
    px, py = bp(-0.8, -0.95)
    chip(cv, px + 60, py - 40, "judgement", a=a, scale=s, col="ffffff", size=38)
    a2, s2 = pop(t, d * 0.75)
    chip(cv, px + 60, py - 40, "judgement: OFF", a=a2, scale=s2, col="2a0a2a", fg="ffffff", size=38)

CUT_FN = {"dopamine": cut_dopamine, "serotonin": cut_serotonin, "heart": cut_heart, "blind": cut_blind}

# ------------------------------------------------------------------ overlays
TOP_CAPTION = ["When you ask him why your heart", "races every time he texts"]

def draw_top_caption(cv):
    f = skia.Font(TF_B, 44)
    w = max(f.measureText(s) for s in TOP_CAPTION) + 60
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 290), 14, 14)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10))
    cv.drawRRect(r, P(C("ffffff")))
    for i, s in enumerate(TOP_CAPTION):
        text(cv, s, 540, 210 + i * 56, 44, C("111111"), tf=TF_B)

def build_caps():
    caps = []
    for s in SEGS:
        words = s["text"].replace("No oh.", "No o.").replace("V T A", "VTA").replace("O C D", "OCD").replace("...", "…").split()
        chunks, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= 3 or w[-1] in ",.!?…":
                chunks.append(cur); cur = []
        if cur:
            chunks.append(cur)
        wts = [sum(len(w) + 1 for w in c) + (5 if c[-1][-1] in ",.!?…" else 0) for c in chunks]
        tot = sum(wts); acc = 0
        for c, wt in zip(chunks, wts):
            caps.append((s["s"] + (s["e"] - s["s"]) * acc / tot, s["s"] + (s["e"] - s["s"]) * (acc + wt) / tot, c, s["who"]))
            acc += wt
    return caps

CAPS = build_caps()

def draw_caption(cv, t):
    for (a, b, words, who) in CAPS:
        if a <= t < b + 0.06:
            k = ease_out_back((t - a) / 0.2, 2.0)
            f = skia.Font(TF_BLACK, 76)
            s = " ".join(words).upper()
            w = f.measureText(s)
            size = 76 if w < 960 else 76 * 960 / w
            f = skia.Font(TF_BLACK, size)
            w = f.measureText(s)
            cv.save(); cv.translate(540, 1690); cv.scale(k, k)
            col = C("ffd23f") if who == "A" else C("ffffff")
            cv.drawString(s, -w / 2, 26 + 6, f, P(C("000000", 0.5), stroke=18, blur=6))
            cv.drawString(s, -w / 2, 26, f, P(C("000000"), stroke=15))
            cv.drawString(s, -w / 2, 26, f, P(col))
            cv.restore()
            break
    # speaker tag
    for s in SEGS:
        if s["s"] <= t < s["e"]:
            name = "AMAKA" if s["who"] == "A" else "TAYO"
            col = "ffd23f" if s["who"] == "A" else "ffffff"
            chip(cv, 540, 1590, name, a=0.95, col=col, fg="1a1a1a", size=30)
            break

def draw_card(cv, t):
    for (a, b, label, bg_, fg) in CARDS:
        if a <= t < b:
            al, k = pop(t, a, 0.45)
            al *= 1 - ss(b - 0.2, b, t)
            chip(cv, 540, 400, label, a=al, scale=k * 1.0, col=bg_, fg=fg, size=66)
    if t >= TAIL_T + 0.6:
        al, k = pop(t, TAIL_T + 0.6, 0.5)
        chip(cv, 540, 400, "DOES LOVE EXPIRE?", a=al, scale=k, col="ff4f7b", fg="ffffff", size=62)
        ya = 500 + 14 * math.sin(t * 6)
        pth = skia.Path(); pth.moveTo(540, ya); pth.lineTo(540, ya + 60); pth.moveTo(510, ya + 32); pth.lineTo(540, ya + 64); pth.lineTo(570, ya + 32)
        cv.drawPath(pth, P(C("ffffff", al), stroke=14))

def render_frame(cv, t):
    cut = None
    for (a, b, kind) in CUTS:
        if a <= t < b:
            cut = (a, b, kind)
    def world():
        z, wx, wy, sx, sy = camera(t)
        cv.save(); cv.translate(sx, sy); cv.scale(z, z); cv.translate(-wx, -wy)
        draw_world(cv, t)
        cv.restore()
    if cut:
        a, b, kind = cut
        CUT_FN[kind](cv, t - a, b - a)
        if t < a + 0.2:
            cv.saveLayerAlpha(None, int(255 * (1 - (t - a) / 0.2))); world(); cv.restore()
        if t > b - 0.2:
            cv.saveLayerAlpha(None, int(255 * (t - (b - 0.2)) / 0.2)); world(); cv.restore()
    else:
        world()
    # scratch flash
    sc = SEGS[16]["e"] + 0.15
    if sc <= t < sc + 0.25:
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("ffffff", 0.6 * (1 - (t - sc) / 0.25))))
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("000000", 0.4)], [0.6, 1])))
    draw_top_caption(cv)
    draw_card(cv, t)
    draw_caption(cv, t)
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
    elif sys.argv[1] == "times":
        print("lines", [(round(s["s"], 1), s["who"]) for s in SEGS]); print("cuts", [(round(a, 1), round(b, 1), k) for a, b, k in CUTS]); print("total", TOTAL)
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
