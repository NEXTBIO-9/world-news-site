#!/usr/bin/env python3
"""Translate official WHO titles into Korean, preserving source titles and URLs."""
import json
import os
import time
from pathlib import Path

PATH = Path('data/bio-official.json')

def main():
    if not PATH.exists():
        print('No official feed yet')
        return
    data = json.loads(PATH.read_text(encoding='utf-8'))
    items = data.get('items', [])
    if not isinstance(items, list) or not items:
        print('No official notices to translate')
        return
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source='en', target='ko')
    except Exception as exc:
        print('Translator unavailable:', exc)
        return
    done = 0
    for item in items[:50]:
        title = str(item.get('title') or '').strip()
        if not title or item.get('title_ko'):
            continue
        try:
            ko = translator.translate(title)
            if ko and ko.strip() and ko.strip() != title:
                item['title_ko'] = ko.strip()[:300]
                done += 1
            time.sleep(0.5)
        except Exception as exc:
            print('Translation failed:', title[:70], str(exc)[:120])
    if done:
        temp = PATH.with_suffix('.tmp')
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        os.replace(temp, PATH)
    print('Translated official titles:', done)

if __name__ == '__main__':
    main()
