#!/usr/bin/env python3
"""Build a compact, read-only pipeline health snapshot from existing data files."""
import json
from datetime import datetime, timezone, timedelta
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
         'source-provenance.json', 'personalization-options.json',
         'publication-gaps.json', 'collection-publication-audit.json', 'cross-source-coverage.json']


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
    now = datetime.now(timezone.utc)
    # Derived datasets may intentionally preserve their timestamps when their content is unchanged.
    # Only the published feed's timestamp is a useful stale-data signal.
    freshness_targets = {'articles.json'}
    for name, record in status.items():
        if not record.get('present'):
            warnings.append({'dataset': name, 'reason': 'missing'})
        elif not record.get('valid_json'):
            warnings.append({'dataset': name, 'reason': 'invalid_json'})
        elif name in freshness_targets and record.get('updated'):
            try:
                stamp = datetime.fromisoformat(str(record['updated']).replace('Z', '+00:00'))
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=timezone.utc)
                stamp = stamp.astimezone(timezone.utc)
                if stamp < now - timedelta(hours=48):
                    warnings.append({'dataset': name, 'reason': 'stale_over_48_hours'})
            except (ValueError, TypeError, OverflowError):
                warnings.append({'dataset': name, 'reason': 'invalid_update_timestamp'})
    # Cross-check publication quality without modifying or deleting articles.
    try:
        feed = json.loads((DATA / 'articles.json').read_text(encoding='utf-8'))
        articles = feed.get('articles')
        if isinstance(articles, list):
            urls = [a.get('url') for a in articles if isinstance(a, dict) and a.get('url')]
            if len(urls) != len(set(urls)):
                warnings.append({'dataset': 'articles.json', 'reason': 'duplicate_published_urls'})
            if len(articles) > 300:
                warnings.append({'dataset': 'articles.json', 'reason': 'published_feed_over_capacity'})
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    try:
        gaps = json.loads((DATA / 'publication-gaps.json').read_text(encoding='utf-8'))
        if isinstance(gaps, dict) and int(gaps.get('pending_at_retry_limit') or 0) > 0:
            warnings.append({'dataset': 'publication-gaps.json', 'reason': 'translation_retry_pressure',
                             'count': int(gaps['pending_at_retry_limit'])})
    except (OSError, ValueError, TypeError, OverflowError):
        pass
    try:
        audit = json.loads((DATA / 'collection-publication-audit.json').read_text(encoding='utf-8'))
        if isinstance(audit, dict):
            count = int((audit.get('counts') or {}).get('important_unpublished') or 0)
            if count > 0:
                warnings.append({'dataset': 'collection-publication-audit.json',
                                 'reason': 'important_collected_articles_unpublished', 'count': count})
    except (OSError, ValueError, TypeError, OverflowError, AttributeError):
        pass
    return {'updated': now.isoformat(),
            'scope': 'data_file_presence_json_syntax_and_nonblocking_warnings',
            'dataset_count': len(status), 'warning_count': len(warnings),
            'warnings': warnings, 'datasets': status}


def main():
    result = build()
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding='utf-8'))
            if all(previous.get(k) == result[k] for k in ('datasets', 'warnings')):
                return
        except (OSError, ValueError):
            pass
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
