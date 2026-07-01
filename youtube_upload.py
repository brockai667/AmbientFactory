#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nahra dlhe ambient video na YouTube (Data API, RESUMABLE CHUNKED -> znesie 2-3 GB subory,
konstantna pamat). OAuth per-nika: zdielany CLIENT_ID/SECRET + refresh_token daneho kanala.
Secrets: ENV (cloud) alebo config.json (lokal)."""
import json, os, requests

ROOT = os.path.dirname(os.path.abspath(__file__))
CHUNK = 16 * 1024 * 1024   # 16 MB (nasobok 256 KB - poziadavka resumable uploadu)


def _cfg(key):
    v = os.environ.get(key)
    if v:
        return v
    p = os.path.join(ROOT, "config.json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8")).get(key.lower())
    return None


def access_token(cid, csec, rtok):
    r = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": cid, "client_secret": csec, "refresh_token": rtok, "grant_type": "refresh_token"})
    r.raise_for_status()
    return r.json()["access_token"]


def set_thumbnail(tok, vid, jpg):
    if not (vid and jpg and os.path.exists(jpg)):
        return
    with open(jpg, "rb") as f:
        requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                      headers={"Authorization": f"Bearer {tok}", "Content-Type": "image/jpeg"},
                      data=f.read(), timeout=120).raise_for_status()


def upload(tok, mp4, title, description, tags, category="10", privacy="public"):
    """resumable CHUNKED upload (category 10 = Music). Vracia video resource."""
    meta = {"snippet": {"title": title[:100], "description": description[:4900],
                        "tags": tags[:15], "categoryId": category},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}}
    init = requests.post(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Type": "video/*"},
        data=json.dumps(meta).encode("utf-8"), timeout=60)
    init.raise_for_status()
    up_url = init.headers["Location"]
    size = os.path.getsize(mp4); sent = 0
    with open(mp4, "rb") as f:
        while sent < size:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            end = sent + len(chunk) - 1
            r = requests.put(up_url, timeout=900, data=chunk,
                             headers={"Content-Length": str(len(chunk)),
                                      "Content-Range": f"bytes {sent}-{end}/{size}"})
            if r.status_code in (200, 201):
                return r.json()
            if r.status_code != 308:                  # 308 = Resume Incomplete (pokracuj)
                r.raise_for_status()
            sent += len(chunk)
            print(f"    upload {sent // (1024*1024)}/{size // (1024*1024)} MB")
    return {}


def upload_video(mp4, meta, refresh_token, jpg=None, client_id=None, client_secret=None):
    cid = client_id or _cfg("YOUTUBE_CLIENT_ID")
    csec = client_secret or _cfg("YOUTUBE_CLIENT_SECRET")
    if not (cid and csec and refresh_token):
        raise RuntimeError("Chybaju YouTube OAuth udaje (client id/secret/refresh token).")
    tok = access_token(cid, csec, refresh_token)
    print(f"  nahravam: {meta['title']}")
    res = upload(tok, mp4, meta["title"], meta["description"], meta["tags"])
    vid = res.get("id")
    print(f"  OK: https://www.youtube.com/watch?v={vid}")
    try:
        set_thumbnail(tok, vid, jpg)
        print("  thumbnail nastaveny.")
    except Exception as e:
        print("  thumbnail preskoceny:", e)
    return vid
