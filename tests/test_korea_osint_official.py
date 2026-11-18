import unittest
from scripts.osint.collect_official import parse, merge_items

class OfficialFeedTests(unittest.TestCase):
    def test_only_korea_security_items(self):
        rss=b"""<rss><channel>
        <item><title>US and South Korea military exercise</title><link>https://example.org/1</link></item>
        <item><title>Football tournament</title><link>https://example.org/2</link></item>
        </channel></rss>"""
        result=parse(rss,"Official test")
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["source"],"Official test")
        self.assertIn("별도 검증",result[0]["verification"])
    def test_bad_cached_list_does_not_crash(self):
        self.assertEqual(merge_items({"items": None}, [{"url":"https://example.org/new"}]), [{"url":"https://example.org/new"}])
    def test_bad_cached_url_is_excluded(self):
        self.assertEqual(merge_items({"items":[{"url":"http://example.org/old"}]}, []), [])
    def test_reject_insecure_link(self):
        rss=b"<rss><channel><item><title>North Korea missile</title><link>http://example.org/1</link></item></channel></rss>"
        self.assertEqual(parse(rss,"Official test"),[])
if __name__=="__main__":unittest.main()
