# NEXT BIO 무료 AI 제목 번역 실험판

## 주의
- 이 패치는 **미검증 실험판**입니다. Python 문법/YAML 구조 검사는 했지만 실제 NLLB 모델 다운로드, GitHub Actions 실행 및 번역 품질은 검증하지 못했습니다.
- 모델 `facebook/nllb-200-distilled-600M`은 **CC BY-NC 4.0 (비상업적 사용 제한)** 조건이므로, NEXT BIO가 상업적 서비스이거나 광고/수익을 내는 경우 **적용하지 마세요**. 사용 조건을 직접 확인하세요.
- 유료 번역 API는 사용하지 않습니다. 다만 GitHub Actions 저장소/계정의 무료 실행 시간과 저장 공간 한도가 적용될 수 있습니다.
- 모델은 첫 실행 시 대용량 다운로드가 필요하며 CPU에서는 30분을 초과할 수 있습니다. 성공을 보장하지 않습니다.

## 변경 파일 4개
1. `.github/workflows/update-news.yml`: 15분 뉴스 수집 작업에서 느린 Argos 번역 단계를 제거합니다.
2. `.github/workflows/translate-news.yml`: **별도** 무료 AI 번역 워크플로. 6시간마다 30개까지, 수동 실행도 가능.
3. `translate_titles_ai.py`: NLLB 영어→한국어 번역 및 숫자/영문 혼합 품질 검사.
4. `scripts/fetch_news.py`: 뉴스 수집 후에도 이미 생성한 AI 번역을 유지합니다. 기존 수집 규칙은 변경하지 않았습니다.

위 4개 파일을 GitHub 저장소의 **정확한 경로**에 업로드/교체하세요. 기존 `app.js`, `index.html`, 북마크, 지도 관련 파일은 변경하지 않습니다. 기존 `translate_titles.py`는 사용하지 않습니다.

## 실행
1. GitHub Actions에서 **Translate news headlines (free AI)** 선택 → Run workflow.
2. `Translate new titles using NLLB` 로그에서 처리 결과 확인.
3. `Report translated titles`에서 `Korean titles: .../...` 확인.
4. 사이트 번역 ON 상태에서 한국어 제목 확인.

## 품질/성능 주의
- 기존 Argos 제목은 신뢰하지 않아 AI 번역으로 교체하기 전까지 영어 원문으로 표시될 수 있습니다.
- 모델은 자연스러운 문장 생성에 유리할 가능성이 있지만, **실측 비교 전이므로 Argos보다 우수하다고 보장하지 않습니다**.
- 번역된 결과가 수치/형식 검사를 통과해도 의미상 오역이 남을 수 있습니다.
- 뉴스 갱신은 별도 작업이므로 번역 실패해도 뉴스 업데이트가 막히지 않도록 구성했습니다.
- 번역 결과는 URL과 원문 제목이 동일할 때만 유지합니다.
