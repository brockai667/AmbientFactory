# -*- coding: utf-8 -*-
"""Lumora thumbnail generator — 1280x720 clickbait-but-tasteful thumbnails for ambient music.
Consistent "world" per brand (aurora sky + layered mountain silhouettes + glowing Lumora moon)
+ big mood headline (<=3 words) + sub-label + duration + LUMORA wordmark. One dominant subject,
high contrast, mobile-legible. Per-niche palette + rotating mood words (seeded).

make(niche, minutes, seed, out_path) -> saves a JPG (<2MB) ready as a YouTube thumbnail.
"""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(ROOT, "fonts")
W, H = 1280, 720

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


def _orb(cx, cy, R, color, halo=2.4):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot(xx - cx, yy - cy)
    glow = np.exp(-(r / (R * halo)) ** 2) * 0.9
    body = np.clip((R - r) / max(R * 0.14, 1) + 1, 0, 1)
    a = np.maximum(body, glow)
    rgb = np.ones((H, W, 3), np.float32) * np.array(color, np.float32)
    # brighten toward core
    rgb += (np.exp(-(r / (R * 0.7)) ** 2) * 25)[..., None]
    return _layer(rgb, a)


def _draw_text(base, xy, text, font, fill, anchor="la",
               glow=None, glow_r=14, shadow=(0, 0, 0), sx=4, sy=6, spacing=0):
    """Draw text with drop shadow + optional colored glow (for pop/contrast)."""
    if glow is not None:
        gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(gl)
        gd.text(xy, text, font=font, fill=glow + (255,), anchor=anchor)
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


def make(niche, minutes, seed, out_path, title=None):
    cfg = NICHES.get(niche, NICHES["focus"])
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    # 1) SKY gradient (vertical) + horizon glow
    top = np.array(cfg["sky"][0], np.float32)
    bot = np.array(cfg["sky"][1], np.float32)
    t = (yy / H)[..., None]
    sky = top[None, None] * (1 - t) + bot[None, None] * t
    horizon = np.exp(-((yy - H * 0.72) / (H * 0.28)) ** 2) * 0.35
    sky += horizon[..., None] * np.array(cfg["aurora"][1], np.float32) * 0.5
    base = Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

    # 2) AURORA bands (curved glowing streaks in upper sky)
    for i, col in enumerate(cfg["aurora"]):
        yc = H * (0.28 + 0.14 * i) + rng.uniform(-20, 20)
        amp = rng.uniform(30, 60)
        thick = rng.uniform(40, 70)
        freq = rng.uniform(1.2, 2.2)
        phase = rng.uniform(0, 6.28)
        line = yc + amp * np.sin(xx / W * np.pi * freq + phase)
        a = np.exp(-((yy - line) / thick) ** 2) * 0.5
        base.alpha_composite(_layer(np.array(col, np.float32), a).filter(ImageFilter.GaussianBlur(8)))

    # 3) STARS (upper sky)
    stars = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stars)
    for _ in range(150):
        sx_, sy_ = rng.uniform(0, W), rng.uniform(0, H * 0.62)
        rad = rng.uniform(0.5, 1.8)
        al = int(rng.uniform(30, 160))
        sd.ellipse([sx_ - rad, sy_ - rad, sx_ + rad, sy_ + rad], fill=(230, 240, 255, al))
    base.alpha_composite(stars.filter(ImageFilter.GaussianBlur(0.5)))

    # 4) MOON (glowing Lumora light), rule-of-thirds upper-right
    mcx, mcy, mR = W * 0.70, H * 0.30, 60
    base.alpha_composite(_orb(mcx, mcy, mR, cfg["moon"]))

    # 5) MOUNTAIN silhouettes (3 layers, atmospheric perspective + moon rim light)
    layers = [
        (H * 0.60, 70, 0.62, 0.28),   # far  (base_y, amp, rough, fog_mix)
        (H * 0.72, 95, 0.58, 0.15),
        (H * 0.86, 120, 0.55, 0.0),   # near (darkest)
    ]
    fog = np.array(cfg["aurora"][1], np.float32)
    for base_y, amp, rough, fogmix in layers:
        heights = _ridge(W, amp, rough, rng, base_y)
        mask = (yy >= heights[None, :]).astype(np.float32)
        col = np.array([7, 9, 16], np.float32) * (1 - fogmix) + fog * fogmix * 0.5
        mtn = _layer(np.ones((H, W, 3), np.float32) * col, mask * (0.90 + 0.1 * fogmix))
        # rim light on the top edge, tinted by moon (light comes from moon side)
        edge = np.clip(mask - np.roll(mask, 3, axis=0), 0, 1)
        edge[:4] = 0
        side = np.clip((xx - (W * 0.35)) / (W * 0.5), 0, 1)   # brighter toward moon (right)
        rim = _layer(np.array(cfg["moon"], np.float32), edge * side * 0.5).filter(ImageFilter.GaussianBlur(1.5))
        base.alpha_composite(mtn)
        base.alpha_composite(rim)

    # 6) foreground haze + vignette
    haze = np.exp(-((H - yy) / (H * 0.22)) ** 2) * 0.22
    base.alpha_composite(_layer(fog, haze))
    vig = ((np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))) ** 2 * 0.55)
    base.alpha_composite(_layer(np.array([0, 0, 0], np.float32), np.clip(vig, 0, 0.7)))

    # 7) TEXT — big mood headline (stacked words), lower-left
    word = title or cfg["words"][int(rng.integers(0, len(cfg["words"])))]
    sub = cfg["subs"][int(rng.integers(0, len(cfg["subs"])))]
    parts = word.split()
    if len(parts) >= 3:
        lines = [" ".join(parts[:-1]), parts[-1]]
    else:
        lines = parts
    # adaptive font size so widest line fits
    size = 150
    while size > 70:
        f = _font("Anton-Regular.ttf", size)
        widest = max(ImageDraw.Draw(base).textlength(ln, font=f) for ln in lines)
        if widest <= W * 0.62:
            break
        size -= 6
    fbig = _font("Anton-Regular.ttf", size)
    lh = int(size * 1.02)
    total = lh * len(lines)
    y0 = int(H * 0.90) - total
    accent = tuple(cfg["accent"])
    for i, ln in enumerate(lines):
        col = (255, 255, 255) if i == 0 else accent
        _draw_text(base, (66, y0 + i * lh), ln, fbig, col, anchor="la",
                   glow=accent, glow_r=16)

    # sub-label above headline
    fsub = _font("Poppins-Bold.ttf", 34)
    _draw_text(base, (72, y0 - 46), _spread(sub, 1), fsub, (232, 238, 250),
               anchor="la", glow=None, shadow=(0, 0, 0), sx=2, sy=3)

    # duration pill (top-left, out of the bottom-right duration stamp zone)
    mins = int(minutes)
    dur = (f"{mins // 60} HOUR" + ("S" if mins >= 120 else "")) if mins >= 60 else f"{mins} MIN"
    fdur = _font("Poppins-Bold.ttf", 30)
    dl = ImageDraw.Draw(base)
    dw = dl.textlength(dur, font=fdur)
    px, py = 66, 54
    dl.rounded_rectangle([px, py, px + dw + 40, py + 52], radius=26,
                         fill=accent + (235,))
    dl.text((px + 20, py + 26), dur, font=fdur, fill=(12, 14, 22, 255), anchor="lm")

    # LUMORA wordmark (top-right, with a mini orb dot)
    fmark = _font("Poppins-Bold.ttf", 34)
    mark = "LUMORA"
    mw = dl.textlength(_spread(mark, 2), font=fmark)
    mx = W - 66 - mw
    my = 70
    dl.ellipse([mx - 40, my - 15, mx - 12, my + 13], fill=accent + (255,))
    dl.ellipse([mx - 34, my - 9, mx - 18, my + 7], fill=(255, 255, 255, 230))
    _draw_text(base, (mx, my), _spread(mark, 2), fmark, (240, 244, 252),
               anchor="lm", glow=None, shadow=(0, 0, 0), sx=1, sy=2)

    base.convert("RGB").save(out_path, "JPEG", quality=90)
    return out_path


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    for n, mins in [("focus", 60), ("study", 60), ("sleep", 180)]:
        p = os.path.join(ROOT, "output", f"thumb_{n}.jpg")
        make(n, mins, seed=7, out_path=p)
        print("OK ->", p)
