#!/usr/bin/env python3
"""Build conservative, source-grounded excerpts without altering the news feed."""
import json, os, re, time, html
from pathlib import Path
from datetime import datetime, timezone
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
LIMIT = int(os.getenv('SUMMARY_MAX_NEW', '35'))
TIME_BUDGET = int(os.getenv('SUMMARY_TIME_BUDGET', '360'))
MAX_CACHE = 2400
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; NEXTBIO/1.0; public-news-excerpts)'}

def clean(s):
    return re.sub(r'\s+', ' ', html.unescape(str(s or ''))).strip()

def normalized(s):
    return re.sub(r'[^\w]+', '', clean(s).casefold())

def useful(text, title):
    t, h = normalized(text), normalized(title)
    return len(t) >= 90 and t != h and not t.startswith(h) and len(t) >= len(h) * 1.5

def excerpt(text, title):
    text = clean(text)
    # First substantive article sentences only: no invented claims or abstractive paraphrase.
    chunks = re.split(r'(?<=[.!?。！？])\s+|(?<=다\.)\s*', text[:5000])
    chosen = []
    for chunk in chunks:
        chunk = clean(chunk)
        if len(chunk) < 35 or not useful(chunk, title):
            continue
        if len(chunk) > 340:
            chunk = chunk[:337].rsplit(' ', 1)[0] + '…'
        chosen.append(chunk)
        if len(' '.join(chosen)) >= 170 or len(chosen) == 2:
            break
    result = ' '.join(chosen)[:390]
    return result if useful(result, title) else ''

def extract(url, title, session):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not parsed.hostname:
        return ''
    # RSS aggregator and social platforms rarely expose original article body.
    if parsed.hostname.endswith(('facebook.com', 'youtube.com', 'x.com', 'twitter.com')):
        return ''
    if parsed.hostname.endswith('news.google.com'):
        if gnewsdecoder is None:
            return ''
        try:
            decoded = gnewsdecoder(url, interval=0)
            url = decoded.get('decoded_url', '') if decoded.get('status') else ''
            if not url or urlparse(url).hostname.endswith('google.com'):
                return ''
        except Exception:
            return ''
    try:
        response = session.get(url, timeout=(4, 9), allow_redirects=True, stream=True)
        response.raise_for_status()
        if not response.url.startswith('https://'):
            return ''
        if 'text/html' not in response.headers.get('Content-Type', '').lower():
            return ''
        raw = response.raw.read(1_200_000, decode_content=True)
        response.close()
        article = trafilatura.extract(raw, include_comments=False, include_tables=False, favor_precision=True)
        return excerpt(article or '', title)
    except (requests.RequestException, ValueError, OSError):
        return ''

def main():
    feed = json.loads(FEED.read_text(encoding='utf-8'))
    articles = feed.get('articles', [])
    previous = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    cache = previous.get('summaries', {})
    # Keep previous successful summaries for repeat appearances.
    now = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    attempted = success = skipped_google = 0
    session = requests.Session()
    session.headers.update(HEADERS)
    for a in articles:
        url = a.get('url', '')
        title = a.get('title', '')
        if not url or not title or url in cache:
            continue
        # Existing RSS description may contain genuine reporting; use it only when distinct.
        rss = clean(a.get('summary', ''))
        summary = excerpt(rss, title) if useful(rss, title) else ''
        if not summary:
            if attempted >= LIMIT or time.monotonic() - started > TIME_BUDGET:
                break
            attempted += 1
            summary = extract(url, title, session)
        if summary:
            cache[url] = {'text': summary, 'kind': 'source_excerpt', 'updated': now}
            success += 1
    # Keep cache bounded, but never remove entries currently in the feed.
    current_urls = {a.get('url') for a in articles}
    if len(cache) > MAX_CACHE:
        others = sorted(((u,v) for u,v in cache.items() if u not in current_urls), key=lambda p: p[1].get('updated',''), reverse=True)
        keep = current_urls | {u for u,_ in others[:max(0, MAX_CACHE - len(current_urls))]}
        cache = {u:v for u,v in cache.items() if u in keep}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'updated':now,'summaries':cache}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Articles={len(articles)}, cached={len(cache)}, new_summaries={success}, fetch_attempts={attempted}')
    print('Note: no article body access => no fabricated summary. Excerpts retain source language.')

if __name__ == '__main__':
    main()
