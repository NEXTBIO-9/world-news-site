#!/usr/bin/env python3
"""NEXT BIO v12: prioritize fresh articles, retain cursor backfill and source-grounded excerpts."""
import html
import base64
import binascii
from html.parser import HTMLParser
import json
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote, urljoin

import requests
import trafilatura
try:
    from googlenewsdecoder import gnewsdecoder
except ImportError:
    gnewsdecoder = None

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / 'data/articles.json'
OUT = ROOT / 'data/article-summaries.json'
MAX_ATTEMPTS = max(1, int(os.getenv('SUMMARY_MAX_NEW', '35')))
BUDGET = max(20, int(os.getenv('SUMMARY_TIME_BUDGET', '360')))
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36', 'Accept-Language': 'en-US,en;q=0.8'}

def clean(value):
    return re.sub(r'\s+', ' ', html.unescape(str(value or ''))).strip()

def normalized(value):
    return re.sub(r'[^\w]+', '', clean(value).casefold())

def useful(value, title):
    text, heading = normalized(value), normalized(title)
    return len(text) >= 100 and text != heading and not text.startswith(heading) and len(text) >= len(heading) * 1.5

def excerpt(value, title):
    chunks = re.split(r'(?<=[.!?。！？])\s+', clean(value)[:7000])
    chosen = []
    for part in chunks:
        part = clean(part)
        if len(part) < 45 or not useful(part, title):
            continue
        if len(part) > 330:
            part = part[:327].rsplit(' ', 1)[0] + '…'
        chosen.append(part)
        if len(' '.join(chosen)) >= 180 or len(chosen) == 2:
            break
    result = ' '.join(chosen)[:420]
    return result if useful(result, title) else ''

# Google News uses multiple URL formats. A decoder failure must not stop every attempt.
BLOCKED_HOSTS = ('google.com', 'googleusercontent.com', 'gstatic.com', 'youtube.com',
                 'facebook.com', 'instagram.com', 'twitter.com', 'x.com', 't.co')

def allowed_source(url):
    p = urlparse(url)
    if p.scheme not in ('http', 'https') or not p.hostname:
        return False
    h = p.hostname.lower().rstrip('.')
    return not any(h == b or h.endswith('.' + b) for b in BLOCKED_HOSTS)

class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('property', '').lower() in ('og:url', 'article:published_url'):
            self.links.append(a.get('content', ''))
        if tag == 'link' and a.get('rel', '').lower() == 'canonical':
            self.links.append(a.get('href', ''))
        if tag == 'a':
            self.links.append(a.get('href', ''))

def legacy_google_decode(url):
    # Older Google News RSS links contain an encoded publisher URL. Newer ones do not.
    token = urlparse(url).path.rstrip('/').split('/')[-1]
    try:
        raw = base64.urlsafe_b64decode(token + '=' * (-len(token) % 4))
        for match in re.finditer(rb'https?://[^\x00-\x20\x7f"<>]+', raw):
            candidate = match.group(0).decode('utf-8', 'ignore').rstrip('\\')
            if allowed_source(candidate):
                return candidate
    except (ValueError, binascii.Error):
        pass
    return ''

def resolve_google(url, session):
    # 1. Google's own redirect/URL parameter (when present).
    query = parse_qs(urlparse(url).query)
    for key in ('url', 'q', 'u'):
        for candidate in query.get(key, []):
            candidate = unquote(candidate)
            if allowed_source(candidate):
                return candidate, 'google_query'
    # 2. Current googlenewsdecoder package, when supported by the URL format.
    if gnewsdecoder is not None:
        try:
            decoded = gnewsdecoder(url, interval=0)
            candidate = decoded.get('decoded_url', '') if isinstance(decoded, dict) else ''
            if allowed_source(candidate):
                return candidate, 'google_decoder'
        except Exception:
            pass
    # 3. Legacy embedded URL.
    candidate = legacy_google_decode(url)
    if candidate:
        return candidate, 'google_legacy'
    # 4. Follow HTTP redirects; inspect explicit publisher links in the landing HTML.
    # Never choose an arbitrary external link (ads/navigation could be mistaken for news).
    try:
        with session.get(url, timeout=(4, 10), allow_redirects=True, stream=True) as response:
            final = response.url
            if allowed_source(final):
                return final, 'google_redirect'
            if response.status_code != 200 or 'text/html' not in response.headers.get('Content-Type', '').lower():
                return '', 'google_http_' + str(response.status_code)
            page = response.raw.read(450_000, decode_content=True).decode('utf-8', 'replace')
        parser = LinkCollector()
        parser.feed(page)
        # Accept only an explicit canonical/og:url if it is a publisher URL.
        for link in parser.links[:2]:
            candidate = urljoin(final, html.unescape(link))
            if allowed_source(candidate):
                return candidate, 'google_canonical'
    except requests.RequestException as exc:
        return '', 'google_request_' + type(exc).__name__
    except Exception as exc:
        return '', 'google_parse_' + type(exc).__name__
    return '', 'google_unresolved'

def get_article(url, title, session):
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        return '', 'invalid_url'
    host = parsed.hostname.lower()
    if host == 'news.google.com':
        url, route = resolve_google(url, session)
        if not url:
            return '', route
    elif not allowed_source(url):
        return '', 'unsupported_host'
    try:
        with session.get(url, timeout=(4, 9), allow_redirects=True, stream=True) as response:
            if response.status_code != 200:
                return '', 'http_' + str(response.status_code)
            if 'text/html' not in response.headers.get('Content-Type', '').lower():
                return '', 'not_html'
            raw = response.raw.read(1_200_000, decode_content=True)
        body = trafilatura.extract(raw, include_comments=False, include_tables=False, favor_recall=True)
        if not body:
            return '', 'no_body_extracted'
        result = excerpt(body, title)
        return (result, 'ok') if result else ('', 'body_too_short_or_title_only')
    except requests.RequestException as exc:
        return '', 'request_' + type(exc).__name__
    except Exception as exc:
        return '', 'extract_' + type(exc).__name__

def main():
    articles = json.loads(FEED.read_text(encoding='utf-8')).get('articles', [])
    previous = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    cache = previous.get('summaries', {})
    if not isinstance(cache, dict):
        cache = {}
    now = datetime.now(timezone.utc).isoformat()
    failures = previous.get('failed_urls', {})
    if not isinstance(failures, dict):
        failures = {}
    # Retry failed URLs after 12 hours, not on every 15-minute run.
    retry_after = time.time() - 12 * 3600
    start = time.monotonic()
    reasons = Counter()
    new_count = attempts = rss_count = 0
    # Preserve cursor-based backfill, but give newly published articles priority.
    # The priority queue is bounded so older articles still receive coverage.
    cursor = int(previous.get('next_index', 0) or 0) % max(1, len(articles))
    scanned = 0
    fresh_count = 0
    # Prefer the newest unprocessed articles while reserving ~1/3 of attempts for backlog.
    # Stable URL cache prevents duplicate fetching and existing translated text is preserved.
    fresh_limit = max(1, MAX_ATTEMPTS * 2 // 3)
    fresh_order = sorted(range(len(articles)), key=lambda i: str(articles[i].get('published') or ''), reverse=True)
    session = requests.Session()
    session.headers.update(HEADERS)
    # Phase A: new-first (only entries not yet cached). Phase B: rotating backlog.
    queue = [(i, True) for i in fresh_order[:min(len(articles), 120)]] + [((cursor + i) % len(articles), False) for i in range(len(articles))]
    seen_indices = set()
    backlog_scanned = 0
    for index, is_fresh in queue:
        if time.monotonic() - start >= BUDGET:
            break
        if is_fresh and fresh_count >= fresh_limit:
            continue
        if index in seen_indices:
            continue
        seen_indices.add(index)
        if not is_fresh:
            backlog_scanned += 1
        scanned += 1
        article = articles[index]
        url, title = article.get('url', ''), article.get('title', '')
        if not url or not title or url in cache:
            continue
        if float(failures.get(url, 0) or 0) > retry_after:
            continue
        rss = clean(article.get('summary_ko') or article.get('summary'))
        text = excerpt(rss, title) if useful(rss, title) else ''
        kind = 'rss_excerpt'
        if text:
            rss_count += 1
        else:
            if attempts >= MAX_ATTEMPTS:
                if not is_fresh:
                    backlog_scanned -= 1
                break
            attempts += 1
            if is_fresh:
                fresh_count += 1
            text, reason = get_article(url, title, session)
            reasons[reason] += 1
            if not text:
                failures[url] = time.time()
            kind = 'source_excerpt'
        if text:
            cache[url] = {'text': text, 'kind': kind, 'updated': now}
            new_count += 1
            failures.pop(url, None)
    next_index = (cursor + backlog_scanned) % max(1, len(articles))
    # Retain prior successful summaries; bound stale cache without deleting current articles.
    if len(cache) > 2400:
        current = {a.get('url') for a in articles}
        stale = sorted(((u, v) for u, v in cache.items() if u not in current), key=lambda x: x[1].get('updated', ''), reverse=True)
        keep = current | {u for u, _ in stale[:max(0, 2400 - len(current))]}
        cache = {u: v for u, v in cache.items() if u in keep}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    current_urls = {a.get('url') for a in articles}
    failures = {u: t for u, t in failures.items() if u in current_urls and float(t or 0) > time.time() - 3 * 86400}
    OUT.write_text(json.dumps({'updated': now, 'next_index': next_index, 'failed_urls': failures, 'summaries': cache}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Articles={len(articles)}, cached={len(cache)}, new_summaries={new_count}, rss_summaries={rss_count}, fetch_attempts={attempts}')
    print(f'cursor_start={cursor}, cursor_next={next_index}, scanned={scanned}, fresh_attempts={fresh_count}, elapsed_seconds={int(time.monotonic()-start)}')
    print('Failure reasons: ' + json.dumps(dict(reasons.most_common()), ensure_ascii=False))
    print('NOTE: Google News URLs may not reveal publisher links; failures cannot be solved by retries alone.')
    if not new_count:
        print('WARNING: zero summaries. Check failure reasons. Do not mistake a successful workflow for successful extraction.')
    print('Only source-backed excerpts are saved; no fabricated article summaries.')

if __name__ == '__main__':
    main()
