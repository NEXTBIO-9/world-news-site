#!/usr/bin/env python3
"""Translate at most 10 WHO titles per run; publish official notices regardless of rate limits."""
import json
import os
import sys
import time
from pathlib import Path

PATH = Path('data/bio-official.json')
LIMIT = 10

def save(data):
    tmp = PATH.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, PATH)

def main():
    if not PATH.exists():
        print('WHO translation skipped: no official data file', flush=True)
        return 0
    data = json.loads(PATH.read_text(encoding='utf-8'))
    items = data.get('items', [])
    if not isinstance(items, list) or not items:
        print('WHO translation skipped: no official notices; publishing step remains enabled', flush=True)
        return 0
    pending = [a for a in items if isinstance(a, dict) and str(a.get('title') or '').strip() and not str(a.get('title_ko') or '').strip()]
    print(f'WHO titles={len(items)} already_translated={len(items)-len(pending)} pending={len(pending)} batch_limit={LIMIT}', flush=True)
    if not pending:
        return 0
    try:
        from deep_translator import GoogleTranslator, MyMemoryTranslator
    except ImportError as exc:
        print(f'WARNING: translator unavailable: {exc}; official notices will still publish', flush=True)
        return 0
    google = GoogleTranslator(source='en', target='ko')
    try:
        memory = MyMemoryTranslator(source='en-US', target='ko-KR')
    except Exception as exc:
        memory = None
        print(f'MyMemory unavailable: {exc}', flush=True)
    google_blocked = False
    successes = 0
    for i, item in enumerate(pending[:LIMIT], 1):
        title = str(item['title']).strip()
        result = None
        if not google_blocked:
            try:
                result = google.translate(title)
            except Exception as exc:
                print(f'Google error {i}: {type(exc).__name__}: {str(exc)[:120]}', flush=True)
                if 'TooManyRequests' in type(exc).__name__ or '429' in str(exc) or 'too many requests' in str(exc).lower():
                    google_blocked = True
                    print('Google rate limited: disabled Google requests for remainder of this run', flush=True)
        if (not result or result.strip().casefold() == title.casefold()) and memory:
            try:
                result = memory.translate(title)
            except Exception as exc:
                print(f'MyMemory error {i}: {type(exc).__name__}: {str(exc)[:120]}', flush=True)
        if isinstance(result, str) and result.strip() and result.strip().casefold() != title.casefold():
            item['title_ko'] = result.strip()[:300]
            successes += 1
            save(data)
        else:
            print(f'Title {i}: not translated; original title retained', flush=True)
        time.sleep(1.2)
    remaining = sum(1 for a in items if isinstance(a, dict) and a.get('title') and not a.get('title_ko'))
    print(f'WHO translation batch: success={successes}, attempted={min(LIMIT,len(pending))}, remaining={remaining}; official feed publication allowed', flush=True)
    return 0

if __name__ == '__main__':
    sys.exit(main())
