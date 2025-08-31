import os
import json
from app.utils.parser import load_feeds, fetch_articles_from_feeds
from app.utils.ai_filter import is_relevant_for_aura

# 📁 Ruta al archivo donde se guardan los resultados
CURATED_FILE = "data/curated.json"

# 📥 Cargar artículos de los feeds
print("[+] Cargando feeds...")
feeds_by_category = load_feeds()
print("[+] Recogiendo artículos...")
articles = fetch_articles_from_feeds(feeds_by_category)
print(f"[+] Artículos obtenidos: {len(articles)}")

# 📂 Cargar artículos ya analizados (si existen)
if os.path.exists(CURATED_FILE):
    with open(CURATED_FILE, "r", encoding="utf-8") as f:
        curated_articles = json.load(f)
else:
    curated_articles = {}

# 🧠 Analizar artículos
for article in articles:
    article_id = article["id"]

    if article_id in curated_articles:
        continue  # Ya evaluado

    print(f"[IA] Evaluando: {article['title'][:100]}")

    try:
        result = is_relevant_for_aura(article)
        curated_articles[article_id] = result
    except Exception as e:
        print(f"[!] Error con el artículo '{article['title'][:100]}': {e}")
        curated_articles[article_id] = False

    # 💾 Guardar tras cada evaluación para no perder datos
    with open(CURATED_FILE, "w", encoding="utf-8") as f:
        json.dump(curated_articles, f, ensure_ascii=False, indent=2)

print("[✅] Proceso completado")
