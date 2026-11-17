"""16:9 compilation of the couple skits, re-rendered in widescreen from the original scene code."""
import importlib.util, json, math, os, subprocess, sys
import numpy as np
import skia
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "video"))
from render import C, ss, ease_out_back, P, lin, rad, poly, text, chip, TF_BLACK, TF_B

W, H, FPS = 1920, 1080, 30
INK = C("141414")

def load(name, folder):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, folder, "render.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

# ------------------------------------------------------------------ world-only drawing for each skit
def w_heart(m, cv, t):
    m.draw_room(cv, t); m.draw_couch_back(cv); m.draw_couch_front(cv)
    m.draw_person(cv, t, m.girl_state(t), m.GIRLX, "girl"); m.draw_person(cv, t, m.guy_state(t), m.GX, "guy")

def w_hell(m, cv, t):
    m.draw_room(cv, t); m.draw_couch_back(cv); m.draw_couch_front(cv)
    gx = m.GIRLX + (700 * m.ss(m.E(7) + 0.2, m.E(7) + 1.6, t) if t > m.E(7) + 0.2 else 0)
    m.draw_person(cv, t, m.girl_state(t), gx, "girl"); m.draw_person(cv, t, m.guy_state(t), m.GX, "guy")

def w_mia(m, cv, t):
    m.draw_room(cv, t); m.draw_couch_back(cv); m.draw_couch_front(cv)
    m.draw_person(cv, t, m.friend_state(t), m.FX, "friend"); m.draw_person(cv, t, m.dave_state(t), m.DX, "guy")
    gx = m.gf_x(t)
    if gx < 1500:
        m.draw_person(cv, t, m.gf_state(t), gx, "girl")
    fl = 0.08 + 0.05 * math.sin(t * 13) * math.sin(t * 5.3)
    cv.drawRect(skia.Rect(-1200, 900, 2300, 1920), P(C("5ab0ff", fl)))

def w_wifi(m, cv, t):
    night = t >= m.T_NIGHT
    m.draw_room(cv, t, night); m.M.draw_person(cv, t, m.guy_state(t), m.GX, "guy"); m.draw_desk(cv, t, night)
    gx = m.girl_x(t)
    if not night and gx < 1500:
        m.M.draw_person(cv, t, m.girl_state(t), gx, "girl")

def w_bday(m, cv, t):
    part = 0 if t < m.PART2 else 1
    m.draw_room(cv, t, part); m.table_items(cv, t, part)
    m.M.draw_person(cv, t, m.guy_state(t), m.GX, "guy"); m.M.draw_person(cv, t, m.girl_state(t), m.HX, "girl")
    times = m.item_times(part)
    for k, tk in enumerate(times):
        if tk <= t < tk + 0.9:
            q = ease_out_back((t - tk) / 0.25, 1.8)
            cx, kind = (m.GX, "guy") if part == 0 else (m.HX, "girl")
            hx, hy = m.hand_world(cx, kind, m.REL_UP)
            m.ITEMS[part][k](cv, hx, hy - 40, 1.0 * q)
    if (part == 0 and t < m.E(0) + 0.4) or (part == 1 and t < m.E(6) + 0.4):
        cx, kind = (m.HX, "girl") if part == 0 else (m.GX, "guy")
        hx, hy = m.hand_world(cx, kind, (-120, -40) if part == 0 else (60, -60))
        cv.save(); cv.translate(hx + (-40 if part == 0 else 40), hy + 90)
        p = poly([(-70, -100), (70, -100), (85, 60), (-85, 60)])
        cv.drawPath(p, P(C("9b59b6"))); cv.drawPath(p, P(INK, stroke=6))
        cv.drawArc(skia.Rect(-40, -150, 40, -60), 180, 180, False, P(INK, stroke=6))
        m.M.heart(cv, 0, -20, 0.9, "ffd23f")
        cv.restore()

def w_worm(m, cv, t):
    dark = m.ss(m.T_LAMP, m.T_LAMP + 0.08, t)
    m.draw_room(cv, t, dark); m.draw_headboard(cv)
    m.M.draw_person(cv, t, m.guy_state(t), m.GX, "guy"); m.M.draw_person(cv, t, m.girl_state(t), m.HX, "girl")
    m.draw_blanket(cv); m.draw_lamp(cv, dark < 0.5)
    if dark > 0:
        cv.drawRect(skia.Rect(-1200, -200, 2300, 2200), P(C("05060f", 0.86 * dark)))
        if t > m.T_LAMP + 0.5:
            m.glowing_eyes(cv, t)

def w_anniv(m, cv, t):
    m.CO.draw_room(cv, t); m.CO.draw_couch_back(cv); m.CO.draw_couch_front(cv)
    gs = m.guy_state(t)
    m.M.draw_person(cv, t, gs, m.GX, "guy"); m.scarf(cv, t, m.GX, gs.get("bob", 0))
    m.soul(cv, t, m.S(2) + 0.6); m.tears(cv, t, m.S(14) - 0.2)
    gx = m.girl_x(t)
    m.M.draw_person(cv, t, m.girl_state(t), gx, "girl")
    hip_g = m.M.SEAT - 18 - 200
    if t < m.T_JERSEY:
        m.gift_bag(cv, gx + 84 + 40, hip_g - 224 + 150 + 70, 0.9)
    else:
        q = ease_out_back((t - m.T_JERSEY) / 0.35, 1.8)
        if t < m.T_HIT:
            m.jersey(cv, gx - 40, 860, 1.0 * q)
        else:
            sw = m.ss(m.T_HIT, m.T_HIT + 0.3, t)
            m.jersey(cv, m.lerp(gx - 40, m.GX + 140, sw), m.lerp(860, 900, sw), 0.9, -60 * sw)
        m.gift_bag(cv, gx + 160, 1560, 0.8)
    m.thwack(cv, t)
    fl = 0.06 + 0.04 * math.sin(t * 11) * math.sin(t * 4.3)
    cv.drawRect(skia.Rect(-1200, 900, 2300, 1920), P(C("5ab0ff", fl)))

SKITS = [
    dict(folder="couch", title="Heart to Heart", fn=w_heart, wall="f3d9b8", floor="c99260"),
    dict(folder="hell", title="\"If I Go to Hell…\"", fn=w_hell, wall="f3d9b8", floor="c99260"),
    dict(folder="mia", title="The Loyalty Test", fn=w_mia, wall="f3d9b8", floor="c99260"),
    dict(folder="wifi", title="The Wi-Fi Password", fn=w_wifi, wall="e9dcc8", floor="c99260", night_wall="3a3f63", night_floor="3a3350"),
    dict(folder="bday", title="Boxers, Singlet & Belt", fn=w_bday, wall="f6e6d4", floor="c99260"),
    dict(folder="worm", title="\"Would You Still Love Me If…\"", fn=w_worm, wall="3b3a63", floor="3a3350"),
    dict(folder="anniv", title="The Forgotten Anniversary", fn=w_anniv, wall="f3d9b8", floor="c99260"),
]
CARD_COLS = ["ff6b8b", "ffb347", "5ab0ff", "5ad17a", "b07ae0", "3b3a63", "e74c3c"]

MODS = {}
def mod(i):
    if i not in MODS:
        MODS[i] = load(f"skit{i}", SKITS[i]["folder"])
    return MODS[i]

def skit_total(i):
    return json.load(open(os.path.join(ROOT, SKITS[i]["folder"], "vo.json")))["total"]

INTRO, CARD, OUTRO = 5.0, 2.4, 6.0
TIMELINE = [("intro", None, INTRO)]
for i in range(len(SKITS)):
    TIMELINE.append(("card", i, CARD))
    TIMELINE.append(("skit", i, round(skit_total(i) * FPS) / FPS))
TIMELINE.append(("outro", None, OUTRO))
TOTAL = sum(d for _, _, d in TIMELINE)

# ------------------------------------------------------------------ camera + world render
def land_cam(m, t):
    z, wx, wy = m.camera(t)
    zl = 1.05 + max(0.0, z - 1.0) * 0.62
    if z < 1.2:
        wy = 1190
    else:
        wy -= 45
    wy = min(wy, 1920 - H / 2 / zl)
    return zl, wx, wy

def extend_bg(cv, sk, night=False):
    wall, floor = (sk.get("night_wall"), sk.get("night_floor")) if night and sk.get("night_wall") else (sk["wall"], sk["floor"])
    cv.drawRect(skia.Rect(-1400, -200, 2500, 1420), P(C(wall)))
    for x in list(range(-1340, 0, 120)) + list(range(1100, 2500, 120)):
        cv.drawRect(skia.Rect(x, -200, x + 10, 1420), P(C("000000", 0.05)))
    cv.drawRect(skia.Rect(-1400, 1420, 2500, 2200), P(C(floor)))
    for i in range(10):
        cv.drawLine(-1400, 1460 + i * 64, 2500, 1460 + i * 64, P(C("000000", 0.08), stroke=4))

def draw_world(cv, i, t, cam=None):
    m = mod(i); sk = SKITS[i]
    z, wx, wy = cam or land_cam(m, t)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(z, z); cv.translate(-wx, -wy)
    night = i == 3 and t >= m.T_NIGHT
    extend_bg(cv, sk, night)
    sk["fn"](m, cv, t)
    cv.restore()

def captions(cv, i, t):
    m = mod(i)
    for c in m.CAPS:
        a, b, txt, who = c[:4]
        if a <= t < b + 0.12:
            k = ease_out_back((t - a) / 0.2, 2.0)
            s = txt.upper()
            f = skia.Font(TF_BLACK, 64); w = f.measureText(s)
            if w > 1600:
                f = skia.Font(TF_BLACK, 64 * 1600 / w); w = f.measureText(s)
            col = {"H": C("ffd23f"), "F": C("8fd8ff")}.get(who, C("ffffff"))
            cv.save(); cv.translate(W / 2, 1000); cv.scale(k, k)
            cv.drawString(s, -w / 2, 22, f, P(C("000000"), stroke=14)); cv.drawString(s, -w / 2, 22, f, P(col))
            cv.restore()
            name = {"H": "HER", "G": "HIM", "D": "DAVE", "F": "FRIEND"}.get(who, "HIM")
            chip(cv, W / 2, 920, name, a=0.95, col={"H": "ffd23f", "F": "8fd8ff"}.get(who, "ffffff"), fg="1a1a1a", size=26)
            return

def skit_overlays(cv, i, t):
    m = mod(i)
    if i == 3:  # wi-fi: red meltdown tint, phone inserts, LATER card
        if m.S(5) <= t < m.E(6):
            cv.drawRect(skia.Rect(0, 0, W, H), P(C("ff2a2a", 0.06 + 0.04 * math.sin(t * 12))))
        def phone(mode, tt):
            cv.save(); cv.translate(W / 2 - 540 * 0.6, H / 2 - 960 * 0.6); cv.scale(0.6, 0.6)
            m.phone_ui(cv, tt, mode, ease_out_back(tt / 0.3, 1.5)); cv.restore()
        if 1.9 <= t < m.S(1) - 0.1:
            phone("wait", t - 1.9)
        if m.E(7) + 0.2 <= t < m.S(8) - 0.1:
            phone("type", t - m.E(7) - 0.2)
        if m.T_LATER <= t < m.T_NIGHT:
            a = min(1, (t - m.T_LATER) / 0.15, (m.T_NIGHT - t) / 0.15)
            cv.drawRect(skia.Rect(0, 0, W, H), P(C("000000", a)))
            text(cv, "LATER…", W / 2, H / 2 + 40, 120, C("ffffff", a), tf=TF_BLACK)
    if i == 2 and m.E(5) + 0.15 <= t < m.S(6) + 0.2:  # loyalty: "Bestie calling" phone
        q = ease_out_back((t - m.E(5) - 0.15) / 0.3, 1.5)
        cv.save(); cv.translate(W / 2, H / 2); cv.scale(q * 0.55, q * 0.55)
        r = skia.RRect.MakeRectXY(skia.Rect(-210, -380, 210, 380), 48, 48)
        cv.drawRRect(r, P(C("2b2b38"))); cv.drawRRect(r, P(INK, stroke=8))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-186, -350, 186, 350), 30, 30), P(0, shader=lin(0, -350, 0, 350, [C("ff8fb3"), C("8f6bff")])))
        cv.drawCircle(0, -150, 90, P(C("ffffff"))); text(cv, "B", 0, -118, 90, C("ff6b8b"), tf=TF_BLACK)
        text(cv, "Bestie", 0, 0, 64, C("ffffff"), tf=TF_BLACK); text(cv, "calling…", 0, 60, 40, C("ffffff"), tf=TF_B)
        cv.drawCircle(0, 240, 52, P(C("5ad17a")))
        cv.restore()
    if i == 4 and m.CARD0 <= t < m.CARD1:  # birthday: 6 months later
        a = min(1, (t - m.CARD0) / 0.15, (m.CARD1 - t) / 0.15)
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("000000", a)))
        text(cv, "6 MONTHS LATER…", W / 2, H / 2 - 20, 80, C("ffffff", a), tf=TF_BLACK)
        text(cv, "HER BIRTHDAY", W / 2, H / 2 + 90, 90, C("ff6b8b", a), tf=TF_BLACK)

def card(cv, i, t):
    draw_world(cv, i, 0.5, cam=(1.05, 540, 1190))
    cv.drawRect(skia.Rect(0, 0, W, H), P(C(CARD_COLS[i], 0.82)))
    k = ease_out_back(t / 0.45, 1.8)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(k, k)
    text(cv, f"#{i + 1}", 0, -90, 170, C("ffffff"), stroke=16, stroke_col=INK)
    text(cv, SKITS[i]["title"], 0, 90, 96, C("ffffff"), stroke=14, stroke_col=INK)
    cv.restore()

def intro(cv, t):
    draw_world(cv, 0, 3.0 + t * 0.2, cam=(1.0 + 0.05 * t / INTRO, 540, 1190))
    cv.drawRect(skia.Rect(0, 0, W, H), P(C("1a0f2e", 0.72)))
    k = ease_out_back(t / 0.5, 1.6)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(k, k)
    text(cv, "COUPLE FIGHTS THAT", 0, -110, 120, C("ffffff"), stroke=16, stroke_col=INK)
    text(cv, "GOT OUT OF HAND", 0, 30, 140, C("ffd23f"), stroke=16, stroke_col=INK)
    cv.restore()
    a2 = ss(1.0, 1.4, t)
    chip(cv, W / 2, H / 2 + 180, "7 ANIMATED SKITS · WHO WAS RIGHT?", a=a2, col="ff6b8b", fg="ffffff", size=44)

def outro(cv, t):
    draw_world(cv, 6, 2.0, cam=(1.05, 540, 1190))
    cv.drawRect(skia.Rect(0, 0, W, H), P(C("1a0f2e", 0.75)))
    k = ease_out_back(t / 0.5, 1.6)
    cv.save(); cv.translate(W / 2, H / 2); cv.scale(k, k)
    text(cv, "WHICH ONE WAS YOUR FAVOURITE?", 0, -80, 86, C("ffffff"), stroke=14, stroke_col=INK)
    text(cv, "Comment the number below", 0, 20, 60, C("ffd23f"), stroke=10, stroke_col=INK)
    cv.restore()
    a2, k2 = ss(1.0, 1.3, t), ease_out_back((t - 1.0) / 0.4, 1.8) if t > 1.0 else 0
    cv.save(); cv.translate(W / 2, H / 2 + 190); cv.scale(max(0.01, k2), max(0.01, k2))
    r = skia.RRect.MakeRectXY(skia.Rect(-260, -60, 260, 60), 60, 60)
    cv.drawRRect(r, P(C("e62117", a2))); text(cv, "SUBSCRIBE", 0, 22, 62, C("ffffff", a2), tf=TF_BLACK)
    cv.restore()

def locate(t):
    acc = 0.0
    for kind, i, d in TIMELINE:
        if t < acc + d:
            return kind, i, t - acc
        acc += d
    kind, i, d = TIMELINE[-1]
    return kind, i, d - 1e-3

def render_frame(cv, t):
    kind, i, lt = locate(t)
    if kind == "intro":
        intro(cv, lt)
    elif kind == "outro":
        outro(cv, lt)
    elif kind == "card":
        card(cv, i, lt)
    else:
        draw_world(cv, i, lt)
        cv.drawRect(skia.Rect(0, 0, W, H), P(0, shader=rad(W / 2, H / 2, 1200, [C("000000", 0), C("000000", 0.28)], [0.6, 1])))
        skit_overlays(cv, i, lt)
        captions(cv, i, lt)
    if t < 0.3:
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("000000", 1 - t / 0.3)))
    if t > TOTAL - 0.6:
        cv.drawRect(skia.Rect(0, 0, W, H), P(C("000000", (t - (TOTAL - 0.6)) / 0.6)))

# ------------------------------------------------------------------ audio
def build_audio():
    SR = 24000
    rng = np.random.default_rng(2)
    parts = []
    def note(mn): return 440 * 2 ** ((mn - 69) / 12)
    for kind, i, d in TIMELINE:
        n = int(round(d * FPS) / FPS * SR)
        if kind == "skit":
            a, sr = sf.read(os.path.join(ROOT, SKITS[i]["folder"], "mix.wav"), dtype="float32")
            if a.ndim > 1:
                a = a.mean(1)
            a = np.pad(a, (0, max(0, n - len(a))))[:n]
        else:
            tt = np.arange(n) / SR
            a = np.zeros(n, np.float32)
            chord = [60, 64, 67, 72] if kind != "card" else [67, 71, 74]
            for j, mn in enumerate(chord):
                st = int(j * 0.08 * SR)
                L = n - st; t2 = np.arange(L) / SR
                a[st:] += (np.sin(2 * np.pi * note(mn) * t2) + 0.3 * np.sin(4 * np.pi * note(mn) * t2)) * np.exp(-t2 * (2.5 if kind != "card" else 4)) * 0.18
            w = rng.standard_normal(int(0.4 * SR)); w = np.convolve(w, np.ones(30) / 30, 'same')
            a[:len(w)] += (w / np.abs(w).max() * np.sin(np.linspace(0, np.pi, len(w))) ** 2 * 0.15).astype(np.float32)
            a[-int(0.15 * SR):] *= np.linspace(1, 0, int(0.15 * SR))
        parts.append(a.astype(np.float32))
    out = np.concatenate(parts); out /= max(1.0, np.abs(out).max() / 0.97)
    sf.write(os.path.join(HERE, "mix.wav"), out, SR)

def worker(args):
    k, f0, f1, out = args
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
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
            surf.makeImageSnapshot().save(os.path.join(HERE, f"st_{ts}.png"), skia.kPNG)
        print("total", TOTAL)
        acc = 0
        for kind, i, d in TIMELINE:
            print(kind, i, round(acc, 2)); acc += d
    elif sys.argv[1] == "audio":
        build_audio(); print("audio ok")
    else:
        from multiprocessing import Pool
        N = int(round(TOTAL * FPS)); nw = 4; step = N // nw
        jobs = [(k, k * step, N if k == nw - 1 else (k + 1) * step, os.path.join(HERE, f"part{k}.mp4")) for k in range(nw)]
        with Pool(nw) as p:
            outs = p.map(worker, jobs)
        with open(os.path.join(HERE, "parts.txt"), "w") as f:
            for o in outs:
                f.write(f"file '{o}'\n")
        print("frames", N)
