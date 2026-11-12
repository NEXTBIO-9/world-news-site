#!/usr/bin/env python3
"""Evidence metadata for published news: no inferred truth or risk scores."""
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'evidence-index.json'
OFFICIAL = {'who.int': 'WHO', 'cdc.gov': 'US CDC', 'fda.gov': 'US FDA',
            'ema.europa.eu': 'EMA', 'ecdc.europa.eu': 'ECDC',
            'usgs.gov': 'USGS', 'noaa.gov': 'NOAA', 'un.org': 'UN',
            'imf.org': 'IMF', 'worldbank.org': 'World Bank'}


def host(url):
    try:
        parsed = urlparse(str(url or ''))
        if parsed.scheme not in ('http', 'https'):
            return ''
        return (parsed.hostname or '').lower().removeprefix('www.')
    except ValueError:
        return ''


def official_name(domain):
    for suffix, name in OFFICIAL.items():
        if domain == suffix or domain.endswith('.' + suffix):
            return name
    return None


def build(articles, now=None):
    records = []
    for article in articles:
        if not isinstance(article, dict):
            continue
        url = str(article.get('url') or '')
        if not host(url):
            continue
        publisher = host(article.get('source_url') or article.get('publisher_url') or url)
        official = official_name(publisher)
        records.append({'url': url, 'title': article.get('title_ko') or article.get('title') or '',
                        'published': article.get('published') or '',
                        'publisher_domain': publisher,
                        'official_organization': official,
                        'classification': 'official_domain' if official else 'unclassified',
                        'independently_verified': False,
                        'evidence_links': [url]})
    return {'updated': (now or datetime.now(timezone.utc)).isoformat(),
            'method': 'publisher_domain_classification_only',
            'disclaimer': 'An official domain is not proof that a claim is true. No independent verification is performed.',
            'record_count': len(records), 'records': records}


def main():
    feed = json.loads((DATA / 'articles.json').read_text(encoding='utf-8'))
    if not isinstance(feed.get('articles'), list):
        raise ValueError('Invalid published articles')
    result = build(feed['articles'])
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding='utf-8'))
            if old.get('records') == result['records']:
                return
        except (ValueError, OSError):
            pass
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
