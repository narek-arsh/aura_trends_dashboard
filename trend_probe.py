import os
import json
import time
from app.utils.parser import load_feeds, fetch_articles_from_feeds
from app.utils.ai_filter import is_relevant_for_aura
from app.utils.utils import parse_gemini_response

CURATED_PATH = "data/curated.json"

# 💾 Cargar artículos ya analizados
if os.path.exists(CURATED_PATH):
    with open(CURATED_PATH, "r", encoding="utf-8") as f:
        curated_articles = json.load(f)
else:
    curated_articles = {}

print("[+] Cargando feeds...")
feeds_by_category = load_feeds()

print("[+] Recogiendo artículos...")
all_articles = []

for category, urls in feeds_by_category.items():
    print(f"[+] Recogiendo artículos de categoría: {category}")
    category_articles = fetch_articles_from_feeds(urls)
    for article in category_articles:
        article["category"] = category
    all_articles.extend(category_articles)

print(f"[+] Artículos obtenidos: {len(all_articles)}")

# ⚙️ Evaluar con IA
for i, article in enumerate(all_articles):
    article_id = article.get("id")
    if not article_id:
        print(f"[!] Artículo sin ID, omitido: {article.get('title', '')}")
        continue

    if article_id in curated_articles:
        print(f"[•] Ya evaluado: {article['title'][:60]}")
        continue

    try:
        print(f"[IA] Evaluando: {article['title'][:80]}")
        result = is_relevant_for_aura(article)

        if not isinstance(result, bool):
            raise ValueError("Respuesta IA malformada")

        curated_articles[article_id] = result

    except Exception as e:
        print(f"[!] Error con el artículo '{article.get('title', '')}': {e}")
        curated_articles[article_id] = False  # Lo marcamos como no relevante

    # Guardar progreso parcial
    with open(CURATED_PATH, "w", encoding="utf-8") as f:
        json.dump(curated_articles, f, ensure_ascii=False, indent=2)

    time.sleep(5)  # Para evitar rate limits

print("[✅] Proceso completado")
