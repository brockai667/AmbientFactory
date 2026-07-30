#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Money-glitch denny beh (Lumora prerobena): vyber NEPOUZITU schemu z banky -> render reel ->
metadata + thumbnail -> YouTube upload -> zaznam do used.json (rotacia). OAuth per kanal
cez ENV YT_REFRESH_<NIKA> (rovnaka plumbing ako povodny ambient).

  python glitch_daily.py            # vsetky zapnute niky co maju token (inak render 1 sample)
  python glitch_daily.py --sample   # len vyrenderuj 1 sample, ziadny upload (test)
"""
import json, os, random, sys, time
from PIL import ImageDraw
import glitch_engine as ge
import schemes
import glitch_gen
import youtube_upload as yt

ROOT = os.path.dirname(os.path.abspath(__file__))
USED = os.path.join(ROOT, "used.json")
OUTDIR = os.path.join(ROOT, "output")
POSTS_PER_RUN = 1            # kolko videi na kanal za beh (zdvihni pre vyssiu kadenciu)


def cfg():
    p = os.path.join(ROOT, "config.json")
    c = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    c["youtube_client_id"] = os.environ.get("YOUTUBE_CLIENT_ID", c.get("youtube_client_id", ""))
    c["youtube_client_secret"] = os.environ.get("YOUTUBE_CLIENT_SECRET", c.get("youtube_client_secret", ""))
    return c


def refresh_for(niche, c):
    return os.environ.get(f"YT_REFRESH_{niche.upper()}") or \
        (c.get("niches", {}).get(niche, {}) or {}).get("youtube_refresh_token", "")


def _load():
    return json.load(open(USED, encoding="utf-8")) if os.path.exists(USED) else []


def used_ids():
    return set(x.get("scheme") for x in _load())


def pick_scheme():
    used = used_ids()
    pool = [s for s in schemes.SCHEMES if s["id"] not in used]
    if not pool:                                   # cely cyklus vycerpany -> reset rotacie
        json.dump([], open(USED, "w", encoding="utf-8"))
        pool = schemes.SCHEMES
    return random.choice(pool)


def mark_used(sch, niche, vid):
    data = _load()
    data.append({"scheme": sch["id"], "title": sch.get("title", ""), "niche": niche,
                 "video_id": vid, "ts": time.strftime("%Y-%m-%d %H:%M")})
    json.dump(data, open(USED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def make_meta(scheme):
    title = (scheme["title"] + " \U0001F92F #shorts")[:100]
    desc = (scheme["title"] + "\n\n"
            "Your daily dose of absurd money \"glitches\" — a new get-rich-quick scheme every day.\n"
            "Satire / entertainment only. This is NOT financial advice (and please don't melt any coins).\n\n"
            "#money #moneyhack #getrichquick #finance #sidehustle #satire #shorts")
    tags = ["money glitch", "how to get rich", "money hack", "get rich quick", "finance",
            "passive income", "side hustle", "money", "satire", "shorts"]
    return {"title": title, "description": desc[:4900], "tags": tags[:15]}


def make_thumb(scheme, path):
    fr = ge.PAPER_IMG.copy(); d = ImageDraw.Draw(fr)
    hook = scheme["steps"][0]["cap"]; fnt = ge.F(104)
    words = hook.split(); lines = []; cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= 960:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    lh = 122; y0 = 360 - (len(lines) - 1) * lh // 2
    for i, ln in enumerate(lines):
        w = d.textlength(ln, font=fnt); d.text((540 - w / 2, y0 + i * lh), ln, font=fnt, fill=ge.INK)
    greens = [s.get("num") for s in scheme["steps"] if s.get("num") and s.get("col") == "green"]
    if greens:
        ge.pop(fr, (540, 960), greens[-1], ge.F(240), ge.GREEN, 1.0, shadow=True)
    ge.paste_c(fr, ge.CHARS[(0, 0)], 540, 1470, 1.0)
    fr.convert("RGB").save(path, "JPEG", quality=88)


def _do(niche, rtok, c):
    avoid = [x.get("title", "") for x in _load()][-40:]
    sch = glitch_gen.generate(avoid) or pick_scheme()      # AUTO-gen (LLM+kontrola) alebo fallback na rucnu banku
    os.makedirs(OUTDIR, exist_ok=True)
    out = os.path.join(OUTDIR, f"{niche}_{sch['id']}.mp4")
    thumb = out[:-4] + ".jpg"
    print(f"=== {niche}: {sch['id']} ===")
    ge.render(sch, out, tmp=OUTDIR)
    make_thumb(sch, thumb)
    meta = make_meta(sch)
    if rtok and c["youtube_client_id"]:
        try:
            vid = yt.upload_video(out, meta, rtok, jpg=thumb,
                                  client_id=c["youtube_client_id"],
                                  client_secret=c["youtube_client_secret"], category="22")
            mark_used(sch, niche, vid)
        except Exception as e:
            print(f"  UPLOAD ZLYHAL ({niche}):", e)
    else:
        print(f"  [pozn.] {niche}: chyba token -> len render (sample), neuploadujem")
    for p in (out, thumb):
        try:
            if rtok:
                os.remove(p)
        except OSError:
            pass


def main():
    if "--sample" in sys.argv:
        sch = pick_scheme(); os.makedirs(OUTDIR, exist_ok=True)
        out = os.path.join(OUTDIR, f"sample_{sch['id']}.mp4")
        ge.render(sch, out, tmp=OUTDIR); make_thumb(sch, out[:-4] + ".jpg")
        print("sample:", out); return
    c = cfg()
    niches = c.get("niches", {})
    want = [n for n in sys.argv[1:] if n in niches]
    selected = want or [n for n, v in niches.items() if v.get("enabled")]
    targets = [(n, refresh_for(n, c)) for n in selected]
    live = [(n, r) for n, r in targets if r]
    if not live:
        print("ziaden kanal nema token -> renderujem 1 sample bez uploadu")
        _do(selected[0] if selected else "focus", "", c)
        return
    for niche, rtok in live:
        for _ in range(POSTS_PER_RUN):
            _do(niche, rtok, c)
    print("hotovo.")


if __name__ == "__main__":
    main()
