#!/usr/bin/env python3
"""Build data-only geographic coverage for the existing map; no UI changes.

Country presence indicates a country tag in published coverage, not impact or risk.
"""
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'geo-coverage.json'


def build(articles, now=None):
    groups = defaultdict(list)
    for article in articles:
        if not isinstance(article, dict) or not article.get('url'):
            continue
        for country in set(c for c in (article.get('countries') or []) if isinstance(c, str) and c.strip()):
            groups[country].append(article)
    countries = []
    for name, items in groups.items():
        items.sort(key=lambda a: str(a.get('published') or ''), reverse=True)
        categories = Counter(str(a.get('category') or '미분류') for a in items)
        countries.append({
            'country': name, 'article_count': len(items),
            'categories': dict(categories.most_common(15)),
            'latest_published': items[0].get('published') or '',
            'sample_urls': [a['url'] for a in items[:10]],
            'geographic_role': 'mentioned_or_tagged_not_verified_affected'
        })
    countries.sort(key=lambda x: (-x['article_count'], x['country']))
    return {'updated': (now or datetime.now(timezone.utc)).isoformat(),
            'disclaimer': 'Country tags indicate news coverage, not verified geographic impact, event occurrence or risk.',
            'countries': countries}


def main():
    feed = json.loads((DATA / 'articles.json').read_text(encoding='utf-8'))
    if not isinstance(feed.get('articles'), list):
        raise ValueError('Invalid published feed')
    result = build(feed['articles'])
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding='utf-8'))
            if previous.get('countries') == result['countries']:
                return
        except (OSError, ValueError):
            pass
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
