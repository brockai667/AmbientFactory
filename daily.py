#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AmbientFactory denny beh: pre kazdu ZAPNUTU niku -> metadata -> render long-form -> upload -> uprac.
Stav v used.json. OAuth refresh token per nika (ENV YT_REFRESH_<NIKA> alebo config).

Pouzitie:
  python daily.py                 # vsetky zapnute niky (config.niches.*.enabled)
  python daily.py focus sleep     # len vybrane
"""
import json, os, random, sys, time
import metadata, make_longform
import youtube_upload as yt

ROOT = os.path.dirname(os.path.abspath(__file__))


def cfg():
    p = os.path.join(ROOT, "config.json")
    c = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    c["youtube_client_id"] = os.environ.get("YOUTUBE_CLIENT_ID", c.get("youtube_client_id", ""))
    c["youtube_client_secret"] = os.environ.get("YOUTUBE_CLIENT_SECRET", c.get("youtube_client_secret", ""))
    return c


def refresh_for(niche, c):
    env = os.environ.get(f"YT_REFRESH_{niche.upper()}")
    if env:
        return env
    return (c.get("niches", {}).get(niche, {}) or {}).get("youtube_refresh_token", "")


def _log(niche, title, vid):
    p = os.path.join(ROOT, "used.json")
    data = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []
    data.append({"niche": niche, "title": title, "video_id": vid, "ts": time.strftime("%Y-%m-%d %H:%M")})
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def main():
    c = cfg()
    niches = c.get("niches", {})
    want = [n for n in sys.argv[1:] if n in niches]
    selected = want or [n for n, v in niches.items() if v.get("enabled")]
    if not selected:
        print("ziadne zapnute niky v config.niches"); return
    for niche in selected:
        nc = niches[niche]; minutes = nc.get("minutes", 60); seed = random.randint(1, 10**6)
        print(f"=== {niche} ({minutes} min) seed={seed} ===")
        meta = metadata.make(niche, minutes, seed)
        out = make_longform.make(niche, minutes, seed=seed)
        jpg = out[:-4] + ".jpg"
        rtok = refresh_for(niche, c)
        if rtok and c["youtube_client_id"]:
            try:
                vid = yt.upload_video(out, meta, rtok, jpg=jpg,
                                      client_id=c["youtube_client_id"], client_secret=c["youtube_client_secret"])
                _log(niche, meta["title"], vid)
            except Exception as e:
                print(f"  UPLOAD ZLYHAL ({niche}):", e)
        else:
            print(f"  [pozn.] {niche}: chyba refresh token -> upload preskoceny (zatial len render)")
        try:                                        # uprac velky subor po uploade (setri disk)
            if rtok and os.path.exists(out):
                os.remove(out)
        except OSError:
            pass
    print("hotovo.")


if __name__ == "__main__":
    main()
