#!/usr/bin/env python3
"""Country and category coverage profiles from published, linked news."""
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'coverage-profiles.json'


def build(articles, now=None):
    country = defaultdict(list)
    category = defaultdict(list)
    for a in articles:
        if not isinstance(a, dict) or not a.get('url'):
            continue
        category[str(a.get('category') or '미분류')].append(a)
        for c in set(v for v in (a.get('countries') or []) if isinstance(v, str) and v):
            country[c].append(a)

    def profiles(groups, other_key):
        result = []
        for name, items in groups.items():
            items.sort(key=lambda a: str(a.get('published') or ''), reverse=True)
            breakdown = Counter()
            publishers = set()
            for a in items:
                if other_key == 'category':
                    breakdown[str(a.get('category') or '미분류')] += 1
                else:
                    breakdown.update(set(v for v in (a.get('countries') or []) if isinstance(v, str)))
                if a.get('source'):
                    publishers.add(str(a['source']))
            result.append({
                'name': name, 'article_count': len(items),
                'distinct_source_labels': len(publishers),
                'breakdown': [{'name': k, 'articles': v} for k, v in breakdown.most_common(20)],
                'latest': [{'title': a.get('title_ko') or a.get('title') or '',
                            'url': a['url'], 'published': a.get('published') or ''}
                           for a in items[:15]]
            })
        return sorted(result, key=lambda p: (-p['article_count'], p['name']))

    return {'updated': (now or datetime.now(timezone.utc)).isoformat(),
            'disclaimer': 'Coverage profiles are descriptive. Source labels do not prove independence or correctness.',
            'countries': profiles(country, 'category'),
            'categories': profiles(category, 'country')}


def main():
    feed = json.loads((DATA / 'articles.json').read_text(encoding='utf-8'))
    if not isinstance(feed.get('articles'), list):
        raise ValueError('Invalid published feed')
    result = build(feed['articles'])
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding='utf-8'))
            if previous.get('countries') == result['countries'] and previous.get('categories') == result['categories']:
                return
        except (ValueError, OSError):
            pass
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
