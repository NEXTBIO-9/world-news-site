#!/usr/bin/env python3
"""Data-only country coverage trend indicators; never label them geopolitical risk."""
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'country-coverage-trends.json'


def published(value):
    try:
        return datetime.fromisoformat(str(value or '').replace('Z', '+00:00')).astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def build(articles, now=None):
    now = now or datetime.now(timezone.utc)
    recent_start = now - timedelta(days=7)
    prior_start = now - timedelta(days=14)
    counts = defaultdict(lambda: [0, 0])
    for a in articles:
        if not isinstance(a, dict):
            continue
        dt = published(a.get('published'))
        if not dt or not prior_start <= dt <= now:
            continue
        period = 0 if dt >= recent_start else 1
        for c in set(v for v in (a.get('countries') or []) if isinstance(v, str) and v):
            counts[c][period] += 1
    result = []
    for name, (recent, prior) in counts.items():
        result.append({'country': name, 'articles_last_7_days': recent,
                       'articles_previous_7_days': prior,
                       'article_count_change': recent - prior,
                       'risk_score': None})
    result.sort(key=lambda x: (-x['articles_last_7_days'], x['country']))
    return {'updated': now.isoformat(),
            'disclaimer': 'Media coverage change is not a risk score. The 300-article live feed may undercount earlier days.',
            'countries': result}


def main():
    feed = json.loads((DATA / 'articles.json').read_text(encoding='utf-8'))
    if not isinstance(feed.get('articles'), list):
        raise ValueError('Invalid feed')
    result = build(feed['articles'])
    if OUT.exists():
        try:
            if json.loads(OUT.read_text(encoding='utf-8')).get('countries') == result['countries']:
                return
        except (OSError, ValueError):
            pass
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
