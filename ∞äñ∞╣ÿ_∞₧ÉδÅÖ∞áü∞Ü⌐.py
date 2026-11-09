#!/usr/bin/env python3
"""Run in the extracted ZIP folder: python 설치_자동적용.py /path/to/world-news-site"""
from pathlib import Path
import shutil
import sys

source = Path(__file__).resolve().parent
if len(sys.argv) != 2:
    raise SystemExit('사용법: python 설치_자동적용.py 세계뉴스사이트폴더경로')
repo = Path(sys.argv[1]).expanduser().resolve()
index = repo / 'index.html'
if not index.is_file() or not (repo / 'data').is_dir():
    raise SystemExit('오류: 사이트 저장소 최상위 폴더를 지정해 주세요.')
html = index.read_text(encoding='utf-8')
script = '<script src="./nextbio-emergency-ticker.js?v=2" defer></script>'
if 'nextbio-emergency-ticker.js' not in html:
    if '</body>' not in html:
        raise SystemExit('오류: index.html에 </body>가 없습니다.')
    html = html.replace('</body>', script + '\n</body>', 1)
    index.write_text(html, encoding='utf-8')
for relative in ['nextbio-emergency-ticker.js', 'scripts/update_emergency_news.py', '.github/workflows/update-emergency-news.yml', 'data/emergency-reviewed.json', 'data/emergency-news.json']:
    destination = repo / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and relative in ['data/emergency-reviewed.json', 'data/emergency-news.json']:
        print('기존 데이터 보존:', relative)
        continue
    shutil.copy2(source / relative, destination)
    print('설치:', relative)
print('완료: GitHub에 변경된 파일을 업로드/커밋하세요.')
