"""Event continuity regression checks."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_event_changes import compare, predecessor


def event(urls):
    return {'title': 'Event', 'article_urls': urls}


class EventContinuityTests(unittest.TestCase):
    def test_one_shared_url_does_not_prove_same_event(self):
        self.assertIsNone(predecessor(event(['a', 'b']), {'old': event(['a', 'c'])}, set()))

    def test_two_shared_urls_recover_renamed_cluster(self):
        old = {'old': event(['a', 'b', 'c'])}
        new = {'new': event(['a', 'b', 'd'])}
        changes = compare(old, new)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]['change'], 'new_coverage')
        self.assertEqual(changes[0]['new_articles'], ['d'])

    def test_ambiguous_predecessor_is_not_selected(self):
        old = {'one': event(['a', 'b']), 'two': event(['a', 'b'])}
        self.assertIsNone(predecessor(event(['a', 'b', 'c']), old, set()))


if __name__ == '__main__':
    unittest.main()
