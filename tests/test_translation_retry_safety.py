"""Regression tests for malformed translation retry counters."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import publish_translated_news as publisher


class RetryCounterTests(unittest.TestCase):
    def test_malformed_retry_counts_are_safe(self):
        for value in ('invalid', None, [], {}, -5):
            self.assertEqual(publisher.retry_count(value), 0)
        self.assertEqual(publisher.retry_count('3'), 3)

    def test_malformed_backlog_retry_does_not_abort_preparation(self):
        staged = {'articles': [{'title': 'New', 'url': 'https://example.com/new'}]}
        queue = {'pending': [{'failures': 'broken', 'article': {
            'title': 'Old', 'url': 'https://example.com/old'}}], 'excluded': []}
        with patch.object(publisher, 'read', return_value=queue):
            items = publisher.combined(staged)
        self.assertEqual(len(items), 2)


if __name__ == '__main__':
    unittest.main()
