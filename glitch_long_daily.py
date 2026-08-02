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


def pick_long(target=TARGET, grow=3):
    """Denne 1 dlhe video: banka STALE rastie (variety) + LRU rotacia, aby sa denne kompilacie neopakovali.
    Vyber = 'najmenej nedavno pouzite' schemy naprieic celou bankou; dlzka (pocet kapitol) rastie s bankou."""
    bank = gd.load_bank()
    avoid = [b.get("title", "") for b in bank]
    tries = 0
    while len(bank) < 45 and tries < grow:       # kazdy beh best-effort pridaj par novych schem (nech banka rastie)
        tries += 1
        try:
            sch = glitch_gen.generate(avoid)
        except Exception:
            sch = None
        if not sch:
            break
        gd.add_to_bank(sch); avoid.append(sch.get("title", "")); bank = gd.load_bank()
    n = min(target, max(8, int(len(bank) * 0.7)))   # rotacia ma vzdy rezervu; video sa predlzuje ako banka rastie
    last_seen = {}                                # poradie posledneho pouzitia kazdej schemy (vyssie = novsie)
    for order, rec in enumerate(_load(USED_LONG)):
        for i in rec.get("ids", []):
            last_seen[i] = order
    random.shuffle(bank)                          # tie-break medzi rovnako "starymi"
    bank.sort(key=lambda s: last_seen.get(s["id"], -1))   # nikdy-nepouzite (-1) prve, potom najstarsie
    chosen = bank[:n]
    random.shuffle(chosen)                        # nech sa meni aj poradie kapitol
    return chosen


TITLES = [
    "{n} Money Glitches That Sound Illegal (But Technically Aren't)",
    "{n} Money Hacks That Sound Too Good To Be Legal",
    "{n} 'Money Glitches' That Sound Illegal But Actually Aren't",
    "I Found {n} Money Glitches That Sound Illegal",
    "{n} Legal Money Loopholes That Sound Like Scams",
    "{n} Get-Rich 'Glitches' That Sound Illegal (But Are Technically Legal)",
]


def make_meta(subset):
    n = len(subset)
    title = random.choice(TITLES).format(n=n)[:100]
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
