#!/usr/bin/env python3
"""Validate recovery archives before a human restores any production data."""
import hashlib
import json
import sys
import tarfile
from pathlib import PurePosixPath


def inspect(archive_path, manifest_path):
    with open(manifest_path, encoding='utf-8') as handle:
        manifest = json.load(handle)
    expected = manifest.get('files')
    if not isinstance(expected, dict) or not expected:
        raise ValueError('Missing backup file manifest')
    found = set()
    with tarfile.open(archive_path, 'r:gz') as archive:
        for member in archive.getmembers():
            path = PurePosixPath(member.name)
            if not member.isfile() or len(path.parts) != 2 or path.parts[0] != 'data':
                raise ValueError('Unsafe archive member')
            name = path.parts[1]
            if name not in expected or name in found:
                raise ValueError('Unexpected or duplicate archive member')
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError('Unreadable archive member')
            content = stream.read()
            json.loads(content)
            record = expected[name]
            if len(content) != record['bytes'] or hashlib.sha256(content).hexdigest() != record['sha256']:
                raise ValueError('Backup checksum mismatch: ' + name)
            found.add(name)
    if found != set(expected):
        raise ValueError('Backup missing expected files')
    return len(found)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Usage: verify_recovery_snapshot.py ARCHIVE MANIFEST')
    print('Verified backup files:', inspect(sys.argv[1], sys.argv[2]))
