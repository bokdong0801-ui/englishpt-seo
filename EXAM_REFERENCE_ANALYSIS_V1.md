# EXAM REFERENCE ANALYSIS V1 — EnglishUp benchmark + ENGLISH PT existing exam pages

기준일: 2026-09-22
상태: REFERENCE ANALYSIS / NOT PRODUCTION
production_deploy: false

## 0. 분석 범위와 한계

사용자가 제공한 EnglishUp live reference URLs:
- https://englishup.kr/ilsan-dong-pungdong-ielts
- https://englishup.kr/giheung-cheongdeokdong-toeic-speaking
- https://englishup.kr/dongjak-sangdodong-toeic
- https://englishup.kr/dongjak-sangdodong-toefl
- https://englishup.kr/dongjak-sangdodong-opic

2026-09-22 현재 외부 fetch/DNS 환경에서 위 live HTML은 직접 열리지 않았다.
따라서 이 문서는 위 5개 live 페이지의 DOM을 직접 분석했다고 주장하지 않는다.

대신 아래 저장소 자료를 실제 분석 기준으로 사용한다.
1. REFERENCE_BENCHMARK_ENGLISHUP_MUNGYEONG_V1.md
   - 과거 사용자 제공 EnglishUp 소스를 기준으로 정리된 정보구조/전환 메커니즘
2. 기존 ENGLISH PT 시험 페이지 6개
   - dalseo-songhyeondong-1to1-toeic.html
   - dalseo-songhyeondong-1to1-toeic-speaking.html
   - dalseo-songhyeondong-1to1-opic.html
   - dalseo-songhyeondong-1to1-ielts.html
   - dalseo-songhyeondong-1to1-duolingo.html
   - dalseo-songhyeondong-1to1-toefl.html
3. CONVERSION_CONTENT_STANDARD_V4_CONVERSATIONAL_COMPACT.md

## 1. EnglishUp benchmark에서 유지할 설계

저장된 benchmark가 추출한 핵심 흐름:
Hero
→ decision/trust strip
→ strong problem insight
→ self-identification
→ evaluation/context literacy
→ priority
→ problem-by-problem explanation
→ curriculum
→ feedback/report
→ fit / other path
→ FAQ
→ deep guide
→ internal-link map
→ consultation pre-check
→ CTA

ENGLISH PT에서는 이를 아래처럼 재해석한다.
내 시험 목표 확인
→ 지금 점수를 막는 행동 찾기
→ 시험 구조와 개인 약점 분리
→ 실제 훈련 방법 확인
→ 새 문제/새 응답에서 재검증
→ 이 시험이 맞는지 다른 시험이 맞는지 판단
→ 상담에서 말할 정보 확인

디자인/문장/색상은 복제하지 않는다.

## 2. 기존 ENGLISH PT 6시험 페이지 DOM/콘텐츠 공통 구조

6시험 기존 페이지는 모두 다음 공통 컴포넌트를 사용한다.

- theme-test / intent-test
- breadcrumb
- Hero H1 + hero statement + hero copy
- Snapshot: GOAL / CURRENT BLOCK / TRAIN / NEXT
- CURRENT MOMENTS 4개
- PT CHECK 4 metrics
- TRAINING PROTOCOL 4단계
- TRAINING NOTE
- SESSION REPORT
- ILLUSTRATIVE CASE 3개
- PROGRESS 5단계
- FIT CHECK / OTHER PATH
- DEEP GUIDE 4~5개
- OFFICIAL NOTE
- FAQ
- final CTA
- RELATED links
- consultation modal

강점:
- 시험 전체를 한 점수로 보지 않고 병목을 분리한다.
- 목표 결과와 현재 약점을 연결한다.
- 실제 시험 일정에서 역산한다.
- sample/illustrative 문구로 허위 후기 위험을 낮춘다.
- 공식 시험 정보가 변경될 수 있음을 고지한다.
- 다른 시험 페이지로의 경계를 제공한다.

개선 필요:
- CHECK/TRAIN/RECHECK 같은 내부 설계 용어가 사용자 화면에 과다 노출된다.
- 서로 다른 시험 페이지에서 공통 문장이 지나치게 반복된다.
- "핵심 TOEIC의 핵심 기능" 같은 자동 문장 조립 흔적이 있다.
- FAQ가 시험별 실제 선택 질문보다 공통 boilerplate에 가깝다.
- Deep Guide 본문이 같은 문장 골격을 반복한다.
- 지역 맥락 문장이 시험 의사결정 정보보다 길어질 수 있다.

V4.5 시험 Gold Standard는 위 강점을 유지하면서 이 반복/자동생성 흔적을 제거한다.

## 3. 시험별 현재 페이지에서 확인된 핵심 축

### TOEIC
현재 지표:
- LC 이해
- 문법·어휘
- 독해 근거
- 시간 배분

현재 훈련:
- 파트별 진단
- 오답 원인
- 시간 훈련
- 실전 재점검

Deep Guide:
- LC/RC와 파트별 병목
- 목표 점수에 따른 파트 우선순위
- 오답 원인 분류
- 시험 직전 실전세트 vs 평소 학습

### TOEIC Speaking
현재 지표:
- 질문 이해
- 답변 구조
- 발화 안정성
- 시간 관리

현재 훈련:
- 핵심 문장
- 이유 확장
- 녹음 피드백
- 실전 시간

Deep Guide:
- 문항 유형별 답변 구조/시간
- 암기 답변 vs 즉석 변형
- 발음보다 전달력/구조/완결성
- 목표 레벨 기준 녹음/재답변

TOS 정책:
- TOS는 별도 indexable 시험 intent를 만들지 않는다.
- 토익스피킹 검색 alias / redirect / copy variant로만 처리한다.

### OPIc
현재 지표:
- 주제 경험
- 답변 길이
- 구조·연결
- 돌발 대응

현재 훈련:
- 스토리 소재
- 답변 구조
- 질문 변형
- 녹음 재답변

Deep Guide:
- 배경설문과 출제 대응
- 외운 답변의 돌발 취약성
- 목표 등급에 맞는 답변 범위
- 녹음/피드백 기반 반복 오류 축소

### IELTS
현재 지표:
- Listening
- Reading
- Writing
- Speaking

현재 훈련:
- 영역 진단
- 답안 분석
- 첨삭·재작성
- 실전 재평가

Deep Guide:
- 4영역 Band 병목
- Academic/General 목적 구분
- Writing 첨삭 / Speaking 피드백
- 시험일까지 남은 기간에 따른 학습 배분

### Duolingo English Test
현재 지표:
- Reading
- Writing
- Listening
- Speaking

현재 페이지에서 특히 강조된 것:
- 지원 학교가 DET를 인정하는지 먼저 확인
- adaptive 형식 적응
- Writing/Speaking open response
- skill/subscore 병목
- practice 재점검

Deep Guide:
- 지원기관 인정 여부/최소 점수
- 점수와 skill/subscore
- adaptive test 적응
- productive response
- 공식 practice 활용

주의:
현재 live EnglishUp Duolingo reference URL은 제공되지 않았다.
따라서 Duolingo Blueprint는 EnglishUp 5개 live 페이지의 직접 분석 결과가 아니라
저장된 benchmark + 기존 ENGLISH PT Duolingo 페이지를 기준으로 설계한다.

### TOEFL
현재 지표:
- Reading
- Listening
- Writing
- Speaking

현재 훈련:
- 정보 요약
- 메모 구조
- 답변/글 구성
- 통합 재적용

Deep Guide:
- Reading/Listening 입력을 Speaking/Writing으로 연결
- 통합형에서 메모와 요약
- 목표 점수별 영역 우선순위
- 시험 일정 기준 실전세트/약점 보완

## 4. V4.5 시험 페이지가 해결해야 할 공통 질문

시험 페이지를 읽고 사용자가 아래 질문에 답할 수 있어야 한다.

1. 이 시험이 내 제출/지원/취업 목적에 맞는가?
2. 시험일 또는 제출 마감은 언제인가?
3. 목표 점수/등급/Band/Level은 무엇인가?
4. 현재 전체 점수보다 실제로 막는 영역은 무엇인가?
5. 단순 문제량이 아니라 어떤 행동을 바꿔야 하는가?
6. 수업에서는 무엇을 확인하고 어떻게 재훈련하는가?
7. 새 문제/새 질문/실전 시간에서도 다시 되는가?
8. 다른 시험이나 일반 회화가 더 직접적인 선택은 아닌가?
9. 공식 시험 구조나 지원기관 요건 중 무엇을 직접 확인해야 하는가?
10. 상담에서 무엇을 알려주면 되는가?

## 5. 최종 적용 원칙

- 시험별 고유 정보구조는 유지하되 페이지 문장 골격은 공유하지 않는다.
- 시험 공식 구조/점수/접수/인정기관 정보는 변동 가능 정보로 취급한다.
- production 생성 시 공식기관 검증 가능한 링크/확인 문구를 둔다.
- 점수 상승, 목표 달성 기간, 합격/등급 보장을 만들지 않는다.
- 실후기가 없으면 illustrative/sample feedback만 사용한다.
- "지역 + 시험명"은 Hero/Title/crumb에서 명확히 사용하되 검증되지 않은 지역별 시험 수요를 만들지 않는다.
