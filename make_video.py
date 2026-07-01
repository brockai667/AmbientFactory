#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lumora VIDEO: hypnoticky flow-field vizual + v2 HUDBA (music.compose) -> mp4 (1920x1080).
To je YouTube formát (vizual + zvuk spolu). Pre dlhe verzie -> make_longform (loop).

Pouzitie: python make_video.py <niche> [sekundy] [seed]
"""
import os, sys, subprocess
import ambient as A
import music


def make(niche, seconds, seed=7):
    if niche not in A.NICHES:
        raise SystemExit(f"neznama nika '{niche}'")
    W, H, fps = 1920, 1080, 30
    p = A.NICHES[niche]
    print(f"[{niche}] 1/3 hudba ({seconds:.0f}s)...")
    aud = os.path.join(A.TMP, f"v_{niche}.wav")
    music.write_wav(aud, music.compose(seconds, seed=seed, niche=niche))
    print(f"[{niche}] 2/3 vizual {W}x{H}...")
    silent = os.path.join(A.TMP, f"v_{niche}_silent.mp4")
    cmd = [A.FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "6M", "-bufsize", "12M",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", silent]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE); last = None; nf = int(fps * seconds)
    for i, fr in enumerate(A.flow_field(niche, W, H, fps, seconds, seed=seed)):
        pr.stdin.write(fr.tobytes()); last = fr
        if i % 60 == 0:
            print(f"    frame {i}/{nf}")
    pr.stdin.close()
    if pr.wait() != 0:
        raise SystemExit("vizual zlyhal")
    print(f"[{niche}] 3/3 mux...")
    out = os.path.join(A.OUT, f"video_{niche}.mp4")
    subprocess.run([A.FF, "-y", "-i", silent, "-i", aud, "-c:v", "copy", "-map", "0:v", "-map", "1:a",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", out])
    accent = tuple((A.PALETTES[p["palette"]][1] * 255).astype(int).tolist())
    A.thumbnail(last, p["brand"], p["sub"], accent, os.path.join(A.OUT, f"video_{niche}.jpg"))
    print(f"[{niche}] HOTOVO -> {out}")
    return out


if __name__ == "__main__":
    niche = sys.argv[1] if len(sys.argv) > 1 else "focus"
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 45.0
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    make(niche, seconds, seed)
