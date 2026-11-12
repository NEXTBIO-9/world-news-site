"""Guard against silent loss of event snapshots when input feeds are corrupt."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_event_changes as changes
from build_cross_source_coverage import build


class EventFeedValidationTests(unittest.TestCase):
    def test_invalid_feed_preserves_existing_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            events = root / 'events.json'
            output = root / 'changes.json'
            events.write_text(json.dumps({'events': None}), encoding='utf-8')
            output.write_text('{"snapshot":{"previous":{}}}', encoding='utf-8')
            with patch.object(changes, 'EVENTS', events), patch.object(changes, 'OUT', output):
                with self.assertRaises(ValueError):
                    changes.main()
            self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['snapshot'],
                             {'previous': {}})

    def test_mixed_type_event_ids_are_sortable(self):
        result = build([{'id': 1, 'timeline': []}, {'id': 'two', 'timeline': []}])
        self.assertEqual([x['event_id'] for x in result['events']], ['1', 'two'])


if __name__ == '__main__':
    unittest.main()
