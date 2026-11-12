"""Daily public-reporting discovery, not an automatic construction-completion estimator."""
import datetime as dt
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

DEST = Path("data/nk-border-status.json")
QUERIES = [
    '"North Korea" border fence construction',
    '북한 국경 철책 건설 요새화',
]
def main():
    old = {}
    if DEST.exists():
        try:
            old = json.loads(DEST.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
    articles = {}
    success = 0
    for query in QUERIES:
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({
            "q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"
        })
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "NEXTBIO-border-monitor/1.0"})
            with urllib.request.urlopen(req, timeout=20) as response:
                root = ET.fromstring(response.read())
            success += 1
            for item in root.findall("./channel/item")[:25]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub = (item.findtext("pubDate") or "").strip()
                if title and link.startswith("https://"):
                    articles[link] = {"title": title, "url": link, "published": pub}
        except (OSError, ET.ParseError, TimeoutError) as exc:
            print(f"Source unavailable: {query}: {exc}")
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    if not success:
        print("All reporting sources unavailable; preserving last successful check")
        return
    data = {
        "last_checked": now,
        "check_status": "ok" if success == len(QUERIES) else "partial",
        "source_count": success,
        "estimates": {
            "scope": "Southern inter-Korean border fortification",
            "reference_period": "2026-08",
            "ground_preparation_pct": 90,
            "fences_mines_pct_min": 30,
            "fences_mines_pct_max": 60,
            "note": "Reported estimates, not verified total border-wall completion or automatic measurements."
        },
        "reports": list(articles.values())[:15]
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Checked {success} feeds, found {len(articles)} links. Estimates unchanged.")
if __name__ == "__main__":
    main()
