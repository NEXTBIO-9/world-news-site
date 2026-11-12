#!/usr/bin/env python3
"""Compact source provenance and coverage limitations, without UI changes."""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'source-provenance.json'


def domain(url):
    try:
        parsed = urlparse(str(url or ''))
        return (parsed.hostname or '').lower().removeprefix('www.') if parsed.scheme in ('https', 'http') else ''
    except ValueError:
        return ''


def build(articles):
    records = []
    domains = Counter()
    seen = set()
    for article in articles:
        if not isinstance(article, dict):
            continue
        url = str(article.get('url') or '')
        if not domain(url) or url in seen:
            continue
        seen.add(url)
        publisher = domain(article.get('source_url') or article.get('publisher_url') or url)
        domains[publisher or 'unknown'] += 1
        records.append({'url': url, 'publisher_domain': publisher,
                        'source_label': article.get('source') or '',
                        'published': article.get('published') or '',
                        'citation_type': 'article_link',
                        'verified_against_primary_source': False})
    return {'updated': datetime.now(timezone.utc).isoformat(),
            'disclaimer': 'A source URL is a citation to published coverage, not independent verification. Publisher domains may be unavailable or syndication hosts.',
            'total_linked_articles': len(records),
            'publisher_counts': [{'domain': k, 'articles': v} for k, v in domains.most_common()],
            'records': records}


def main():
    feed = json.loads((DATA / 'articles.json').read_text(encoding='utf-8'))
    if not isinstance(feed.get('articles'), list):
        raise ValueError('Invalid published feed')
    result = build(feed['articles'])
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding='utf-8'))
            if all(old.get(key) == result[key] for key in ('records', 'publisher_counts')):
                return
        except (ValueError, OSError):
            pass
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
