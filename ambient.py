#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AmbientFactory engine -- parametricke ambientne long-form video pre rozne niky
(focus / study / yoga / sleep / meditation). Vsetko PROGRAMOVO: zvuk (pady + pentatonicky
zvoncek + sum + fade) + hypnoticky vizual (flow-field). 0 copyrightu, ziadne Suno.
1920x1080 landscape (long-form YouTube). Skaluje na 1-3h cez ffmpeg -stream_loop.

Pouzitie:
  python ambient.py <niche> [sekundy] [seed]     # napr. python ambient.py focus 30
  python ambient.py demos                          # kratke demo kazdej niky
  python ambient.py list
"""
import os, sys, wave, shutil, subprocess
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "output"); os.makedirs(OUT, exist_ok=True)
TMP = os.path.join(ROOT, "temp"); os.makedirs(TMP, exist_ok=True)

# mood -> akordove pomery (vzdy konsonantne); scale -> pentatonika pre zvoncek (vzdy lubozvucne)
MOODS = {
    "add9":  [(1.0, .22), (1.5, .18), (2.0, .18), (3.0, .13), (4.0, .10), (2.25, .07)],   # jasne, povzbudzujuce
    "minor": [(1.0, .24), (1.2, .16), (1.5, .18), (2.0, .16), (3.0, .10), (2.4, .08)],    # hlboke, emotivne
    "sus":   [(1.0, .24), (1.333, .18), (1.5, .16), (2.0, .16), (2.667, .10), (2.25, .07)],  # neutralne, meditativne
}
SCALES = {
    "min_pent": np.array([1.0, 1.2, 1.3333, 1.5, 1.8, 2.0, 2.4]),     # mol pentatonika (+oktava)
    "maj_pent": np.array([1.0, 1.125, 1.25, 1.5, 1.6667, 2.0, 2.25]),  # dur pentatonika
}
NICHES = {
    "focus": {"brand": "LUMORA", "sub": "deep focus", "key": 196.0, "mood": "add9", "brown": .05, "air": .05,
              "shimmer": .05, "lfo": 1.0, "bells": {"scale": "maj_pent", "dens": .24, "decay": 2.2, "vol": .16},
              "palette": "cool", "speed": 1.0, "n": 6500, "decay": .94, "bloom": 6.0},
    "study": {"brand": "LULL", "sub": "study tones", "key": 174.6, "mood": "add9", "brown": .06, "air": .04,
              "shimmer": .04, "lfo": .9, "bells": {"scale": "maj_pent", "dens": .32, "decay": 2.6, "vol": .20},
              "palette": "warm", "speed": .85, "n": 6000, "decay": .945, "bloom": 6.5},
    "yoga":  {"brand": "LULL", "sub": "yoga & flow", "key": 164.8, "mood": "sus", "brown": .07, "air": .035,
              "shimmer": .045, "lfo": .8, "bells": {"scale": "min_pent", "dens": .22, "decay": 3.0, "vol": .17},
              "palette": "green", "speed": .8, "n": 6200, "decay": .95, "bloom": 6.5},
    "sleep": {"brand": "LULL", "sub": "deep sleep", "key": 146.8, "mood": "minor", "brown": .09, "air": .02,
              "shimmer": .02, "lfo": .6, "bells": None,
              "palette": "dark", "speed": .6, "n": 5200, "decay": .955, "bloom": 7.0},
    "medit": {"brand": "LULL", "sub": "meditation", "key": 196.0, "mood": "sus", "brown": .05, "air": .03,
              "shimmer": .05, "lfo": .7, "bells": {"scale": "min_pent", "dens": .18, "decay": 3.4, "vol": .20},
              "palette": "violet", "speed": .7, "n": 6000, "decay": .95, "bloom": 7.0},
}

# ----------------------------- AUDIO ---------------------------------------

def _brown(n, rng):
    b = np.cumsum(rng.standard_normal(n)); b -= np.linspace(b[0], b[-1], n)
    return b / (np.max(np.abs(b)) + 1e-9)


def _air(n, rng):
    w = rng.standard_normal(n); w -= np.convolve(w, np.ones(48) / 48, mode="same")
    return w / (np.max(np.abs(w)) + 1e-9)


def _pads(t, key, mood, phase, lfo_mul):
    sig = np.zeros_like(t)
    for i, (r, a) in enumerate(MOODS[mood]):
        f = key * r
        lfo = 0.55 + 0.45 * np.sin(2 * np.pi * t / ((15.0 + 5 * i) / lfo_mul) + phase + i * 0.7)
        v = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.003 * t + 0.3)
        sig += a * lfo * v
    return sig


def _bells(t, key, spec, seed, sr):
    """sparse pentatonicke tony (sinus + 2.harmonicka, rychly attack + exp doznievanie).
    Pentatonika => lubozvucne aj pri nahodnom vybere not. Stereo cez nahodny pan."""
    n = len(t)
    if not spec:
        return np.zeros(n), np.zeros(n)
    rng = np.random.default_rng(seed + 999)
    dur = n / sr
    scale = SCALES[spec["scale"]]
    L = np.zeros(n); R = np.zeros(n)
    for _ in range(max(1, int(dur * spec["dens"]))):
        on = rng.uniform(0, max(0.1, dur - spec["decay"])); i0 = int(on * sr)
        f = key * 2 * float(rng.choice(scale))                  # oktava nad padmi -> jasny tonik
        dec = spec["decay"] * rng.uniform(.7, 1.2)
        ln = int(dec * sr); st = np.arange(ln) / sr
        env = np.exp(-st / (dec * 0.35)) * (1 - np.exp(-st / 0.01))   # rychly attack, exp decay
        tone = (np.sin(2 * np.pi * f * st) + 0.3 * np.sin(2 * np.pi * 2 * f * st)) * env * spec["vol"]
        pan = rng.uniform(0.2, 0.8); i1 = min(n, i0 + ln); m = i1 - i0
        L[i0:i1] += tone[:m] * (1 - pan); R[i0:i1] += tone[:m] * pan
    return L, R


def ambient_audio(niche, seconds, sr=48000, seed=7, fin=4.0, fout=6.0):
    p = NICHES[niche]; rng = np.random.default_rng(seed)
    n = int(seconds * sr); t = np.arange(n) / sr; key = p["key"]
    shimmer = p["shimmer"] * np.sin(2 * np.pi * key * 6 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * t / 9.0))
    nlL = 0.6 + 0.4 * np.sin(2 * np.pi * t / 13.0 * p["lfo"])
    nlR = 0.6 + 0.4 * np.sin(2 * np.pi * t / 13.0 * p["lfo"] + 1.7)
    bL, bR = _bells(t, key, p["bells"], seed, sr)
    L = _pads(t, key, p["mood"], 0.0, p["lfo"]) + shimmer + _brown(n, rng) * p["brown"] * nlL + _air(n, rng) * p["air"] + bL
    R = _pads(t, key, p["mood"], 1.1, p["lfo"]) + shimmer + _brown(n, rng) * p["brown"] * nlR + _air(n, rng) * p["air"] + bR
    a = np.stack([L, R], 1); a /= (np.max(np.abs(a)) + 1e-9)
    a = np.tanh(a * 1.6) / np.tanh(1.6); a *= 0.92
    fi, fo = int(fin * sr), int(fout * sr); env = np.ones(n)
    env[:fi] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fi))
    env[n - fo:] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, fo))
    return a * env[:, None]


def write_wav(path, a, sr=48000):
    pcm = (np.clip(a, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())

# ----------------------------- VISUAL --------------------------------------

PALETTES = {  # (nizka farba, vysoka farba) -> lerp podla per-castica odtienu
    "cool":   (np.array([.10, .30, .78]), np.array([.30, .75, .95])),
    "warm":   (np.array([.85, .45, .20]), np.array([.95, .75, .40])),
    "green":  (np.array([.12, .55, .40]), np.array([.45, .85, .55])),
    "violet": (np.array([.45, .20, .70]), np.array([.78, .45, .95])),
    "dark":   (np.array([.10, .20, .45]), np.array([.20, .35, .60])),
}


def _tonemap(canvas, bloom):
    img = 1.0 - np.exp(-np.clip(canvas, 0, None))
    u8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    im = Image.fromarray(u8, "RGB")
    small = im.resize((im.width // 2, im.height // 2), Image.BILINEAR)
    glow = small.filter(ImageFilter.GaussianBlur(radius=bloom / 2)).resize(im.size, Image.BILINEAR)
    A = np.asarray(im, np.float32); B = np.asarray(glow, np.float32)
    return np.clip(255 - (255 - A) * (255 - B) / 255.0, 0, 255).astype(np.uint8)


def flow_field(niche, W, H, fps, duration, seed=7):
    p = NICHES[niche]; rng = np.random.default_rng(seed)
    n = p["n"]; pos = np.stack([rng.uniform(0, W, n), rng.uniform(0, H, n)], 1).astype(np.float64)
    lo, hi = PALETTES[p["palette"]]; tc = rng.uniform(0, 1, n)[:, None]
    col = np.clip(lo[None, :] * (1 - tc) + hi[None, :] * tc, 0.04, 1.0) * (0.35 if p["palette"] == "dark" else 0.5)
    canvas = np.zeros((H, W, 3), np.float64); nf = int(fps * duration)
    sc = 0.0013; speed = min(W, H) * 0.0013 * p["speed"]; decay = p["decay"]
    for f in range(nf):
        canvas *= decay; tt = f / fps; x = pos[:, 0]; y = pos[:, 1]
        ang = (np.sin(x * sc + 0.5 * np.sin(tt * 0.05)) + np.cos(y * sc * 1.3 - tt * 0.06)
               + 0.6 * np.sin((x + y) * sc * 0.7 + tt * 0.04)) * np.pi
        pos[:, 0] = (x + np.cos(ang) * speed) % W; pos[:, 1] = (y + np.sin(ang) * speed) % H
        xi = pos[:, 0].astype(np.int32); yi = pos[:, 1].astype(np.int32)
        np.add.at(canvas, (yi, xi), col * 0.55)
        yield _tonemap(canvas, p["bloom"])


def _font(sz):
    for q in (r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):   # Linux runner (CI)
        try:
            return ImageFont.truetype(q, sz)
        except Exception:
            pass
    return ImageFont.load_default()


def thumbnail(frame_u8, brand, sub, accent, path):
    im = Image.fromarray(frame_u8, "RGB").resize((1280, 720), Image.LANCZOS)
    d = ImageDraw.Draw(im); bw, sw = _font(150), _font(52)
    tw = d.textlength(brand, font=bw); d.text(((1280 - tw) / 2, 250), brand, font=bw, fill=(245, 247, 255))
    tw2 = d.textlength(sub, font=sw); d.text(((1280 - tw2) / 2, 430), sub, font=sw, fill=accent)
    im.save(path, "JPEG", quality=90)

# ----------------------------- FFMPEG / RENDER -----------------------------

def _ffmpeg():
    try:
        import static_ffmpeg; static_ffmpeg.add_paths()
    except Exception:
        pass
    return shutil.which("ffmpeg") or "ffmpeg"


FF = _ffmpeg()


def render(niche, seconds, seed=7, tag=None):
    if niche not in NICHES:
        raise SystemExit(f"neznama nika '{niche}'. dostupne: {', '.join(NICHES)}")
    p = NICHES[niche]; W, H, fps = 1920, 1080, 30
    name = tag or niche
    print(f"[{niche}] 1/3 zvuk ({seconds:.0f}s)...")
    wav = os.path.join(TMP, f"{name}.wav"); write_wav(wav, ambient_audio(niche, seconds, seed=seed))
    print(f"[{niche}] 2/3 vizual {W}x{H}@{fps}...")
    silent = os.path.join(TMP, f"{name}_silent.mp4")
    cmd = [FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-maxrate", "6M", "-bufsize", "12M", "-pix_fmt", "yuv420p", "-movflags", "+faststart", silent]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE); last = None; nf = int(fps * seconds)
    for i, fr in enumerate(flow_field(niche, W, H, fps, seconds, seed=seed)):
        pr.stdin.write(fr.tobytes()); last = fr
        if i % 60 == 0:
            print(f"    {niche} frame {i}/{nf}")
    pr.stdin.close()
    if pr.wait() != 0:
        raise SystemExit(f"[{niche}] render zlyhal")
    print(f"[{niche}] 3/3 mux (loudnorm) + thumbnail...")
    out = os.path.join(OUT, f"{name}.mp4")
    r = subprocess.run([FF, "-y", "-i", silent, "-i", wav, "-c:v", "copy", "-map", "0:v", "-map", "1:a",
                        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                        "-shortest", out])
    if r.returncode != 0:
        os.replace(silent, out)
    accent = tuple((PALETTES[p["palette"]][1] * 255).astype(int).tolist())
    thumbnail(last, p["brand"], p["sub"], accent, os.path.join(OUT, f"{name}.jpg"))
    print(f"[{niche}] HOTOVO -> {out}")
    return out


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        print("niky:", ", ".join(NICHES)); return
    if sys.argv[1] == "demos":
        for nm in ("focus", "study", "yoga", "sleep"):
            render(nm, 18, seed=7, tag="demo_" + nm)
        return
    niche = sys.argv[1]
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    render(niche, secs, seed=seed)


if __name__ == "__main__":
    main()
