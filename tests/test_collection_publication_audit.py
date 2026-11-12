"""Regression tests for news collection-to-publication gap accounting."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_collection_publication_audit import build


class CollectionPublicationAuditTests(unittest.TestCase):
    def test_flags_important_unpublished_and_pending(self):
        staged = [
            {'url': 'https://example.org/1', 'title': 'Missile attack reported'},
            {'url': 'https://example.org/2', 'title': 'Routine local update'},
            {'url': 'https://example.org/3', 'title': 'Routine sports report'},
        ]
        published = [{'url': 'https://example.org/2'}]
        pending = [{'article': {'url': 'https://example.org/1'}}]
        report = build(staged, published, pending)
        self.assertEqual(report['collected_unique_urls'], 3)
        self.assertEqual(report['counts']['published'], 1)
        self.assertEqual(report['counts']['pending'], 1)
        self.assertEqual(report['counts']['important_unpublished'], 1)
        self.assertEqual(report['unpublished'][0]['url'], 'https://example.org/1')

    def test_duplicate_collection_urls_are_counted_once(self):
        staged = [{'url': 'https://example.org/1', 'title': 'Routine'},
                  {'url': 'https://example.org/1', 'title': 'Routine'}]
        report = build(staged, [], [])
        self.assertEqual(report['collected_unique_urls'], 1)
        self.assertEqual(report['counts']['not_in_current_queue'], 1)


if __name__ == '__main__':
    unittest.main()
