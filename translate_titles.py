#!/usr/bin/env python3
"""NEXT BIO: free headline translation with conservative quality checks.

Uses Argos Translate, preserves original title and rejects suspect translations.
No external paid translation APIs. Works with data/articles.json.
"""
import json
import os
import re
import subprocess
from pathlib import Path

DATA = Path('data/articles.json')
LIMIT = max(0, min(int(os.getenv('TRANSLATE_MAX_NEW', '60')), 150))
VERSION = 2

# Applied to English input before Argos, so terminology is more consistent.
# Keep these expressions narrow: replacing generic terms can distort meaning.
GLOSSARY = {
    r'\bmeasles\b': '홍역',
    r'\barrhythmia\b': '부정맥',
    r'\bmicrobiology\b': '미생물학',
    r'\bantimicrobial resistance\b': '항균제 내성',
    r'\bantibiotic resistance\b': '항생제 내성',
    r'\bclinical trial(s)?\b': '임상시험',
    r'\bFDA\b': 'FDA',
}

# Safe, limited fixes after translation. No factual paraphrasing or invented claims.
POST_FIXES = [
    (r'(?i)\bmeasles\b', '홍역'),
    (r'(?i)\barrhythmia\b', '부정맥'),
    (r'(?i)\bmicrobiology\b', '미생물학'),
    (r'(?i)\bbiotech\b', '바이오 기술'),
    (r'(?i)\bwearable(s)?\b', '웨어러블'),
    (r'(?i)\bhype\b', '과장된 기대'),
    (r'\s+([,.!?…])', r'\1'),
    (r'\s{2,}', ' '),
]

# These are specific, non-ambiguous headline patterns; prefer exact meaning.
PATTERNS = [
    (re.compile(r'^Factors Driving the Rapid Microbiology Testing Kits Market:?$', re.I),
     '신속 미생물 검사 키트 시장의 성장 요인'),
    (re.compile(r'^Recall Roundup: (January|February|March|April|May|June|July|August|September|October|November|December) (\d{4})$', re.I),
     None),
]
MONTHS = dict(zip('January February March April May June July August September October November December'.split(), range(1, 13)))


def special_title(title):
    for pattern, output in PATTERNS:
        m = pattern.fullmatch(title.strip())
        if not m:
            continue
        if output is not None:
            return output
        return f'{m.group(2)}년 {MONTHS[m.group(1).title()]}월 제품 리콜 종합'
    return None


def extract_numbers(s):
    # Protect numeric quantities, including percentages and years.
    return re.findall(r'(?<![\w])\d[\d,.]*(?:\s*%)?', s)


def quality_ok(original, korean):
    if not korean or not re.search(r'[가-힣]', korean):
        return False
    if extract_numbers(original) != extract_numbers(korean):
        return False
    if len(korean) < 5 or len(korean) > max(200, len(original) * 3):
        return False
    # Reject severely mixed-language output; permit company names and acronyms.
    english_words = re.findall(r'\b[A-Za-z]{4,}\b', korean)
    if len(english_words) >= 4 or (len(english_words) >= 2 and len(english_words) > len(re.findall(r'[가-힣]+', korean))):
        return False
    if re.search(r'(?i)\b(?:measles|arrhythmia|hype)\b', korean):
        return False
    return True


def polish(text):
    for pattern, replacement in POST_FIXES:
        text = re.sub(pattern, replacement, text)
    return text.strip()


def load_translator():
    from argostranslate import package, translate
    installed = translate.get_installed_languages()
    en = next((x for x in installed if x.code == 'en'), None)
    ko = next((x for x in installed if x.code == 'ko'), None)
    if en and ko:
        result = en.get_translation(ko)
        if result:
            return result
    package.update_package_index()
    model = next((p for p in package.get_available_packages() if p.from_code == 'en' and p.to_code == 'ko'), None)
    if not model:
        raise RuntimeError('English-to-Korean Argos model unavailable')
    package.install_from_path(model.download())
    installed = translate.get_installed_languages()
    en = next(x for x in installed if x.code == 'en')
    ko = next(x for x in installed if x.code == 'ko')
    return en.get_translation(ko)


def previous_titles():
    try:
        p = subprocess.run(['git', 'show', 'HEAD:data/articles.json'], capture_output=True, text=True, check=True)
        return {(a.get('url'), a.get('title')): a for a in json.loads(p.stdout).get('articles', []) if isinstance(a, dict)}
    except (OSError, ValueError, subprocess.CalledProcessError):
        return {}


def main():
    if not DATA.is_file():
        print('data/articles.json missing; skipped')
        return
    payload = json.loads(DATA.read_text(encoding='utf-8'))
    articles = payload.get('articles', [])
    if not isinstance(articles, list):
        raise ValueError('articles must be a list')
    previous = previous_titles()
    pending = []
    fixed = 0
    for a in articles:
        if not isinstance(a, dict):
            continue
        original = str(a.get('title') or '').strip()
        if not original:
            continue
        if re.search(r'[가-힣]', original):
            a['title_ko'] = original
            a['translation_quality_version'] = VERSION
            continue
        prior = previous.get((a.get('url'), original), {})
        if not a.get('title_ko') and prior.get('title_ko'):
            a['title_ko'] = prior['title_ko']
            if prior.get('translation_quality_version'):
                a['translation_quality_version'] = prior['translation_quality_version']
        exact = special_title(original)
        if exact:
            a['title_ko'] = exact
            a['translation_quality_version'] = VERSION
            fixed += 1
            continue
        # Old translations must be rechecked. Do not trust existing Argos output.
        if a.get('translation_quality_version') == VERSION and quality_ok(original, str(a.get('title_ko', ''))):
            continue
        # Hide low-quality old translations until a new one passes validation.
        a.pop('title_ko', None)
        a.pop('translation_quality_version', None)
        pending.append(a)

    translated = rejected = 0
    if pending and LIMIT:
        try:
            translator = load_translator()
        except Exception as e:
            print('Translator unavailable; original English headlines retained:', repr(e))
            translator = None
        if translator:
            for a in pending[:LIMIT]:
                original = a['title'].strip()
                try:
                    candidate = polish(translator.translate(original))
                    if quality_ok(original, candidate):
                        a['title_ko'] = candidate
                        a['translation_quality_version'] = VERSION
                        translated += 1
                    else:
                        rejected += 1
                except Exception as e:
                    rejected += 1
                    print('Translation failed for one headline:', repr(e))
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Quality v{VERSION}: exact={fixed}, translated={translated}, rejected={rejected}, pending={len(pending)}')


if __name__ == '__main__':
    main()
