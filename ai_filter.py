from ai_utils import configure_gemini
import hashlib
import json
import os

CURATED_PATH = "data/trends_curated.json"

def load_curated_ids():
    if os.path.exists(CURATED_PATH):
        with open(CURATED_PATH, "r", encoding="utf-8") as f:
            return {a["id"] for a in json.load(f)}
    return set()

def save_curated(articles):
    if os.path.exists(CURATED_PATH):
        with open(CURATED_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = []
    existing += articles
    with open(CURATED_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

def hash_article(title, summary):
    return hashlib.sha256((title + summary).encode("utf-8")).hexdigest()

def filter_and_enrich_articles(articles):
    model = configure_gemini()
    curated_ids = load_curated_ids()
    new_articles = []

    for a in articles:
        id_ = hash_article(a["title"], a.get("summary", ""))
        if id_ in curated_ids:
            continue

        prompt = f"""
Eres un curador de noticias para un hotel de lujo. Analiza el siguiente artículo:

Título: {a["title"]}
Resumen: {a.get("summary", "")}

¿Es relevante para un cliente interesado en moda, gastronomía, arte, lifestyle o lujo? 
Si no es relevante, responde solo con: DESCARTAR

Si es relevante, dame:
1. Un resumen breve
2. Una frase explicando "Por qué es importante"
3. Una frase con "Ideas de activación" para un host en un hotel 5*.

Responde en este formato:
---
RESUMEN: ...
WHY IT MATTERS: ...
IDEAS DE ACTIVACIÓN: ...
"""

        response = model.generate_content(prompt)
        text = response.text.strip()

        if text.startswith("DESCARTAR"):
            continue

        lines = text.splitlines()
        enriched = {
            "id": id_,
            "title": a["title"],
            "link": a["link"],
            "summary": next((l.split(":",1)[1].strip() for l in lines if l.startswith("RESUMEN:")), ""),
            "why": next((l.split(":",1)[1].strip() for l in lines if l.startswith("WHY IT MATTERS:")), ""),
            "activation": next((l.split(":",1)[1].strip() for l in lines if l.startswith("IDEAS DE ACTIVACIÓN:")), "")
        }

        new_articles.append(enriched)

    save_curated(new_articles)
    return new_articles
