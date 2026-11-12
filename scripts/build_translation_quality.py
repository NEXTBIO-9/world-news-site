#!/usr/bin/env python3
"""Source-vs-Korean title comparison and translation coverage, without changing UI."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'translation-quality.json'
HANGUL = re.compile('[가-힣]')


def build(articles):
    records = []
    for a in articles:
        if not isinstance(a, dict) or not a.get('url'):
            continue
        original = str(a.get('title') or '').strip()
        translated = str(a.get('title_ko') or '').strip()
        if not original:
            continue
        records.append({'url': a['url'], 'original_title': original,
                        'korean_title': translated,
                        'has_korean_characters': bool(HANGUL.search(translated)),
                        'same_as_original': original.casefold() == translated.casefold(),
                        'manual_review_status': 'not_reviewed'})
    translated_count = sum(r['has_korean_characters'] for r in records)
    return {'updated': datetime.now(timezone.utc).isoformat(),
            'method': 'script_detection_and_exact_title_comparison',
            'disclaimer': 'This is not a semantic translation accuracy score; translations are not independently verified.',
            'article_count': len(records), 'korean_script_count': translated_count,
            'records': records}


def main():
    feed = json.loads((DATA / 'articles.json').read_text(encoding='utf-8'))
    if not isinstance(feed.get('articles'), list):
        raise ValueError('Invalid published feed')
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
