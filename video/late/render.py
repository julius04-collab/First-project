import math, os, subprocess, sys
import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from render import C, lerpc, clamp, ss, ease_out_back, P, lin, rad, poly, text, chip, pop, TF_BLACK, TF_XB, TF_B

W, H, FPS = 1080, 1920, 30
SPLICE_A, SPLICE_B = 24.18, 4.82
OFF = SPLICE_A - SPLICE_B          # 19.36 s: chorus 2 offset
SONG_END = SPLICE_A + OFF          # 43.54
TOTAL = SONG_END + 4.2
BEAT0, BEAT = 4.98, 0.605
INK = C("15110f")

def lerp(a, b, t):
    return a + (b - a) * t

def lerp2(p, q, t):
    return (lerp(p[0], q[0], t), lerp(p[1], q[1], t))

# ------------------------------------------------------------------ lyrics
# (word, start, syllables) ; phrases: (call/resp label, singer group, words)
CH1 = [
    ("call", "boss", [("Tell", 4.95, 1), ("me", 5.45, 1), ("why", 5.75, 1)], 6.45),
    ("resp", "guy", [("Ain't", 6.45, 1), ("nothing", 7.45, 2), ("but", 7.7, 1), ("a", 7.95, 1), ("heartache", 8.2, 2)], 9.5),
    ("call", "boss", [("Tell", 9.55, 1), ("me", 10.0, 1), ("why", 10.25, 1)], 10.7),
    ("resp", "guy", [("Ain't", 10.7, 1), ("nothing", 11.55, 2), ("but", 11.95, 1), ("a", 12.45, 1), ("mistake", 12.7, 2)], 14.45),
    ("call", "boss", [("Tell", 14.45, 1), ("me", 14.95, 1), ("why", 15.2, 1)], 15.7),
    ("resp", "guy+cw", [("I", 15.7, 1), ("never", 16.2, 2), ("wanna", 16.95, 2), ("hear", 17.45, 1), ("you", 17.95, 1), ("say", 18.45, 1)], 19.65),
    ("final", "all", [("I", 19.7, 1), ("want", 20.7, 1), ("it", 21.45, 1), ("that", 22.2, 1), ("way", 22.95, 1)], 24.1),
]
PHRASES = []
for chorus, off in ((1, 0.0), (2, OFF)):
    for kind, who, words, end in CH1:
        if chorus == 2:
            who = {"boss": "boss", "guy": "crew", "guy+cw": "crew", "all": "all"}[who]
        PHRASES.append(dict(kind=kind, who=who, chorus=chorus, words=[(w, s + off, n) for w, s, n in words], end=end + off,
                            start=words[0][1] + off))

def singers(ph):
    return {"boss": {"boss"}, "guy": {"guy"}, "guy+cw": {"guy", "cw1", "cw2"}, "crew": {"guy", "cw1", "cw2"}, "all": {"boss", "guy", "cw1", "cw2"}}[ph["who"]]

def sing_amp(name, t):
    for ph in PHRASES:
        if ph["start"] <= t < ph["end"] and name in singers(ph):
            ws = ph["words"]
            for i, (w, s, n) in enumerate(ws):
                e = ws[i + 1][1] if i + 1 < len(ws) else ph["end"]
                if s <= t < e:
                    d = e - s
                    u = (t - s) / d
                    if d > 0.75:
                        return 0.55 + 0.25 * abs(math.sin(t * 5)) if u < 0.92 else 0.15
                    return 0.15 + 0.7 * abs(math.sin(math.pi * u * n))
    return 0.0

def phrase_at(t):
    cur = None
    for ph in PHRASES:
        if ph["start"] - 0.05 <= t:
            cur = ph
    return cur

# ------------------------------------------------------------------ characters
CHARS = {
    "guy": dict(skin="7a4a2c", hair="fade", shirt="3b82c4", tie="f2c14e", pants="2b2d42", glasses=False, belly=0),
    "boss": dict(skin="5a3620", hair="bald", shirt="f7f7f7", tie="c0392b", pants="3a3a4a", glasses=True, belly=1, stache=True),
    "cw1": dict(skin="8a5534", hair="puff", shirt="8e44ad", tie=None, pants="2b2d42", glasses=False, belly=0, earrings=True),
    "cw2": dict(skin="6b4128", hair="short", shirt="27ae60", tie=None, pants="2b2d42", glasses=True, belly=0),
}
HR = 72
SH_Y, SH_X = -235, 52
L1, L2 = 108, 104

def ik(sx, sy, tx, ty, outward_x):
    dx, dy = tx - sx, ty - sy
    d = clamp(math.hypot(dx, dy), 20, L1 + L2 - 2)
    a = math.atan2(dy, dx)
    al = math.acos(clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1))
    c1 = (sx + L1 * math.cos(a + al), sy + L1 * math.sin(a + al))
    c2 = (sx + L1 * math.cos(a - al), sy + L1 * math.sin(a - al))
    hx, hy = sx + d * math.cos(a), sy + d * math.sin(a)
    e = c1 if (c1[0] - sx) * outward_x + (c1[1] - sy) * 0.5 > (c2[0] - sx) * outward_x + (c2[1] - sy) * 0.5 else c2
    return e, (hx, hy)

def beat_phase(t):
    return ((t - BEAT0) / BEAT) % 1.0

def beat_idx(t):
    return int(math.floor((t - BEAT0) / BEAT))

def pose(name, t, face=1):
    """face=+1 means the 'front' arm points to viewer right. Returns L/R hand targets rel. to hip, legs mode, flags."""
    f = face
    d = dict(L=(-72, -15), R=(72, -15), legs="stand", lean=0.0, flags=set(), drop=0.0)
    if name == "cross":
        d["L"] = (52, -150); d["R"] = (-52, -142); d["flags"].add("fold")
    elif name == "tap":
        d["L"] = (52, -150); d["R"] = (-52, -142); d["flags"].add("fold"); d["legs"] = "tap"
    elif name == "tiptoe":
        d["L"] = (-30, -190); d["R"] = (70, -175); d["legs"] = "walk"; d["lean"] = 5
    elif name == "freeze":
        d["L"] = (-95, -260); d["R"] = (95, -260); d["flags"].add("palms")
    elif name == "wait":
        d["R"] = (120, -330); d["flags"].add("finger_R")
    elif name == "point":
        d[("R" if f > 0 else "L")] = (f * 255, -255)
        d[("L" if f > 0 else "R")] = (-f * 70, -85)
        d["flags"].add("point")
    elif name == "kneel":
        d["R"] = (16, -175); d["L"] = (-200, -330); d["legs"] = "kneel"; d["drop"] = 125; d["flags"].add("palms")
    elif name == "pray":
        d["L"] = (-6, -195); d["R"] = (6, -195); d["flags"].add("pray")
    elif name == "point_clock":
        d["L"] = (-170, -390); d["R"] = (8, -190); d["flags"].add("finger_L")
    elif name == "uncross":
        d["L"] = (-90, -110); d["R"] = (90, -110); d["flags"].add("palms")
    elif name == "sing_wide":
        d["L"] = (-195, -330); d["R"] = (195, -330); d["flags"].add("palms")
    elif name == "sing_heart":
        d["R"] = (14, -180); d["L"] = (-200, -300); d["flags"].add("palms")
    elif name == "band":
        bp = beat_phase(t); b = beat_idx(t) % 2
        d["R"] = (150, -150) if b == 0 else (120, -360)
        d["L"] = (-14, -180) if b == 0 else (-120, -360)
        d["legs"] = "dance"; d["flags"].add("finger_R")
    elif name == "disco":
        b = beat_idx(t) % 2
        if b == 0:
            d["R"] = (165, -420); d["L"] = (-75, -85)
        else:
            d["L"] = (-165, -420); d["R"] = (75, -85)
        d["legs"] = "dance"; d["flags"] |= {"finger_R", "finger_L"}
    elif name == "mic":
        d["R"] = (30, -300); d["L"] = (-200 + 30 * math.sin(t * 3), -270); d["flags"] |= {"mic", "palms"}; d["legs"] = "dance"
    elif name == "mic_out":
        d["R"] = (200, -250); d["L"] = (-150, -330 + 20 * math.sin(t * 6)); d["flags"] |= {"mic", "palms"}; d["legs"] = "dance"
    elif name == "watch":
        d["L"] = (-20, -200); d["R"] = (20, -190); d["flags"].add("watch")
    elif name == "thumbs":
        d["R"] = (120, -230); d["L"] = (-80, -100); d["flags"] |= {"thumb", "palms"}
    elif name == "sip":
        d["R"] = (34, -292); d["L"] = (-72, -15); d["flags"].add("mug")
    elif name == "hide_bob":
        pass
    return d

def blend(a, b, k):
    o = dict(a)
    o["L"] = lerp2(a["L"], b["L"], k); o["R"] = lerp2(a["R"], b["R"], k)
    o["lean"] = lerp(a["lean"], b["lean"], k); o["drop"] = lerp(a["drop"], b["drop"], k)
    o["flags"] = b["flags"] if k > 0.5 else a["flags"]
    o["legs"] = b["legs"] if k > 0.5 else a["legs"]
    return o

EXPR = {
    "angry": dict(brow=(14, -6), eye="n", mouth="frown"),
    "annoyed": dict(brow=(8, 0), eye="half", mouth="flat"),
    "soft": dict(brow=(2, 0), eye="n", mouth="flat"),
    "smile": dict(brow=(-2, 0), eye="n", mouth="smile"),
    "grin": dict(brow=(-6, -2), eye="n", mouth="grin"),
    "happy": dict(brow=(-8, -2), eye="happy", mouth="grin"),
    "nervous": dict(brow=(-12, 6), eye="wide", mouth="wobble", sweat=True),
    "smug": dict(brow=(4, -10), eye="half", mouth="smirk"),
    "puppy": dict(brow=(-18, 4), eye="puppy", mouth="smile"),
    "sing": dict(brow=(-10, -4), eye="n", mouth="smile"),
    "passion": dict(brow=(-14, 4), eye="shut", mouth="smile"),
    "flat": dict(brow=(4, 4), eye="half", mouth="flat"),
}

def draw_head(cv, cfg, x, y, tilt, expr, look, amp, t, blink_seed):
    e = EXPR[expr]
    skin = C(cfg["skin"])
    R = HR
    cv.save(); cv.translate(x, y); cv.rotate(tilt)
    hair = cfg["hair"]
    if hair == "puff":
        cv.drawCircle(0, -R * 1.15, R * 0.62, P(C("1c120d")))
        cv.drawCircle(0, -R * 1.15, R * 0.62, P(INK, stroke=5))
    head = skia.Rect(-R, -R, R, R)
    cv.drawOval(head, P(skin))
    cv.drawOval(head, P(0, shader=rad(-R * 0.35, -R * 0.4, R * 1.6, [C("ffffff", 0.18), C("000000", 0.0), C("000000", 0.18)], [0, 0.6, 1])))
    cv.save(); oc = skia.Path(); oc.addOval(head); cv.clipPath(oc, skia.ClipOp.kIntersect, True)
    if hair == "fade":
        cv.drawRect(skia.Rect(-R, -R - 4, R, -R * 0.45), P(C("17100b")))
        cv.drawRect(skia.Rect(-R, -R * 0.45, -R * 0.86, R * 0.05), P(C("17100b")))
        cv.drawRect(skia.Rect(R * 0.86, -R * 0.45, R, R * 0.05), P(C("17100b")))
    elif hair == "puff" or hair == "short":
        cv.drawRect(skia.Rect(-R, -R - 4, R, -R * 0.5), P(C("1c120d")))
    elif hair == "bald":
        for sx in (-1, 1):
            cv.drawOval(skia.Rect(sx * R - R * 0.35, -R * 0.35, sx * R + R * 0.35, R * 0.25), P(C("b8b8b8")))
        cv.drawOval(skia.Rect(-R * 0.45, -R * 0.92, -R * 0.05, -R * 0.62), P(C("ffffff", 0.35)))
    cv.restore()
    cv.drawOval(head, P(INK, stroke=6))
    if cfg.get("earrings"):
        for sx in (-1, 1):
            cv.drawCircle(sx * R * 0.98, R * 0.32, 11, P(C("f2c14e"), stroke=5))
    bl = 1.0 if ((t + blink_seed * 1.37) % 3.4) < 0.11 else 0.0
    lx = look
    for ex in (-1, 1):
        cx, cy = ex * 30, -12
        rx, ry = 26, 32
        if e["eye"] in ("wide", "puppy"):
            rx, ry = 30, 37
        eye = skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry)
        if e["eye"] in ("happy", "shut") or bl > 0.5:
            pth = skia.Path(); pth.moveTo(cx - 18, cy + 4); pth.quadTo(cx, cy - 16 if e["eye"] == "happy" else cy + 10, cx + 18, cy + 4)
            cv.drawPath(pth, P(INK, stroke=6))
            continue
        cv.drawOval(eye, P(C("ffffff")))
        pr = 14 if e["eye"] == "puppy" else (8 if e["eye"] == "wide" else 10)
        cv.drawCircle(cx + lx * 10, cy + 4, pr, P(INK))
        cv.drawCircle(cx + lx * 10 - 3, cy - 1, 4 if e["eye"] == "puppy" else 3, P(C("ffffff")))
        if e["eye"] == "puppy":
            cv.drawCircle(cx + lx * 10 + 4, cy + 8, 2, P(C("ffffff")))
        if e["eye"] == "half":
            cv.save(); ec = skia.Path(); ec.addOval(eye); cv.clipPath(ec, skia.ClipOp.kIntersect, True)
            cv.drawRect(skia.Rect(cx - rx - 2, cy - ry - 2, cx + rx + 2, cy - ry * 0.05), P(skin)); cv.restore()
            cv.drawLine(cx - rx, cy - ry * 0.05, cx + rx, cy - ry * 0.05, P(INK, stroke=5))
        cv.drawOval(eye, P(INK, stroke=5))
    if cfg.get("glasses"):
        for ex in (-1, 1):
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(ex * 30 - 34, -48, ex * 30 + 34, 22), 14, 14), P(C("222222"), stroke=5))
        cv.drawLine(-4, -16, 4, -16, P(C("222222"), stroke=5))
    bi, bo = e["brow"]
    for ex in (-1, 1):
        cv.drawLine(ex * 10, -58 + bi, ex * 48, -56 + bo, P(C("b8b8b8") if cfg["hair"] == "bald" else INK, stroke=8))
    my = R * 0.45
    if cfg.get("stache"):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-32, my - 22, 32, my - 8), 7, 7), P(C("c9c9c9")))
    if amp > 0.06:
        w = 20 + 8 * amp; hgt = 6 + 30 * amp
        r = skia.Rect(-w, my - hgt * 0.45, w, my + hgt * 0.7)
        cv.drawOval(r, P(C("3a0c10")))
        cv.save(); oc = skia.Path(); oc.addOval(r); cv.clipPath(oc, skia.ClipOp.kIntersect, True)
        cv.drawOval(skia.Rect(-w * 0.6, my + hgt * 0.2, w * 0.6, my + hgt), P(C("d9536a")))
        cv.drawRect(skia.Rect(-w, my - hgt * 0.45 - 2, w, my - hgt * 0.45 + 6), P(C("ffffff")))
        cv.restore()
        cv.drawOval(r, P(INK, stroke=4))
    else:
        m = e["mouth"]; p = skia.Path()
        if m in ("smile", "grin"):
            p.moveTo(-22, my - 4); p.quadTo(0, my + (14 if m == "smile" else 22), 22, my - 4)
        elif m == "frown":
            p.moveTo(-20, my + 8); p.quadTo(0, my - 8, 20, my + 8)
        elif m == "smirk":
            p.moveTo(-16, my + 4); p.quadTo(4, my + 10, 22, my - 8)
        elif m == "wobble":
            p.moveTo(-20, my + 4)
            for k in range(1, 6):
                p.lineTo(-20 + k * 8, my + (4 if k % 2 == 0 else -2))
        else:
            p.moveTo(-16, my + 2); p.lineTo(16, my + 2)
        cv.drawPath(p, P(INK, stroke=5))
    if e.get("sweat"):
        q = (t * 1.5) % 1
        sx, sy = R * 0.95, -R * 0.4 + q * 40
        dp = skia.Path(); dp.moveTo(sx, sy - 18); dp.quadTo(sx + 14, sy + 4, sx, sy + 10); dp.quadTo(sx - 14, sy + 4, sx, sy - 18)
        cv.drawPath(dp, P(C("7fd3ff", 1 - q * 0.5))); cv.drawPath(dp, P(INK, stroke=3))
    cv.restore()

def legs_for(mode, t, phase_seed=0.0):
    std = [((-20, 150), (-32, 300)), ((20, 150), (32, 300))]
    dy = 0.0
    if mode == "walk":
        ph = t * 5 + phase_seed
        out = []
        for k, sgn in ((0, -1), (1, 1)):
            s = math.sin(ph + k * math.pi)
            lift = max(0, s) * 26
            out.append(((sgn * 20 + 28 * s, 150 - lift * 0.5), (sgn * 30 + 55 * s, 300 - lift)))
        return out, 6 * abs(math.sin(ph))
    if mode == "tap":
        lift = max(0, math.sin(t * 9)) * 16
        return [((-20, 150), (-32, 300)), ((24, 150 - lift * 0.4), (40, 300 - lift))], 0
    if mode == "kneel":
        return [((55, 40), (62, 175)), ((-40, 175), (-135, 178))], 0
    if mode == "dance":
        bp = beat_phase(t)
        bounce = abs(math.sin(math.pi * bp))
        dy = 16 * (1 - bounce)
        sw = 18 * math.sin(math.pi * beat_idx(t))
        return [((-26 + sw * 0.5, 150 - dy * 0.3), (-34, 300 - dy)), ((26 + sw * 0.5, 150 - dy * 0.3), (34, 300 - dy))], dy
    return std, 0

def draw_char(cv, name, x, y, ps, expr, look, amp, t, scale=1.0, layer="all"):
    cfg = CHARS[name]
    cv.save(); cv.translate(x, y); cv.scale(scale, scale)
    legs, dy = legs_for(ps["legs"], t, (len(name) * 3) % 7)
    drop = ps["drop"] + dy
    lean = math.radians(ps["lean"])
    bob = -4 * amp * math.sin(t * 16)
    def rot(px, py):
        return (px * math.cos(lean) - py * math.sin(lean), drop + px * math.sin(lean) + py * math.cos(lean))
    shL, shR = rot(-SH_X, SH_Y + bob), rot(SH_X, SH_Y + bob)
    neck = rot(0, SH_Y - 10 + bob)
    head = rot(0, SH_Y - 28 - HR + bob)
    if layer in ("all", "body"):
        for (kn, ft), k in zip(legs, (-1, 1)):
            hip = (k * 24, drop)
            knee = (kn[0], kn[1]) if ps["legs"] == "kneel" else (kn[0], kn[1] - (300 - (ft[1])) * 0 + 0)
            if ps["legs"] == "kneel":
                hip = (k * 24, drop); knee = (kn[0], drop + kn[1] - 0); foot = (ft[0], drop + ft[1] - 0)
                knee = (kn[0], kn[1] + drop - 125 + 125 - 0) if False else (kn[0], drop + kn[1])
                foot = (ft[0], drop + ft[1])
            else:
                knee = (kn[0], kn[1]); foot = (ft[0], ft[1])
                hip = (k * 24, drop)
            pth = skia.Path(); pth.moveTo(*hip); pth.lineTo(*knee); pth.lineTo(*foot)
            cv.drawPath(pth, P(C(cfg["pants"]), stroke=24))
            sh = skia.Rect(foot[0] - 30 + k * 10, foot[1] - 8, foot[0] + 30 + k * 10, foot[1] + 14)
            cv.drawOval(sh, P(C("1a1a1a")))
        # torso
        bw = 58 + (16 if cfg["belly"] else 0)
        body = poly([rot(-SH_X - 6, SH_Y + 2 + bob), rot(SH_X + 6, SH_Y + 2 + bob), rot(bw, -40), rot(bw - 6, 8), rot(-bw + 6, 8), rot(-bw, -40)])
        cv.drawPath(body, P(C(cfg["shirt"])))
        cv.drawPath(body, P(0, shader=lin(-60, SH_Y, 60, 0, [C("ffffff", 0.15), C("000000", 0.12)])))
        cv.drawPath(body, P(INK, stroke=5))
        if cfg["tie"]:
            tp = poly([rot(-9, SH_Y + 10 + bob), rot(9, SH_Y + 10 + bob), rot(14, SH_Y + 120), rot(0, SH_Y + 145), rot(-14, SH_Y + 120)])
            cv.drawPath(tp, P(C(cfg["tie"]))); cv.drawPath(tp, P(INK, stroke=3))
        cv.drawPath(poly([rot(-22, SH_Y + 2 + bob), rot(0, SH_Y + 22 + bob), rot(22, SH_Y + 2 + bob)], close=False), P(INK, stroke=4))
        cv.drawLine(neck[0], neck[1], head[0], head[1] + HR - 4, P(INK, stroke=9))
        if ps.get("backpack"):
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-SH_X - 24, SH_Y + 8 + drop, -SH_X + 6, SH_Y + 110 + drop), 8, 8), P(C("d9534f")))
            cv.drawLine(-SH_X + 4, SH_Y + 6 + drop, -SH_X + 10, SH_Y + 120 + drop, P(C("8a2a25"), stroke=6))
        def arm(sh, tg, outward, side):
            tx, ty = rot(*tg)
            el, hd = ik(sh[0], sh[1], tx, ty, outward)
            pth = skia.Path(); pth.moveTo(*sh); pth.lineTo(*el); pth.lineTo(*hd)
            cv.drawPath(pth, P(C(cfg["shirt"]), stroke=24))
            cv.drawPath(pth, P(INK, stroke=4))
            # sleeve stops at elbow: forearm skin stick
            cv.drawLine(el[0], el[1], hd[0], hd[1], P(C(cfg["shirt"]), stroke=26))
            cv.drawLine(el[0], el[1], hd[0], hd[1], P(INK, stroke=9))
            cv.drawCircle(el[0], el[1], 13, P(C(cfg["shirt"])))
            fl = ps["flags"]
            cv.drawCircle(hd[0], hd[1], 15, P(C(cfg["skin"]))); cv.drawCircle(hd[0], hd[1], 15, P(INK, stroke=4))
            ang = math.atan2(hd[1] - el[1], hd[0] - el[0])
            if ("finger_" + side) in fl or ("point" in fl and ((side == "R") == (tg[0] > 0)) and abs(tg[0]) > 150):
                cv.drawLine(hd[0], hd[1], hd[0] + 30 * math.cos(ang), hd[1] + 30 * math.sin(ang), P(INK, stroke=7))
            if "thumb" in fl and side == "R":
                cv.drawLine(hd[0], hd[1] - 8, hd[0], hd[1] - 34, P(INK, stroke=8))
            if "mic" in fl and side == "R":
                cv.save(); cv.translate(hd[0], hd[1]); cv.rotate(math.degrees(ang) + 90 if "mic" in fl and tg[1] > -280 else -10)
                cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-8, -6, 8, 46), 5, 5), P(C("2b2b2b")))
                cv.drawCircle(0, -14, 16, P(C("b0b0b0"))); cv.drawCircle(0, -14, 16, P(INK, stroke=3))
                cv.restore()
            if "mug" in fl and side == "R":
                cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(hd[0] - 18, hd[1] - 26, hd[0] + 18, hd[1] + 14), 5, 5), P(C("ffffff")))
                cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(hd[0] - 18, hd[1] - 26, hd[0] + 18, hd[1] + 14), 5, 5), P(INK, stroke=3))
                for k in range(2):
                    q = (t * 0.8 + k * 0.5) % 1
                    cv.drawLine(hd[0] - 6 + k * 12, hd[1] - 32 - q * 30, hd[0] - 2 + k * 12, hd[1] - 46 - q * 30, P(C("ffffff", 0.7 * (1 - q)), stroke=4))
            if "watch" in fl and side == "L":
                cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(hd[0] - 30, hd[1] - 12, hd[0] - 10, hd[1] + 12), 4, 4), P(C("f2c14e")))
        arm(shL, ps["L"], -1, "L")
        arm(shR, ps["R"], 1, "R")
        draw_head(cv, cfg, head[0], head[1], math.degrees(lean) * 0.5 + 4 * amp * math.sin(t * 8), expr, look, amp, t, (len(name) + ord(name[-1])) % 5)
        if "fold" in ps["flags"]:
            tx, ty = rot(*ps["L"])
            el, hd = ik(shL[0], shL[1], tx, ty, -1)
            cv.drawLine(el[0], el[1], hd[0], hd[1], P(C(cfg["shirt"]), stroke=26)); cv.drawLine(el[0], el[1], hd[0], hd[1], P(INK, stroke=9))
            cv.drawCircle(hd[0], hd[1], 15, P(C(cfg["skin"]))); cv.drawCircle(hd[0], hd[1], 15, P(INK, stroke=4))
    cv.restore()

# ------------------------------------------------------------------ choreography
# keyframes per character: (time, pose, expr, look)
K = {
    "boss": [(0, "tap", "angry", -1), (4.4, "cross", "angry", -1), (4.95, "point", "angry", -1), (6.45, "cross", "annoyed", -1),
             (9.55, "point", "annoyed", -1), (10.7, "cross", "soft", -1), (14.45, "uncross", "soft", -1), (15.7, "uncross", "smile", -1),
             (17.4, "sing_wide", "grin", -1), (19.7, "sing_wide", "sing", 0), (23.0, "band", "sing", 0),
             (24.0, "mic", "sing", 0), (25.7, "mic_out", "grin", -1), (28.9, "mic", "sing", 0), (30.1, "mic_out", "grin", -1),
             (33.8, "mic", "sing", 0), (35.1, "mic_out", "grin", -1), (39.0, "disco", "sing", 0), (43.6, "watch", "flat", 0),
             (44.9, "thumbs", "smile", -1)],
    "guy": [(0, "tiptoe", "smug", 1), (2.6, "freeze", "nervous", 1), (4.0, "wait", "smug", 1), (6.45, "kneel", "passion", 1),
            (9.55, "kneel", "puppy", 1), (10.7, "point_clock", "puppy", 1), (12.6, "pray", "puppy", 1), (15.7, "sing_wide", "sing", 0),
            (19.7, "band", "sing", 0), (24.0, "disco", "happy", 1), (25.7, "disco", "sing", 0), (39.0, "disco", "sing", 0),
            (43.6, "sip", "smug", 0)],
    "cw1": [(0, "hide_bob", "flat", 0), (15.7, "sing_wide", "sing", 0), (19.7, "band", "sing", 0), (24.0, "disco", "happy", 1),
            (25.7, "disco", "sing", 0), (43.6, "hide_bob", "smile", 0)],
    "cw2": [(0, "hide_bob", "flat", 0), (15.7, "sing_wide", "sing", 0), (19.7, "band", "sing", 0), (24.0, "disco", "happy", -1),
            (25.7, "disco", "sing", 0), (43.6, "hide_bob", "smile", 0)],
}

def char_state(name, t):
    ks = K[name]
    i = max(j for j in range(len(ks)) if ks[j][0] <= t)
    t0, pn, ex, lk = ks[i]
    face = -1 if name == "boss" else 1
    cur = pose(pn, t, face)
    if i > 0:
        prev = pose(ks[i - 1][1], t, face)
        k = ss(t0, t0 + 0.22, t)
        ps = blend(prev, cur, k)
        if k < 0.5:
            ex, lk = ks[i - 1][2], ks[i - 1][3]
    else:
        ps = cur
    return ps, ex, lk

def positions(t):
    gx = lerp(-120, 330, ss(0.3, 2.6, t))
    gy = 1300
    j = ss(15.75, 16.15, t) * (1 - ss(24.0, 24.4, t))
    hop = math.sin(math.pi * ss(15.75, 16.15, t)) * 80 + math.sin(math.pi * ss(24.0, 24.4, t)) * 80
    gy = lerp(1300, 1040, j) - hop
    gx = lerp(gx, 300, ss(24.0, 24.4, t)) if t > 24 else gx
    bx = lerp(760, 560, ss(24.0, 24.6, t)) if t < 43.6 else lerp(560, 700, ss(43.6, 44.2, t))
    bx = lerp(bx, 760, 0) if t < 24 else bx
    if 24.6 <= t < 43.6:
        bx = 560
    pop1 = ss(15.6, 16.0, t) * (1 - ss(43.7, 44.2, t))
    pop2 = ss(15.75, 16.15, t) * (1 - ss(43.8, 44.3, t))
    return dict(guy=(gx, gy), boss=(bx, 1300), cw1=(200, 1215 + 420 * (1 - pop1)), cw2=(880, 1215 + 420 * (1 - pop2)))

# ------------------------------------------------------------------ set
RNG = np.random.default_rng(5)

def draw_set(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, 1300), P(0, shader=lin(0, 0, 0, 1300, [C("e8eef2"), C("cfd9e0")])))
    cv.drawRect(skia.Rect(0, 1180, W, 1300), P(C("b9c6cf")))
    # window
    wx0, wy0, wx1, wy1 = 560, 330, 1010, 820
    cv.drawRect(skia.Rect(wx0, wy0, wx1, wy1), P(0, shader=lin(0, wy0, 0, wy1, [C("8fd0f5"), C("d6f0ff")])))
    rr = np.random.default_rng(2)
    x = wx0
    while x < wx1:
        bw = rr.uniform(40, 90); bh = rr.uniform(120, 330)
        cv.drawRect(skia.Rect(x, wy1 - bh, x + bw, wy1), P(C(rr.choice(["9fb4c4", "aebfcc", "8ea5b7"]))))
        for yy in np.arange(wy1 - bh + 12, wy1 - 10, 22):
            for xx in np.arange(x + 8, x + bw - 8, 16):
                cv.drawRect(skia.Rect(xx, yy, xx + 7, yy + 10), P(C("e9f4fb", 0.8)))
        x += bw + 6
    cv.drawCircle(wx1 - 70, wy0 + 70, 40, P(C("fff3b0")))
    for k in range(1, 3):
        cv.drawLine(wx0 + k * (wx1 - wx0) / 3, wy0, wx0 + k * (wx1 - wx0) / 3, wy1, P(C("ffffff"), stroke=12))
    cv.drawRect(skia.Rect(wx0, wy0, wx1, wy1), P(C("ffffff"), stroke=18))
    # clock
    cx, cy, r = 250, 470, 82
    cv.drawCircle(cx, cy + 6, r, P(C("000000", 0.2), blur=8))
    cv.drawCircle(cx, cy, r, P(C("ffffff"))); cv.drawCircle(cx, cy, r, P(INK, stroke=9))
    for k in range(12):
        a = k * math.pi / 6
        cv.drawLine(cx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78, cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.9, P(INK, stroke=5))
    mins = 47 + t / 60 * 0
    ah = math.radians((9 + mins / 60) * 30 - 90); am = math.radians(mins * 6 - 90); as_ = math.radians(t * 6 * 6 - 90)
    cv.drawLine(cx, cy, cx + math.cos(ah) * r * 0.5, cy + math.sin(ah) * r * 0.5, P(INK, stroke=9))
    cv.drawLine(cx, cy, cx + math.cos(am) * r * 0.75, cy + math.sin(am) * r * 0.75, P(INK, stroke=6))
    cv.drawLine(cx, cy, cx + math.cos(as_) * r * 0.8, cy + math.sin(as_) * r * 0.8, P(C("e74c3c"), stroke=3))
    cv.drawCircle(cx, cy, 7, P(INK))
    # poster
    cv.drawRect(skia.Rect(140, 630, 370, 900), P(C("ffffff")))
    cv.drawRect(skia.Rect(140, 630, 370, 900), P(C("34495e"), stroke=10))
    cv.drawRect(skia.Rect(160, 650, 350, 800), P(0, shader=lin(0, 650, 0, 800, [C("f39c12"), C("e74c3c")])))
    text(cv, "BE ON", 255, 845, 34, C("2c3e50"), tf=TF_BLACK)
    text(cv, "TIME", 255, 882, 34, C("2c3e50"), tf=TF_BLACK)
    star = skia.Path()
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5; rr_ = 55 if k % 2 == 0 else 22
        px, py = 255 + math.cos(a) * rr_, 725 + math.sin(a) * rr_
        star.moveTo(px, py) if k == 0 else star.lineTo(px, py)
    star.close(); cv.drawPath(star, P(C("ffffff")))
    # water cooler
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(950, 1000, 1060, 1300), 10, 10), P(C("ecf0f1")))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(950, 1000, 1060, 1300), 10, 10), P(C("95a5a6"), stroke=5))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(965, 840, 1045, 1000), 30, 30), P(C("7fc8f8", 0.85)))
    # floor
    cv.drawRect(skia.Rect(0, 1300, W, H), P(0, shader=lin(0, 1300, 0, H, [C("8a97a3"), C("66727d")])))
    for k in range(-6, 10):
        cv.drawLine(540 + k * 60, 1300, 540 + k * 200, H, P(C("5a6570", 0.4), stroke=3))

def draw_partitions(cv):
    for (x0, x1) in ((40, 420), (660, 1040)):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0, 1110, x1, 1330), 10, 10), P(C("5d6d7e")))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0 + 12, 1124, x1 - 12, 1318), 6, 6), P(C("85929e")))
        cv.drawRect(skia.Rect(x0, 1104, x1, 1118), P(C("34495e")))

def draw_front_desk(cv):
    cv.drawRect(skia.Rect(90, 1330, 520, 1352), P(C("a0714f")))
    cv.drawRect(skia.Rect(105, 1352, 505, 1560), P(C("8a5d3e")))
    cv.drawRect(skia.Rect(105, 1352, 505, 1560), P(C("000000", 0.15), stroke=4))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(110, 1180, 260, 1290), 8, 8), P(C("2c3e50")))
    cv.drawRect(skia.Rect(120, 1190, 250, 1280), P(C("5dade2")))
    cv.drawRect(skia.Rect(175, 1290, 195, 1330), P(C("2c3e50")))
    cv.drawRect(skia.Rect(130, 1316, 240, 1330), P(C("2c3e50")))

def draw_disco(cv, t, amt):
    if amt <= 0:
        return
    cv.drawRect(skia.Rect(0, 0, W, H), P(C("1a0a33", 0.62 * amt)))
    cols = ["ff4f9a", "4fc3ff", "ffd23f", "7dff6b"]
    for k in range(4):
        a = math.sin(t * (0.9 + k * 0.2) + k * 1.5) * 0.5
        sx = 140 + k * 266
        tip = (sx, -20)
        L = 1900
        p1 = (sx + math.sin(a - 0.13) * L, math.cos(a - 0.13) * L)
        p2 = (sx + math.sin(a + 0.13) * L, math.cos(a + 0.13) * L)
        cv.drawPath(poly([tip, p1, p2]), P(C(cols[k], 0.18 * amt)))
    by = lerp(-100, 300, ss(0, 1, amt))
    cv.drawLine(540, 0, 540, by - 70, P(C("aaaaaa", amt), stroke=4))
    cv.drawCircle(540, by, 70, P(C("c0c0c0", amt)))
    for i in range(36):
        a = i * 0.7 + t * 2
        fx, fy = 540 + math.cos(a) * 50 * ((i % 4) / 4 + 0.3), by + math.sin(a * 1.3) * 50 * ((i % 3) / 3 + 0.3)
        cv.drawRect(skia.Rect(fx - 7, fy - 7, fx + 7, fy + 7), P(C("ffffff" if i % 3 else "9fd0ff", 0.9 * amt * (0.5 + 0.5 * math.sin(t * 8 + i)))))
    for i in range(30):
        x = (i * 151 + t * 120 * (1 + i % 3)) % W
        y = (i * 263 + t * 40) % 1300
        cv.drawCircle(x, y, 6, P(C(cols[i % 4], 0.7 * amt), blur=3))

CONF = [(RNG.uniform(0, W), RNG.uniform(-400, 0), RNG.uniform(0, 6.28), RNG.choice(["ff4f9a", "4fc3ff", "ffd23f", "7dff6b", "ffffff"]), RNG.uniform(150, 320)) for _ in range(120)]

def draw_confetti(cv, t, t0):
    if t < t0:
        return
    q = t - t0
    for (x, y, ph, col, sp) in CONF:
        yy = y + q * sp
        if yy > H:
            continue
        cv.save(); cv.translate(x + 30 * math.sin(q * 2 + ph), yy); cv.rotate(math.degrees(q * 4 + ph))
        cv.drawRect(skia.Rect(-9, -5, 9, 5), P(C(col, 1 - ss(3.5, 4.5, q))))
        cv.restore()

def bubble(cv, x, y, lines, a, k):
    if a <= 0:
        return
    cv.save(); cv.translate(x, y); cv.scale(k, k); cv.saveLayerAlpha(None, int(a * 255))
    f = skia.Font(TF_BLACK, 44)
    w = max(f.measureText(s) for s in lines) + 60
    h = 60 * len(lines) + 30
    r = skia.RRect.MakeRectXY(skia.Rect(-w / 2, -h, w / 2, 0), 30, 30)
    tail = poly([(30, -4), (80, 50), (80, -4)])
    cv.drawRRect(r, P(C("000000", 0.25), blur=10))
    cv.drawRRect(r, P(C("ffffff"))); cv.drawPath(tail, P(C("ffffff")))
    cv.drawRRect(r, P(INK, stroke=5))
    cv.drawLine(32, -2, 80, 50, P(INK, stroke=5)); cv.drawLine(80, 50, 80, -2, P(INK, stroke=5))
    cv.drawLine(34, -3, 78, -3, P(C("ffffff"), stroke=8))
    for i, s in enumerate(lines):
        text(cv, s, 0, -h + 62 + i * 60, 44, C("c0392b") if i == 0 else INK)
    cv.restore(); cv.restore()

def draw_world(cv, t):
    draw_set(cv, t)
    disco = ss(19.6, 20.1, t) * (1 - ss(43.55, 43.9, t))
    pos = positions(t)
    order_back = ["cw1", "cw2"]
    cv.save(); cv.clipRect(skia.Rect(0, 0, W, 1320))
    for n in order_back:
        ps, ex, lk = char_state(n, t)
        x, y = pos[n]
        draw_char(cv, n, x, y, ps, ex, lk, sing_amp(n, t), t, scale=0.82)
    cv.restore()
    draw_partitions(cv)
    draw_front_desk(cv)
    draw_disco(cv, t, disco)
    for n in ("boss", "guy"):
        ps, ex, lk = char_state(n, t)
        if n == "guy" and t < 3.9:
            ps["backpack"] = True
        x, y = pos[n]
        if disco > 0:
            cv.drawOval(skia.Rect(x - 130, 1560, x + 130, 1640) if n == "boss" or y > 1200 else skia.Rect(x - 130, 1300, x + 130, 1370),
                        P(C("fff3b0", 0.35 * disco), blur=20))
        draw_char(cv, n, x, y, ps, ex, lk, sing_amp(n, t), t)
    # dropped backpack
    if t >= 3.9:
        fall = ss(3.9, 4.25, t)
        bx_, by_ = 250, lerp(1080, 1560, fall)
        cv.save(); cv.translate(bx_, by_); cv.rotate(70 * fall)
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-40, -55, 40, 40), 14, 14), P(C("d9534f")))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-40, -55, 40, 40), 14, 14), P(INK, stroke=4))
        cv.restore()
    a, k = pop(t, 1.5, 0.4)
    a *= 1 - ss(4.6, 4.9, t)
    bubble(cv, 640, 830, ["You're 47 minutes", "LATE!!"], a, k)
    draw_confetti(cv, t, 42.9)

# ------------------------------------------------------------------ camera
def shot_at(t):
    ph = phrase_at(t)
    if t < 4.9:
        return ("wide", None)
    if t >= SONG_END:
        return ("wide", None)
    if ph is None:
        return ("wide", None)
    if ph["kind"] == "call":
        return ("boss", None)
    if ph["kind"] == "resp":
        if ph["chorus"] == 1 and ph["words"][-1][0] == "heartache":
            return ("guy", None)
        return ("wide", None)
    return ("group", ph["start"])

def camera(t):
    shot, st = shot_at(t)
    pos = positions(t)
    if shot == "boss":
        bx, by = pos["boss"]
        return 1.75, bx, by - 330, 540, 860
    if shot == "guy":
        gx, gy = pos["guy"]
        return 1.45, gx + 60, gy - 220, 540, 900
    if shot == "group":
        z = 1.0 + 0.12 * ss(st, st + 4.3, t)
        return z, 540, 1100, 540, 1100
    z = 1.0 + (0.04 * ss(0, 4.9, t) if t < 4.9 else 0)
    return z, 540, 1150, 540, 1150

# ------------------------------------------------------------------ overlays
TOP = ["When you come late to work but you", "know exactly how to handle your boss"]

def draw_top(cv):
    f = skia.Font(TF_B, 42)
    w = max(f.measureText(s) for s in TOP) + 60
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 140, 540 + w / 2, 276), 14, 14)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    for i, s in enumerate(TOP):
        text(cv, s, 540, 198 + i * 54, 42, C("111111"), tf=TF_B)

def draw_lyrics(cv, t):
    ph = phrase_at(t)
    if ph is None or t > ph["end"] + 0.3 or t < 4.85:
        return
    idx = PHRASES.index(ph)
    lines = []
    if ph["kind"] == "resp":
        lines.append((PHRASES[idx - 1]["words"], False))
        lines.append((ph["words"], True))
    else:
        lines.append((ph["words"], True))
    f = skia.Font(TF_BLACK, 68)
    y0 = 1720 if len(lines) == 2 else 1760
    for li, (words, active) in enumerate(lines):
        shown = [(w, s) for (w, s, n) in words if (not active) or s <= t + 0.02]
        if not shown:
            continue
        s_all = " ".join(w for w, s in shown)
        total = f.measureText(s_all)
        x = 540 - total / 2
        y = y0 + li * 84
        cur_i = len(shown) - 1
        for i, (w, s) in enumerate(shown):
            col = C("ffd23f") if (active and i == cur_i) else C("ffffff")
            cv.drawString(w, x, y, f, P(C("000000"), stroke=14))
            cv.drawString(w, x, y, f, P(col))
            x += f.measureText(w + " ")
    # who's singing tag
    name = {"boss": "BOSS", "guy": "HIM", "crew": "EVERYBODY", "all": "EVERYBODY"}.get(ph["who"], "HIM + THE OFFICE")
    if ph["who"] == "guy+cw":
        name = "HIM + THE OFFICE"
    chip(cv, 540, y0 - 92, name, a=0.95, col="ffd23f" if ph["who"] == "boss" else "ffffff", fg="1a1a1a", size=30)

def render_frame(cv, t):
    z, wx, wy, sx, sy = camera(t)
    cv.save(); cv.translate(sx, sy); cv.scale(z, z); cv.translate(-wx, -wy)
    draw_world(cv, t)
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("000000", 0.35)], [0.6, 1])))
    draw_top(cv)
    draw_lyrics(cv, t)
    if t >= 45.0:
        a, k = pop(t, 45.0, 0.5)
        chip(cv, 540, 400, "HOW TO COME LATE TO WORK 101", a=a, scale=k, col="ffd23f", fg="1a1a1a", size=50)
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
        N = int(math.ceil(TOTAL * FPS)); nw = 4; step = math.ceil(N / nw)
        jobs = [(k, k * step, min(N, (k + 1) * step), os.path.join(HERE, f"part{k}.mp4")) for k in range(nw)]
        with Pool(nw) as p:
            outs = p.map(worker, jobs)
        with open(os.path.join(HERE, "parts.txt"), "w") as f:
            for o in outs:
                f.write(f"file '{o}'\n")
        print("frames", N, "dur", TOTAL)
