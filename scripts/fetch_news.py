import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

FEEDS = [
    ("외교·국제", "https://news.google.com/rss/search?q=world+politics+OR+diplomacy&hl=ko&gl=KR&ceid=KR:ko"),
    ("분쟁·군사", "https://news.google.com/rss/search?q=war+OR+military+OR+defense&hl=ko&gl=KR&ceid=KR:ko"),
    ("경제·금융", "https://news.google.com/rss/search?q=world+economy+OR+finance+OR+markets&hl=ko&gl=KR&ceid=KR:ko"),
    ("재해·재난", "https://news.google.com/rss/search?q=disaster+OR+earthquake+OR+flood&hl=ko&gl=KR&ceid=KR:ko"),
    ("일반", "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"),
]

def fetch(category, url):
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        root = ET.fromstring(response.read())

    articles = []

    for item in root.findall(".//item")[:15]:
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        desc = item.findtext("description", "").strip()
        desc = re.sub(r"<[^>]+>", " ", desc)
        desc = re.sub(r"\s+", " ", desc).strip()

        pub = item.findtext("pubDate", "")
        try:
            date = parsedate_to_datetime(pub).astimezone(
                timezone.utc
            ).isoformat()
        except Exception:
            date = datetime.now(timezone.utc).isoformat()

        source = ""
        if " - " in title:
            title, source = title.rsplit(" - ", 1)

        if title and link:
            articles.append({
                "category": category,
                "title": title,
                "url": link,
                "summary": desc[:260],
                "source": source or "Google News RSS",
                "published": date
            })

    return articles


def main():
    seen = set()
    articles = []

    for category, url in FEEDS:
        try:
            for article in fetch(category, url):
                if article["url"] not in seen:
                    seen.add(article["url"])
                    articles.append(article)
        except Exception as error:
            print(f"Feed failed ({category}): {error}")

    articles.sort(
        key=lambda x: x["published"], reverse=True
    )

    Path("data").mkdir(exist_ok=True)

    payload = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "articles": articles[:75]
    }

    Path("data/articles.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"Saved {len(payload['articles'])} articles")


if __name__ == "__main__":
    main()
