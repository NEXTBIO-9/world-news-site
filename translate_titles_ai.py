#!/usr/bin/env python3
"""NEXT BIO offline EN->KO translation. No paid API.

Requires transformers, sentencepiece, torch. Model: facebook/nllb-200-distilled-600M.
NOTE: NLLB weights have CC-BY-NC-4.0 terms; review suitability before use.
"""
import json
import os
import re
import sys
from pathlib import Path

DATA = Path('data/articles.json')
MODEL = os.getenv('TRANSLATION_MODEL', 'facebook/nllb-200-distilled-600M')
LIMIT = min(max(int(os.getenv('TRANSLATE_MAX_NEW', '30')), 0), 100)
VERSION = 'nllb600m-v1'


def numbers(s):
    # compare as a multiset; allow number reordering in Korean headlines
    return sorted(re.findall(r'(?<![\w])\d+(?:[,.]\d+)*(?:\s*%)?', s))


def clean(s):
    s = re.sub(r'\s+([,.:;!?])', r'\1', s).strip()
    s = re.sub(r'\s{2,}', ' ', s)
    return s


def valid(source, translated):
    if not translated or not re.search('[가-힣]', translated):
        return False, 'no Korean'
    if numbers(source) != numbers(translated):
        return False, 'numbers changed'
    if len(translated) < 6 or len(translated) > max(220, len(source) * 2.8):
        return False, 'length anomaly'
    if re.search(r'[\u4e00-\u9fff]{3,}', translated):
        return False, 'untranslated CJK text'
    english = re.findall(r'\b[A-Za-z]{3,}\b', translated)
    # Allow named entities/acronyms, but not long chunks of untranslated English.
    if len(english) >= 6:
        return False, 'too much English'
    if translated.lower().strip(' .!?') == source.lower().strip(' .!?'):
        return False, 'unchanged'
    return True, 'ok'


def main():
    data = json.loads(DATA.read_text(encoding='utf-8'))
    articles = data.get('articles')
    if not isinstance(articles, list):
        raise ValueError('articles must be a list')
    pending = []
    for article in articles:
        if not isinstance(article, dict):
            continue
        source = str(article.get('title') or '').strip()
        if not source:
            continue
        if re.search('[가-힣]', source):
            article['title_ko'] = source
            article['translation_quality_version'] = VERSION
            continue
        # Old Argos output is not considered reliable; remove it until retranslated.
        if article.get('translation_quality_version') != VERSION:
            article.pop('title_ko', None)
            article.pop('translation_quality_version', None)
        elif article.get('title_ko') and valid(source, str(article['title_ko']))[0]:
            continue
        pending.append(article)
    print(f'Pending {len(pending)} of {len(articles)}; per-run limit {LIMIT}', flush=True)
    if not pending or LIMIT == 0:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return

    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    print(f'Loading model {MODEL} (first download may take time)', flush=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL, src_lang='eng_Latn')
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL)
    model.eval()
    target_id = tokenizer.convert_tokens_to_ids('kor_Hang')
    if target_id is None or target_id == tokenizer.unk_token_id:
        raise RuntimeError('Korean target language token unavailable')

    ok_count = reject_count = 0
    for i, article in enumerate(pending[:LIMIT], 1):
        source = article['title'].strip()
        try:
            inputs = tokenizer(source, return_tensors='pt', truncation=True, max_length=256)
            with torch.inference_mode():
                ids = model.generate(**inputs, forced_bos_token_id=target_id,
                                     max_new_tokens=160, num_beams=4, do_sample=False)
            candidate = clean(tokenizer.batch_decode(ids, skip_special_tokens=True)[0])
            accepted, reason = valid(source, candidate)
            if accepted:
                article['title_ko'] = candidate
                article['translation_quality_version'] = VERSION
                ok_count += 1
            else:
                reject_count += 1
                print(f'[{i}] Rejected ({reason}): {source[:75]} -> {candidate[:75]}', flush=True)
        except Exception as exc:
            reject_count += 1
            print(f'[{i}] Error: {type(exc).__name__}: {exc}', flush=True)
        # Save after every headline so an interrupted run retains progress locally.
        if i % 5 == 0:
            DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Finished: translated={ok_count}, rejected={reject_count}, remaining~={max(0,len(pending)-LIMIT)}', flush=True)


if __name__ == '__main__':
    main()
