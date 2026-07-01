#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AmbientFactory -> SPOTIFY / Apple Music: generuj ALBUM kratkych tratkov (2-3 min) +
stvorcovy cover (3000x3000) + metadata.csv pre DistroKid.
Ten isty engine ako YouTube, len KRATKE standalone tracky (Spotify = per-stream, kratke = viac streamov).

DistroKid nema verejne API -> album nahras RUCNE (bulk drag-drop). Fabrika ho len pripravi.

Pouzitie: python make_album.py <niche> [pocet_tratkov] [seed]
"""
import os, sys, csv, random
from PIL import Image, ImageDraw
import ambient as A
import music

OUT = os.path.join(A.ROOT, "albums")

TRACK_NAMES = {
    "focus": ["Clarity", "Deep Work", "Flow State", "Concentration", "Still Mind", "In the Zone",
              "Quiet Focus", "Momentum", "Undisturbed", "Tunnel Vision", "Calm Precision", "Locked In"],
    "study": ["Quiet Hours", "Study Session", "Open Book", "Late Library", "Soft Focus", "Revision",
              "Slow Reading", "Gentle Mind", "Exam Calm", "Page Turn", "Memory", "Coffee and Books"],
    "sleep": ["Drifting", "Night Rain", "Deep Rest", "Into Sleep", "Slow Breath", "Moonless",
              "Still Night", "Fading", "Dream Tide", "Quiet Dark", "Weightless", "Midnight Calm"],
}
ARTIST = "Lumora"
GENRE = "Ambient"


def square_cover(niche, path, seed=7, size=3000):
    """stvorcovy cover: kratky flow-field render (1440px) -> posledny frame -> upscale + brand text."""
    last = None
    for fr in A.flow_field(niche, 1440, 1440, 30, 2.0, seed=seed):
        last = fr
    im = Image.fromarray(last, "RGB").resize((size, size), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    p = A.NICHES[niche]; accent = tuple((A.PALETTES[p["palette"]][1] * 255).astype(int).tolist())
    bf, sf = A._font(int(size * 0.12)), A._font(int(size * 0.05))
    bw = d.textlength(ARTIST, font=bf); d.text(((size - bw) / 2, size * 0.40), ARTIST, font=bf, fill=(245, 247, 255))
    sub = p["sub"].upper(); sw = d.textlength(sub, font=sf)
    d.text(((size - sw) / 2, size * 0.55), sub, font=sf, fill=accent)
    im.save(path, "JPEG", quality=92)


def make_album(niche, n=12, seed=7):
    if niche not in A.NICHES:
        raise SystemExit(f"neznama nika '{niche}'")
    rng = random.Random(seed)
    names = TRACK_NAMES[niche][:]; rng.shuffle(names); n = min(n, len(names))
    album = f"{niche.capitalize()}, Vol. 1"
    folder = os.path.join(OUT, f"{niche}_vol1"); os.makedirs(folder, exist_ok=True)
    print(f"[{niche}] cover 3000x3000...")
    square_cover(niche, os.path.join(folder, "cover.jpg"), seed=seed)
    rows = []
    for i in range(n):
        title = names[i]; secs = rng.uniform(150, 200)         # 2.5-3.3 min (legit, nie spam)
        A.write_wav(os.path.join(folder, f"{i+1:02d} {title}.wav"),
                    music.compose(secs, seed=seed * 1000 + i, niche=niche, fin=4.0, fout=6.0))
        rows.append({"track": i + 1, "title": title, "artist": ARTIST, "album": album,
                     "genre": GENRE, "length": f"{int(secs//60)}:{int(secs%60):02d}", "file": f"{i+1:02d} {title}.wav"})
        print(f"  {i+1:02d} {title}  ({secs/60:.1f} min)")
    with open(os.path.join(folder, "metadata.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"[{niche}] HOTOVO -> {folder}  ({n} tratkov + cover.jpg + metadata.csv)")
    return folder


if __name__ == "__main__":
    niche = sys.argv[1] if len(sys.argv) > 1 else "focus"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    make_album(niche, n, seed)
