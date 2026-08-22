# -*- coding: utf-8 -*-
"""Auto-generovanie money-glitch schem cez LLM (GitHub Models) s TVRDOU kontrolou kvality.
Aby boli VZDY dobre a nikdy sa neopakovali:
  1) LLM vrati JEDNODUCHY PLOCHY format (cap, vo, icon, num?, col?) - lahke dodrzat -> vysoka uspesnost,
  2) validate() odvodi layout z ikony ('mascot'->mascot, 'loop'->loop diagram, inak icon+cislo),
     coerce nevalidnych ikon, bookendy=mascot, kazde vo=1 veta (SentenceBoundary),
  3) druhy LLM 'sudca': logic/funny/payoff >=3 inak reject,
  4) dedup proti avoid-listu (stopword-filter aby nefalsoval na 'money/make/cash'),
  5) ak COKOLVEK zlyha -> None -> glitch_daily fallbackne na rucnu banku (nikdy nespadne).
Token: ENV MODELS_TOKEN alebo GITHUB_TOKEN (Actions s permission models:read)."""
import os, json, re, time, urllib.request, urllib.error
from glitch_engine import ICONS

MODEL = os.environ.get("GLITCH_MODEL") or os.environ.get("MODELS_MODEL", "openai/gpt-oss-120b")
FALLBACK = os.environ.get("MODELS_FALLBACK", "openai/gpt-oss-20b")     # Groq 8/2026: Llama modely vyradene
ENDPOINT = os.environ.get("MODELS_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/") + "/chat/completions"
ICON_NAMES = set(ICONS.keys())

def _token():
    return os.environ.get("MODELS_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""

FALLBACK2 = os.environ.get("MODELS_FALLBACK2", "groq/compound-mini")


def _msg_text(m):
    return (m.get("content") or "").strip() or (m.get("reasoning") or "").strip()


def call_model(messages, temperature=0.9, max_tokens=1500, tries=3, json_mode=False):
    tok = _token()
    if not tok:
        return None
    if json_mode:
        messages = list(messages) + [{"role": "system", "content":
            "Respond with ONLY a single valid JSON object. No prose, no markdown fences, no reasoning."}]
    for model in (MODEL, FALLBACK, FALLBACK2):
        payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        if model.startswith("openai/gpt-oss"):
            payload["reasoning_effort"] = "low"          # reasoning inak zozerie max_tokens -> prazdny content
        body = json.dumps(payload).encode()
        waited = False
        for i in range(tries):
            try:
                req = urllib.request.Request(ENDPOINT, data=body,
                    headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json",
                             "User-Agent": "MoneyGlitch/1.0 (+github actions)"})
                r = json.loads(urllib.request.urlopen(req, timeout=70).read().decode())
                txt = _msg_text(r["choices"][0]["message"])
                if txt:
                    return txt
                print(f"  [gen] {model}: prazdna odpoved"); break
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="replace")[:160]
                print(f"  [gen] {model} HTTP {e.code}: {msg}")
                if e.code == 404:
                    break
                if e.code == 429:
                    if not waited:
                        waited = True; time.sleep(65); continue   # TPM okno -> pockaj, ten isty model
                    break
                time.sleep(3 * (i + 1))
            except Exception as e:
                print("  [gen] model err:", str(e)[:90]); time.sleep(3 * (i + 1))
    return None
    if json_mode:
        # gpt-oss cez Groq: striktny json_object mode hadze 400 -> JSON len promptom, _extract() ho vylusti
        messages = list(messages) + [{"role": "system", "content":
            "Respond with ONLY a single valid JSON object. No prose, no markdown fences, no reasoning."}]
    for model in (MODEL, FALLBACK):                  # primar -> fallback (iny quota bucket / ak model zmizne)
        payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        body = json.dumps(payload).encode()
        for i in range(tries):
            try:
                req = urllib.request.Request(ENDPOINT, data=body,
                    headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json",
                             "User-Agent": "MoneyGlitch/1.0 (+github actions)"})   # bez UA = Cloudflare 403 (1010)
                r = json.loads(urllib.request.urlopen(req, timeout=70).read().decode())
                return r["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="replace")[:160]
                print(f"  [gen] {model} HTTP {e.code}: {msg}")
                if e.code in (404, 429, 413):        # model prec / kvota vycerpana -> ROVNO fallback (iny bucket)
                    break
                time.sleep(3 * (i + 1))
            except Exception as e:
                print("  [gen] model err:", str(e)[:90]); time.sleep(3 * (i + 1))
    return None
    for model in (MODEL, FALLBACK):                  # primar -> fallback (iny quota bucket / ak model zmizne)
        payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        # gpt-oss cez Groq: striktny json_object mode hadze 400 "Failed to validate JSON" (model
        # obaluje JSON textom/reasoningom) -> JSON NEvynucujeme, pytame ho v prompte a _extract() ho vylusti
        if json_mode:
            messages = messages + [{"role": "system", "content": "Respond with ONLY a single valid JSON object. No prose, no markdown fences, no reasoning."}]
        body = json.dumps(payload).encode()
        for i in range(tries):
            try:
                req = urllib.request.Request(ENDPOINT, data=body,
                    headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json",
                             "User-Agent": "MoneyGlitch/1.0 (+github actions)"})   # bez UA = Cloudflare 403 (1010)
                r = json.loads(urllib.request.urlopen(req, timeout=70).read().decode())
                return r["choices"][0]["message"]["content"]
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="replace")[:160]
                print(f"  [gen] {model} HTTP {e.code}: {msg}")
                if e.code == 404:                    # model neexistuje -> rovno fallback
                    break
                time.sleep(3 * (i + 1))
            except Exception as e:
                print("  [gen] model err:", str(e)[:90]); time.sleep(3 * (i + 1))
    return None

SYS = ("You are head writer for a viral deadpan-comedy short-form channel called 'Money Glitch'. "
       "Each video is an ABSURD but internally-LOGICAL get-rich-quick 'money glitch', narrated by a tired deadpan man. "
       "The humor: every step sounds like real financial logic, chained to a ridiculous conclusion, delivered totally straight.\n"
       "RULES:\n"
       "- MECHANISM must be a REAL concept pushed to an absurd extreme (currency hyperinflation, coin melt value, "
       "credit-card cashback loops, compounding interest, precious metals in e-waste, bottle-deposit arbitrage, bulk resale, "
       "collectible appreciation, tax loopholes...). The math must ROUGHLY hold — NO obvious holes.\n"
       "- Confident 'here's the hack' tone: imperatives (Get, Buy, Melt, Sell) + 'you'll make $X' + confident payoff. "
       "NEVER undercut it with 'but it doesn't work' or 'it's impossible'.\n"
       "- Numbers ESCALATE to one big final dollar payoff.\n"
       "- 8 to 10 steps. First and last step icon MUST be 'mascot'.\n"
       "- Each step: cap = short on-screen caption (<=30 chars); vo = ONE flowing spoken sentence connecting to the next "
       "(never fragments, never two sentences).")

FEWSHOT = (
 '{"title":"How to make $73,000 a year buying absolutely nothing","steps":['
 '{"cap":"Make $73,000 a year.","vo":"Here\'s how to make seventy three thousand dollars a year.","icon":"mascot"},'
 '{"cap":"Get a 2% cashback card.","vo":"First, get a credit card that pays you two percent cash back.","icon":"card","num":"2% back","col":"green"},'
 '{"cap":"Buy $10,000 in gift cards.","vo":"Use it to buy ten thousand dollars in gift cards.","icon":"gift","num":"$10,000","col":"red"},'
 '{"cap":"Turn them into money orders.","vo":"Then turn those gift cards into money orders.","icon":"order"},'
 '{"cap":"Deposit them at the bank.","vo":"Deposit the money orders straight into your bank account.","icon":"cash"},'
 '{"cap":"$10,000 in a perfect circle.","vo":"You just moved ten thousand dollars in a perfect circle.","icon":"loop"},'
 '{"cap":"The bank paid you $200.","vo":"And the bank just paid you two hundred dollars to do it.","icon":"cash","num":"$200","col":"green"},'
 '{"cap":"Every day = $73,000/yr.","vo":"Do that every single day, and that is seventy three thousand a year.","icon":"cash","num":"$73,000","col":"green"},'
 '{"cap":"...for buying nothing.","vo":"For buying absolutely nothing.","icon":"mascot"}]}')

def _extract(txt):
    """Vylusti prvy validny JSON objekt z textu (gpt-oss rado obali JSON reasoningom / ```json fences /
    prida dalsie {} v texte). Skusi: (1) fenced blok, (2) kazdy vyvazeny {...} usek zlava, (3) trailing-comma fix."""
    txt = txt or ""
    cands = []
    for m in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", txt, re.S):
        cands.append(m.group(1))
    starts = [i for i, ch in enumerate(txt) if ch == "{"]
    for s in starts[:12]:
        depth = 0; instr = False; esc = False
        for j in range(s, len(txt)):
            ch = txt[j]
            if instr:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    instr = False
                continue
            if ch == '"':
                instr = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    cands.append(txt[s:j + 1]); break
    for cand in cands:
        for c in (cand, re.sub(r",\s*([}\]])", r"\1", cand)):
            try:
                j = json.loads(c)
                if isinstance(j, dict):
                    return j
            except Exception:
                continue
    return None

def _one_sentence(vo):
    vo = re.sub(r"\s+", " ", str(vo)).strip()
    vo = re.sub(r"\.\s+(?=[A-Za-z0-9])", ", ", vo)
    if not vo.endswith((".", "!", "?")):
        vo += "."
    return vo

def validate(sc):
    if not isinstance(sc, dict):
        return None
    steps = sc.get("steps"); title = sc.get("title")
    if not (isinstance(title, str) and isinstance(steps, list) and 6 <= len(steps) <= 12):
        return None
    out = []
    for st in steps:
        if not isinstance(st, dict):
            return None
        cap = str(st.get("cap", "")).strip()[:40]; vo = str(st.get("vo", "")).strip()
        if not cap or not vo:
            return None
        ic = str(st.get("icon", "")).strip().lower()
        step = {"cap": cap, "vo": _one_sentence(vo)}
        if ic == "mascot":
            step["layout"] = "mascot"
        elif ic == "loop":
            step["layout"] = "loop"; step["loop"] = ["card", "coin", "cash", "bag"]
        else:
            step["layout"] = "icon"; step["icon"] = ic if ic in ICON_NAMES else "cash"
        if st.get("num") and step["layout"] != "mascot":
            step["num"] = str(st["num"])[:16]
            step["col"] = st.get("col") if st.get("col") in ("red", "green", "ink") else "green"
        out.append(step)
    out[0] = {"cap": out[0]["cap"], "vo": out[0]["vo"], "layout": "mascot"}
    out[-1] = {"cap": out[-1]["cap"], "vo": out[-1]["vo"], "layout": "mascot"}
    if not any(s.get("num") for s in out):
        return None
    sid = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40] or "gen"
    return {"id": "gen-" + sid, "title": title.strip()[:95], "steps": out}

def quality_ok(sc):
    msgs = [{"role": "system", "content": 'You judge deadpan-comedy "money glitch" scripts. Reply ONLY JSON '
             '{"logic":1-5,"funny":1-5,"payoff":1-5,"verdict":"ok"|"reject"}.'},
            {"role": "user", "content": "Title: " + sc["title"] + "\nCaptions: " +
             " | ".join(s["cap"] for s in sc["steps"]) +
             "\nRate logic(money-math roughly holds, no glaring hole), funny(absurd/deadpan), "
             "payoff(escalates to a big number). verdict=reject if any score < 3."}]
    j = _extract(call_model(msgs, temperature=0.2, max_tokens=120, json_mode=True) or "")
    if not j:
        return True
    if j.get("verdict") == "reject":
        return False
    return all(int(j.get(k, 3)) >= 3 for k in ("logic", "funny", "payoff"))

_STOP = set(("money make cash rich year into from with your turn how the and get you for that this quick free easy "
             "dollars dollar thousand thousands million millions billion trillion daily glitch make making profit").split())
def _sim(a, b):
    wa = set(re.findall(r"[a-z]{4,}", a.lower())) - _STOP
    wb = set(re.findall(r"[a-z]{4,}", b.lower())) - _STOP
    return len(wa & wb) >= 2

def generate(avoid=None, tries=4):
    """Nova validna+kvalitna schema (dict) alebo None (fallback na banku)."""
    if not _token():
        return None
    avoid = [a for a in (avoid or []) if a]
    icons = ", ".join(sorted(ICON_NAMES))
    for _k in range(tries):
        if _k: time.sleep(12)
        user = ("Each step is a flat object: {\"cap\":\"...\",\"vo\":\"...\",\"icon\":\"NAME\"} plus optional "
                "\"num\":\"$X\" and \"col\":\"red\"|\"green\". "
                f"icon must be one of: mascot, loop, {icons}. Use icon \"mascot\" for the FIRST and LAST step, "
                "and icon \"loop\" for a repeating-cycle step. Put the money-math on steps via num (red=scary quantity, "
                "green=dollar payoff).\n"
                f"Example (copy this shape EXACTLY):\n{FEWSHOT}\n\n"
                "Now write ONE brand-new money-glitch scheme as a single JSON object in that EXACT flat shape, 8-10 steps. "
                f"Do NOT reuse these mechanisms/titles: {', '.join(avoid[:30]) or 'none'}.")
        sc = validate(_extract(call_model(
            [{"role": "system", "content": SYS}, {"role": "user", "content": user}],
            temperature=0.95, json_mode=True) or ""))
        if not sc:
            continue
        if any(_sim(sc["title"], a) for a in avoid):
            continue
        if not quality_ok(sc):
            continue
        print("  [gen] nova schema:", sc["title"])
        return sc
    return None

if __name__ == "__main__":
    sc = generate(["manufactured spending", "copper pennies", "vending machines"])
    print(json.dumps(sc, indent=2, ensure_ascii=False) if sc else "GEN FAILED (fallback na banku)")
