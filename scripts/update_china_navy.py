"""Collect public reports of Chinese naval exercises and deployments daily."""
import datetime as dt
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path("data/china-navy-news.json")
SEARCHES = [
    ('항공모함', '"Chinese aircraft carrier" naval exercise'),
    ('대만해협', '"China navy" Taiwan drills'),
    ('남중국해', '"PLA Navy" South China Sea exercise'),
    ('서태평양', '"Chinese navy" western Pacific deployment'),
    ('합동훈련', '"China navy" joint naval exercise'),
    ('해경', '"China coast guard" maritime exercise'),
    ('함정·전력', '"PLA Navy" destroyer submarine sea trials'),
    ('중국어 보도', '中国海军 演习 航母'),
]
def collect():
    items = {}
    ok = 0
    for category, query in SEARCHES:
        url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode(
            {'q': query + ' when:30d', 'hl': 'en-US', 'gl': 'US', 'ceid': 'US:en'})
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 NEXTBIO-News-Monitor'})
            with urllib.request.urlopen(req, timeout=25) as res:
                root = ET.fromstring(res.read())
            ok += 1
            for entry in root.findall('./channel/item')[:25]:
                title = (entry.findtext('title') or '').strip()
                link = (entry.findtext('link') or '').strip()
                date = (entry.findtext('pubDate') or '').strip()
                if not title or not link.startswith('https://'):
                    continue
                key = re.sub(r'[^a-z0-9\u4e00-\u9fff\uac00-\ud7a3]', '', title.casefold())
                if key not in items:
                    items[key] = {'title': title, 'url': link, 'published': date, 'category': category}
        except (OSError, TimeoutError, ET.ParseError) as exc:
            print(f'Feed failed: {category}: {exc}')
    return ok, list(items.values())

def main():
    ok, items = collect()
    if not ok:
        print('No feeds available; keeping prior data')
        return
    from email.utils import parsedate_to_datetime
    def stamp(a):
        try: return parsedate_to_datetime(a['published']).timestamp()
        except (ValueError, TypeError): return 0
    items.sort(key=stamp, reverse=True)
    previous = {}
    if OUT.exists():
        try: previous = json.loads(OUT.read_text(encoding='utf-8'))
        except (OSError, ValueError): pass
    # Preserve existing Korean editorial titles only when the exact URL still matches.
    translated = {x.get('url'): x.get('title_ko') for x in previous.get('items', []) if x.get('title_ko')}
    for item in items:
        if item['url'] in translated: item['title_ko'] = translated[item['url']]
    payload = {'last_checked': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
               'successful_queries': ok, 'items': items[:100]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Updated {len(payload["items"])} reports from {ok} queries')
if __name__ == '__main__':
    main()
