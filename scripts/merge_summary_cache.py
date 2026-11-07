#!/usr/bin/env python3
"""Merge locally generated summary data with latest remote cache without losing entries."""
import json
import sys
from pathlib import Path

remote_path, local_path = map(Path, sys.argv[1:3])
remote = json.loads(remote_path.read_text(encoding='utf-8')) if remote_path.exists() else {}
local = json.loads(local_path.read_text(encoding='utf-8'))
merged = dict(remote)
merged['summaries'] = dict(remote.get('summaries') or {})
for url, entry in (local.get('summaries') or {}).items():
    old = merged['summaries'].get(url)
    if isinstance(old, dict) and isinstance(entry, dict):
        # Keep Korean translations already present on either branch.
        combined = dict(old)
        combined.update(entry)
        if old.get('text_ko') and not entry.get('text_ko'):
            combined['text_ko'] = old['text_ko']
        merged['summaries'][url] = combined
    else:
        merged['summaries'][url] = entry
merged['failed_urls'] = {**(remote.get('failed_urls') or {}), **(local.get('failed_urls') or {})}
merged['next_index'] = local.get('next_index', remote.get('next_index', 0))
merged['updated'] = local.get('updated', remote.get('updated'))
remote_path.parent.mkdir(parents=True, exist_ok=True)
remote_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
