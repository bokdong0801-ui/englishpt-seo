# V4.5 5×7 HUMAN CONTENT REVIEW V1

기준일: 2026-09-21
대상: pilot-v45-5x7 35 service pages
상태: HUMAN_CONTENT_QA_HOLD_BEFORE_MASS_GENERATION
production_deploy: false

## 결론

35페이지는 구조/정적/중복/브라우저 렌더 QA는 통과했지만, 5,149개 전국 생성 전에 사람 관점의 문장 품질 gate를 한 번 더 통과해야 한다.

현재 강점:
- 7타깃별 첫 고민과 핵심 상황이 명확히 분리됨
- 5개 지역 variation pack이 서로 다른 사고 흐름을 사용함
- Decision Proof / 예시 피드백 / 다른 과정 경계가 타깃별로 구분됨
- 허위 후기·성과 수치 없이 process evidence를 사용함
- same-intent duplicate gate와 70-render QA 통과

현재 HOLD 이유:
1. 조사 자동 결합 오류
2. 동적 명사구 삽입 문장의 문법 오류
3. 본문 정보량이 V4 기준보다 얇음
4. 지역별 구조 차이는 있으나 실제 locality 맥락은 얕음
5. 일부 공통 문구와 section label이 prototype 느낌을 남김

## 1. 조사 자동 결합 — CRITICAL

35/35 페이지의 첫 본문 lead에서 서비스명 뒤에 고정 '을'이 붙는다.

예:
- 초등학생영어과외을 알아볼 때
- 중학생영어회화을 알아볼 때
- 대학생영어회화을 알아볼 때
- 취준생영어회화을 알아볼 때
- 주부영어회화을 알아볼 때
- 직장인비즈니스영어을 알아볼 때

개별 HTML 교정보다 generator에서 받침 여부 기반 을/를 처리가 필요하다.

또한 동적 명사 뒤 이나/나 처리도 필요하다.
명확한 오류 예:
- 의견·근거이나 → 의견·근거나
- 발표이나 → 발표나
- 읽기이나 → 읽기나
- 자기소개이나 → 자기소개나
- 회의이나 → 회의나
- 듣기이나 → 듣기나
- 말하기이나 → 말하기나
- 대화이나 → 대화나
- 경계이나 → 경계나

## 2. 동적 단계명 삽입 — CRITICAL

단계 제목 문자열을 문장에 그대로 붙이면서 자연어가 깨지는 사례가 있다.

예:
- 현재 읽기와 이해를 짧게 확인을 통해...
- 익숙한 단어로 문장 만들기은...
- 다음 수업에서 다시 확인 결과를 보고...
- 평가 행동으로 다시 확인을 다음 실제 장면과 연결해...

규칙:
단계명은 UI label로만 사용하고 설명문은 별도 완성 문장 template/copy bank에서 생성한다.
단계명 + 조사 자동결합으로 설명문을 만들지 않는다.

## 3. 정보량 — HIGH

PILOT_5X7_QA_V1 기준 visible_chars:
- min 1,391
- max 1,628
- avg 1,482

CONVERSION_CONTENT_STANDARD_V4_CONVERSATIONAL_COMPACT.md:
핵심 서비스 페이지 기본 범위는 약 4,000~7,000자에서 시작.

현재 pilot은 구조/variation 검증 fixture로는 충분하지만 전국 indexable SEO landing의 final content depth로 승격하지 않는다.

보강 우선순위:
- Real Situations: 각 상황별 원인/확인법/연습법
- Class Flow: 단계별 실제 예시
- Decision Proof: 관찰 기준을 단순 label이 아니라 판단 문장으로 설명
- Sample Feedback: 타깃별 2~3형식
- FAQ: 실제 선택 질문 5~7개
- Deep Guide: 타깃 검색 의도에 맞는 2~3개 판단 정보 블록

## 4. 7타깃 분리 — PASS WITH IMPROVEMENT

### Elementary
강점: 읽기/뜻 설명/기억/직접 사용의 행동 단위가 좋음.
보완: 학부모 관찰 문장을 더 늘리고 school-English vs tutoring boundary를 분명히 한다.

### Middle
강점: 본문/문법/듣기/수행의 연결 문제와 시험 일정 우선순위가 분명함.
보완: 평소/수행 직전/지필 직전의 실제 학습 차이를 더 구체화한다.

### High
강점: 내신·모의·수능·수행과 회화의 경계를 명확히 잡음.
보완: 고1/고2/고3별 deadline example과 수행/면접 example을 더 분리한다.

### University
강점: 발표 Q&A·세미나·팀프로젝트·교환학생이 실제 캠퍼스 output 중심으로 정리됨.
보완: 발표/토론/교환학생 목적별로 같은 회화 페이지 안에서 우선순위 분기를 더 깊게 준다.

### Jobseeker
강점: 자기소개/경험 근거/직무 연결/꼬리질문이 일반 회화와 명확히 다름.
보완: first 20 seconds, STAR evidence, company/job linkage, unexpected question recovery를 실제 답변 행동 예시로 확장한다.

### Worker
강점: 회의/발표/전화·화상/고객·협상과 다음 업무 output이 선명함.
보완: role/meeting/presentation/call별 짧은 sample scenario를 추가한다.

### Housewife
강점: 가족 일정/재시작/여행/아이 영어/루틴이라는 생활 맥락이 살아 있음.
보완: 30·40·50·60대를 stereotype 없이 '상담 상황'으로만 더 구체화하고, 여행/아이/재취업/자기계발 분기를 확장한다.

## 5. 5개 지역 variation — STRUCTURAL PASS / LOCALITY DEPTH HOLD

현재 지역 variation:
- 서울 서초 내곡동: scene-log / 최근 막힌 장면 기록형
- 강릉 내곡동: deadline-context / 가까운 일정 우선형
- 강릉 강남동: error-trace / 막힘 원인 추적형
- 세종 고운동: use-case / 다음 실제 사용 장면형
- 부산 해운대 중동: reuse-test / 조건을 바꿔 재사용 확인형

이 구조 차이는 의미가 있고 지역명 치환만 한 복제보다 낫다.

단, 지역 고유 사실을 직접 활용하는 수준은 낮다.
전국 생성에서는 검증되지 않은 학교/상권/생활 패턴을 만들어내지 않는다.
지역 차별화는:
1) variation pack,
2) 검색의도/타깃,
3) 검증된 locality metadata,
4) 필요할 때만 검증 가능한 지역 context
순으로 만든다.

## 6. Prototype 느낌 제거 — MEDIUM

production 전 정리 대상:
- DETAILED INTRO
- SCOPE / REAL SITUATIONS
- PRIORITY
- CLASS FLOW
- FIT / OBSERVABLE CHANGE
- DECISION PROOF
- DEEP GUIDE / ...

내부 설계 용어처럼 보일 수 있으므로 숨기거나 자연스러운 한국어 UI label로 교체한다.

공통 final CTA:
'과정보다 먼저, 지금 필요한 장면부터 확인하세요.'
35개 공통 사용은 기술적으로 문제 없지만 전국 대량 페이지에서는 타깃별 3~5개 ending bank로 분산하는 편이 좋다.

## 7. 사람 관점 최종 Gate

현재:
- STRUCTURE: PASS
- STATIC QA: PASS
- SAME-INTENT DUPLICATE: PASS
- RENDER: PASS
- 7 TARGET DIFFERENTIATION: PASS
- REGION VARIATION STRUCTURE: PASS
- NATURAL KOREAN GRAMMAR: HOLD
- CONTENT DEPTH: HOLD
- PRODUCTION COPY POLISH: HOLD

따라서 5,149개 mass generation은 아직 실행하지 않는다.

다음 승격 조건:
1. Korean particle helper 적용
2. dynamic phrase sentence templates 제거/재작성
3. V4.5 full-depth content generator 보강
4. 5×7 재생성
5. human sample re-review
6. duplicate/static/render 재검사
7. existing 95 + redirect regression
8. explicit production approval
