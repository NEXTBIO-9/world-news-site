"""Protect event-change auditing against malformed upstream data."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_event_changes import snapshot


class EventSnapshotTests(unittest.TestCase):
    def test_malformed_fields_are_safely_normalized(self):
        result = snapshot([{'id': 'event1', 'timeline': {'url': 'bad'},
                            'countries': 'not a list'}])
        self.assertEqual(result['event1']['article_urls'], [])
        self.assertEqual(result['event1']['countries'], [])

    def test_non_string_urls_do_not_break_snapshot(self):
        result = snapshot([{'id': 'event2', 'timeline': [
            {'url': ['invalid']}, {'url': 'https://example.com/a'},
            {'url': 'https://example.com/a'}],
            'countries': ['한국', None, '미국']}])
        self.assertEqual(result['event2']['article_urls'], ['https://example.com/a'])
        self.assertEqual(result['event2']['countries'], ['미국', '한국'])


if __name__ == '__main__':
    unittest.main()
