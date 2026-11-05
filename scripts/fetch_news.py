
import json
import re
import html
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from difflib import SequenceMatcher

MAX_PER_FEED = 35
MAX_TOTAL = 1000
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; WorldNews/9.1)'}

# category, subcategory, query, language, region
SEARCHES = [
    ('외교·국제', None, '국제 외교 정상회담', 'ko', 'KR'),
    ('분쟁·군사', None, '국방 군사 분쟁', 'ko', 'KR'),
    ('경제·금융', None, '세계 경제 금융 시장', 'ko', 'KR'),
    ('재해·재난', None, '지진 홍수 산불 재난', 'ko', 'KR'),
    ('제약·신약', None, '신약 개발 임상시험 제약', 'ko', 'KR'),
    ('제약·신약', None, 'clinical trials drug approval biotech', 'en', 'US'),
    ('의료기기', None, '의료기기 체외진단 의료기기 인허가', 'ko', 'KR'),
    ('의료기기', None, 'medical device diagnostics FDA', 'en', 'US'),
    ('바이오기업', None, '바이오 기업 기술이전 투자', 'ko', 'KR'),
    ('바이오기업', None, 'biotech funding biopharma licensing', 'en', 'US'),
    ('감염병', None, '감염병 유행 질병관리청', 'ko', 'KR'),
    ('감염병', None, 'infectious disease outbreak vaccine', 'en', 'US'),
    ('미생물', '세균', '세균 박테리아 병원균 연구', 'ko', 'KR'),
    ('미생물', '세균', 'bacterial pathogen microbiology research', 'en', 'US'),
    ('미생물', '세균', 'Bacillus Escherichia coli Salmonella microbiology', 'en', 'US'),
    ('미생물', '진균', '진균 곰팡이 효모 연구', 'ko', 'KR'),
    ('미생물', '진균', 'fungal Candida Aspergillus research', 'en', 'US'),
    ('미생물', '진균', 'yeast mold fungal diagnostics', 'en', 'US'),
    ('미생물', '바이러스', '바이러스학 바이러스 연구', 'ko', 'KR'),
    ('미생물', '바이러스', 'virology viral research', 'en', 'US'),
    ('미생물', '바이러스', 'viral diagnostics emerging viruses', 'en', 'US'),
    ('미생물', '항생제 내성', '항생제 내성 슈퍼박테리아', 'ko', 'KR'),
    ('미생물', '항생제 내성', 'antimicrobial resistance AMR bacteria', 'en', 'US'),
    ('미생물', '항생제 내성', 'antibiotic resistance superbugs research', 'en', 'US'),
    ('미생물', '미생물 검사', '미생물 검사 배양배지 무균시험', 'ko', 'KR'),
    ('미생물', '미생물 검사', 'microbial testing culture media sterility testing', 'en', 'US'),
    ('미생물', '미생물 검사', 'food microbiology testing contamination', 'en', 'US'),
    ('미생물', '미생물 검사', 'microbiological quality control environmental monitoring', 'en', 'US'),
    ('미생물', None, 'microbiome microbiology research', 'en', 'US'),
    ('미생물', None, '미생물 마이크로바이옴 연구', 'ko', 'KR'),
    ('일반', None, '주요 뉴스', 'ko', 'KR'),
]

def rss_url(query, language, region):
    ceid = f'{region}:{language}'
    params = urllib.parse.urlencode({
        'q': query + ' when:14d',
        'hl': language,
        'gl': region,
        'ceid': ceid
    })
    return 'https://news.google.com/rss/search?' + params

def text(node, tag):
    el = node.find(tag)
    return (el.text or '').strip() if el is not None else ''

def normalize_title(title):
    title = html.unescape(title)
    return re.sub(r'\s+', ' ', title).strip()

def title_key(title):
    title = normalize_title(title).lower()
    return re.sub(r'[^\w가-힣]+', '', title)

def fetch(category, subcategory, query, language, region):
    url = rss_url(query, language, region)
    req = urllib.request.Request(url, headers=HEADERS)

    with urllib.request.urlopen(req, timeout=25) as response:
        raw = response.read()

    root = ET.fromstring(raw)
    results = []

    for item in root.findall('.//item')[:MAX_PER_FEED]:
        title = normalize_title(text(item, 'title'))
        link = text(item, 'link')
        desc = re.sub(r'<[^>]+>', ' ', text(item, 'description'))
        desc = re.sub(r'\s+', ' ', html.unescape(desc)).strip()
        source = text(item, 'source')

        if ' - ' in title:
            candidate, publisher = title.rsplit(' - ', 1)
            if not source:
                source = publisher
            title = candidate

        if not title or not link.startswith(('https://', 'http://')):
            continue

        try:
            published = parsedate_to_datetime(
                text(item, 'pubDate')
            ).astimezone(timezone.utc).isoformat()
        except Exception:
            published = datetime.now(timezone.utc).isoformat()

        results.append({
            'category': category,
            'subcategory': subcategory or '',
            'title': title,
            'url': link,
            'summary': desc[:260],
            'source': source or 'Google News RSS',
            'published': published,
            'region': '국내' if region == 'KR' else '해외',
            'language': language,
        })

    return results

def is_duplicate(article, existing, exact_keys):
    key = title_key(article['title'])

    if not key or key in exact_keys:
        return True

    for other in existing:
        other_key = other['_key']

        if abs(len(key) - len(other_key)) > max(
            12, int(max(len(key), len(other_key)) * .25)
        ):
            continue

        if SequenceMatcher(None, key, other_key).ratio() >= .93:
            return True

    return False

def main():
    candidates = []
    succeeded = 0

    for category, subcategory, query, language, region in SEARCHES:
        try:
            items = fetch(category, subcategory, query, language, region)
            candidates.extend(items)
            succeeded += 1
            print(f'OK {category} [{language}/{region}] {len(items)} items')
        except Exception as exc:
            print(f'FAILED {category} [{language}/{region}]: {exc}')

        time.sleep(.15)

    if not candidates:
        raise RuntimeError(
            'No RSS articles retrieved; existing data preserved'
        )

    candidates.sort(
        key=lambda a: a['published'],
        reverse=True
    )

    seen_urls = set()
    seen_titles = set()
    accepted = []

    for article in candidates:
        if article['url'] in seen_urls:
            continue

        if is_duplicate(article, accepted, seen_titles):
            continue

        seen_urls.add(article['url'])
        key = title_key(article['title'])
        seen_titles.add(key)

        accepted.append({
            **article,
            '_key': key
        })

        if len(accepted) >= MAX_TOTAL:
            break

    articles = [
        {k: v for k, v in article.items() if k != '_key'}
        for article in accepted
    ]

    payload = {
        'updated': datetime.now(timezone.utc).isoformat(),
        'articles': articles
    }

    Path('data').mkdir(exist_ok=True)

    Path('data/articles.json').write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )

    print(
        f'Successful feeds: {succeeded}/{len(SEARCHES)}; '
        f'candidates: {len(candidates)}; saved: {len(articles)}'
    )

    print(
        'Microbiology:',
        sum(a['category'] == '미생물' for a in articles),
        'by subcategory:',
        {
            s: sum(a.get('subcategory') == s for a in articles)
            for s in [
                '세균',
                '진균',
                '바이러스',
                '항생제 내성',
                '미생물 검사'
            ]
        }
    )

if __name__ == '__main__':
    main()
