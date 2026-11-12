#!/usr/bin/env python3
"""Keep a bounded, versioned recovery snapshot of critical published data.

This script writes a compressed backup artifact for GitHub Actions upload.
It never overwrites or restores production data automatically.
"""
import gzip
import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
BACKUP = ROOT / 'nextbio-recovery.tar.gz'
MANIFEST = ROOT / 'nextbio-recovery-manifest.json'
FILES = ('articles.json', 'article-summaries.json', 'title-translations.json',
         'pending-title-news.json', 'event-timelines.json', 'historical-index.json')


def build():
    present = []
    manifest = {'created': datetime.now(timezone.utc).isoformat(), 'files': {}}
    for name in FILES:
        path = DATA / name
        if not path.is_file():
            continue
        payload = path.read_bytes()
        json.loads(payload)
        manifest['files'][name] = {'sha256': hashlib.sha256(payload).hexdigest(), 'bytes': len(payload)}
        present.append((name, path))
    if not present:
        raise RuntimeError('No data files to back up')
    with tarfile.open(BACKUP, 'w:gz') as archive:
        for name, path in present:
            archive.add(path, arcname='data/' + name, recursive=False)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print('Recovery snapshot created for', len(present), 'datasets')


if __name__ == '__main__':
    build()
