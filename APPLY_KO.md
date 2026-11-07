# NEXT BIO 무료 번역 작동 점검 패치

확인된 원인: 업로드된 원본 data/articles.json 기사 856개 중 title_ko가 있는 기사는 0개였습니다. 버튼만으로는 번역이 생성되지 않습니다.

## 적용
1. ZIP의 `.github/workflows/update-news.yml` 및 `translate_titles.py` 두 파일을 저장소 동일 경로에 업로드합니다. 기존 `app.js`, `index.html`, `nextbio-extras.js`는 건드리지 마세요.
2. GitHub → Actions → Update news feed → Run workflow를 실행합니다.
3. 실행 로그에서 `Translate English headlines locally`와 `Report translated headlines` 단계를 확인합니다. `Korean titles: N/전체`에서 N이 1 이상이어야 실제 번역 데이터가 생성된 것입니다.
4. GitHub의 `data/articles.json`에서 `title_ko`를 검색하고, 사이트를 강력 새로고침합니다.
5. 번역된 제목이 있어도 버튼으로 전환되지 않으면 `nextbio-translation.js` 로딩 및 브라우저 콘솔 오류를 확인해야 합니다.

## 제한
- 1회 최대 100개 처리; 여러 번 실행하면 누적될 수 있습니다.
- 번역 모델 다운로드 실패, 번역 품질 검사 탈락, Actions 실패 시 번역 수가 0일 수 있습니다.
- 무료 오프라인 Argos 모델이므로 ChatGPT 수준의 번역 품질은 보장할 수 없습니다.
- 이 패치는 실제 GitHub Actions 실행 결과를 검증한 것은 아닙니다.
