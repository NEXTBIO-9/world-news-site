#!/usr/bin/env python3
"""Report news publication gaps and backlog pressure using only local data.

No external claim of complete world-news coverage is made.
"""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'publication-gaps.json'


def read(name):
    path = DATA / name
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('Invalid dataset: ' + name)
    return value


def report():
    feed = read('articles.json')
    queue = read('pending-title-news.json')
    published = feed.get('articles', [])
    pending = queue.get('pending', [])
    if not isinstance(published, list) or not isinstance(pending, list):
        raise ValueError('Invalid published or pending article array')
    published_urls = {a.get('url') for a in published if isinstance(a, dict)}
    reasons = Counter()
    waiting = []
    for entry in pending:
        if not isinstance(entry, dict) or not isinstance(entry.get('article'), dict):
            reasons['malformed_queue_entry'] += 1
            continue
        article = entry['article']
        url = article.get('url')
        if url in published_urls:
            reasons['already_published_url'] += 1
            continue
        title = str(article.get('title') or '')
        if not title or not url:
            reasons['missing_title_or_url'] += 1
            continue
        failures = max(0, int(entry.get('failures') or 0))
        reasons['awaiting_translation_or_summary'] += 1
        waiting.append({'url': url, 'title': title, 'failures': failures,
                        'published': article.get('published') or '',
                        'category': article.get('category') or ''})
    waiting.sort(key=lambda a: (-a['failures'], a['published'], a['url']))
    return {
        'updated': datetime.now(timezone.utc).isoformat(),
        'scope': 'local_published_feed_and_retained_pending_queue_only',
        'disclaimer': 'Cannot detect stories never collected from external sources. Queue entries are not independently verified.',
        'published_count': len(published),
        'pending_count': len(waiting),
        'pending_at_retry_limit': sum(a['failures'] >= 4 for a in waiting),
        'reason_counts': dict(sorted(reasons.items())),
        'pending_articles': waiting[:600],
    }


def main():
    result = report()
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding='utf-8'))
            keys = ('published_count', 'pending_count', 'pending_at_retry_limit',
                    'reason_counts', 'pending_articles')
            if all(old.get(k) == result[k] for k in keys):
                return
        except (ValueError, OSError):
            pass
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
