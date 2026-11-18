"""Conservative OSINT grouping and templated briefings; no model-generated judgments."""
import datetime as dt
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

DATA = Path("data/osint/events.json")
REPORTS = Path("data/osint/reports.json")
KEYWORDS = {"missile": r"미사일|탄도|missile|ballistic", "nuclear": r"핵실험|핵무기|nuclear|nuke",
            "exercise": r"연합훈련|군사훈련|military exercise|joint drill", "cyber": r"사이버공격|해킹|cyberattack|hacking",
            "sanctions": r"제재|sanctions", "naval": r"해군|군함|naval|warship"}
def topic(item):
    text = str(item.get("original_title") or item.get("title") or "")
    for key, pattern in KEYWORDS.items():
        if re.search(pattern, text, re.I):
            return key
    return "other"

def group(items):
    """Group broad topic for navigation only; never assert same-event corroboration."""
    grouped = defaultdict(list)
    for item in items:
        day = local_day(item)
        grouped[(day, topic(item))].append(item)
    return [{"day": day, "topic": kind, "count": len(rows), "items": rows}
            for (day, kind), rows in sorted(grouped.items(), reverse=True)]

def local_day(item):
    try:
        timestamp = dt.datetime.fromisoformat(str(item.get("published") or "").replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            # Date-only values denote the source calendar date; do not shift days.
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(item.get("published") or "")):
                return timestamp.date().isoformat()
            return ""
        return timestamp.astimezone(dt.timezone(dt.timedelta(hours=9))).date().isoformat()
    except (ValueError, TypeError):
        return ""

def briefing(items, kind, date):
    selected = [x for x in items if local_day(x) == date] if kind == "daily" else items
    return {"id": hashlib.sha256((kind+date).encode()).hexdigest()[:12], "type": kind,
            "date": date, "title": ("대한민국 안보 일일 브리핑" if kind == "daily" else "대한민국 안보 주간 동향"),
            "summary": f"한국 안보 관련 보도 후보 {len(selected)}건. 독립적 사실 검증 및 전략적 판단은 수행되지 않았습니다.",
            "items": selected[:20], "verification": "미검증 보도 목록"}

def build(items, now=None):
    now = now or dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    local = now.astimezone(dt.timezone(dt.timedelta(hours=9)))
    today = local.date()
    daily_day = (today - dt.timedelta(days=1)).isoformat()
    week_start = today - dt.timedelta(days=7)
    weekly = [x for x in items if week_start.isoformat() <= local_day(x) < today.isoformat()]
    reports = [briefing(items, "daily", daily_day)]
    if today.weekday() == 6 and local.hour >= 7:
        reports.append(briefing(weekly, "weekly", today.isoformat()))
    return {"updated": local.isoformat(), "reports": reports, "topic_groups": group(items)}

def main():
    from verify_sources import annotate, special_candidates, source_comparison
    data = json.loads(DATA.read_text(encoding="utf-8"))
    items = annotate(data.get("events", []))
    result = build(items)
    result["source_comparison_candidates"] = source_comparison(items)
    result["special_review_candidates"] = special_candidates(items)
    result["special_review_required"] = True
    result["special_publication_enabled"] = False
    REPORTS.parent.mkdir(parents=True, exist_ok=True)
    # Keep daily briefing stable during hourly collection; publish at/after 07:00 KST.
    if REPORTS.exists():
        try:
            previous = json.loads(REPORTS.read_text(encoding="utf-8"))
            old_reports = previous.get("reports", [])
            old_daily = next((x for x in old_reports if x.get("type") == "daily"), None)
            old_weekly = next((x for x in old_reports if x.get("type") == "weekly"), None)
            now_local = dt.datetime.fromisoformat(result["updated"])
            if old_daily and (now_local.hour < 7 or (now_local.hour >= 7 and old_daily.get("date") == result["reports"][0]["date"])):
                result["reports"][0] = old_daily
            if old_weekly and not any(x.get("type") == "weekly" for x in result["reports"]):
                result["reports"].append(old_weekly)
        except (ValueError, OSError, TypeError, AttributeError):
            pass
    REPORTS.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("Generated", len(result["reports"]), "templated briefings")

if __name__ == "__main__":
    main()
