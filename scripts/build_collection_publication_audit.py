#!/usr/bin/env python3
"""Audit collection-to-publication coverage without guessing about external news."""
import json
import re
import html
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


def rss_fallback_candidate(article):
    """Diagnostic only: a substantive RSS description, never automatic publication."""
    title = str(article.get('title') or '').strip()
    raw = html.unescape(str(article.get('summary') or '')).strip()
    raw = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', raw)).strip()
    normalized = lambda value: re.sub(r'[^\w]+', '', value.casefold())
    body, heading = normalized(raw), normalized(title)
    return bool(title and len(raw) >= 85 and len(body) >= max(65, int(len(heading) * 1.25))
                and body != heading and not (body.startswith(heading) and len(body) < len(heading) * 1.6))


def build(staged, published, pending, summary_cache=None, excluded=None):
    summary_cache = summary_cache if isinstance(summary_cache, dict) else {}
    blocked = summary_cache.get('blocked_urls') or {}
    nonextractable = summary_cache.get('nonextractable_counts') or {}
    excluded = excluded if isinstance(excluded, list) else []
    excluded_urls = {item[0] for item in excluded if isinstance(item, list) and len(item) == 2 and isinstance(item[0], str)}
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
        reason = 'in_retry_queue' if state == 'pending' else 'unexplained_not_queued'
        if state != 'pending':
            if url in blocked:
                reason = 'source_blocked'
            elif int(nonextractable.get(url, 0) or 0) >= 3:
                reason = 'repeated_extraction_failure'
            elif url in excluded_urls:
                reason = 'title_retry_excluded'
        unpublished.append({'url': url, 'title': article.get('title') or '',
                            'important': important(article), 'state': state, 'reason': reason,
                            'rss_fallback_candidate': rss_fallback_candidate(article) if reason == 'source_blocked' else False})
    unpublished.sort(key=lambda a: (not a['important'], a['state'], str(a['url'])))
    important_states = dict(Counter(a['state'] for a in unpublished if a['important']))
    important_reasons = dict(Counter(a['reason'] for a in unpublished if a['important']))
    # Distinguish queued priority reports from those requiring manual diagnosis.
    # A missing queue entry alone is not proof of a dropped article.
    return {'updated': datetime.now(timezone.utc).isoformat(),
            'scope': 'latest_collected_batch_compared_to_published_and_pending_urls',
            'disclaimer': 'Not-in-queue does not prove data loss: age limits, duplicate handling, failed summaries and publication caps can explain differences.',
            'collected_unique_urls': len(staged_by_url),
            'counts': dict(sorted(counts.items())),
            'important_unpublished_by_state': important_states,
            'important_unpublished_by_reason': important_reasons,
            'blocked_important_rss_candidates': sum(a['rss_fallback_candidate'] for a in unpublished if a['important'] and a['reason'] == 'source_blocked'),
            'important_requires_review': [a for a in unpublished if a['important'] and a['state'] == 'not_in_current_queue'][:100],
            'unpublished': unpublished[:500]}


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: build_collection_publication_audit.py STAGED_ARTICLES_JSON')
    pending_path = DATA / 'pending-title-news.json'
    pending_data = json.loads(pending_path.read_text(encoding='utf-8')) if pending_path.exists() else {}
    if not isinstance(pending_data, dict):
        pending_data = {}
    cache_path = DATA / 'article-summaries.json'
    summary_cache = json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
    result = build(load(sys.argv[1]), load(DATA / 'articles.json'), pending_data.get('pending', []),
                   summary_cache, pending_data.get('excluded', []))
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding='utf-8'))
            if all(previous.get(k) == result[k] for k in ('counts', 'important_unpublished_by_state', 'important_unpublished_by_reason', 'blocked_important_rss_candidates', 'important_requires_review', 'unpublished')):
                return
        except (OSError, ValueError):
            pass
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
