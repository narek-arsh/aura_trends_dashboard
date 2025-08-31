import yaml
import feedparser
import os

def load_feeds():
    path = os.path.join("config", "feeds.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def fetch_articles_from_feeds(feeds_by_category, limit_per_category=60):
    all_articles = []

    for category, feeds in feeds_by_category.items():
        print(f"[+] Recogiendo artículos de categoría: {category}")
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
                    "category": category
                }

                all_articles.append(article)
                count += 1

    print(f"[+] Artículos obtenidos: {len(all_articles)}")
    return all_articles
