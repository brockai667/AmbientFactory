# -*- coding: utf-8 -*-
"""16:9 DLHY 'dokumentarny' money-glitch engine (8-15 min): intro -> kapitoly (schemy) -> outro.
Rovnaka vizualna rec ako shorts (papier, rucny font, ikony, velke farebne cisla, cerveny kruh,
draw-on, cha-ching, deadpan maskot) ale LANDSCAPE 1920x1080 + maskot ako stály 'host' vlavo dole +
kapitolove karty s cislom glitchu. Znovupouziva primitiva z glitch_engine (E.*).

  python glitch_long.py                 # vzorka: intro + 3 schemy + outro (~90s) na schvalenie
  python glitch_long.py id1 id2 id3 ... # vlastny vyber schem
"""
import os, sys, math, wave, subprocess
import numpy as np
from PIL import Image, ImageDraw
import glitch_engine as E
import schemes

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "demo_out"); os.makedirs(OUT, exist_ok=True)
LW, LH, FPS, SR = 1920, 1080, E.FPS, E.SR
clamp = lambda v, a=0.0, b=1.0: max(a, min(b, v))

# --- 16:9 papier + vinetacia + zrno + watermark (vpravo dole) ---
_ln = np.random.default_rng(7).normal(0, 4, (LH//4, LW//4, 1)).astype(np.int16)
LPAPER = Image.fromarray(np.clip(np.zeros((LH//4, LW//4, 3), np.int16) + np.array(E.PAPER, np.int16) + _ln, 0, 255).astype(np.uint8), "RGB").resize((LW, LH))
_yy, _xx = np.mgrid[0:LH, 0:LW]; _dd = np.sqrt(((_xx-LW/2)/(LW*0.64))**2 + ((_yy-LH/2)/(LH*0.64))**2)
_v = np.zeros((LH, LW, 4), np.uint8); _v[..., 3] = np.clip((_dd-0.6)*150, 0, 70).astype(np.uint8)
LVIGN = Image.fromarray(_v, "RGBA")
LGRAIN = [np.random.default_rng(300+k).normal(0, 4, (LH, LW, 3)).astype(np.int16) for k in range(6)]
LWM = Image.new("RGBA", (LW, 60), (0, 0, 0, 0)); ImageDraw.Draw(LWM).text((LW-46, 20), E.BRAND, font=E.FWM, fill=(150, 150, 150), anchor="rm")

# --- maskot host (znovupouziva E.char_expr) ---
def present(fr, level, blink, big=False, brow=0, smirk=0):
    tile = E.char_expr(level, blink, brow, smirk)
    sc, cx, cy = (0.95, 720, 560) if big else (0.5, 250, 880)
    t = tile.resize((max(1, int(560*sc)), max(1, int(820*sc))))
    fr.paste(t, (int(cx-t.width/2), int(cy-t.height/2)), t)

# --- landscape scena (icon/icons/two/equation/loop) ---
SX, SY = 1180, 470
def scene16(fr, d, st, tin, f):
    lay = st.get("layout", "icon"); r = clamp(tin/0.28)
    num = st.get("num"); ncol = E.COL.get(st.get("col", "green"), E.GREEN); sd = (sum(map(ord, str(num))) % 997)+1
    if lay == "icon":
        E.paste_wobble(fr, E.icon(st.get("icon", "coin"), 360), SX, SY if num else SY+90, f, rev=r)
        if num: E.draw_number(fr, d, (SX, SY+300), num, E.FNUM, ncol, tin, 0.30, sd)
    elif lay == "icons":
        for k, (dx, dy) in enumerate([(-270, -10), (-100, 60), (90, -30), (270, 60), (20, -150)]):
            E.paste_wobble(fr, E.icon(st.get("icon", "coin"), 180), SX+dx, SY+dy, f, phase=k*1.3, rev=min(1, (r*5-k)))
        if num: E.draw_number(fr, d, (SX, SY+330), num, E.FNUM, ncol, tin, 0.34, sd)
    elif lay == "two":
        E.paste_wobble(fr, E.icon(st.get("a", "dollar"), 290), SX-260, SY, f, rev=r)
        if r > 0.5: E.arrow(d, (SX-70, SY+3), (SX+70, SY+3))
        E.paste_wobble(fr, E.icon(st.get("b", "cash"), 290), SX+260, SY, f, phase=2.0, rev=r)
        if num: E.draw_number(fr, d, (SX, SY+300), num, E.FNUM, ncol, tin, 0.30, sd)
    elif lay == "equation":
        E.draw_number(fr, d, (SX, SY-110), st.get("eq", ""), E.FEQ, E.INK, tin, 0.12, 7)
        if num: E.draw_number(fr, d, (SX, SY+120), num, E.FNUM, ncol, tin, 0.42, sd)
    elif lay == "loop":
        cx, cy, R = SX, SY, 220; P = [(cx, cy-R), (cx+R, cy), (cx, cy+R), (cx-R, cy)]; ic = st.get("loop", ["dollar", "coin", "cash", "bag"])
        def edge(a, b, g=88):
            ax, ay = a; bx, by = b; dx, dy = bx-ax, by-ay; L = math.hypot(dx, dy) or 1; ux, uy = dx/L, dy/L
            E.arrow(d, (ax+ux*g, ay+uy*g), (bx-ux*g, by-uy*g))
        if r > 0.4:
            for i in range(4): edge(P[i-1], P[i]) if i > 0 else edge(P[3], P[0])
        szs = [150, 165, 140, 155]
        for i, nm in enumerate(ic[:4]): E.paste_wobble(fr, E.icon(nm, szs[i]), P[i][0], P[i][1], f, phase=i*1.6, rev=r)
        if num: E.draw_number(fr, d, (cx, cy+R+150), num, E.FNUM, ncol, tin, 0.34, sd)

# --- skript: intro + kapitoly + outro ---
def build_long(subset):
    intro = {"cap": "Money glitches that sound illegal", "vo": "Here are some money glitches that sound completely illegal, but somehow are technically legal.", "layout": "mascot", "big": 1, "brow": 1, "nochap": 1}
    outro = {"cap": "Which one are you trying first?", "vo": "So, which one of these are you actually trying first?", "layout": "mascot", "big": 1, "smirk": 1, "nochap": 1}
    steps = [intro]
    for i, sch in enumerate(subset, 1):
        steps.append({"cap": f"Glitch #{i}", "vo": f"Money glitch number {i}.", "layout": "chapter", "chap": f"GLITCH #{i}", "title": sch["title"]})
        for st in sch["steps"]:
            s = dict(st); s["chap"] = f"GLITCH #{i}"; steps.append(s)
    steps.append(outro)
    return steps

def render_long(steps, out_path, tmp):
    audio, starts, wav, total = E.build_audio(steps, tmp)
    sfx = np.zeros(len(audio), np.float32)                       # cha-ching len na zeleny payoff
    for i, st in enumerate(steps):
        if st.get("num") and st.get("col", "green") == "green":
            t0 = int((starts[i]+0.66)*SR)
            if 0 <= t0 < len(sfx): seg = E.CHA[:len(sfx)-t0]; sfx[t0:t0+len(seg)] += seg*0.5
    mix = np.clip(audio*0.9 + sfx, -1, 1).astype(np.float32)
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((mix*32767).astype("<i2").tobytes())
    n = int(total*FPS); env = E.lip_env(audio, n)
    chaps = []; cur = None                                        # dopln aktivnu kapitolu (forward-fill)
    for st in steps:
        cur = None if st.get("nochap") else (st.get("chap") or cur)
        chaps.append(cur)
    def step_at(tt):
        i = 0
        for k, s in enumerate(starts):
            if tt >= s: i = k
        return i
    blink = set(); fb = 25
    while fb < n:
        for k in range(4): blink.add(fb+k)
        fb += int(3.4*FPS)
    p = subprocess.Popen([E.FFMPEG, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{LW}x{LH}", "-r", str(FPS),
        "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-shortest", out_path], stdin=subprocess.PIPE)
    for f in range(n):
        tt = f/FPS; ci = step_at(tt); st = steps[ci]; tin = tt-starts[ci]; lay = st.get("layout", "icon")
        fr = LPAPER.copy(); d = ImageDraw.Draw(fr); bl = 1 if f in blink else 0; lv = int(round(env[f]*5))
        if lay == "mascot":                                      # intro/outro = velky host v strede
            present(fr, lv, bl, big=True, brow=st.get("brow", 0), smirk=st.get("smirk", 0))
        elif lay == "chapter":                                   # kapitolova karta: host + velke cislo + nazov
            present(fr, lv, bl)
            E.draw_number(fr, d, (1180, 360), st["chap"], E.F(150), E.INK, tin, 0.10, 3)
            E.draw_number(fr, d, (1180, 560), st.get("title", ""), E.F(56), E.INK, tin, 0.45, 5)
        else:                                                    # obsah: maly host vlavo dole + scena vpravo
            present(fr, lv, bl)
            scene16(fr, d, st, tin, f)
        E.pop(fr, (1010, 120), st["cap"], E.FCAP, E.INK, clamp(tin/0.25), maxw=1600)
        if chaps[ci]:                                            # stala kapitolova znacka vlavo hore
            d.text((46, 60), chaps[ci], font=E.F(46), fill=(150, 60, 52), anchor="lm")
        fr.paste(LVIGN, (0, 0), LVIGN); fr.paste(LWM, (0, LH-116), LWM)
        arr = np.clip(np.asarray(fr, np.int16) + LGRAIN[f % 6], 0, 255).astype(np.uint8)
        try:
            p.stdin.write(arr.tobytes())
        except (BrokenPipeError, OSError):
            break
    try:
        p.stdin.close()
    except (BrokenPipeError, OSError):
        pass
    p.wait(); return out_path

if __name__ == "__main__":
    ids = sys.argv[1:]
    if ids:
        subset = [s for s in schemes.SCHEMES if s["id"] in ids] or schemes.SCHEMES[:3]
    else:
        subset = [s for s in schemes.SCHEMES if s["id"] in ("manufactured-spending", "ewaste-gold", "vending-machines")] or schemes.SCHEMES[:3]
    steps = build_long(subset)
    print("kapitol:", len(subset), "| krokov spolu:", len(steps))
    out = os.path.join(OUT, "LONG_sample.mp4")
    render_long(steps, out, tmp=OUT)
    print("HOTOVO ->", out)
