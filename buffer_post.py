# -*- coding: utf-8 -*-
"""Cross-post money-glitch reelu na TikTok + Instagram cez Buffer (YouTube ide priamo cez youtube_upload).
Tok: MP4 -> GitHub Release (public repo = free bandwidth, verejna URL) -> Buffer createPost na TikTok/IG
kanaly naplanovane na najblizsi slot. GRACEFUL: ak chyba buffer_token alebo buffer_channels -> ticho skip
(kym user nevytvori TikTok+IG ucty pre Money Glitch a neprepoji Buffer).
Vzor: FacelessFactory/push_to_buffer.py. Secrets cez ENV (BUFFER_TOKEN) / config."""
import os, sys, json, time, datetime
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
BUFFER_API = "https://api.buffer.com"
WANT = {"tiktok", "instagram"}
SLOT_HOURS = [8, 15, 20]

def next_slot():
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Europe/Bratislava")
    except Exception:
        tz = datetime.timezone(datetime.timedelta(hours=2))
    now = datetime.datetime.now(tz)
    for day in range(3):
        for h in SLOT_HOURS:
            t = (now + datetime.timedelta(days=day)).replace(hour=h, minute=0, second=0, microsecond=0)
            if t > now:
                return t.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return None

def gql(token, query, variables=None, attempts=3):
    last = None
    for a in range(attempts):
        try:
            r = requests.post(BUFFER_API, timeout=60,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"query": query, "variables": variables or {}})
            d = r.json()
            if "errors" in d:
                raise RuntimeError(json.dumps(d["errors"])[:300])
            return d["data"]
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last = e; time.sleep(2 * (a + 1))
    raise last

def _mutation(service):
    base = "$channelId: ChannelId!, $text: String!, $url: String!, $dueAt: DateTime!"
    if service == "instagram":
        return f"""mutation({base}) {{ createPost(input: {{ channelId: $channelId, text: $text,
          schedulingType: automatic, mode: customScheduled, dueAt: $dueAt, assets: [{{ video: {{ url: $url }} }}],
          metadata: {{ instagram: {{ type: reel, shouldShareToFeed: true }} }} }})
          {{ ... on PostActionSuccess {{ post {{ id }} }} ... on MutationError {{ message }} }} }}""", False
    return f"""mutation({base}, $title: String!) {{ createPost(input: {{ channelId: $channelId, text: $text,
      schedulingType: automatic, mode: customScheduled, dueAt: $dueAt, assets: [{{ video: {{ url: $url }} }}],
      metadata: {{ tiktok: {{ title: $title }} }} }})
      {{ ... on PostActionSuccess {{ post {{ id }} }} ... on MutationError {{ message }} }} }}""", True

def create_post(token, service, channel_id, text, url, title, due):
    q, use_title = _mutation(service)
    v = {"channelId": channel_id, "text": text, "url": url, "dueAt": due}
    if use_title:
        v["title"] = title
    for a in range(2):
        try:
            res = gql(token, q, v)["createPost"]
            if res.get("message"):
                last = res["message"]
            else:
                return True, ""
        except Exception as e:
            last = str(e)
        if a == 0:
            time.sleep(3)
    return False, last

def upload_github_release(path):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY") or os.environ.get("GH_REPO", "")
    if not (token and repo):
        raise RuntimeError("chyba GITHUB_TOKEN/GITHUB_REPOSITORY pre Release hosting")
    api = "https://api.github.com"; H = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json"}
    r = requests.get(f"{api}/repos/{repo}/releases/tags/media", headers=H, timeout=30)
    if r.status_code == 404:
        r = requests.post(f"{api}/repos/{repo}/releases", headers=H, timeout=30,
            json={"tag_name": "media", "name": "media assets", "body": "auto-host pre Buffer", "prerelease": True})
    r.raise_for_status(); rel = r.json(); assets = rel.get("assets", []); name = os.path.basename(path)
    for a in assets:
        if a.get("name") == name:
            requests.delete(f"{api}/repos/{repo}/releases/assets/{a['id']}", headers=H, timeout=30)
    old = sorted([a for a in assets if a.get("name") != name], key=lambda a: a.get("created_at", ""))
    for a in (old[:-40] if len(old) > 40 else []):
        requests.delete(f"{api}/repos/{repo}/releases/assets/{a['id']}", headers=H, timeout=30)
    up = rel["upload_url"].split("{")[0]
    with open(path, "rb") as f:
        ur = requests.post(up + "?name=" + name,
            headers={"Authorization": "Bearer " + token, "Content-Type": "video/mp4"}, data=f.read(), timeout=900)
    ur.raise_for_status(); return ur.json()["browser_download_url"]

def discover_channels(token):
    """Samo-objavi pripojene TikTok+IG kanaly priamo z Buffer tokenu (ZIADNE manualne profile IDs netreba).
    Staci nastavit BUFFER_TOKEN -> najde vsetky IG/TikTok kanaly na ucte."""
    orgs = (gql(token, "query { account { organizations { id } } }").get("account") or {}).get("organizations") or []
    out, seen = [], set()
    for o in orgs:
        oid = o.get("id")
        if not oid:
            continue
        data = gql(token, "query($input: ChannelsInput!){ channels(input:$input){ id name service type isDisconnected } }",
                   {"input": {"organizationId": oid}})
        for c in (data.get("channels") or []):
            svc = (c.get("service") or "").lower()
            if svc in WANT and not c.get("isDisconnected") and c.get("id") and c["id"] not in seen:
                seen.add(c["id"]); out.append({"id": c["id"], "service": svc, "name": c.get("name", "")})
    return out

def post_social(cfg, mp4, title, body):
    """Hostuje video + naplanuje na TikTok/IG cez Buffer. GRACEFUL skip ak nie je nakonfigurovane.
    Kanaly: z config.buffer_channels ak su, INAK sa SAMO-OBJAVIA z tokenu (staci nastavit BUFFER_TOKEN)."""
    token = (cfg.get("buffer_token") or os.environ.get("BUFFER_TOKEN") or "").strip()
    channels = [c for c in (cfg.get("buffer_channels") or []) if c.get("service", "").lower() in WANT and c.get("id")]
    if token and not channels:                                  # ziadne rucne IDs -> objav ich sam z tokenu
        try:
            channels = discover_channels(token)
            if channels:
                print("  [Buffer] auto-objavene kanaly:", ", ".join(f"{c['service']}:{c['name']}" for c in channels))
        except Exception as e:
            print("  [Buffer] auto-discovery zlyhalo:", str(e)[:140])
    if not token or not channels:
        print("  [Buffer] TikTok/IG preskocene (chyba BUFFER_TOKEN alebo ziadne pripojene TikTok/IG kanaly)"); return
    try:
        url = upload_github_release(mp4)
    except Exception as e:
        print("  [Buffer] hosting zlyhal:", str(e)[:140]); return
    due = next_slot()
    for c in channels:
        svc = c["service"].lower()
        ok, msg = create_post(token, svc, c["id"], body, url, title, due)
        print(f"  [Buffer/{svc}] {'do fronty OK (' + str(due) + ')' if ok else 'CHYBA: ' + str(msg)[:120]}")

if __name__ == "__main__":
    # lokalny dry: overi token + (auto-objavi) kanaly
    import glitch_daily as gd
    c = gd.cfg(); tok = (c.get("buffer_token") or os.environ.get("BUFFER_TOKEN") or "").strip()
    print("buffer_token:", "ANO" if tok else "NIE")
    ch = c.get("buffer_channels") or []
    if tok and not ch:
        try:
            ch = discover_channels(tok)
        except Exception as e:
            print("auto-discovery err:", str(e)[:200])
    print("kanaly:", ch or "(ziadne)")
