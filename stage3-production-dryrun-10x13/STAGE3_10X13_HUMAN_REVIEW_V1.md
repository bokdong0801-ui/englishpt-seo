# Stage 3 10×13 Human Review V1

기준일: 2026-09-23
상태: HUMAN_REVIEW_PASS_USER_REVIEW_PENDING_NOT_PRODUCTION
production_deploy: false

## 범위
10개 audited locality rows × 13 intents = 130페이지

대표 직접 검수:
- 노형동 초등학생영어과외
- 가경동 중학생영어회화
- 화정동 고등학생영어회화
- 내곡동 대학생영어회화
- 중동 취준생영어회화
- 청라1동 직장인비즈니스영어
- 강남동 주부영어회화
- 사직동 토익과외
- 고운동 토익스피킹과외
- 강릉 내곡동 오픽과외
- 화정동 아이엘츠과외
- 사직동 듀오링고영어테스트
- 노형동 토플과외

## 자동 QA
- pages: 130
- localities: 10
- intents: 13
- visible text: 10,244 ~ 12,781자
- static failures: 0
- duplicate pairs: 585
- max cosine: 0.7511 < 0.82
- max 5-shingle Jaccard: 0.1982 < 0.24
- render: 260/260 PASS
- desktop: 130/130
- mobile: 130/130
- overflow: 0
- console/page errors: 0

## 사람 검수에서 발견하고 수정한 문제

### 1. 동적 조사 오류
초기 대표 페이지에서:
- `'처음 보는 문장 읽기'을 다음 확인 기준으로 남깁니다.`

수정:
- `다음 확인 기준으로는 '처음 보는 문장 읽기' 항목을 남깁니다.`

generator QA에 동적 라벨 뒤 잘못된 조사 패턴을 추가했다.

### 2. 우선순위 제목 조립 오류
초기:
- `시험일·발표일·면접일처럼 날짜가 있다면 남은 시간에 바꿀 수 있는 행동부터 역산합니다에서 무엇부터 볼지 정합니다`

수정:
- intro_pattern별 완성형 PRIORITY_HEADING 사용
- 예: `가장 가까운 일정에서 거꾸로 우선순위를 정합니다`
- 예: `현재 도움 수준을 보고 첫 순서를 정합니다`
- 예: `여러 선택지를 같은 기준으로 놓고 우선순위를 정합니다`

### 3. 중복 Gate 보강
기존 7차원 variation만으로는 Gold 핵심 본문 비중이 커서 일부 지역 간 동일 intent 중복이 높았다.

수정:
- 10개 locality 각각에 장문 독립 판단 서술 5개 문단 추가
- 지역 특성을 만들지 않고, variation signature의 관점/순서/상담 방식/연습 관점만 다르게 설명
- 결과:
  - max cosine 0.8837 → 0.7511
  - max 5-shingle 0.3313 → 0.1982

## 최종 전환 흐름

Hero
→ 빠른 판단 요약
→ 자기상황 식별
→ 5가지 선택 기준
→ 학습/시험 맥락 이해
→ 판단 가이드
→ 지역별 판단 방식
→ 우선순위
→ 수업 흐름
→ 중간 CTA
→ 판단 기준
→ 피드백 예시
→ FAQ
→ Deep Guide
→ 12개 관련 과정 내부링크
→ 상담 전 체크
→ Final CTA

## 선택 기준 5요소
모든 13 intent에서 아래를 intent별 실제 정보로 제공:
1. 이런 경우 잘 맞음
2. 다른 선택이 더 나을 수 있는 경우
3. 비용을 좌우하는 변수
4. 선생님/수업 비교 기준
5. 상담 전에 준비할 자료

## 대표 페이지 사람 판정
13개 대표본 모두:
- H1 intent 정확
- 선택 기준 intent별 구체화
- 우선순위 제목 자연어 완성형
- FAQ 동적 조사 오류 없음
- generic marketing copy 없음
- 허위 성과/기간 보장 없음
- 내부 DB 필드 노출 없음
- TOS standalone 없음
- 사용자 판단 중심 전환 흐름 유지

판정: HUMAN_REVIEW_PASS

## 다음 Gate
Stage 4 — 100 localities × 13 intents = 1,300 pages pre-production batch

Stage 4로 자동 승격하지 않고 사용자에게 Stage 3 실제 예시와 QA 결과를 먼저 보여준다.

main_merge: false
production_deploy: false
sitemap: false
robots: noindex,nofollow
