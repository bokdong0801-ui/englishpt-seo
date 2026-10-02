# V4.5 EXAM 5×6 HUMAN CONTENT REVIEW V1

기준일: 2026-09-22  
상태: HUMAN_CONTENT_QA_PASS_RENDER_PENDING_NOT_PRODUCTION  
production_deploy: false

## 1. 검수 범위

5개 지역 × 6개 시험 = 30개 Full-depth 시험형 Pilot의 정적/중복 QA 통과 후,
아래 4개 대표 페이지를 실제 독자 흐름으로 직접 읽고 문장 품질과 시험별 차별화를 검수했다.

- TOEIC: `pilot-v45-exam-5x6/seoul-seocho-naegokdong-toeic.html`
- IELTS: `pilot-v45-exam-5x6/gangwon-gangneung-naegokdong-ielts.html`
- OPIc: `pilot-v45-exam-5x6/gangwon-gangneung-gangnamdong-opic.html`
- TOEIC Speaking: `pilot-v45-exam-5x6/sejong-goundong-toeic-speaking.html`

최종 생성 workflow:
- run: 35692359949
- generated source head after workflow: `8854e47e592111c2e6d6787b43717223dc65a72c`

## 2. 자동 QA 최종 결과

- page_count: 30
- visible text: 6,299 ~ 7,137자
- average visible text: 6,771.8자
- static failures: 0
- same-exam locality comparison: 60 pairs
- max cosine: 0.7871 < 0.82
- max 5-shingle Jaccard: 0.2391 < 0.24
- standalone TOS pages: 0
- malformed Korean patterns caught by generator QA: 0
- production deploy: false

## 3. 사람 검수 중 발견해 generator 단계에서 수정한 문제

### A. 중복 감소용 blind token replacement 제거
초기 시도에서 중복률을 낮추기 위해 단어를 기계적으로 치환하자 다음과 같은 비문이 발생했다.

- `Part 5·6 문항를`
- `질의을`
- `응시이`
- `제한 제한 시간`

해결:
- token replacement 방식을 폐기
- 시험별 원문은 자연어 그대로 유지
- 지역 variation 차이는 독립적인 장면/일정/오류/사용/재사용 판단 가이드로 생성

### B. 동적 라벨 조사 오류
대표 TOEIC Speaking에서:
- `'질문 이해'과 연결된`

해결:
- `'질문 이해'에 연결된`처럼 조사가 필요 없는 완성문 구조로 변경
- QA에 quoted-label connective 오류 검사 추가

### C. 내부 제작 언어 제거
기존 FAQ:
- `이 프로젝트에서는 토스/TOS를...`

최종 사용자 문장:
- `토스/TOS는 TOEIC Speaking을 가리키는 표현으로 보고 같은 시험 대비 페이지에서 안내합니다. 별도의 토스 시험 페이지로 나누지 않습니다.`

### D. 시험 성격과 맞지 않는 공통 피드백 제거
초기 OPIc 오류형 예시에는 `경험 소재 오답`, `근거 선택`처럼 문제풀이형 표현이 있었다.

해결:
- 5개 variation의 피드백 generator를 시험 공통으로 자연스러운 행동 관찰 언어로 재작성
- 예: `'경험 소재' 항목은 첫 시도에서 기준이 흔들렸지만 짧은 힌트 뒤에는 수정됨. 다음에는 비슷한 새 문제나 응답에서 힌트 없이 다시 확인하기.`

## 4. 대표 페이지별 사람 검수

### TOEIC — PASS
H1: `내곡동 토익과외`

좋은 점:
- LC/RC 전체 점수보다 파트·오답원인·시간배분 병목을 먼저 제시한다.
- `LC 처리 / 문법·어휘 근거 / 독해 근거 / 실전 점수 변동`이 실제 토익 고민으로 분리돼 있다.
- Class Flow가 `최근 점수·마감 → 파트별 병목 → 오답 원인 → 제한 시간 → 새 세트 재검증`으로 시험 준비 행동과 연결된다.
- Deep Guide가 문제량과 오답분석, Part 7 시간 문제, 시험 직전 학습을 별도 판단정보로 제공한다.
- TOEIC Speaking/OPIc 및 유학시험과의 Boundary가 명확하다.

판정:
- generic 영어시험 페이지가 아니라 TOEIC 전용 intent가 명확함.
- 문장 조립 이상 없음.
- PASS.

### IELTS — PASS
H1: `내곡동 아이엘츠과외`

좋은 점:
- Overall Band 하나가 아니라 Listening/Reading/Writing/Speaking 4영역 병목을 구분한다.
- 일정형 variation이 시험일·지원 마감과 자연스럽게 연결된다.
- Writing은 첨삭→재작성, Speaking은 새 질문 재답변, Reading/Listening은 오답근거·시간으로 각각 역할이 다르다.
- 다른 시험(TOEFL/DET)과의 선택 경계를 제공한다.
- Deep Guide가 Band 병목, Writing 첨삭 활용, Speaking 즉석확장, Listening/Reading 근거, 기간별 배분으로 나뉜다.

판정:
- 4영역 시험이라는 IELTS 성격이 본문 전체에 유지됨.
- PASS.

### OPIc — PASS
H1: `강남동 오픽과외`

좋은 점:
- `경험 소재 / 답변 길이 / 구조·연결 / 돌발 대응`으로 OPIc 특성이 분명하다.
- 배경설문 자체보다 실제 에피소드와 질문 변형 대응을 강조한다.
- 스크립트 암기와 돌발 회복의 차이를 사용자 언어로 설명한다.
- 녹음은 점수 약속이 아니라 반복 표현·첫 반응·구조를 확인하는 증거로 사용한다.
- 사람 검수에서 발견된 문제풀이식 공통 피드백은 generator에서 제거 완료했다.

판정:
- TOEIC Speaking과 다른 OPIc 검색 의도가 충분히 분리됨.
- PASS.

### TOEIC Speaking — PASS
H1: `고운동 토익스피킹과외`

좋은 점:
- `질문 이해 / 첫 반응 / 답변 구조 / 시간·변형 대응`을 실제 말하기시험 행동으로 제시한다.
- `문항 요구 → 첫 문장 → 이유·예시 → 녹음 → 시간제한/변형 재답변` 흐름이 선명하다.
- 발음만 과도하게 강조하지 않고 전달력·구조·완결성과 함께 판단한다.
- 토스/TOS를 별도 중복 URL로 만들지 않고 TOEIC Speaking alias로 자연스럽게 안내한다.
- 동적 조사 오류와 내부 프로젝트 문구를 generator 단계에서 수정 완료했다.

판정:
- OPIc과 역할이 분명히 다르고 시험 intent가 명확함.
- PASS.

## 5. 공통 품질 판정

PASS:
- 6시험별 문제 정의와 수업 흐름이 구분됨
- 5지역 variation은 지역 사실을 꾸며내지 않고 설명 프레임만 다르게 사용
- 점수 상승/등급/기간 보장 없음
- 예시 피드백을 실제 후기처럼 사용하지 않음
- 공식 시험 구조·접수·지원기관 정보는 변동 가능 정보로 고지
- TOS 별도 indexable 페이지 없음
- 한국어 동적 조립 결함을 generator QA에 추가함

의도적으로 남겨둔 Pilot 문구:
- `V4.5 EXAM FULL-DEPTH PILOT · noindex`
- production 미배포
- 상담 폼 실제 전송 비활성 안내

이 문구들은 production 승격 시 제거/전환해야 하며 현재는 안전장치다.

## 6. 최종 결론

**HUMAN_CONTENT_QA_PASS**

30페이지는:
- STATIC PASS
- DUPLICATE PASS
- HUMAN CONTENT PASS

상태다.

다음 Gate는 desktop/mobile Render QA다.
Render QA까지 통과하기 전에는 `EXAM GOLD SAMPLE FROZEN` 또는 production-ready로 승격하지 않는다.
