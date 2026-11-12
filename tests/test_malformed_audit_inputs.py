"""Defensive checks for malformed audit inputs."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_cross_source_coverage import build
from build_collection_publication_audit import build as collection_build


class MalformedAuditTests(unittest.TestCase):
    def test_invalid_event_timeline_is_ignored(self):
        result = build([{'id': 'x', 'timeline': 'not a list'}])
        self.assertEqual(result['events'][0]['distinct_publisher_domains'], 0)

    def test_invalid_event_url_is_ignored(self):
        result = build([{'id': 'x', 'timeline': [{'url': ['not', 'a', 'url']}]}])
        self.assertEqual(result['events'][0]['distinct_publisher_domains'], 0)

    def test_malformed_queue_and_urls_are_ignored(self):
        staged = [{'url': ['invalid'], 'title': 'Broken'}, {'url': 'https://example.com/a', 'title': 'Report'}]
        result = collection_build(staged, [], {'not': 'a list'})
        self.assertEqual(result['collected_unique_urls'], 1)
        self.assertEqual(result['counts']['not_in_current_queue'], 1)


if __name__ == '__main__':
    unittest.main()
