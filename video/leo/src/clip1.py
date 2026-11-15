import json, math, sys
from common import *

FEET = (760.0, 1600.0)
SIT_HIP = (1401.0 - FEET[1]) / S_LEO      # bed front-top edge in local units
STAND_HIP = -210.0
DOWN_L, DOWN_R = (-14.0, 150.0), (14.0, 150.0)
RAISED_L = (-125.0, -82.0)
SLIGHT_L = (-138.0, 22.0)

def leo_pose(t):
    p = default_pose()
    # --- sitting + stretch + yawn (0-1.7)
    sit = 1.0 - ss(1.7, 2.45, t)
    p["sit"] = sit
    p["hip_y"] = lerp(STAND_HIP, SIT_HIP, sit)
    p["lean"] = 10 * math.sin(math.pi * ss(1.7, 2.45, t))
    up = ss(0.2, 0.65, t) * (1 - ss(1.25, 1.65, t))
    rest_L, rest_R = lerp2(DOWN_L, (-4.0, 118.0), sit), lerp2(DOWN_R, (4.0, 118.0), sit)
    p["handL"] = lerp2(rest_L, (-46.0, -140.0), up)
    p["handR"] = lerp2(rest_R, (46.0, -140.0), up)
    if t < 0.35:
        p["eyes"], p["mouth"] = "sleepy", "flat"
    elif t < 1.35:
        p["eyes"], p["mouth"] = "closed", "yawn"
    elif t < 1.7:
        p["eyes"], p["mouth"] = "sleepy", "flat"
    else:
        p["eyes"], p["mouth"] = "n", "smile"
    p["tilt"] = -6 * up
    # --- idle
    if t >= 2.45:
        p["bounce"] = 2.5 * abs(math.sin(t * 3.2))
    # --- raise right arm casually (3.0-5.0), lower (5.0-5.5)
    r = ss(3.0, 3.75, t) * (1 - ss(5.0, 5.5, t))
    p["handL"] = lerp2(p["handL"], RAISED_L, r)
    if 3.0 <= t < 5.0:
        p["look"] = lerp2((0, 0), (-0.6, -0.5), ss(3.0, 3.6, t))
        p["handL"] = (p["handL"][0] + 4 * math.sin(t * 4) * r, p["handL"][1])
    # --- notices shadow (5.5-7)
    if t >= 5.5:
        p["look"] = lerp2((0, 0), (-0.7, 0.85), ss(5.5, 5.8, t))
        p["mouth"] = "flat"
        p["bounce"] = 0
    if t >= 5.9:
        k = ss(5.9, 6.2, t)
        p["brows"] = (9 * k, -5 * k)
        p["mouth"] = "wobble"
        p["tilt"] = 3 * math.sin((t - 5.9) * 6) * (1 - ss(6.6, 7.0, t))
    # --- slow wave (7.0-8.4), lower + head tilt (8.4-8.8)
    w = ss(7.0, 7.45, t) * (1 - ss(8.35, 8.75, t))
    p["handL"] = lerp2(p["handL"], (-62.0, -112.0), w)
    if 7.4 <= t < 8.4:
        p["wave"] = (t - 7.4) * 7.5
    if t >= 8.35:
        p["tilt"] = 12 * ss(8.4, 8.8, t)
        p["brows"] = lerp2((9, -5), (14, -3), ss(8.4, 8.8, t))
    if t >= 8.85:
        p["eyes"] = "wide"; p["mouth"] = "o"
        p["brows"] = (16, -2)
        p["look"] = (-0.65, 0.9)
    return p

FROZEN = None

def shadow_pose(t):
    global FROZEN
    if t < 5.0:
        p = leo_pose(t)
        p["bounce"] = 0
        return p
    if FROZEN is None:
        FROZEN = leo_pose(4.9); FROZEN["bounce"] = 0; FROZEN["tilt"] = 0; FROZEN["look"] = (0, 0)
        FROZEN["handL"] = RAISED_L
    p = dict(FROZEN)
    k = ss(8.9, 9.15, t)
    p["handL"] = lerp2(RAISED_L, SLIGHT_L, k)
    return p

def camera(t):
    if t < 3.0:
        k = ss(0, 3.0, t)
        return (lerp(1.0, 1.08, k), lerp(540, 565, k), lerp(960, 1010, k))
    if t < 7.0:
        k = ss(3.0, 7.0, t)
        return (lerp(1.55, 1.6, k), lerp(545, 555, k), lerp(1295, 1300, k))
    if t < 9.5:
        return (1.3, 545, 1180)
    k = ss(9.5, 10.0, t)
    return (lerp(1.3, 1.42, k), 545, lerp(1180, 1240, k))

def frame(cv, t):
    cv.save(); apply_camera(cv, camera(t))
    draw_room(cv)
    draw_shadow(cv, shadow_pose(t), *FEET)
    contact_shadow(cv, *FEET)
    draw_dust(cv, t)
    draw_leo(cv, leo_pose(t), *FEET)
    cv.restore()

if __name__ == "__main__":
    if sys.argv[1:] and sys.argv[1] == "still":
        room_image()
        surf = skia.Surface(W, H)
        for ts in sys.argv[2:]:
            cv = surf.getCanvas(); cv.clear(C("000000")); frame(cv, float(ts))
            surf.makeImageSnapshot().save(f"{HERE}/s_{ts}.png", skia.kPNG)
    else:
        out = render_clip("clip01", frame, 10.0)
        end = dict(feet=FEET, leo=leo_pose(9.999), shadow=shadow_pose(9.999), camera=camera(9.999))
        json.dump(end, open(f"{HERE}/clip01_endstate.json", "w"), indent=1)
        print(out)
