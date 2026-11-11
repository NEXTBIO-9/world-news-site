#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_event_timelines import build, compatible


def article(title, url, category='분쟁·군사', country='우크라이나'):
    return {'title': title, 'url': url, 'source': url, 'published': '2026-11-11T01:00:00+00:00',
            'category': category, 'countries': [country]}


class EventTimelineTests(unittest.TestCase):
    def test_related_reports_group(self):
        a = article('Ukraine missile attack damages major city power infrastructure', 'https://one.example/1')
        b = article('Ukraine missile attack damages major city power infrastructure again', 'https://two.example/2')
        result = build([a, b])
        self.assertEqual(result['event_count'], 1)
        self.assertEqual(result['events'][0]['distinct_sources'], 2)
        self.assertEqual(result['events'][0]['verification'], 'not_independently_verified')

    def test_distinct_country_or_category_not_merged(self):
        a = article('Ukraine missile attack damages major city power infrastructure', 'https://one.example/1')
        b = article('Ukraine missile attack damages major city power infrastructure', 'https://two.example/2', country='일본')
        self.assertFalse(compatible(a, b))
        self.assertEqual(build([a, b])['event_count'], 0)

    def test_single_article_not_a_corrobated_event(self):
        self.assertEqual(build([article('Ukraine missile attack damages major city power infrastructure', 'https://one.example/1')])['event_count'], 0)


if __name__ == '__main__':
    unittest.main()
