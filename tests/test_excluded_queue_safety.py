"""Malformed exclusion and translation attempt metadata must not stop publishing."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from publish_translated_news import excluded_keys


class ExclusionSafetyTests(unittest.TestCase):
    def test_invalid_entries_are_ignored(self):
        queue = {'excluded': [['https://example.com/a', 'Valid'],
                              [['unhashable'], 'Bad'], ['missing'], None,
                              ['https://example.com/b', {'bad': True}]]}
        self.assertEqual(excluded_keys(queue), {('https://example.com/a', 'Valid')})

    def test_non_list_exclusions_are_safe(self):
        self.assertEqual(excluded_keys({'excluded': {'unexpected': 1}}), set())


if __name__ == '__main__':
    unittest.main()
