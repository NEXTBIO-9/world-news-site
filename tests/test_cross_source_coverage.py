"""Regression coverage for source diversity and audit semantics."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_cross_source_coverage import build


class CrossSourceTests(unittest.TestCase):
    def test_two_domains_are_only_diversity_not_fact_check(self):
        events = [{'id': 'event-1', 'title': 'Sample event',
                   'timeline': [{'url': 'https://publisher-a.example/a'},
                                {'url': 'https://publisher-b.example/b'}]}]
        result = build(events)
        item = result['events'][0]
        self.assertEqual(item['distinct_publisher_domains'], 2)
        self.assertTrue(item['multiple_domains_observed'])
        self.assertFalse(item['independently_fact_checked'])

    def test_repeated_domain_counts_once(self):
        events = [{'id': 'event-2', 'timeline': [
            {'url': 'https://publisher-a.example/a'},
            {'url': 'https://publisher-a.example/b'}]}]
        self.assertEqual(build(events)['events'][0]['distinct_publisher_domains'], 1)


if __name__ == '__main__':
    unittest.main()
