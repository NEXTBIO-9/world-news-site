#!/usr/bin/env python3
"""Publish staged news only after Korean titles exist; keep untranslated new items private."""
import json, sys
from pathlib import Path
from translate_news_titles import english, valid

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

def read(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

def identity(article):
    return (article.get('url'), article.get('title'))

def main():
    staged_path = Path(sys.argv[1])
    audit_path = Path(sys.argv[2])
    staged = read(staged_path)
    current = read(DATA / 'articles.json')
    cache = read(DATA / 'title-translations.json').get('translations') or {}
    if not isinstance(cache, dict):
        raise ValueError('Invalid translation cache')
    new_items = staged.get('articles')
    if not isinstance(new_items, list) or not new_items:
        raise ValueError('Missing or empty staged feed; refusing publication')
    current_items = current.get('articles') or []
    if not isinstance(current_items, list):
        raise ValueError('Invalid current feed')
    previous = {identity(a): a for a in current_items if isinstance(a, dict)}
    published, seen = [], set()
    withheld = 0
    for a in new_items:
        if not isinstance(a, dict) or not a.get('title'):
            continue
        key = identity(a)
        if key in seen:
            continue
        old = previous.get(key, {})
        title = a['title']
        translated = (cache.get(title) if valid(title, cache.get(title)) else None)
        if not translated and valid(title, old.get('title_ko')):
            translated = old['title_ko']
        if english(title) and not translated:
            withheld += 1
            continue
        item = dict(a)
        if translated:
            item['title_ko'] = translated
        published.append(item)
        seen.add(key)
    # Keep previously published articles visible while newly collected titles wait.
    # Never introduce a new untranslated English headline.
    for old in current_items:
        if not isinstance(old, dict):
            continue
        key = identity(old)
        if key not in seen:
            published.append(old)
            seen.add(key)
    cap = max(1, len(new_items))
    published = published[:cap]
    # Do not roll back to an older collection if workflows finish out of order.
    if str(staged.get('updated') or '') < str(current.get('updated') or ''):
        print('Older staged collection; skipping publication')
        return
    DATA.mkdir(exist_ok=True)
    output = {'updated': staged.get('updated'), 'articles': published}
    (DATA / 'articles.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if audit_path.exists():
        (DATA / 'news_quality_audit.json').write_bytes(audit_path.read_bytes())
    print(f'Published={len(published)} withheld_untranslated_new={withheld} staged={len(new_items)}')

if __name__ == '__main__':
    main()
