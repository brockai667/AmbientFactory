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


def frames(niche, W, H, fps, seconds, seed):
    cfg = thumbnail.NICHES.get(niche, thumbnail.NICHES["focus"])
    rng = np.random.default_rng(seed * 7 + 3)
    sc = H / 1080.0

    # base scene rendered with margin so zoom/pan never reveals an edge
    MRG = 1.08
    BW, BH = int(W * MRG), int(H * MRG)
    scene = thumbnail.build_scene(niche, seed, BW, BH).convert("RGB")

    # mood text layer (headline + LUMORA wordmark), rendered ONCE at final res -> slowly circles
    word, sub = thumbnail.pick_text(niche, seed)
    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    thumbnail.draw_headline(text_layer, niche, seed, word=word, sub=sub, wordmark=True)

    # dust particles
    n = int(80 * (W * H) / (1920 * 1080)) + 40
    bx = rng.uniform(0, W, n)
    by = rng.uniform(0, H * 0.95, n)
    depth = rng.uniform(0.30, 1.0, n)          # far(small/dim) .. near(big/bright)
    amp = (7 + depth * 24) * sc                 # drift amplitude (px)
    phx = rng.uniform(0, 6.283, n)
    phy = rng.uniform(0, 6.283, n)
    kx = rng.integers(1, 3, n)                  # integer harmonics -> periodic over loop
    ky = rng.integers(1, 3, n)
    col = tuple(cfg["moon"])
    sprites = [_dot((5 + depth[i] * 15) * sc, col, 0.22 + depth[i] * 0.5) for i in range(n)]

    N = int(round(seconds * fps))
    for i in range(N):
        ang = 2 * np.pi * (i / N)               # one full period over the whole loop
        # breathing zoom in [1.0 .. ~1.056] + gentle micro-pan (all periodic)
        z = 1.0 + 0.028 * (1 - np.cos(ang))
        cw, ch = W / z, H / z
        panx = (BW - cw) * (0.5 + 0.12 * np.sin(ang))
        pany = (BH - ch) * (0.5 + 0.10 * np.sin(ang + 1.1))
        panx = min(max(panx, 0.0), BW - cw)
        pany = min(max(pany, 0.0), BH - ch)
        fr = scene.crop((int(panx), int(pany), int(panx + cw), int(pany + ch))) \
                  .resize((W, H), Image.BILINEAR).convert("RGBA")
        # floating dust (paste = clip/negative-safe)
        for k in range(n):
            x = bx[k] + amp[k] * np.sin(ang * kx[k] + phx[k])
            y = by[k] + amp[k] * 0.7 * np.sin(ang * ky[k] + phy[k])
            sp = sprites[k]
            fr.paste(sp, (int(x - sp.width / 2), int(y - sp.height / 2)), sp)
        # text slowly circling (a few px orbit)
        dx = int(9 * sc * np.cos(ang))
        dy = int(7 * sc * np.sin(ang))
        fr.paste(text_layer, (dx, dy), text_layer)
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
