#!/usr/bin/env python3
"""Merge locally produced title translations into the newest remote cache."""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

def read(path):
    p = Path(path)
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}

def main():
    destination, incoming = map(Path, sys.argv[1:3])
    old, new = read(destination), read(incoming)
    merged = dict(old.get('translations') or {})
    merged.update({k:v for k,v in (new.get('translations') or {}).items() if isinstance(v,str) and v.strip()})
    if destination.exists() and merged == old.get('translations', {}):
        print('No new title translations; keeping existing file unchanged')
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({'updated': datetime.now(timezone.utc).isoformat(), 'translations': merged}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Merged title translations:', len(merged))
if __name__ == '__main__':
    main()
