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
    staged_by_url = {a['url']: a for a in staged if isinstance(a, dict) and isinstance(a.get('url'), str) and a['url']}
    published_urls = {a['url'] for a in published if isinstance(a, dict) and isinstance(a.get('url'), str) and a['url']}
    pending = pending if isinstance(pending, list) else []
    pending_urls = {entry['article']['url'] for entry in pending
                    if isinstance(entry, dict) and isinstance(entry.get('article'), dict)
                    and isinstance(entry['article'].get('url'), str) and entry['article']['url']}
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
    important_states = dict(Counter(a['state'] for a in unpublished if a['important']))
    # Distinguish queued priority reports from those requiring manual diagnosis.
    # A missing queue entry alone is not proof of a dropped article.
    return {'updated': datetime.now(timezone.utc).isoformat(),
            'scope': 'latest_collected_batch_compared_to_published_and_pending_urls',
            'disclaimer': 'Not-in-queue does not prove data loss: age limits, duplicate handling, failed summaries and publication caps can explain differences.',
            'collected_unique_urls': len(staged_by_url),
            'counts': dict(sorted(counts.items())),
            'important_unpublished_by_state': important_states,
            'important_requires_review': [a for a in unpublished if a['important'] and a['state'] == 'not_in_current_queue'][:100],
            'unpublished': unpublished[:500]}


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: build_collection_publication_audit.py STAGED_ARTICLES_JSON')
    pending_path = DATA / 'pending-title-news.json'
    pending_data = json.loads(pending_path.read_text(encoding='utf-8')) if pending_path.exists() else {}
    if not isinstance(pending_data, dict):
        pending_data = {}
    result = build(load(sys.argv[1]), load(DATA / 'articles.json'), pending_data.get('pending', []))
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding='utf-8'))
            if all(previous.get(k) == result[k] for k in ('counts', 'important_unpublished_by_state', 'important_requires_review', 'unpublished')):
                return
        except (OSError, ValueError):
            pass
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
