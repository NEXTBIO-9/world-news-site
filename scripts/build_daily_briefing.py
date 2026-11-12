#!/usr/bin/env python3
"""Daily source-linked briefing from already published headlines; no generated claims."""
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / 'data/articles.json'
OUT = ROOT / 'data/daily-briefing.json'


def valid_url(value):
    try:
        parsed = urlparse(str(value))
        return parsed.scheme in ('https', 'http') and bool(parsed.hostname)
    except ValueError:
        return False


def parse_date(value):
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00')).astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def build(articles, now=None):
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)
    selected = []
    seen = set()
    for a in articles:
        if not isinstance(a, dict) or not valid_url(a.get('url')):
            continue
        when = parse_date(a.get('published'))
        if when is None or not cutoff <= when <= now or a['url'] in seen:
            continue
        seen.add(a['url'])
        selected.append(a)
    selected.sort(key=lambda a: str(a.get('published') or ''), reverse=True)
    countries = Counter(c for a in selected for c in set(v for v in (a.get('countries') or []) if isinstance(v, str)))
    categories = Counter(str(a.get('category') or '미분류') for a in selected)
    return {
        'updated': now.isoformat(), 'window_hours': 24,
        'disclaimer': 'Article counts describe coverage, not verified events or risk.',
        'article_count': len(selected),
        'top_categories': [{'name': k, 'count': v} for k, v in categories.most_common(10)],
        'top_countries': [{'name': k, 'count': v} for k, v in countries.most_common(10)],
        'headlines': [{'title': a.get('title_ko') or a.get('title') or '제목 없음',
                       'url': a['url'], 'published': a.get('published', ''),
                       'source': a.get('source', ''), 'category': a.get('category', '')}
                      for a in selected[:40]]
    }


def main():
    if not FEED.exists():
        raise SystemExit('Published feed missing')
    feed = json.loads(FEED.read_text(encoding='utf-8'))
    if not isinstance(feed.get('articles'), list):
        raise ValueError('Invalid feed')
    result = build(feed['articles'])
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding='utf-8'))
            keys = ('article_count', 'top_categories', 'top_countries', 'headlines')
            if all(old.get(k) == result[k] for k in keys):
                return
        except (OSError, ValueError):
            pass
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
