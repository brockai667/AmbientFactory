# -*- coding: utf-8 -*-
"""Jednorazovy rebrand YouTube kanalov na 'Money Glitch': nastavi TITLE (meno) + DESCRIPTION (popis)
cez YouTube Data API (channels.update, part=brandingSettings). Spusta sa v Actions (tam su tokeny).
POZN: avatar/foto sa cez API NEDA (len Studio). Meno (title) moze byt read-only pri Brand uctoch -> log ukaze."""
import os, json, requests

CID = os.environ["YOUTUBE_CLIENT_ID"]; CSEC = os.environ["YOUTUBE_CLIENT_SECRET"]
TITLE = "Money Glitch"
DESC = ("Your daily dose of absurd money 'glitches'.\n\n"
        "Every day, one ridiculous but weirdly logical get-rich-quick scheme, explained with a completely straight face.\n\n"
        "Satire and entertainment only - this is NOT financial advice. (Please don't actually melt any coins.)\n\n"
        "New video every single day.")

def access(rtok):
    r = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": CID, "client_secret": CSEC, "refresh_token": rtok, "grant_type": "refresh_token"})
    r.raise_for_status(); return r.json()["access_token"]

for niche in ("focus", "study", "sleep"):
    rtok = os.environ.get("YT_REFRESH_" + niche.upper())
    if not rtok:
        print(f"[{niche}] ziadny token -> skip"); continue
    try:
        tok = access(rtok); H = {"Authorization": "Bearer " + tok}
        g = requests.get("https://www.googleapis.com/youtube/v3/channels",
                         params={"part": "brandingSettings,snippet", "mine": "true"}, headers=H, timeout=30).json()
        if not g.get("items"):
            print(f"[{niche}] channels.list vratilo nic: {json.dumps(g)[:160]}"); continue
        it = g["items"][0]; cid = it["id"]; cur = it["snippet"]["title"]
        body = {"id": cid, "brandingSettings": {"channel": {"title": TITLE, "description": DESC}}}
        up = requests.put("https://www.googleapis.com/youtube/v3/channels",
                          params={"part": "brandingSettings"}, headers={**H, "Content-Type": "application/json"},
                          data=json.dumps(body), timeout=30)
        if up.status_code < 400:
            new = up.json().get("brandingSettings", {}).get("channel", {})
            print(f"[{niche}] {cid} '{cur}' -> UPDATE OK; title now: '{new.get('title')}' | desc set: {bool(new.get('description'))}")
        else:
            print(f"[{niche}] {cid} '{cur}' -> UPDATE FAIL HTTP {up.status_code}: {up.text[:220]}")
    except Exception as e:
        print(f"[{niche}] ERR: {str(e)[:200]}")
print("done.")
