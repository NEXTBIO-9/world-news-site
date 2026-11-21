"""Delete one published manual article, only for owner-authored delete issues."""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

title = os.environ["REQUEST_TITLE"].strip()
body = os.environ.get("REQUEST_BODY", "")
match = re.fullmatch(r"\[(?:DELETE-MANUAL|자체기사삭제)\] #(\d+)", title)
if not match:
    print("Not a manual deletion request; skipping.")
    raise SystemExit(0)
number = int(match.group(1))
if number < 1 or not re.search(r"(?m)^삭제할 기사 번호:\s*" + str(number) + r"\s*$", body):
    raise ValueError("Delete request body does not match issue number")

path = Path("data/manual-articles.json")
data = json.loads(path.read_text(encoding="utf-8"))
articles = data.get("articles")
if not isinstance(articles, list):
    raise ValueError("Invalid manual article data")
remaining = [a for a in articles if not (isinstance(a, dict) and a.get("manual") is True and a.get("manual_issue") == number)]
if len(remaining) != len(articles) - 1:
    raise ValueError("Expected exactly one published article with that issue number")
data["articles"] = remaining
data["updated"] = datetime.now(timezone.utc).isoformat()
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
