import feedparser
import yaml
import json
import os
from ai_filter import filter_and_enrich_articles

with open("config/feeds.yaml", "r", encoding="utf-8") as f:
    feeds_config = yaml.safe_load(f)

with open("config/config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

articles = []

for category, urls in feeds_config["feeds"].items():
    count = 0
    limit = config["limits"].get(category, 30)
    for url in urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if count >= limit:
                break
            articles.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.get("summary", ""),
                "category": category
            })
            count += 1

if config.get("use_ai", False):
    final_articles = filter_and_enrich_articles(articles)
else:
    final_articles = articles

with open("data/trends.json", "w", encoding="utf-8") as f:
    json.dump(final_articles, f, ensure_ascii=False, indent=2)
