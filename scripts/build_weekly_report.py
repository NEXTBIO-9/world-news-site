#!/usr/bin/env python3
"""Seven-day reporting from published articles, with source links and no speculative risk scoring."""
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'


def build(articles, now=None):
    now = now or datetime.now(timezone.utc)
    start = now - timedelta(days=7)
    unique = {}
    for a in articles:
        if not isinstance(a, dict):
            continue
        url = str(a.get('url') or '')
        p = urlparse(url)
        if p.scheme not in ('http', 'https') or not p.hostname:
            continue
        try:
            published = datetime.fromisoformat(str(a.get('published') or '').replace('Z', '+00:00')).astimezone(timezone.utc)
        except (ValueError, TypeError, OverflowError):
            continue
        if start <= published <= now:
            unique[url] = a
    records = sorted(unique.values(), key=lambda a: str(a.get('published') or ''), reverse=True)
    categories = Counter(str(a.get('category') or '미분류') for a in records)
    countries = Counter(c for a in records for c in set(v for v in (a.get('countries') or []) if isinstance(v, str)))
    return {'updated': now.isoformat(), 'window_days': 7, 'article_count': len(records),
            'disclaimer': 'Published article counts do not indicate real-world incident totals or risk.',
            'categories': [{'name': k, 'articles': v} for k, v in categories.most_common(20)],
            'countries': [{'name': k, 'articles': v} for k, v in countries.most_common(20)],
            'headlines': [{'title': a.get('title_ko') or a.get('title'), 'title_ko': a.get('title_ko', ''),
                           'original_title': a.get('original_title') or a.get('title', ''),
                           'summary_ko': a.get('summary_ko', ''), 'summary': a.get('summary', ''), 'url': a['url'],
                           'published': a.get('published', ''), 'source': a.get('source', '')}
                          for a in records[:60]]}


def main():
    archive = DATA / 'historical-index.json'
    feed = json.loads((archive if archive.exists() else DATA / 'articles.json').read_text(encoding='utf-8'))
    articles = feed.get('articles')
    if not isinstance(articles, list):
        raise ValueError('Invalid published feed')
    output = DATA / 'weekly-report.json'
    result = build(articles)
    if output.exists():
        try:
            old = json.loads(output.read_text(encoding='utf-8'))
            if all(old.get(k) == result[k] for k in ('article_count', 'categories', 'countries', 'headlines')):
                return
        except (OSError, ValueError):
            pass
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
