#!/usr/bin/env python3
"""Build factual navigation indexes, historical snapshots and coverage statistics."""
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'intelligence.json'
OFFICIAL = ('who.int', 'cdc.gov', 'ecdc.europa.eu', 'fda.gov', 'ema.europa.eu',
            'usgs.gov', 'noaa.gov', 'un.org', 'worldbank.org', 'imf.org')
TERMS = {
    'military': r'(?i)\b(?:missile|military|airstrike|blockade|troops|ceasefire|warship)\b|미사일|군사|공습|봉쇄|휴전',
    'outbreak': r'(?i)\b(?:outbreak|infection|epidemic|pandemic|measles|virus)\b|감염|유행|바이러스|확진',
    'disaster': r'(?i)\b(?:earthquake|flood|tsunami|wildfire|typhoon)\b|지진|홍수|산불|태풍',
    'clinical': r'(?i)\b(?:clinical trial|phase [123]|drug approval|FDA|EMA)\b|임상시험|신약|승인',
    'market': r'(?i)\b(?:inflation|interest rate|stock market|tariff|central bank)\b|물가|금리|증시|관세'
}


def hostname(url):
    try:
        return (urlparse(str(url)).hostname or '').lower().removeprefix('www.')
    except ValueError:
        return ''


def build(articles, now=None):
    now = now or datetime.now(timezone.utc)
    country = defaultdict(list)
    category = defaultdict(list)
    dates = Counter()
    records = []
    for a in articles:
        if not isinstance(a, dict) or not a.get('url') or not a.get('title'):
            continue
        url = str(a['url'])
        if not hostname(url):
            continue
        title = str(a.get('title_ko') or a['title'])
        source_title = str(a['title'])
        host = hostname(a.get('source_url') or url)
        official = any(host == domain or host.endswith('.' + domain) for domain in OFFICIAL)
        matched = [key for key, pattern in TERMS.items() if re.search(pattern, source_title)]
        countries = [str(c) for c in (a.get('countries') or []) if isinstance(c, str)][:10]
        cat = str(a.get('category') or '미분류')
        published = str(a.get('published') or '')
        date = published[:10] if re.fullmatch(r'\d{4}-\d{2}-\d{2}', published[:10]) else ''
        item = {'title': title, 'original_title': source_title, 'url': url,
                'published': published, 'category': cat, 'countries': countries,
                'source': str(a.get('source') or host), 'publisher_domain': host,
                'source_type': 'official_domain' if official else 'media_or_other',
                'topics': matched}
        records.append(item)
        for c in countries:
            country[c].append(item)
        category[cat].append(item)
        if date:
            dates[date] += 1
    records.sort(key=lambda a: a['published'], reverse=True)
    def group(items):
        return [{'name': name, 'articles': len(vals), 'latest': vals[0]['published'] if vals else ''}
                for name, vals in sorted(items.items(), key=lambda pair: -len(pair[1]))]
    return {'updated': now.isoformat(),
            'disclaimer': 'Coverage counts and keyword tags are descriptive only. Official-domain labels do not verify claims.',
            'total_articles': len(records), 'countries': group(country), 'categories': group(category),
            'daily_counts': [{'date': day, 'articles': count} for day, count in sorted(dates.items())],
            'articles': records[:300]}


def main():
    feed = json.loads((DATA / 'articles.json').read_text(encoding='utf-8'))
    articles = feed.get('articles')
    if not isinstance(articles, list):
        raise ValueError('Invalid news feed')
    OUT.write_text(json.dumps(build(articles), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
