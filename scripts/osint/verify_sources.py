"""Conservative source diversity annotations. NOT a claim-level fact checker."""
import re
from urllib.parse import urlparse

def publisher(item):
    source = str(item.get("source") or "").strip().lower()
    source = re.sub(r"\s+", " ", source)
    if source and source != "출처 미상":
        return source
    host = urlparse(str(item.get("url") or "")).hostname or ""
    return host.lower()

def annotate(items):
    """Do not treat topic/day matches as same incident or independent corroboration."""
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
