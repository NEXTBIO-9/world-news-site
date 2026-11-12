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
        timeline = e.get('timeline')
        if not isinstance(timeline, list):
            timeline = []
        countries = e.get('countries')
        if not isinstance(countries, list):
            countries = []
        result[str(e['id'])] = {'title': e.get('title', ''), 'article_count': e.get('article_count', 0),
                               'last_reported': e.get('last_reported', ''),
                               'countries': sorted(c for c in countries if isinstance(c, str)),
                               'article_urls': sorted({t['url'] for t in timeline if isinstance(t, dict)
                                                       and isinstance(t.get('url'), str) and t['url']})}
    return result


def predecessor(current, old, used):
    """Find a likely renamed cluster by shared source URLs, never by title alone."""
    urls = set(current.get('article_urls') or [])
    if not urls:
        return None
    candidates = []
    for key, previous in old.items():
        if key in used:
            continue
        before = set(previous.get('article_urls') or [])
        overlap = len(urls & before)
        if overlap >= 2 and overlap / min(len(urls), len(before)) >= 0.6:
            candidates.append((overlap, key))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    # A tie is ambiguous: do not attach an event to an arbitrary predecessor.
    return candidates[0][1] if len(candidates) == 1 or candidates[0][0] > candidates[1][0] else None


def compare(old, new):
    changes = []
    used = set()
    for key, event in new.items():
        previous_key = key if key in old and key not in used else predecessor(event, old, used)
        before = old.get(previous_key) if previous_key else None
        if previous_key:
            used.add(previous_key)
        if before is None:
            changes.append({'id': key, 'change': 'new_cluster', 'title': event['title'],
                            'new_articles': event['article_urls']})
        else:
            additions = sorted(set(event['article_urls']) - set(before.get('article_urls') or []))
            if additions:
                changes.append({'id': key, 'change': 'new_coverage', 'title': event['title'],
                                'previous_id': previous_key if previous_key != key else None,
                                'new_articles': additions})
    return changes[:100]


def main():
    data = json.loads(EVENTS.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('events'), list):
        raise ValueError('Invalid event timeline feed: expected events list')
    new = snapshot(data['events'])
    old = {}
    if OUT.exists():
        try:
            previous_data = json.loads(OUT.read_text(encoding='utf-8'))
            if not isinstance(previous_data, dict) or not isinstance(previous_data.get('snapshot'), dict):
                raise ValueError('Invalid prior event snapshot')
            old = previous_data['snapshot']
        except (OSError, ValueError) as exc:
            raise ValueError('Cannot safely compare events against corrupt prior snapshot') from exc
    changes = compare(old, new) if old else []
    if old == new:
        return
    if not old and OUT.exists():
        # A missing or corrupt snapshot must not turn all existing events into alerts.
        changes = []
    output = {'updated': datetime.now(timezone.utc).isoformat(),
              'note': 'Changes describe published coverage only, not confirmed real-world event changes.',
              'changes': changes, 'snapshot': new}
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
