#!/usr/bin/env python3
"""Create source-linked military, outbreak, clinical and market cross-reference indexes."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'specialized-indexes.json'
RULES = {
    'military': r'(?i)\b(?:military|missile|airstrike|blockade|naval|troops|warship|ceasefire)\b|군사|미사일|공습|봉쇄|함정|휴전',
    'infectious_disease': r'(?i)\b(?:outbreak|epidemic|pandemic|infection|measles|cholera|influenza)\b|감염병|감염|홍역|콜레라|독감',
    'clinical_trials': r'(?i)\b(?:clinical trial|phase [123]|randomized trial|trial results)\b|임상시험|임상 [123]상',
    'market': r'(?i)\b(?:stock market|interest rate|inflation|central bank|earnings|tariff)\b|증시|금리|물가|중앙은행|실적|관세',
}
PATTERNS = {k: re.compile(v) for k, v in RULES.items()}


def build(articles, now=None):
    indexes = {k: [] for k in RULES}
    for a in articles:
        if not isinstance(a, dict) or not a.get('url'):
            continue
        title = str(a.get('title') or '')
        for key, pattern in PATTERNS.items():
            if pattern.search(title):
                indexes[key].append({
                    'title': a.get('title_ko') or title, 'url': a['url'],
                    'published': a.get('published') or '', 'source': a.get('source') or '',
                    'countries': [c for c in (a.get('countries') or []) if isinstance(c, str)][:10],
                    'verified_official_statistics': False})
    for values in indexes.values():
        values.sort(key=lambda a: a['published'], reverse=True)
        del values[100:]
    return {'updated': (now or datetime.now(timezone.utc)).isoformat(),
            'method': 'headline_keyword_index',
            'disclaimer': 'Not a military movement map, disease case count, clinical registry or real-time market feed.',
            'indexes': indexes}


def main():
    feed = json.loads((DATA / 'articles.json').read_text(encoding='utf-8'))
    if not isinstance(feed.get('articles'), list):
        raise ValueError('Invalid feed')
    result = build(feed['articles'])
    if OUT.exists():
        try:
            if json.loads(OUT.read_text(encoding='utf-8')).get('indexes') == result['indexes']:
                return
        except (OSError, ValueError):
            pass
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
