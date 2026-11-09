#!/usr/bin/env python3
"""Stage, retry and publish Korean-title news with a bounded persistent backlog."""
import json
import sys
from datetime import datetime, timezone
import re
from pathlib import Path
from translate_news_titles import english, valid

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
QUEUE = DATA / 'pending-title-news.json'
MAX_FAILURES = 2
MAX_PENDING = 250


def read(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def identity(article):
    return (article.get('url'), article.get('title'))


def combined(staged):
    """Current feed first; then still-fresh queued items not in this collection."""
    queue = read(QUEUE)
    excluded = {tuple(x) for x in queue.get('excluded', []) if isinstance(x, list) and len(x) == 2}
    entries = queue.get('pending', [])
    if not isinstance(entries, list):
        raise ValueError('Invalid pending-title queue')
    result = []
    seen = set()
    # Retry existing backlog first, so the 60-title batch cannot starve it.
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('article'), dict):
            continue
        item = entry['article']
        if int(entry.get('failures', 0)) < MAX_FAILURES and item.get('title') and identity(item) not in seen and identity(item) not in excluded:
            result.append(item)
            seen.add(identity(item))
    for item in staged['articles']:
        if isinstance(item, dict) and item.get('title') and identity(item) not in seen and identity(item) not in excluded:
            result.append(item)
            seen.add(identity(item))
    return result


def prepare(staged_path, output_path):
    staged = read(staged_path)
    if not isinstance(staged.get('articles'), list) or not staged['articles']:
        raise ValueError('Missing or empty staged feed')
    items = combined(staged)
    write(output_path, {'updated': staged.get('updated'), 'articles': items})
    print('Translation candidates including retained backlog:', len(items))


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
    excluded = {tuple(x) for x in read(QUEUE).get('excluded', []) if isinstance(x, list) and len(x) == 2}
    failure_counts = {identity(e['article']): int(e.get('failures', 0)) for e in existing
                      if isinstance(e, dict) and isinstance(e.get('article'), dict)}
    attempted_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    attempted = set(read(attempted_path).get('attempted', [])) if attempted_path and attempted_path.exists() else set()
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
    # Bound site feed and backlog independently.
    cap = min(300, max(1, len(new_items)))
    published = published[:cap]
    waiting = waiting[:MAX_PENDING]
    write(DATA / 'articles.json', {'updated': staged.get('updated'), 'articles': published})
    write(QUEUE, {'updated': now.isoformat(), 'pending': waiting, 'excluded': [list(k) for k in sorted(excluded, key=str)]})
    if audit_path.exists():
        (DATA / 'news_quality_audit.json').write_bytes(audit_path.read_bytes())
    print(f'Published={len(published)} pending_retry={len(waiting)} excluded_after_2_failures={sum(1 for a in combined(staged) if english(a["title"]) and a["title"] in attempted and failure_counts.get(identity(a), 0) + 1 >= MAX_FAILURES and not valid(a["title"], cache.get(a["title"]))) } staged={len(new_items)}')


def main():
    if len(sys.argv) == 4 and sys.argv[1] == 'prepare':
        prepare(Path(sys.argv[2]), Path(sys.argv[3]))
    elif len(sys.argv) in (3, 4):
        publish(Path(sys.argv[1]), Path(sys.argv[2]))
    else:
        raise SystemExit('Usage: publish_translated_news.py prepare STAGED OUT | STAGED AUDIT [ATTEMPTED_JSON]')

if __name__ == '__main__':
    main()
