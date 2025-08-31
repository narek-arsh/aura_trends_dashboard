import os
import json
from app.utils.parser import load_feeds, fetch_articles_from_feeds
from app.utils.ai_filter import is_relevant_for_aura
import google.api_core.exceptions

CURATED_PATH = "data/curated.json"

print("[+] Cargando feeds...")
feeds_by_category = load_feeds()

print("[+] Recogiendo artículos...")
articles = []
for category, urls in feeds_by_category.items():
    print(f"[+] Recogiendo artículos de categoría: {category}")
    category_articles = fetch_articles_from_feeds(urls)
    for article in category_articles:
        article["category"] = category
    articles.extend(category_articles)

print(f"[+] Artículos obtenidos: {len(articles)}")

# Cargar los artículos ya procesados previamente
if os.path.exists(CURATED_PATH):
    with open(CURATED_PATH, "r", encoding="utf-8") as f:
        curated_articles = json.load(f)
else:
    curated_articles = {}

trends = []

for article in articles:
    article_id = f"{article.get('title','')}|{article.get('link','')}|{article.get('published','')}"
    title = article.get("title", "Sin título")

    if article_id in curated_articles:
        print(f"[·] Ya procesado: {title}")
        continue

    print(f"[IA] Evaluando: {title}")

    try:
        result = is_relevant_for_aura(article)
        curated_articles[article_id] = result
        if result:
            trends.append(result)
            print(f"[✓] Aprobado: {title[:50]}")
        else:
            print(f"[✗] Descartada: {title[:50]}")

    except google.api_core.exceptions.ResourceExhausted as e:
        print(f"[‼] Se agotaron los créditos de Gemini: {e}")
        print("[💾] Guardando artículos procesados hasta ahora...")
        with open(CURATED_PATH, "w", encoding="utf-8") as f:
            json.dump(curated_articles, f, indent=2, ensure_ascii=False)
        break

    except Exception as e:
        print(f"[!] Error con el artículo '{title}': {e}")
        curated_articles[article_id] = False
        continue

# Guardar resultados finales si no hubo error de crédito
else:
    print("[💾] Guardando artículos procesados...")
    with open(CURATED_PATH, "w", encoding="utf-8") as f:
        json.dump(curated_articles, f, indent=2, ensure_ascii=False)

    with open("data/trends.json", "w", encoding="utf-8") as f:
        json.dump(trends, f, indent=2, ensure_ascii=False)

    print("[✅] Proceso completado")
