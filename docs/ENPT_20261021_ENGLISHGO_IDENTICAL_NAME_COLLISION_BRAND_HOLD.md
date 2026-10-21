# 브랜드명 변경 검토 게이트 — 2026-10-21

## 현재 판정
- 후보: 잉글리시GO / ENGLISH GO
- **정확한 한글 이름이 이미 국내 영어교육 서비스에서 사용됨**.
- 아이스크림에듀 '리틀홈런' 잉글리시GO 공식 페이지: https://www.home-learn.co.kr/homelearn/intro107/english-go.html
- 2024-03-15 아이스크림 홈런 소개: https://m.home-learn.com/board/BoardView.do?bbsConfigUid=37&bbsDataUid=5699&cmsDirUid=49&cmsLocalUid=0&currentPage=1&searchField=ALL&searchLowItem=ALL&searchValue=&siteUid=1
- 법률상 상표권 침해 여부를 단정하지 않음. 그러나 업종 중복/브랜드 혼동 위험으로 공개 배포 **HOLD**.

## 기술 구현 상태
- 기존 QA 브랜치의 ENPT_20261021_BRAND_ENGLISHGO_ALL_PAYLOADS_STAGING.py 는 158,571개 Edge HTML 포함 텍스트 교체 패치를 보유함.
- 2026-10-21 GitHub Actions run 39558464964: 브랜드 교체 및 SEO/form/robots/URL 안전 검사 PASS, 1회 Netlify CLI Draft upload TIMEOUT(exit 124).
- 이 기록만으로 Ready 상태의 비게시 Draft가 생성됐다고 판단하지 않음.
- 현재 마지막 확인된 Production deploy: 6ad7506cdeb778280a54ee2a.
- 기존 정상 동선 Draft: 6ad84addd983624c4c5b2e8d / https://enptfourpathsfix2review20261021--englishpt-seo.netlify.app
- 안전 게이트 통과 전: 새 명칭 Production 게시/브랜드 메타 전환/사이트맵 변경/도메인 리디렉션 금지.

## 공개 전 최소 승인조건
1. KIPRIS 상표 유사도 조사(41류 교육서비스)와 상호명 검토; 제3자의 동명 사용에 따른 상표 분쟁 가능성 해소.
2. 고유성이 높은 명칭이 필요한 경우 새로운 후보 선정 및 재검색.
3. 브랜드명 확정 후 전체 158,571개 생성 페이지/허브/OG/JSON-LD/앱/UI/상담 알림 메타 변경 전체 QA.
4. 새 비게시 Draft 실제 HTTP, 390/768/1440px 화면, 6종 학생과정 이동, 국제학교/시니어, form GET-only 동선 QA.
5. 현재 콘텐츠 중복 및 주소 HOLD 항목 분리 보고 후 범위별 Production GO/HOLD 의사결정.
6. 명시적인 실제 운영 배포 승인 전 Production 사이트 변경 금지.

## 우선순위
P0: 브랜드 사용 충돌 해소, 명칭 결정
P1: 브랜드명 전체 텍스트·검색 메타·시각 요소 패치 검증 및 단일 비게시 Draft
P2: 전체 내부 링크·대표 이미지·네이버/구글 구조화 데이터·상담 알림 교차검사
P3: 중복 콘텐츠/역 주소 품질 위험 범위 확정, 공개 전 통합 심사
P4: 승인된 정확한 Draft 1회 Production 배포, 배포 후 HTTP/색인/폼 수신 QA
