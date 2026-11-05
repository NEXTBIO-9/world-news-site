# WORLD NEWS — 무료 뉴스 사이트 시제품

SBH News에서 영감을 받은 독립형 뉴스 포털 시제품입니다. 원본 로고·기사 본문·브랜드 자산을 복제하지 않습니다.

## 기능
- 반응형 뉴스 홈페이지
- 주요 뉴스 3건 및 최신 기사 목록
- 카테고리 필터
- Google News 공개 RSS 기반 헤드라인 수집
- GitHub Actions로 매시간 데이터 갱신
- GitHub Pages 무료 배포 가능

## 무료 배포 순서

1. GitHub 계정으로 로그인하고 새 **Public repository**를 만듭니다. 예: `world-news-site`
2. 이 ZIP의 파일을 모두 저장소 최상위에 업로드합니다. `.github/workflows/update-news.yml` 경로도 유지해야 합니다.
3. 저장소의 **Settings → Actions → General → Workflow permissions**에서 `Read and write permissions`를 선택하고 저장합니다.
4. **Actions → Update news feed → Run workflow**를 눌러 첫 뉴스 수집을 실행합니다.
5. 저장소의 **Settings → Pages**에서 `Deploy from a branch`를 선택하고 `main` / `/(root)`로 저장합니다.
6. Pages가 제공하는 주소로 접속합니다. 보통 `https://사용자명.github.io/world-news-site/` 형태입니다.

## 주의사항
- 자동 수집은 공개 RSS의 제목·요약·원문 링크를 표시하는 방식입니다. 원문 전문이나 이미지를 무단 복제하지 마세요.
- Google News RSS는 제공 정책·응답 형식·접근 가능 여부가 바뀔 수 있으며 수집 실패가 발생할 수 있습니다.
- 첫 배포 후 `data/articles.json` 파일이 생성됐는지 확인하세요. 수집이 실패하면 Actions 로그를 확인하세요.
- 매시간 자동 갱신은 GitHub Actions의 스케줄 실행에 의존합니다. GitHub 정책상 예약 실행이 지연될 수 있습니다.
- 광고·회원가입·댓글·검색·관리자 로그인은 아직 포함되지 않은 초기 버전입니다.
- 상업적 언론사 운영 전에는 각 원천 피드의 이용약관, 저작권, 개인정보 및 정정·삭제 요청 절차를 검토해야 합니다.
