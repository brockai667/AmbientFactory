#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deploy AmbientFactory do PUBLIC GitHub repa + nastav Actions secrets + push.
Spustaj az ked su v config.json 3 refresh tokeny (po youtube_auth.py).

ENV:  GITHUB_PAT = osobny token (repo + workflow scope)
Pouzitie:  GITHUB_PAT=ghp_... python deploy.py
"""
import base64, json, os, re, subprocess, sys
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
OWNER = "brockai667"
REPO = "AmbientFactory"
# token si sam ocisti: vytiahne cisty PAT aj ked okolo neho ostali uvodzovky/medzery/BOM
_pat_raw = os.environ.get("GITHUB_PAT", "")
_pat_m = re.search(r"(github_pat_[A-Za-z0-9_]+|gh[opsu]_[A-Za-z0-9]+)", _pat_raw)
PAT = _pat_m.group(1) if _pat_m else _pat_raw.strip()


def gh(method, path, **kw):
    r = requests.request(method, f"https://api.github.com{path}", timeout=60,
                         headers={"Authorization": f"Bearer {PAT}",
                                  "Accept": "application/vnd.github+json"}, **kw)
    return r


def secret_box(pubkey_b64, value):
    from nacl import public, encoding
    pk = public.PublicKey(pubkey_b64.encode(), encoding.Base64Encoder())
    sealed = public.SealedBox(pk).encrypt(value.encode())
    return base64.b64encode(sealed).decode()


def main():
    if not PAT:
        sys.exit("CHYBA: chyba GITHUB_PAT v ENV")
    print(f"[pat] dlzka={len(PAT)} spravny_prefix={PAT.startswith(('ghp_', 'github_pat_', 'gho_', 'ghs_', 'ghu_'))}")
    cfg = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
    cid = cfg.get("youtube_client_id"); csec = cfg.get("youtube_client_secret")
    niches = cfg.get("niches", {})
    # tokeny per nika
    secrets = {"YOUTUBE_CLIENT_ID": cid, "YOUTUBE_CLIENT_SECRET": csec}
    missing = []
    for n, v in niches.items():
        rt = v.get("youtube_refresh_token", "")
        if rt:
            secrets[f"YT_REFRESH_{n.upper()}"] = rt
        elif v.get("enabled"):
            missing.append(n)
    if missing:
        print(f"[pozn.] chybaju refresh tokeny pre: {missing} -> tie kanaly sa nenahraju (dobehni youtube_auth.py)")
    if not (cid and csec):
        sys.exit("CHYBA: chyba youtube_client_id/secret v config.json")

    # 1) repo (public)
    r = gh("GET", f"/repos/{OWNER}/{REPO}")
    if r.status_code == 404:
        print("vytváram repo (public)...")
        gh("POST", "/user/repos", json={"name": REPO, "private": False,
            "description": "Lull - ambient long-form (YouTube) + albums (Spotify), fully generated"}).raise_for_status()
    else:
        print("repo uz existuje.")

    # 2) secrets (sealed box)
    pk = gh("GET", f"/repos/{OWNER}/{REPO}/actions/secrets/public-key").json()
    for name, val in secrets.items():
        enc = secret_box(pk["key"], val)
        rr = gh("PUT", f"/repos/{OWNER}/{REPO}/actions/secrets/{name}",
                json={"encrypted_value": enc, "key_id": pk["key_id"]})
        print(f"  secret {name}: {rr.status_code}")

    # 3) push (config.json je gitignored -> tajomstva sa NEnahraju)
    url = f"https://{OWNER}:{PAT}@github.com/{OWNER}/{REPO}.git"
    cmds = [
        ["git", "init", "-q"],
        ["git", "add", "-A"],
        ["git", "-c", "user.name=brockai667", "-c", "user.email=brock.ia667@gmail.com",
         "commit", "-q", "-m", "AmbientFactory (Lull): multi-platform ambient factory"],
        ["git", "branch", "-M", "main"],
        ["git", "remote", "remove", "origin"],
        ["git", "remote", "add", "origin", url],
        ["git", "push", "-u", "-q", "--force", "origin", "main"],
    ]
    for c in cmds:
        rc = subprocess.run(c, cwd=ROOT).returncode
        if rc != 0 and c[1] not in ("remote",):   # remove origin moze zlyhat ak neexistuje
            print(f"[pozn.] '{' '.join(c[:2])}' rc={rc}")
    print(f"\nHOTOVO -> https://github.com/{OWNER}/{REPO}  (Actions cron bezi denne)")


if __name__ == "__main__":
    main()
