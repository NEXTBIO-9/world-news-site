"""News publication must not show the same source URL twice."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from publish_translated_news import unique_by_url


class PublicationUrlDeduplicationTests(unittest.TestCase):
    def test_same_url_different_titles_only_keeps_first(self):
        items = [
            {'url': 'https://example.com/a', 'title': 'Latest'},
            {'url': 'https://example.com/a', 'title': 'Older'},
            {'url': 'https://example.com/b', 'title': 'Other'},
        ]
        self.assertEqual(unique_by_url(items), [items[0], items[2]])

    def test_invalid_urls_are_skipped_and_limit_applies(self):
        items = [{'url': None}, {'url': ['invalid']},
                 {'url': 'https://example.com/a'}, {'url': 'https://example.com/b'}]
        self.assertEqual(unique_by_url(items, limit=1), [items[2]])


if __name__ == '__main__':
    unittest.main()
