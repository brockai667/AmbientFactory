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
import buffer_post
import youtube_upload as yt

ROOT = os.path.dirname(os.path.abspath(__file__))
USED = os.path.join(ROOT, "used.json")
BANK = os.path.join(ROOT, "bank.json")   # rastuca banka schem (seed=schemes.SCHEMES, prirasta o auto-gen)
OUTDIR = os.path.join(ROOT, "output")
POSTS_PER_RUN = 1            # kolko videi na kanal za beh (zdvihni pre vyssiu kadenciu)


def cfg():
    p = os.path.join(ROOT, "config.json")
    c = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    c["youtube_client_id"] = os.environ.get("YOUTUBE_CLIENT_ID", c.get("youtube_client_id", ""))
    c["youtube_client_secret"] = os.environ.get("YOUTUBE_CLIENT_SECRET", c.get("youtube_client_secret", ""))
    c["buffer_token"] = os.environ.get("BUFFER_TOKEN", c.get("buffer_token", ""))
    return c


def refresh_for(niche, c):
    return os.environ.get(f"YT_REFRESH_{niche.upper()}") or \
        (c.get("niches", {}).get(niche, {}) or {}).get("youtube_refresh_token", "")


def _load():
    return json.load(open(USED, encoding="utf-8")) if os.path.exists(USED) else []


def used_ids():
    return set(x.get("scheme") for x in _load())


def load_bank():
    """Rastuca banka schem: seed z schemes.SCHEMES, potom prirasta o dobre auto-generovane (bank.json)."""
    if os.path.exists(BANK):
        try:
            return json.load(open(BANK, encoding="utf-8"))
        except Exception:
            pass
    data = [dict(s) for s in schemes.SCHEMES]
    json.dump(data, open(BANK, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return data


def add_to_bank(sch):
    """Prida dobru auto-generovanu schemu do banky (ak nie je duplikat titulu) -> banka rastie."""
    bank = load_bank()
    if any(glitch_gen._sim(sch["title"], b.get("title", "")) for b in bank):
        return
    bank.append(sch)
    json.dump(bank, open(BANK, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  [bank] +1 schema (banka ma teraz {len(bank)})")


def pick_scheme():
    bank = load_bank(); used = used_ids()
    pool = [s for s in bank if s["id"] not in used]
    if not pool:                                   # cely cyklus vycerpany -> reset rotacie
        json.dump([], open(USED, "w", encoding="utf-8"))
        pool = bank
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
    sch = glitch_gen.generate(avoid)                       # AUTO-gen (LLM + kontrola kvality)
    if sch:
        add_to_bank(sch)                                   # dobra generovana schema -> prirastie do RASTUCEJ banky
    else:
        sch = pick_scheme()                                # fallback na (rastucu) banku
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
    try:                                                    # cross-post na TikTok+IG cez Buffer (graceful ak nenastavene)
        buffer_post.post_social(c, out, meta["title"], meta["description"])
    except Exception as e:
        print("  [Buffer] preskoceny:", str(e)[:120])
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
