"""Static frontend contract checks; not a substitute for a browser E2E test."""
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class IdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.scripts = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "script" and "src" in attrs:
            self.scripts.append(attrs["src"])

class OSINTPageTests(unittest.TestCase):
    def test_frontend_elements_exist_once(self):
        page = IdParser()
        page.feed((ROOT / "korea-osint.html").read_text(encoding="utf-8"))
        js = (ROOT / "korea-osint.js").read_text(encoding="utf-8")
        requested = set(re.findall(r'getElementById\("([^"]+)"\)', js))
        self.assertTrue(requested)
        for name in requested:
            self.assertEqual(page.ids.count(name), 1, name)
        self.assertEqual(len(page.ids), len(set(page.ids)))
    def test_script_and_data_paths(self):
        page = IdParser()
        page.feed((ROOT / "korea-osint.html").read_text(encoding="utf-8"))
        for script in page.scripts:
            self.assertTrue((ROOT / script.split("?")[0]).is_file())
        js = (ROOT / "korea-osint.js").read_text(encoding="utf-8")
        for name in ("events", "official", "reports"):
            self.assertIn(f"./data/osint/{name}.json", js)
            data = json.loads((ROOT / "data" / "osint" / f"{name}.json").read_text(encoding="utf-8"))
            self.assertIsInstance(data, dict)

if __name__ == "__main__":
    unittest.main()
