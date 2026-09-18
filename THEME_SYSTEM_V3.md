# ENGLISH PT THEME SYSTEM V3

기준일: 2026-09-18  
상태: 전국 확장용 디자인·콘텐츠 테마 기준

## 1. 핵심 원칙

ENGLISH PT는 **지역 계층 페이지와 대상별 서비스 페이지를 하나의 디자인 시스템으로 연결하되, 두 페이지군의 역할과 시각 언어를 분리**한다.

- 지역 계층 페이지 = 길찾기 / 서비스 탐색 / 하위 지역 연결
- 대상별 서비스 페이지 = 해당 타깃의 문제를 깊게 설명하고 상담 전환
- 지역 계층 페이지의 색은 ENGLISH PT 중립 브랜드 톤으로 통일
- 대상별 서비스 페이지는 초등·중등·고등·대학생·취준생·직장인·성인·주부 등 각 타깃의 기존 색상 테마를 유지
- 색상만 다르게 하고 본문은 같은 템플릿으로 복제하는 방식은 금지
- 타깃별로 문제 장면, 진단 기준, 훈련 모듈, 사례, CTA 전 문맥이 달라져야 한다

## 2. 지역 계층 페이지의 역할

지역 페이지는 행정정보 문서가 아니다. 향후 서울 → 종로구 → 청운동처럼 계층형 탐색을 지원하더라도 본문 목적은 영어 서비스 탐색이어야 한다.

### 허용 정보
- 정확한 지역명과 상위 계층
- breadcrumb
- 하위 지역 또는 해당 지역의 서비스 진입점
- 초등/중등/고등/대학생/취준생/직장인/성인·주부 등 타깃 라우터
- 영어회화/영어과외/시험/면접/비즈니스 등 허용된 서비스 라우터
- 짧은 지역 문맥
- PT 진단 CTA

### 금지 정보
- place_id, official_code, 좌표, relation dump
- 법정동/행정동 자체를 주제로 한 긴 설명
- 영어 서비스보다 행정정보가 더 많은 페이지

지역 계층의 깊이는 **색상 변화가 아니라 breadcrumb, hierarchy label, 하위 지역 카드 구조**로 표현한다.

## 3. 지역 페이지의 중립 팔레트

- accent: #50665B
- accent2: #9C927D
- hero: #EDEAE2
- heroText: #18211D
- soft: #F6F4EE
- paper: #FFFDF8
- ink: #18211D
- muted: #6D7771
- line: #D7DCD7

지역 허브에서 대상 카드를 보여줄 때는 카드 상단/라벨에서 각 대상의 accent 색을 미리 보여줄 수 있다. 그러나 페이지 전체 배경·헤더·CTA는 중립 지역 테마를 유지한다.

## 4. 대상별 테마

| 대상 | body class | 핵심 색감 | 콘텐츠 톤 |
|---|---|---|---|
| 초등 | theme-elem | 청록 | 안정적·친근, 기초와 학습 루틴 |
| 중등 | theme-mid | 딥블루/청록 | 내신·수행·학습관리 분석형 |
| 고등 | theme-high | 네이비+골드 | 내신·모의·수능 중심 고밀도 분석형 |
| 대학생 | theme-univ | 블루그레이+브론즈 | 캠퍼스·발표·교환학생·진로형 |
| 취준생 | theme-job | 딥그린+브론즈 | 마감·면접·공인영어 실전형 |
| 직장인 | theme-worker | 포레스트+골드 | 회의·발표·협상 전문형 |
| 성인 | theme-adult | 세이지+샌드 | 생활·여행·재시작형 |
| 주부 | theme-housewife | 올리브+로즈브라운 | 생활 일정·자기계발형 |
| 시니어 | theme-senior | 세이지+베이지 | 이해·반복·생활 활용형 |
| 국제학교 | theme-intl | 인디고+브론즈 | Academic Writing·Reading·Debate형 |

실제 HEX 값과 생성 규칙은 `theme_manifest_v3.json`을 단일 기준으로 사용한다.

## 5. 같은 디자인 시스템으로 보이게 하는 공통 요소

다음은 페이지군이 달라도 동일하게 유지한다.

- ENGLISH PT 헤더/브랜드 마크
- Pretendard 기반 타이포그래피
- 최대 콘텐츠 폭과 grid 원칙
- PT CHECK / TRAINING / REPORT 시각 문법
- 버튼 모양과 상담 모달
- 모바일 sticky CTA
- breadcrumb 형태
- 카드 테두리와 spacing scale
- 접근성 focus 상태
- footer

즉, 사용자는 어느 페이지에서도 같은 브랜드 안에 있다고 느끼지만 **대상 페이지에 들어가면 색과 콘텐츠의 성격이 명확히 달라져야 한다.**

## 6. 대상별 콘텐츠를 강제로 분리하는 규칙

### 초등
기초·학교영어·어휘·읽기·말하기 자신감·학습 루틴. 수능/취업 중심 전개 금지.

### 중등
내신·수행평가·문법·독해·듣기·오답·주간 학습관리. 성인 시험영어 중심 전개 금지.

### 고등
내신·모의고사·수능·독해·듣기·수행평가·어휘·등급/약점·1:1 계획. 정보밀도를 가장 높게 유지.

### 대학생
캠퍼스 대화·발표·세미나 질문·교환학생·공인영어·면접.

### 취준생
자기소개·경험·지원동기·STAR·꼬리질문·영어면접·OPIc/TOEIC Speaking/TOEIC.

### 직장인
회의·발표·제안·협상·고객/이해관계자 대응·비즈니스 영어. 학생 과외 문구 금지.

### 성인/주부
일상·여행·영어 재시작·첫 문장·질문 이어가기·생활 일정 안의 루틴. 취업/수능 중심 전개 금지.

## 7. 지역 허브 → 서비스 페이지의 시각 전환

예: 청운동 허브에서는 전체 배경을 중립 베이지/그린으로 유지한다.

- 초등 카드: 청록 accent
- 중등 카드: 딥블루 accent
- 고등 카드: 네이비+골드 accent
- 대학생 카드: 블루그레이 accent
- 취준생 카드: 딥그린 accent
- 직장인 카드: 포레스트 accent
- 성인 카드: 세이지 accent
- 주부 카드: 올리브 accent

사용자가 고등 카드를 누르면 해당 서비스 페이지 전체가 `theme-high`로 전환된다. 이때 hero, report, section accent, CTA 주변 시각 신호가 고등 테마를 사용한다.

## 8. 계층형 URL과 연결 원칙

현재 신규 동 URL 규칙을 기준으로 한다.

- 동 허브: `seoul-jongno-cheongundong.html`
- 고등 서비스: `seoul-jongno-cheongundong-high-conv.html`
- 중등 서비스: `seoul-jongno-cheongundong-mid-conv.html`

향후 상위 지역 페이지가 승인되면:
- 시도 서비스 허브: `seoul.html`
- 시군구 서비스 허브: `seoul-jongno.html`
- 동 서비스 허브: `seoul-jongno-cheongundong.html`

단, 디자인 시스템이 상위 계층을 지원한다고 해서 현재 동 단계보다 먼저 시/구 페이지를 대량 생성하지 않는다. 배포 순서는 DONG_PHASE_V3의 phase gate를 따른다.

## 9. 생성기에서 필요한 필드

모든 신규 HTML은 최소 다음 값을 결정한 뒤 생성한다.

- page_role = region | service
- region_level = sido | sigungu | dong | newtown | village | district | null
- audience = elem | mid | high | univ | job | worker | adult | housewife | senior | intl | generic
- theme_class
- content_blueprint
- primary_intent
- canonical
- breadcrumb_chain

서비스 페이지에서 `audience`와 `theme_class`가 불일치하면 생성 실패로 처리한다.

## 10. QA HARD GATE

- 지역 페이지가 audience 전용 theme를 전체 페이지에 사용하면 FAIL
- audience 서비스 페이지가 theme-local만 사용하면 FAIL
- 파일명/intent의 audience와 body theme가 다르면 FAIL
- 대상별 금지 콘텐츠가 핵심 모듈에 들어가면 FAIL
- 지역 페이지가 영어 서비스 의도 없이 행정정보만 설명하면 FAIL
- 지역 허브의 audience 카드 accent와 서비스 페이지 theme가 매칭되지 않으면 FAIL
- 기존 95페이지의 타깃 theme를 신규 공통 테마로 덮어버리면 FAIL

## 11. 현재 적용 전략

1. 기존 95페이지의 현재 팔레트는 보존한다.
2. 팔레트를 `theme_manifest_v3.json`과 공통 CSS에 중앙화한다.
3. 기존 페이지는 점진적으로 inline `:root` 의존을 제거하되 URL/콘텐츠를 한 번에 변경하지 않는다.
4. 새 전국 페이지는 처음부터 manifest 기반으로 생성한다.
5. 청운동 지역 허브는 neutral region theme + target-colored route cards로 개선한다.
6. 청운동 고등/중등/초등/대학생/취준생/직장인/주부 샘플에서 각 theme와 content blueprint를 검수한 뒤 전국 생성기로 확장한다.

## 12. 최종 기준

> 지역 계층은 사용자를 올바른 영어 서비스로 안내하는 지도이고, 대상별 랜딩은 각 사용자의 실제 문제를 해결하는 상담 페이지다. 둘은 같은 ENGLISH PT 브랜드 문법을 공유하지만 같은 색, 같은 문장, 같은 콘텐츠 구조로 평준화하지 않는다.
