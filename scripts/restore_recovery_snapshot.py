#!/usr/bin/env python3
"""Offline, opt-in restoration of a previously verified recovery snapshot.

Never runs in the publishing workflow. Restores only into a NEW directory,
not the live data directory, so an operator can review before deployment.
"""
import argparse
import json
import tarfile
from pathlib import Path

from verify_recovery_snapshot import inspect


def restore(archive, manifest, destination):
    destination = Path(destination).resolve()
    live_data = (Path(__file__).resolve().parents[1] / 'data').resolve()
    if destination == live_data or live_data in destination.parents:
        raise ValueError('Refusing to restore inside the live data directory')
    if destination.exists():
        raise FileExistsError('Destination already exists; use a new directory')
    inspect(archive, manifest)
    destination.mkdir(parents=True)
    try:
        with tarfile.open(archive, 'r:gz') as bundle:
            for member in bundle.getmembers():
                if not member.isfile() or not member.name.startswith('data/'):
                    raise ValueError('Unexpected archive member')
                name = member.name.split('/', 1)[1]
                if '/' in name or name in ('', '.', '..'):
                    raise ValueError('Unsafe filename')
                stream = bundle.extractfile(member)
                if stream is None:
                    raise ValueError('Unreadable archive member')
                payload = stream.read()
                json.loads(payload)
                (destination / name).write_bytes(payload)
    except Exception:
        for path in destination.iterdir():
            if path.is_file():
                path.unlink()
        destination.rmdir()
        raise
    return destination


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('archive')
    parser.add_argument('manifest')
    parser.add_argument('destination')
    args = parser.parse_args()
    print('Verified files restored for manual review to:',
          restore(args.archive, args.manifest, args.destination))


if __name__ == '__main__':
    main()
