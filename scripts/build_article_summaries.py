#!/usr/bin/env python3
"""NEXT BIO v10: rotating source-grounded excerpts and actionable failure diagnostics."""
import html
import json
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

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

def get_article(url, title, session):
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        return '', 'invalid_url'
    host = parsed.hostname.lower()
    if host.endswith(('facebook.com', 'youtube.com', 'x.com', 'twitter.com', 'instagram.com')):
        return '', 'social_media'
    if host == 'news.google.com':
        if gnewsdecoder is None:
            return '', 'decoder_missing'
        try:
            result = gnewsdecoder(url, interval=0)
            if not isinstance(result, dict) or not result.get('status'):
                return '', 'google_decode_failed'
            url = result.get('decoded_url', '')
            decoded = urlparse(url)
            if decoded.scheme not in ('http', 'https') or not decoded.hostname or decoded.hostname.endswith('google.com'):
                return '', 'google_decode_invalid'
        except Exception as exc:
            return '', 'google_decode_exception_' + type(exc).__name__
    try:
        with session.get(url, timeout=(3, 7), allow_redirects=True, stream=True) as response:
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
    start = time.monotonic()
    reasons = Counter()
    new_count = attempts = rss_count = 0
    # Key fix: continue from the NEXT article on each run rather than retrying the same first 35 forever.
    cursor = int(previous.get('next_index', 0) or 0) % max(1, len(articles))
    scanned = 0
    session = requests.Session()
    session.headers.update(HEADERS)
    while scanned < len(articles) and time.monotonic() - start < BUDGET:
        index = (cursor + scanned) % len(articles)
        scanned += 1
        article = articles[index]
        url, title = article.get('url', ''), article.get('title', '')
        if not url or not title or url in cache:
            continue
        rss = clean(article.get('summary_ko') or article.get('summary'))
        text = excerpt(rss, title) if useful(rss, title) else ''
        kind = 'rss_excerpt'
        if text:
            rss_count += 1
        else:
            if attempts >= MAX_ATTEMPTS:
                scanned -= 1
                break
            attempts += 1
            text, reason = get_article(url, title, session)
            reasons[reason] += 1
            kind = 'source_excerpt'
        if text:
            cache[url] = {'text': text, 'kind': kind, 'updated': now}
            new_count += 1
    next_index = (cursor + scanned) % max(1, len(articles))
    # Retain prior successful summaries; bound stale cache without deleting current articles.
    if len(cache) > 2400:
        current = {a.get('url') for a in articles}
        stale = sorted(((u, v) for u, v in cache.items() if u not in current), key=lambda x: x[1].get('updated', ''), reverse=True)
        keep = current | {u for u, _ in stale[:max(0, 2400 - len(current))]}
        cache = {u: v for u, v in cache.items() if u in keep}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'updated': now, 'next_index': next_index, 'summaries': cache}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Articles={len(articles)}, cached={len(cache)}, new_summaries={new_count}, rss_summaries={rss_count}, fetch_attempts={attempts}')
    print(f'cursor_start={cursor}, cursor_next={next_index}, scanned={scanned}, elapsed_seconds={int(time.monotonic()-start)}')
    print('Failure reasons: ' + json.dumps(dict(reasons.most_common()), ensure_ascii=False))
    if not new_count:
        print('WARNING: zero summaries. Check failure reasons. Do not mistake a successful workflow for successful extraction.')
    print('Only source-backed excerpts are saved; no fabricated article summaries.')

if __name__ == '__main__':
    main()
