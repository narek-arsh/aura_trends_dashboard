# trend_probe.py

import os
import sys
import json
from app.utils.parser import load_feeds, fetch_articles_from_feeds
from app.utils.ai_filter import is_relevant_for_aura

DATA_DIR = "data"
CURATED_PATH = os.path.join(DATA_DIR, "curated.json")
TRENDS_PATH  = os.path.join(DATA_DIR, "trends.json")

os.makedirs(DATA_DIR, exist_ok=True)

def _read_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[!] No pude leer {path}: {e} → reinicio formato.")
    return default

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _normalize_curated(obj):
    """
    Acepta los formatos antiguos y los convierte a dict {id: bool}.
    - []                            -> {}
    - ["id1","id2"]                 -> {"id1": False, "id2": False}
    - [{"id":"..."}]                -> {"...": False}
    - [{"id":"...","relevante":T}]  -> {"...": True}
    - dict                          -> se deja tal cual
    """
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, list):
        out = {}
        for item in obj:
            if isinstance(item, str):
                out[item] = False
            elif isinstance(item, dict) and "id" in item:
                val = item.get("relevante")
                if isinstance(val, bool):
                    out[item["id"]] = val
                else:
                    out[item["id"]] = False
        return out
    return {}

def _normalize_trends(obj):
    return obj if isinstance(obj, list) else []

# --- Inicio ---
print("🧪 GEMINI_API_KEY presente:", bool(os.getenv("GEMINI_API_KEY")))

print("[+] Cargando feeds...")
feeds_by_category = load_feeds()
if not feeds_by_category:
    print("[❌] No hay feeds cargados. Revisa config/feeds.yaml (indentación y clave 'feeds:').")
    sys.exit(1)

print("[+] Recogiendo artículos...")
articles = fetch_articles_from_feeds(feeds_by_category, per_category=60)
print(f"[+] Artículos obtenidos: {len(articles)}")

# Cargar progreso previo (tolerante a formatos antiguos)
curated_raw = _read_json(CURATED_PATH, default={})
trends_raw  = _read_json(TRENDS_PATH,  default=[])

curated = _normalize_curated(curated_raw)   # dict {id: bool}
trends  = _normalize_trends(trends_raw)     # list[article dict]

procesados_nuevos = 0

for art in articles:
    art_id = art.get("id") or art.get("link") or art.get("title")
    if not art_id:
        print("[!] Artículo sin ID/link/título. Saltado.")
        continue
    if art_id in curated:
        # Ya evaluado previamente
        continue

    title = art.get("title", "Sin título")
    print(f"[IA] Evaluando: {title[:90]}")

    try:
        is_rel = is_relevant_for_aura(art)  # debe devolver True/False
        curated[art_id] = bool(is_rel)
        if is_rel:
            trends.append(art)
            print(f"[✓] Relevante: {title[:60]}")
        else:
            print(f"[✗] Descartada: {title[:60]}")
        procesados_nuevos += 1

    except Exception as e:
        msg = str(e).lower()
        # Manejo de cuota/429
        if "429" in msg or "quota" in msg or "resourceexhausted" in msg:
            print(f"[⛔] Cuota de Gemini alcanzada: {e}")
            print("[💾] Guardando progreso y saliendo…")
            _save_json(CURATED_PATH, curated)
            _save_json(TRENDS_PATH, trends)
            sys.exit(0)

        print(f"[!] Error con el artículo: {e}")
        curated[art_id] = False

    # Guardado incremental tras cada artículo
    _save_json(CURATED_PATH, curated)
    _save_json(TRENDS_PATH, trends)

print(f"[✅] Proceso completado. Nuevos procesados: {procesados_nuevos}")
