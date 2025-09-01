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
    # Fijamos 12s para ir muy por debajo del límite por minuto
    return 12.0

def _is_invalid_key_error(err: Exception) -> bool:
    msg = str(err).lower()
    return (
        "api key expired" in msg
        or "api_key_invalid" in msg
        or ("400" in msg and "api key" in msg and "invalid" in msg)
    )

# ─────────────────────────────────────────────────────────────
# Detección de tipo de 429 (minuto vs día) y retry_delay
# ─────────────────────────────────────────────────────────────
_PER_MINUTE_HINTS = (
    "RequestsPerMinute", "PerMinute", "PerMinutePerProject", "PerMinutePerProjectPerModel"
)
_PER_DAY_HINTS = (
    "RequestsPerDay", "PerDay", "PerDayPerProject"
)

_RETRY_DELAY_RX = re.compile(r"retry_delay\s*\{\s*seconds:\s*(\d+)", re.IGNORECASE)
def _classify_429(err: Exception):
    """
    Devuelve ('minute'|'day'|'unknown', retry_delay_seconds|None)
    """
    text = str(err)
    # retry_delay seconds
    m = _RETRY_DELAY_RX.search(text)
    retry_delay = int(m.group(1)) if m else None

    # mira quota_metric:
    # e.g. quota_metric: "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"
    if any(h in text for h in _PER_MINUTE_HINTS):
        return "minute", retry_delay
    if any(h in text for h in _PER_DAY_HINTS):
        return "day", retry_delay
    return "unknown", retry_delay

def _backoff_sleep(seconds: float):
    # Límite razonable
    seconds = max(1.0, min(float(seconds), 300.0))
    print(f"⏳ Backoff {seconds:.0f}s…", flush=True)
    time.sleep(seconds)

# ─────────────────────────────────────────────────────────────
# Llamada base a Gemini
# ─────────────────────────────────────────────────────────────
def _try_generate(prompt: str) -> str:
    model = genai.GenerativeModel("gemini-1.5-flash")
    resp = model.generate_content(prompt)
    return (resp.text or "").strip()

def _generate_single_pass(prompt: str) -> str:
    """
    Prueba cada clave en orden (máx. una vuelta), con reintentos en 429 por minuto.
    - 429 PerMinute → esperar retry_delay (o ~65s) y reintentar la misma clave (hasta 2 veces por clave).
    - 429 PerDay → marcar la clave como agotada para hoy y pasar a la siguiente.
    - 429 unknown → backoff corto (30s) y reintentar una vez.
    - Otras excepciones transitorias (timeout/503) → intentar siguiente clave.
    - Si ninguna clave sirve → ResourceExhausted.
    """
    if not _API_KEYS:
        raise ResourceExhausted("No valid API keys configured.")
    pause = _pause_seconds()
    daily_exhausted = set()

    for idx, key in enumerate(_API_KEYS, start=1):
        if key in daily_exhausted:
            continue

        _configure_with_key(key)
        if idx > 1:
            time.sleep(1.0)

        # Hasta 2 intentos por clave si el 429 es por minuto
        attempts_left = 2
        while attempts_left > 0:
            try:
                text = _try_generate(prompt)
                time.sleep(pause)
                return text

            except ResourceExhausted as e:
                scope, retry_delay = _classify_429(e)
                if scope == "minute":
                    # backoff recomendado o ~65s y reintentamos MISMA clave
                    wait_s = retry_delay + 2 if (retry_delay and retry_delay > 0) else 65
                    print(f"⛽ Key #{idx} 429 PerMinute. Esperando {wait_s}s y reintentando misma clave…", flush=True)
                    _backoff_sleep(wait_s)
                    attempts_left -= 1
                    continue  # reintenta misma clave

                if scope == "day":
                    print(f"⛽ Key #{idx} 429 PerDay. Marcada como agotada para hoy. Pasando a la siguiente…", flush=True)
                    daily_exhausted.add(key)
                    break  # salir del while → pasar a siguiente clave

                # unknown 429 → backoff corto y un reintento
                print(f"⛽ Key #{idx} 429 (scope desconocido). Backoff 30s y reintento…", flush=True)
                _backoff_sleep(30)
                attempts_left -= 1
                continue

            except (DeadlineExceeded, ServiceUnavailable) as e:
                print(f"🌐 Transient error con key #{idx}: {e}. Probando siguiente clave…", flush=True)
                break  # pasa a siguiente clave

            except Exception as e:
                if _is_invalid_key_error(e):
                    print(f"⛔ Key #{idx} inválida/expirada. Saltando…", flush=True)
                    break
                print(f"❗ Error genérico con key #{idx}: {e} → devolviendo vacío", flush=True)
                time.sleep(pause)
                return ""

    # Si llegamos aquí, ninguna clave pudo responder
    raise ResourceExhausted("All keys exhausted (minute and/or daily) for this article.")

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
