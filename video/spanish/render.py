import importlib.util, json, math, os, subprocess, sys
import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "video"))
from render import C, lerpc, clamp, ss, ease_out_back, P, lin, rad, poly, text, chip, pop, TF_BLACK, TF_XB, TF_B

spec = importlib.util.spec_from_file_location("late_render", os.path.join(HERE, "..", "late", "render.py"))
LR = importlib.util.module_from_spec(spec); spec.loader.exec_module(LR)

W, H, FPS = 1080, 1920, 30
INK = C("15110f")
D = json.load(open(os.path.join(HERE, "vo.json")))
LEAD = 0.6
SEGS = D["segs"]
for s in SEGS:
    s["s"] = s["start"] + LEAD; s["e"] = s["end"] + LEAD
BEAT_T = D["beat_start"] + LEAD
BPM = D["bpm"]; BEAT = 60 / BPM
TOTAL = D["end"] + LEAD + 2.6
END_CARD = SEGS[-1]["e"] + 0.3

def lerp(a, b, t):
    return a + (b - a) * t

# ------------------------------------------------------------------ characters
LR.CHARS["guy"] = dict(skin="7a4a2c", hair="cap", shirt="2c3e50", tie=None, pants="2b2d42", glasses=False, belly=0)
LR.CHARS["sofia"] = dict(skin="d9a37a", hair="long", shirt="e74c3c", tie=None, pants="2b2d42", glasses=False, belly=0, earrings=True)
LR.EXPR["confused"] = dict(brow=(-14, 10), eye="wide", mouth="wobble")
LR.EXPR["shock"] = dict(brow=(-20, -20), eye="wide", mouth="flat")
LR.EXPR["teach"] = dict(brow=(-4, -2), eye="n", mouth="smile")
_orig_head = LR.draw_head

def head_wrap(cv, cfg, x, y, tilt, expr, look, amp, t, seed):
    R = LR.HR
    if cfg["hair"] == "long":
        cv.save(); cv.translate(x, y); cv.rotate(tilt)
        hp = skia.Path()
        hp.moveTo(-R * 1.05, -R * 0.2)
        hp.cubicTo(-R * 1.35, R * 1.0, -R * 1.25, R * 2.0, -R * 0.9, R * 2.3)
        hp.lineTo(R * 0.9, R * 2.3)
        hp.cubicTo(R * 1.25, R * 2.0, R * 1.35, R * 1.0, R * 1.05, -R * 0.2)
        hp.close()
        cv.drawPath(hp, P(C("3a2116")))
        for k in range(-3, 4):
            w = skia.Path(); w.moveTo(k * R * 0.3, R * 0.6)
            w.cubicTo(k * R * 0.3 + 14, R * 1.2, k * R * 0.3 - 14, R * 1.7, k * R * 0.3 + 6, R * 2.2)
            cv.drawPath(w, P(C("5a3626"), stroke=4))
        cv.drawPath(hp, P(INK, stroke=5))
        cv.restore()
    _orig_head(cv, cfg, x, y, tilt, expr, look, amp, t, seed)
    cv.save(); cv.translate(x, y); cv.rotate(tilt)
    if cfg["hair"] == "long":
        cv.save(); oc = skia.Path(); oc.addOval(skia.Rect(-R, -R, R, R)); cv.clipPath(oc, skia.ClipOp.kIntersect, True)
        fr = skia.Path(); fr.moveTo(-R, -R * 0.15); fr.cubicTo(-R * 0.6, -R * 0.9, R * 0.2, -R * 0.75, R * 0.25, -R * 0.55)
        fr.cubicTo(R * 0.5, -R * 0.8, R * 0.9, -R * 0.6, R, -R * 0.2); fr.lineTo(R, -R * 1.2); fr.lineTo(-R, -R * 1.2); fr.close()
        cv.drawPath(fr, P(C("3a2116"))); cv.restore()
        cv.drawOval(skia.Rect(-R, -R, R, R), P(INK, stroke=6))
        cv.drawCircle(R * 0.55, -R * 0.75, 12, P(C("ffd23f")))
    if cfg["hair"] == "cap":
        cap = skia.Path(); cap.addArc(skia.Rect(-R * 1.02, -R * 1.08, R * 1.02, R * 0.6), 180, 180); cap.close()
        cv.save(); cl = skia.Path(); cl.addRect(skia.Rect(-R * 1.2, -R * 1.2, R * 1.2, -R * 0.42)); cv.clipPath(cl, skia.ClipOp.kIntersect, True)
        cv.drawOval(skia.Rect(-R * 1.03, -R * 1.08, R * 1.03, R * 0.9), P(C("1f6f5c")))
        cv.drawOval(skia.Rect(-R * 1.03, -R * 1.08, R * 1.03, R * 0.9), P(INK, stroke=5))
        cv.restore()
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-R * 0.2, -R * 0.55, R * 1.35, -R * 0.38), 10, 10), P(C("17594a")))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-R * 0.2, -R * 0.55, R * 1.35, -R * 0.38), 10, 10), P(INK, stroke=4))
    # headphones
    band = skia.Path(); band.addArc(skia.Rect(-R * 1.12, -R * 1.18, R * 1.12, R * 0.9), 195, 150)
    cv.drawPath(band, P(C("222222"), stroke=14, cap=skia.Paint.kButt_Cap))
    for sx in (-1, 1):
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(sx * R * 1.02 - 20, -R * 0.35, sx * R * 1.02 + 20, R * 0.35), 14, 14), P(C("2b2b2b")))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(sx * R * 1.02 - 20, -R * 0.35, sx * R * 1.02 + 20, R * 0.35), 14, 14), P(INK, stroke=4))
    cv.restore()

LR.draw_head = head_wrap

def amp_for(who, t):
    for s in SEGS:
        if s["who"] == who and s["s"] <= t < s["e"]:
            i = int((t - s["s"]) * FPS)
            if 0 <= i < len(s["env"]):
                return s["env"][i]
    return 0.0

def base_pose():
    return dict(L=(-80, -95), R=(80, -95), legs="stand", lean=0.0, flags=set(), drop=0.0)

def guy_pose(t):
    d = base_pose(); expr = "smug"; look = 1
    q_index = None
    for i, s in enumerate(SEGS):
        if s["who"] == "G" and s["s"] - 0.1 <= t:
            q_index = i
    n_q = sum(1 for s in SEGS[:q_index + 1] if s["who"] == "G") if q_index is not None else 0
    cur = SEGS[q_index]["text"] if q_index is not None else ""
    if t >= BEAT_T - 0.2 and t < SEGS[-2]["s"] - 0.1:
        # vibing then lost
        b = ((t - BEAT_T) / BEAT) % 2
        d["R"] = (60 + 60 * math.sin(math.pi * b), -260); d["L"] = (-80, -95); d["flags"].add("palms")
        expr = "confused" if t > BEAT_T + 2.6 else "smile"
        d["lean"] = 4 * math.sin((t - BEAT_T) / BEAT * math.pi)
        return d, expr, 1
    if t >= SEGS[-2]["s"] - 0.1:
        d["L"] = (-120, -230); d["R"] = (120, -230); d["flags"].add("palms")
        return d, "shock", 1
    if n_q <= 1:
        d["R"] = (120, -200); d["flags"].add("palms"); expr = "smug"
    elif n_q <= 3:
        d["R"] = (110, -190); d["flags"].add("palms"); expr = "smile" if n_q == 2 else "flat"
    elif n_q <= 6:
        d["L"] = (-70, -330); d["flags"].add("finger_L"); expr = "confused"
    elif n_q <= 8:
        d["R"] = (130, -210); d["flags"].add("palms"); expr = "confused"
    else:
        d["R"] = (150, -240); d["flags"].add("finger_R"); expr = "smug"
    return d, expr, 1

def sofia_pose(t):
    d = base_pose(); expr = "teach"; look = -1
    if t >= BEAT_T - 0.1:
        b = int((t - BEAT_T) / BEAT) % 2
        d["L"] = (-150, -380) if b == 0 else (-60, -260); d["R"] = (150, -300) if b == 0 else (70, -380)
        d["lean"] = 6 * math.sin((t - BEAT_T) / BEAT * math.pi); d["flags"] |= {"palms"}
        expr = "happy" if amp_for("S", t) < 0.06 else "teach"
        if t > SEGS[-1]["s"] - 0.2:
            d["L"] = (-130, -200); d["R"] = (130, -200); expr = "smile"
        return d, expr, 0
    d["L"] = (-150, -200); d["flags"].add("palms")
    return d, expr, -1

# ------------------------------------------------------------------ icons
def icon(cv, word, x, y, s, t):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    if word == "Potato":
        p = skia.Path(); p.addOval(skia.Rect(-110, -70, 110, 75))
        cv.drawPath(p, P(0, shader=rad(-30, -30, 160, [C("e0b070"), C("a8763a")]))); cv.drawPath(p, P(INK, stroke=6))
        for (a, b) in ((-50, -20), (20, 10), (60, -30), (-10, 40)):
            cv.drawCircle(a, b, 7, P(C("7a5226")))
    elif word == "Dad":
        cv.drawCircle(0, 0, 95, P(C("8a5534"))); cv.drawCircle(0, 0, 95, P(INK, stroke=6))
        cv.drawRect(skia.Rect(-95, -95, 95, -50), P(C("9a9a9a")))
        for sx in (-1, 1):
            cv.drawCircle(sx * 35, -10, 26, P(C("ffffff"))); cv.drawCircle(sx * 35, -10, 26, P(INK, stroke=5)); cv.drawCircle(sx * 35, -6, 9, P(INK))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-50, 30, 50, 52), 10, 10), P(C("3a2a20")))
        cv.drawPath(skia.Path().moveTo(-25, 68).quadTo(0, 78, 25, 68), P(INK, stroke=5))
    elif word == "Pope":
        m = poly([(-60, -10), (-55, -150), (0, -200), (55, -150), (60, -10)])
        cv.drawPath(m, P(C("ffffff"))); cv.drawPath(m, P(INK, stroke=6))
        cv.drawLine(0, -170, 0, -40, P(C("e0b030"), stroke=12)); cv.drawLine(-30, -120, 30, -120, P(C("e0b030"), stroke=12))
        cv.drawCircle(0, 60, 75, P(C("f0c8a0"))); cv.drawCircle(0, 60, 75, P(INK, stroke=6))
        cv.drawRect(skia.Rect(-62, -10, 62, 6), P(C("e0b030")))
        for sx in (-1, 1):
            cv.drawCircle(sx * 25, 55, 8, P(INK))
        cv.drawPath(skia.Path().moveTo(-20, 95).quadTo(0, 108, 20, 95), P(INK, stroke=5))
    elif word == "Llama":
        body = skia.Path(); body.addRRect(skia.RRect.MakeRectXY(skia.Rect(-40, -150, 20, 40), 28, 28))
        cv.drawOval(skia.Rect(-110, 0, 110, 110), P(C("f4ede0"))); cv.drawOval(skia.Rect(-110, 0, 110, 110), P(INK, stroke=6))
        cv.drawPath(body, P(C("f4ede0"))); cv.drawPath(body, P(INK, stroke=6))
        cv.drawOval(skia.Rect(-70, -200, 50, -120), P(C("f4ede0"))); cv.drawOval(skia.Rect(-70, -200, 50, -120), P(INK, stroke=6))
        for ex in (-40, 20):
            cv.drawOval(skia.Rect(ex - 10, -240, ex + 10, -190), P(C("f4ede0"))); cv.drawOval(skia.Rect(ex - 10, -240, ex + 10, -190), P(INK, stroke=5))
        cv.drawCircle(-35, -165, 8, P(INK)); cv.drawCircle(15, -165, 8, P(INK))
        cv.drawLine(-15, -135, -5, -132, P(INK, stroke=4))
        for lx in (-70, -30, 30, 70):
            cv.drawLine(lx, 100, lx, 150, P(INK, stroke=10))
    elif word == "Flame":
        fl = 1 + 0.06 * math.sin(t * 14)
        p = skia.Path(); p.moveTo(0, 110); p.cubicTo(-120, 90, -100, -40, -20, -140 * fl); p.cubicTo(-20, -60, 40, -60, 30, -170 * fl)
        p.cubicTo(110, -80, 120, 80, 0, 110)
        cv.drawPath(p, P(C("ff7a1a"))); cv.drawPath(p, P(INK, stroke=6))
        q = skia.Path(); q.moveTo(0, 95); q.cubicTo(-55, 80, -50, 0, 0, -60 * fl); q.cubicTo(50, 0, 55, 80, 0, 95)
        cv.drawPath(q, P(C("ffd23f")))
    elif word == "Calls":
        cv.save(); cv.rotate(10 * math.sin(t * 30))
        r = skia.RRect.MakeRectXY(skia.Rect(-60, -110, 60, 110), 20, 20)
        cv.drawRRect(r, P(C("2b2b35"))); cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-48, -92, 48, 88), 10, 10), P(C("5ad17a")))
        cv.drawCircle(0, -20, 26, P(C("ffffff"))); text(cv, "☎", 0, 0, 30, C("2b2b35"), tf=TF_B)
        cv.restore()
        for k in range(3):
            q = (t * 2 + k / 3) % 1
            for sx in (-1, 1):
                a = skia.Path(); a.addArc(skia.Rect(-90 - 50 * q, -90 - 50 * q, 90 + 50 * q, 90 + 50 * q), -40 if sx > 0 else 140, 80)
                cv.drawPath(a, P(C("5ad17a", 1 - q), stroke=7))
    elif word == "Wine":
        g = skia.Path(); g.moveTo(-70, -120); g.lineTo(70, -120); g.cubicTo(70, 0, 20, 20, 8, 30); g.lineTo(8, 110); g.lineTo(50, 120)
        g.lineTo(-50, 120); g.lineTo(-8, 110); g.lineTo(-8, 30); g.cubicTo(-20, 20, -70, 0, -70, -120); g.close()
        cv.drawPath(g, P(C("ffffff", 0.6)))
        wine = skia.Path(); wine.moveTo(-66, -60); wine.lineTo(66, -60); wine.cubicTo(62, 0, 20, 18, 0, 22); wine.cubicTo(-20, 18, -62, 0, -66, -60); wine.close()
        cv.drawPath(wine, P(C("8e1b3a")))
        cv.drawPath(g, P(INK, stroke=6))
    elif word == "Came":
        cv.drawRect(skia.Rect(-110, -150, 10, 130), P(C("8a5d3e"))); cv.drawRect(skia.Rect(-110, -150, 10, 130), P(INK, stroke=6))
        cv.drawCircle(-20, 0, 8, P(C("ffd23f")))
        wx = 40 + 20 * math.sin(t * 6)
        cv.drawCircle(wx, -100, 28, P(C("7a4a2c"))); cv.drawCircle(wx, -100, 28, P(INK, stroke=5))
        cv.drawLine(wx, -72, wx, 20, P(INK, stroke=8))
        ph = t * 8
        for k in (-1, 1):
            cv.drawLine(wx, 20, wx + 30 * math.sin(ph) * k, 110, P(INK, stroke=8))
            cv.drawLine(wx, -40, wx + 35 * math.sin(ph + 1) * k, 10, P(INK, stroke=8))
        for k in range(3):
            cv.drawLine(wx - 60 - k * 18, -60 + k * 30, wx - 90 - k * 18, -60 + k * 30, P(INK, stroke=5))
    cv.restore()

# ------------------------------------------------------------------ set
RNG = np.random.default_rng(3)

def draw_studio(cv, t, beat_amt):
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=lin(0, 0, 0, 1300, [C("2a1f1a"), C("3d2c24")])))
    for r in range(14):
        for c in range(10):
            x = c * 112 - (r % 2) * 56; y = 250 + r * 80
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x + 6, y + 6, x + 106, y + 74), 8, 8), P(C("251a15")))
            cv.drawLine(x + 10, y + 20, x + 102, y + 20, P(C("3a2a22"), stroke=4))
    for k in range(5):
        bx = 110 + k * 215
        fl = 0.85 + 0.15 * math.sin(t * 2 + k)
        if beat_amt > 0:
            fl = fl * (1 - beat_amt) + beat_amt * (0.6 + 0.6 * abs(math.sin(math.pi * (t - BEAT_T) / BEAT + k)))
        cv.drawCircle(bx, 200, 90 * fl, P(C("ffb347", 0.35), blur=40))
        cv.drawCircle(bx, 200, 16, P(C("fff1c4")))
    if beat_amt > 0:
        cols = ["ff4f9a", "4fc3ff", "ffd23f"]
        for k in range(3):
            a = math.sin(t * 1.3 + k * 2) * 0.45
            sx = 200 + k * 340
            cv.drawPath(poly([(sx, -20), (sx + math.sin(a - 0.12) * 1900, 1900), (sx + math.sin(a + 0.12) * 1900, 1900)]), P(C(cols[k], 0.14 * beat_amt)))

def draw_desk(cv):
    cv.drawRect(skia.Rect(0, 1400, W, H), P(0, shader=lin(0, 1400, 0, H, [C("6b4a36"), C("3a2a20")])))
    cv.drawRect(skia.Rect(0, 1388, W, 1412), P(C("8a6448")))
    for mx, dirx in ((395, 1), (685, -1)):
        arm = skia.Path(); arm.moveTo(mx + dirx * 90, 1390); arm.lineTo(mx + dirx * 60, 1290); arm.lineTo(mx, 1230)
        cv.drawPath(arm, P(C("222222"), stroke=10))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(mx - 34, 1110, mx + 34, 1250), 32, 32), P(C("2b2b2b")))
        for k in range(5):
            cv.drawLine(mx - 27, 1135 + k * 22, mx + 27, 1135 + k * 22, P(C("555555"), stroke=3))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(mx - 34, 1110, mx + 34, 1250), 32, 32), P(INK, stroke=4))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(440, 1340, 640, 1390), 10, 10), P(C("1a1a1a")))
    for k in range(5):
        cv.drawRect(skia.Rect(458 + k * 36, 1354, 478 + k * 36, 1362 + (k % 3) * 8), P(C("4fc3ff" if k % 2 else "ffd23f")))

def current_word(t):
    cur = None
    for s in SEGS:
        if s.get("word") and s["s"] - 0.05 <= t:
            cur = s
    return cur

SCENE_ITEMS = [("Dad", 250, 650, 0.5), ("Calls", 400, 560, 0.36), ("Llama", 560, 700, 0.5), ("Flame", 700, 720, 0.4),
               ("Pope", 850, 620, 0.46), ("Wine", 950, 740, 0.34), ("Potato", 130, 760, 0.36), ("Came", 990, 600, 0.0)]

def draw_world(cv, t):
    beat_amt = ss(BEAT_T - 0.05, BEAT_T + 0.2, t)
    draw_studio(cv, t, beat_amt)
    gp, ge, gl = guy_pose(t)
    sp, se, sl = sofia_pose(t)
    LR.draw_char(cv, "guy", 290, 1620, gp, ge, gl, amp_for("G", t), t, scale=1.6)
    LR.draw_char(cv, "sofia", 790, 1620, sp, se, sl, amp_for("S", t), t, scale=1.6)
    draw_desk(cv)
    # word card
    ws = current_word(t)
    if ws and t < BEAT_T - 0.4:
        en = ws["word"]; es = ws["text"].rstrip(".")
        a, k = pop(t, ws["s"] - 0.05, 0.4)
        nxt = [s for s in SEGS if s.get("word") and s["s"] > ws["s"]]
        end_t = (nxt[0]["s"] - 1.0) if nxt else BEAT_T - 0.4
        a *= 1 - ss(end_t + 0.6, end_t + 0.85, t) if nxt else 1 - ss(SEGS[-7]["s"], SEGS[-7]["s"] + 0.3, t)
        cv.save(); cv.translate(540, 640); cv.scale(k, k); cv.saveLayerAlpha(None, int(255 * a))
        r = skia.RRect.MakeRectXY(skia.Rect(-210, -230, 210, 190), 36, 36)
        cv.drawRRect(r, P(C("000000", 0.35), blur=14)); cv.drawRRect(r, P(C("fff8ec"))); cv.drawRRect(r, P(INK, stroke=6))
        text(cv, en.upper(), 0, -170, 40, C("8a7a6a"), tf=TF_XB)
        icon(cv, en, 0, 40, 0.72, t)
        cv.restore(); cv.restore()
        a2, k2 = pop(t, ws["s"], 0.35)
        cv.save(); cv.translate(540, 900); cv.scale(k2, k2); cv.saveLayerAlpha(None, int(255 * a * a2))
        text(cv, es.upper(), 0, 30, 110, C("ffd23f"), stroke=18, stroke_col=C("1a1a1a"))
        cv.restore(); cv.restore()
    # the combined scene during the sentence
    if t >= BEAT_T - 0.3:
        for i, (wd, x, y, s) in enumerate(SCENE_ITEMS):
            if s == 0:
                continue
            a, k = pop(t, BEAT_T + i * 0.35, 0.45)
            a *= 1 - ss(SEGS[-2]["s"] - 0.2, SEGS[-2]["s"] + 0.2, t)
            bob = 10 * math.sin(math.pi * (t - BEAT_T) / BEAT + i)
            cv.save(); cv.saveLayerAlpha(None, int(255 * a))
            icon(cv, wd, x, y - 120 + bob, s * k, t)
            cv.restore(); cv.restore()

def camera(t):
    if t >= SEGS[-2]["s"] - 0.1 and t < SEGS[-1]["s"] - 0.1:
        return 1.5, 365, 1100, 540, 900
    z = 1.0 + 0.04 * math.sin(t * 0.3)
    if t >= BEAT_T:
        z = 1.0 + 0.025 * abs(math.sin(math.pi * (t - BEAT_T) / BEAT))
    return z, 540, 1150, 540, 1150

# ------------------------------------------------------------------ overlays
TOP = ["When you ask a Spanish girl", "to teach you Spanish"]

def draw_top(cv):
    f = skia.Font(TF_B, 44)
    w = max(f.measureText(s) for s in TOP) + 60
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 140, 540 + w / 2, 280), 14, 14)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    for i, s in enumerate(TOP):
        text(cv, s, 540, 200 + i * 56, 44, C("111111"), tf=TF_B)

def build_caps():
    caps = []
    for s in SEGS:
        words = s["text"].replace("...", "…").split()
        chunks, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= 3 or w[-1] in ",.!?…":
                chunks.append(cur); cur = []
        if cur:
            chunks.append(cur)
        wts = [sum(len(w) + 1 for w in c) + (4 if c[-1][-1] in ",.!?…" else 0) for c in chunks]
        tot = sum(wts); acc = 0
        for c, wt in zip(chunks, wts):
            caps.append((s["s"] + (s["e"] - s["s"]) * acc / tot, s["s"] + (s["e"] - s["s"]) * (acc + wt) / tot, c, s["who"], s.get("sentence")))
            acc += wt
    return caps

CAPS = build_caps()
SENT_WORDS = "Papá llama a la llama, junto a la llama, y el Papa vino con vino y papa.".split()

def draw_caption(cv, t):
    if BEAT_T - 0.05 <= t < SEGS[-2]["s"] - 0.3:
        # full sentence karaoke
        spoken = 0
        for (a, b, words, who, sent) in CAPS:
            if sent is not None and a <= t:
                spoken += len(words) if t >= b else max(1, int(len(words) * (t - a) / max(0.01, b - a)) + 1)
        lines = [SENT_WORDS[0:5], SENT_WORDS[5:9], SENT_WORDS[9:13], SENT_WORDS[13:]]
        f = skia.Font(TF_BLACK, 70)
        idx = 0
        for li, ln in enumerate(lines):
            wtot = f.measureText(" ".join(ln)); x = 540 - wtot / 2; y = 1560 + li * 84
            for w in ln:
                on = idx < spoken
                col = C("ffd23f") if on else C("ffffff", 0.55)
                cv.drawString(w, x, y, f, P(C("000000"), stroke=14)); cv.drawString(w, x, y, f, P(col))
                x += f.measureText(w + " "); idx += 1
        return
    for (a, b, words, who, sent) in CAPS:
        if a <= t < b + 0.08 and sent is None:
            k = ease_out_back((t - a) / 0.2, 2.0)
            s = " ".join(words).upper()
            f = skia.Font(TF_BLACK, 76); w = f.measureText(s)
            if w > 960:
                f = skia.Font(TF_BLACK, 76 * 960 / w); w = f.measureText(s)
            cv.save(); cv.translate(540, 1700); cv.scale(k, k)
            col = C("ffd23f") if who == "S" else C("ffffff")
            cv.drawString(s, -w / 2, 26, f, P(C("000000"), stroke=15)); cv.drawString(s, -w / 2, 26, f, P(col))
            cv.restore()
            chip(cv, 540, 1600, "HER" if who == "S" else "HIM", a=0.95, col="ffd23f" if who == "S" else "ffffff", fg="1a1a1a", size=30)
            break

def render_frame(cv, t):
    z, wx, wy, sx, sy = camera(t)
    cv.save(); cv.translate(sx, sy); cv.scale(z, z); cv.translate(-wx, -wy)
    draw_world(cv, t)
    cv.restore()
    if BEAT_T <= t < BEAT_T + 0.12:
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("ffffff", 0.5 * (1 - (t - BEAT_T) / 0.12))))
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("000000", 0.4)], [0.6, 1])))
    draw_top(cv)
    if BEAT_T - 0.6 <= t < BEAT_T + 0.3 or False:
        pass
    if SEGS[-7]["s"] <= t < BEAT_T - 0.2:
        a, k = pop(t, SEGS[-7]["s"] + 1.6, 0.4)
        chip(cv, 540, 420, "Dad calls the llama next to the flame,", a=a, scale=k, col="ffffff", size=34)
        chip(cv, 540, 490, "and the Pope came with wine and potatoes.", a=a, scale=k, col="ffffff", size=34)
    if t >= END_CARD:
        a, k = pop(t, END_CARD, 0.45)
        chip(cv, 540, 430, "Now say it 3 times fast", a=a, scale=k, col="ffd23f", fg="1a1a1a", size=56)
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
        print("beat", BEAT_T, "total", TOTAL)
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
