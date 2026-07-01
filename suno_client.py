#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Suno API klient (PLUGGABLE) -- generuj instrumentalnu hudbu cez API, stiahni do assets/music/.
Podporuje OFICIALNY Suno API aj kompatibilne third-party endpointy (sunoapi.org a pod.) cez 'profil'.

CESTNE:
  - OFICIALNY API = odporucane (legalne, stabilne). Kluc ziskas v Suno ucte (Developer/API sekcia).
  - Third-party reselleri = funguju, plat-za-generaciu, spoliehas sa na cudziu sluzbu.
  - Cookie-scraping wrappery (gcui-art/suno-api) = proti Suno ToS => RIZIKO BANU. Nie default.

  >>> Endpointy/poly NIZSIE over podla docs SVOJHO providera -- su zamerne pluggable. <<<

Kluc: NIKDY necommituj. Lokalne v config.json (gitignored), v cloude cez ENV SUNO_API_KEY.

Test:  python suno_client.py "calm felt piano, deep focus" "lofi, jazzy, soft, instrumental"
"""
import json, os, sys, time, requests

ROOT = os.path.dirname(os.path.abspath(__file__))

# --- profily providera: ako sa vola generate/status a ako sa cita odpoved (uprav podla docs) ---
PROVIDERS = {
    # vseobecny third-party tvar (sunoapi.org a klony gcui-art/suno-api)
    "generic": {
        "gen_path": "/api/generate",
        "payload": lambda prompt, style, instr: {
            "gpt_description_prompt": prompt, "tags": style,
            "make_instrumental": instr, "mv": "chirp-v4", "prompt": "",
        },
        "ids_from": lambda d: [c["id"] for c in (d if isinstance(d, list) else d.get("clips", d.get("data", [])))],
        "status_url": lambda base, ids: f"{base}/api/get?ids={','.join(ids)}",
        "clips_from": lambda d: d if isinstance(d, list) else d.get("clips", d.get("data", [])),
        "audio_of": lambda c: c.get("audio_url") or "",
        "ready": lambda c: bool(c.get("audio_url")) and c.get("status") in (None, "complete", "streaming"),
    },
    # OFICIALNY Suno API -- over presny tvar v ich docs a doplň
    "official": {
        "gen_path": "/v1/generate",
        "payload": lambda prompt, style, instr: {"prompt": prompt, "tags": style, "make_instrumental": instr},
        "ids_from": lambda d: [c["id"] for c in (d.get("clips", d) if isinstance(d, dict) else d)],
        "status_url": lambda base, ids: f"{base}/v1/clips?ids={','.join(ids)}",
        "clips_from": lambda d: d.get("clips", d) if isinstance(d, dict) else d,
        "audio_of": lambda c: c.get("audio_url") or "",
        "ready": lambda c: bool(c.get("audio_url")),
    },
}


def cfg():
    c = {}
    p = os.path.join(ROOT, "config.json")
    if os.path.exists(p):
        c = json.load(open(p, encoding="utf-8"))
    c["suno_api_key"] = os.environ.get("SUNO_API_KEY", c.get("suno_api_key", ""))
    c["suno_base_url"] = os.environ.get("SUNO_BASE_URL", c.get("suno_base_url", "https://api.sunoapi.org"))
    c["suno_provider"] = os.environ.get("SUNO_PROVIDER", c.get("suno_provider", "generic"))
    return c


def _prof_base_key(c):
    prof = PROVIDERS.get(c["suno_provider"])
    if not prof:
        raise SystemExit(f"CHYBA: neznamy suno_provider '{c['suno_provider']}' (generic|official)")
    if not c["suno_api_key"]:
        raise SystemExit("CHYBA: chyba suno_api_key (config.json alebo ENV SUNO_API_KEY)")
    return prof, c["suno_base_url"].rstrip("/"), c["suno_api_key"]


def generate(prompt, style="ambient, warm analog pads, peaceful, no drums, instrumental", instrumental=True, c=None):
    c = c or cfg()
    prof, base, key = _prof_base_key(c)
    r = requests.post(base + prof["gen_path"], timeout=60,
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                      json=prof["payload"](prompt, style, instrumental))
    r.raise_for_status()
    ids = prof["ids_from"](r.json())
    print(f"  zadane {len(ids)} klipov: {ids}")
    return ids


def wait_and_download(ids, out_dir, c=None, timeout=360, every=8):
    c = c or cfg()
    prof, base, key = _prof_base_key(c)
    os.makedirs(out_dir, exist_ok=True)
    done, t0 = {}, time.time()
    while len(done) < len(ids) and time.time() - t0 < timeout:
        r = requests.get(prof["status_url"](base, ids), timeout=60, headers={"Authorization": f"Bearer {key}"})
        r.raise_for_status()
        for clip in prof["clips_from"](r.json()):
            cid = clip.get("id")
            if cid and cid not in done and prof["ready"](clip):
                url = prof["audio_of"](clip)
                path = os.path.join(out_dir, f"suno_{str(cid)[:8]}.mp3")
                with requests.get(url, timeout=180, stream=True) as a:
                    a.raise_for_status()
                    with open(path, "wb") as f:
                        for chunk in a.iter_content(8192):
                            f.write(chunk)
                done[cid] = path
                print(f"  stiahnute: {os.path.basename(path)}")
        if len(done) < len(ids):
            time.sleep(every)
    if len(done) < len(ids):
        print(f"  [pozn.] hotovych {len(done)}/{len(ids)} (timeout/nedokoncene)")
    return list(done.values())


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "calm ambient pads for deep focus and sleep"
    style = sys.argv[2] if len(sys.argv) > 2 else "ambient, warm analog pads, peaceful, no drums, instrumental"
    ids = generate(prompt, style)
    files = wait_and_download(ids, os.path.join(ROOT, "assets", "music"))
    print("HOTOVO:", files)
