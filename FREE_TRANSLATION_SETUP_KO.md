# NEXT BIO 무료 제목 번역 적용

유료 API 및 OPENAI_API_KEY가 필요 없습니다. Argos Translate 오픈소스 모델을 GitHub Actions 실행 환경에 설치해 로컬에서 번역합니다.

## 적용
1. 이 ZIP의 파일을 GitHub 저장소의 같은 경로에 업로드/교체하세요. `.github/workflows/update-news.yml` 경로를 정확히 유지하세요.
2. GitHub Actions > Update news feed > Run workflow를 실행하세요.
3. 번역 완료 후 사이트를 새로고침하고 `뉴스 제목 한국어 번역` 버튼으로 전환하세요.

## 주의
- 기존 원문 제목은 유지됩니다. 번역이 실패하거나 품질 검사에 걸리면 원문을 표시합니다.
- 한 번 실행할 때 신규 최대 60개를 번역합니다. 기존 기사 전체 번역은 여러 번 실행해야 할 수 있습니다.
- Argos 모델 다운로드와 번역에 시간이 소요됩니다. 무료 모델의 자연스러움은 ChatGPT 수준을 보장하지 않습니다.
- GitHub Actions 사용 가능 여부와 실행 한도는 저장소 공개 여부 및 계정 정책에 따릅니다. 유료 API 호출은 하지 않습니다.
- `index.html`, `app.js`, `nextbio-extras.js`는 제공된 최신 저장소에 번역 표시 기능을 최소 추가한 버전입니다. 이후 직접 수정한 파일이 있다면 차이를 확인 후 적용하세요.
