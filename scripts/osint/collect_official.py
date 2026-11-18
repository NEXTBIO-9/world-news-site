"""Collect titles from public official RSS feeds; no scraping of protected pages."""
import datetime as dt
import json
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

DEST = Path("data/osint/official.json")
# Official publisher feeds; feed reachability and terms must be checked in production.
FEEDS = [
    ("US Department of Defense", "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&max=30"),
    ("US Indo-Pacific Command", "https://www.pacom.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=681&max=30"),
]
def parse(xml, source):
    root = ET.fromstring(xml)
    out = []
    for item in root.findall(".//item")[:40]:
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        date = (item.findtext("pubDate") or "").strip()
        if not title or not url.startswith("https://"):
            continue
        try:
            date = parsedate_to_datetime(date).astimezone(dt.timezone.utc).isoformat()
        except (TypeError, ValueError, OverflowError):
            date = ""
        out.append({"title": title, "url": url, "source": source, "published": date,
                    "verification": "기관 발표 원문 링크 · 발표 내용 별도 검증 필요"})
    return out

def main():
    items, errors = [], []
    for name, url in FEEDS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"NEXTBIO-OSINT/1.0"})
            with urllib.request.urlopen(req, timeout=15) as response:
                items.extend(parse(response.read(1024*1024), name))
        except (OSError, ET.ParseError, TimeoutError, ValueError) as exc:
            errors.append(name+": "+str(exc)[:160])
    if not items:
        print("No official RSS items; preserving existing data. Errors:", errors)
        return
    old = {}
    if DEST.exists():
        try: old = json.loads(DEST.read_text(encoding="utf-8"))
        except (ValueError, OSError): pass
    unique = {a["url"]:a for a in old.get("items", []) if isinstance(a,dict) and a.get("url")}
    unique.update({a["url"]:a for a in items})
    data = {"updated":dt.datetime.now(dt.timezone.utc).isoformat(), "items":list(unique.values())[-150:],
            "sources_ok":len(FEEDS)-len(errors),"sources_total":len(FEEDS),"errors":errors}
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Official RSS entries:",len(items),"errors:",errors)
if __name__=="__main__":main()
