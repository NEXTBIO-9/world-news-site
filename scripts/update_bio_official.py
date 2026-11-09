#!/usr/bin/env python3
"""WHO Disease Outbreak News collector; preserve existing notices on failures."""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

OUT = Path('data/bio-official.json')
BASE = 'https://www.who.int'
ENDPOINTS = [BASE + '/api/news/diseaseoutbreaknews?$top=60&$orderby=PublicationDate%20desc',
             BASE + '/api/default/diseaseoutbreaknews?$top=60&$orderby=PublicationDate%20desc',
             BASE + '/api/emergencies/diseaseoutbreaknews?$top=60&$orderby=PublicationDate%20desc']
PATH_PREFIX = '/emergencies/disease-outbreak-news/item/'


def fetch(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (NEXTBIO official WHO monitor)',
                                'Accept': 'application/json'})
    with urlopen(req, timeout=25) as response:
        return json.load(response)


def entries(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for k in ('value', 'items', 'Items', 'results', 'Results'):
            if isinstance(data.get(k), list):
                return data[k]
        if isinstance(data.get('d'), dict):
            return entries(data['d'])
    return []


def field(item, *names):
    for name in names:
        v = item.get(name)
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, dict):
            for key in ('Value', 'value', 'en', 'English'):
                if isinstance(v.get(key), str) and v[key].strip():
                    return v[key].strip()
    return ''


def verified_url(item):
    slug = field(item, 'UrlName', 'urlName', 'urlname')
    direct = field(item, 'ItemDefaultUrl', 'itemDefaultUrl', 'Url', 'url')
    candidates = [direct]
    if slug:
        candidates.append(PATH_PREFIX + slug.strip('/'))
    for candidate in candidates:
        if not candidate:
            continue
        url = urljoin(BASE + '/', candidate)
        p = urlsplit(url)
        if p.scheme != 'https' or p.hostname not in ('who.int', 'www.who.int'):
            continue
        if p.path.startswith(PATH_PREFIX) and len(p.path) > len(PATH_PREFIX):
            return BASE + p.path.rstrip('/')
    return ''


def parse(data):
    rows = entries(data)
    print('WHO API raw records:', len(rows), flush=True)
    if rows and isinstance(rows[0], dict):
        print('WHO API sample field names:', ', '.join(sorted(rows[0].keys())[:35]), flush=True)
        print('WHO API sample URL fields:', {k: str(rows[0].get(k, ''))[:150] for k in
              ('ItemDefaultUrl', 'UrlName', 'Url', 'Title')}, flush=True)
    found = {}
    rejected = {'no_title': 0, 'no_verified_url': 0}
    for obj in rows:
        if not isinstance(obj, dict):
            continue
        title = field(obj, 'OverrideTitle', 'Title', 'title', 'Headline', 'headline')
        if not title:
            rejected['no_title'] += 1
            continue
        url = verified_url(obj)
        if not url:
            rejected['no_verified_url'] += 1
            continue
        published = field(obj, 'PublicationDate', 'PublicationDateAndTime', 'publicationDate', 'DateCreated')
        if published.startswith('/Date('):
            m = re.search(r'\d{10,13}', published)
            if m:
                n = int(m.group())
                published = datetime.fromtimestamp(n / (1000 if n > 10**11 else 1), timezone.utc).isoformat()
        found[url] = {'title': re.sub(r'<[^>]*>', '', title).strip()[:240],
                      'url': url, 'source': 'WHO Disease Outbreak News', 'published': published}
    print('WHO API rejected:', rejected, 'accepted:', len(found), flush=True)
    return list(found.values())


def main():
    new = []
    for endpoint in ENDPOINTS:
        try:
            new = parse(fetch(endpoint))
            print('WHO API accepted from:', endpoint, len(new), flush=True)
            if new:
                break
        except Exception as exc:
            print('WHO API error:', endpoint, repr(exc)[:300], file=sys.stderr, flush=True)
    if not new:
        print('ERROR: No verified WHO reports extracted; previous data unchanged.', file=sys.stderr)
        sys.exit(1)
    old = []
    if OUT.exists():
        try:
            old = [x for x in json.loads(OUT.read_text(encoding='utf-8')).get('items', [])
                   if isinstance(x, dict) and verified_url({'ItemDefaultUrl': x.get('url', '')})]
        except (ValueError, OSError):
            pass
    merged = {x['url']: x for x in old}
    for x in new:
        prev = merged.get(x['url'], {})
        if prev.get('title') == x['title'] and prev.get('title_ko'):
            x['title_ko'] = prev['title_ko']
        merged[x['url']] = x
    items = sorted(merged.values(), key=lambda x: x.get('published', ''), reverse=True)[:100]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'updated': datetime.now(timezone.utc).isoformat(),
                               'items': items}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('WHO official announcements saved:', len(items))


if __name__ == '__main__':
    main()
