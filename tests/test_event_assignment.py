"""Regression checks for duplicate event assignment."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_event_changes import compare


class EventAssignmentTests(unittest.TestCase):
    def test_old_event_is_not_reused_for_two_new_events(self):
        old = {'original': {'title': 'Old', 'article_urls': ['a', 'b', 'c']}}
        new = {
            'renamed_one': {'title': 'First', 'article_urls': ['a', 'b', 'd']},
            'renamed_two': {'title': 'Second', 'article_urls': ['a', 'b', 'e']},
        }
        changes = compare(old, new)
        linked = [c for c in changes if c.get('previous_id') == 'original']
        self.assertEqual(len(linked), 1)
        self.assertEqual(len(changes), 2)


if __name__ == '__main__':
    unittest.main()
