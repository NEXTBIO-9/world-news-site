# NEXT BIO 2.5 한국어 뉴스 제목 번역

기반: NEXT BIO 2.4 Optimized. 기존 지도 자동 순회/히트맵/높이 수정/15분 뉴스 수집 유지.

## 핵심
- 수집기에서 Google Cloud Translation API (Basic v2)로 영어 제목을 한국어 번역해 `title_ko` 저장.
- 한영 버튼: 한국어 모드는 번역 제목 우선, 영어 모드는 원문 제목 우선.
- 번역 실패/미설정 시 원문 표시. 한국어 원문 제목은 그대로 유지.
- 이전 기사 번역 결과를 `data/articles.json`에서 재사용, 매 실행 새 번역 최대 80건.
- Google Cloud Translation API는 유료 사용량이 발생할 수 있음.

## 설정 (번역 활성화에 필수)
1. Google Cloud 프로젝트에서 Cloud Translation API를 활성화하고 결제 설정을 확인.
2. 해당 API에 접근 가능한 API 키를 발급하고 API 제한 설정을 적용.
3. GitHub 저장소 Settings > Secrets and variables > Actions > New repository secret
   Name: GOOGLE_TRANSLATE_API_KEY
   Secret: 발급한 키
4. GitHub Actions > Update news feed > Run workflow를 실행하거나 다음 15분 예약 실행을 기다림.
5. 데이터에 `title_ko`가 추가된 뒤 Pages 배포 완료 시 사이트에서 확인.

API 키를 GitHub 코드나 HTML에 절대 직접 입력하지 마세요.
번역되지 않은 기사는 영어 원문으로 표시되며, 전체 과거 기사 일괄 번역은 보장하지 않습니다.
기사 본문/요약은 번역하지 않습니다.

## 배포
ZIP 압축을 해제하여 저장소에 폴더 구조 그대로 업로드.
기존 data/articles.json은 ZIP에 포함되지 않으므로 보존됩니다.
실제 Google API 호출과 브라우저 배포는 검증하지 않았습니다.
