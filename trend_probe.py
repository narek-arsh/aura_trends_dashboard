import json
from pathlib import Path
from app.utils.parser import load_feeds, parse_all_feeds
from app.utils.ai_filter import is_relevant_for_aura

# Paths
CURATED_PATH = Path("data/curated.json")
TRENDS_PATH = Path("data/trends.json")

# Cargar memoria de noticias ya procesadas
def load_curated_ids():
    if CURATED_PATH.exists():
        with open(CURATED_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(item["id"] for item in data)
    return set()

def save_curated(new_entries):
    if CURATED_PATH.exists():
        with open(CURATED_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = []
    combined = existing + new_entries
    with open(CURATED_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

def save_trends(entries):
    with open(TRENDS_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

def main():
    print("[+] Cargando feeds...")
    feeds = load_feeds()

    print("[+] Recogiendo artículos...")
    articles = parse_all_feeds(feeds, per_category_limit=60)  # Máx por categoría

    print(f"[+] Artículos obtenidos: {len(articles)}")

    curated_ids = load_curated_ids()
    new_curated = []
    trends = []

    for article in articles:
        if article["id"] in curated_ids:
            continue

        enriched = is_relevant_for_aura(article)
        if enriched:
            print(f"[✓] Aprobada: {article['title'][:60]}...")
            article.update(enriched)
            trends.append(article)
            new_curated.append({"id": article["id"]})
        else:
            print(f"[✗] Descartada: {article['title'][:60]}...")

    if trends:
        save_trends(trends)
        save_curated(new_curated)
        print(f"[✔] Noticias guardadas: {len(trends)}")
    else:
        print("[!] No hubo noticias relevantes.")

if __name__ == "__main__":
    main()
