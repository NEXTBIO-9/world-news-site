
import json
import collections
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
MAX_TOTAL = 180
MAX_PER_COUNTRY = 6
MAX_GENERAL = 80
ARTICLE_MAX_AGE_DAYS = 3
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

# Quality filter: conservative, transparent title-based scoring.
# It does not claim to verify article content or publisher reliability.
NOISE_PATTERNS = [
    r'(?i)\b(FIFA sanctions|World Cup final clashes|appeals FIFA sanctions|celebrity|tourist arrivals target)\b',
    r'(?i)\b(horoscope|zodiac|lottery numbers|celebrity gossip|red carpet|box office|recipe|fashion tips|shopping deals|coupon|viral video|dating advice|travel guide|restaurant review|football scores|match highlights|transfer rumours|transfer rumors)\b',
    r'오늘의 운세|별자리 운세|로또 당첨번호|연예인 근황|열애설|결별설|맛집 추천|오늘의 레시피|할인 쿠폰|쇼핑 특가|경기 결과|이적설|패션 화보|방송 예고|미스 유니버스|선수 부상',
    r'(?i)\b(miss universe|beauty pageant|ankle injury|ruled out of .* tour|weekly wrap-up|weekly roundup|horoscope|celebrity wedding|match preview|sports scores|football match|cricket match|player injury|celebrity|reality show|movie premiere|best restaurants|travel tips|daily horoscope|weekend guide)\b',
    r'(?i)\b(footballer|cricketer|striker|goalkeeper)\b.*\b(injury|injured|ruled out|transfer)\b',
    r'연예인|아이돌|미인대회|스포츠 경기|축구 선수|야구 선수|크리켓 선수|주말 여행|주간 소식 모음',
]
HIGH_IMPACT = [
    r'(?i)\b(war|ceasefire|peace deal|sanctions|tariff|trade agreement|election|president|prime minister|parliament|central bank|interest rates?|inflation|recession|earthquake|wildfire|floods?|hurricane|pandemic|outbreak|FDA approval|clinical trial|phase [123]|semiconductor|artificial intelligence|AI regulation|nuclear|missile|treaty|vaccine|antibiotic resistance|antimicrobial resistance|drug approval|merger|acquisition)\b',
    r'전쟁|휴전|제재|관세|무역협정|대통령|총리|정상회담|선거|국회|금리|인플레이션|물가|지진|산불|홍수|태풍|감염병|백신|임상시험|신약 승인|반도체|인공지능|핵무기|미사일|조약|항생제 내성|기술이전|인수합병',
]
BIOMEDICAL = [
    r'(?i)\b(biotech|biopharma|pharmaceutical|clinical trial|FDA|EMA|drug approval|medical device|diagnostic|pathogen|bacteria|bacterial|fungal|virus|virology|microbiology|microbiome|antibiotic|antimicrobial|sterility testing|culture media|vaccine|genome|genomic)\b',
    r'바이오|제약|신약|임상|의료기기|체외진단|병원균|세균|진균|바이러스|미생물|마이크로바이옴|항생제|배양배지|무균시험|백신|유전체',
]
LOW_INFORMATION = [
    r'(?i)^(watch|photos?|video|live blog|opinion|what to know|explained|here\'s why|top \d+|how to)\b',
    r'^\[?(영상|사진|포토|칼럼|사설|기고)\]?',
    r'(?i)\b(weekly review|week in review|weekly digest|market roundup|daily roundup|morning briefing)\b',
    r'주간 종합|한 주간의 소식|이번 주 주요 뉴스',
]

# An event/action in the headline is stronger evidence than the RSS query category.
EVENT_SIGNALS = [
    r'(?i)\b(approves?|approved|passes?|passed|announces?|announced|signs?|signed|launches?|launched|bans?|banned|raises?|raised|cuts?|cut|strikes?|struck|attacks?|attacked|kills?|killed|arrests?|arrested|investigates?|investigation|recalls?|recalled|acquires?|acquired|merges?|merged|files? for|reports?|reported|discovers?|discovered|develops?|developed|publishes?|published|confirms?|confirmed|reaches?|reached|surges?|surged|falls?|fell|declines?|declined|outbreak|earthquake|flood|wildfire|ceasefire|sanctions|tariffs|trial results|phase [123])\b',
    r'발표|승인|통과|체결|서명|금지|인상|인하|공격|사망|체포|수사|조사|리콜|인수|합병|상장|발견|개발|확인|급등|급락|폭락|발생|확산|휴전|제재|관세|임상 결과|실적|지진|홍수|산불|파업|투자|수출|수입|감염',
]

def quality_score(article):
    title = article.get('title', '').strip()
    if len(title) < (10 if re.search(r'[가-힣]', title) else 18) or len(title) > 240:
        return 0
    if any(re.search(p, title) for p in NOISE_PATTERNS):
        return 0
    category = article.get('category', '')
    # Category indicates search intent, not verified content.
    score = 42
    if category == '일반':
        score -= 8
    if category in {'외교·국제', '분쟁·군사', '경제·금융', '정치', '재해·재난'}:
        score += 14
    elif category in {'제약·신약', '의료기기', '바이오기업', '감염병', '미생물', '보건·의료'}:
        score += 16
    elif category == '과학·기술':
        score += 10
    impact = any(re.search(p, title) for p in HIGH_IMPACT)
    event = any(re.search(p, title) for p in EVENT_SIGNALS)
    if impact:
        score += 25
    if event:
        score += 12
    if not impact and not event:
        score -= 15
    if category in {'제약·신약', '의료기기', '바이오기업', '감염병', '미생물', '보건·의료'} and any(re.search(p, title) for p in BIOMEDICAL):
        score += 18
    if any(re.search(p, title) for p in LOW_INFORMATION):
        score -= 25
    if not article.get('source') or article['source'] == 'Google News RSS':
        score -= 8
    try:
        age_hours = (datetime.now(timezone.utc) - datetime.fromisoformat(article['published'])).total_seconds() / 3600
        if age_hours > 48:
            score -= 10
        elif age_hours > 24:
            score -= 4
    except (ValueError, TypeError, KeyError):
        score -= 10
    return max(0, min(100, score))

MIN_QUALITY_SCORE = 68

# Country-scoped Google queries are not proof of country relevance.
# Require a country reference in the title for English queries.
COUNTRY_ENGLISH = {name: english for name, english, _ in COUNTRY_FEEDS}
COUNTRY_NATIVE = {
    '대한민국': ('한국', '대한민국', '우리나라', '韓国', '한국은행'),
    '미국': ('미국', '美國', '美联储'),
    '일본': ('일본', '日本'),
    '중국': ('중국', '中国', '中國'),
    '독일': ('독일', 'Deutschland'),
    '프랑스': ('프랑스',),
    '이탈리아': ('이탈리아', 'Italia'),
    '스페인': ('스페인', 'España'),
    '브라질': ('브라질', 'Brasil'),
    '베트남': ('베트남', 'Việt Nam'),
    '태국': ('태국', 'ประเทศไทย'),
    '튀르키예': ('튀르키예', '터키', 'Türkiye'),
    '러시아': ('러시아',),
    '우크라이나': ('우크라이나',),
    '인도': ('인도',),
    '영국': ('영국',),
    '아랍에미리트': ('아랍에미리트',),
}
COUNTRY_ALIASES = {
    '대한민국': r'\b(?:South Korea|South Korean|Republic of Korea)\b',
    '미국': r'\b(?:U\.S\.|USA|United States|American|Americans)\b',
    '영국': r'\b(?:U\.K\.|Britain|British|United Kingdom)\b',
    '아랍에미리트': r'\b(?:UAE|United Arab Emirates|Emirati)\b',
    '튀르키예': r'\b(?:Turkey|Turkish|Türkiye)\b',
}

# Known ambiguous place names must not be treated as countries.
AMBIGUOUS_COUNTRY_PLACE = [
    (r'(?i)\b(?:Mt\.?|Mount) Lebanon\b', '레바논'),
    (r'(?i)\b(?:New York|New Jersey|New Hampshire)\b', None),
]

def infer_category(article):
    """Use explicit headline evidence before the broad RSS search category."""
    t = article.get('title', '')
    rules = [
        ('재해·재난', r'(?i)\b(?:earthquake|quake|tremor|tsunami|wildfires?|flooding|floods?|hurricane|typhoon|landslide|volcanic eruption)\b|지진|여진|쓰나미|산불|홍수|태풍|산사태'),
        ('분쟁·군사', r'(?i)\b(?:missile (?:strike|attack|launch)|missiles? (?:targeting|intercepted)|intercepts? .*missile|drone attack|military base attack|airstrike|ceasefire|offensive in (?:Lebanon|Ukraine)|gunman|shooting|armed attack|soldiers? (?:killed|injured))\b|미사일 (?:공격|요격|발사)|드론 공격|군사기지 공격|총격|휴전|공습'),
        ('정치', r'(?i)\b(?:presidential election|parliamentary election|election results|parliament votes|prime minister resigns|government coalition)\b|대통령 선거|총선 결과|국회 표결|총리 사임'),
        ('경제·금융', r'(?i)\b(?:central bank|interest rate|rate decision|inflation|ECB|European Central Bank|oil (?:prices?|touches|surges)|tariffs?)\b|중앙은행|기준금리|금리 (?:동결|인상|인하)|물가|인플레이션|관세'),
        ('제약·신약', r'(?i)\b(?:phase [123] (?:clinical )?trial|drug approval|FDA approves? (?:a |the )?(?:drug|therapy)|EMA approves? (?:a |the )?(?:drug|therapy))\b|임상(?:시험)? [123]상|신약 (?:승인|허가)'),
        ('의료기기', r'(?i)\b(?:medical device (?:approval|recall)|diagnostic device approved|FDA clears? (?:a |the )?(?:device|test))\b|의료기기 (?:승인|허가|리콜)'),
        ('감염병', r'(?i)\b(?:measles|mpox|infectious disease outbreak|disease outbreak|pandemic)\b|홍역|감염병 (?:확산|유행|발생)'),
        ('미생물', r'(?i)\b(?:antibacterial activity|microbiome causal|microbial testing|microbiology research|drug-resistant (?:bacteria|pseudomonas))\b|항균 활성|미생물군집|내성균 연구'),
    ]
    # Preserve specialist RSS labels unless the headline explicitly signals a disaster or military conflict.
    specialist = article.get('category') in SPECIALIST_CATEGORIES
    for category, pattern in rules:
        if specialist and category not in ('재해·재난', '분쟁·군사'):
            continue
        if re.search(pattern, t):
            article['category'] = category
            if category != '미생물':
                article['subcategory'] = ''
            return

# Small, routine tremors are not major news without documented harm or warnings.
MICRO_QUAKE = re.compile(r'(?i)\b(?:weak|light|minor|moderate)?\s*(?:mag(?:nitude)?\.?|magnitude[- ]?)\s*([0-9]+(?:\.[0-9]+)?)\b')
QUAKE_HARM = re.compile(r'(?i)\b(?:kill|kills|killed|dead|death|deaths|injure|injures|injured|casualties|fatalities|evacuated|damage|collapsed|tsunami warning|emergency|major disruption)\b|사망|부상|피해|대피|쓰나미 경보|붕괴')
ROUTINE_QUAKE = re.compile(r'(?i)\b(?:weak|light|minor)\s+mag\.?|\b(?:unconfirmed earthquake|seismic-like event)\b')

def is_routine_quake(article):
    t = article.get('title', '')
    if not re.search(r'(?i)\b(?:earthquake|quake|tremor|seismic-like event)\b|지진', t):
        return False
    if QUAKE_HARM.search(re.sub(r'(?i)\bno tsunami warning\b', '', t)):
        return False
    match = MICRO_QUAKE.search(t)
    if match and float(match.group(1)) < 4.5:
        return True
    return bool(ROUTINE_QUAKE.search(t) and not re.search(r'(?i)\b(?:major|strong|powerful)\b', t))

# Phase 9: suppress generic, low-information records without rejecting major events.
# Keep this narrow: a source's reputation is not proof of factual correctness.
LOW_VALUE_RECORDS = [
    r'(?i)\b(?:unconfirmed earthquake|seismic-like event|earthquake or seismic-like event)\b',
    r'(?i)\b(?:earthquake|quake)\b.*\b(?:no damage|no injuries)\b.*\b(?:magnitude|mag\.)\s*[0-3](?:\.\d+)?\b',
    r'(?i)\b(?:guide to (?:medical device|.* APIs)|database: search guide|scope, APC & review)\b',
    r'(?i)\b(?:API documentation|developer documentation|searchable database|privacy policy|terms of service|subscription plans|event calendar|conference agenda|job openings|careers at|press release archive)\b',
    r'(?i)\b(?:live earthquake map|earthquake tracker|latest earthquakes list|historical earthquake catalog)\b',
    r'개발자 문서|이용약관|개인정보처리방침|채용 공고|행사 일정|학회 일정|보도자료 목록',
]
MAX_PER_SOURCE = 12  # soft cap; unused slots are backfilled below


def is_low_value_record(article):
    return any(re.search(p, article.get('title', '')) for p in LOW_VALUE_RECORDS)


def event_date(article):
    try:
        return datetime.fromisoformat(article['published'].replace('Z', '+00:00')).date()
    except (ValueError, TypeError, KeyError, AttributeError):
        return None


def event_compatible(a, b):
    # Do not merge events separated by days, or reports that clearly disagree
    # about the location. Different aftershocks remain separate.
    da, db = event_date(a), event_date(b)
    if da is None or db is None or abs((da - db).days) > 1:
        return False
    if a.get('countries') and b.get('countries') and not set(a['countries']) & set(b['countries']):
        return False
    return True


def source_key(article):
    return re.sub(r'\s+', ' ', article.get('source', '').strip().casefold()) or 'unknown'


def source_diversity_select(pool, selected_ids, slots, cap=MAX_PER_SOURCE):
    """Prefer publisher variety, then backfill so source caps never shrink coverage."""
    picked = []
    counts = collections.Counter(source_key(a) for a in pool if id(a) in selected_ids)
    for article in pool:
        if len(picked) >= slots:
            break
        if id(article) in selected_ids or counts[source_key(article)] >= cap:
            continue
        picked.append(article)
        counts[source_key(article)] += 1
    return picked


# Only merge explicitly identifiable, near-simultaneous repeated reports.
# Avoid merging distinct follow-up events (aftershocks, new strikes, trials).
def event_fingerprint(article):
    t = article.get('title', '')
    if re.search(r'(?i)\b(?:japan|japanese)\b', t) and re.search(r'(?i)\b(?:earthquake|quake)\b', t):
        m = re.search(r'(?i)\b5[.,]7\b', t)
        if m and not re.search(r'(?i)\b(?:aftershock|second quake|another quake)\b', t):
            return 'japan-earthquake-5.7'
    if re.search(r'(?i)\b(?:krakow|kraków|poland)\b', t) and re.search(r'(?i)\b(?:shooting|gunman|gun attack)\b', t):
        if not re.search(r'(?i)\b(?:another shooting|second attack|new shooting)\b', t):
            return 'krakow-shooting'
    return None

def confirmed_countries(article):
    title = article.get('title', '')
    result = []
    for country in article.get('countries', []):
        if any(blocked == country and re.search(pattern, title) for pattern, blocked in AMBIGUOUS_COUNTRY_PLACE):
            continue
        name = COUNTRY_ENGLISH.get(country, '')
        patterns = [COUNTRY_ALIASES.get(country, '')]
        if name:
            patterns.append(r'\b' + re.escape(name) + r'\b')
        native = COUNTRY_NATIVE.get(country, (country,))
        if any(re.search(p, title, re.I) for p in patterns if p) or any(n in title for n in native):
            result.append(country)
    return result

# Conservative event-level deduplication: same language, category and strongly
# overlapping headline. Different developments should remain separate.
STOPWORDS = {'the','and','for','with','from','after','over','into','amid','says','said','new','news','report','reports','latest','대한','관련','속보','뉴스','오늘','기자'}
def event_tokens(title):
    words = re.findall(r'[a-z0-9]{3,}|[가-힣]{2,}', title.lower())
    return {w for w in words if w not in STOPWORDS}

def same_event(a, b):
    if a.get('language') != b.get('language'):
        return False
    if a.get('category') != b.get('category'):
        return False
    x, y = event_tokens(a['title']), event_tokens(b['title'])
    if len(x) < 3 or len(y) < 3:
        return False
    overlap = len(x & y)
    if overlap < 3:
        return False
    containment = overlap / min(len(x), len(y))
    similarity = SequenceMatcher(None, title_key(a['title']), title_key(b['title'])).ratio()
    return (containment >= .78 and similarity >= .64) or similarity >= .88

def dedupe_events(pool):
    kept = []
    removed = []
    for article in pool:
        match = next((old for old in kept if same_event(article, old)), None)
        if match is None:
            kept.append(article)
        else:
            match['countries'] = sorted(set(match['countries']) | set(article['countries']))
            removed.append((article['title'], match['title']))
    return kept, removed

def quality_reason(article):
    title = article.get('title', '').strip()
    if is_routine_quake(article):
        return '미소지진·미확인 관측'
    if any(re.search(p, title) for p in NOISE_PATTERNS):
        return '잡뉴스'
    if is_low_value_record(article):
        return '정보성·미확인 기록'
    if len(title) < (10 if re.search(r'[가-힣]', title) else 18) or len(title) > 240:
        return '제목 길이'
    if quality_score(article) < MIN_QUALITY_SCORE:
        return '중요도 미달'
    return '통과'


# Phase 5/6: retain high-consequence reporting, audit exclusions, and
# distinguish source signals from independent verification.
AUDIT_PATH = Path('data/news_quality_audit.json')
PROTECTED_EVENTS = [
    r'(?i)\b(?:ceasefire|invasion|earthquake|tsunami|hurricane|pandemic|outbreak|mass casualty|central bank|rate decision|drug approval|FDA approves|EMA approves|phase [123] (?:trial|results)|clinical trial results|recall|antimicrobial resistance|antibiotic resistance|vaccine approval|emergency declaration)\b',
    r'휴전|침공|지진|쓰나미|태풍|대규모 사상|기준금리 (?:결정|인상|인하)|신약 (?:허가|승인)|임상(?:시험)? (?:결과|성공|실패)|의약품 리콜|항생제 내성|감염병 (?:확산|발생)|긴급사태',
    # 실제 탈락 기사에서 확인된 중대 사건
    r'(?i)\b(?:missiles? (?:intercepted|targeting|strike)|intercepts? (?:houthi |ballistic )?missiles?|drone attack|military base attack|shooting (?:kills?|leaves?)|(?:\d+|several) (?:people |soldiers )?(?:killed|injured|dead)|(?:kills?|injures?) \d+|attack on (?:military|airbase|airport)|gun attack|measles cases? (?:hit|surpass|reach)|measles outbreaks?|disease epidemiology|drug-resistant (?:bacteria|pathogens?|pseudomonas)|antibacterial activity|microbiome causal analysis)\b',
    r'미사일 (?:요격|발사|공격)|드론 (?:공격|피격)|군사기지 (?:공격|피격)|총격 (?:사건|사망)|\d+명 (?:사망|부상)|홍역 (?:확산|유행|감염)|항균 활성|내성균|항생제 내성균|역학(?:조사|연구)|미생물군집',
]
# 완전히 별개인 전문 연구/사건이 제목 유사성만으로 합쳐지는 것을 제한
SPECIALIST_EVENT_TERMS = [
    r'(?i)\b(?:antibacterial|antimicrobial|drug-resistant|microbiome|microbiology|epidemiology|measles|pseudomonas|clinical trial|phase [123]|FDA approval|EMA approval)\b',
    r'항균|내성균|미생물|역학|홍역|임상|허가|승인',
]
SPECIALIST_CATEGORIES = {'미생물', '제약·신약', '의료기기', '감염병', '바이오기업'}
SPECIALIST_MINIMUM = {'미생물': 5, '제약·신약': 5, '의료기기': 3, '감염병': 5, '바이오기업': 3}
# Signals only: these are not guarantees of factual correctness.
OFFICIAL_SOURCE_MARKERS = (
    'who.int', 'cdc.gov', 'fda.gov', 'ema.europa.eu', 'nih.gov',
    'ecb.europa.eu', 'federalreserve.gov', 'gov.uk', 'nature.com',
    'science.org', 'nejm.org', 'thelancet.com',
)
KNOWN_NEWS_MARKERS = (
    'reuters', 'associated press', 'ap news', 'bbc', 'financial times',
    'bloomberg', 'yonhap', '연합뉴스', 'kbs', 'mbc', 'sbs', 'nhk',
)
UNVERIFIED_CLAIM_PATTERNS = [
    r'(?i)\b(?:rumou?r|unconfirmed|allegedly|reportedly|sources say|claims? without evidence)\b',
    r'(?i)\b(?:miracle cure|guaranteed cure|shocking truth|you won.t believe)\b',
    r'확인되지 않은|미확인|루머|소문|충격적인 진실|기적의 치료',
]

def is_protected(article):
    title = article.get('title', '')
    # Hard noise exclusions still apply: a sports article mentioning 'war'
    # should not be promoted automatically.
    return not any(re.search(p, title) for p in NOISE_PATTERNS) and any(
        re.search(p, title) for p in PROTECTED_EVENTS
    )

def source_signals(article):
    source = article.get('source', '').strip().lower()
    url = article.get('url', '').lower()
    # Google News links are aggregators, not evidence of the publisher's domain.
    official = any(s in source for s in OFFICIAL_SOURCE_MARKERS)
    established = any(s in source for s in KNOWN_NEWS_MARKERS)
    caution = any(re.search(p, article.get('title', '')) for p in UNVERIFIED_CLAIM_PATTERNS)
    return {
        'source_type': 'official_or_journal' if official else ('known_news' if established else 'unassessed'),
        'independent_verification': 'not_checked',
        'caution': bool(caution),
    }

def selection_score(article):
    score = quality_score(article)
    if is_protected(article):
        score += 15
    signals = source_signals(article)
    if signals['source_type'] == 'official_or_journal':
        score += 5
    elif signals['source_type'] == 'known_news':
        score += 3
    if signals['caution']:
        score -= 12
    return min(100, max(0, score))

def protected_reason(article):
    reason = quality_reason(article)
    if reason == '중요도 미달' and is_protected(article):
        return '핵심 사건 보호'
    return reason

# Phase 10: conservative event signatures for repeated reports with different wording.
# Require a distinctive location, a narrow event class, and compatible dates.
EVENT_LOCATIONS = {
    'krakow': r'(?i)\b(?:krakow|kraków)\b',
    'central_japan': r'(?i)\b(?:central japan|japan quake|japan earthquake|quake strikes japan|earthquake strikes japan)\b',
    'colombia_base': r'(?i)\b(?:colombia|colombian)\b',
    'riyadh': r'(?i)\b(?:riyadh|saudi arabia|saudi)\b',
}
EVENT_CLASSES = {
    'earthquake': r'(?i)\b(?:earthquake|quake|tremor)\b|지진',
    'shooting': r'(?i)\b(?:shooting|gunman|gun attack)\b|총격',
    'drone_base': r'(?i)\b(?:drone attack|drone strike)\b|드론 공격',
    'missile': r'(?i)\b(?:missiles?|ballistic)\b|미사일',
}


def event_signature(article):
    title = article.get('title', '')
    place = next((k for k, pattern in EVENT_LOCATIONS.items() if re.search(pattern, title)), None)
    kind = next((k for k, pattern in EVENT_CLASSES.items() if re.search(pattern, title)), None)
    if not place or not kind:
        return None
    if (place, kind) not in {('krakow', 'shooting'), ('central_japan', 'earthquake'),
                             ('colombia_base', 'drone_base'), ('riyadh', 'missile')}:
        return None
    if re.search(r'(?i)\b(?:another|second|new attack|aftershock|follow-up)\b|추가 공격|여진', title):
        return None
    if kind == 'earthquake':
        mag = MICRO_QUAKE.search(title) or re.search(r'(?i)\b([0-9]\.[0-9])[- ]magnitude\b', title)
        # Only merge explicitly known magnitude to avoid unrelated Japan quakes.
        if not mag or abs(float(mag.group(1)) - 5.7) > .1:
            return None
    return place, kind


def cautious_same_event(a, b):
    if not event_compatible(a, b):
        return False
    # Phase 5: reduce false merges of distinct trial results or follow-ups.
    if a.get('subcategory') != b.get('subcategory'):
        return False
    if re.search(r'(?i)\b(?:earthquake|quake)\b', a['title']) and re.search(r'(?i)\b(?:earthquake|quake)\b', b['title']):
        ma = re.search(r'\b([0-9]\.[0-9])\s+magnitude\b', a['title'], re.I) or MICRO_QUAKE.search(a['title'])
        mb = re.search(r'\b([0-9]\.[0-9])\s+magnitude\b', b['title'], re.I) or MICRO_QUAKE.search(b['title'])
        if ma and mb and abs(float(ma.group(1))-float(mb.group(1))) >= 0.2:
            return False
    # Distinct named events: compatible time and explicit event anchors required.
    sa, sb = event_signature(a), event_signature(b)
    if sa and sa == sb:
        return True
    fa, fb = event_fingerprint(a), event_fingerprint(b)
    if fa and fa == fb:
        return True
    if is_protected(a) or is_protected(b):
        x, y = event_tokens(a['title']), event_tokens(b['title'])
        if not x or not y:
            return False
        similarity = SequenceMatcher(None, title_key(a['title']), title_key(b['title'])).ratio()
        return similarity >= .94 and len(x & y) / max(len(x | y), 1) >= .78
    return same_event(a, b)

def audited_dedupe(pool):
    kept, merged = [], []
    for article in pool:
        match = next((old for old in kept if cautious_same_event(article, old)), None)
        if match is None:
            kept.append(article)
        else:
            match['countries'] = sorted(set(match['countries']) | set(article['countries']))
            merged.append({'title': article['title'], 'kept_title': match['title'], 'reason': '유사 사건'})
    return kept, merged

def write_audit(payload):
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = AUDIT_PATH.with_suffix('.tmp')
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(AUDIT_PATH)

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
        raise RuntimeError('No RSS articles retrieved; existing data preserved')
    # If most RSS feeds fail, do not overwrite the last healthy edition.
    minimum_successful_feeds = max(10, int(len(FEEDS) * .25))
    if succeeded < minimum_successful_feeds:
        raise RuntimeError(
            f'Only {succeeded}/{len(FEEDS)} feeds succeeded; existing data preserved'
        )

    # Preserve country coverage before allowing general feeds to fill remaining slots.
    # Deduplicate by URL/title, keeping all applicable country tags from scoped searches.
    candidates.sort(key=lambda a: a['published'], reverse=True)
    for article in candidates:
        infer_category(article)
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

    pool_before_filter = len(unique)
    reasons = collections.Counter()
    pool = []
    for article in unique.values():
        reason = protected_reason(article)
        reasons[reason] += 1
        if reason in ('통과', '핵심 사건 보호'):
            article['countries'] = confirmed_countries(article)
            pool.append(article)
    pool.sort(key=lambda a: (selection_score(a), a['published']), reverse=True)
    pool, merged_events = audited_dedupe(pool)
    print('Near-duplicate events merged:', len(merged_events))
    print('Sample merged events:', merged_events[:10])
    print(f'Quality filter: {pool_before_filter} unique -> {len(pool)} eligible (threshold {MIN_QUALITY_SCORE})')
    print('Filter reasons:', dict(reasons))
    print('Sample rejected titles:', [a['title'] for a in list(unique.values()) if quality_reason(a) != '통과'][:12])
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
    # Preserve a small number of specialist articles if the candidate pool permits.
    for category, minimum in SPECIALIST_MINIMUM.items():
        current = sum(a['category'] == category for a in accepted)
        for a in pool:
            if current >= minimum or len(accepted) >= MAX_TOTAL:
                break
            if id(a) in selected or a['category'] != category:
                continue
            if any(counts.get(c, 0) >= MAX_PER_COUNTRY for c in a['countries']):
                continue
            selected.add(id(a))
            accepted.append(a)
            for c in a['countries']:
                counts[c] = counts.get(c, 0) + 1
            current += 1

    general_count = sum(not a['countries'] for a in accepted)
    publisher_counts = collections.Counter(source_key(a) for a in accepted)
    deferred_by_source = []
    for a in pool:
        if len(accepted) >= MAX_TOTAL:
            break
        if id(a) in selected:
            continue
        if publisher_counts[source_key(a)] >= MAX_PER_SOURCE:
            deferred_by_source.append(a)
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
        selected.add(id(a))
        publisher_counts[source_key(a)] += 1
    # Backfill unused capacity so the diversity cap never sacrifices coverage.
    for a in deferred_by_source:
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
        selected.add(id(a))
        publisher_counts[source_key(a)] += 1
    accepted.sort(key=lambda a: (selection_score(a), a['published']), reverse=True)

    articles = [
        {k: v for k, v in article.items() if k != '_key'}
        for article in accepted
    ]

    if len(articles) < 15:
        raise RuntimeError('Too few quality articles; existing data preserved (minimum 15)')
    # Protect the public site from a sudden abnormal collapse in article coverage.
    previous_path = Path('data/articles.json')
    if previous_path.exists():
        try:
            previous_articles = json.loads(previous_path.read_text(encoding='utf-8')).get('articles', [])
            if len(previous_articles) >= 80 and len(articles) < max(30, int(len(previous_articles) * .35)):
                raise RuntimeError('Severe feed coverage drop; previous articles preserved')
        except (OSError, ValueError, TypeError, AttributeError):
            pass

    payload = {
        'updated': datetime.now(timezone.utc).isoformat(),
        'articles': articles
    }

    Path('data').mkdir(exist_ok=True)

    audit = {
        'updated': payload['updated'],
        'version': 'quality-10',
        'total_candidates': len(candidates),
        'unique_candidates': pool_before_filter,
        'passed_after_dedupe': len(pool),
        'saved': len(articles),
        'filter_reasons': dict(reasons),
        'protected_saved': sum(is_protected(a) for a in articles),
        'protected_candidates': sum(is_protected(a) for a in unique.values()),
        'excluded_review_priority_high': sum(
            protected_reason(a) not in ('통과', '핵심 사건 보호')
            and any(re.search(p, a['title']) for p in SPECIALIST_EVENT_TERMS)
            for a in unique.values()
        ),
        'category_counts': dict(collections.Counter(a['category'] for a in articles)),
        'routine_quakes_rejected': sum(quality_reason(a) == '미소지진·미확인 관측' for a in unique.values()),
        'event_duplicates_merged': len(merged_events),
        'low_value_records_rejected': sum(quality_reason(a) == '정보성·미확인 기록' for a in unique.values()),
        'distinct_publishers_saved': len(set(source_key(a) for a in articles)),
        'largest_publisher_share': round(max(collections.Counter(source_key(a) for a in articles).values(), default=0) / max(len(articles), 1), 3),
        'country_tagged_saved': sum(bool(a['countries']) for a in articles),
        'uncategorized_saved': sum(a['category'] == '일반' for a in articles),
        'feed_success_rate': round(succeeded / max(len(FEEDS), 1), 3),
        'successful_feeds': succeeded,
        'attempted_feeds': len(FEEDS),
        'country_counts': dict(collections.Counter(c for a in articles for c in a.get('countries', []))),
        'publisher_counts_top20': dict(collections.Counter(source_key(a) for a in articles).most_common(20)),
        'event_signature_coverage': sum(event_signature(a) is not None for a in articles),
        'excluded_total': sum(protected_reason(a) not in ('통과', '핵심 사건 보호') for a in unique.values()),
        'excluded': sorted([
            {'title': a['title'], 'category': a['category'], 'reason': protected_reason(a),
             'source': a.get('source', ''), 'url': a.get('url', ''),
             'review_priority': 'high' if any(re.search(p, a['title']) for p in SPECIALIST_EVENT_TERMS) else 'normal'}
            for a in unique.values() if protected_reason(a) not in ('통과', '핵심 사건 보호')
        ], key=lambda a: (a['review_priority'] != 'high', a['title'])), 
        'merged': merged_events[:200],
        'selected_source_signals': [
            {'title': a['title'], 'source': a.get('source', ''), **source_signals(a)}
            for a in articles
        ],
        'note': 'Publisher signals are not independent fact checking; article bodies were not verified.',
    }
    write_audit(audit)
    print('Quality audit saved:', AUDIT_PATH, 'excluded:', len(audit['excluded']))

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
