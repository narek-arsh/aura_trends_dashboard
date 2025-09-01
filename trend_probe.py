# trend_probe.py

import os
import json
from datetime import datetime
from app.utils.parser import load_feeds, fetch_articles_from_feeds
from app.utils.ai_filter import is_relevant_for_aura

CURATED_PATH = "data/curated.json"
ALL_PATH = "data/all_articles.json"

# Verificamos API
print(f"🧪 GEMINI_API_KEY presente: {bool(os.getenv('GEMINI_API_KEY'))}")

# Cargar feeds
print("[+] Cargando feeds...")
feeds_by_category = load_feeds()

# Recoger artículos
print("[+] Recogiendo artículos...")
articles = fetch_articles_from_feeds(feeds_by_category)
print(f"[+] Artículos obtenidos: {len(articles)}")

# Guardamos todos los artículos
with open(ALL_PATH, "w", encoding="utf-8") as f:
    json.dump(articles, f, indent=2, ensure_ascii=False)

# Cargar artículos ya curados
if os.path.exists(CURATED_PATH):
    with open(CURATED_PATH, "r", encoding="utf-8") as f:
        curated_articles = json.load(f)
else:
    curated_articles = []

# Empezamos a filtrar
nuevos = 0
for article in articles:
    try:
        article_id = article.get("id") or article.get("link") or article.get("title")
        if article_id in curated_articles:
            continue

        print(f"[IA] Evaluando: {article['title'][:80]}")
        result = is_relevant_for_aura(article)
        curated_articles[article_id] = result
        nuevos += 1

    except json.JSONDecodeError as e:
        print(f"[!] Error al parsear respuesta IA: {e}")
        curated_articles[article_id] = False

    except Exception as e:
        msg = str(e)
        if "429" in msg or "quota" in msg.lower():
            print("[⛔] Límite de cuota alcanzado. Guardando y saliendo.")
            break
        print(f"[!] Error con el artículo '{article.get('title', 'sin título')}': {e}")
        curated_articles[article_id] = False

# Guardar resultados
with open(CURATED_PATH, "w", encoding="utf-8") as f:
    json.dump(curated_articles, f, indent=2, ensure_ascii=False)

print(f"[✅] Proceso completado. Artículos nuevos procesados: {nuevos}")
