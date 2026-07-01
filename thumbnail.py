# -*- coding: utf-8 -*-
"""Lumora thumbnail + scene generator.
Consistent "world" per brand (aurora sky + layered mountain silhouettes + glowing Lumora moon).
`build_scene()` = the pure animated-able background (no text) — reused by visual.py for the video.
`make()` = 1280x720 thumbnail (scene + big mood headline + sub + duration pill + LUMORA wordmark).
Per-niche palette + rotating mood words (seeded)."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(ROOT, "fonts")

NICHES = {
    "focus": {
        "sky": ((6, 13, 26), (9, 42, 55)),
        "aurora": [(46, 214, 200), (66, 150, 225)],
        "moon": (215, 246, 255),
        "accent": (64, 224, 214),
        "words": ["DEEP FOCUS", "LOCKED IN", "FLOW STATE", "PURE FOCUS", "DEEP WORK"],
        "subs": ["FOCUS MUSIC", "CONCENTRATION", "DEEP WORK BEATS", "PRODUCTIVITY FLOW"],
    },
    "study": {
        "sky": ((11, 8, 27), (54, 27, 62)),
        "aurora": [(232, 120, 200), (242, 182, 96)],
        "moon": (255, 226, 172),
        "accent": (243, 176, 120),
        "words": ["STUDY FLOW", "STUDY SESSION", "LATE NIGHT STUDY", "EXAM MODE", "STUDY WITH ME"],
        "subs": ["STUDY MUSIC", "CONCENTRATION", "LOFI STUDY BEATS", "READING & REVISION"],
    },
    "sleep": {
        "sky": ((4, 5, 15), (21, 27, 60)),
        "aurora": [(126, 124, 244), (92, 162, 222)],
        "moon": (212, 227, 255),
        "accent": (152, 152, 242),
        "words": ["DEEP SLEEP", "FALL ASLEEP", "SLEEP INSTANTLY", "DREAM DEEP", "NIGHT RAIN"],
        "subs": ["SLEEP MUSIC", "RELAXING AMBIENT", "FALL ASLEEP FAST", "RAIN & PIANO"],
    },
}
NICHES["yoga"] = NICHES["focus"]


def _font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def _layer(rgb, alpha):
    """rgb: (3,) or HxWx3 float; alpha: HxW float 0..1 -> RGBA PIL image."""
    h, w = alpha.shape
    if np.ndim(rgb) == 1:
        rgb = np.ones((h, w, 3), np.float32) * np.array(rgb, np.float32)
    arr = np.dstack([np.clip(rgb, 0, 255), np.clip(alpha, 0, 1) * 255]).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def _ridge(width, amp, rough, rng, base):
    """Midpoint-displacement ridgeline -> array of y (len=width)."""
    k = 7
    n = 2 ** k + 1
    h = np.zeros(n, np.float32)
    h[0] = rng.uniform(-amp, amp)
    h[-1] = rng.uniform(-amp, amp)
    step, a = n - 1, amp
    while step > 1:
        half = step // 2
        for i in range(half, n - 1, step):
            h[i] = (h[i - half] + h[i + half]) / 2 + rng.uniform(-a, a)
        step, a = half, a * rough
    x = np.linspace(0, n - 1, width)
    xi = x.astype(int)
    xf = x - xi
    xi2 = np.clip(xi + 1, 0, n - 1)
    return base + h[xi] * (1 - xf) + h[xi2] * xf


def _orb(W, H, cx, cy, R, color, halo=2.4):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot(xx - cx, yy - cy)
    glow = np.exp(-(r / (R * halo)) ** 2) * 0.9
    body = np.clip((R - r) / max(R * 0.14, 1) + 1, 0, 1)
    a = np.maximum(body, glow)
    rgb = np.ones((H, W, 3), np.float32) * np.array(color, np.float32)
    rgb += (np.exp(-(r / (R * 0.7)) ** 2) * 25)[..., None]
    return _layer(rgb, a)


def build_scene(niche, seed, W, H):
    """The pure Lumora world (NO text) — aurora sky + stars + glowing moon + mountain
    silhouettes + haze + vignette. 16:9. Reused by the thumbnail AND the long-form video."""
    cfg = NICHES.get(niche, NICHES["focus"])
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    # sky gradient + horizon glow
    top = np.array(cfg["sky"][0], np.float32)
    bot = np.array(cfg["sky"][1], np.float32)
    t = (yy / H)[..., None]
    sky = top[None, None] * (1 - t) + bot[None, None] * t
    horizon = np.exp(-((yy - H * 0.72) / (H * 0.28)) ** 2) * 0.35
    sky += horizon[..., None] * np.array(cfg["aurora"][1], np.float32) * 0.5
    base = Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

    # aurora bands
    for i, col in enumerate(cfg["aurora"]):
        yc = H * (0.28 + 0.14 * i) + rng.uniform(-20, 20)
        amp = rng.uniform(30, 60) * (H / 720)
        thick = rng.uniform(40, 70) * (H / 720)
        freq = rng.uniform(1.2, 2.2)
        phase = rng.uniform(0, 6.28)
        line = yc + amp * np.sin(xx / W * np.pi * freq + phase)
        a = np.exp(-((yy - line) / thick) ** 2) * 0.5
        base.alpha_composite(_layer(np.array(col, np.float32), a).filter(ImageFilter.GaussianBlur(8)))

    # stars
    stars = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stars)
    for _ in range(int(150 * (W * H) / (1280 * 720))):
        sx_, sy_ = rng.uniform(0, W), rng.uniform(0, H * 0.62)
        rad = rng.uniform(0.5, 1.8) * (H / 720)
        al = int(rng.uniform(30, 160))
        sd.ellipse([sx_ - rad, sy_ - rad, sx_ + rad, sy_ + rad], fill=(230, 240, 255, al))
    base.alpha_composite(stars.filter(ImageFilter.GaussianBlur(0.5)))

    # moon (glowing Lumora light), rule-of-thirds upper-right
    mR = 60 * (H / 720)
    base.alpha_composite(_orb(W, H, W * 0.70, H * 0.30, mR, cfg["moon"]))

    # mountain silhouettes (3 layers, atmospheric perspective + moon rim light)
    layers = [(H * 0.60, 70, 0.62, 0.28), (H * 0.72, 95, 0.58, 0.15), (H * 0.86, 120, 0.55, 0.0)]
    fog = np.array(cfg["aurora"][1], np.float32)
    for base_y, amp, rough, fogmix in layers:
        heights = _ridge(W, amp * (H / 720), rough, rng, base_y)
        mask = (yy >= heights[None, :]).astype(np.float32)
        col = np.array([7, 9, 16], np.float32) * (1 - fogmix) + fog * fogmix * 0.5
        mtn = _layer(np.ones((H, W, 3), np.float32) * col, mask * (0.90 + 0.1 * fogmix))
        edge = np.clip(mask - np.roll(mask, int(3 * H / 720), axis=0), 0, 1)
        edge[:4] = 0
        side = np.clip((xx - (W * 0.35)) / (W * 0.5), 0, 1)
        rim = _layer(np.array(cfg["moon"], np.float32), edge * side * 0.5).filter(ImageFilter.GaussianBlur(1.5))
        base.alpha_composite(mtn)
        base.alpha_composite(rim)

    # foreground haze + vignette
    haze = np.exp(-((H - yy) / (H * 0.22)) ** 2) * 0.22
    base.alpha_composite(_layer(fog, haze))
    vig = ((np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))) ** 2 * 0.55)
    base.alpha_composite(_layer(np.array([0, 0, 0], np.float32), np.clip(vig, 0, 0.7)))
    return base


def _draw_text(base, xy, text, font, fill, anchor="la",
               glow=None, glow_r=14, shadow=(0, 0, 0), sx=4, sy=6):
    """Text with drop shadow + optional colored glow (pop/contrast)."""
    W, H = base.size
    if glow is not None:
        gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(gl).text(xy, text, font=font, fill=glow + (255,), anchor=anchor)
        gl = gl.filter(ImageFilter.GaussianBlur(glow_r))
        base.alpha_composite(gl)
        base.alpha_composite(gl)
    if shadow is not None:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((xy[0] + sx, xy[1] + sy), text, font=font,
                                fill=shadow + (200,), anchor=anchor)
        sh = sh.filter(ImageFilter.GaussianBlur(5))
        base.alpha_composite(sh)
    ImageDraw.Draw(base).text(xy, text, font=font, fill=fill + (255,), anchor=anchor)


def _spread(text, n=1):
    return (" " * n).join(list(text))


def pick_text(niche, seed):
    """Deterministic mood word + sub for a niche+seed (so thumbnail & video match)."""
    cfg = NICHES.get(niche, NICHES["focus"])
    rng = np.random.default_rng(seed)
    return (cfg["words"][int(rng.integers(0, len(cfg["words"])))],
            cfg["subs"][int(rng.integers(0, len(cfg["subs"])))])


def draw_headline(base, niche, seed, word=None, sub=None, wordmark=True):
    """Draw the big mood headline (+ optional sub + LUMORA wordmark) onto `base`.
    Scales with base height. Used by the thumbnail and the video overlay."""
    W, H = base.size
    k = H / 720.0
    cfg = NICHES.get(niche, NICHES["focus"])
    if word is None or sub is None:
        word, sub = pick_text(niche, seed)
    accent = tuple(cfg["accent"])
    parts = word.split()
    lines = [" ".join(parts[:-1]), parts[-1]] if len(parts) >= 3 else parts
    size = int(150 * k)
    while size > int(70 * k):
        f = _font("Anton-Regular.ttf", size)
        widest = max(ImageDraw.Draw(base).textlength(ln, font=f) for ln in lines)
        if widest <= W * 0.62:
            break
        size -= int(6 * k) or 1
    fbig = _font("Anton-Regular.ttf", size)
    lh = int(size * 1.02)
    y0 = int(H * 0.90) - lh * len(lines)
    for i, ln in enumerate(lines):
        _draw_text(base, (int(66 * k), y0 + i * lh), ln, fbig,
                   (255, 255, 255) if i == 0 else accent, glow=accent, glow_r=int(16 * k))
    _draw_text(base, (int(72 * k), y0 - int(46 * k)), _spread(sub, 1),
               _font("Poppins-Bold.ttf", int(34 * k)), (232, 238, 250), shadow=(0, 0, 0), sx=2, sy=3)
    if wordmark:
        fmark = _font("Poppins-Bold.ttf", int(34 * k))
        dl = ImageDraw.Draw(base)
        mark = _spread("LUMORA", 2)
        mw = dl.textlength(mark, font=fmark)
        mx, my = W - int(66 * k) - mw, int(70 * k)
        dl.ellipse([mx - 40 * k, my - 15 * k, mx - 12 * k, my + 13 * k], fill=accent + (255,))
        dl.ellipse([mx - 34 * k, my - 9 * k, mx - 18 * k, my + 7 * k], fill=(255, 255, 255, 230))
        _draw_text(base, (mx, my), mark, fmark, (240, 244, 252), anchor="lm", shadow=(0, 0, 0), sx=1, sy=2)


def make(niche, minutes, seed, out_path, title=None):
    """1280x720 thumbnail = scene + headline + duration pill + wordmark."""
    W, H = 1280, 720
    base = build_scene(niche, seed, W, H)
    word, sub = pick_text(niche, seed)
    if title:
        word = title
    draw_headline(base, niche, seed, word=word, sub=sub, wordmark=True)
    # duration pill (top-left)
    cfg = NICHES.get(niche, NICHES["focus"])
    accent = tuple(cfg["accent"])
    mins = int(minutes)
    dur = (f"{mins // 60} HOUR" + ("S" if mins >= 120 else "")) if mins >= 60 else f"{mins} MIN"
    fdur = _font("Poppins-Bold.ttf", 30)
    dl = ImageDraw.Draw(base)
    dw = dl.textlength(dur, font=fdur)
    dl.rounded_rectangle([66, 54, 66 + dw + 40, 106], radius=26, fill=accent + (235,))
    dl.text((86, 80), dur, font=fdur, fill=(12, 14, 22, 255), anchor="lm")
    base.convert("RGB").save(out_path, "JPEG", quality=90)
    return out_path


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    for n, mins in [("focus", 60), ("study", 60), ("sleep", 180)]:
        p = os.path.join(ROOT, "output", f"thumb_{n}.jpg")
        make(n, mins, seed=7, out_path=p)
        print("OK ->", p)
