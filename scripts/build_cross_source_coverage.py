#!/usr/bin/env python3
"""Read-only source coverage and cross-publisher corroboration indicators.

Publisher agreement is not fact verification. Exact event grouping is conservative.
"""
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'cross-source-coverage.json'


def publisher(article):
    for key in ('publisher_url', 'source_url', 'url'):
        try:
            host = (urlparse(str(article.get(key) or '')).hostname or '').lower().removeprefix('www.')
        except ValueError:
            host = ''
        if host and host not in ('news.google.com', 'google.com') and not host.endswith('.google.com'):
            return host
    return ''


def build(events):
    results = []
    for event in events:
        if not isinstance(event, dict):
            continue
        timeline = event.get('timeline') or []
        sources = defaultdict(set)
        for item in timeline:
            if not isinstance(item, dict):
                continue
            host = publisher(item)
            url = item.get('url')
            if host and url:
                sources[host].add(url)
        results.append({'event_id': event.get('id') or '',
                        'event_title': event.get('title') or '',
                        'publisher_domains': sorted(sources),
                        'distinct_publisher_domains': len(sources),
                        'multiple_domains_observed': len(sources) >= 2,
                        'independently_fact_checked': False})
    results.sort(key=lambda r: (-r['distinct_publisher_domains'], r['event_id']))
    return {'updated': datetime.now(timezone.utc).isoformat(),
            'method': 'event_cluster_publisher_domain_count',
            'disclaimer': 'Unknown publisher domains are excluded. Multiple domains can republish one wire story; this is not independent verification.',
            'events': results}


def main():
    data = json.loads((DATA / 'event-timelines.json').read_text(encoding='utf-8'))
    if not isinstance(data.get('events'), list):
        raise ValueError('Invalid event timeline data')
    result = build(data['events'])
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding='utf-8'))
            if old.get('events') == result['events']:
                return
        except (OSError, ValueError):
            pass
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
