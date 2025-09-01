import yaml
import feedparser
import hashlib

def _make_id(title, link, published):
    base = f"{link or ''}|{title or ''}|{published or ''}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()

def load_feeds(path="config/feeds.yaml"):
    """
    Carga el YAML y acepta dos formatos:
    A) con 'feeds:' como raíz (preferido)
    B) plano por categorías (retrocompatibilidad)
    Nunca devuelve None. Si algo va mal, devuelve {}.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        if not cfg:
            print("[❌] feeds.yaml está vacío.")
            return {}

        # Formato A: {"feeds": {categoria: [urls]}}
        if isinstance(cfg, dict) and "feeds" in cfg and isinstance(cfg["feeds"], dict):
            return cfg["feeds"]

        # Formato B: {categoria: [urls]}
        if isinstance(cfg, dict) and all(isinstance(v, list) for v in cfg.values()):
            return cfg

        print("[❌] Formato de feeds.yaml no reconocido. Revisa la indentación.")
        return {}
    except Exception as e:
        print(f"[❌] Error leyendo {path}: {e}")
        return {}

def fetch_articles_from_feeds(feeds_by_category, per_category=60):
    """
    Recorre el dict {categoria: [urls]} y devuelve una lista de artículos,
    con id estable, título, resumen, link, fecha y categoría.
    """
    all_articles = []
    for category, urls in (feeds_by_category or {}).items():
        collected = 0
        for url in urls:
            if collected >= per_category:
                break
            feed = feedparser.parse(url)
            for entry in getattr(feed, "entries", []):
                if collected >= per_category:
                    break
                title = entry.get("title", "")
                link = entry.get("link", "")
                published = entry.get("published", "")
                summary = entry.get("summary", "")
                art_id = entry.get("id") or _make_id(title, link, published)

                all_articles.append({
                    "id": art_id,
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "published": published,
                    "category": category
                })
                collected += 1
    return all_articles
