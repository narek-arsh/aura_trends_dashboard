# Parser de feeds RSSimport yaml
import feedparser
import hashlib

CONFIG_PATH = "config/feeds.yaml"

def hash_article(entry):
    raw = entry.get("title", "") + entry.get("link", "")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def parse_feed(url):
    parsed = feedparser.parse(url)
    return [{
        "id": hash_article(entry),
        "title": entry.get("title", "").strip(),
        "summary": entry.get("summary", "").strip() if entry.get("summary") else "",
        "link": entry.get("link", "").strip()
    } for entry in parsed.entries]

def load_feeds():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    feeds_by_category = {}
    for category, urls in config.items():
        category_articles = []
        for url in urls:
            articles = parse_feed(url)
            category_articles.extend(articles)
        feeds_by_category[category] = category_articles

    return feeds_by_category
