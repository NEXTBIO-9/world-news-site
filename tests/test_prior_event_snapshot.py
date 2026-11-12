"""Preserve existing event change data if previous snapshot is corrupt."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_event_changes as changes


class PriorSnapshotSafetyTests(unittest.TestCase):
    def test_corrupt_previous_snapshot_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            events = data / 'events.json'
            previous = data / 'event-changes.json'
            events.write_text('{"events":[{"id":"one","timeline":[]}]}', encoding='utf-8')
            previous.write_text('{"snapshot":"corrupt"}', encoding='utf-8')
            with patch.object(changes, 'EVENTS', events), patch.object(changes, 'OUT', previous):
                with self.assertRaises(ValueError):
                    changes.main()
            self.assertEqual(previous.read_text(encoding='utf-8'), '{"snapshot":"corrupt"}')


if __name__ == '__main__':
    unittest.main()
