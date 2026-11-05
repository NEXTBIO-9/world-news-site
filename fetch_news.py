import json, re, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

FEEDS = [
    ("외교·국제", "https://news.google.com/rss/search?q=world+politics+OR+diplomacy&hl=ko&gl=KR&ceid=KR:ko"),
    ("분쟁·군사", "https://news.google.com/rss/search?q=war+OR+military+OR+defense&hl=ko&gl=KR&ceid=KR:ko"),
    ("경제·금융", "https://news.google.com/rss/search?q=world+economy+OR+finance+OR+markets&hl=ko&gl=KR&ceid=KR:ko"),
    ("재해·재난", "https://news.google.com/rss/search?q=disaster+OR+earthquake+OR+flood&hl=ko&gl=KR&ceid=KR:ko"),
    ("제약·신약", "https://news.google.com/rss/search?q=pharmaceutical+OR+drug+discovery+OR+clinical+trial&hl=ko&gl=KR&ceid=KR:ko"),
    ("미생물", "https://news.google.com/rss/search?q=microbiology+OR+bacteria+OR+microbiome&hl=ko&gl=KR&ceid=KR:ko"),
    ("의료기기", "https://news.google.com/rss/search?q=medical+device+OR+diagnostic+device+OR+medical+equipment&hl=ko&gl=KR&ceid=KR:ko"),
    ("바이오기업", "https://news.google.com/rss/search?q=biotech+company+OR+biopharma+investment+OR+biotech+stock&hl=ko&gl=KR&ceid=KR:ko"),
    ("감염병", "https://news.google.com/rss/search?q=infectious+disease+OR+virus+outbreak+OR+vaccine&hl=ko&gl=KR&ceid=KR:ko"),
    ("일반", "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"),
]
HEADERS={"User-Agent":"Mozilla/5.0 (compatible; WorldNewsPrototype/1.0)"}

def text(node, tag):
    x=node.find(tag)
    return (x.text or "").strip() if x is not None else ""

def fetch(category, url):
    req=urllib.request.Request(url,headers=HEADERS)
    with urllib.request.urlopen(req,timeout=25) as r: raw=r.read()
    root=ET.fromstring(raw)
    out=[]
    for item in root.findall(".//item")[:15]:
        title=text(item,"title")
        link=text(item,"link")
        desc=re.sub(r"<[^>]+>"," ",text(item,"description"))
        desc=re.sub(r"\s+"," ",desc).strip()
        pub=text(item,"pubDate")
        try: dt=parsedate_to_datetime(pub).astimezone(timezone.utc).isoformat()
        except Exception: dt=datetime.now(timezone.utc).isoformat()
        # Google News title often ends with source name after a dash.
        source=""
        if " - " in title:
            title,source=title.rsplit(" - ",1)
        if title and link:
            out.append({"category":category,"title":title,"url":link,"summary":desc[:260],"source":source or "Google News RSS","published":dt})
    return out

def main():
    seen=set(); articles=[]
    for category,url in FEEDS:
        try:
            for a in fetch(category,url):
                key=a["url"]
                if key not in seen:
                    seen.add(key); articles.append(a)
        except Exception as e:
            print(f"Feed failed ({category}): {e}")
    articles.sort(key=lambda x:x["published"],reverse=True)
    if not articles:
        raise RuntimeError("No RSS articles retrieved; keeping previous data file")
    Path("data").mkdir(exist_ok=True)
    payload={"updated":datetime.now(timezone.utc).isoformat(),"articles":articles[:75]}
    Path("data/articles.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Saved {len(payload['articles'])} articles")

if __name__=="__main__": main()
