import os
import time
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

_ACTIVE_KEYS = _load_api_keys()
print(f"🔑 Claves Gemini detectadas: {len(_ACTIVE_KEYS)}")

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
    return 12.0  # MUY prudente

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

def _generate_with_rotation(prompt: str) -> str:
    """
    Reintenta el MISMO prompt rotando claves:
    - 429 (quota) → rota a la siguiente y reintenta MISMO artículo.
    - 400 (key inválida/expirada) → elimina la key y sigue con el MISMO artículo.
    - Timeouts/503 → breve backoff y reintento en misma key.
    - Si todas sin cuota o inválidas → ResourceExhausted.
    """
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
