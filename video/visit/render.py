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

W, H, FPS = 1080, 1920, 30
D = json.load(open(os.path.join(HERE, "vo.json")))
SEGS, TOTAL = D["segs"], D["total"]
INK = C("141414")

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
FLOOR = 1600
SLIP = (E(1) + 0.15, E(1) + 1.35)
RING = (E(2) + 0.1, S(3))
BELL1 = E(10) + 0.12
H0 = E(14) + 0.1                     # hide montage start
HIDE = [(H0, H0 + 0.85), (H0 + 0.85, H0 + 1.7), (H0 + 1.7, H0 + 2.55)]
DOOR = (H0 + 2.75, S(15))            # door opens
SCAN = (E(20) + 0.1, S(21))
PICK = (E(26) + 0.05, S(27))
REVEAL = (E(27) + 0.05, S(28))
FREEZE = (E(28) + 0.05, S(29))
SOFT = (E(33) + 0.05, S(34))
DANCE = (E(38) + 0.1, S(39) - 0.1)
STARE = (E(44) + 0.05, S(45))
BLACK = E(46) + 0.6
ANGRY = (11, 13, 15, 25, 27, 38, 39, 45)
STOOL = 780.0
DOORX = (30, 250)
GDOOR, HDOOR = 430.0, 170.0

def at(t):
    return FREEZE[0] if FREEZE[0] <= t < FREEZE[1] else t

def dance_phase(t):
    return (t - DANCE[0]) / (DANCE[1] - DANCE[0])

def guy_x(t):
    if t < H0:
        x = 560
        if S(0) <= t < SLIP[1]:
            x += 50 * math.sin((t - S(0)) * 3.0)
        return x
    if t < HIDE[0][1]:
        return STOOL - 150
    if t < HIDE[1][1]:
        return lerp(500, 760, ss(HIDE[1][0], HIDE[1][1] - 0.1, t))
    if t < DOOR[0]:
        return lerp(380, GDOOR, ss(HIDE[2][1], DOOR[0], t))
    if t < SCAN[0]:
        return lerp(GDOOR, 540, ss(S(17), S(17) + 0.8, t))
    if t < DANCE[0]:
        return lerp(540, 420, ss(SCAN[0], SCAN[1], t))
    if t < DANCE[1]:
        q = dance_phase(t)
        return 450 + 60 * math.sin(q * 14) * (q < 0.5)
    return 450

def girl_x(t):
    if t < DOOR[0] + 0.25:
        return None
    if t < SCAN[0]:
        return lerp(HDOOR, 200, ss(S(16), S(17), t))
    if t < PICK[1]:
        return lerp(200, 700, ss(SCAN[0], SCAN[1] + 0.6, t))
    return 700

def chair_x(t):
    return lerp(300, 905, ss(HIDE[1][0] + 0.1, HIDE[1][1] - 0.1, t))

def door_open(t):
    return ss(DOOR[0], DOOR[0] + 0.35, t)

REST_L, REST_R = (-30, 175), (30, 175)
UP_L, UP_R = (-120, -190), (120, -190)
HIPS_L, HIPS_R = (-18, 168), (18, 168)
CLASP_L, CLASP_R = (60, 60), (-60, 60)

def guy_state(t):
    st = dict(handL=REST_L, handR=REST_R, look=(1.0, 0.1), brows=(8, 8), mouth="smirk", grass="mouth", tilt=0, rise=1.0)
    st["blink"] = (t % 3.7) < 0.12
    def facing_girl():
        st["look"] = (1.0, 0.0)
    if t < H0:
        if t < SLIP[0]:   # following the tutorial
            w = math.sin(t * 6)
            st.update(handL=(-120, -60 + 40 * w), handR=(120, -60 - 40 * w), look=(1.0, 0.2), brows=(14, 14), mouth="flat")
            if S(1) <= t:
                st.update(mouth="smile", eyes="happy" if amp("G", t) < 0.05 else "n", tilt=6 * w)
        elif t < SLIP[1]:
            q = (t - SLIP[0]) / (SLIP[1] - SLIP[0])
            st.update(lean=-22 * math.sin(math.pi * q) * (1 if q < 0.6 else 0.5), bob=-40 * math.sin(math.pi * min(1, q * 1.4)),
                      handL=(-170, -150), handR=(170, -40), eyes="wide", mouth="o", brows=(22, 22), tilt=-12 * math.sin(math.pi * q))
        else:
            st.update(handL=HIPS_L, handR=HIPS_R, brows=(-10, 14), mouth="flat", look=(1.0, 0.3))
        if RING[0] <= t:
            st.update(look=(1.0, 0.4), brows=(14, 14), handL=REST_L, handR=REST_R)
        if S(3) <= t < E(9) + 0.2:
            st.update(handL=(70, -150), phone=True, handR=REST_R, look=(0.4, 0.0), mouth="smile", brows=(10, 10))
            if S(5) <= t < E(5) + 0.1:
                st.update(eyes="n", mouth="smirk", look=(0.6, 0.5))
            if S(9) <= t:
                st.update(eyes="wide", brows=(18, 18), mouth="flat")
        if E(9) + 0.2 <= t:
            st.update(look=(0.0, 0.0), brows=(16, 4), tilt=8, mouth="flat")
        if BELL1 <= t:
            st.update(eyes="wide", brows=(22, 22), mouth="o", look=(-1.0, 0.0), handL=UP_L, handR=UP_R, tilt=0)
        if S(12) <= t:
            st.update(handL=REST_L, handR=REST_R, mouth="flat", sweat=True)
        if S(13) <= t:
            st.update(handL=(-60, -220), handR=(60, -220), mouth="o", look=(0.0, 0.0))
        if S(14) <= t:
            w = math.sin(t * 14)
            st.update(handL=(-150, -80 + 40 * w), handR=(150, -80 - 40 * w), look=(1.0 if w > 0 else -1.0, 0.0))
        return st | {"amp": amp("G", t)}
    st["sweat"] = t < SOFT[0]
    if t < HIDE[0][1]:
        st.update(handR=(120, 180), handL=(100, 120), eyes="wide", brows=(20, 20), mouth="flat", lean=6)
    elif t < HIDE[1][1]:
        st.update(handL=(150, 40), handR=(160, 30), look=(1.0, 0.0), lean=8, eyes="wide", mouth="flat", walk=t * 12)
    elif t < SCAN[0]:
        st.update(book=True, handR=(60, -40), eyes="n", brows=(14, 14), mouth="smile", look=(-1.0, 0.0))
        if S(16) <= t:
            st.update(eyes="wide", brows=(18, 18), look=(-1.0, 0.0))
        if S(18) <= t:
            st.update(eyes="n", mouth="smile", brows=(16, 16))
        if S(20) <= t:
            st.update(handL=(-130, -50), brows=(14, 4), tilt=6)
    else:
        st.update(look=(1.0, 0.0), mouth="smile", brows=(16, 16), book=t < PICK[0], handR=(60, -40) if t < PICK[0] else REST_R)
        if SCAN[0] <= t < S(21):
            st.update(eyes="n", tilt=4 * math.sin(t * 5))
        if S(22) <= t < E(22) + 0.2:
            st.update(handL=(-140, -40), mouth="smile")
        if S(24) <= t < E(24) + 0.4:
            st.update(mouth="flat", brows=(4, 4), eyes="n", look=(1.0, 0.0))     # completely straight face
        if S(26) <= t < E(26) + 0.2:
            st.update(handL=(-130, -60), mouth="smirk", brows=(10, 4))
        if PICK[0] <= t < REVEAL[1]:
            st.update(handL=(150, -100), handR=(160, -60), eyes="wide", mouth="o", brows=(24, 24))
        if REVEAL[1] <= t < S(30):
            st.update(eyes="wide", mouth="flat", brows=(22, 22), handL=REST_L, handR=REST_R)
            if S(29) <= t:
                st.update(handL=(-120, -60), handR=(120, -60), eyes="n", brows=(18, 18))
        if S(31) <= t < SOFT[0]:
            st.update(look=(0.3, 0.6), brows=(14, 14), mouth="flat", handL=CLASP_L, handR=CLASP_R)
            if S(33) <= t:
                st.update(look=(1.0, 0.0), mouth="smile")
        if SOFT[0] <= t < DANCE[0]:
            st.update(eyes="n", mouth="smile", brows=(14, 14))
            if S(35) <= t < E(35) + 0.2:
                st.update(eyes="happy", brows=(18, 18))
            if S(37) <= t:
                st.update(eyes="wide", mouth="flat", brows=(20, 20), sweat=True)
        if DANCE[0] <= t < DANCE[1]:
            q = dance_phase(t)
            st.update(sweat=True, mouth="smile", brows=(16, 16))
            if q < 0.48:              # awful arm-wave routine
                w = math.sin(q * 30)
                st.update(handL=(-150, -120 + 70 * w), handR=(150, -120 - 70 * w), tilt=10 * w, walk=t * 8, eyes="happy")
            elif q < 0.66:            # the "spin"
                s_ = math.sin((q - 0.48) * 70)
                st.update(look=(s_, 0.0), handL=(-170, -60), handR=(170, -60), walk=t * 16, eyes="n")
            elif q < 0.78:            # steps on his own foot
                k = (q - 0.66) / 0.12
                st.update(lean=-14 * k, bob=-30 * math.sin(math.pi * k), handL=(-170, -160), handR=(170, -100), eyes="wide", mouth="o", brows=(24, 24))
            else:                     # falls onto the couch
                k = ss(0.78, 0.9, q)
                st.update(rise=1 - k, lean=-14 + 6 * k, tilt=18 * k, handL=(-160, -120 + 60 * k), handR=(160, -60), eyes="closed" if k > 0.95 else "wide", mouth="o")
        if DANCE[1] <= t:
            st.update(rise=0.0, lean=-8, tilt=14, handL=(-160, -60), handR=(130, 40), eyes="n", mouth="flat", brows=(10, 10))
            if S(40) <= t:
                st.update(tilt=4, lean=-4, look=(1.0, -0.2), eyes="wide")
            if S(42) <= t:
                st.update(eyes="n", mouth="flat", brows=(16, 16), handL=REST_L, handR=REST_R, tilt=0, lean=0)
            if S(44) <= t:
                st.update(look=(1.0, -0.2), mouth="smile", brows=(18, 18), tilt=6)    # sheepish
            if S(45) <= t:
                st.update(eyes="wide", mouth="o", brows=(24, 24), sweat=True, tilt=-6)
            if S(46) <= t:
                st.update(eyes="n", mouth="smile", brows=(18, 18), handL=(70, 40), handR=(-70, 40), tilt=8)
    st["amp"] = amp("G", t)
    return st

def girl_state(t):
    st = dict(handL=HIPS_L, handR=HIPS_R, look=(-1.0, 0.0), brows=(6, 6), mouth="smile", tilt=-4, rise=1.0)
    st["blink"] = (t % 4.1) < 0.12
    if t < S(17):
        st.update(handL=(-120, -190), handR=(120, -190), eyes="happy", brows=(14, 14), tilt=8)   # SURPRISE!
        if S(16) <= t:
            st.update(handL=CLASP_L, handR=CLASP_R, eyes="n", brows=(10, 10))
    elif t < SCAN[0]:
        st.update(brows=(-10, 8), mouth="flat")
        if S(19) <= t:
            st.update(brows=(4, 4), mouth="smile", tilt=6)
        if S(20) <= t:
            st.update(brows=(-10, 10), mouth="flat")
    elif t < PICK[0]:
        st.update(brows=(-14, 8), mouth="flat", tilt=0)
        if t < S(21):   # slowly scans the room
            st.update(look=(math.sin((t - SCAN[0]) * 3.4), -0.2), walk=t * 7)
        if S(23) <= t:
            st.update(look=(1.0, 0.2), handR=(130, 40), brows=(-12, 12))
        if S(24) <= t:
            st.update(look=(-1.0, 0.0), handR=HIPS_R)
        if S(25) <= t < E(25) + 0.3:
            st.update(handL=(-120, -190), handR=(120, -190), brows=(-20, 14), mouth="o")
        if S(26) <= t:
            st.update(brows=(-18, -18), mouth="flat")
    elif t < REVEAL[0]:
        st.update(look=(1.0, 0.3), handR=(90, 70), brows=(-18, -18), mouth="flat")
        if PICK[0] + 0.4 <= t:
            st.update(phone=True, handR=(-110, 40), look=(-0.6, 0.5))
    elif t < SOFT[0]:
        st.update(phone=True, handR=(-110, 40), look=(-0.6, 0.5), brows=(-16, 10), mouth="flat")
        if S(28) <= t:
            st.update(look=(-1.0, 0.0), brows=(-16, 12))
        if S(30) <= t:
            st.update(brows=(-6, 16), mouth="o")
        if S(32) <= t:
            st.update(brows=(-10, 10), mouth="flat")
    elif t < DANCE[0]:
        k = ss(SOFT[0], SOFT[1], t)
        st.update(phone=k < 0.5, handR=(-110, 40) if k < 0.5 else CLASP_R, handL=CLASP_L if k >= 0.5 else HIPS_L,
                  brows=(lerp(-10, 14, k), lerp(10, 14, k)), mouth="smile" if k > 0.4 else "flat", tilt=lerp(-4, 10, k))
        if S(34) <= t:
            st.update(eyes="happy" if amp("H", t) < 0.05 else "n")
        if S(36) <= t:
            st.update(handL=(-120, -150), handR=(120, -150), eyes="n", brows=(16, 16))
        if S(38) <= t:
            st.update(handL=(-120, -190 + 10 * math.sin(t * 20)), handR=(120, -190), brows=(18, 18))
    elif t < DANCE[1]:
        q = dance_phase(t)
        st.update(handL=CLASP_L, handR=CLASP_R, eyes="happy" if q < 0.3 else "n", brows=(14, 14) if q < 0.3 else (18, 18), mouth="smile" if q < 0.3 else "o", tilt=8 if q < 0.3 else 0)
        if q > 0.66:
            st.update(handL=(-60, -230), handR=(60, -230), eyes="wide")
    else:
        st.update(handL=HIPS_L, handR=HIPS_R, brows=(-6, 10), mouth="flat")
        if S(39) <= t < E(39) + 0.2:
            st.update(handL=(-120, -150), handR=(120, -150), brows=(10, 10), mouth="o")
        if S(41) <= t:
            st.update(brows=(4, 4), mouth="smile", tilt=8, handL=CLASP_L, handR=CLASP_R)
        if S(43) <= t:
            st.update(brows=(-8, 14), mouth="flat", tilt=-4, handL=HIPS_L, handR=HIPS_R)
        if E(44) <= t:
            st.update(eyes="n", brows=(-16, -16), mouth="flat", tilt=-6)
        if S(45) <= t:
            st.update(handL=(-120, -195 + 12 * math.sin(t * 22)), handR=(120, -195 + 12 * math.cos(t * 22)), brows=(-28, -28), tilt=-10)
        if E(45) + 0.3 <= t:
            st.update(handL=HIPS_L, handR=HIPS_R, brows=(-22, -22), eyes="n", mouth="flat")
    if t < S(23) and girl_x(t) is not None:
        gx0, gx1 = girl_x(t - 0.03), girl_x(t + 0.03)
        if gx0 is not None and abs(gx1 - gx0) > 2:
            st["walk"] = t * 9
    st["amp"] = amp("H", t)
    return st

def G_CU(t, z=1.85):
    us = guy_state(t); r = us["rise"]
    return (z, guy_x(t) + 30, 990 - 190 * r)
def H_CU(t, z=1.85):
    x = girl_x(t) or HDOOR
    return (z, x - 10, 805)
WIDE = (1.0, 560, 1130)
TWO = (1.2, 560, 1050)

def camera(t):
    if t < SLIP[0]:
        return WIDE if t < S(1) else (1.3, 600, 1060)
    if t < SLIP[1]:       # quick zoom when he nearly falls
        k = ss(SLIP[0], SLIP[0] + 0.15, t); return (lerp(1.3, 2.0, k), 600, lerp(1060, 860, k))
    if RING[0] <= t < S(3):
        return (1.4, 600, 1000)
    if BELL1 <= t < S(11):
        return G_CU(t, 2.2)
    if S(12) <= t < S(13):
        return (1.1, 300, 1080)                        # toward the door
    if S(13) <= t < E(13) + 0.2:
        return G_CU(t, 2.5)
    if HIDE[0][0] <= t < HIDE[0][1]:
        return (1.7, STOOL - 60, 1110)                 # scarf on phone
    if HIDE[1][0] <= t < HIDE[1][1]:
        return (1.15, 640, 1120)                       # chair shove
    if HIDE[2][0] <= t < HIDE[2][1]:
        return G_CU(t, 2.1)                            # grabs book
    if HIDE[2][1] <= t < S(16):
        return (1.4, 270, 1040)                        # door opens on her
    if SCAN[0] <= t < S(21):
        return (1.05, 560, 1110)
    if S(21) <= t < S(22):
        return H_CU(t)
    if S(24) <= t < E(24) + 0.5:
        return G_CU(t, 2.2)
    if PICK[0] <= t < REVEAL[0]:
        return (1.3, 680, 1060)
    if REVEAL[0] <= t < S(28):
        return H_CU(t, 2.0)
    if FREEZE[0] <= t < FREEZE[1]:
        k = ss(FREEZE[0], FREEZE[0] + 0.12, t); return G_CU(FREEZE[0], lerp(1.9, 2.3, k))
    if SOFT[0] <= t < S(34):
        k = (t - SOFT[0]) / (S(34) - SOFT[0]); return H_CU(t, lerp(1.7, 2.2, k))
    if DANCE[0] <= t < DANCE[1]:
        q = dance_phase(t)
        if q < 0.66: return (1.15, 560, 1080)
        if q < 0.78: return G_CU(t, 1.6)
        return (1.2, 520, 1080)
    if STARE[0] <= t < S(45):
        k = (t - STARE[0]) / (S(45) - STARE[0]); return H_CU(t, lerp(1.8, 2.3, k))
    shots = [(3, G_CU), (4, G_CU), (5, G_CU), (9, lambda t: G_CU(t, 2.0)), (10, G_CU), (11, lambda t: G_CU(t, 2.3)),
             (14, (1.1, 560, 1100)), (16, G_CU), (17, H_CU), (18, G_CU), (19, H_CU), (20, G_CU),
             (22, G_CU), (23, H_CU), (25, lambda t: H_CU(t, 2.2)), (26, G_CU), (27, (1.2, 620, 1040)),
             (29, G_CU), (30, H_CU), (31, G_CU), (32, H_CU), (33, G_CU), (34, H_CU), (35, G_CU), (36, H_CU), (37, G_CU),
             (38, lambda t: H_CU(t, 2.2)), (39, H_CU), (40, G_CU), (41, H_CU), (42, G_CU), (43, H_CU), (44, G_CU),
             (45, lambda t: H_CU(t, 2.5)), (46, G_CU)]
    cur = None
    for i, c in shots:
        if S(i) <= t:
            cur = (i, c)
    if cur is None:
        return WIDE
    i, c = cur
    c = c(t) if callable(c) else c
    nx = [S(j) for j, _ in shots if S(j) > S(i)]
    b = nx[0] if nx else TOTAL
    q = (t - S(i)) / max(0.1, b - S(i))
    return (c[0] * (1 + 0.05 * q), c[1], c[2])

def shake(t):
    for i, amt in ((11, 12), (13, 18), (25, 12), (27, 10), (38, 8), (45, 22)):
        if S(i) <= t < S(i) + 0.4:
            d = 1 - (t - S(i)) / 0.4
            return (amt * d * math.sin(t * 90), amt * d * math.cos(t * 77))
    if BELL1 <= t < BELL1 + 0.3:
        d = 1 - (t - BELL1) / 0.3; return (10 * d * math.sin(t * 90), 0)
    fall = DANCE[0] + 0.88 * (DANCE[1] - DANCE[0])
    if fall <= t < fall + 0.35:
        d = 1 - (t - fall) / 0.35; return (14 * d * math.sin(t * 90), 10 * d * math.cos(t * 70))
    return (0, 0)

HL = {0: {"LEFT": "y", "FOOT": "y"}, 1: {"EASY!": "b"}, 2: {"COMPLICATED": "y", "NONSENSE": "b"}, 3: {"BABY!": "y"},
      4: {"DOING?": "y"}, 5: {"NOTHING.": "b", "RELAXING.": "y"}, 6: {"MISS": "y"}, 8: {"LATER!": "b"}, 9: {"MEAN?": "y"},
      10: {"LATER?": "y", "MEAN?": "b"}, 11: {"WHO": "b"}, 12: {"OPEN": "y", "DOOR!": "b"}, 13: {"OH": "b", "NO!": "b"},
      14: {"DANCE": "y", "MOVES!": "y", "MUSIC!": "y", "EVERYTHING!": "b"}, 15: {"SURPRISE!": "b"}, 16: {"WONDERFUL": "y"},
      17: {"HAPPY": "y"}, 18: {"VERY": "b", "SURPRISED.": "y"}, 19: {"MISSED": "y"}, 20: {"EMOTIONALLY!": "b"},
      21: {"STRANGE?": "b"}, 22: {"NORMALLY": "y", "FURNITURE.": "y"}, 23: {"SCARF": "y", "PHONE?": "b"},
      24: {"COLD.": "b"}, 25: {"COLD?!": "b"}, 26: {"TECHNOLOGY": "y"}, 27: {"WAIT!": "b"}, 28: {"THIS?": "y"},
      29: {"EXPLAIN.": "b"}, 30: {"DANCE?": "y"}, 32: {"WHY?": "y"}, 33: {"ANNIVERSARY": "b", "ROMANTIC": "y", "DANCE.": "y"},
      34: {"SWEET!": "y"}, 35: {"REALLY?": "y"}, 36: {"SHOW": "y"}, 37: {"NOW?": "y"}, 38: {"NOW!": "b"}, 39: {"BABE!": "b"},
      41: {"DINNER": "y"}, 42: {"HIDING.": "y"}, 44: {"BURNT": "b", "FOOD.": "b"}, 45: {"BURNT": "b", "FOOD": "b", "TOO?!": "b"},
      46: {"NEXT": "y", "YEAR?": "b"}}
def chunks():
    out = []
    for s in SEGS:
        words = s["text"].replace('"', "").split()
        cs, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= 3 or w[-1] in ",.?!…:—":
                cs.append(cur); cur = []
        if cur:
            cs.append(cur)
        wt = [sum(len(w) + 2 for w in c) for c in cs]; tot = sum(wt); acc = 0
        for c, x in zip(cs, wt):
            out.append((s["start"] + (s["end"] - s["start"]) * acc / tot, s["start"] + (s["end"] - s["start"]) * (acc + x) / tot, c, s["who"], s["i"]))
            acc += x
    return out
CAPS = chunks()
CAP_Y = 1460

def draw_caption(cv, t):
    for n, (a, b, words, who, i) in enumerate(CAPS):
        nxt = CAPS[n + 1][0] if n + 1 < len(CAPS) else b + 0.4
        if a <= t < min(b + 0.35, nxt):
            k = ease_out_back(min(1, (t - a) / 0.16), 2.2)
            ws = [w.upper() for w in words]
            size = 96
            f = skia.Font(TF_BLACK, size); gap = 26
            wid = lambda: sum(f.measureText(w) for w in ws) + gap * (len(ws) - 1)
            if wid() > 960:
                size *= 960 / wid(); f = skia.Font(TF_BLACK, size); gap *= size / 96
            tw = wid()
            jx = 6 * math.sin(t * 50) if i in ANGRY else 0
            cv.save(); cv.translate(540 + jx, CAP_Y); cv.scale(k, k)
            x = -tw / 2
            for w in ws:
                st = HL.get(i, {}).get(w)
                ww = f.measureText(w)
                if st == "b":
                    r = skia.RRect.MakeRectXY(skia.Rect(x - 12, -size * 0.78, x + ww + 12, size * 0.2), 14, 14)
                    cv.drawRRect(r, P(C("000000"), stroke=12)); cv.drawRRect(r, P(C("e8262a")))
                    cv.drawString(w, x, 0, f, P(C("ffffff")))
                else:
                    cv.drawString(w, x, 0, f, P(C("000000"), stroke=18))
                    cv.drawString(w, x, 0, f, P(C("ffd21f") if st == "y" else C("ffffff")))
                x += ww + gap
            cv.restore()
            if who in ("G", "H", "T"):
                chip(cv, 540, CAP_Y - 128, {"H": "HER", "G": "HIM", "T": "TUTORIAL"}[who], a=0.95, col="ffd23f" if who == "H" else "ffffff", fg="1a1a1a", size=30)
            return

# ---------------------------------------------------------------- pop-up graphics
def xmark(cv, x, y, s, a=1.0):
    for d in (1, -1):
        cv.drawLine(x - s, y - s * d, x + s, y + s * d, P(C("ffffff", a), stroke=s * 0.62))
        cv.drawLine(x - s, y - s * d, x + s, y + s * d, P(C("e8262a", a), stroke=s * 0.42))

def tag(cv, t, t0, t1, label, y, col="ffd23f", fg="141414", size=56):
    if t0 <= t < t1:
        a, k = pop(t, t0, 0.35)
        a = min(a, (t1 - t) / 0.15)
        chip(cv, 540, y, label, a=a, scale=k, col=col, fg=fg, size=size)




def draw_door(cv, t):
    k = door_open(t)
    x0, x1, y0, y1 = DOORX[0], DOORX[1], 620, 1420
    cv.drawRect(skia.Rect(x0 - 16, y0 - 16, x1 + 16, y1), P(C("8a5a3a"))); cv.drawRect(skia.Rect(x0 - 16, y0 - 16, x1 + 16, y1), P(INK, stroke=7))
    cv.drawRect(skia.Rect(x0, y0, x1, y1), P(0, shader=lin(0, y0, 0, y1, [C("3b2a6b"), C("e0708a"), C("6aa36a")], [0, 0.6, 0.62])))
    w = (x1 - x0) * (1 - 0.82 * k)
    cv.drawRect(skia.Rect(x0, y0, x0 + w, y1), P(C("b9774a"))); cv.drawRect(skia.Rect(x0, y0, x0 + w, y1), P(INK, stroke=6))
    if w > 80:
        cv.drawRect(skia.Rect(x0 + 24, y0 + 30, x0 + w - 24, y0 + 330), P(C("a8683f"))); cv.drawRect(skia.Rect(x0 + 24, y0 + 30, x0 + w - 24, y0 + 330), P(INK, stroke=4))
        cv.drawRect(skia.Rect(x0 + 24, y0 + 380, x0 + w - 24, y1 - 40), P(C("a8683f"))); cv.drawRect(skia.Rect(x0 + 24, y0 + 380, x0 + w - 24, y1 - 40), P(INK, stroke=4))
        cv.drawCircle(x0 + w - 30, 1040, 13, P(C("e8c34a"))); cv.drawCircle(x0 + w - 30, 1040, 13, P(INK, stroke=4))
    # doormat
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(20, 1600, 280, 1640), 10, 10), P(C("7a4b3a")))

def draw_mirror(cv, t):
    cv.drawLine(950, 1500, 910, 1600, P(INK, stroke=10)); cv.drawLine(1010, 1500, 1050, 1600, P(INK, stroke=10))
    o = skia.Rect(890, 860, 1070, 1520)
    cv.drawOval(o, P(C("c9a26a"))); cv.drawOval(o, P(INK, stroke=7))
    g = skia.Rect(910, 880, 1050, 1500)
    cv.drawOval(g, P(0, shader=lin(910, 880, 1050, 1500, [C("dff3ff"), C("a9d4ee")])))
    cv.drawLine(940, 980, 990, 930, P(C("ffffff", 0.8), stroke=10)); cv.drawLine(945, 1040, 1015, 970, P(C("ffffff", 0.6), stroke=6))

def draw_chair(cv, cx):
    wood, dk = C("b9773f"), C("8a5426")
    cv.drawRect(skia.Rect(cx + 50, 1130, cx + 74, 1420), P(wood)); cv.drawRect(skia.Rect(cx + 50, 1130, cx + 74, 1420), P(INK, stroke=5))
    for y in (1180, 1260):
        cv.drawRect(skia.Rect(cx - 60, y, cx + 70, y + 22), P(wood)); cv.drawRect(skia.Rect(cx - 60, y, cx + 70, y + 22), P(INK, stroke=4))
    cv.drawRect(skia.Rect(cx - 80, 1400, cx + 80, 1430), P(dk)); cv.drawRect(skia.Rect(cx - 80, 1400, cx + 80, 1430), P(INK, stroke=5))
    for x in (cx - 70, cx + 60):
        cv.drawRect(skia.Rect(x, 1430, x + 14, 1600), P(wood)); cv.drawRect(skia.Rect(x, 1430, x + 14, 1600), P(INK, stroke=4))

def draw_stool(cv, t):
    x = STOOL
    cv.drawRect(skia.Rect(x - 80, 1340, x + 80, 1370), P(C("6b4a8a"))); cv.drawRect(skia.Rect(x - 80, 1340, x + 80, 1370), P(INK, stroke=5))
    for dx in (-66, 52):
        cv.drawRect(skia.Rect(x + dx, 1370, x + dx + 14, 1600), P(C("6b4a8a"))); cv.drawRect(skia.Rect(x + dx, 1370, x + dx + 14, 1600), P(INK, stroke=4))
    in_hand = (S(3) <= t < E(9) + 0.2) or t >= PICK[0] + 0.4
    scarf = HIDE[0][0] + 0.35 <= t
    if not in_hand:
        vib = 4 * math.sin(t * 80) if RING[0] <= t < S(3) else 0
        cv.save(); cv.translate(x + vib, 1340); cv.rotate(-12)
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-30, -110, 30, 0), 10, 10), P(C("2b2b38")))
        playing = t < S(12)
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-24, -104, 24, -6), 6, 6), P(C("ffd6e6" if playing else "9aa3b5")))
        if playing:
            cv.drawCircle(0, -78, 7, P(INK, stroke=3)); cv.drawLine(0, -71, 0, -45, P(INK, stroke=3))
            sw = 10 * math.sin(t * 8)
            cv.drawLine(0, -62, -12, -60 + sw, P(INK, stroke=3)); cv.drawLine(0, -62, 12, -60 - sw, P(INK, stroke=3))
            cv.drawLine(0, -45, -8, -26, P(INK, stroke=3)); cv.drawLine(0, -45, 8, -26, P(INK, stroke=3))
        else:
            cv.drawRect(skia.Rect(-10, -66, -3, -44), P(C("ffffff"))); cv.drawRect(skia.Rect(3, -66, 10, -44), P(C("ffffff")))
        cv.restore()
        if RING[0] <= t < S(3):
            for j in range(3):
                r = 50 + 30 * (((t * 2.5) + j / 3) % 1)
                cv.drawArc(skia.Rect(x - r, 1280 - r, x + r, 1280 + r), -60, 120, False, P(C("3ccf5a", 0.8), stroke=6))
    if scarf:
        k = min(1, (t - HIDE[0][0] - 0.35) / 0.15)
        top = 1225 if not in_hand else 1335
        sp = poly([(x - 70, 1345), (x - 50, top + (1 - k) * -200), (x + 40, top - 10 + (1 - k) * -200), (x + 75, 1345), (x + 60, 1395), (x - 60, 1395)])
        cv.drawPath(sp, P(C("e8424a"))); cv.drawPath(sp, P(INK, stroke=5))
        for j in range(3):
            cv.drawLine(x - 40 + j * 35, 1390, x - 44 + j * 35, 1410, P(C("e8424a"), stroke=6))

def draw_book(cv, gx, st):
    hip = M.SEAT - 18 - 200 * st["rise"] - st.get("bob", 0)
    hx, hy = gx + 94 + st["handR"][0], hip - 224 + st["handR"][1]
    cv.save(); cv.translate(hx, hy - 40); cv.rotate(-8)
    cv.drawRect(skia.Rect(-60, -80, 60, 80), P(C("2f6fb8"))); cv.drawRect(skia.Rect(-60, -80, 60, 80), P(INK, stroke=6))
    cv.drawRect(skia.Rect(-60, -80, -46, 80), P(C("1f4f88")))
    text(cv, "BOOK", 6, 10, 30, C("ffffff"), tf=TF_BLACK)
    cv.restore()
    cv.drawCircle(hx, hy, 16, P(C("ffffff"))); cv.drawCircle(hx, hy, 16, P(INK, stroke=5))

def draw_smoke(cv, t):
    if t < S(44) + 0.4:
        return
    a0 = min(1, (t - S(44) - 0.4) / 1.5)
    for j in range(14):
        q = ((t - S(44)) * 0.18 + j / 14) % 1
        x = 1130 - 520 * q + 40 * math.sin(j * 2.1 + t)
        y = 1050 - 650 * q + 30 * math.cos(j * 1.7 + t * 0.8)
        r = 50 + 120 * q
        cv.drawCircle(x, y, r, P(C("6e6e78", 0.32 * a0 * (1 - q)), blur=18))

def draw_reveal_phone(cv, t):
    a0, a1 = REVEAL[0], REVEAL[1] + 1.2
    if not (a0 <= t < a1):
        return
    k = ease_out_back(min(1, (t - a0) / 0.3), 1.8); a = min(1, (a1 - t) / 0.2)
    cv.save(); cv.translate(540, 800); cv.rotate(-4); cv.scale(k * 1.15, k * 1.15)
    body = skia.RRect.MakeRectXY(skia.Rect(-220, -380, 220, 380), 44, 44)
    cv.drawRRect(body, P(C("000000", 0.35 * a), blur=24)); cv.drawRRect(body, P(C("1d1d26", a)))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-196, -350, 196, 350), 26, 26), P(C("141418", a)))
    vid = skia.Rect(-196, -300, 196, -40)
    cv.drawRect(vid, P(C("ffc2d6", a)))
    for dx, s_ in ((-60, 1), (60, -1)):
        bx = dx + 10 * math.sin(t * 6) * s_
        cv.drawCircle(bx, -210, 26, P(C("ffffff", a))); cv.drawCircle(bx, -210, 26, P(INK, stroke=5))
        cv.drawLine(bx, -184, bx, -110, P(INK, stroke=6))
        cv.drawLine(bx, -160, bx + 40 * s_, -175 + 10 * math.sin(t * 6), P(INK, stroke=6))
        cv.drawLine(bx, -110, bx - 20, -60, P(INK, stroke=6)); cv.drawLine(bx, -110, bx + 20, -60, P(INK, stroke=6))
    M.heart(cv, 0, -250, 0.9)
    cv.drawRect(skia.Rect(-196, -46, -196 + 392 * min(1, 0.3 + (t - a0) * 0.1), -40), P(C("e8262a", a)))
    for j, ln in enumerate(("HOW TO DANCE", "ROMANTICALLY FOR", "YOUR GIRLFRIEND")):
        text(cv, ln, -176, 20 + j * 52, 40, C("ffffff", a), tf=TF_BLACK, align="l")
    chip(cv, -50, 210, "BEGINNER CLASS", a=a, col="e8262a", fg="ffffff", size=34)
    text(cv, "Dance Tutorials • 3.2M views", -176, 290, 24, C("9aa0ad", a), tf=TF_B, align="l")
    cv.restore()

def bubble(cv, t, t0, t1, label, x, y, col="ffffff", fg="141414", size=70, rot=-6):
    if t0 <= t < t1:
        a, k = pop(t, t0, 0.3); a = min(a, (t1 - t) / 0.15)
        cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(k, k)
        chip(cv, 0, 0, label, a=a, col=col, fg=fg, size=size)
        cv.restore()

TOP = ["When she plans a SURPRISE visit…", "HE WAS NOT READY"]

def draw_top(cv, t):
    f = skia.Font(TF_B, 44)
    w = max(f.measureText(TOP[0]), skia.Font(TF_BLACK, 48).measureText(TOP[1])) + 70
    r = skia.RRect.MakeRectXY(skia.Rect(540 - w / 2, 150, 540 + w / 2, 286), 16, 16)
    cv.drawRRect(r, P(C("000000", 0.3), blur=10)); cv.drawRRect(r, P(C("ffffff")))
    text(cv, TOP[0], 540, 208, 44, C("111111"), tf=TF_B)
    text(cv, TOP[1], 540, 264, 48, C("e74c3c"), tf=TF_BLACK)

def render_frame(cv, t):
    ta = at(t)
    z, wx, wy = camera(t)
    sx, sy = shake(t)
    wy = min(wy, H - H / 2 / z); wx = min(max(wx, W / 2 / z), W - W / 2 / z)
    cv.save(); cv.translate(W / 2 + sx, H / 2 + sy); cv.scale(z, z); cv.translate(-wx, -wy)
    CO.draw_room(cv, ta); CO.draw_couch_back(cv); CO.draw_couch_front(cv)
    draw_door(cv, ta); draw_mirror(cv, ta); draw_chair(cv, chair_x(ta)); draw_stool(cv, ta)
    gx = girl_x(ta)
    if gx is not None:
        M.draw_person(cv, ta, girl_state(ta), gx, "girl")
    us = guy_state(ta); ux = guy_x(ta)
    M.draw_person(cv, ta, us, ux, "guy")
    if us.get("book"):
        draw_book(cv, ux, us)
    fall = DANCE[0] + 0.9 * (DANCE[1] - DANCE[0])
    if fall <= ta < fall + 0.5:
        a = 1 - (ta - fall) / 0.5
        for j in range(5):
            an = j * 1.25 + ta * 6
            cv.drawCircle(ux + 120 * math.cos(an), 900 + 40 * math.sin(an), 14, P(C("ffd21f", a)))
    draw_smoke(cv, ta)
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(540, 960, 1300, [C("000000", 0), C("1a1010", 0.35)], [0.6, 1])))
    if FREEZE[0] <= t < FREEZE[1]:
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("7a7f8c", 0.4)))
        bubble(cv, t, FREEZE[0], FREEZE[1], "CAUGHT", 540, 760, col="e8262a", fg="ffffff", size=90)
    draw_top(cv, t)
    tag(cv, t, 0.3, S(1), "SECRET DANCE PRACTICE", 470, col="ffd23f", size=56)
    tag(cv, t, SLIP[0], E(2), "DANCE SKILL: 3%", 470, col="e8262a", fg="ffffff", size=58)
    tag(cv, t, RING[0], S(4), "BABY IS CALLING", 470, col="3ccf5a", fg="141414", size=58)
    bubble(cv, t, BELL1, S(11) + 0.6, "DING DONG!", 540, 560, col="ffd23f", size=84)
    tag(cv, t, S(13), H0, "PANIC MODE", 470, col="e8262a", fg="ffffff", size=64)
    for j, lab in enumerate(("1. HIDE THE PHONE", "2. BLOCK THE MIRROR", "3. ACT NORMAL")):
        tag(cv, t, HIDE[j][0], HIDE[j][1] + (0.6 if j == 2 else 0), lab, 470, col="ffffff", size=56)
    tag(cv, t, S(33) + 0.8, SOFT[1], "ANNIVERSARY: NEXT WEEK", 470, col="ff7aa8", fg="141414", size=54)
    if DANCE[0] <= t < DANCE[1]:
        tag(cv, t, DANCE[0] + 0.2, DANCE[0] + 0.5 * (DANCE[1] - DANCE[0]), "ROMANTIC DANCE", 470, col="ff7aa8", fg="141414", size=60)
        tag(cv, t, DANCE[0] + 0.5 * (DANCE[1] - DANCE[0]), DANCE[1], "DANCE SKILL: STILL 3%", 470, col="e8262a", fg="ffffff", size=56)
    draw_reveal_phone(cv, t)
    if not (FREEZE[0] <= t < FREEZE[1]):
        draw_caption(cv, t)
    if t >= BLACK:
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("000000")))

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
