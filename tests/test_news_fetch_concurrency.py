"""Fast, network-free checks for the RSS concurrent collection helper."""
import importlib.util
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fetch_news.py"
spec = importlib.util.spec_from_file_location("fetch_news_test_target", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ConcurrentRSSFetchTests(unittest.TestCase):
    def test_preserves_feed_order_and_counts_successful_sources(self):
        feeds = [
            ("일반", None, "slow", "ko", "KR", None),
            ("경제", None, "fast", "en", "US", None),
            ("의료", None, "fail", "en", "US", None),
        ]

        def fetcher(category, subcategory, query, language, region, hint):
            if query == "slow":
                time.sleep(0.06)
            if query == "fail":
                raise ValueError("synthetic failure")
            return [{"title": query, "category": category}]

        candidates, count = module.collect_feeds(feeds, workers=3, fetcher=fetcher)
        self.assertEqual(count, 2)
        self.assertEqual([x["title"] for x in candidates], ["slow", "fast"])

    def test_empty_feed_is_not_counted_as_failure(self):
        one = [("일반", None, "empty", "ko", "KR", None)]
        items, succeeded = module.collect_feeds(one, workers=1, fetcher=lambda *args: [])
        self.assertEqual(items, [])
        self.assertEqual(succeeded, 1)


if __name__ == "__main__":
    unittest.main()
