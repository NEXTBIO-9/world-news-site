#!/usr/bin/env python3
"""Generate evidence-linked topic monitoring summaries from published news.

Counts describe media coverage, not real-world incident counts, severity, or forecasts.
"""
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / 'data/articles.json'
OUT = ROOT / 'data/topic-monitor.json'
TOPICS = {
    'conflict': ('군사·분쟁', r'(?i)\b(?:missile|airstrike|invasion|ceasefire|blockade|military|troops|drone attack)\b|미사일|공습|침공|휴전|봉쇄|군사|병력'),
    'health': ('감염병·보건', r'(?i)\b(?:outbreak|epidemic|pandemic|measles|infection|WHO|vaccine)\b|감염병|홍역|유행|백신|확진'),
    'disaster': ('재난·기후', r'(?i)\b(?:earthquake|tsunami|typhoon|hurricane|flood|wildfire|evacuation)\b|지진|쓰나미|태풍|홍수|산불|대피'),
    'economy': ('경제·금융', r'(?i)\b(?:inflation|interest rate|central bank|recession|tariff|stock market)\b|물가|금리|중앙은행|관세|증시'),
    'biotech': ('바이오·제약', r'(?i)\b(?:clinical trial|FDA|EMA|drug approval|antibiotic resistance|biotech)\b|임상시험|신약|승인|항생제 내성|바이오'),
}
PATTERNS = {key: re.compile(expr) for key, (_, expr) in TOPICS.items()}


def build(articles):
    result = {}
    for key, (label, _) in TOPICS.items():
        matches = []
        for article in articles:
            if not isinstance(article, dict) or not article.get('url'):
                continue
            title = str(article.get('title') or '')
            if not PATTERNS[key].search(title):
                continue
            matches.append(article)
        matches.sort(key=lambda a: str(a.get('published') or ''), reverse=True)
        country_counts = Counter(c for a in matches for c in (a.get('countries') or []) if isinstance(c, str))
        result[key] = {
            'label': label, 'article_count': len(matches),
            'countries': [{'name': name, 'articles': count} for name, count in country_counts.most_common(15)],
            'latest': [
                {'title': a.get('title_ko') or a.get('title'), 'url': a['url'],
                 'published': a.get('published', ''), 'source': a.get('source', '')}
                for a in matches[:15]
            ]
        }
    return {'updated': datetime.now(timezone.utc).isoformat(),
            'method': 'keyword_match_of_published_headlines',
            'disclaimer': 'Counts reflect published headlines, not verified incident totals, risk, spread or predictions.',
            'topics': result}


def main():
    if not FEED.exists():
        raise SystemExit('Published news feed missing; preserving prior monitoring data')
    data = json.loads(FEED.read_text(encoding='utf-8'))
    if not isinstance(data.get('articles'), list):
        raise ValueError('Invalid published news feed')
    OUT.write_text(json.dumps(build(data['articles']), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Topic monitoring updated')


if __name__ == '__main__':
    main()
