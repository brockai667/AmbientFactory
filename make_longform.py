#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AmbientFactory -- render PLNEHO DLHEHO videa (1-3h) pre niku, EFEKTIVNE:
  - zvuk: generovany PO KUSKOCH -> WAV (bounded memory, ~46MB/kus), bez per-loop fade
  - vizual: kratky loop (~90s) vyrenderovany RAZ (preto je 2h rovnako lacne ako 2min)
  - finale: ffmpeg -stream_loop oboje na cielovu dlzku + GLOBALNY fade in/out + loudnorm
Output moze byt velky (2h ~ 2-3 GB) -> po uploade sa zmaze.

Pouzitie: python make_longform.py <niche> [minuty] [seed]
"""
import os, sys, subprocess
import ambient as A
import music
import thumbnail
import visual

OUT, TMP, FF = A.OUT, A.TMP, A.FF
SR = 48000
AUDIO_LOOP_CAP = 12 * 60      # max dlzka hud. slucky (dlhsie sa loopuje cez stream_loop)
VIS_LOOP = 90                 # dlzka vizual slucky (s) -- renderuje sa RAZ


def stream_audio(niche, seconds, path, seed=7):
    """v3 hudba: koherentny hudobny loop (piano + akordy + lo-fi beat). Bez velkych fade
    (seamless-ish loop; globalny fade in/out sa aplikuje az v finalnom muxe)."""
    music.write_wav(path, music.compose(seconds, seed=seed, niche=niche, fin=0.25, fout=0.25))
    print(f"    hudba {int(seconds)}s ok")


def render_visual_loop(niche, path, seed=7):
    W, H, fps = 1920, 1080, 30
    cmd = [FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-g", str(fps * 2),
           "-maxrate", "6M", "-bufsize", "12M", "-pix_fmt", "yuv420p", "-movflags", "+faststart", path]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE); nf = int(fps * VIS_LOOP); last = None
    for i, fr in enumerate(visual.frames(niche, W, H, fps, VIS_LOOP, seed=seed)):
        pr.stdin.write(fr.tobytes()); last = fr
        if i % 90 == 0:
            print(f"    vizual {i}/{nf}")
    pr.stdin.close()
    if pr.wait() != 0:
        raise SystemExit("vizual loop zlyhal")
    return last


def make(niche, minutes, seed=7):
    if niche not in A.NICHES:
        raise SystemExit(f"neznama nika '{niche}'. dostupne: {', '.join(A.NICHES)}")
    p = A.NICHES[niche]; total = int(minutes * 60); fin, fout = 6.0, 10.0
    aud = os.path.join(TMP, f"{niche}_audio.wav"); vis = os.path.join(TMP, f"{niche}_visloop.mp4")
    a_sec = min(total, AUDIO_LOOP_CAP)
    print(f"[{niche}] 1/3 zvuk {a_sec}s (loop unit)...");  stream_audio(niche, a_sec, aud, seed=seed)
    print(f"[{niche}] 2/3 vizual loop {VIS_LOOP}s (raz)..."); last = render_visual_loop(niche, vis, seed=seed)
    print(f"[{niche}] 3/3 skladam {int(minutes)} min cez -stream_loop + fade + loudnorm...")
    out = os.path.join(OUT, f"{niche}_{int(minutes)}min.mp4")
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:st=0:d={fin},"
          f"afade=t=out:st={max(0, total - fout):.1f}:d={fout}")
    cmd = [FF, "-y", "-stream_loop", "-1", "-i", vis, "-stream_loop", "-1", "-i", aud,
           "-t", str(total), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
           "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out]
    if subprocess.run(cmd).returncode != 0:
        raise SystemExit("finalny mux zlyhal")
    jpg = os.path.join(OUT, f"{niche}_{int(minutes)}min.jpg")
    try:                                            # pekny Lumora thumbnail (aurora+hory+mesiac+text)
        thumbnail.make(niche, minutes, seed, jpg)
    except Exception as e:                          # poistka: ak zlyha (napr. font), pouzi stary frame
        print(f"    [pozn.] pekny thumbnail zlyhal ({e}) -> fallback na frame")
        accent = tuple((A.PALETTES[p["palette"]][1] * 255).astype(int).tolist())
        A.thumbnail(last, p["brand"], p["sub"], accent, jpg)
    print(f"[{niche}] HOTOVO -> {out}")
    return out


if __name__ == "__main__":
    niche = sys.argv[1] if len(sys.argv) > 1 else "focus"
    minutes = float(sys.argv[2]) if len(sys.argv) > 2 else 60.0
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    make(niche, minutes, seed)
