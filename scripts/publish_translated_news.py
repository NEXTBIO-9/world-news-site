#!/usr/bin/env python3
"""Stage, retry and publish Korean-title news with a bounded persistent backlog."""
import json
import sys
from datetime import datetime, timezone
import re
from pathlib import Path
from translate_news_titles import english, valid
from news_priority import important

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
QUEUE = DATA / 'pending-title-news.json'
MAX_FAILURES = 5
MAX_PENDING = 600
MAX_PUBLISHED = 1000

# Prioritize consequential developments while retaining a fair share of routine news.
PRIORITY_TERMS = re.compile(
    r'(?i)\b(?:breaking|urgent|killed|deaths?|casualties|evacuat(?:ed|ion)|'
    r'missile|airstrike|invasion|blockade|ceasefire|nuclear|earthquake|tsunami|'
    r'outbreak|pandemic|emergency|FDA approv(?:es|al|ed)|recall|'
    r'central bank|interest rate)\b|속보|긴급|사망|대피|미사일|공습|침공|봉쇄|'
    r'휴전|핵실험|지진|쓰나미|감염병|확산|승인|리콜|기준금리'
)


def priority(article):
    article = article.get('article', article)
    title = str(article.get('title') or '')
    return important(article) or bool(PRIORITY_TERMS.search(title))


def prioritize(items):
    """Process recent reports first, breaking ties in favor of important news.

    An old high-priority backlog must not starve today's ordinary headlines.
    Malformed or missing publication dates rank last.
    """
    def timestamp(entry):
        article = entry.get('article', entry)
        raw = str(article.get('published') or '')
        try:
            dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).timestamp()
        except (ValueError, TypeError, OverflowError, OSError):
            return float('-inf')
    return sorted(items, key=lambda a: (timestamp(a), priority(a)), reverse=True)


def read(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def identity(article):
    """Return a hashable article key even when upstream metadata is malformed."""
    url = article.get('url')
    title = article.get('title')
    return (url if isinstance(url, str) else '',
            title if isinstance(title, str) else '')


def excluded_keys(queue):
    """Ignore malformed exclusion entries without discarding valid ones."""
    values = queue.get('excluded', [])
    if not isinstance(values, list):
        return set()
    return {(item[0], item[1]) for item in values
            if isinstance(item, list) and len(item) == 2
            and isinstance(item[0], str) and isinstance(item[1], str)}


def retry_count(value):
    """Treat malformed retry counters as zero rather than aborting publication."""
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError, OverflowError):
        return 0


def combined(staged):
    """Current feed first; then still-fresh queued items not in this collection."""
    queue = read(QUEUE)
    excluded = excluded_keys(queue)
    entries = queue.get('pending', [])
    if not isinstance(entries, list):
        raise ValueError('Invalid pending-title queue')
    result = []
    seen = set()
    # Merge backlog with fresh collection, then rank by article publication time.
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('article'), dict):
            continue
        item = entry['article']
        if (retry_count(entry.get('failures')) < MAX_FAILURES
                and isinstance(item.get('title'), str) and item['title'].strip()
                and isinstance(item.get('url'), str) and item['url'].strip()
                and identity(item) not in seen and identity(item) not in excluded):
            result.append(item)
            seen.add(identity(item))
    for item in staged['articles']:
        if (isinstance(item, dict) and isinstance(item.get('title'), str) and item['title'].strip()
                and isinstance(item.get('url'), str) and item['url'].strip()
                and identity(item) not in seen and identity(item) not in excluded):
            result.append(item)
            seen.add(identity(item))
    return prioritize(result)


def prepare(staged_path, output_path):
    staged = read(staged_path)
    if not isinstance(staged.get('articles'), list) or not staged['articles']:
        raise ValueError('Missing or empty staged feed')
    items = combined(staged)
    write(output_path, {'updated': staged.get('updated'), 'articles': items})
    print('Translation candidates including retained backlog:', len(items))


def unique_by_url(articles, limit=MAX_PUBLISHED):
    """Retain the first (newest) valid entry for each source URL."""
    result, urls = [], set()
    for article in articles:
        if not isinstance(article, dict):
            continue
        url = article.get('url')
        if not isinstance(url, str) or not url.strip() or url in urls:
            continue
        urls.add(url)
        result.append(article)
        if len(result) >= limit:
            break
    return result


def korean_summary_ready(article, summaries):
    """Require source-backed Korean excerpt; never accept a title-only placeholder."""
    entry = summaries.get(article.get('url'))
    if not isinstance(entry, dict) or entry.get('kind') not in ('source_excerpt', 'rss_excerpt'):
        return False
    source = str(entry.get('text') or '').strip()
    korean = str(entry.get('text_ko') or '').strip()
    if not korean and len(re.findall(r'[가-힣]', source)) >= 15:
        korean = source
    if len(korean) < 25 or len(re.findall(r'[가-힣]', korean)) < 15:
        return False
    title = str(article.get('title_ko') or article.get('title') or '').strip()
    return korean != title and len(korean) > len(title) * 0.7


def publish(staged_path, audit_path):
    staged = read(staged_path)
    current = read(DATA / 'articles.json')
    cache = read(DATA / 'title-translations.json').get('translations') or {}
    summaries = read(DATA / 'article-summaries.json').get('summaries') or {}
    if not isinstance(summaries, dict):
        raise ValueError('Invalid summary cache')
    if not isinstance(cache, dict):
        raise ValueError('Invalid translation cache')
    new_items = staged.get('articles')
    if not isinstance(new_items, list) or not new_items:
        raise ValueError('Missing or empty staged feed; refusing publication')
    current_items = current.get('articles') or []
    if not isinstance(current_items, list):
        raise ValueError('Invalid current feed')
    # A delayed run must never replace newer published content or backlog.
    if str(staged.get('updated') or '') < str(current.get('updated') or ''):
        print('Older staged collection; skipping publication')
        return
    previous = {identity(a): a for a in current_items if isinstance(a, dict)}
    existing = read(QUEUE).get('pending', [])
    if not isinstance(existing, list):
        raise ValueError('Invalid pending-title queue')
    excluded = excluded_keys(read(QUEUE))
    failure_counts = {identity(e['article']): retry_count(e.get('failures')) for e in existing
                      if isinstance(e, dict) and isinstance(e.get('article'), dict)}
    attempted_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    attempts_data = read(attempted_path) if attempted_path and attempted_path.exists() else {}
    attempts_list = attempts_data.get('attempted', []) if isinstance(attempts_data, dict) else []
    attempted = {title for title in attempts_list if isinstance(title, str)} if isinstance(attempts_list, list) else set()
    now = datetime.now(timezone.utc)
    published, seen, waiting = [], set(), []
    for a in combined(staged):
        key = identity(a)
        old = previous.get(key, {})
        title = a['title']
        translated = cache.get(title) if valid(title, cache.get(title)) else None
        if not translated and valid(title, old.get('title_ko')):
            translated = old['title_ko']
        if english(title) and not translated:
            failures = failure_counts.get(key, 0) + (1 if title in attempted else 0)
            if failures < MAX_FAILURES:
                waiting.append({'failures': failures, 'article': a})
            else:
                # Keep unsuccessful important reports retryable instead of silently losing them.
                if priority(a):
                    waiting.append({'failures': MAX_FAILURES - 1, 'article': a})
                else:
                    excluded.add(key)
            continue
        item = dict(a)
        if translated:
            item['title_ko'] = translated
        if not korean_summary_ready(item, summaries):
            waiting.append({'failures': failure_counts.get(key, 0), 'article': a})
            continue
        published.append(item)
        seen.add(key)
    for old in current_items:
        if not isinstance(old, dict):
            continue
        key = identity(old)
        if key in seen or key in excluded:
            continue
        old_title = old.get('title', '')
        old_ko = old.get('title_ko') or cache.get(old_title)
        if english(old_title) and not valid(old_title, old_ko):
            continue
        restored = dict(old)
        if english(old_title):
            restored['title_ko'] = old_ko
        if korean_summary_ready(restored, summaries):
            published.append(restored)
            seen.add(key)
    # Keep up to 1,000 published stories in publication-time order.
    # Old important stories must not bury newly published reports.
    # Missing or malformed publication dates rank oldest.
    def published_time(article):
        raw = str(article.get('published') or '')
        try:
            dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (ValueError, TypeError, OverflowError):
            return datetime.min.replace(tzinfo=timezone.utc)

    published.sort(key=lambda a: (published_time(a), priority(a)), reverse=True)
    # Multiple titles can point to one source URL; publish only its newest entry.
    published = unique_by_url(published, limit=MAX_PUBLISHED)
    # A bounded queue must never sacrifice a critical item merely due to position.
    pending_before_trim = len(waiting)
    waiting = prioritize(waiting)[:MAX_PENDING]
    # Avoid rewriting the public feed when only the collection timestamp changed.
    # Cache/backlog updates are still committed independently by the workflow.
    if published != current_items:
        write(DATA / 'articles.json', {'updated': staged.get('updated'), 'articles': published})
    else:
        print('Public articles unchanged; preserving existing feed timestamp')
    queue_payload = {'updated': now.isoformat(), 'pending': waiting,
                     'excluded': [list(k) for k in sorted(excluded, key=str)]}
    prior_queue = read(QUEUE)
    if prior_queue.get('pending') != queue_payload['pending'] or prior_queue.get('excluded') != queue_payload['excluded']:
        write(QUEUE, queue_payload)
    else:
        print('Pending queue unchanged; preserving queue timestamp')
    if audit_path.exists():
        audit = read(audit_path)
        if isinstance(audit, dict):
            audit['publication'] = {
                'published': len(published),
                'important_published': sum(priority(a) for a in published),
                'pending': len(waiting),
                'important_pending': sum(priority(e) for e in waiting),
                'excluded_title_failures': len(excluded),
                'pending_overflow': pending_before_trim - len(waiting),
                'updated': now.isoformat(),
            }
            write(DATA / 'news_quality_audit.json', audit)
    print(f'Published={len(published)} pending_retry={len(waiting)} exhausted_title_retries={sum(1 for a in combined(staged) if english(a["title"]) and a["title"] in attempted and failure_counts.get(identity(a), 0) + 1 >= MAX_FAILURES and not valid(a["title"], cache.get(a["title"]))) } staged={len(new_items)}')


def main():
    if len(sys.argv) == 4 and sys.argv[1] == 'prepare':
        prepare(Path(sys.argv[2]), Path(sys.argv[3]))
    elif len(sys.argv) in (3, 4):
        publish(Path(sys.argv[1]), Path(sys.argv[2]))
    else:
        raise SystemExit('Usage: publish_translated_news.py prepare STAGED OUT | STAGED AUDIT [ATTEMPTED_JSON]')

if __name__ == '__main__':
    main()
