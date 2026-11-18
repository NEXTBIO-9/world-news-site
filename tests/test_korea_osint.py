import unittest
from scripts.osint.filter_korea import classify, collect

class KoreaOSINTTests(unittest.TestCase):
    def test_direct_security(self):
        self.assertEqual(classify({"title":"North Korea launches ballistic missile"}), "A")
    def test_unrelated(self):
        self.assertIsNone(classify({"title":"Spain election debate"}))
    def test_unrelated_security(self):
        self.assertIsNone(classify({"title":"France military drill in Europe"}))
    def test_non_security_korea(self):
        self.assertIsNone(classify({"title":"South Korea pop music awards"}))
    def test_korea_publisher_not_evidence(self):
        self.assertIsNone(classify({"title":"Japan nuclear policy debate", "summary":"The Korea Daily"}))
    def test_korea_only_in_summary_not_sufficient(self):
        self.assertIsNone(classify({"title":"Japan military exercise", "summary":"South Korea mentioned in unrelated summary"}))
    def test_indirect_russia_north_korea_link(self):
        self.assertEqual(classify({"title":"북러 군사협력 확대"}), "B")
    def test_unrelated_japan_military(self):
        self.assertIsNone(classify({"title":"Japan military exercise near Tokyo"}))
    def test_deduplicate(self):
        a={"title":"North Korea missile launch","url":"https://example.com/1","source":"Test"}
        self.assertEqual(len(collect([a,a])),1)
    def test_no_http(self):
        self.assertFalse(collect([{"title":"North Korea missile launch","url":"http://example.com"}]))
if __name__=="__main__": unittest.main()
