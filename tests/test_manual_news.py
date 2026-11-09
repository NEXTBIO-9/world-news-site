import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "publish_manual_news.py"

class ManualNewsTests(unittest.TestCase):
    def test_publish_and_edit_preserves_date(self):
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, ISSUE_NUMBER="42", ISSUE_URL="https://github.com/NEXTBIO-9/world-news-site/issues/42")
            def publish(title):
                env["ISSUE_BODY"] = f"""### 기사 제목

{title}

### 카테고리

세계

### 관련 국가

대한민국, 미국

### 기사 본문

첫째 줄
둘째 줄

### 대표 이미지 URL (선택)

_No response_

### 중요 뉴스

중요
"""
                subprocess.run([sys.executable, str(SCRIPT)], cwd=directory, env=env, check=True)
                return json.loads((Path(directory)/"data/manual-articles.json").read_text(encoding="utf-8"))["articles"]
            first=publish("테스트 기사")
            self.assertEqual(len(first),1)
            self.assertEqual(first[0]["url"],"./article.html?id=42")
            self.assertTrue(first[0]["important"])
            self.assertEqual(first[0]["countries"],["대한민국","미국"])
            second=publish("수정 기사")
            self.assertEqual(len(second),1)
            self.assertEqual(second[0]["title"],"수정 기사")
            self.assertEqual(second[0]["published"],first[0]["published"])

    def test_missing_body_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            env=dict(os.environ, ISSUE_NUMBER="5", ISSUE_URL="https://github.com/example/issues/5", ISSUE_BODY="### 기사 제목\n\n제목\n\n### 기사 본문\n\n")
            r=subprocess.run([sys.executable,str(SCRIPT)],cwd=directory,env=env,capture_output=True)
            self.assertNotEqual(r.returncode,0)
            self.assertFalse((Path(directory)/"data/manual-articles.json").exists())

if __name__=="__main__":
    unittest.main()
