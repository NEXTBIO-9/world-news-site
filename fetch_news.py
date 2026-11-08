
import json
import re
import html
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from difflib import SequenceMatcher

MAX_PER_FEED = 35
MAX_TOTAL = 1800
MAX_PER_COUNTRY = 15
MAX_GENERAL = 120
ARTICLE_MAX_AGE_DAYS = 7
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


# Comprehensive world coverage. Search locale is not itself evidence of event location.
# A country tag is attached only to queries explicitly scoped to that country.
COUNTRY_FEEDS = [
    ('대한민국','South Korea','KR'),('미국','United States','US'),
    ('일본','Japan','JP'),('중국','China','SG'),('인도','India','IN'),
    ('영국','United Kingdom','GB'),('독일','Germany','DE'),
    ('프랑스','France','FR'),('이탈리아','Italy','IT'),('스페인','Spain','ES'),
    ('폴란드','Poland','PL'),('우크라이나','Ukraine','UA'),
    ('러시아','Russia','GB'),('캐나다','Canada','CA'),
    ('멕시코','Mexico','MX'),('브라질','Brazil','BR'),
    ('아르헨티나','Argentina','AR'),('호주','Australia','AU'),
    ('뉴질랜드','New Zealand','NZ'),('인도네시아','Indonesia','ID'),
    ('베트남','Vietnam','VN'),('태국','Thailand','TH'),
    ('필리핀','Philippines','PH'),('말레이시아','Malaysia','MY'),
    ('싱가포르','Singapore','SG'),('대만','Taiwan','TW'),
    ('사우디아라비아','Saudi Arabia','SA'),
    ('아랍에미리트','United Arab Emirates','AE'),
    ('이스라엘','Israel','IL'),('이란','Iran','GB'),
    ('튀르키예','Turkey','TR'),('이집트','Egypt','EG'),
    ('남아프리카공화국','South Africa','ZA'),
    ('나이지리아','Nigeria','NG'),('케냐','Kenya','KE'),
    ('파키스탄','Pakistan','PK'),('방글라데시','Bangladesh','BD'),
    ('스웨덴','Sweden','SE'),('노르웨이','Norway','NO'),
    ('스위스','Switzerland','CH'),('네덜란드','Netherlands','NL'),
    ('벨기에','Belgium','BE'),('핀란드','Finland','FI'),
    ('그리스','Greece','GR'),('포르투갈','Portugal','PT'),
    ('칠레','Chile','CL'),('콜롬비아','Colombia','CO'),
    ('페루','Peru','PE'),('에티오피아','Ethiopia','ET'),
    ('수단','Sudan','GB'),('팔레스타인','Palestine','GB'),
    ('레바논','Lebanon','LB'),('시리아','Syria','GB'),
    ('이라크','Iraq','GB'),('카타르','Qatar','QA'),
    ('카자흐스탄','Kazakhstan','KZ'),('몽골','Mongolia','MN'),
]

TOPIC_FEEDS = [
    ('정치',None,'election parliament government policy','en','US'),
    ('정치',None,'대통령 국회 정부 정책 정치','ko','KR'),
    ('경제·금융',None,'global economy inflation interest rates stocks','en','US'),
    ('경제·금융',None,'세계 경제 금융 증시 물가','ko','KR'),
    ('외교·국제',None,'diplomacy summit international relations','en','GB'),
    ('분쟁·군사',None,'war conflict military ceasefire defense','en','GB'),
    ('분쟁·군사',None,'전쟁 분쟁 군사 휴전 국방','ko','KR'),
    ('재해·재난',None,'earthquake flood wildfire disaster','en','US'),
    ('과학·기술',None,'artificial intelligence technology semiconductor space','en','US'),
    ('보건·의료',None,'public health hospitals medical research','en','US'),
]
# (category, subcategory, query, language, region, country_hint)
# Search terms must explicitly include the country; locale alone is not a location tag.
FEEDS = [(cat, sub, query, lang, region, None)
         for cat, sub, query, lang, region in SEARCHES + TOPIC_FEEDS]

# A local-language query can find reporting that English-only searches miss.
# Google News language/edition combinations are intentionally conservative.
LOCAL_EDITION = {
    '대한민국': ('ko', 'KR', '한국'),
    '일본': ('ja', 'JP', '日本'),
    '중국': ('zh-CN', 'CN', '中国'),
    '독일': ('de', 'DE', 'Deutschland'),
    '프랑스': ('fr', 'FR', 'France'),
    '이탈리아': ('it', 'IT', 'Italia'),
    '스페인': ('es', 'ES', 'España'),
    '멕시코': ('es', 'MX', 'México'),
    '브라질': ('pt-BR', 'BR', 'Brasil'),
    '아르헨티나': ('es', 'AR', 'Argentina'),
    '인도네시아': ('id', 'ID', 'Indonesia'),
    '베트남': ('vi', 'VN', 'Việt Nam'),
    '태국': ('th', 'TH', 'ประเทศไทย'),
    '튀르키예': ('tr', 'TR', 'Türkiye'),
    '네덜란드': ('nl', 'NL', 'Nederland'),
    '폴란드': ('pl', 'PL', 'Polska'),
    '포르투갈': ('pt-PT', 'PT', 'Portugal'),
    '칠레': ('es', 'CL', 'Chile'),
    '콜롬비아': ('es', 'CO', 'Colombia'),
    '페루': ('es', 'PE', 'Perú'),
}

# News-rich markets need fewer extra searches. For underrepresented countries,
# add broader economic, social, disaster and local-language discovery feeds.
HIGH_VOLUME = {'대한민국', '미국', '일본'}
for country, english, region in COUNTRY_FEEDS:
    FEEDS.extend([
        ('일반', None, f'"{english}" latest news', 'en', region, country),
        ('정치', None, f'"{english}" government election diplomacy', 'en', region, country),
        ('분쟁·군사', None, f'"{english}" security defense conflict', 'en', region, country),
        ('보건·의료', None, f'"{english}" healthcare biotech pharmaceuticals', 'en', region, country),
    ])
    if country not in HIGH_VOLUME:
        FEEDS.extend([
            ('경제·금융', None, f'"{english}" economy business trade investment', 'en', region, country),
            ('재해·재난', None, f'"{english}" flood earthquake weather disaster', 'en', region, country),
            ('과학·기술', None, f'"{english}" technology science energy', 'en', region, country),
        ])
        if country in LOCAL_EDITION:
            lang, edition, native = LOCAL_EDITION[country]
            FEEDS.append(('일반', None, f'{native} 뉴스 경제 정치 사회', lang, edition, country))

# Avoid duplicate requests with identical query/locale/category.
FEEDS = list(dict.fromkeys(FEEDS))

def rss_url(query, language, region):
    ceid = f'{region}:{language}'
    params = urllib.parse.urlencode({
        'q': query + f' when:{ARTICLE_MAX_AGE_DAYS}d',
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

def fetch(category, subcategory, query, language, region, country_hint=None):
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
            published_dt = parsedate_to_datetime(
                text(item, 'pubDate')
            ).astimezone(timezone.utc)
        except Exception:
            # 날짜가 확인되지 않은 기사는 최근 7일 기사로 간주하지 않음
            continue

        now = datetime.now(timezone.utc)
        if not now - timedelta(days=ARTICLE_MAX_AGE_DAYS) <= published_dt <= now + timedelta(minutes=5):
            continue
        published = published_dt.isoformat()

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
            'countries': [country_hint] if country_hint else [],
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

    for category, subcategory, query, language, region, country_hint in FEEDS:
        try:
            items = fetch(category, subcategory, query, language, region, country_hint)
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

    # Preserve country coverage before allowing general feeds to fill remaining slots.
    # Deduplicate by URL/title, keeping all applicable country tags from scoped searches.
    candidates.sort(key=lambda a: a['published'], reverse=True)
    unique = {}
    url_index = {}
    for a in candidates:
        key = title_key(a['title'])
        if not key:
            continue
        previous = unique.get(key) or url_index.get(a['url'])
        if previous is not None:
            previous['countries'] = sorted(set(previous['countries'] + a['countries']))
            if previous['category'] == '일반' and a['category'] != '일반':
                previous['category'] = a['category']
                previous['subcategory'] = a['subcategory']
            continue
        unique[key] = a
        url_index[a['url']] = a

    pool = list(unique.values())
    pool.sort(key=lambda a: a['published'], reverse=True)
    accepted = []
    selected = set()
    counts = {}
    # Round-robin across countries, not just one large global latest-first queue.
    country_order = [name for name, _, _ in COUNTRY_FEEDS]
    for _ in range(MAX_PER_COUNTRY):
        added = False
        for country in country_order:
            for a in pool:
                if id(a) in selected or country not in a['countries']:
                    continue
                if counts.get(country, 0) >= MAX_PER_COUNTRY:
                    break
                if any(counts.get(c, 0) >= MAX_PER_COUNTRY for c in a['countries']):
                    continue
                selected.add(id(a))
                accepted.append(a)
                for c in a['countries']:
                    counts[c] = counts.get(c, 0) + 1
                added = True
                break
        if not added or len(accepted) >= MAX_TOTAL:
            break
    general_count = 0
    for a in pool:
        if len(accepted) >= MAX_TOTAL:
            break
        if id(a) in selected:
            continue
        if a['countries']:
            if any(counts.get(c, 0) >= MAX_PER_COUNTRY for c in a['countries']):
                continue
            for c in a['countries']:
                counts[c] = counts.get(c, 0) + 1
        else:
            if general_count >= MAX_GENERAL:
                continue
            general_count += 1
        accepted.append(a)
    accepted.sort(key=lambda a: a['published'], reverse=True)

    articles = [
        {k: v for k, v in article.items() if k != '_key'}
        for article in accepted
    ]

    # Preserve verified translations across regular RSS refreshes.
    # Only reuse when both URL and original title match; never trust stale text.
    prior_translations = {}
    try:
        old_payload = json.loads(Path('data/articles.json').read_text(encoding='utf-8'))
        for old in old_payload.get('articles', []):
            if isinstance(old, dict) and old.get('translation_quality_version') == 'nllb600m-v1' and old.get('title_ko'):
                prior_translations[(old.get('url'), old.get('title'))] = old['title_ko']
    except (OSError, ValueError, TypeError):
        pass
    for article in articles:
        translated = prior_translations.get((article.get('url'), article.get('title')))
        if translated:
            article['title_ko'] = translated
            article['translation_quality_version'] = 'nllb600m-v1'


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
        f'Successful feeds: {succeeded}/{len(FEEDS)}; '
        f'candidates: {len(candidates)}; saved: {len(articles)}'
    )

    print('Country distribution:', sorted(counts.items(), key=lambda x: -x[1]))
    print('Unassigned/general articles:', general_count)
    print('Countries represented:', len(counts), '/', len(COUNTRY_FEEDS))
    print('Countries with 0 articles:', [name for name, _, _ in COUNTRY_FEEDS if counts.get(name, 0) == 0])
    print('Countries with 1-2 articles:', [(name, counts.get(name, 0)) for name, _, _ in COUNTRY_FEEDS if 0 < counts.get(name, 0) <= 2])
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
