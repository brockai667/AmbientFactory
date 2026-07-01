# AmbientFactory (Lull)

Long-form **ambient** YouTube fabrika — spánok / focus / učenie. Všetko **programovo**
(zvuk aj vizuál), **0 copyrightu**, žiadne Suno. Monetizácia cez **watch-time + reklamy**
(2-3h video = ľudia ho nechajú hrať hodiny).

## Ako to funguje
1. `ambient.py` — parametrický engine: zvuk (pady + pentatonický zvonček + šum + fade) a
   hypnotický vizuál (flow-field, 1920×1080). Preset per nika (`NICHES`).
2. `make_longform.py` — efektívny render 1-3h videa: zvuk po kúskoch (bounded memory) +
   krátky vizuál loop (raz) + `ffmpeg -stream_loop` na cieľovú dĺžku + globálny fade + loudnorm.
3. `metadata.py` — titulky/popisy/tagy (šablóny + rotácia).
4. `youtube_upload.py` — resumable **chunked** upload (znesie 2-3 GB súbory), OAuth per kanál.
5. `daily.py` — denný beh: pre každú zapnutú niku → metadata → render → upload → uprac.

## Nika = vlastný YouTube kanál
Netreba nové Gmaily — použi **YouTube brand accounts** (viac kanálov pod 1 Google loginom).
Každá nika má vlastný OAuth `refresh_token`.

## Lokálne
```bash
pip install numpy pillow requests static-ffmpeg
python ambient.py demos                 # krátke ukážky ník
python make_longform.py focus 60        # 1h focus video
python daily.py focus                    # render + (ak je token) upload
```

## Deploy (GitHub Actions, public repo = neobmedzené minúty)
Secrets: `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YT_REFRESH_FOCUS`,
`YT_REFRESH_STUDY`, `YT_REFRESH_SLEEP`. Cron beží denne 02:00 UTC (`.github/workflows/daily.yml`).

`config.json` (tajomstvá) je **gitignored** — v cloude idú cez ENV/secrets.
