import feedparser
import hashlib
import datetime
import yaml
from pathlib import Path

def load_feeds(feed_file="config/feeds.yaml"):
    """Carga los feeds desde el archivo YAML."""
    with open(feed_file, "r", encoding="utf-8") as f:
        feeds = yaml.safe_load(f)
    return feeds

def generate_id(entry):
    """Genera un ID único por noticia en base a su link o título."""
    base = entry.get("link") or entry.get("title", "")
    return hashlib.md5(base.encode("utf-8")).hexdigest()

def parse_feed(feed_url, category):
    """Parsea un único feed RSS y devuelve noticias como diccionarios."""
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries:
        article = {
            "id": generate_id(entry),
            "title": entry.get("title", ""),
            "summary": entry.get("summary", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "category": category,
            "image": extract_image(entry),
        }
        articles.append(article)
    return articles

def extract_image(entry):
    """Extrae una imagen destacada si está disponible en el RSS."""
    # Busca campos típicos donde pueden aparecer imágenes
    if "media_content" in entry and entry.media_content:
        return entry.media_content[0].get("url", "")
    if "media_thumbnail" in entry and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url", "")
    if "image" in entry:
        return entry["image"]
    return ""

def parse_all_feeds(feeds, per_category_limit=60):
    """Parsea todos los feeds agrupados por categoría, con límite."""
    all_articles = []
    for category, urls in feeds.items():
        collected = 0
        for url in urls:
            if collected >= per_category_limit:
                break
            articles = parse_feed(url, category)
            for art in articles:
                if collected < per_category_limit:
                    all_articles.append(art)
                    collected += 1
    return all_articles
