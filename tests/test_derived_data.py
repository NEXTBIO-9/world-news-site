import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_daily_briefing import build as briefing
from build_topic_monitor import build as monitor
from validate_news_data import validate


class DerivedDataTests(unittest.TestCase):
    def test_topic_monitor_counts_only_matching_titles(self):
        items = [{'title': 'Major earthquake hits coast', 'url': 'https://a.example/1',
                  'published': '2026-11-11T00:00:00+00:00', 'countries': ['일본']},
                 {'title': 'Museum announces new exhibit', 'url': 'https://a.example/2'}]
        result = monitor(items)
        self.assertEqual(result['topics']['disaster']['article_count'], 1)
        self.assertEqual(result['topics']['conflict']['article_count'], 0)

    def test_briefing_excludes_stale_duplicate_and_future(self):
        now = datetime(2026, 11, 11, 12, tzinfo=timezone.utc)
        items = [{'title': 'Recent', 'url': 'https://a.example/1',
                  'published': '2026-11-11T09:00:00+00:00'},
                 {'title': 'Duplicate', 'url': 'https://a.example/1',
                  'published': '2026-11-11T08:00:00+00:00'},
                 {'title': 'Old', 'url': 'https://a.example/2',
                  'published': '2026-11-09T08:00:00+00:00'}]
        self.assertEqual(briefing(items, now)['article_count'], 1)

    def test_validator_detects_broken_event_link(self):
        feed = {'articles': [{'url': 'https://a.example/1'}]}
        events = {'events': [{'id': 'one', 'related_events': [{'id': 'missing'}]}]}
        self.assertIn('Broken cross-country event link',
                      validate(feed, events, {'topics': {}}, {'headlines': []}))


if __name__ == '__main__':
    unittest.main()
