#!/usr/bin/env python3
"""Daily public-report index, not live ship tracking."""
import datetime as dt
import email.utils
import json
import pathlib
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "mpsron-news.json"
QUERIES = [
    'site:dvidshub.net/news "prepositioning" (Okinawa OR Japan OR Korea OR Pohang OR Busan)',
    'site:msc.usff.navy.mil "prepositioning" (Japan OR Korea OR Okinawa)',
    'site:dvidshub.net/news "MPSRON-3" (Okinawa OR Korea OR Japan)',
]
REGION = re.compile(r'okinawa|japan|japanese|korea|korean|pohang|busan|kin bay|sasebo|yokosuka|일본|한국|오키나와|포항|부산', re.I)
SUBJECT = re.compile(r'preposition|mpsron|maritime pre-position|usns .* (lummus|seay|pomeroy|watkins)', re.I)
NOW = dt.datetime.now(dt.timezone.utc)
items = {}
for query in QUERIES:
    url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q': query, 'hl': 'en-US', 'gl': 'US', 'ceid': 'US:en'})
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (public-news-indexer)'})
        with urllib.request.urlopen(req, timeout=25) as response:
            xml = ET.fromstring(response.read(1_500_000))
    except Exception as exc:
        print('Feed unavailable:', type(exc).__name__, str(exc)[:150])
        continue
    for entry in xml.findall('./channel/item'):
        title = (entry.findtext('title') or '').strip()
        description = re.sub(r'<[^>]*>', ' ', entry.findtext('description') or '')
        if not SUBJECT.search(title) or not REGION.search(title + ' ' + description):
            continue
        source = entry.find('source')
        publisher = (source.text or '').strip() if source is not None else ''
        if not any(s in publisher.lower() for s in ('dvids', 'military sealift command')):
            continue
        link = (entry.findtext('link') or '').strip()
        if not link.startswith('https://'):
            continue
        try:
            published = email.utils.parsedate_to_datetime(entry.findtext('pubDate') or '').astimezone(dt.timezone.utc)
        except Exception:
            continue
        if published > NOW or published < NOW - dt.timedelta(days=365):
            continue
        key = re.sub(r'\W+', '', title.lower())
        items[key] = {'title': title, 'published': published.date().isoformat(), 'url': link,
                      'source': publisher, 'category': '동북아 관련 공식 발표 보도 · 실제 활동 지역·일자 원문 확인'}
result = sorted(items.values(), key=lambda a: a['published'], reverse=True)[:10]
previous = {}
if OUT.exists():
    try:
        previous = json.loads(OUT.read_text(encoding='utf-8'))
    except (ValueError, OSError):
        pass
if not result and previous.get('items'):
    result = previous['items'][:10]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({'last_checked': NOW.isoformat(timespec='seconds'), 'items': result}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Indexed', len(result), 'public reports')
