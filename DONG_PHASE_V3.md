# ENGLISH PT — 전국 동 우선 구축 계획 V3

기준일: 2026-09-15
상태: Phase 1 최우선 실행 기준

## 1. 확장 순서

전국 확장은 아래 순서를 고정한다.

1. 동(DONG)
2. 구(GU)
3. 시(SI)
4. 신도시(NEWTOWN)
5. 마을(VILLAGE)
6. 지구(DISTRICT)

동 단계의 데이터 정규화, URL 정책, 랜딩 템플릿, 중복 방지, 내부링크, QA가 안정화되기 전에는 다음 단계로 넘어가지 않는다.

---

## 2. V5 기준 동 현황

CURRENT 기준:

- LEGAL_DONG: 3,656
- ADMIN_DONG: 2,220
- 동 엔티티 합계: 5,876
- 같은 시군구 안에서 동일 이름의 LEGAL_DONG + ADMIN_DONG 중복: 663 검색지역
- 동일 이름을 검색지역 기준으로 병합한 1차 landing candidate: 5,213

ABOLISHED:

- LEGAL_DONG: 6,660
- ADMIN_DONG: 3,525

폐지 동은 신규 indexable 랜딩을 만들지 않는다. 과거 검색어, alias, redirect, 현재 지역 연결을 위한 resolver 데이터로만 유지한다.

---

## 3. 가장 중요한 구분 — DB 엔티티와 공개 랜딩은 다르다

### DB 레이어

법정동과 행정동을 절대 합쳐서 저장하지 않는다.

예:
- LEGAL_DONG `청운동`
- ADMIN_DONG `청운효자동`

각각 place_id, official_code, parent, CURRENT/ABOLISHED, relation을 그대로 보존한다.

### 공개 검색지역 레이어

사용자가 검색하는 지역명 단위로 landing candidate를 만든다.

규칙:

A. 같은 시군구 + 같은 이름의 LEGAL_DONG과 ADMIN_DONG이 둘 다 있으면 공개 지역 후보는 1개로 병합한다.

B. 같은 시군구에서 이름이 다른 행정동은 독립 검색지역 후보로 유지한다.

C. 법정동 이름과 행정동 이름이 다르더라도 ADMINISTERS 관계를 resolver에서 연결한다.

D. 페이지 본문에는 `법정동/행정동 코드 DB`를 설명하지 않는다. 필요할 때만 자연어 지역 문맥으로 사용한다.

E. 같은 동명이 다른 시군구에 존재하면 각각 별도 지역이다. full hierarchy로 식별한다.

---

## 4. 동 데이터 산출물

Phase 1 데이터는 최소 네 층으로 관리한다.

### 4.1 dong_entity_master

V5 CURRENT 동 원본 엔티티 테이블.

필드 예:
- place_id
- place_type = LEGAL_DONG / ADMIN_DONG
- name_ko
- full_name_ko
- official_code
- parent_place_id
- legal_status
- source_id
- source_snapshot_date

### 4.2 dong_relation_master

현재 ADMIN_DONG ↔ LEGAL_DONG의 정확한 ADMINISTERS 관계.

이름 추측으로 연결하지 않는다.

### 4.3 dong_search_locality_master

실제 공개 랜딩 후보를 위한 검색지역 테이블.

핵심 필드:
- locality_key
- sido
- sigungu
- dong_name
- legal_dong_ids
- admin_dong_ids
- related_legal_dong_ids
- related_admin_dong_ids
- current_status
- canonical_candidate
- landing_status
- slug_status

### 4.4 dong_alias_master

폐지 지역, 과거 명칭, 표기 변형을 현재 검색지역으로 연결하는 내부 resolver 테이블.

신규 indexable 페이지를 무조건 만들지 않는다.

---

## 5. 동 랜딩의 정확한 의미

`동 랜딩페이지`는 지역 DB 상세페이지가 아니다.

예: 청운동 랜딩

잘못된 형태:
- 청운동 공식코드
- 좌표
- parent_place_id
- relation 표
- V5 데이터 카드

올바른 형태:
- H1: 청운동 영어회화·영어과외처럼 영어 서비스 의도가 명확한 지역 허브
- 청운동에서 선택할 수 있는 영어 학습 목적
- 초등 / 중등 / 고등 / 대학생 / 취준생 / 직장인 / 성인·주부 등 목적별 진입
- 영어회화 / 영어과외 / 기초영어 / 시험영어 / 영어면접 / 비즈니스영어 등 허용된 intent 연결
- PT 진단 방식
- 지역의 정확한 상위 계층을 breadcrumb와 짧은 문맥에 반영
- 해당 지역과 정확히 연결되는 내부링크
- 무료 PT 진단 CTA

지역 자체 설명은 최소한으로 사용하고 영어 학습 선택을 돕는 것이 본문 목적이다.

---

## 6. 동 랜딩 생성 단계

### STEP 1 — 전국 동 원본 정규화

모든 CURRENT LEGAL_DONG / ADMIN_DONG 추출.

검사:
- 중복 place_id 0
- parent 누락 0 또는 예외 목록 명시
- CURRENT/ABOLISHED 혼입 금지
- full_name_ko와 hierarchy 일치

### STEP 2 — 법정동/행정동 관계 결합

ADMINISTERS relation만 사용한다.

검사:
- 이름 유사도 기반 임의 결합 금지
- 폐지 admin relation은 current landing 관계에서 제외
- 한 행정동이 여러 법정동을 관리할 수 있음을 허용

### STEP 3 — 공개 검색지역 후보 생성

`같은 관할 + 같은 이름`은 병합하고 이름이 다른 admin/legal 지역은 각각 후보 유지.

예상 1차 후보: 5,213.

여기서 아직 HTML을 대량 생성하지 않는다.

### STEP 4 — URL manifest 확정

DB ID URL 금지.

URL은 최소 다음을 식별해야 한다.
- 상위 지역
- 동 이름
- 서비스 intent

동명이인 충돌을 resolver에서 검증한다.

URL 문법은 샘플 검수 후 고정한다.

### STEP 5 — 동 지역 허브 샘플

먼저 3~5개 성격이 다른 동으로 검수한다.

샘플 유형:
- 법정동 중심, 행정동명이 다른 곳: 청운동
- 법정동/행정동 이름이 같은 곳
- 행정동 이름만 강한 곳
- 동일 동명이 다른 지역에 존재하는 사례
- 광역시/특별자치시 등 hierarchy 특수 사례

샘플 통과 후 generator를 만든다.

### STEP 6 — 서비스 랜딩 샘플

한 동에서 대표 intent를 검수한다.

우선순위:
1. 고등학생영어회화
2. 중학생영어회화 또는 영어과외
3. 초등학생영어과외 또는 영어회화
4. 대학생영어회화
5. 취준생영어회화/영어면접
6. 직장인비즈니스영어
7. 성인/주부영어회화

95개 송현동 URL을 그대로 전부 복제하지 않는다.

### STEP 7 — 중복/doorway QA

지역명만 바꾼 동일 문서가 되지 않도록 content signature를 비교한다.

최소 검사:
- title/H1/canonical unique
- 지역 hierarchy 정확
- target/service intent 정확
- 대상별 금지 콘텐츠 없음
- intro/section/case 과도한 중복 없음
- 관련 링크 실제 존재
- DB 코드 노출 없음
- FAQPage schema 없음
- 허위 후기 없음

### STEP 8 — 제한 배포

전국 5,213개를 처음부터 한 번에 index하지 않는다.

권장 방식:
- 샘플 승인
- 1개 시도 또는 소규모 묶음 배포
- index/크롤링/중복/사용성 확인
- 다음 묶음 확대

---

## 7. URL을 지금 바로 확정하지 않는 이유

전국 동에는 다음 문제가 있다.

- 같은 이름의 동이 여러 시군구에 존재
- 법정동과 행정동 이름이 같은 경우와 다른 경우가 혼재
- 특별시/광역시/특별자치시의 hierarchy 차이
- 기존 송현동 URL과 신규 URL의 호환성
- 한글 slug / romanized slug 정책

따라서 DB ID 기반 URL로 도망가지 않고, 실제 샘플 3~5개로 충돌을 검증한 뒤 URL 문법을 고정한다.

---

## 8. Phase 1 완료 조건

동 단계가 완료됐다고 판단하려면 아래가 모두 충족돼야 한다.

1. CURRENT 동 entity master 완성
2. legal/admin exact relation master 완성
3. search locality master 완성
4. abolished/alias resolver 완성
5. URL manifest 확정
6. 지역 허브 샘플 승인
7. 타깃 서비스 샘플 승인
8. 자동 generator 완성
9. duplicate/doorway QA 통과
10. staged deployment 검증
11. sitemap/canonical/redirect 검증
12. 기존 95페이지와 74 redirects 회귀 테스트 통과

이 12개가 끝난 뒤에만 구 단계로 넘어간다.

---

## 9. 이후 단계

### Phase 2 — 구

동 랜딩의 상위 서비스 허브로 설계. 단순 구청/행정정보 페이지가 아니라 구 단위 영어 서비스 탐색 및 하위 동 연결 허브.

### Phase 3 — 시

시 단위 서비스 탐색 허브. 하위 구/동이 많은 도시와 단일 시군구형 도시를 분리 설계.

### Phase 4 — 신도시

V5 exact relation이 있는 신도시만 사용. 행정동과 동일 취급하지 않음. 신도시 검색의도가 실제 영어 서비스 탐색과 연결될 때 별도 landing 후보.

### Phase 5 — 마을

농촌마을/생활권/리와 혼동하지 않고 source와 relation이 검증된 마을만 적용.

### Phase 6 — 지구

택지·도시개발·공공주택·산단 등 district type을 구분. 단순 명칭 중복으로 지역 landing을 생성하지 않음.

---

## 10. 최종 원칙

전국 지역 DB의 폭을 먼저 넓히지 않는다.

`동 데이터 정확도 → 동 검색지역 정규화 → 동 영어 서비스 랜딩 품질 → 자동화/QA → 제한 배포`

이 순서를 완성한 뒤 다음 지역 유형으로 한 단계씩 확장한다.
