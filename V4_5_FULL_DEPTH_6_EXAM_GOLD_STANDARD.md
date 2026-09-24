# V4.5 FULL-DEPTH 6-EXAM GOLD STANDARD

기준일: 2026-09-22
상태: FINAL_FOR_6_EXAM_PILOT / NOT PRODUCTION
production_deploy: false

## 0. 범위

독립 시험 intent:
1. TOEIC
2. TOEIC Speaking
3. OPIc
4. IELTS
5. Duolingo English Test
6. TOEFL iBT

TOS 정책:
- 별도 Blueprint / URL / indexable 페이지 생성 금지
- TOEIC Speaking의 alias로 처리
- 기존 TOS URL은 TOEIC Speaking 대표 URL로 redirect 유지

## 1. 공통 페이지 흐름

1. Minimal Localized Hero
2. Goal / Deadline Intro
3. Self-identification: 실제로 막히는 장면 4개
4. Exam Context: 시험 구조와 개인 약점 분리
5. Bottleneck Diagnosis
6. Priority / Deadline Allocation
7. Training Flow
8. Observable Decision Proof
9. Sample Feedback — 예시 명시
10. Fit / Other Test
11. Deep Guide 3~5개
12. FAQ 5~7개
13. Official Verification Note
14. Related Test Links
15. Consultation Preview
16. Final CTA

Hero H1:
- {dong_name} 토익과외
- {dong_name} 토익스피킹과외
- {dong_name} 오픽과외
- {dong_name} 아이엘츠과외
- {dong_name} 듀오링고영어테스트
- {dong_name} 토플과외

Hero는 페이지 정체성만 보여준다.
긴 점수 진단 문장과 시험 설명은 첫 본문으로 이동한다.

## 2. 시험 페이지 공통 생성 규칙

### Goal First
현재 점수만 묻지 않는다.
제출/지원/취업 목적 + 시험일/마감 + 목표 결과를 먼저 확인한다.

### Bottleneck, not score-only
전체 점수 하나로 학습 방향을 정하지 않는다.
각 시험의 영역/문항/응답 행동을 나눠 현재 병목을 찾는다.

### Official vs Personal
공식 시험 구조와 개인 약점을 섞지 않는다.
공식 구조는 모든 응시자에게 공통이고, 학습 우선순위는 개인별로 다르다.

### Train and Recheck
설명/문제풀이에서 끝나지 않는다.
오답 또는 불완전 응답의 원인을 기록하고 새 문제/새 질문/실전 시간에서 다시 확인한다.

### No promises
점수 상승 보장, 목표 달성 기간 보장, 합격/등급 보장 금지.

### Official verification
시험 구조·점수·접수·인정기관 정책은 변경될 수 있으므로
최종 production 페이지는 공식 시험기관 또는 지원기관 최신 정보를 확인하도록 안내한다.

## 3. TOEIC Gold Standard

Blueprint: v45-exam-toeic-bottleneck-v1

첫 질문:
"LC와 RC를 계속 풀고 있는데, 정작 어느 파트와 시간 배분이 점수를 막는지는 알고 있나요?"

핵심 장면:
- LC에서 들은 내용을 문제 선택으로 연결하지 못함
- Part 5/6에서 문법·어휘 오답 이유가 남지 않음
- Part 7에서 근거를 찾지만 시간이 부족함
- 실전 세트마다 점수 변동 원인을 설명하기 어려움

진단 축:
- LC 처리
- 문법·어휘 근거
- 독해 근거
- 시간 배분
- 반복 오답 원인

수업 흐름:
최근 점수/마감 확인
→ 파트별 병목 분리
→ 오답 원인 태깅
→ 제한 시간 적용
→ 새 세트 재검증

Decision Proof:
- 어떤 파트가 실제 병목인지 설명 가능
- 오답 이유를 근거로 말할 수 있음
- 제한 시간 안에서 풀이 순서를 유지
- 새 문제에서도 같은 기준 적용
- 다음 세트 우선순위 기록

Boundary:
말하기 점수 제출이 목적이면 TOEIC Speaking/OPIc가 더 직접적일 수 있다.
유학/해외대학 지원이 목적이면 IELTS/TOEFL/DET 요구조건을 먼저 확인한다.

Deep Guide:
- LC/RC와 파트별 병목 구분
- 문제량과 오답 분석의 차이
- 시간 부족이 실력 문제인지 순서 문제인지
- 시험일에서 역산한 평소/직전 학습 분리

## 4. TOEIC Speaking Gold Standard

Blueprint: v45-exam-toeic-speaking-response-v1
Alias: TOS / 토스

첫 질문:
"답변 내용은 알고 있는데, 준비 시간이 끝나면 첫 문장을 바로 시작하고 제한 시간 안에 마무리할 수 있나요?"

핵심 장면:
- 질문 의도 파악이 늦어 시작이 늦음
- 첫 문장은 나오지만 이유/예시가 이어지지 않음
- 발음에 신경 쓰다 답변 구조가 무너짐
- 문항이 변형되면 암기 답변을 그대로 쓰기 어려움

진단 축:
- 질문 이해
- 첫 반응
- 답변 구조
- 발화 명료성
- 시간 관리
- 질문 변형 대응

수업 흐름:
목표 Level/시험일
→ 문항 요구 파악
→ 첫 문장/핵심 답
→ 이유·예시 확장
→ 녹음 피드백
→ 시간 제한/질문 변형 재답변

Decision Proof:
- 첫 반응 지연 감소
- 결론/이유 구조 유지
- 제한 시간 내 완결
- 녹음에서 반복 오류 확인
- 질문 변형에도 재구성

Boundary:
자유로운 경험 스토리와 돌발 대응이 핵심이면 OPIc가 더 직접적인 목적일 수 있다.
일반 업무 회화가 목표라면 직장인 비즈니스영어가 더 직접적이다.

Deep Guide:
- 문항 요구와 답변 구조
- 암기답변 vs 즉석 변형
- 발음보다 전달력/구조/완결성
- 녹음 비교와 재답변 루틴

## 5. OPIc Gold Standard

Blueprint: v45-exam-opic-story-recovery-v1

첫 질문:
"외운 답변은 있는데, 돌발 질문이나 표현이 조금 바뀌면 내 이야기로 다시 이어갈 수 있나요?"

핵심 장면:
- 배경설문은 정했지만 실제 경험 소재가 부족함
- 답변 길이가 짧거나 내용이 반복됨
- 연결어는 쓰지만 스토리 구조가 약함
- 돌발 질문에서 암기답변이 무너짐

진단 축:
- 경험 소재
- 첫 반응
- 답변 길이
- 구조·연결
- 돌발 대응
- 녹음 안정성

수업 흐름:
목표 등급/시험일
→ 실제 경험 소재 정리
→ 짧은 스토리 블록
→ 질문 변형
→ 돌발 회복
→ 녹음 비교/재답변

Decision Proof:
- 같은 경험을 다른 질문에 재사용
- 답변 길이 과소/과다 조절
- 예상 밖 질문에서 회복
- 스크립트 없이 핵심 유지
- 녹음 전후 반복 오류 감소

Boundary:
제한된 문항 구조와 업무 제출용 말하기시험이 목표라면 TOEIC Speaking이 더 직접적일 수 있다.

Deep Guide:
- 배경설문과 실제 경험 소재
- 외운 답변이 돌발에서 무너지는 이유
- 등급 목표에 따른 답변 범위
- 녹음/피드백/재답변

## 6. IELTS Gold Standard

Blueprint: v45-exam-ielts-four-skill-band-v1

첫 질문:
"Overall Band만 보고 있나요, 아니면 네 영역 중 어떤 영역이 목표 Band를 막는지 알고 있나요?"

핵심 장면:
- Listening에서 들었지만 답으로 옮기는 과정에서 놓침
- Reading에서 시간과 근거 찾기가 동시에 흔들림
- Writing에서 논리/구성/표현 피드백이 반복됨
- Speaking에서 아는 내용도 즉석 확장이 어려움

진단 축:
- Listening
- Reading
- Writing
- Speaking
- 목표 Band와 영역별 차이
- 시험일/지원 마감

수업 흐름:
지원 목적/시험 유형/마감
→ 4영역 현재 수준 분리
→ Band 병목 우선순위
→ Writing 첨삭·재작성 / Speaking 재답변
→ Reading/Listening 오답 근거
→ 실전 조건 재평가

Decision Proof:
- 영역별 병목을 설명 가능
- Writing 수정 이유를 이해하고 재작성
- Speaking 새 질문에서도 같은 기준 적용
- Reading/Listening 오답 근거 기록
- 시험일까지 학습비중 재조정

Boundary:
TOEFL/DET 등 지원기관이 다른 시험을 인정하는 경우 제출 조건을 먼저 비교한다.
Academic/General 등 세부 시험 선택은 공식 최신 안내 확인이 필요하다.

Deep Guide:
- 4영역 Band 병목
- 시험 목적/유형 확인
- Writing 첨삭과 Speaking 피드백
- 영역별 목표와 전체 목표의 차이
- 시험일까지 남은 기간에 따른 배분

## 7. Duolingo English Test Gold Standard

Blueprint: v45-exam-det-adaptive-output-v1

첫 질문:
"DET 점수를 준비하기 전에, 지원 학교가 시험을 인정하는지와 어떤 영어 기능이 현재 결과를 막는지 확인했나요?"

핵심 장면:
- 지원기관 인정 여부/최소 요구조건 확인이 안 됨
- adaptive 형식에서 연습 결과 변동이 큼
- Writing/Speaking open response가 짧음
- 총점만 보고 skill별 약점을 설명하기 어려움

진단 축:
- 지원기관 요구조건
- Reading
- Writing
- Listening
- Speaking
- adaptive format 적응
- productive response

수업 흐름:
지원기관/마감 확인
→ skill별 현재 수행
→ adaptive format 적응
→ Writing/Speaking 응답 확장
→ 공식 practice 활용
→ 새 practice 재점검

Decision Proof:
- 지원조건을 직접 확인
- skill별 병목 구분
- open response 완결성 향상 여부 확인
- 형식 변화에도 핵심 유지
- 공식 practice 결과로 재점검

Boundary:
지원기관이 TOEFL/IELTS 등 다른 시험을 요구하거나 선호하는 경우 해당 시험 조건을 먼저 비교한다.

Deep Guide:
- 지원기관 인정 여부/최소 기준 확인
- adaptive format과 일반 영어 숙련도
- productive response
- skill/subscore 해석
- 공식 practice 활용

주의:
live EnglishUp Duolingo reference는 제공되지 않았다.
본 Blueprint는 저장된 EnglishUp benchmark + 기존 ENGLISH PT DET 페이지를 기준으로 한다.

## 8. TOEFL iBT Gold Standard

Blueprint: v45-exam-toefl-integrated-academic-v1

첫 질문:
"Reading과 Listening은 이해하는데, 그 정보를 Speaking이나 Writing 답변으로 연결할 때 흔들리나요?"

핵심 장면:
- Reading 핵심을 잡지만 요약이 길어짐
- Listening 메모가 많아도 핵심 관계가 남지 않음
- Speaking에서 입력 정보를 제한 시간 안에 재구성하기 어려움
- Writing에서 읽기/듣기 정보를 논리적으로 연결하기 어려움

진단 축:
- Reading
- Listening
- 메모/요약
- Speaking
- Writing
- 통합형 연결
- 시험일/목표 점수

수업 흐름:
지원/시험일
→ Reading/Listening 핵심 추출
→ 메모 구조
→ Speaking/Writing 답변 구성
→ 통합형 적용
→ 다른 자료 재적용

Decision Proof:
- 읽기/듣기 핵심을 짧게 요약
- 메모량보다 관계 중심으로 기록
- Speaking/Writing에 입력정보 연결
- 다른 자료에서도 통합 기준 유지
- 실전 시간에서 재확인

Boundary:
IELTS/DET 등 지원기관이 다른 시험을 인정하는 경우 지원조건과 시험 적합성을 먼저 확인한다.

Deep Guide:
- Reading/Listening 입력과 Speaking/Writing 연결
- 통합형에서 메모와 요약
- 목표 점수별 영역 우선순위
- 실전 세트와 취약영역 보완

## 9. Full-depth 권장 분량

visible text:
- Hero + Intro: 450~700자
- Self-identification: 600~900자
- Exam Context/Diagnosis: 700~1,100자
- Priority/Deadline: 400~700자
- Training Flow: 700~1,000자
- Decision Proof: 450~700자
- Sample Feedback: 300~500자
- Fit/Other Test: 300~500자
- Deep Guide: 900~1,400자
- FAQ: 600~900자
- Official/CTA/Links: 250~450자

전체 4,500~7,500자 권장.

## 10. 6시험 Pilot Hard Gate

- 6 Blueprint allowlist only
- TOS standalone URL 0
- Hero H1 exactly one
- localized H1 exact
- canonical unique
- malformed Korean particle 0
- internal design jargon visible 0
- official-changing-info disclaimer present
- sample feedback explicitly example
- fabricated review/score/time promise 0
- same-exam cross-locality cosine < 0.82
- same-exam 5-shingle Jaccard < 0.24
- desktop/mobile overflow 0
- console/page error 0
- production_deploy false
