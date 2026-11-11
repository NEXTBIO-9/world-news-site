#!/usr/bin/env python3
"""Regression tests for retry windows without network or translation dependencies."""
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import summary_work_gate as gate


class ExtractionGateTests(unittest.TestCase):
    def run_gate(self, article, failure_age):
        with patch.object(gate, 'load', side_effect=[
            {'summaries': {}, 'failed_urls': {'https://example.org/a': time.time() - failure_age}},
            {'articles': [article]},
        ]):
            with patch.object(gate, 'emit') as emit:
                with patch.object(sys, 'argv', ['summary_work_gate.py', 'extract']):
                    gate.main()
                return emit.call_args.args[0]

    def test_important_retry_after_half_hour(self):
        a = {'url': 'https://example.org/a', 'title': 'Major earthquake strikes coast'}
        self.assertFalse(self.run_gate(a, 10 * 60))
        self.assertTrue(self.run_gate(a, 40 * 60))

    def test_routine_retry_after_three_hours(self):
        a = {'url': 'https://example.org/a', 'title': 'Local museum opens exhibition'}
        self.assertFalse(self.run_gate(a, 40 * 60))
        self.assertTrue(self.run_gate(a, 4 * 3600))

    def test_title_gate_module_import(self):
        from scripts.translate_news_titles import pending
        self.assertEqual(pending({'articles': []}, {}), [])


if __name__ == '__main__':
    unittest.main()
