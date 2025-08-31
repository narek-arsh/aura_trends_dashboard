import feedparser

def load_feeds():
    import yaml
    with open("config/feeds.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config["feeds"]

def fetch_articles_from_feeds(feed_urls):
    articles = []

    for feed_url in feed_urls:
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries:
            article = {
                "id": entry.get("id", entry.get("link")),
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
            }
            articles.append(article)

    return articles
