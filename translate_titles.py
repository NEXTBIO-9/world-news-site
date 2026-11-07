#!/usr/bin/env python3
"""Offline English-to-Korean headline translation with Argos Translate.
No paid API, API keys, or external translation service.
"""
import json
import os
import re
import subprocess
from pathlib import Path

DATA = Path('data/articles.json')
LIMIT = max(0, min(int(os.environ.get('TRANSLATE_MAX_NEW', '60')), 150))

def previous_titles():
    try:
        result = subprocess.run(['git', 'show', 'HEAD:data/articles.json'],
                                capture_output=True, text=True, check=True)
        articles = json.loads(result.stdout).get('articles', [])
        return {(a.get('url'), a.get('title')): a['title_ko']
                for a in articles if isinstance(a, dict) and a.get('title_ko')}
    except (OSError, ValueError, subprocess.CalledProcessError):
        return {}

def load_translator():
    from argostranslate import package, translate
    languages = translate.get_installed_languages()
    en = next((x for x in languages if x.code == 'en'), None)
    ko = next((x for x in languages if x.code == 'ko'), None)
    if en and ko:
        translation = en.get_translation(ko)
        if translation: return translation

    # Download the open-source language model only when it is not cached.
    package.update_package_index()
    packages = package.get_available_packages()
    model = next((p for p in packages if p.from_code == 'en' and p.to_code == 'ko'), None)
    if not model:
        raise RuntimeError('No direct English-to-Korean Argos model in package index')
    package.install_from_path(model.download())
    languages = translate.get_installed_languages()
    en = next(x for x in languages if x.code == 'en')
    ko = next(x for x in languages if x.code == 'ko')
    return en.get_translation(ko)

def main():
    if not DATA.is_file():
        print('No data/articles.json; translation skipped')
        return
    payload = json.loads(DATA.read_text(encoding='utf-8'))
    articles = payload.get('articles', [])
    if not isinstance(articles, list): raise ValueError('articles must be a list')
    cache = previous_titles()
    pending = []
    for a in articles:
        if not isinstance(a, dict): continue
        title = str(a.get('title') or '').strip()
        if not title: continue
        if re.search(r'[가-힣]', title):
            a['title_ko'] = title
        elif not a.get('title_ko'):
            cached = cache.get((a.get('url'), title))
            if cached: a['title_ko'] = cached
            else: pending.append(a)

    if pending and LIMIT:
        try:
            translator = load_translator()
        except Exception as e:
            print('Free translation model unavailable; English originals preserved:', repr(e))
            translator = None
        if translator:
            translated = 0
            for a in pending[:LIMIT]:
                try:
                    original = str(a['title']).strip()
                    korean = translator.translate(original).strip()
                    if korean and korean != original and re.search(r'[가-힣]', korean):
                        a['title_ko'] = korean
                        translated += 1
                except Exception as e:
                    print('Could not translate one title:', repr(e))
            print('New Korean titles:', translated)
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Korean titles available:', sum(bool(a.get('title_ko')) for a in articles if isinstance(a, dict)))

if __name__ == '__main__': main()
