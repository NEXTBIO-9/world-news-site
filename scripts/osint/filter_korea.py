"""Korea-focused public-news filter. No AI or external paid API."""
import datetime as dt
import json
import re
from pathlib import Path

INPUT = Path("data/articles.json")
OUTPUT = Path("data/osint/events.json")
DIRECT = re.compile(r"북한|대한민국|한국군|합참|주한미군|한미연합|한미일|한반도|서해\s*NLL|독도|north korea|south korea|rok military|usfk|korean peninsula|kim jong un|pyongyang|seoul", re.I)
SECURITY = re.compile(r"미사일|핵무기|핵실험|군사|국방|안보|방위|군함|해군|공군|훈련|사이버공격|해킹|제재|군사협력|탄도|잠수함|방공|전투기|missile|nuclear|military|defen[cs]e|security|navy|warship|drill|exercise|sanction|cyberattack|ballistic|submarine|fighter jet", re.I)
REGIONAL = re.compile(r"중국|일본|러시아|대만|동중국해|서해|동해|북러|미중|china|japan|russia|taiwan|east china sea|yellow sea|sea of japan|indo.pacific", re.I)
INDIRECT = re.compile(r"북러|대북|북·러|북-러|north korea.russia|russia.north korea|russia.dprk|dprk.russia|anti.north korea", re.I)

def classify(article):
    text = " ".join(str(article.get(k) or "") for k in ("title", "title_ko", "summary"))
    if not SECURITY.search(text):
        return None
    headline = " ".join(str(article.get(k) or "") for k in ("title", "title_ko"))
    if DIRECT.search(headline):
        return "A"
    # A regional headline is not enough: the Korea connection must be explicit
    # in the headline, not merely in the scraped summary/source label.
    if REGIONAL.search(headline) and INDIRECT.search(headline):
        return "B"
    return None

def collect(articles, limit=100):
    results, seen = [], set()
    for article in articles:
        if not isinstance(article, dict):
            continue
        tier = classify(article)
        url = str(article.get("url") or "")
        title = str(article.get("title_ko") or article.get("title") or "").strip()
        if not tier or not title or not url.startswith("https://") or url in seen:
            continue
        seen.add(url)
        results.append({"title": title, "original_title": str(article.get("title") or ""),
                        "url": url, "source": str(article.get("source") or "출처 미상"),
                        "published": str(article.get("published") or ""),
                        "countries": article.get("countries") if isinstance(article.get("countries"), list) else [],
                        "relevance": tier, "verification": "단일 보도 · 원문 확인 필요"})
    results.sort(key=lambda x: x["published"], reverse=True)
    return results[:limit]

def main():
    raw = json.loads(INPUT.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("articles"), list):
        raise ValueError("Expected articles list")
    items = collect(raw["articles"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({"updated": dt.datetime.now(dt.timezone.utc).isoformat(),
                                  "method": "keyword-filter; not independently verified",
                                  "events": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Korea OSINT candidates:", len(items))

if __name__ == "__main__":
    main()
