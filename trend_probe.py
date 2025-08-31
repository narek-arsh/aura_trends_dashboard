import feedparser
import yaml
import hashlib
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

def clean_summary(html):
    return BeautifulSoup(html, "html.parser").get_text()

def get_image(entry):
    media = entry.get("media_content", [])
    if media and "url" in media[0]:
        return media[0]["url"]
    return entry.get("image", None)

def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def is_valid(entry, category_config, global_keywords):
    title = entry.get("title", "").lower()
    summary = clean_summary(entry.get("summary", "")).lower()
    content = title + " " + summary

    if not any(kw in content for kw in global_keywords):
        return False
    if "include" in category_config["keywords"]:
        if not any(kw in content for kw in category_config["keywords"]["include"]):
            return False
    if "exclude" in category_config["keywords"]:
        if any(kw in content for kw in category_config["keywords"]["exclude"]):
            return False
    return True

def generate_id(link):
    return hashlib.md5(link.encode("utf-8")).hexdigest()

def collect_trends(config_path="config.yaml"):
    config = load_config(config_path)
    results = []

    for category, cat_data in config["categories"].items():
        for feed_url in cat_data["feeds"]:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                if not is_valid(entry, cat_data, config["global_keywords"]["include"]):
                    continue
                item = {
                    "id": generate_id(entry.link),
                    "category": category,
                    "title": entry.title,
                    "link": entry.link,
                    "summary": clean_summary(entry.get("summary", "")),
                    "published": str(dateparser.parse(entry.get("published", str(datetime.utcnow())))),
                    "image": get_image(entry),
                    "saved": False,
                    "score": 0,
                    "why_it_matters": "",
                    "activation_ideas": ""
                }
                results.append(item)

    with open("data/trends.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    collect_trends()