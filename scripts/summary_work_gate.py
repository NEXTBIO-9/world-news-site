#!/usr/bin/env python3
"""Cheap, dependency-free gate for NEXT BIO summary extraction / Korean translation.

Usage: python scripts/summary_work_gate.py extract|translate
Writes should_run=true/false to GITHUB_OUTPUT when available.
"""
import json
import os
import re
import sys
import time
from news_priority import important
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / 'data/articles.json'
CACHE = ROOT / 'data/article-summaries.json'


def load(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def emit(enabled, reason):
    value = 'true' if enabled else 'false'
    print(f'NEXT BIO gate: should_run={value}; {reason}')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as f:
            f.write(f'should_run={value}\n')


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    if mode not in ('extract', 'translate'):
        raise SystemExit('Usage: summary_work_gate.py extract|translate')
    cache = load(CACHE)
    summaries = cache.get('summaries') or {}
    if not isinstance(summaries, dict):
        raise ValueError('Invalid summaries cache')
    now = time.time()
    if mode == 'extract':
        feed = load(FEED)
        articles = feed.get('articles') or []
        if not isinstance(articles, list):
            raise ValueError('Invalid articles feed')
        failures = cache.get('failed_urls') or {}
        if not isinstance(failures, dict):
            failures = {}
        blocked = cache.get('blocked_urls') or {}
        if not isinstance(blocked, dict):
            blocked = {}
        candidates = 0
        for article in articles:
            if not isinstance(article, dict):
                continue
            url, title = article.get('url'), article.get('title')
            if not url or not title or url in summaries or url in blocked:
                continue
            try:
                last_failure = float(failures.get(url, 0) or 0)
            except (TypeError, ValueError):
                last_failure = 0
            cooldown = 30 * 60 if important(article) else 3 * 3600
            if last_failure > now - cooldown:
                continue
            candidates += 1
        emit(candidates > 0, f'extraction candidates={candidates}; cached={len(summaries)}; blocked={len(blocked)}')
    else:
        pending = 0
        for item in summaries.values():
            if not isinstance(item, dict):
                continue
            source = str(item.get('text') or '').strip()
            if not source or item.get('text_ko'):
                continue
            if len(re.findall(r'[A-Za-z]', source)) <= 45 or len(re.findall(r'[가-힣]', source)) >= 10:
                continue
            try:
                retry_after = float(item.get('ko_retry_after', 0) or 0)
            except (TypeError, ValueError):
                retry_after = 0
            if retry_after <= now:
                pending += 1
        emit(pending > 0, f'Korean translation candidates={pending}')


if __name__ == '__main__':
    main()
