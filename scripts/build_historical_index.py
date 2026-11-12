#!/usr/bin/env python3
"""Historical coverage archive: monthly aggregates and bounded source-linked index.

The live feed is capped at 300 articles; this index does not claim complete history.
"""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'historical-index.json'
MAX_RECORDS = 5000


def build(articles, prior=None):
    records = {}
    for item in (prior or {}).get('articles', []):
        if isinstance(item, dict) and item.get('url'):
            records[item['url']] = item
    for a in articles:
        if not isinstance(a, dict) or not a.get('url'):
            continue
        records[a['url']] = {
            'url': a['url'], 'title': a.get('title_ko') or a.get('title') or '',
            'published': a.get('published') or '',
            'category': a.get('category') or '',
            'countries': [c for c in (a.get('countries') or []) if isinstance(c, str)][:10],
            'source': a.get('source') or ''
        }
    items = sorted(records.values(), key=lambda x: str(x.get('published') or ''), reverse=True)[:MAX_RECORDS]
    months = Counter(a['published'][:7] for a in items if len(a.get('published') or '') >= 7)
    return {'updated': datetime.now(timezone.utc).isoformat(), 'max_records': MAX_RECORDS,
            'disclaimer': 'Incremental archive of articles seen since deployment; not a complete historical database.',
            'article_count': len(items),
            'monthly_counts': [{'month': k, 'articles': v} for k, v in sorted(months.items())],
            'articles': items}


def main():
    feed = json.loads((DATA / 'articles.json').read_text(encoding='utf-8'))
    if not isinstance(feed.get('articles'), list):
        raise ValueError('Invalid published feed')
    old = {}
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            pass
    result = build(feed['articles'], old)
    if old.get('articles') == result['articles']:
        return
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
