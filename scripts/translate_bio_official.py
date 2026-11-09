#!/usr/bin/env python3
"""Translate WHO announcement titles and fail visibly if translations cannot be produced."""
import json
import os
import sys
import time
from pathlib import Path

PATH = Path('data/bio-official.json')


def save(data):
    temp = PATH.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temp, PATH)


def main():
    if not PATH.exists():
        print('ERROR: Official notices file is missing.', file=sys.stderr)
        return 1
    data = json.loads(PATH.read_text(encoding='utf-8'))
    items = data.get('items', [])
    if not isinstance(items, list) or not items:
        print('ERROR: No official WHO notices to translate.', file=sys.stderr)
        return 1

    pending = [item for item in items if isinstance(item, dict)
               and str(item.get('title') or '').strip()
               and not str(item.get('title_ko') or '').strip()]
    print(f'WHO titles: {len(items)}; already Korean: {len(items)-len(pending)}; pending: {len(pending)}', flush=True)
    if not pending:
        return 0

    try:
        from deep_translator import GoogleTranslator, MyMemoryTranslator
    except ImportError as exc:
        print(f'ERROR: Translation dependency unavailable: {exc}', file=sys.stderr)
        return 1

    engines = [('Google', GoogleTranslator(source='en', target='ko'))]
    try:
        engines.append(('MyMemory', MyMemoryTranslator(source='en-US', target='ko-KR')))
    except Exception as exc:
        print(f'MyMemory initialization failed: {exc}', flush=True)

    success = 0
    failed = 0
    for index, item in enumerate(pending, 1):
        original = str(item['title']).strip()
        translated = ''
        for name, engine in engines:
            try:
                result = engine.translate(original)
                if isinstance(result, str) and result.strip() and result.strip().casefold() != original.casefold():
                    translated = result.strip()[:300]
                    break
                print(f'[{index}/{len(pending)}] {name}: empty or unchanged result', flush=True)
            except Exception as exc:
                print(f'[{index}/{len(pending)}] {name} error: {type(exc).__name__}: {str(exc)[:160]}', flush=True)
        if translated:
            item['title_ko'] = translated
            success += 1
            if success % 10 == 0:
                save(data)
        else:
            failed += 1
            print(f'[{index}/{len(pending)}] FAILED title: {original[:100]}', flush=True)
        time.sleep(0.3)
    if success:
        save(data)
    print(f'WHO Korean title translations: success={success}, failed={failed}, total={len(items)}', flush=True)
    if failed:
        print('ERROR: Some WHO titles could not be translated. Partial translations were saved locally; retry the workflow.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
