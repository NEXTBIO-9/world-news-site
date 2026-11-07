#!/usr/bin/env python3
"""Translate cached, source-backed excerpts to Korean, without inventing content."""
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'data/article-summaries.json'
MODEL = os.getenv('SUMMARY_KO_MODEL', 'Helsinki-NLP/opus-mt-en-ko')
LIMIT = max(1, int(os.getenv('SUMMARY_KO_LIMIT', '18')))
BUDGET = max(30, int(os.getenv('SUMMARY_KO_BUDGET', '270')))


def needs_translation(item):
    source = str(item.get('text') or '').strip()
    return bool(source) and not item.get('text_ko') and len(re.findall(r'[A-Za-z]', source)) > 45 and len(re.findall(r'[가-힣]', source)) < 10


def acceptable(source, translated):
    if not translated or len(translated) < 15 or len(translated) > max(800, len(source) * 3):
        return False
    if len(re.findall(r'[가-힣]', translated)) < 8:
        return False
    # Reject translations that drop numeric facts; keep source text available for review.
    numbers = lambda s: set(re.findall(r'(?<!\w)\d+(?:[.,]\d+)*(?!\w)', s))
    if not numbers(source).issubset(numbers(translated)):
        return False
    return True


def main():
    if not PATH.exists():
        print('No summary cache; skipping Korean translation.')
        return
    data = json.loads(PATH.read_text(encoding='utf-8'))
    summaries = data.get('summaries', {})
    if not isinstance(summaries, dict):
        raise ValueError('Invalid summary cache')
    pending = [(url, item) for url, item in summaries.items() if isinstance(item, dict) and needs_translation(item)]
    # Newest excerpts first; older entries are translated over subsequent runs.
    pending.sort(key=lambda pair: pair[1].get('updated', ''), reverse=True)
    pending = pending[:LIMIT]
    if not pending:
        print('Korean summary translations: pending=0, translated=0')
        return
    # Model loads only when needed, in a separate workflow step from article fetching.
    import torch
    from transformers import MarianMTModel, MarianTokenizer
    torch.set_num_threads(min(4, os.cpu_count() or 2))
    tokenizer = MarianTokenizer.from_pretrained(MODEL)
    model = MarianMTModel.from_pretrained(MODEL).eval()
    started = time.monotonic()
    successes = 0
    rejected = 0
    for url, item in pending:
        if time.monotonic() - started > BUDGET:
            break
        source = str(item['text']).strip()
        try:
            inputs = tokenizer([source], return_tensors='pt', truncation=True, max_length=384)
            with torch.inference_mode():
                tokens = model.generate(**inputs, max_new_tokens=400, num_beams=3, do_sample=False)
            translated = tokenizer.batch_decode(tokens, skip_special_tokens=True)[0].strip()
            if acceptable(source, translated):
                item['text_ko'] = translated
                item['translated_at'] = datetime.now(timezone.utc).isoformat()
                successes += 1
            else:
                rejected += 1
        except Exception as exc:
            rejected += 1
            print('Translation error: ' + type(exc).__name__)
    data['updated'] = datetime.now(timezone.utc).isoformat()
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Korean summary translations: pending={len(pending)}, translated={successes}, rejected={rejected}, total_ko={sum(bool(v.get("text_ko")) for v in summaries.values() if isinstance(v, dict))}')


if __name__ == '__main__':
    main()
