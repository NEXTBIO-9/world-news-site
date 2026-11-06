NEXT BIO 2.3 지도 빈 공간 수정 V2

원인: 오른쪽 뉴스 패널의 콘텐츠가 많아 패널/그리드 높이가 커지는 문제.
해결: 지도 왼쪽 열의 실제 높이를 ResizeObserver로 측정해 오른쪽 패널 높이를 동기화하고,
뉴스 목록은 오른쪽 패널 안에서만 스크롤되도록 설정.

권장 적용(기존 2.3 미니멀 지도 설치 기준):
1) index.html
2) nextbio-command-center.css
3) nextbio-map-layout-fix.js
위 3개 파일만 교체/추가하세요.

다른 app.js, nextbio-extras.js, styles.css, GitHub Actions는 수정하지 않습니다.
배포 성공 후 Ctrl+F5, 국가 자동 순회 및 뉴스 패널 스크롤 확인.
실제 브라우저에서 검증한 것은 아니므로 백업 후 적용하세요.
