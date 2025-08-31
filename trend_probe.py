import json
from app.utils.parser import load_articles
from app.utils.ai_filter import is_relevant_for_aura
import os

CURATED_PATH = "data/curated.json"
TRENDS_PATH = "data/trends.json"

# Crear archivos si no existen
if not os.path.exists(CURATED_PATH):
    with open(CURATED_PATH, "w") as f:
        json.dump([], f)

if not os.path.exists(TRENDS_PATH):
    with open(TRENDS_PATH, "w") as f:
        json.dump([], f)

# Cargar artículos ya curados (para no repetir)
with open(CURATED_PATH, "r") as f:
    curated_ids = set(json.load(f))

# Cargar artículos ya seleccionados como tendencia
with open(TRENDS_PATH, "r") as f:
    curated_articles = json.load(f)

print("[+] Cargando feeds...")
feeds_by_category = load_articles()

print("[+] Recogiendo artículos...")
all_articles = []
for category, articles in feeds_by_category.items():
    for article in articles:
        article["category"] = category
        all_articles.append(article)

print(f"[+] Artículos obtenidos: {len(all_articles)}")

# Procesar artículos
for article in all_articles:
    article_id = article["id"]

    if article_id in curated_ids:
        print(f"[✓] Ya procesado: {article['title'][:60]}")
        continue

    print(f"[IA] Evaluando: {article['title'][:60]}")

    try:
        result = is_relevant_for_aura(article)

        if result["relevante"]:
            print(f"[✔] Añadido: {article['title'][:60]}")

            enriched_article = {
                "id": article_id,
                "title": article["title"],
                "link": article["link"],
                "summary": result["resumen"],
                "category": article["category"],
                "idea_activacion": result["idea_activacion"],
                "motivo": result["motivo"]
            }

            curated_articles.append(enriched_article)

            # ✅ Guardar avances parciales
            with open(TRENDS_PATH, "w") as f:
                json.dump(curated_articles, f, ensure_ascii=False, indent=2)

        else:
            print(f"[✗] Descartada: {article['title'][:60]}")

    except Exception as e:
        print(f"[!] Error de IA: {e}")
        continue  # saltar al siguiente

    # ✅ Marcar como procesado, pase lo que pase
    curated_ids.add(article_id)
    with open(CURATED_PATH, "w") as f:
        json.dump(list(curated_ids), f, ensure_ascii=False, indent=2)

print("[✓] Proceso finalizado.")
