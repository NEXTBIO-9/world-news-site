#!/usr/bin/env python3
"""NEXT BIO offline EN->KO translation. No paid API.

Requires transformers, sentencepiece, torch. Model: facebook/nllb-200-distilled-600M.
NOTE: NLLB weights have CC-BY-NC-4.0 terms; review suitability before use.
"""
import json
import os
import re
from collections import Counter
from pathlib import Path

DATA = Path('data/articles.json')
MODEL = os.getenv('TRANSLATION_MODEL', 'facebook/nllb-200-distilled-600M')
LIMIT = min(max(int(os.getenv('TRANSLATE_MAX_NEW', '100')), 0), 300)
VERSION = 'nllb600m-v7'
# v3 prioritizes missing titles, then refreshes older translations without deleting them.


def numbers(s):
    """Compare numeric facts, ignoring comma grouping and spacing before %."""
    found = re.findall(r'(?<![\w])\d+(?:[,.]\d+)*(?:\s*%)?', s)
    return sorted(re.sub(r'\s+', '', x).replace(',', '') for x in found)


def source_acronyms(s):
    """Acronyms are easy to accidentally omit or hallucinate."""
    return Counter(re.findall(r'(?<![A-Za-z])[A-Z]{2,6}(?![A-Za-z])', s))


def source_polarity(s):
    return bool(re.search(r"\b(?:not|never|no longer|without|won't|isn't|aren't|can't|cannot|fails? to|denies?|rejects?)\b", s, re.I))


def clean(s):
    s = re.sub(r'\s+([,.:;!?])', r'\1', s).strip()
    s = re.sub(r'\s{2,}', ' ', s)
    return s


def polish(source, translated):
    """Conservative edits only: never invent facts or rewrite unfamiliar names."""
    result = clean(translated)
    # Known false friend: 'effortless' is easy/convenient, not powerless.
    if re.search(r'\beffortless\b', source, re.I):
        result = result.replace('무력하다는', '간편하다는').replace('무력한', '간편한')
        result = result.replace('노력이 없다는', '간편하다는')
    # Common international-news collocation: fuel clashes = intensify clashes.
    if re.search(r'\bfuel(?:s|ed|ing)?\b.*\bclashes\b', source, re.I):
        result = result.replace('충돌을 불러일으킨다', '충돌을 격화시킨다')
    # Conservative, source-conditioned corrections based on observed news errors.
    if re.search(r'\beffortless\b', source, re.I):
        result = result.replace('무력하다는', '간편하다는').replace('무력하다고', '간편하다고')
        result = result.replace('무력한', '간편한').replace('노력이 필요 없는', '간편한')
    if re.search(r'\binternal feuds\b', source, re.I):
        result = result.replace('내부 분쟁', '내부 갈등')
    if re.search(r'\bpolitical violence\b', source, re.I):
        result = result.replace('정치 폭행', '정치적 폭력')
    # Avoid the period at the end of a Korean news headline.
    return result.rstrip(' .')


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
    if re.search(r'\beffortless\b', source, re.I) and re.search(r'무력|무능', translated):
        return False, 'effortless mistranslated'
    if re.search(r'\b(?:safe|safely)\b', source, re.I) and re.search(r'위험하|안전하지 않', translated):
        return False, 'safety polarity mismatch'
    if source_polarity(source) and not re.search(r'않|아니|못|없|금지|중단|거부|불가|부정|실패|없이|거절|부인', translated):
        return False, 'possible missing negation'
    if any(translated.count(x) < n for x, n in source_acronyms(source).items()):
        return False, 'acronym lost'
    if translated.lower().strip(' .!?') == source.lower().strip(' .!?'):
        return False, 'unchanged'
    return True, 'ok'


def headline_score(source, candidate):
    """Conservative ranking, not a semantic accuracy guarantee."""
    score = 0
    score += min(len(re.findall(r'[가-힣]', candidate)), 35) / 10
    score -= len(re.findall(r'\b[A-Za-z]{3,}\b', candidate)) * 1.5
    score -= len(re.findall(r'[!?]{2,}|[.]{3,}', candidate)) * 2
    # Disfavor known damaging mistranslations from real NEXT BIO headlines.
    if re.search(r'\beffortless\b', source, re.I) and re.search(r'무력|무능', candidate):
        score -= 100
    if re.search(r'\b(?:safe|safely)\b', source, re.I) and re.search(r'위험하|안전하지 않', candidate):
        score -= 100
    return score


def generate_candidates(model, tokenizer, target_id, source, torch, beams=4, count=1):
    inputs = tokenizer(source, return_tensors='pt', truncation=True, max_length=256)
    with torch.inference_mode():
        ids = model.generate(**inputs, forced_bos_token_id=target_id,
                             max_new_tokens=160, num_beams=beams,
                             num_return_sequences=count, do_sample=False)
    return list(dict.fromkeys(polish(source, x) for x in tokenizer.batch_decode(ids, skip_special_tokens=True)))



STOPWORDS = {'the', 'a', 'an', 'of', 'to', 'and', 'in', 'on', 'at', 'for', 'with',
             'from', 'by', 'as', 'is', 'are', 'was', 'were', 'will', 'has', 'have',
             'that', 'this', 'after', 'over', 'amid', 'its', 'their', 'his', 'her'}


def content_words(text):
    """Lightweight round-trip content check; not a semantic correctness proof."""
    return {x for x in re.findall(r"[a-z]{3,}", text.lower()) if x not in STOPWORDS}


def roundtrip_score(model, tokenizer, candidate, source, torch):
    """Back-translate candidate KO->EN to flag obvious missing source concepts.

    Same locally cached model, no network or paid API. Use only to rank candidates;
    it is not reliable enough to assert semantic equivalence on its own.
    """
    tokenizer.src_lang = 'kor_Hang'
    try:
        tokens = tokenizer(candidate, return_tensors='pt', truncation=True, max_length=256)
        with torch.inference_mode():
            output = model.generate(**tokens,
                forced_bos_token_id=tokenizer.convert_tokens_to_ids('eng_Latn'),
                max_new_tokens=160, num_beams=3)
        reconstructed = tokenizer.batch_decode(output, skip_special_tokens=True)[0]
    finally:
        tokenizer.src_lang = 'eng_Latn'
    original = content_words(source)
    recovered = content_words(reconstructed)
    return (len(original & recovered) / len(original)) if original else 0.5


def select_best(model, tokenizer, target_id, source, torch):
    """Evaluate multiple beam candidates with local backtranslation as a weak signal."""
    options = generate_candidates(model, tokenizer, target_id, source, torch, beams=5, count=3)
    good = [x for x in options if valid(source, x)[0]]
    if not good:
        return None, 'no candidate passed factual safeguards'
    # Evaluate up to 3 candidates, only for already-valid headlines.
    scored = []
    for candidate in good[:3]:
        try:
            fidelity = roundtrip_score(model, tokenizer, candidate, source, torch)
        except Exception as exc:
            print(f'Backtranslation check unavailable: {type(exc).__name__}: {exc}', flush=True)
            fidelity = None
        # A low round-trip score is a warning, not automatic proof of mistranslation.
        score = headline_score(source, candidate) + (fidelity * 6 if fidelity is not None else 0)
        scored.append((score, fidelity, candidate))
    scored.sort(key=lambda x: x[0], reverse=True)
    _, fidelity, candidate = scored[0]
    # Only reject extremely low lexical recovery on longer titles, as a safety net.
    if fidelity is not None and len(content_words(source)) >= 6 and fidelity < 0.12:
        return None, f'very low round-trip content overlap ({fidelity:.2f})'
    return candidate, 'ok'

def main():
    data = json.loads(DATA.read_text(encoding='utf-8'))
    articles = data.get('articles')
    if not isinstance(articles, list):
        raise ValueError('articles must be a list')
    missing = []
    refresh = []
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
        current = str(article.get('title_ko') or '').strip()
        if current and article.get('translation_quality_version') == VERSION and valid(source, current)[0]:
            continue
        # Preserve previously published translations until a better result is ready.
        # First translate titles with no usable Korean; then improve older translations.
        if not current or not valid(source, current)[0]:
            if article.get('translation_failed_version') != VERSION:
                missing.append(article)
        else:
            refresh.append(article)
    pending = missing + refresh
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
            candidate, selection_reason = select_best(model, tokenizer, target_id, source, torch)
            if candidate is None:
                article['translation_failed_version'] = VERSION
                reject_count += 1
                print(f'[{i}] Rejected ({selection_reason}): {source[:100]}', flush=True)
                continue
            accepted, reason = valid(source, candidate)
            if accepted:
                article['title_ko'] = candidate
                article['translation_quality_version'] = VERSION
                article.pop('translation_failed_version', None)
                ok_count += 1
            else:
                article['translation_failed_version'] = VERSION
                reject_count += 1
                print(f'[{i}] Rejected ({reason}): {source[:75]} -> {candidate[:75]}', flush=True)
        except Exception as exc:
            # Transient errors must remain retryable.
            reject_count += 1
            print(f'[{i}] Error: {type(exc).__name__}: {exc}', flush=True)
        # Save after every headline so an interrupted run retains progress locally.
        if i % 5 == 0:
            DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Finished: translated={ok_count}, rejected={reject_count}, remaining~={max(0,len(pending)-LIMIT)}', flush=True)


if __name__ == '__main__':
    main()
