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

_API_KEYS = _load_api_keys()
print(f"🔑 Claves Gemini detectadas: {len(_API_KEYS)}")

if _API_KEYS:
    genai.configure(api_key=_API_KEYS[0])
else:
    genai.configure(api_key="")

_current_idx = 0

def _set_key(i: int):
    global _current_idx
    if not _API_KEYS:
        return
    _current_idx = i % len(_API_KEYS)
    genai.configure(api_key=_API_KEYS[_current_idx])

def _pause_seconds() -> float:
    val = os.getenv("GEMINI_SECONDS_PER_CALL", "").strip()
    if val:
        try:
            s = float(val)
            return max(s, 2.0)
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

    return 12.0  # por defecto MUY prudente

def _try_generate(prompt: str) -> str:
    model = genai.GenerativeModel("gemini-1.5-flash")
    resp = model.generate_content(prompt)
    return (resp.text or "").strip()

def _generate_with_rotation(prompt: str, per_key_retries: int = 1) -> str:
    if not _API_KEYS:
        raise RuntimeError("No hay claves en el entorno (GEMINI_API_KEYS / GEMINI_API_KEY).")

    n = len(_API_KEYS)
    last_err = None

    for off in range(n):
        idx = (_current_idx + off) % n
        _set_key(idx)
        if off > 0:
            time.sleep(1.0)

        for attempt in range(per_key_retries):
            try:
                text = _try_generate(prompt)
                time.sleep(_pause_seconds())
                return text
            except ResourceExhausted as e:
                print(f"⛽ Clave #{idx+1} agotada (429). Rotando…")
                last_err = e
                break
            except (DeadlineExceeded, ServiceUnavailable) as e:
                print(f"🌐 Error transitorio con clave #{idx+1} (intento {attempt+1}): {e}")
                last_err = e
                time.sleep(2.0)
            except Exception as e:
                print(f"❗ Error genérico con clave #{idx+1}: {e}")
                time.sleep(_pause_seconds())
                return ""

    if isinstance(last_err, ResourceExhausted):
        raise last_err
    return ""

def is_relevant_for_aura(article: dict) -> bool:
    prompt = f"""
Eres curador de tendencias para un hotel de lujo lifestyle (ME by Meliá, Málaga).
¿Esta noticia puede servir para conversación/experiencia (moda, arte, gastronomía, lifestyle, bienestar, eventos, lujo, cultura)?
Responde SOLO con: true  o  false

Título: {article.get('title','')}
Resumen: {article.get('summary','')}
Categoría: {article.get('category','')}
Enlace: {article.get('link','')}
""".strip()

    try:
        text = _generate_with_rotation(prompt).lower()
        if "true" in text:
            return True
        if "false" in text:
            return False
        if text == "":
            return False
        print(f"[IA] Respuesta inesperada: {text!r}")
        return False

    except ResourceExhausted as e:
        raise e
