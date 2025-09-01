import os
import sys
import json
from app.utils.parser import load_feeds, fetch_articles_from_feeds
from app.utils.ai_filter import is_relevant_for_aura
from google.api_core.exceptions import ResourceExhausted

DATA_DIR = "data"
CURATED_PATH = os.path.join(DATA_DIR, "curated.json")
TRENDS_PATH  = os.path.join(DATA_DIR, "trends.json")

# Límites por entorno (opcionales, con defaults conservadores)
PER_CATEGORY_LIMIT = int(os.getenv("PER_CATEGORY_LIMIT", "30"))
MAX_TOTAL_ARTICLES = int(os.getenv("MAX_TOTAL_ARTICLES", "120"))

os.makedirs(DATA_DIR, exist_ok=True)

def _read_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[!] No pude leer {path}: {e} → reinicio formato.", flush=True)
    return default

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _normalize_curated(obj):
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, list):
        out = {}
        for item in obj:
            if isinstance(item, str):
                out[item] = False
            elif isinstance(item, dict) and "id" in item:
                val = item.get("relevante")
                out[item["id"]] = bool(val) if isinstance(val, bool) else False
        return out
    return {}

def _normalize_trends(obj):
    return obj if isinstance(obj, list) else []

print("🧪 GEMINI_API_KEY/GEMINI_API_KEYS presente:",
      any([os.getenv("GEMINI_API_KEY"), os.getenv("GEMINI_API_KEYS")]),
      flush=True)

print(f"[+] Cargando feeds...", flush=True)
feeds_by_category = load_feeds()
if not feeds_by_category:
    print("[❌] No hay feeds cargados. Revisa config/feeds.yaml (indentación y 'feeds:' en raíz).", flush=True)
    sys.exit(1)

print(f"[+] Recogiendo artículos (por categoría: {PER_CATEGORY_LIMIT})…", flush=True)
articles = fetch_articles_from_feeds(feeds_by_category, per_category=PER_CATEGORY_LIMIT)

# Limitar total si se desea
if len(articles) > MAX_TOTAL_ARTICLES:
    articles = articles[:MAX_TOTAL_ARTICLES]

print(f"[+] Artículos obtenidos: {len(articles)}", flush=True)

curated = _normalize_curated(_read_json(CURATED_PATH, default={}))
trends  = _normalize_trends(_read_json(TRENDS_PATH,  default=[]))

procesados_nuevos = 0
total = len(articles)

for idx, art in enumerate(articles, start=1):
    art_id = art.get("id") or art.get("link") or art.get("title")
    if not art_id:
        print(f"[{idx}/{total}] [!] Artículo sin ID/link/título. Saltado.", flush=True)
        continue
    if art_id in curated:
        print(f"[{idx}/{total}] [·] Ya evaluado: {art.get('title','Sin título')[:70]}", flush=True)
        continue

    title = art.get("title", "Sin título")
    print(f"[{idx}/{total}] [IA] Evaluando: {title[:90]}", flush=True)

    try:
        is_rel = is_relevant_for_aura(art)   # rota claves y deja pasar 429 si todas se agotan
        curated[art_id] = bool(is_rel)
        if is_rel:
            trends.append(art)
            print(f"[{idx}/{total}] [✓] Relevante", flush=True)
        else:
            print(f"[{idx}/{total}] [✗] Descartada", flush=True)
        procesados_nuevos += 1

    except ResourceExhausted as e:
        print(f"[{idx}/{total}] [⛔] Cuota de Gemini agotada en todas las claves: {e}", flush=True)
        print("[💾] Guardando progreso y saliendo…", flush=True)
        _save_json(CURATED_PATH, curated)
        _save_json(TRENDS_PATH, trends)
        sys.exit(0)

    except Exception as e:
        print(f"[{idx}/{total}] [!] Error con el artículo: {e}", flush=True)
        curated[art_id] = False

    # Guardado incremental tras cada artículo
    _save_json(CURATED_PATH, curated)
    _save_json(TRENDS_PATH, trends)

# Resumen en logs (para comprobar que no están vacíos)
print(f"[ℹ] Resumen guardado: curated={len(curated)} entradas, trends={len(trends)} relevantes", flush=True)
print(f"[ℹ] Ejemplos curated (hasta 3): {list(curated)[:3]}", flush=True)
print(f"[ℹ] Ejemplos trends (hasta 1): {trends[:1]}", flush=True)

print(f"[✅] Proceso completado. Nuevos procesados: {procesados_nuevos}", flush=True)
