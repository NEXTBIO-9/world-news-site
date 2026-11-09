"""Publish a GitHub issue form submitted by the repository owner."""
import json, os, re
from datetime import datetime, timezone
from pathlib import Path

body = os.environ['ISSUE_BODY']
number = int(os.environ['ISSUE_NUMBER'])
url = os.environ['ISSUE_URL']

def field(name):
    m = re.search(r'(?m)^### ' + re.escape(name) + r'\s*\n(.*?)(?=\n### |\Z)', body, re.S)
    return m.group(1).strip() if m else ''

title = field('기사 제목')
category = field('카테고리')
content = field('기사 본문')
countries = [x.strip() for x in field('관련 국가').split(',') if x.strip() and x.strip() != '_No response_']
image = field('대표 이미지 URL (선택)')
priority = field('중요 뉴스')
if not title or not content or len(title)>300 or len(content)>30000:
    raise ValueError('Invalid title or body')
if image and not image.startswith('https://'):
    image = ''
path = Path('data/manual-articles.json')
path.parent.mkdir(parents=True, exist_ok=True)
try:
    data = json.loads(path.read_text(encoding='utf-8'))
except FileNotFoundError:
    data = {'articles': []}
articles = data.get('articles', [])
old = next((a for a in articles if a.get('manual_issue') == number), None)
article = {
    'manual_issue': number, 'manual': True, 'important': priority == '중요',
    'title': title, 'title_ko': title, 'category': category,
    'summary': content[:240], 'body': content, 'image': image,
    'url': url, 'source': 'NEXT BIO 직접 작성',
    'published': old.get('published') if old else datetime.now(timezone.utc).isoformat(),
    'region': '해외', 'language': 'ko', 'countries': countries
}
articles = [a for a in articles if a.get('manual_issue') != number]
articles.insert(0, article)
path.write_text(json.dumps({'updated': datetime.now(timezone.utc).isoformat(), 'articles': articles}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
