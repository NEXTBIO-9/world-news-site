#!/usr/bin/env python3
"""Regression tests for high-impact news ordering."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from news_priority import important, ordered


class NewsPriorityTests(unittest.TestCase):
    def test_important_events(self):
        for title in (
            'Strong earthquake injures dozens in Japan',
            'FDA approves new drug for rare disease',
            'Central bank announces interest rate decision',
            '대형 지진 발생으로 주민 대피',
        ):
            with self.subTest(title=title):
                self.assertTrue(important({'title': title}))

    def test_routine_not_promoted(self):
        self.assertFalse(important({'title': 'Local museum opens a new exhibition'}))

    def test_unconfirmed_not_promoted(self):
        self.assertFalse(important({'title': 'Unconfirmed missile report circulates online'}))

    def test_priority_order_is_stable(self):
        items = [
            {'title': 'Local museum opens'},
            {'title': 'Major earthquake hits coast'},
            {'title': 'New restaurant opens'},
            {'title': 'FDA approves drug'},
        ]
        self.assertEqual(
            [x['title'] for x in ordered(items)],
            ['Major earthquake hits coast', 'FDA approves drug',
             'Local museum opens', 'New restaurant opens']
        )


if __name__ == '__main__':
    unittest.main()
