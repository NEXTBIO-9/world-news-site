#!/usr/bin/env python3
"""Build a conservative, source-linked event timeline from published articles.

This is a navigation aid, not independent fact verification or a prediction.
"""
import hashlib
import json
import re
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta
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


def publication_time(article):
    try:
        return datetime.fromisoformat(str(article.get('published') or '').replace('Z', '+00:00')).astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def compatible(a, b):
    if a.get('category') != b.get('category'):
        return False
    if a.get('countries') and b.get('countries') and not set(a['countries']) & set(b['countries']):
        return False
    da, db = publication_time(a), publication_time(b)
    if da and db and abs(da - db) > timedelta(days=14):
        return False
    ta, tb = event_key(a), event_key(b)
    if not ta or not tb:
        return False
    shared = ta & tb
    # Require strong lexical overlap, avoiding accidental mergers.
    return len(shared) >= 4 and len(shared) / min(len(ta), len(tb)) >= .72


def cluster(articles):
    groups = []
    seen_urls = set()
    valid_articles = (a for a in articles if isinstance(a, dict) and a.get('url') and a.get('title'))
    for article in sorted(valid_articles, key=lambda a: (str(a.get('published') or ''), str(a['url']))):
        if article['url'] in seen_urls:
            continue
        seen_urls.add(article['url'])
        group = next((g for g in groups if all(compatible(existing, article) for existing in g)), None)
        if group is None:
            groups.append([article])
        else:
            group.append(article)
    return groups


def publisher(article):
    """Prefer the publisher's hostname over a potentially inconsistent source label."""
    for value in (article.get('source_url'), article.get('publisher_url'), article.get('url')):
        if not value:
            continue
        try:
            host = (urlparse(str(value)).hostname or '').lower().removeprefix('www.')
        except ValueError:
            continue
        if host and not host.endswith('news.google.com'):
            return host
    return str(article.get('source') or '').strip().casefold()


def cross_country_links(events):
    """Suggest related coverage, never infer causality or shared actors."""
    for event in events:
        event['related_events'] = []
    for i, left in enumerate(events):
        left_countries = set(left.get('countries') or [])
        if not left_countries:
            continue
        for right in events[i + 1:]:
            right_countries = set(right.get('countries') or [])
            if not right_countries or left_countries & right_countries:
                continue
            if left.get('category') != right.get('category'):
                continue
            a, b = tokens(left.get('original_title', '')), tokens(right.get('original_title', ''))
            if len(a) < 5 or len(b) < 5:
                continue
            shared = a & b
            if len(shared) < 4 or len(shared) / min(len(a), len(b)) < .75:
                continue
            left['related_events'].append({'id': right['id'], 'title': right['title'],
                                           'countries': right_countries and sorted(right_countries),
                                           'basis': 'headline_similarity_only'})
            right['related_events'].append({'id': left['id'], 'title': left['title'],
                                            'countries': sorted(left_countries),
                                            'basis': 'headline_similarity_only'})
    for event in events:
        event['related_events'] = event['related_events'][:5]
        event.pop('original_title', None)


def build(articles):
    events = []
    for group in cluster(articles):
        if len(group) < 2:
            continue
        first = group[0]
        event_id = hashlib.sha256(str(first['url']).encode('utf-8')).hexdigest()[:16]
        timeline = [
            {'published': a.get('published', ''), 'title': a.get('title_ko') or a['title'],
             'source': a.get('source', ''), 'url': a['url'],
             'source_url': a.get('source_url') or '',
             'publisher_url': a.get('publisher_url') or ''}
            for a in group
        ]
        events.append({
            'id': event_id, 'title': first.get('title_ko') or first['title'],
            'original_title': first['title'],
            'category': first.get('category', ''),
            'countries': sorted({c for a in group for c in (a.get('countries') or []) if isinstance(c, str)}),
            'article_count': len(group), 'distinct_sources': len({publisher(a) for a in group if publisher(a)}),
            'verification': 'not_independently_verified',
            'first_reported': timeline[0]['published'],
            'last_reported': timeline[-1]['published'],
            'timeline': timeline
        })
    events.sort(key=lambda e: e['last_reported'], reverse=True)
    events = events[:100]
    cross_country_links(events)
    return {'updated': datetime.now(timezone.utc).isoformat(),
            'note': 'Related headlines are grouped heuristically. Cross-country links indicate headline similarity, not causation or independent verification.',
            'event_count': min(len(events), 100), 'events': events[:100]}


def main():
    if not FEED.exists():
        raise SystemExit('Published feed missing; preserving existing timelines')
    data = json.loads(FEED.read_text(encoding='utf-8'))
    articles = data.get('articles')
    if not isinstance(articles, list):
        raise ValueError('Invalid published feed')
    result = build(articles)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if OUTPUT.exists():
        try:
            previous = json.loads(OUTPUT.read_text(encoding='utf-8'))
            if previous.get('events') == result['events']:
                print('Event timelines unchanged; keeping previous update time')
                return
        except (OSError, ValueError, AttributeError):
            pass
    OUTPUT.write_text(payload, encoding='utf-8')
    print('Event timelines generated:', result['event_count'])


if __name__ == '__main__':
    main()
