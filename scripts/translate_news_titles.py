#!/usr/bin/env python3
"""Translate English headlines to Korean with NLLB; preserve successful translations."""
import json, os, re, time
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / 'data/articles.json'
CACHE = ROOT / 'data/title-translations.json'
LIMIT = max(1, int(os.getenv('TITLE_KO_LIMIT', '60')))
BUDGET = max(30, int(os.getenv('TITLE_KO_BUDGET', '1000')))
MODEL = os.getenv('SUMMARY_KO_MODEL', 'facebook/nllb-200-distilled-600M')

def load(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

def english(title):
    return len(re.findall(r'[A-Za-z]', title)) >= 8 and len(re.findall(r'[가-힣]', title)) < 5

def pending(feed, cache):
    titles = []
    seen = set()
    for a in feed.get('articles', []):
        title = str(a.get('title') or '').strip()
        if title and title not in seen and english(title) and not cache.get(title):
            titles.append(title)
            seen.add(title)
    return titles

def main():
    feed = load(FEED)
    data = load(CACHE)
    cache = data.get('translations') or {}
    if not isinstance(cache, dict):
        raise ValueError('Invalid title translation cache')
    todo = pending(feed, cache)[:LIMIT]
    if not todo:
        print('Title translations: pending=0')
        return
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    torch.set_num_threads(min(4, os.cpu_count() or 2))
    tokenizer = AutoTokenizer.from_pretrained(MODEL, src_lang='eng_Latn')
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL).eval()
    ko = tokenizer.convert_tokens_to_ids('kor_Hang')
    if ko is None or ko == tokenizer.unk_token_id:
        raise RuntimeError('Korean token not found')
    start = time.monotonic()
    successes = 0
    for title in todo:
        if time.monotonic() - start >= BUDGET:
            break
        try:
            inputs = tokenizer([title], return_tensors='pt', truncation=True, max_length=160)
            with torch.inference_mode():
                tokens = model.generate(**inputs, max_new_tokens=180, num_beams=2, do_sample=False, forced_bos_token_id=ko)
            result = tokenizer.batch_decode(tokens, skip_special_tokens=True)[0].strip()
            if len(re.findall(r'[가-힣]', result)) >= 4 and result != title and len(result) <= max(250, len(title) * 3):
                cache[title] = result
                successes += 1
        except Exception as exc:
            print('Title translation failed:', type(exc).__name__)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({'updated': datetime.now(timezone.utc).isoformat(), 'translations': cache}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Title translations: attempted={len(todo)}, new={successes}, cached={len(cache)}')

if __name__ == '__main__':
    main()
