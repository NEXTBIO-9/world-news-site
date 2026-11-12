#!/usr/bin/env python3
"""Build a compact, read-only pipeline health snapshot from existing data files."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'pipeline-health.json'
FILES = ['articles.json', 'event-timelines.json', 'event-changes.json',
         'topic-monitor.json', 'daily-briefing.json', 'weekly-report.json',
         'intelligence.json', 'evidence-index.json', 'geo-coverage.json',
         'coverage-profiles.json', 'breaking-candidates.json',
         'historical-index.json', 'country-coverage-trends.json',
         'specialized-indexes.json', 'translation-quality.json',
         'source-provenance.json', 'personalization-options.json']


def build():
    status = {}
    for filename in FILES:
        path = DATA / filename
        if not path.exists():
            status[filename] = {'present': False}
            continue
        try:
            parsed = json.loads(path.read_text(encoding='utf-8'))
            status[filename] = {'present': True, 'valid_json': True,
                                'bytes': path.stat().st_size,
                                'updated': parsed.get('updated') if isinstance(parsed, dict) else None}
        except (OSError, ValueError, TypeError):
            status[filename] = {'present': True, 'valid_json': False}
    warnings = []
    for name, record in status.items():
        if not record.get('present'):
            warnings.append({'dataset': name, 'reason': 'missing'})
        elif not record.get('valid_json'):
            warnings.append({'dataset': name, 'reason': 'invalid_json'})
    return {'updated': datetime.now(timezone.utc).isoformat(),
            'scope': 'data_file_presence_json_syntax_and_nonblocking_warnings',
            'dataset_count': len(status), 'warning_count': len(warnings),
            'warnings': warnings, 'datasets': status}


def main():
    result = build()
    if OUT.exists():
        try:
            if all(json.loads(OUT.read_text(encoding='utf-8')).get(k) == result[k]
                   for k in ('datasets', 'warnings')):
                return
        except (OSError, ValueError):
            pass
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
