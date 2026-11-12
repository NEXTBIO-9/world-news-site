#!/usr/bin/env python3
"""Read-only quality gate for generated NEXT BIO news datasets."""
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / 'data' / name).read_text(encoding='utf-8'))


def validate(feed, events, topics):
    errors = []
    articles = feed.get('articles')
    if not isinstance(articles, list):
        return ['Published feed must contain an articles array']
    if len(articles) > 300:
        errors.append('Published feed exceeds 300 articles')
    urls = set()
    for a in articles:
        if not isinstance(a, dict):
            errors.append('Invalid published article')
            continue
        url = a.get('url')
        try:
            p = urlparse(str(url))
            valid = p.scheme in ('https', 'http') and bool(p.hostname)
        except ValueError:
            valid = False
        if not valid:
            errors.append('Invalid article URL')
        if url in urls:
            errors.append('Duplicate published URL')
        urls.add(url)
    event_items = events.get('events')
    if not isinstance(event_items, list):
        errors.append('Invalid event timelines')
    else:
        ids = {e.get('id') for e in event_items if isinstance(e, dict)}
        for event in event_items:
            if not isinstance(event, dict):
                errors.append('Invalid event item')
                continue
            for related in event.get('related_events', []):
                if related.get('id') not in ids:
                    errors.append('Broken cross-country event link')
    if not isinstance(topics.get('topics'), dict):
        errors.append('Invalid topic monitor')
    return errors


def main():
    errors = validate(read('articles.json'), read('event-timelines.json'),
                      read('topic-monitor.json'))
    for err in errors:
        print('QUALITY ERROR:', err, file=sys.stderr)
    if errors:
        raise SystemExit(1)
    print('NEXT BIO generated data passed validation')


if __name__ == '__main__':
    main()
