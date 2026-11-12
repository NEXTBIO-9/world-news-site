"""Health warnings should expose backlog pressure without blocking publication."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_pipeline_health as health


class PipelineHealthTests(unittest.TestCase):
    def test_important_unpublished_and_retry_pressure(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            (data / 'articles.json').write_text(json.dumps({
                'updated': '2099-01-01T00:00:00+00:00',
                'articles': [{'url': 'https://example.com/1'}]}), encoding='utf-8')
            (data / 'publication-gaps.json').write_text(
                json.dumps({'pending_at_retry_limit': 3}), encoding='utf-8')
            (data / 'collection-publication-audit.json').write_text(
                json.dumps({'counts': {'important_unpublished': 2}}), encoding='utf-8')
            with patch.object(health, 'DATA', data):
                result = health.build()
            reasons = {w['reason'] for w in result['warnings']}
            self.assertIn('translation_retry_pressure', reasons)
            self.assertIn('important_collected_articles_unpublished', reasons)

    def test_duplicate_urls_warning(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            (data / 'articles.json').write_text(json.dumps({
                'articles': [{'url': 'https://example.com/1'},
                             {'url': 'https://example.com/1'}]}), encoding='utf-8')
            with patch.object(health, 'DATA', data):
                result = health.build()
            self.assertIn('duplicate_published_urls',
                          {w['reason'] for w in result['warnings']})


if __name__ == '__main__':
    unittest.main()
