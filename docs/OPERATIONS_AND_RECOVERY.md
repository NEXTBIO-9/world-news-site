# NEXT BIO 운영·복구 점검표

이 문서는 사이트 UI를 변경하지 않고 뉴스 수집, 번역, 게시 파이프라인을 운영하기 위한 절차입니다.

## 실행 순서
1. **Update news feed**가 공개 RSS를 수집하고 `nextbio-unpublished-news` 아티팩트를 생성합니다.
2. **Build and translate source-grounded summaries v20**가 수집 결과를 읽어 제목 번역, 본문 추출, 한국어 요약을 수행합니다.
3. 한국어 제목과 출처 기반 한국어 요약이 준비된 기사만 게시합니다.
4. 사건·통계·감사 데이터를 생성하고 검증한 후 main 브랜치에 게시합니다.

## 누락 조사
- `data/news_quality_audit.json`: 수집원 성공률, 수집 제외 이유, 중요 기사 제외 후보
- `data/collection-publication-audit.json`: 이번 수집분 중 게시되지 않은 중요 기사
- `data/publication-gaps.json`: 현재 번역·요약 대기 목록 및 재시도 압력
- `data/pipeline-health.json`: 데이터 파일 누락, JSON 오류, 일부 파일의 오래된 갱신 시각
- `data/cross-source-coverage.json`: 사건별 서로 다른 발행 도메인 수. 독립적인 사실 확인은 아님

수집되지 않은 외부 기사는 위 파일만으로 식별할 수 없습니다. 외부 수집원과 직접 비교해야 합니다.

## 복구
1. 해당 번역·게시 실행의 GitHub Actions 아티팩트 `nextbio-recovery-<run-id>`를 다운로드합니다.
2. `python scripts/verify_recovery_snapshot.py nextbio-recovery.tar.gz nextbio-recovery-manifest.json`을 실행합니다.
3. `python scripts/restore_recovery_snapshot.py nextbio-recovery.tar.gz nextbio-recovery-manifest.json /tmp/nextbio-reviewed-restore`로 **새 폴더에만** 추출합니다.
4. 복구 대상 데이터, 현재 브랜치 및 게시 시각을 검토한 후 별도로 수동 배포합니다.

자동으로 운영 파일을 덮어쓰지 않습니다. 백업 보존 기간은 30일이며 GitHub Actions 보존 정책에 따릅니다.

## 남은 외부 의존성
- WHO·CDC·질병관리청 통계는 원문 데이터의 정의·발표일·단위·수정 이력을 검증한 후에만 수치로 게시할 수 있습니다.
- ClinicalTrials.gov 등의 임상시험 등록정보는 식별자, 상태 변경일, 출처를 검증한 별도 수집기가 필요합니다.
- 군사 이동·해상 봉쇄는 기사 키워드만으로 실제 발생 여부나 좌표를 판단할 수 없습니다.
- 시장 가격은 라이선스와 지연 시간, 거래소 시간대가 명시된 공식 공급자가 필요합니다.
- 번역에 한글이 있다는 사실만으로 의미 정확도를 증명할 수 없습니다.

## 장애 대응
수집 단계가 실패하면 직전 공개 데이터는 유지하고, 실패한 실행 로그와 감사 데이터를 먼저 확인합니다. 번역·게시 단계가 실패하면 제목/요약 캐시와 대기 목록을 확인한 뒤 수동 재실행을 검토합니다. 실패한 실행이 성공한 것으로 보이도록 데이터 파일을 임의로 수정하지 않습니다.
