import os
import time
import json
import re
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded, ServiceUnavailable

# ─────────────────────────────────────────────────────────────
# Gestión de claves y ritmo
# ─────────────────────────────────────────────────────────────
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
    # Fijamos 12s para ir muy por debajo del límite
    return 12.0

def _is_invalid_key_error(err: Exception) -> bool:
    msg = str(err).lower()
    return (
        "api key expired" in msg
        or "api_key_invalid" in msg
        or ("400" in msg and "api key" in msg and "invalid" in msg)
    )

# ─────────────────────────────────────────────────────────────
# Llamada base a Gemini
# ─────────────────────────────────────────────────────────────
def _try_generate(prompt: str) -> str:
    model = genai.GenerativeModel("gemini-1.5-flash")
    resp = model.generate_content(prompt)
    return (resp.text or "").strip()

def _generate_single_pass(prompt: str) -> str:
    """
    Prueba cada clave en orden, máximo una vez.
    Si todas fallan → ResourceExhausted.
    """
    if not _API_KEYS:
        raise ResourceExhausted("No valid API keys configured.")
    pause = _pause_seconds()

    for idx, key in enumerate(_API_KEYS, start=1):
        _configure_with_key(key)
        if idx > 1:
            time.sleep(1.0)  # respiro al cambiar de clave
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
            print(f"❗ Error genérico con clave #{idx}: {e} → devolviendo vacío")
            time.sleep(pause)
            return ""

    raise ResourceExhausted("All keys exhausted or invalid for this article.")

# ─────────────────────────────────────────────────────────────
# Helpers de parsing
# ─────────────────────────────────────────────────────────────
_JSON_BLOCK_RX = re.compile(r"\{[\s\S]*\}", re.MULTILINE)

def _extract_json_block(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:].lstrip("\n\r ")
    m = _JSON_BLOCK_RX.search(s)
    return m.group(0).strip() if m else s

# ─────────────────────────────────────────────────────────────
# Clasificación (ES, prompt ligero)
# ─────────────────────────────────────────────────────────────
def is_relevant_for_aura(article: dict) -> bool:
    title = article.get('title','')
    summary = article.get('summary','')
    category = article.get('category','')
    link = article.get('link','')

    prompt = f"""
Eres curador de tendencias para ME by Meliá (Málaga).
Evalúa si esta noticia sirve para conversar con huéspedes o inspirar experiencias.

Di **true** solo si:
- Habla de Málaga, Costa del Sol, Andalucía o España (eventos, cultura, gastronomía, lifestyle, aperturas).
- O trata de marcas/tendencias de lujo internacionales de alto nivel (ej. Dior, LV, Hermès, Chanel, Michelin, 50 Best).
- O muestra novedades en gastronomía, wellness, arte o diseño aplicables a hoteles de lujo.

Di **false** si es demasiado local en otra ciudad, corporativo/financiero sin interés para huéspedes, o ajeno a lujo/experiencias.

Responde SOLO: true  o  false.

Título: {title}
Resumen: {summary}
Categoría: {category}
Enlace: {link}
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

# ─────────────────────────────────────────────────────────────
# Enriquecimiento (ES)
# ─────────────────────────────────────────────────────────────
def enrich_article_fields(article: dict) -> dict:
    title = article.get('title','')
    summary = article.get('summary','')
    category = article.get('category','')
    link = article.get('link','')

    prompt = f"""
Eres “Aura Host” en ME by Meliá (Málaga). Te paso una noticia y quiero:

1) "why_it_matters": 2–3 frases concisas (máx. 280 caracteres), en español,
   que expliquen por qué interesa a un huésped de lujo.
   - Si es de Málaga/España → destaca valor inmediato para la estancia.
   - Si es global → preséntala como tendencia de lujo reconocible.

2) "activation_ideas": 3 frases cortas en español (máx. 12 palabras),
   cada una empezando con un verbo (ej. "Recomendar…", "Sugerir…", "Invitar a…").
   - Si es local → aplicables en Málaga o dentro del hotel.
   - Si es global → sirven como conversación o inspiración en el servicio.

Devuelve SOLO JSON válido:

{{
  "why_it_matters": "texto breve en español",
  "activation_ideas": ["frase 1", "frase 2", "frase 3"]
}}

Título: {title}
Resumen: {summary}
Categoría: {category}
Enlace: {link}
""".strip()

    try:
        raw = _generate_single_pass(prompt)
        if not raw:
            return {}

        block = _extract_json_block(raw)
        data = json.loads(block)

        out = {}
        w = data.get("why_it_matters")
        if isinstance(w, str) and w.strip():
            out["why_it_matters"] = w.strip()

        ideas = data.get("activation_ideas")
        if isinstance(ideas, list):
            cleaned = [str(x).strip() for x in ideas if str(x).strip()]
            out["activation_ideas"] = cleaned[:5]

        return out
    except ResourceExhausted:
        raise
    except Exception as e:
        print(f"[IA] Enrichment parse error: {e}")
        return {}
