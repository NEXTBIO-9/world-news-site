"""Regression checks for the selective 70-point publication policy."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from fetch_news import MIN_QUALITY_SCORE, quality_score, selection_score
from publish_translated_news import eligible

NOW = datetime.now(timezone.utc).isoformat()

class ImportantNewsThresholdTests(unittest.TestCase):
    def article(self, title, category="경제·금융"):
        return {"title": title, "category": category, "source": "Reuters",
                "published": NOW, "url": "https://example.com/story"}

    def test_threshold_is_seventy(self):
        self.assertEqual(MIN_QUALITY_SCORE, 70)

    def test_routine_news_is_not_eligible(self):
        self.assertFalse(eligible(self.article("Local museum announces weekend visitor programme", "일반")))

    def test_important_story_is_eligible(self):
        a = self.article("Central bank announces interest rate cut after inflation surge")
        self.assertGreaterEqual(quality_score(a), 70)
        self.assertGreaterEqual(selection_score(a), 70)
        self.assertTrue(eligible(a))

    def test_protected_keywords_cannot_bypass_low_base_score(self):
        a = self.article("Earthquake reported in a short daily roundup", "일반")
        self.assertFalse(eligible(a))

    def test_malformed_article_rejected(self):
        self.assertFalse(eligible(None))
        self.assertFalse(eligible({}))

if __name__ == "__main__":
    unittest.main()
