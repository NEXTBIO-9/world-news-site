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

# category, query, locale, region
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


# V13: Explicit country evidence. RSS locale and publisher country are NOT
# used as event locations. The same aliases are shared with the map.
COUNTRY_ALIASES = {'대한민국': ['대한민국', '한국', '남한', 'south korea', 'republic of korea', 'seoul', '서울', '부산', '인천', '대전', '대구', '광주', '울산', '수원', '제주'], '북한': ['북한', 'north korea', 'pyongyang', '평양'], '미국': ['미국', 'united states', 'u.s.', 'u.s.a.', 'usa', 'american', '워싱턴', 'washington dc', 'washington d.c.', 'new york', '뉴욕', 'california', '캘리포니아', 'texas', '텍사스', 'boston', '보스턴', 'chicago', '시카고', 'los angeles', '로스앤젤레스', '트럼프', '바이든'], '중국': ['중국', 'china', 'chinese', 'beijing', '베이징', 'shanghai', '상하이', 'shenzhen', '선전', 'wuhan', '우한', '시진핑'], '일본': ['일본', 'japan', 'japanese', 'tokyo', '도쿄', 'osaka', '오사카', 'kyoto', '교토'], '러시아': ['러시아', 'russia', 'russian', 'moscow', '모스크바', 'putin', '푸틴'], '우크라이나': ['우크라이나', 'ukraine', 'ukrainian', 'kyiv', '키이우', 'zelensky', '젤렌스키'], '대만': ['대만', '타이완', 'taiwan', 'taipei', '타이베이'], '영국': ['영국', 'united kingdom', 'britain', 'british', 'england', 'london', '런던', 'scotland', '스코틀랜드'], '프랑스': ['프랑스', 'france', 'french', 'paris', '파리', 'lyon', '리옹'], '독일': ['독일', 'germany', 'german', 'berlin', '베를린', 'munich', '뮌헨', 'frankfurt', '프랑크푸르트'], '이스라엘': ['이스라엘', 'israel', 'israeli', 'tel aviv', '텔아비브', 'jerusalem', '예루살렘'], '이란': ['이란', 'iran', 'iranian', 'tehran', '테헤란'], '팔레스타인': ['팔레스타인', 'palestine', 'palestinian', 'gaza', '가자', 'west bank', '서안지구'], '사우디아라비아': ['사우디', 'saudi arabia', 'saudi', 'riyadh', '리야드'], '인도': ['인도', 'india', 'indian', 'new delhi', '뉴델리', 'mumbai', '뭄바이', 'bengaluru', '벵갈루루'], '파키스탄': ['파키스탄', 'pakistan', 'pakistani', 'islamabad', '이슬라마바드'], '튀르키예': ['튀르키예', '터키', 'turkey', 'türkiye', 'turkiye', 'ankara', '앙카라', 'istanbul', '이스탄불'], '브라질': ['브라질', 'brazil', 'brazilian', 'brasilia', '브라질리아', 'sao paulo', '상파울루'], '캐나다': ['캐나다', 'canada', 'canadian', 'ottawa', '오타와', 'toronto', '토론토', 'vancouver', '밴쿠버'], '멕시코': ['멕시코', 'mexico', 'mexican', 'mexico city', '멕시코시티'], '호주': ['호주', '오스트레일리아', 'australia', 'australian', 'sydney', '시드니', 'melbourne', '멜버른', 'canberra', '캔버라'], '인도네시아': ['인도네시아', 'indonesia', 'indonesian', 'jakarta', '자카르타'], '베트남': ['베트남', 'vietnam', 'vietnamese', 'hanoi', '하노이', 'ho chi minh', '호찌민'], '태국': ['태국', 'thailand', 'thai', 'bangkok', '방콕'], '필리핀': ['필리핀', 'philippines', 'philippine', 'manila', '마닐라'], '이집트': ['이집트', 'egypt', 'egyptian', 'cairo', '카이로'], '남아프리카공화국': ['남아공', '남아프리카공화국', 'south africa', 'south african', 'cape town', '케이프타운', 'johannesburg', '요하네스버그'], '폴란드': ['폴란드', 'poland', 'polish', 'warsaw', '바르샤바'], '스페인': ['스페인', 'spain', 'spanish', 'madrid', '마드리드', 'barcelona', '바르셀로나'], '이탈리아': ['이탈리아', 'italy', 'italian', 'rome', '로마', 'milan', '밀라노'], '아르헨티나': ['아르헨티나', 'argentina', 'argentine', 'buenos aires', '부에노스아이레스'], '네덜란드': ['네덜란드', 'netherlands', 'dutch', 'amsterdam', '암스테르담', 'rotterdam', '로테르담'], '벨기에': ['벨기에', 'belgium', 'belgian', 'brussels', '브뤼셀'], '스위스': ['스위스', 'switzerland', 'swiss', 'zurich', '취리히', 'geneva', '제네바'], '스웨덴': ['스웨덴', 'sweden', 'swedish', 'stockholm', '스톡홀름'], '노르웨이': ['노르웨이', 'norway', 'norwegian', 'oslo', '오슬로'], '덴마크': ['덴마크', 'denmark', 'danish', 'copenhagen', '코펜하겐'], '핀란드': ['핀란드', 'finland', 'finnish', 'helsinki', '헬싱키'], '아일랜드': ['아일랜드', 'ireland', 'irish', 'dublin', '더블린'], '포르투갈': ['포르투갈', 'portugal', 'portuguese', 'lisbon', '리스본'], '오스트리아': ['오스트리아', 'austria', 'austrian', 'vienna', '빈'], '체코': ['체코', 'czech republic', 'czechia', 'prague', '프라하'], '헝가리': ['헝가리', 'hungary', 'hungarian', 'budapest', '부다페스트'], '그리스': ['그리스', 'greece', 'greek', 'athens', '아테네'], '루마니아': ['루마니아', 'romania', 'romanian', 'bucharest', '부쿠레슈티'], '불가리아': ['불가리아', 'bulgaria', 'bulgarian', 'sofia', '소피아'], '세르비아': ['세르비아', 'serbia', 'serbian', 'belgrade', '베오그라드'], '크로아티아': ['크로아티아', 'croatia', 'croatian', 'zagreb', '자그레브'], '슬로바키아': ['슬로바키아', 'slovakia', 'slovak', 'bratislava', '브라티슬라바'], '슬로베니아': ['슬로베니아', 'slovenia', 'slovenian', 'ljubljana', '류블랴나'], '리투아니아': ['리투아니아', 'lithuania', 'lithuanian', 'vilnius', '빌뉴스'], '라트비아': ['라트비아', 'latvia', 'latvian', 'riga', '리가'], '에스토니아': ['에스토니아', 'estonia', 'estonian', 'tallinn', '탈린'], '벨라루스': ['벨라루스', 'belarus', 'belarusian', 'minsk', '민스크'], '몰도바': ['몰도바', 'moldova', 'moldovan', 'chisinau', '키시너우'], '조지아': ['조지아', 'georgia country', 'tbilisi', '트빌리시'], '아르메니아': ['아르메니아', 'armenia', 'armenian', 'yerevan', '예레반'], '아제르바이잔': ['아제르바이잔', 'azerbaijan', 'azerbaijani', 'baku', '바쿠'], '카자흐스탄': ['카자흐스탄', 'kazakhstan', 'kazakh', 'astana', '아스타나'], '우즈베키스탄': ['우즈베키스탄', 'uzbekistan', 'uzbek', 'tashkent', '타슈켄트'], '키르기스스탄': ['키르기스스탄', 'kyrgyzstan', 'kyrgyz', 'bishkek', '비슈케크'], '타지키스탄': ['타지키스탄', 'tajikistan', 'tajik', 'dushanbe', '두샨베'], '투르크메니스탄': ['투르크메니스탄', 'turkmenistan', 'turkmen', 'ashgabat', '아시가바트'], '몽골': ['몽골', 'mongolia', 'mongolian', 'ulaanbaatar', '울란바토르'], '네팔': ['네팔', 'nepal', 'nepalese', 'kathmandu', '카트만두'], '방글라데시': ['방글라데시', 'bangladesh', 'bangladeshi', 'dhaka', '다카'], '스리랑카': ['스리랑카', 'sri lanka', 'sri lankan', 'colombo', '콜롬보'], '미얀마': ['미얀마', 'myanmar', 'burma', 'yangon', '양곤', 'naypyidaw', '네피도'], '캄보디아': ['캄보디아', 'cambodia', 'cambodian', 'phnom penh', '프놈펜'], '라오스': ['라오스', 'laos', 'laotian', 'vientiane', '비엔티안'], '말레이시아': ['말레이시아', 'malaysia', 'malaysian', 'kuala lumpur', '쿠알라룸푸르'], '싱가포르': ['싱가포르', 'singapore', 'singaporean'], '브루나이': ['브루나이', 'brunei', 'bandar seri begawan'], '동티모르': ['동티모르', 'timor-leste', 'east timor', 'dili', '딜리'], '뉴질랜드': ['뉴질랜드', 'new zealand', 'new zealander', 'auckland', '오클랜드', 'wellington', '웰링턴'], '피지': ['피지', 'fiji', 'fijian', 'suva', '수바'], '파푸아뉴기니': ['파푸아뉴기니', 'papua new guinea', 'port moresby'], '칠레': ['칠레', 'chile', 'chilean', 'santiago', '산티아고'], '페루': ['페루', 'peru', 'peruvian', 'lima', '리마'], '콜롬비아': ['콜롬비아', 'colombia', 'colombian', 'bogota', '보고타'], '베네수엘라': ['베네수엘라', 'venezuela', 'venezuelan', 'caracas', '카라카스'], '에콰도르': ['에콰도르', 'ecuador', 'ecuadorian', 'quito', '키토'], '볼리비아': ['볼리비아', 'bolivia', 'bolivian', 'la paz', '라파스'], '파라과이': ['파라과이', 'paraguay', 'paraguayan', 'asuncion', '아순시온'], '우루과이': ['우루과이', 'uruguay', 'uruguayan', 'montevideo', '몬테비데오'], '쿠바': ['쿠바', 'cuba', 'cuban', 'havana', '아바나'], '도미니카공화국': ['도미니카공화국', 'dominican republic', 'santo domingo', '산토도밍고'], '아이티': ['아이티', 'haiti', 'haitian', 'port-au-prince', '포르토프랭스'], '자메이카': ['자메이카', 'jamaica', 'jamaican', 'kingston', '킹스턴'], '파나마': ['파나마', 'panama', 'panamanian', 'panama city'], '코스타리카': ['코스타리카', 'costa rica', 'costa rican', 'san jose', '산호세'], '과테말라': ['과테말라', 'guatemala', 'guatemalan'], '온두라스': ['온두라스', 'honduras', 'honduran', 'tegucigalpa'], '엘살바도르': ['엘살바도르', 'el salvador', 'salvadoran'], '니카라과': ['니카라과', 'nicaragua', 'nicaraguan', 'managua'], '나이지리아': ['나이지리아', 'nigeria', 'nigerian', 'lagos', '라고스', 'abuja', '아부자'], '케냐': ['케냐', 'kenya', 'kenyan', 'nairobi', '나이로비'], '에티오피아': ['에티오피아', 'ethiopia', 'ethiopian', 'addis ababa', '아디스아바바'], '가나': ['가나', 'ghana', 'ghanaian', 'accra', '아크라'], '우간다': ['우간다', 'uganda', 'ugandan', 'kampala', '캄팔라'], '탄자니아': ['탄자니아', 'tanzania', 'tanzanian', 'dar es salaam', '다르에스살람'], '르완다': ['르완다', 'rwanda', 'rwandan', 'kigali', '키갈리'], '콩고민주공화국': ['콩고민주공화국', 'democratic republic of the congo', 'dr congo', 'drc', 'kinshasa', '킨샤사'], '콩고공화국': ['콩고공화국', 'republic of the congo', 'brazzaville', '브라자빌'], '수단': ['수단', 'sudan', 'sudanese', 'khartoum', '하르툼'], '남수단': ['남수단', 'south sudan', 'juba', '주바'], '소말리아': ['소말리아', 'somalia', 'somali', 'mogadishu', '모가디슈'], '모로코': ['모로코', 'morocco', 'moroccan', 'rabat', '라바트', 'casablanca', '카사블랑카'], '알제리': ['알제리', 'algeria', 'algerian', 'algiers', '알제'], '튀니지': ['튀니지', 'tunisia', 'tunisian', 'tunis', '튀니스'], '리비아': ['리비아', 'libya', 'libyan', 'tripoli', '트리폴리'], '세네갈': ['세네갈', 'senegal', 'senegalese', 'dakar', '다카르'], '코트디부아르': ['코트디부아르', 'ivory coast', 'cote d’ivoire', 'côte d’ivoire', 'abidjan', '아비장'], '카메룬': ['카메룬', 'cameroon', 'cameroonian', 'yaounde', '야운데'], '잠비아': ['잠비아', 'zambia', 'zambian', 'lusaka', '루사카'], '짐바브웨': ['짐바브웨', 'zimbabwe', 'zimbabwean', 'harare', '하라레'], '모잠비크': ['모잠비크', 'mozambique', 'mozambican', 'maputo', '마푸투'], '마다가스카르': ['마다가스카르', 'madagascar', 'malagasy', 'antananarivo', '안타나나리보'], '앙골라': ['앙골라', 'angola', 'angolan', 'luanda', '루안다'], '보츠와나': ['보츠와나', 'botswana', 'gaborone', '가보로네'], '나미비아': ['나미비아', 'namibia', 'namibian', 'windhoek', '빈트후크'], '아랍에미리트': ['아랍에미리트', 'united arab emirates', 'uae', 'dubai', '두바이', 'abu dhabi', '아부다비'], '카타르': ['카타르', 'qatar', 'qatari', 'doha', '도하'], '쿠웨이트': ['쿠웨이트', 'kuwait', 'kuwaiti'], '바레인': ['바레인', 'bahrain', 'bahraini', 'manama', '마나마'], '오만': ['오만', 'oman', 'omani', 'muscat', '무스카트'], '예멘': ['예멘', 'yemen', 'yemeni', 'sanaa', '사나'], '이라크': ['이라크', 'iraq', 'iraqi', 'baghdad', '바그다드'], '시리아': ['시리아', 'syria', 'syrian', 'damascus', '다마스쿠스'], '요르단': ['요르단', 'jordan', 'jordanian', 'amman', '암만'], '레바논': ['레바논', 'lebanon', 'lebanese', 'beirut', '베이루트'], '아프가니스탄': ['아프가니스탄', 'afghanistan', 'afghan', 'kabul', '카불'], '키프로스': ['키프로스', 'cyprus', 'cypriot', 'nicosia', '니코시아'], '아이슬란드': ['아이슬란드', 'iceland', 'icelandic', 'reykjavik', '레이캬비크']}

def country_matches(text):
    text = (text or '').casefold()
    found = []
    for name, aliases in COUNTRY_ALIASES.items():
        for alias in aliases:
            k = alias.casefold().strip()
            if not k:
                continue
            if re.fullmatch(r"[a-z][a-z .'-]*", k):
                pattern = r'(?<![a-z])' + re.escape(k) + r'(?![a-z])'
                hit = re.search(pattern, text) is not None
            else:
                hit = k in text
            if hit:
                found.append(name)
                break
    return found

def add_country_evidence(article):
    title_matches = country_matches(article.get('title', ''))
    summary_matches = country_matches(article.get('summary', ''))
    names = list(dict.fromkeys(title_matches + summary_matches))
    article['countries'] = names
    article['country_evidence'] = (
        'title+summary' if title_matches and summary_matches else
        'title' if title_matches else
        'summary' if summary_matches else 'unclassified'
    )
    return article

def rss_url(query, language, region):
    ceid = f'{region}:{language}'
    params = urllib.parse.urlencode({'q': query + ' when:14d', 'hl': language, 'gl': region, 'ceid': ceid})
    return 'https://news.google.com/rss/search?' + params

def text(node, tag):
    el = node.find(tag)
    return (el.text or '').strip() if el is not None else ''

def normalize_title(title):
    title = html.unescape(title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title

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
            published = parsedate_to_datetime(text(item, 'pubDate')).astimezone(timezone.utc).isoformat()
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
    # Limit fuzzy comparisons to similar title lengths to avoid excessive comparisons.
    for other in existing:
        other_key = other['_key']
        if abs(len(key) - len(other_key)) > max(12, int(max(len(key), len(other_key)) * .25)):
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
        raise RuntimeError('No RSS articles retrieved; existing data preserved')
    candidates.sort(key=lambda a: a['published'], reverse=True)
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
        accepted.append({**article, '_key': key})
        if len(accepted) >= MAX_TOTAL:
            break
    articles = [add_country_evidence({k: v for k, v in article.items() if k != '_key'}) for article in accepted]
    payload = {'updated': datetime.now(timezone.utc).isoformat(), 'articles': articles}
    Path('data').mkdir(exist_ok=True)
    Path('data/articles.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Successful feeds: {succeeded}/{len(SEARCHES)}; candidates: {len(candidates)}; saved: {len(articles)}')
    print('Country classified:', sum(bool(a['countries']) for a in articles), 'unclassified:', sum(not a['countries'] for a in articles))
    print('Microbiology:', sum(a['category']=='미생물' for a in articles), 'by subcategory:', {s:sum(a.get('subcategory')==s for a in articles) for s in ['세균','진균','바이러스','항생제 내성','미생물 검사']})

if __name__ == '__main__':
    main()
