#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Long-form (16:9, 8-15 min) money-glitch orchestrator. Typ 'TOP N' kompilacia:
vyber N schem z (rastucej) banky -> glitch_long.build_long -> render_long -> 16:9 thumbnail ->
YouTube upload (regular video, nie shorts) -> zaznam do used_long.json (rotacia).
Bank sa best-effort dogeneruje (glitch_gen) na cielovu dlzku/variety. Long-form NEcross-postuje
na TikTok/IG (to su shorts platformy) — ide len na YouTube kanal Money Glitch.

  python glitch_long_daily.py            # ostry beh: pick + render (8-15min) + YT upload
  python glitch_long_daily.py --sample   # rychla vzorka (3 schemy, bez uploadu) na overenie wiringu
"""
import json, os, random, sys, time
from PIL import Image, ImageDraw
import glitch_engine as ge
import glitch_long as gl
import glitch_gen
import glitch_daily as gd          # znovupouzi cfg / load_bank / add_to_bank / refresh_for
import youtube_upload as yt

ROOT = os.path.dirname(os.path.abspath(__file__))
USED_LONG = os.path.join(ROOT, "used_long.json")
OUTDIR = os.path.join(ROOT, "output")
TARGET = 18                         # cielovy pocet kapitol (~8-10 min); banka sa best-effort dogeneruje


def _load(p):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


def pick_long(target=TARGET):
    """Vyber ~target schem: najprv best-effort dogeneruj banku (variety+dlzka), potom rotuj proti poslednym videam."""
    bank = gd.load_bank()
    avoid = [b.get("title", "") for b in bank]
    tries = 0
    while len(bank) < target and tries < 6:      # best-effort dopln banku (aj ju to natrvalo zvacsi)
        tries += 1
        try:
            sch = glitch_gen.generate(avoid)
        except Exception:
            sch = None
        if not sch:
            break
        gd.add_to_bank(sch); avoid.append(sch.get("title", "")); bank = gd.load_bank()
    used = set()
    for rec in _load(USED_LONG)[-2:]:            # vyhni sa opakovaniu oproti poslednym 2 dlhym videam
        used |= set(rec.get("ids", []))
    pool = [s for s in bank if s["id"] not in used]
    random.shuffle(pool)
    chosen = pool[:target]
    if len(chosen) < target:                     # dopln z celej banky ak treba
        have = {c["id"] for c in chosen}
        rest = [s for s in bank if s["id"] not in have]; random.shuffle(rest)
        chosen += rest[:target - len(chosen)]
    return chosen


def make_meta(subset):
    n = len(subset)
    title = f"{n} Money Glitches That Sound Illegal (But Technically Aren't)"[:100]
    desc = (f"The internet's most absurd get-rich money \"glitches\" — {n} of them, back to back.\n\n"
            "Satire / entertainment only. This is NOT financial advice (and no, don't actually melt any coins).\n\n"
            "Chapters:\n" + "\n".join(f"{i}. {s['title']}" for i, s in enumerate(subset, 1))[:3500] + "\n\n"
            "#money #moneyhacks #getrichquick #finance #sidehustle #passiveincome #satire")
    tags = ["money glitch", "money hacks", "get rich quick", "passive income", "side hustle",
            "money", "finance", "how to get rich", "satire", "money compilation"]
    return {"title": title, "description": desc[:4900], "tags": tags[:15]}


def make_thumb(subset, path):
    """16:9 thumbnail 1280x720: velke 'N MONEY GLITCHES' + 'that sound illegal' + maskot."""
    W, H = 1280, 720
    fr = Image.new("RGB", (W, H), ge.PAPER); d = ImageDraw.Draw(fr)
    n = len(subset)
    d.text((470, 190), str(n), font=ge.F(300), fill=ge.GREEN, anchor="mm")
    d.text((760, 150), "MONEY", font=ge.F(150), fill=ge.INK, anchor="lm")
    d.text((760, 300), "GLITCHES", font=ge.F(150), fill=ge.INK, anchor="lm")
    sub = "that sound illegal"
    d.text((70, 470), sub, font=ge.F(96), fill=ge.RED, anchor="lm")
    # rucny cerveny podciarknik pod podnadpisom
    tw = d.textlength(sub, font=ge.F(96))
    d.line([(70, 528), (70 + tw, 534)], fill=ge.RED, width=9)
    m = ge.CHARS[(0, 0)]; mh = 470; m = m.resize((int(m.width * mh / m.height), mh))
    fr.paste(m, (W - m.width - 30, H - mh + 20), m)
    fr.convert("RGB").save(path, "JPEG", quality=90)


def main():
    sample = "--sample" in sys.argv
    c = gd.cfg()
    os.makedirs(OUTDIR, exist_ok=True)
    if sample:
        subset = gd.load_bank()[:3]
        steps = gl.build_long(subset)
        out = os.path.join(OUTDIR, "long_sample.mp4")
        gl.render_long(steps, out, tmp=OUTDIR); make_thumb(subset, out[:-4] + ".jpg")
        print(f"[sample] {len(subset)} kapitol -> {out} (+ thumb), bez uploadu"); return
    subset = pick_long()
    print(f"=== LONG: {len(subset)} kapitol ===")
    steps = gl.build_long(subset)
    out = os.path.join(OUTDIR, "long.mp4"); thumb = out[:-4] + ".jpg"
    gl.render_long(steps, out, tmp=OUTDIR)
    make_thumb(subset, thumb)
    meta = make_meta(subset)
    rtok = os.environ.get("YT_REFRESH_FOCUS") or gd.refresh_for("focus", c)
    if rtok and c.get("youtube_client_id"):
        try:
            vid = yt.upload_video(out, meta, rtok, jpg=thumb,
                                  client_id=c["youtube_client_id"],
                                  client_secret=c["youtube_client_secret"], category="22")
            rec = {"ts": time.strftime("%Y-%m-%d %H:%M"), "video_id": vid,
                   "title": meta["title"], "ids": [s["id"] for s in subset]}
            data = _load(USED_LONG); data.append(rec)
            json.dump(data, open(USED_LONG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            print("  upload OK:", vid)
        except Exception as e:
            print("  UPLOAD ZLYHAL:", str(e)[:200])
    else:
        print("  [pozn.] chyba YT token -> len render, neuploadujem")
    for p in (out, thumb):
        try:
            if rtok:
                os.remove(p)
        except OSError:
            pass


if __name__ == "__main__":
    main()
