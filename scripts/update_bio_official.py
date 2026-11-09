#!/usr/bin/env python3
"""Collect WHO Disease Outbreak News announcements from the official WHO listing.

Only WHO-origin links are accepted; no invented dates or risk classifications.
"""
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from urllib.request import Request, urlopen

OUT = Path('data/bio-official.json')
WHO = 'https://www.who.int'
PAGES = [
    WHO + '/emergencies/disease-outbreak-news',
    WHO + '/emergencies/disease-outbreak-news/',
]
# WHO Disease Outbreak News articles normally live under /emergencies/disease-outbreak-news/item/.
ARTICLE = re.compile(r'^/emergencies/disease-outbreak-news/(?:item|don)/[^/?#]+/?$', re.I)
DATE = re.compile(r'(20\d{2})[-/](\d{1,2})[-/](\d{1,2})')

class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current = None
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'a': return
        attrs = dict(attrs)
        self.current = {'href': attrs.get('href', ''), 'text': [], 'title': attrs.get('title', '')}
    def handle_data(self, data):
        if self.current is not None:
            self.current['text'].append(data)
    def handle_endtag(self, tag):
        if tag.lower() == 'a' and self.current is not None:
            self.links.append(self.current)
            self.current = None

def fetch(url):
    request = Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; NEXTBIO-OfficialNoticeMonitor/2.0)',
        'Accept': 'text/html,application/xhtml+xml',
    })
    with urlopen(request, timeout=25) as response:
        return response.read(5_000_000).decode('utf-8', 'replace')

def normalize(href):
    url = urljoin(WHO + '/', href.strip())
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in ('www.who.int', 'who.int'):
        return None
    path = unquote(parsed.path)
    if not ARTICLE.match(path):
        return None
    return WHO + path.rstrip('/')

def extract(html):
    parser = Links()
    parser.feed(html)
    results = {}
    for link in parser.links:
        url = normalize(link['href'])
        if not url: continue
        title = re.sub(r'\s+', ' ', ''.join(link['text']).strip() or link['title'].strip())
        # A link without a readable article title is not publishable.
        if len(title) < 8: continue
        # Avoid repeated site navigation / misleading placeholders.
        if title.lower() in ('read more', 'learn more', 'more information', 'view details'): continue
        date_match = DATE.search(url)
        published = ''
        if date_match:
            try:
                published = datetime(*map(int, date_match.groups()), tzinfo=timezone.utc).isoformat()
            except ValueError:
                pass
        results[url] = {'title': title[:240], 'url': url,
                        'source': 'WHO Disease Outbreak News', 'published': published}
    return list(results.values())

def main():
    items = []
    for url in PAGES:
        try:
            html = fetch(url)
            items = extract(html)
            print(f'WHO page fetched: {url}; article links: {len(items)}')
            if items: break
        except Exception as exc:
            print(f'WHO page unavailable: {url}: {exc}', file=sys.stderr)
    if not items:
        print('ERROR: No WHO announcements parsed. Existing data preserved.', file=sys.stderr)
        sys.exit(1)
    # Keep older stored announcements as well, without mixing in non-WHO content.
    old = []
    if OUT.exists():
        try:
            data = json.loads(OUT.read_text(encoding='utf-8'))
            old = [x for x in data.get('items', []) if isinstance(x, dict)
                   and normalize(str(x.get('url', ''))) and
                   str(x.get('source', '')).startswith('WHO')]
        except (ValueError, OSError):
            pass
    merged = {}
    for item in old + items:
        merged[item['url']] = item
    unique = sorted(merged.values(), key=lambda a: a.get('published', ''), reverse=True)[:100]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'updated': datetime.now(timezone.utc).isoformat(),
                               'items': unique}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'WHO official announcements saved: {len(unique)}')

if __name__ == '__main__':
    main()
