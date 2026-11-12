#!/usr/bin/env python3
"""Track changes in published event clusters without changing site presentation."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'event-changes.json'
EVENTS = DATA / 'event-timelines.json'


def snapshot(events):
    result = {}
    for e in events:
        if not isinstance(e, dict) or not e.get('id'):
            continue
        result[e['id']] = {'title': e.get('title', ''), 'article_count': e.get('article_count', 0),
                           'last_reported': e.get('last_reported', ''),
                           'countries': sorted(e.get('countries') or []),
                           'article_urls': sorted({t.get('url') for t in e.get('timeline', []) if isinstance(t, dict) and t.get('url')})}
    return result


def compare(old, new):
    changes = []
    for key, event in new.items():
        before = old.get(key)
        if before is None:
            changes.append({'id': key, 'change': 'new_cluster', 'title': event['title'],
                            'new_articles': event['article_urls']})
        else:
            additions = sorted(set(event['article_urls']) - set(before.get('article_urls') or []))
            if additions:
                changes.append({'id': key, 'change': 'new_coverage', 'title': event['title'],
                                'new_articles': additions})
    return changes[:100]


def main():
    data = json.loads(EVENTS.read_text(encoding='utf-8'))
    new = snapshot(data.get('events') or [])
    old = {}
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding='utf-8')).get('snapshot') or {}
        except (OSError, ValueError):
            pass
    changes = compare(old, new)
    if old == new:
        return
    output = {'updated': datetime.now(timezone.utc).isoformat(),
              'note': 'Changes describe published coverage only, not confirmed real-world event changes.',
              'changes': changes, 'snapshot': new}
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
