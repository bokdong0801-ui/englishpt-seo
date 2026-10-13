# ENGLISH PT — 66,937 PAGE PRODUCTION STAGE GATES V1

기준일: 2026-09-22
상태: BUILD_DEPLOYABLE_SYSTEM
production_deploy: false

## 최종 생성 범위

Eligible locality rows: 5,149

Independent intents per locality: 13

### 7 service intents
- elem-tutor
- mid-conv
- high-conv
- univ-conv
- jobseeker-conv
- biz-business-conv
- housewife-conv

### 6 exam intents
- toeic
- toeic-speaking
- opic
- ielts
- duolingo
- toefl

TOS/토스:
- standalone page 생성 금지
- TOEIC Speaking alias로만 처리

Final new-page count:
- 5,149 × 13 = 66,937 pages

Region hub pages:
- 5,149
- 현재 66,937 production batch에는 포함하지 않음

## 현재 완료 상태

PASS / FROZEN:
- V4.5 7-target Gold Sample: 35 pages
- V4.5 6-exam Gold Sample: 30 pages
- 95 preserved URL regression: PASS
- 74 legacy redirects regression: PASS
- 7-target desktop/mobile render: PASS
- 6-exam desktop/mobile render: PASS
- reserved 95 slug conflicts: 0

아직 완료되지 않은 production prerequisite:
1. 5,149 row-level locality manifest materialization
2. 13-intent combined production manifest
3. production generator that consumes row manifest + two Gold Sample families
4. staged dry-run QA
5. bulk generation + bulk QA
6. sitemap/deploy/rollback packaging

## Stage 1 — 5,149 locality row manifest

목표:
- 실제 생성 가능한 5,149개 동을 row-level JSON/JSONL로 고정
- 각 row에 canonical region_slug, visible dong_name, jurisdiction, source type, variation assignment 포함
- HOLD 64 rows 제외
- preserved 95 conflict = 0 재확인

다음 단계 진입 조건:
- rows = 5,149 exactly
- slug unique = 5,149
- malformed row = 0
- hold rows included = 0
- reserved 95 collision = 0

### 사용자에게 반드시 보여줄 예시
최소 5개 locality row:
- 서울 서초 내곡동
- 강릉 내곡동
- 강릉 강남동
- 세종 고운동
- 부산 해운대 중동

그리고 실제 생성될 13개 H1 중 한 지역 전체 세트 예시를 표시한다.

## Stage 2 — 1 locality × 13 intents integration preview

목표:
- service generator와 exam generator를 하나의 production interface로 연결
- 한 locality에서 13개 page가 동일 URL/canonical contract로 생성되는지 확인

생성 수:
- 13 pages

QA:
- H1 exact
- canonical exact
- unique title/meta
- no malformed Korean
- no TOS standalone
- internal links
- schema parse
- Gold Sample contract match

### 사용자에게 반드시 보여줄 예시
13개 HTML 전부 파일명 + H1을 보여준다.
추가로 최소 4개 실제 페이지 본문 preview:
- elementary
- university
- TOEIC
- IELTS

사용자 검토 없이 Stage 3로 넘어가지 않는 것을 기본 원칙으로 한다.

## Stage 3 — 10 localities × 13 intents dry-run

목표:
- 5 variation frame과 same-name locality를 섞어 production generator 검증

생성 수:
- 130 pages

QA:
- static
- duplicate
- cross-intent collision
- canonical/schema/internal links
- desktop/mobile representative render

### 사용자에게 반드시 보여줄 예시
- 지역 10개 목록
- 13 intent 각각 최소 1페이지
- 총 13개 대표 HTML preview
- 가장 유사도가 높은 pair와 가장 긴/짧은 페이지 예시

## Stage 4 — 100 localities × 13 intents pre-production batch

목표:
- production-scale file count와 runtime 문제를 1,300페이지에서 먼저 검증

생성 수:
- 1,300 pages

QA:
- filename collisions = 0
- canonical collisions = 0
- missing files = 0
- static failures = 0
- duplicate thresholds
- sitemap shard prototype
- deploy package size estimate
- sampled render QA

### 사용자에게 반드시 보여줄 예시
- 13 intents × 서로 다른 지역 = 최소 13페이지
- same-name locality 비교 2세트
- mobile/desktop screenshot 대신 실제 렌더 QA 결과와 HTML preview 제공
- sitemap shard sample

## Stage 5 — Full generation

진입 조건:
Stages 1~4 모두 PASS.

생성:
- 5,149 localities × 13 intents
- exactly 66,937 new HTML pages

이 시점이 사용자가 질문한 “6만 개 넘는 페이지를 실제 생성하는 단계”다.

주의:
- 이 단계는 생성 단계이지 production deploy 승인 단계가 아니다.
- 기본 출력은 production-ready artifact/directory이며 deploy는 별도 Gate.

### 사용자에게 반드시 보여줄 예시
전체 생성 직후 자동으로 아래 sample pack을 만든다.
- 13 intents × 3 지역 = 39 representative pages
- same-name locality samples
- longest/shortest page
- highest duplicate-similarity pair
- 5 random deterministic samples using fixed slug ordering, not random runtime selection
- page-count report
- collision report
- QA summary

## Stage 6 — Full bulk QA

66,937 files에 대해:
- exact file count
- unique canonical
- unique URL
- H1 exact
- malformed Korean
- JSON-LD parse
- internal links
- TOS standalone zero
- preserved 95 collision zero
- duplicate sampling/matrix strategy
- forbidden production/pilot copy
- noindex/index policy according to deploy stage

### 사용자에게 반드시 보여줄 예시
실패가 0이어도 representative 13 pages를 다시 보여준다.
실패가 있으면 실패 페이지를 sample pack 최상단에 배치한다.

## Stage 7 — Sitemap / deploy preview / rollback

production deploy 직전:
- sitemap shards
- sitemap index
- robots
- redirects
- preserved 95
- rollback package
- Netlify preview or deploy artifact

### 사용자에게 반드시 보여줄 예시
- sitemap shard 실제 예시
- 최종 production URL 예시 13개
- preserved old URL redirect 예시
- deploy preview page examples

## Stage 8 — explicit production approval

사용자 명시 승인 전:
- main merge 금지
- production deploy 금지
- bulk index request 금지

## 변경 금지

현재부터 새 디자인/콘텐츠 방향 변경은 중단한다.
허용:
- generator defect
- Korean grammar defect
- QA defect
- collision
- URL/canonical/schema/internal-link defect
- sitemap/redirect/deploy/rollback defect

Gold Sample을 수정해야 하는 blocking defect가 발견되면 기존 freeze를 직접 덮어쓰지 않고 새 버전으로 검증한다.
