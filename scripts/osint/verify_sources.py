"""Evidence provenance and independent-source hints, not automated truth verification."""
import re
from urllib.parse import urlparse

ALIASES = {
    "reuters": "reuters", "reuters.com": "reuters",
    "associated press": "ap", "ap news": "ap", "apnews.com": "ap",
    "yonhap": "yonhap", "yonhap news": "yonhap", "yna.co.kr": "yonhap",
    "us department of defense": "us-dod", "defense.gov": "us-dod",
    "us indo-pacific command": "us-indopacom", "pacom.mil": "us-indopacom",
}
def publisher(item):
    source = re.sub(r"\\s+", " ", str(item.get("source") or "").strip().lower())
    host = (urlparse(str(item.get("url") or "")).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    # Publisher field is preferred because aggregator URLs are often news.google.com.
    return ALIASES.get(source, ALIASES.get(host, source or host or "unknown"))

def normalize_title(item):
    title = str(item.get("original_title") or item.get("title") or "").lower()
    title = re.sub(r"[^\\w\\s가-힣]", " ", title)
    words = [x for x in title.split() if len(x) >= 3]
    return set(words)

def source_comparison(items):
    """Surface candidate headline overlaps; do not call them confirmed incidents."""
    results = []
    for i, left in enumerate(items):
        a = normalize_title(left)
        if len(a) < 3:
            continue
        for right in items[i+1:]:
            if publisher(left) == publisher(right):
                continue
            b = normalize_title(right)
            if len(b) < 3:
                continue
            overlap = len(a & b) / max(1, len(a | b))
            if overlap >= 0.55:
                results.append({"left_url": left.get("url"), "right_url": right.get("url"),
                                "publishers": [publisher(left), publisher(right)],
                                "headline_similarity": round(overlap, 3),
                                "status": "서로 다른 발행처의 유사 제목 · 사건 동일성 미확인"})
    return results[:100]

def annotate(items):
    out = []
    for item in items:
        row = dict(item)
        row["verification"] = "원문 및 독립 출처 확인 필요"
        row["source_key"] = publisher(item)
        row["corroborated"] = False
        out.append(row)
    return out

def special_candidates(items):
    """Escalation candidates only. Human review required before special publication."""
    pattern = re.compile(r"탄도미사일|핵실험|군사충돌|ballistic missile|nuclear test|armed clash", re.I)
    return [x for x in items if pattern.search(str(x.get("original_title") or x.get("title") or ""))]
