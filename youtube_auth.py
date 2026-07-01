#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JEDNORAZOVE per kanal: prihlasi YouTube BRAND kanal a ziska jeho REFRESH TOKEN.
Pouzitie:  python youtube_auth.py <niche>      # napr. python youtube_auth.py focus

Cita youtube_client_id/secret z config.json (Desktop OAuth klient, YouTube Data API zapnute).
V prehliadaci VYBER SPRAVNY brand kanal (napr. Lull Focus) a klikni Allow.
Token sa ULOZI do config.json -> niches.<niche>.youtube_refresh_token (gitignored)."""
import json, os, sys, time, urllib.parse, threading, webbrowser, requests
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 8724
REDIRECT = f"http://localhost:{PORT}"
SCOPE = "https://www.googleapis.com/auth/youtube.upload"
_got = {}


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _got["code"] = q.get("code", [None])[0]; _got["error"] = q.get("error", [None])[0]
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
        self.wfile.write("<h2>Hotovo. Zatvor okno a vrat sa do terminalu.</h2>".encode("utf-8"))

    def log_message(self, *a):
        pass


def main():
    niche = sys.argv[1] if len(sys.argv) > 1 else "channel"
    cpath = os.path.join(ROOT, "config.json")
    cfg = json.load(open(cpath, encoding="utf-8")) if os.path.exists(cpath) else {}
    cid = cfg.get("youtube_client_id"); csec = cfg.get("youtube_client_secret")
    if not cid or not csec:
        print("CHYBA: do config.json daj youtube_client_id a youtube_client_secret"); return
    auth = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": REDIRECT, "response_type": "code",
        "scope": SCOPE, "access_type": "offline", "prompt": "select_account consent"})
    srv = HTTPServer(("localhost", PORT), H)
    threading.Thread(target=srv.handle_request, daemon=True).start()
    print(f"\n[{niche}] Otvaram prehliadac. VYBER brand kanal pre '{niche}' a klikni Allow...")
    try:
        webbrowser.open(auth)
    except Exception:
        print("Otvor manualne:\n", auth)
    for _ in range(300):
        if _got.get("code") or _got.get("error"):
            break
        time.sleep(1)
    srv.server_close()
    if _got.get("error") or not _got.get("code"):
        print("Zamietnute/timeout:", _got.get("error")); return
    r = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": cid, "client_secret": csec, "code": _got["code"],
        "grant_type": "authorization_code", "redirect_uri": REDIRECT})
    rt = r.json().get("refresh_token")
    if not rt:
        print("Nedostal som refresh_token. Odpoved:", r.json()); return
    cfg.setdefault("niches", {}).setdefault(niche, {})["youtube_refresh_token"] = rt
    json.dump(cfg, open(cpath, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nOK: refresh token pre '{niche}' ulozeny do config.json (niches.{niche}.youtube_refresh_token)")
    print(f"   (do GitHub secrets pojde ako YT_REFRESH_{niche.upper()})")


if __name__ == "__main__":
    main()
