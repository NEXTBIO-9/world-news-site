"""Regression test for initial event snapshot creation with an empty event feed."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_event_changes as changes


class InitialSnapshotTests(unittest.TestCase):
    def test_empty_first_feed_creates_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            events = root / 'events.json'
            output = root / 'changes.json'
            events.write_text('{"events":[]}', encoding='utf-8')
            with patch.object(changes, 'EVENTS', events), patch.object(changes, 'OUT', output):
                changes.main()
            self.assertTrue(output.exists())
            self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['snapshot'], {})
            self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['changes'], [])


if __name__ == '__main__':
    unittest.main()
