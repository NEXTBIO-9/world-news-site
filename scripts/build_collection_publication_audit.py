#!/usr/bin/env python3
"""Audit collection-to-publication coverage without guessing about external news."""
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from news_priority import important

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'collection-publication-audit.json'


def load(path):
    result = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(result, dict) or not isinstance(result.get('articles'), list):
        raise ValueError('Expected article feed')
    return result['articles']


def build(staged, published, pending):
    staged_by_url = {a['url']: a for a in staged if isinstance(a, dict) and a.get('url')}
    published_urls = {a['url'] for a in published if isinstance(a, dict) and a.get('url')}
    pending = pending if isinstance(pending, list) else []
    pending_urls = {entry['article']['url'] for entry in pending
                    if isinstance(entry, dict) and isinstance(entry.get('article'), dict)
                    and entry['article'].get('url')}
    unpublished = []
    counts = Counter()
    for url, article in staged_by_url.items():
        if url in published_urls:
            counts['published'] += 1
            continue
        state = 'pending' if url in pending_urls else 'not_in_current_queue'
        counts[state] += 1
        if important(article):
            counts['important_unpublished'] += 1
        unpublished.append({'url': url, 'title': article.get('title') or '',
                            'important': important(article), 'state': state})
    unpublished.sort(key=lambda a: (not a['important'], a['state'], str(a['url'])))
    return {'updated': datetime.now(timezone.utc).isoformat(),
            'scope': 'latest_collected_batch_compared_to_published_and_pending_urls',
            'disclaimer': 'Not-in-queue does not prove data loss: age limits, duplicate handling, failed summaries and publication caps can explain differences.',
            'collected_unique_urls': len(staged_by_url),
            'counts': dict(sorted(counts.items())),
            'unpublished': unpublished[:500]}


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: build_collection_publication_audit.py STAGED_ARTICLES_JSON')
    result = build(load(sys.argv[1]), load(DATA / 'articles.json'),
                   json.loads((DATA / 'pending-title-news.json').read_text(encoding='utf-8')).get('pending', []))
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding='utf-8'))
            if previous.get('counts') == result['counts'] and previous.get('unpublished') == result['unpublished']:
                return
        except (OSError, ValueError):
            pass
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
