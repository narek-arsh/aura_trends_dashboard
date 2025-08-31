import feedparser
import yaml

def load_feeds():
    with open("config/feeds.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config["feeds"]

def fetch_articles_from_feeds(feeds_by_category):
    all_articles = []

    for category, feed_urls in feeds_by_category.items():
        for url in feed_urls:
            parsed_feed = feedparser.parse(url)
            for entry in parsed_feed.entries:
                article = {
                    "id": entry.get("id") or entry.get("link"),
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "link": entry.get("link", ""),
                    "category": category,
                }
                all_articles.append(article)

    return all_articles
