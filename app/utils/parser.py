import feedparser
import yaml
import os

def load_feeds():
    print("[+] Cargando feeds...")
    with open("config/feeds.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config

def fetch_articles_from_feeds(feeds_by_category, limit_per_category=60):
    print("[+] Recogiendo artículos...")
    all_articles = []

    for category, feeds in feeds_by_category.items():
        count = 0
        for feed_url in feeds:
            if count >= limit_per_category:
                break
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                if count >= limit_per_category:
                    break
                article = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", ""),
                    "category": category,
                }
                all_articles.append(article)
                count += 1

    print(f"[+] Artículos obtenidos: {len(all_articles)}")
    return all_articles
