import os
import time
import json
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded, ServiceUnavailable

def _load_api_keys():
    keys = []
    raw = os.getenv("GEMINI_API_KEYS", "")
    if raw.strip():
        keys.extend([k.strip() for k in raw.split(",") if k.strip()])
    single = os.getenv("GEMINI_API_KEY", "").strip()
    if single and single not in keys:
        keys.append(single)
    out = []
    for k in keys:
        if k and k not in out:
            out.append(k)
    return out

_API_KEYS = _load_api_keys()
print(f"🔑 Gemini keys detected: {len(_API_KEYS)}")

def _configure_with_key(key: str):
    genai.configure(api_key=key)

def _pause_seconds() -> float:
    val = os.getenv("GEMINI_SECONDS_PER_CALL", "").strip()
    if val:
        try:
            return max(float(val), 2.0)
        except:
            pass
    rpm = os.getenv("GEMINI_RPM_PER_KEY", "").strip()
    if rpm:
        try:
            r = float(rpm)
            if r > 0:
                return max(60.0 / r, 2.0)
        except:
            pass
    return 12.0

def _is_invalid_key_error(err: Exception) -> bool:
    msg = str(err).lower()
    return (
        "api key expired" in msg
        or "api_key_invalid" in msg
        or ("400" in msg and "api key" in msg and "invalid" in msg)
    )

def _try_generate(prompt: str) -> str:
    model = genai.GenerativeModel("gemini-1.5-flash")
    resp = model.generate_content(prompt)
    return (resp.text or "").strip()

def _generate_single_pass(prompt: str) -> str:
    """
    Try each key once (in order) for the same article.
    If all keys fail (429 or invalid), raise ResourceExhausted to let caller save & stop.
    """
    if not _API_KEYS:
        raise ResourceExhausted("No valid API keys configured.")
    pause = _pause_seconds()

    for idx, key in enumerate(_API_KEYS, start=1):
        _configure_with_key(key)
        if idx > 1:
            time.sleep(1.0)  # small breath when switching keys
        try:
            text = _try_generate(prompt)
            time.sleep(pause)
            return text
        except ResourceExhausted:
            print(f"⛽ Key #{idx} quota exhausted (429). Trying next…")
            continue
        except (DeadlineExceeded, ServiceUnavailable) as e:
            print(f"🌐 Transient error with key #{idx}: {e}. Trying next…")
            continue
        except Exception as e:
            if _is_invalid_key_error(e):
                print(f"⛔ Key #{idx} invalid/expired. Skipping…")
                continue
            print(f"❗ Generic error with key #{idx}: {e} → returning empty")
            time.sleep(pause)
            return ""

    raise ResourceExhausted("All keys exhausted or invalid for this article.")

def is_relevant_for_aura(article: dict) -> bool:
    prompt = f"""
You are a trends curator for a luxury lifestyle hotel (ME by Meliá, Málaga).
Is this news useful for guest conversation or experiences (fashion, art, gastronomy, lifestyle, wellness, luxury, culture, events)?
Answer ONLY with: true  or  false

Title: {article.get('title','')}
Summary: {article.get('summary','')}
Category: {article.get('category','')}
Link: {article.get('link','')}
""".strip()

    text = _generate_single_pass(prompt).lower()
    if "true" in text:
        return True
    if "false" in text:
        return False
    if text == "":
        return False
    print(f"[IA] Unexpected response: {text!r}")
    return False

def enrich_article_fields(article: dict) -> dict:
    """Return {'why_it_matters': str, 'activation_ideas': [str, ...]} or {} on failure."""
    prompt = f"""
You are a trends concierge for a luxury lifestyle hotel in Málaga (ME by Meliá).
Given the news item, write:
- A concise 2-3 sentence 'why_it_matters' tailored to a guest conversation.
- 3 short 'activation_ideas' (max 12 words each), practical, hotel-host friendly.

Return STRICT JSON with keys: why_it_matters (string), activation_ideas (array of strings). No prose before/after.

Title: {article.get('title','')}
Summary: {article.get('summary','')}
Category: {article.get('category','')}
Link: {article.get('link','')}
""".strip()

    try:
        raw = _generate_single_pass(prompt)
        if not raw:
            return {}
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if "json" in raw[:10].lower():
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw
        data = json.loads(raw)
        out = {}
        w = data.get("why_it_matters")
        if isinstance(w, str) and w.strip():
            out["why_it_matters"] = w.strip()
        ideas = data.get("activation_ideas")
        if isinstance(ideas, list):
            out["activation_ideas"] = [str(x).strip() for x in ideas if str(x).strip()][:5]
        return out
    except ResourceExhausted:
        raise
    except Exception as e:
        print(f"[IA] Enrichment parse error: {e}")
        return {}
