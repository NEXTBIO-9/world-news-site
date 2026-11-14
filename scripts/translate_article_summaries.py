#!/usr/bin/env python3
"""Translate cached, source-backed excerpts to Korean, without inventing content."""
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from news_priority import important

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'data/article-summaries.json'
MODEL = os.getenv('SUMMARY_KO_MODEL', 'facebook/nllb-200-distilled-600M')
LIMIT = max(1, int(os.getenv('SUMMARY_KO_LIMIT', '18')))
BUDGET = max(30, int(os.getenv('SUMMARY_KO_BUDGET', '270')))


def needs_translation(item):
    source = str(item.get('text') or '').strip()
    return bool(source) and not item.get('text_ko') and len(re.findall(r'[A-Za-z]', source)) > 45 and len(re.findall(r'[가-힣]', source)) < 10


NUMBER_PATTERN = re.compile(r'(?<![A-Za-z0-9_])\d+(?:[.,]\d+)*(?![A-Za-z0-9_])')


def numeric_facts(text):
    """Normalize only unambiguous comma grouping; preserve actual numeric facts."""
    facts = set()
    for match in NUMBER_PATTERN.finditer(text):
        token = match.group()
        if re.fullmatch(r'\d{1,3}(?:,\d{3})+(?:\.\d+)?', token):
            token = token.replace(',', '')
        elif ',' in token:
            # A decimal comma or ambiguous mixed punctuation must remain exact.
            facts.add(token)
            continue
        try:
            facts.add(str(Decimal(token).normalize()))
        except InvalidOperation:
            facts.add(token)
    return facts


def rejection_reason(source, translated):
    if not translated or len(translated) < 15:
        return 'too_short'
    if len(translated) > max(800, len(source) * 3):
        return 'too_long'
    if len(re.findall(r'[가-힣]', translated)) < 8:
        return 'insufficient_korean'
    if not numeric_facts(source).issubset(numeric_facts(translated)):
        return 'missing_numeric_facts'
    return None


def acceptable(source, translated):
    return rejection_reason(source, translated) is None


def translate_preserving_facts(source, tokenizer, model, target_lang_id):
    """Translate short source sentences separately to reduce numeric omissions.

    Only return a result when every numeric fact survives the full translation.
    """
    import torch
    parts = [p.strip() for p in re.split(r'(?<=[.!?。！？])\s+', source) if p.strip()]
    if not parts or len(parts) > 8:
        return ''
    translated_parts = []
    for part in parts:
        inputs = tokenizer([part], return_tensors='pt', truncation=True, max_length=384)
        with torch.inference_mode():
            tokens = model.generate(**inputs, max_new_tokens=400, num_beams=2,
                                    do_sample=False, forced_bos_token_id=target_lang_id)
        result = tokenizer.batch_decode(tokens, skip_special_tokens=True)[0].strip()
        if not result or not numeric_facts(part).issubset(numeric_facts(result)):
            # Long single sentences can omit figures. Retry bounded clauses,
            # but never append missing numbers without their source context.
            clauses = [c.strip() for c in re.split(r'(?<=[;:])\s+|;\s*', part) if c.strip()]
            if len(clauses) < 2 or len(clauses) > 5:
                return ''
            clause_results = []
            for clause in clauses:
                clause_inputs = tokenizer([clause], return_tensors='pt', truncation=True, max_length=384)
                with torch.inference_mode():
                    clause_tokens = model.generate(**clause_inputs, max_new_tokens=400, num_beams=2,
                                                   do_sample=False, forced_bos_token_id=target_lang_id)
                clause_result = tokenizer.batch_decode(clause_tokens, skip_special_tokens=True)[0].strip()
                if not clause_result or not numeric_facts(clause).issubset(numeric_facts(clause_result)):
                    return ''
                clause_results.append(clause_result)
            result = ' '.join(clause_results)
        translated_parts.append(result)
    combined = ' '.join(translated_parts)
    return combined if acceptable(source, combined) else ''


def main():
    if not PATH.exists():
        print('No summary cache; skipping Korean translation.')
        return
    data = json.loads(PATH.read_text(encoding='utf-8'))
    summaries = data.get('summaries', {})
    if not isinstance(summaries, dict):
        raise ValueError('Invalid summary cache')
    # Failed translations are retried after a cooldown, rather than consuming every run.
    pending = [(url, item) for url, item in summaries.items()
               if isinstance(item, dict) and needs_translation(item)
               and float(item.get('ko_retry_after', 0) or 0) <= time.time()]
    feed_path = ROOT / 'data/articles.json'
    feed = json.loads(feed_path.read_text(encoding='utf-8')) if feed_path.exists() else {}
    by_url = {a.get('url'): a for a in feed.get('articles', []) if isinstance(a, dict)}
    # Fresh publication time takes precedence; keep a quarter of capacity for
    # older eligible excerpts so the backlog also makes forward progress.
    def published_time(pair):
        article = by_url.get(pair[0], {})
        return str(article.get('published') or pair[1].get('updated') or '')
    # Translate articles in the current publication queue before orphaned cache
    # entries; otherwise stale cached excerpts can consume the entire budget.
    active = [pair for pair in pending if pair[0] in by_url]
    inactive = [pair for pair in pending if pair[0] not in by_url]
    newest = sorted(active, key=lambda pair: (published_time(pair), important(by_url.get(pair[0], {}))), reverse=True)
    fresh_limit = max(1, LIMIT - max(1, LIMIT // 4))
    selected = newest[:fresh_limit]
    used = {url for url, _ in selected}
    selected += [pair for pair in reversed(newest) if pair[0] not in used][:LIMIT - len(selected)]
    # Only use spare capacity for summaries no longer in the active queue.
    if len(selected) < LIMIT:
        selected += sorted(inactive, key=published_time, reverse=True)[:LIMIT - len(selected)]
    pending = selected
    if not pending:
        print('Korean summary translations: pending=0, translated=0')
        return
    # Model loads only when needed, in a separate workflow step from article fetching.
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    torch.set_num_threads(min(4, os.cpu_count() or 2))
    tokenizer = AutoTokenizer.from_pretrained(MODEL, src_lang='eng_Latn')
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL).eval()
    target_lang_id = tokenizer.convert_tokens_to_ids('kor_Hang')
    if target_lang_id is None or target_lang_id == tokenizer.unk_token_id:
        raise RuntimeError('NLLB Korean target language ID unavailable')
    started = time.monotonic()
    successes = 0
    rejected = 0
    rejection_counts = Counter()
    for url, item in pending:
        if time.monotonic() - started > BUDGET:
            break
        source = str(item['text']).strip()
        try:
            inputs = tokenizer([source], return_tensors='pt', truncation=True, max_length=384)
            with torch.inference_mode():
                tokens = model.generate(**inputs, max_new_tokens=400, num_beams=2, do_sample=False, forced_bos_token_id=target_lang_id)
            translated = tokenizer.batch_decode(tokens, skip_special_tokens=True)[0].strip()
            reason = rejection_reason(source, translated)
            if reason == 'missing_numeric_facts':
                # A full-excerpt translation may omit a number. Retry in
                # sentence-sized pieces, never inventing or inserting figures.
                fallback = translate_preserving_facts(source, tokenizer, model, target_lang_id)
                if fallback:
                    translated = fallback
                    reason = None
            if reason is None:
                item['text_ko'] = translated
                item['translated_at'] = datetime.now(timezone.utc).isoformat()
                item.pop('ko_retry_after', None)
                successes += 1
            else:
                rejected += 1
                rejection_counts[reason] += 1
                item['ko_retry_after'] = time.time() + (30 * 60 if important(by_url.get(url, {})) else 3 * 3600)
        except Exception as exc:
            rejected += 1
            rejection_counts['exception_' + type(exc).__name__] += 1
            item['ko_retry_after'] = time.time() + 3 * 3600
            print('Translation error: ' + type(exc).__name__)
    data['updated'] = datetime.now(timezone.utc).isoformat()
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Korean summary translations: pending={len(pending)}, translated={successes}, rejected={rejected}, total_ko={sum(bool(v.get("text_ko")) for v in summaries.values() if isinstance(v, dict))}')
    print('Korean summary rejection reasons: ' + json.dumps(dict(sorted(rejection_counts.items())), ensure_ascii=False))


if __name__ == '__main__':
    main()
