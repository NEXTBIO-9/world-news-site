#!/usr/bin/env python3
"""Build a conservative, source-linked event timeline from published articles.

This is a navigation aid, not independent fact verification or a prediction.
"""
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / 'data/articles.json'
OUTPUT = ROOT / 'data/event-timelines.json'
STOP = {'the', 'and', 'for', 'with', 'from', 'after', 'amid', 'says', 'said',
        'new', 'news', 'latest', 'report', 'reports', 'today', 'over', 'into'}


def tokens(title):
    return {word for word in re.findall(r'[a-z0-9]{3,}|[가-힣]{2,}', str(title).lower())
            if word not in STOP}


def event_key(article):
    """Require at least two distinctive shared terms; avoid vague categories."""
    title = article.get('title') or ''
    terms = tokens(title)
    if len(terms) < 4:
        return None
    return terms


def compatible(a, b):
    if a.get('category') != b.get('category'):
        return False
    if a.get('countries') and b.get('countries') and not set(a['countries']) & set(b['countries']):
        return False
    ta, tb = event_key(a), event_key(b)
    if not ta or not tb:
        return False
    shared = ta & tb
    # Require strong lexical overlap, avoiding accidental mergers.
    return len(shared) >= 4 and len(shared) / min(len(ta), len(tb)) >= .72


def cluster(articles):
    groups = []
    for article in sorted(articles, key=lambda a: str(a.get('published') or '')):
        if not isinstance(article, dict) or not article.get('url') or not article.get('title'):
            continue
        group = next((g for g in groups if compatible(g[0], article)), None)
        if group is None:
            groups.append([article])
        elif all(item.get('url') != article['url'] for item in group):
            group.append(article)
    return groups


def build(articles):
    events = []
    for group in cluster(articles):
        if len(group) < 2:
            continue
        first = group[0]
        urls = sorted({a['url'] for a in group})
        event_id = hashlib.sha256('\n'.join(urls).encode('utf-8')).hexdigest()[:16]
        timeline = [
            {'published': a.get('published', ''), 'title': a.get('title_ko') or a['title'],
             'source': a.get('source', ''), 'url': a['url']}
            for a in group
        ]
        events.append({
            'id': event_id, 'title': first.get('title_ko') or first['title'],
            'category': first.get('category', ''), 'countries': first.get('countries', []),
            'article_count': len(group), 'distinct_sources': len({a.get('source', '') for a in group if a.get('source')}),
            'verification': 'not_independently_verified',
            'first_reported': timeline[0]['published'],
            'last_reported': timeline[-1]['published'],
            'timeline': timeline
        })
    events.sort(key=lambda e: e['last_reported'], reverse=True)
    return {'updated': datetime.now(timezone.utc).isoformat(),
            'note': 'Related headlines are grouped heuristically. Source count is not independent verification.',
            'event_count': len(events), 'events': events[:100]}


def main():
    if not FEED.exists():
        raise SystemExit('Published feed missing; preserving existing timelines')
    data = json.loads(FEED.read_text(encoding='utf-8'))
    articles = data.get('articles')
    if not isinstance(articles, list):
        raise ValueError('Invalid published feed')
    result = build(articles)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Event timelines generated:', result['event_count'])


if __name__ == '__main__':
    main()
