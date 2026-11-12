#!/usr/bin/env python3
"""Privacy-preserving optional topic profile defaults for future personalization.

No users, cookies, identifiers, browsing history or device data are collected.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/personalization-options.json'
OPTIONS = {
    'version': 1,
    'enabled_by_default': False,
    'storage': 'none',
    'collect_user_data': False,
    'available_topics': ['military', 'infectious_disease', 'disaster',
                         'economy', 'biotechnology', 'clinical_trials'],
    'available_filters': ['country', 'category', 'topic', 'published_date'],
    'note': 'Configuration only. Personalization is not active and no UI changes are made.'
}


def main():
    payload = json.dumps(OPTIONS, ensure_ascii=False, indent=2) + '\n'
    if not OUT.exists() or OUT.read_text(encoding='utf-8') != payload:
        OUT.write_text(payload, encoding='utf-8')


if __name__ == '__main__':
    main()
