import os
import time
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded, ServiceUnavailable

# ---------------------------------------------------------------------
# Load API keys (supports GEMINI_API_KEYS="K1,K2,K3" and fallback GEMINI_API_KEY)
# ---------------------------------------------------------------------
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
print(f"Gemini keys detected: {len(_API_KEYS)}")

def _configure_with_key(key: str):
    genai.configure(api_key=key)

def _pause_seconds() -> float:
    # Default very conservative cadence: 12s per call
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
    Try each key once (in order) for the SAME article.
    - 429 quota: try next key.
    - 400 invalid/expired: skip that key and try next.
    - Timeout/503: try next key.
    If no key can answer: raise ResourceExhausted so the caller saves and stops.
    """
    if not _API_KEYS:
        raise ResourceExhausted("No valid API keys configured.")
    pause = _pause_seconds()

    for idx, key in enumerate(_API_KEYS, start=1):
        _configure_with_key(key)
        if idx > 1:
            time.sleep(1.0)  # short break when switching keys
        try:
            text = _try_generate(prompt)
            time.sleep(pause)
            return text
        except ResourceExhausted:
            print(f"Key #{idx} quota exhausted (429). Trying next…")
            continue
        except (DeadlineExceeded, ServiceUnavailable) as e:
            print(f"Transient error with key #{idx}: {e}. Trying next…")
            continue
        except Exception as e:
            if _is_invalid_key_error(e):
                print(f"Key #{idx} invalid/expired. Skipping…")
                continue
            # Other unexpected error: return empty so caller marks False and continues to next ARTICLE
            print(f"Generic error with key #{idx}: {e} -> mark False and continue to next article")
            time.sleep(pause)
            return ""

    # None of the keys could answer this article
    raise ResourceExhausted("All keys exhausted or invalid for this article.")

# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------
def is_relevant_for_aura(article: dict) -> bool:
    # Build prompt without triple quotes and only ASCII
    lines = [
        "You are a trends curator for a luxury lifestyle hotel (ME by Melia, Malaga).",
        "Is this news useful for guest conversation or experiences (fashion, art, gastronomy, lifestyle, wellness, luxury, culture, events)?",
        "Answer ONLY with: true or false",
        "",
        f"Title: {article.get('title','')}",
        f"Summary: {article.get('summary','')}",
        f"Category: {article.get('category','')}",
        f"Link: {article.get('link','')}",
    ]
    prompt = "\n".join(lines)

    text = _generate_single_pass(prompt).lower()
    if "true" in text:
        return True
    if "false" in text:
        return False
    if text == "":
        return False
    print(f"Unexpected model response: {text!r}")
    return False    """
    if not _API_KEYS:
        raise ResourceExhausted("No valid API keys configured.")
    pause = _pause_seconds()

    for idx, key in enumerate(_API_KEYS, start=1):
        _configure_with_key(key)
        if idx > 1:
            time.sleep(1.0)  # short break when switching keys
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
            print(f"❗ Generic error with key #{idx}: {e} → mark False and continue to next ARTICLE")
            time.sleep(pause)
            return ""

    raise ResourceExhausted("All keys exhausted or invalid for this article.")

# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
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
    return False    """
    if not _API_KEYS:
        raise ResourceExhausted("No valid API keys configured.")
    pause = _pause_seconds()

    for idx, key in enumerate(_API_KEYS, start=1):
        _configure_with_key(key)
        if idx > 1:
            time.sleep(1.0)  # short break when switching keys
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
            print(f"❗ Generic error with key #{idx}: {e} → mark False and continue to next ARTICLE")
            time.sleep(pause)
            return ""

    raise ResourceExhausted("All keys exhausted or invalid for this article.")

# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
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
    return False    - 400 (key inválida/expirada): salta esa clave y prueba la siguiente.
    - Timeout/503: pasa a la siguiente clave.
    - Si ninguna clave responde: lanza ResourceExhausted.
    """
    if not _API_KEYS:
        raise ResourceExhausted("No hay claves válidas configuradas.")
    pause = _pause_seconds()

    for idx, key in enumerate(_API_KEYS, start=1):
        _configure_with_key(key)
        if idx > 1:
            time.sleep(1.0)  # respiro al cambiar de key
        try:
            text = _try_generate(prompt)
            time.sleep(pause)
            return text
        except ResourceExhausted:
            print(f"⛽ Clave #{idx} agotada (429). Probando la siguiente…")
            continue
        except (DeadlineExceeded, ServiceUnavailable) as e:
            print(f"🌐 Error transitorio con clave #{idx}: {e}. Probando la siguiente…")
            continue
        except Exception as e:
            if _is_invalid_key_error(e):
                print(f"⛔ Clave #{idx} inválida/expirada. Saltando…")
                continue
            print(f"❗ Error genérico con clave #{idx}: {e} → marcar False y seguir con el siguiente ARTÍCULO")
            time.sleep(pause)
            return ""

    raise ResourceExhausted("Todas las claves agotadas/invalidas para este artículo.")

# ─────────────────────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────────────────────
def is_relevant_for_aura(article: dict) -> bool:
    prompt = f"""
Eres curador de tendencias para un hotel de lujo lifestyle (ME by Meliá, Málaga).
¿Esta noticia puede servir para conversación/experiencia (moda, arte, gastronomía, lifestyle, bienestar, lujo, cultura, eventos)?
Responde SOLO con: true  o  false

Título: {article.get('title','')}
Resumen: {article.get('summary','')}
Categoría: {article.get('category','')}
Enlace: {article.get('link','')}
""".strip()

    text = _generate_single_pass(prompt).lower()
    if "true" in text:
        return True
    if "false" in text:
        return False
    if text == "":
        return False
    print(f"[IA] Respuesta inesperada: {text!r}")
    return False
def _generate_single_pass(prompt: str) -> str:
    """
    PRUEBA CADA CLAVE 1 VEZ (en orden) PARA EL MISMO ARTÍCULO.
    - 429 (cuota): intenta la siguiente clave.
    - 400 (key inválida/expirada): salta esa clave y prueba la siguiente.
    - Timeout/503: pasa a la siguiente clave.
    - Si ninguna clave responde: lanza ResourceExhausted para que trend_probe.py GUARDE Y PARE.
    """
    if not _API_KEYS:
        raise ResourceExhausted("No hay claves válidas configuradas.")
    pause = _pause_seconds()

    for idx, key in enumerate(_API_KEYS, start=1):
        _configure_with_key(key)
        if idx > 1:
            time.sleep(1.0)  # respiro al cambiar de key
        try:
            text = _try_generate(prompt)
            time.sleep(pause)
            return text
        except ResourceExhausted:
            print(f"⛽ Clave #{idx} agotada (429). Probando la siguiente…")
            continue
        except (DeadlineExceeded, ServiceUnavailable) as e:
            print(f"🌐 Error transitorio con clave #{idx}: {e}. Probando la siguiente…")
            continue
        except Exception as e:
            if _is_invalid_key_error(e):
                print(f"⛔ Clave #{idx} inválida/expirada. Saltando…")
                continue
            # Otro error no clasificable → devolvemos vacío (el caller marcará False)
            print(f"❗ Error genérico con clave #{idx}: {e} → marcar False y seguir con el siguiente ARTÍCULO")
            time.sleep(pause)
            return ""

    # Ninguna clave pudo responder este artículo → que el caller guarde y corte
    raise ResourceExhausted("Todas las claves agotadas/invalidas para este artículo.")

# ─────────────────────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────────────────────
def is_relevant_for_aura(article: dict) -> bool:
    """
    True/False según relevancia.
    - Intenta el MISMO artículo con cada clave (una vez).
    - Si todas están agotadas/invalidas → ResourceExhausted (trend_probe.py guardará y parará).
    - En errores no críticos → False (conservador).
    """
    prompt = f"""
Eres curador de tendencias para un hotel de lujo lifestyle (ME by Meliá, Málaga).
¿Esta noticia puede servir para conversación/experiencia (moda, arte, gastronomía, lifestyle, bienestar, lujo, cultura, eventos)?
Responde SOLO con: true  o  false

Título: {article.get('title','')}
Resumen: {article.get('summary','')}
Categoría: {article.get('category','')}
Enlace: {article.get('link','')}
""".strip()

    text = _generate_single_pass(prompt).lower()
    if "true" in text:
        return True
    if "false" in text:
        return False
    if text == "":
        return False
    print(f"[IA] Respuesta inesperada: {text!r}")
    return False    """
    global _ACTIVE_KEYS
    if not _ACTIVE_KEYS:
        raise ResourceExhausted("No hay claves válidas configuradas.")

    pause = _pause_seconds()
    idx = 0

    while _ACTIVE_KEYS:  # seguirá intentando hasta quedar sin claves o lograr respuesta
        key = _ACTIVE_KEYS[idx % len(_ACTIVE_KEYS)]
        _configure_with_key(key)
        if idx > 0:
            time.sleep(1.0)  # respiro al cambiar de key

        try:
            text = _try_generate(prompt)
            time.sleep(pause)
            return text

        except ResourceExhausted as e:
            # Esta key llegó a 429 → prueba con la siguiente key para el MISMO artículo
            print("⛽ Clave agotada (429). Rotando…")
            idx += 1
            continue

        except (DeadlineExceeded, ServiceUnavailable) as e:
            # Error transitorio → backoff corto y reintenta MISMA key (mismo artículo)
            print(f"🌐 Error transitorio con la clave actual: {e}")
            time.sleep(2.0)
            continue

        except Exception as e:
            # Clave inválida/expirada → elimínala y sigue el MISMO artículo con otra key
            if _is_invalid_key_error(e):
                print("⛔ Clave inválida/expirada. Eliminando de la rotación…")
                try:
                    _ACTIVE_KEYS.remove(key)
                except ValueError:
                    pass
                idx = 0  # reinicia desde el principio de las claves restantes
                continue

            # Otro error no clasificable → devolvemos vacío; caller marcará False
            print(f"❗ Error genérico con la clave actual: {e}")
            time.sleep(pause)
            return ""

    # Si salimos del bucle, no quedan claves válidas/cuota
    raise ResourceExhausted("Sin claves válidas o con cuota disponible.")

def is_relevant_for_aura(article: dict) -> bool:
    prompt = f"""
Eres curador de tendencias para un hotel de lujo lifestyle (ME by Meliá, Málaga).
¿Esta noticia puede servir para conversación/experiencia (moda, arte, gastronomía, lifestyle, bienestar, lujo, cultura, eventos)?
Responde SOLO con: true  o  false

Título: {article.get('title','')}
Resumen: {article.get('summary','')}
Categoría: {article.get('category','')}
Enlace: {article.get('link','')}
""".strip()

    text = _generate_with_rotation(prompt).lower()
    if "true" in text:
        return True
    if "false" in text:
        return False
    if text == "":
        return False
    print(f"[IA] Respuesta inesperada: {text!r}")
    return False
