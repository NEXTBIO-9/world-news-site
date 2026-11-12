#!/usr/bin/env python3
"""Read-only breaking-news candidates based on explicit headline terms.

This is a triage queue, not confirmation of a breaking event.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'breaking-candidates.json'
PATTERN = re.compile(r'(?i)\b(?:breaking|urgent|earthquake|tsunami|missile launch|airstrike|outbreak|evacuation|ceasefire)\b|속보|긴급|지진|쓰나미|미사일 발사|공습|집단감염|대피|휴전')


def build(articles, now=None):
    found = []
    seen = set()
    for a in sorted((x for x in articles if isinstance(x, dict)),
                    key=lambda x: str(x.get('published') or ''), reverse=True):
        url = a.get('url')
        title = str(a.get('title') or '')
        if not url or url in seen or not PATTERN.search(title):
            continue
        seen.add(url)
        found.append({'title': a.get('title_ko') or title, 'original_title': title,
                      'url': url, 'published': a.get('published') or '',
                      'category': a.get('category') or '', 'status': 'unverified_candidate'})
    return {'updated': (now or datetime.now(timezone.utc)).isoformat(),
            'disclaimer': 'Keyword-based candidate detection is not a verified breaking-news alert.',
            'candidates': found[:100]}


def main():
    feed = json.loads((DATA / 'articles.json').read_text(encoding='utf-8'))
    if not isinstance(feed.get('articles'), list):
        raise ValueError('Invalid feed')
    result = build(feed['articles'])
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding='utf-8'))
            if previous.get('candidates') == result['candidates']:
                return
        except (OSError, ValueError):
            pass
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
