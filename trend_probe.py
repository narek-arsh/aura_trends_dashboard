import os
import json
from app.utils.parser import load_feeds, fetch_articles_from_feeds
from app.utils.ai_filter import is_relevant_for_aura

CURATED_FILE = "data/curated.json"
TRENDS_FILE = "data/trends.json"

# Cargar artículos ya procesados
if os.path.exists(CURATED_FILE):
    with open(CURATED_FILE, "r", encoding="utf-8") as f:
        curated_articles = json.load(f)
else:
    curated_articles = {}

if os.path.exists(TRENDS_FILE):
    with open(TRENDS_FILE, "r", encoding="utf-8") as f:
        trends = json.load(f)
else:
    trends = []

print("[+] Cargando feeds...")
feeds_by_category = load_feeds()

print("[+] Recogiendo artículos...")
articles = fetch_articles_from_feeds(feeds_by_category)
print(f"[+] Artículos obtenidos: {len(articles)}")

for article in articles:
    article_id = article["id"]
    title = article.get("title", "Sin título")

    if article_id in curated_articles:
        print(f"[=] Ya procesado: {title}")
        continue

    print(f"[IA] Evaluando: {title}")
    try:
        result = is_relevant_for_aura(article)
        if result:
            trends.append(result)
            curated_articles[article_id] = True
            print(f"[✓] Aprobado: {title}")
        else:
            curated_articles[article_id] = False
            print(f"[✗] Descartada: {title}")

    except Exception as e:
        print(f"[!] Error con el artículo '{title}': {e}")
        break  # Cortamos para evitar perder todo si se agotó el límite

# Guardar resultados
with open(CURATED_FILE, "w", encoding="utf-8") as f:
    json.dump(curated_articles, f, ensure_ascii=False, indent=2)

with open(TRENDS_FILE, "w", encoding="utf-8") as f:
    json.dump(trends, f, ensure_ascii=False, indent=2)

print("[✅] Proceso completado")
