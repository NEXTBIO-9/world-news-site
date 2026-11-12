"""Collect Korean-language reporting on Chinese naval exercises and deployments daily."""
import datetime as dt
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path("data/china-navy-news.json")
SEARCHES = [
    ('항공모함', '중국 해군 항공모함 훈련'),
    ('대만해협', '중국 해군 대만해협 군사훈련'),
    ('남중국해', '중국 해군 남중국해 훈련'),
    ('서태평양', '중국 해군 서태평양 진출'),
    ('합동훈련', '중국 해군 합동훈련'),
    ('해경', '중국 해경 해상 훈련'),
    ('함정·전력', '중국 해군 구축함 잠수함 훈련'),
]
def collect():
    items = {}
    ok = 0
    for category, query in SEARCHES:
        url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode(
            {'q': query + ' when:30d', 'hl': 'ko', 'gl': 'KR', 'ceid': 'KR:ko'})
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 NEXTBIO-News-Monitor'})
            with urllib.request.urlopen(req, timeout=25) as res:
                root = ET.fromstring(res.read())
            ok += 1
            for entry in root.findall('./channel/item')[:25]:
                title = (entry.findtext('title') or '').strip()
                link = (entry.findtext('link') or '').strip()
                date = (entry.findtext('pubDate') or '').strip()
                if not title or not link.startswith('https://') or len(re.findall(r'[가-힣]', title)) < 5:
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
    payload = {'last_checked': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
               'successful_queries': ok, 'items': items[:100]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Updated {len(payload["items"])} reports from {ok} queries')
if __name__ == '__main__':
    main()
