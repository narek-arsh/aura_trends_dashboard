import os
import json
from app.utils.parser import load_feeds, fetch_articles_from_feeds
from app.utils.ai_filter import is_relevant_for_aura

DATA_DIR = "data"
CURATED_PATH = os.path.join(DATA_DIR, "curated.json")
TRENDS_PATH  = os.path.join(DATA_DIR, "trends.json")

os.makedirs(DATA_DIR, exist_ok=True)

def _load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] No pude leer {path}: {e} → lo reinicio.")
    return default

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 1) Cargar feeds
print("🧪 GEMINI_API_KEY presente:", bool(os.getenv("GEMINI_API_KEY")))
print("[+] Cargando feeds...")
feeds_by_category = load_feeds()
if not feeds_by_category:
    print("[❌] No hay feeds cargados. Revisa config/feeds.yaml (indentación).")
    raise SystemExit(1)

# 2) Recoger artículos
print("[+] Recogiendo artículos...")
articles = fetch_articles_from_feeds(feeds_by_category, per_category=60)
print(f"[+] Artículos obtenidos: {len(articles)}")

# 3) Cargar progreso previo
curated = _load_json(CURATED_PATH, default={})   # dict: id -> bool
trends  = _load_json(TRENDS_PATH,  default=[])   # lista de artículos relevantes

# 4) Procesar
for art in articles:
    art_id = art.get("id") or art.get("link") or art.get("title")
    if not art_id:
        print("[!] Artículo sin ID ni link ni título. Saltado.")
        continue

    if art_id in curated:
        # Ya evaluado antes
        continue

    title = art.get("title", "Sin título")
    print(f"[IA] Evaluando: {title[:90]}")

    try:
        is_rel = is_relevant_for_aura(art)
        curated[art_id] = is_rel
        if is_rel:
            trends.append(art)
            print(f"[✓] Relevante: {title[:60]}")
        else:
            print(f"[✗] Descartada: {title[:60]}")

    except Exception as e:
        # Si es error de cuota/rate-limit, guardamos y cortamos
        msg = str(e).lower()
        if "429" in msg or "quota" in msg or "resourceexhausted" in msg:
            print(f"[⛔] Cuota de Gemini alcanzada: {e}")
            print("[💾] Guardando progreso y saliendo…")
            _save_json(CURATED_PATH, curated)
            _save_json(TRENDS_PATH, trends)
            raise SystemExit(0)
        # Si es otro error puntual, marcamos como no relevante y seguimos
        print(f"[!] Error con el artículo: {e}")
        curated[art_id] = False

    # Guardado incremental tras cada artículo (para no perder progreso)
    _save_json(CURATED_PATH, curated)
    _save_json(TRENDS_PATH, trends)

print("[✅] Proceso completado sin errores.")
