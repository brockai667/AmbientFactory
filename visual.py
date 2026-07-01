# -*- coding: utf-8 -*-
"""Lumora long-form VIDEO visual — the thumbnail SCENE brought to life, like a real ambient/lofi
music video: a gorgeous still (aurora + mountains + moon) with SUBTLE motion —
  - floating dust motes (gentle sinusoidal drift)
  - slow "breathing" zoom + micro-pan (Ken Burns)
  - the mood text slowly circling a few px
Everything is periodic over the loop -> SEAMLESS when ffmpeg -stream_loop repeats it for 1-3h.

frames(niche, W, H, fps, seconds, seed) -> yields numpy uint8 (H,W,3) RGB, drop-in for ambient.flow_field.
"""
import numpy as np
from PIL import Image
import thumbnail


def _dot(size, color, bright):
    """Soft round glowing dust sprite (RGBA)."""
    s = max(3, int(size))
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    c = (s - 1) / 2.0
    r = np.hypot(xx - c, yy - c) / (c + 1e-6)
    a = np.clip(1 - r, 0, 1) ** 1.8 * float(bright)
    arr = np.dstack([np.full((s, s), color[0], np.float32),
                     np.full((s, s), color[1], np.float32),
                     np.full((s, s), color[2], np.float32),
                     np.clip(a, 0, 1) * 255]).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def frames(niche, W, H, fps, seconds, seed, period=None):
    """period = motion cycle length in seconds (defaults to `seconds` -> exact seamless loop).
    A separate `period` lets a short preview show the real (slow) speed."""
    cfg = thumbnail.NICHES.get(niche, thumbnail.NICHES["focus"])
    rng = np.random.default_rng(seed * 7 + 3)
    sc = H / 1080.0
    T = float(period or seconds)

    # base scene rendered with margin so zoom/pan never reveals an edge
    MRG = 1.13
    BW, BH = int(W * MRG), int(H * MRG)
    scene = thumbnail.build_scene(niche, seed, BW, BH).convert("RGB")

    # mood text layer (headline + LUMORA wordmark), rendered ONCE at final res -> slowly circles
    word, sub = thumbnail.pick_text(niche, seed)
    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    thumbnail.draw_headline(text_layer, niche, seed, word=word, sub=sub, wordmark=True)

    # dust particles (softer + bigger so any residual stepping is imperceptible)
    n = int(70 * (W * H) / (1920 * 1080)) + 30
    bx = rng.uniform(0, W, n)
    by = rng.uniform(0, H * 0.95, n)
    depth = rng.uniform(0.30, 1.0, n)          # far(small/dim) .. near(big/bright)
    amp = (10 + depth * 34) * sc                # drift amplitude (px)
    phx = rng.uniform(0, 6.283, n)
    phy = rng.uniform(0, 6.283, n)
    kx = rng.integers(1, 3, n)                  # integer harmonics -> periodic over loop
    ky = rng.integers(1, 3, n)
    col = tuple(cfg["moon"])
    ss = 2                                        # dust supersample -> sub-pixel smooth drift
    sprites = [_dot((7 + depth[i] * 17) * sc * ss, col, 0.20 + depth[i] * 0.45) for i in range(n)]

    N = int(round(seconds * fps))
    for i in range(N):
        ang = 2 * np.pi * (i / (fps * T))       # one full cycle every T seconds
        # breathing zoom in [1.0 .. ~1.05] + gentle micro-pan (all periodic, eased)
        z = 1.0 + 0.042 * (1 - np.cos(ang))
        cw, ch = W / z, H / z
        panx = (BW - cw) * (0.5 + 0.17 * np.sin(ang))
        pany = (BH - ch) * (0.5 + 0.14 * np.sin(ang + 1.1))
        panx = min(max(panx, 0.0), BW - cw)
        pany = min(max(pany, 0.0), BH - ch)
        # SUB-PIXEL zoom/pan via affine sampling (BICUBIC) -> smooth, no pixel stair-stepping
        fr = scene.transform((W, H), Image.AFFINE, (cw / W, 0, panx, 0, ch / H, pany),
                             resample=Image.BICUBIC).convert("RGBA")
        # floating dust on a 2x layer -> downscaled = sub-pixel smooth
        ov = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
        for k in range(n):
            x = (bx[k] + amp[k] * np.sin(ang * kx[k] + phx[k])) * ss
            y = (by[k] + amp[k] * 0.7 * np.sin(ang * ky[k] + phy[k])) * ss
            sp = sprites[k]
            ov.paste(sp, (int(x - sp.width / 2), int(y - sp.height / 2)), sp)
        fr.alpha_composite(ov.resize((W, H), Image.LANCZOS))
        # text slowly circling (sub-pixel float orbit via affine translate)
        dx = 9 * sc * np.cos(ang)
        dy = 7 * sc * np.sin(ang)
        fr.alpha_composite(text_layer.transform((W, H), Image.AFFINE, (1, 0, -dx, 0, 1, -dy),
                                                 resample=Image.BICUBIC))
        yield np.asarray(fr.convert("RGB"), dtype=np.uint8)


if __name__ == "__main__":
    # quick sanity: dump a few frames to inspect the look (not a full render)
    import os
    out = os.path.join(thumbnail.ROOT, "output")
    os.makedirs(out, exist_ok=True)
    gen = frames("focus", 1920, 1080, 30, 6, seed=7)
    for idx, f in enumerate(gen):
        if idx in (0, 90, 179):
            Image.fromarray(f).save(os.path.join(out, f"visual_frame_{idx}.jpg"), quality=88)
            print("saved frame", idx)
