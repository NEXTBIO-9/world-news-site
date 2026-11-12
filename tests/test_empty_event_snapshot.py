"""A valid empty previous event snapshot must not hide newly published events."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_event_changes as changes


class EmptySnapshotTests(unittest.TestCase):
    def test_new_cluster_after_empty_snapshot_is_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            events = root / 'events.json'
            output = root / 'changes.json'
            events.write_text(json.dumps({'events': [{'id': 'new', 'title': 'News',
                'timeline': [{'url': 'https://example.com/a'}]}]}), encoding='utf-8')
            output.write_text(json.dumps({'snapshot': {}, 'changes': []}), encoding='utf-8')
            with patch.object(changes, 'EVENTS', events), patch.object(changes, 'OUT', output):
                changes.main()
            result = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(result['changes'][0]['change'], 'new_cluster')
            self.assertEqual(result['changes'][0]['id'], 'new')


if __name__ == '__main__':
    unittest.main()
