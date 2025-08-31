import os
import json
from app.utils.parser import load_feeds
from app.utils.ai_filter import is_relevant_for_aura

DATA_DIR = "data"
CURATED_PATH = os.path.join(DATA_DIR, "curated.json")
TRENDS_PATH = os.path.join(DATA_DIR, "trends.json")

# Crear carpeta si no existe
os.makedirs(DATA_DIR, exist_ok=True)

# Cargar feeds
print("[+] Cargando feeds...")
feeds_by_category = load_feeds()

# Cargar artículos
print("[+] Recogiendo artículos...")
articles = []
for category, feed_articles in feeds_by_category.items():
    for article in feed_articles:
        article["categoria"] = category
        articles.append(article)

print(f"[+] Artículos obtenidos: {len(articles)}")

# Cargar IDs ya procesados
if os.path.exists(CURATED_PATH):
    with open(CURATED_PATH, "r", encoding="utf-8") as f:
        curated_ids = {item["id"] for item in json.load(f)}
else:
    curated_ids = set()

# Preparar contenedor de nuevos trends
trends = []

for article in articles:
    article_id = article["id"]
    if article_id in curated_ids:
        continue

    print(f"[IA] Evaluando: {article['title'][:70]}")

    result = is_relevant_for_aura(article)

    curated_ids.add(article_id)

    if result["es_util"]:
        print(f"[✓] Aprobada: {article['title'][:60]}")
        trends.append({
            "id": article_id,
            "title": article["title"],
            "summary": article["summary"],
            "categoria": article["categoria"],
            "link": article["link"],
            "why_it_matters": result["why_it_matters"],
            "ideas_activacion": result["ideas_activacion"]
        })
    else:
        print(f"[✗] Descartada: {article['title'][:60]}")

# Guardar resultados
with open(TRENDS_PATH, "w", encoding="utf-8") as f:
    json.dump(trends, f, indent=2, ensure_ascii=False)

with open(CURATED_PATH, "w", encoding="utf-8") as f:
    json.dump([{"id": x} for x in curated_ids], f, indent=2)

print(f"[✔] Noticias guardadas: {len(trends)}")
# Lógica de recogida de noticias y filtrado con IA
