import unittest
from scripts.osint.verify_sources import publisher, source_comparison, annotate

class VerificationTests(unittest.TestCase):
    def test_aliases(self):
        self.assertEqual(publisher({"source":"Reuters","url":"https://news.google.com/rss/abc"}),"reuters")
    def test_same_publisher_not_independent(self):
        items=[{"title":"North Korea launches ballistic missile near coast","source":"Reuters","url":"https://a.org/1"},
               {"title":"North Korea launches ballistic missile near coast","source":"Reuters.com","url":"https://b.org/2"}]
        self.assertEqual(source_comparison(items),[])
    def test_distinct_publishers_candidate_only(self):
        items=[{"title":"North Korea launches ballistic missile near coast","source":"Reuters","url":"https://a.org/1"},
               {"title":"North Korea launches ballistic missile near coast","source":"AP News","url":"https://b.org/2"}]
        pairs=source_comparison(items)
        self.assertEqual(len(pairs),1)
        self.assertIn("미확인",pairs[0]["status"])
        self.assertFalse(any(x["corroborated"] for x in annotate(items)))
    def test_unrelated(self):
        items=[{"title":"North Korea launches ballistic missile near coast","source":"Reuters"},
               {"title":"Japan economic report new trade policy","source":"AP News"}]
        self.assertEqual(source_comparison(items),[])
if __name__=="__main__":unittest.main()
