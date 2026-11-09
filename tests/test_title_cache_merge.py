"""Guard against spurious cache commits and lost headline translations."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "merge_title_cache.py"


class TitleCacheMergeTests(unittest.TestCase):
    def test_no_change_preserves_file_bytes_and_mtime(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "remote.json"
            incoming = Path(td) / "new.json"
            data = {"updated": "2026-01-01T00:00:00Z", "translations": {"English headline": "한국어 제목"}}
            target.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            incoming.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            original = target.read_bytes()
            original_mtime = target.stat().st_mtime_ns
            subprocess.run([sys.executable, str(SCRIPT), str(target), str(incoming)], check=True)
            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(target.stat().st_mtime_ns, original_mtime)

    def test_new_translations_are_added_without_losing_previous(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "remote.json"
            incoming = Path(td) / "new.json"
            target.write_text(json.dumps({"translations": {"old": "기존"}}, ensure_ascii=False), encoding="utf-8")
            incoming.write_text(json.dumps({"translations": {"new": "새로운", "invalid": ""}}, ensure_ascii=False), encoding="utf-8")
            subprocess.run([sys.executable, str(SCRIPT), str(target), str(incoming)], check=True)
            result = json.loads(target.read_text(encoding="utf-8"))["translations"]
            self.assertEqual(result, {"old": "기존", "new": "새로운"})

if __name__ == "__main__":
    unittest.main()
