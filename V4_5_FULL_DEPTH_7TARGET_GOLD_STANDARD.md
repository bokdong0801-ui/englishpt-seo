# V4.5 FULL-DEPTH 7-TARGET GOLD STANDARD

기준일: 2026-09-21
상태: FINAL GENERATION CONTRACT / NOT PRODUCTION DEPLOYED
적용 범위: 동 Phase 1 서비스 랜딩페이지
production_deploy: false

## 0. 목적

V4.5 Full-depth 페이지는 단순 키워드 랜딩이나 지역명 치환 페이지가 아니다.
검색자가 상담 전 아래 질문에 스스로 답할 수 있어야 한다.

1. 내 상황과 같은 문제인가?
2. 왜 이런 문제가 생기는가?
3. 무엇부터 확인해야 하는가?
4. 수업에서는 실제로 무엇을 하는가?
5. 무엇이 달라졌는지 어떤 행동으로 확인하는가?
6. 이 과정이 아니라 다른 과정이 먼저인 경우는 무엇인가?
7. 상담에서 무엇을 말하면 되는가?

핵심 서비스 페이지 visible text 권장 범위는 4,000~7,000자다.
글자 수 자체가 목적은 아니며, 반복 문장으로 분량을 채우지 않는다.

## 1. 공통 섹션 계약

모든 7타깃은 아래 판단 흐름을 유지한다.

1. Minimal Localized Hero
2. Detailed Intro
3. Self-identification / Real Situations
4. Diagnosis / Why it happens
5. Priority / Boundary
6. Class Flow
7. Observable Change / Decision Proof
8. Sample Feedback — 반드시 예시 형식임을 표시
9. Fit / Other Path
10. FAQ 5~7개
11. Deep Guide 2~4개
12. Related Intent Links
13. Consultation Preview / Phone CTA
14. Final CTA

Hero H1은 반드시 지역명 + 핵심 서비스 키워드만 표시한다.
긴 진단 문장과 고민 질문은 Hero 다음 첫 본문에 둔다.

## 2. 문장 생성 Gold Rule

### 2.1 한국어 조사
동적 토큰 뒤 조사를 문자열로 고정 결합하지 않는다.
Hangul final consonant 기반 helper를 통해 아래를 처리한다.

- 은/는
- 이/가
- 을/를
- 과/와
- 이나/나
- 으로/로

금지 예:
- 대학생영어회화을
- 의견·근거이나
- 익숙한 단어로 문장 만들기은

### 2.2 단계명과 설명문 분리
UI label 또는 단계명을 완성 문장 안에 그대로 삽입하지 않는다.

금지:
- 현재 읽기와 이해를 짧게 확인을 통해...
- 다음 수업에서 다시 확인 결과를 보고...

허용:
- 먼저 익숙한 문장과 처음 보는 문장을 각각 읽어봅니다.
- 수업 마지막에는 다음 시간에 다시 확인할 한두 가지 행동을 기록합니다.

### 2.3 자연어 완성문
설명문은 완성된 sentence bank 또는 타깃 전용 copy block에서 가져온다.
명사구 + 조사 + 공통 suffix 조립만으로 본문을 만들지 않는다.

### 2.4 반복 방지
같은 페이지 안에서 동일한 결론문/연결문을 2회 이상 반복하지 않는다.
35개 pilot에서는 같은 intent의 5개 지역이 동일한 문단 순서와 동일한 첫 문장을 공유하지 않도록 한다.

## 3. 지역 Variation Gold Rule

지역 차별화를 위해 검증되지 않은 지역 생활상·학교·상권·인구 특성을 만들어내지 않는다.

5개 pilot variation archetype:

### Scene Log
최근 실제로 막힌 한 장면을 기록하고 그 장면 앞뒤를 잘라 확인한다.
핵심 질문: "최근 어디에서 멈췄나요?"

### Deadline Context
가장 가까운 시험·발표·면접·여행·업무 일정을 기준으로 우선순위를 정한다.
핵심 질문: "다음 영어 사용 일정이 언제인가요?"

### Error Trace
겉으로 같은 막힘도 어휘/이해/구조/회수/첫 반응 중 원인을 분리한다.
핵심 질문: "왜 그 순간에 막혔나요?"

### Use Case
다음 실제 사용 장면에서 해야 하는 행동을 먼저 정한 뒤 역산한다.
핵심 질문: "다음에 영어로 무엇을 해야 하나요?"

### Reuse Test
한 번 성공한 문장을 질문·상대·순서·시간 압박이 달라져도 다시 쓸 수 있는지 확인한다.
핵심 질문: "조건이 바뀌어도 다시 할 수 있나요?"

지역 variation은 글쓰기 프레임이며 지역 고유 사실을 가장하지 않는다.

## 4. 초등 Gold Standard — v4-elem-parent-evidence-v2

### 독자
초등학생 본인보다 학부모의 관찰과 선택을 우선한다.

### 반드시 다룰 실제 장면
- 처음 보는 문장을 소리 내어 읽기
- 단어 뜻을 문장 안에서 연결하기
- 며칠 뒤 배운 표현 기억하기
- 배운 내용을 자기 말로 설명하거나 짧게 사용하기

### 진단 깊이
읽기 문제를 발음 하나로 묶지 않는다.
소리 연결, 단어 인식, 문장 뜻 연결, 기억 회수, 직접 사용을 분리한다.

### Priority
학교 진도와 기초가 충돌하면 무조건 선행하지 않는다.
현재 수업을 따라가는 데 필요한 기초와 다음 학교영어 장면을 먼저 연결한다.

### Class Flow
현재 행동 확인 → 익숙한 단어로 성공 → 새 문장으로 변형 → 자기 말로 설명 → 다음 수업 재확인

### Decision Proof
읽기 / 이해 / 기억 / 사용 / 학부모 5분 확인 / 다음 확인 항목

### Boundary
시험 단기 점수가 가장 급한 경우, 영어 독서만이 목적일 경우, 별도 과정이 더 직접적일 수 있음을 안내한다.

### FAQ
학부모가 집에서 확인할 수 있는 질문을 포함한다.

## 5. 중등 Gold Standard — v4-mid-school-bridge-v2

### 반드시 다룰 실제 장면
- 교과서 본문
- 문법 적용
- 듣고 바로 반응
- 수행평가 말하기
- 평소 / 수행 직전 / 지필 직전 우선순위

### 진단 깊이
'외웠는데 바뀌면 틀림'을 본문 기억, 문법 전이, 듣기 처리, 말하기 회수로 분리한다.

### Class Flow
학교 일정 확인 → 본문 의미 재구성 → 문법을 새 문장에 적용 → 듣고 한 문장 반응 → 수행 질문 변형 → 다음 시험 약점 기록

### Decision Proof
본문 / 문법 / 듣기 / 수행 / 학년별 우선순위 / 다음 시험 약점

### Boundary
내신 지필고사 자체가 가장 급하면 시험 범위 학습을 우선한다.

## 6. 고등 Gold Standard — v4-high-priority-deadline-v2

### 반드시 다룰 실제 장면
- 수행 발표
- 질문 대응
- 듣고 요약
- 면접/발표 첫 반응
- 내신·모의·수능·수행의 경계

### 핵심
고등 영어 전체를 회화로 해결한다고 말하지 않는다.
가장 가까운 평가와 회화가 실제로 필요한 행동을 분리한다.

### Class Flow
deadline 선택 → 질문/요약 기준 확인 → 짧은 답 구조 → 예상 밖 질문 변형 → 실제 평가 행동 재확인

### Decision Proof
deadline / 질문 / 요약 / boundary / 고1·고2·고3 우선순위 / 평가행동 피드백

## 7. 대학생 Gold Standard — v4-univ-campus-output-v2

### 반드시 다룰 실제 장면
- 발표 Q&A
- 세미나 의견과 근거
- 팀프로젝트 동의·반대·확인 질문
- 교환학생 생활/수업 참여
- 발표·토론·생활영어의 일정 우선순위

### 진단 깊이
첫 반응, 의견 근거, 요약/바꿔 말하기, 질문 대응, 되묻기를 분리한다.

### Class Flow
가까운 캠퍼스 일정 → 첫 반응 → 근거 연결 → 요약/바꿔 말하기 → 질문 대응/되묻기 → 다른 캠퍼스 장면 재사용

### Decision Proof
첫 반응 / 의견·근거 / 요약·바꿔 말하기 / 질문 대응 / 가까운 일정 / 캠퍼스 장면 재사용

### Boundary
TOEIC·IELTS 점수 자체가 급하면 시험영어 우선.
영어면접이 더 가깝다면 취준생 영어면접 과정 우선.

## 8. 취준생 Gold Standard — v4-job-interview-evidence-v2

### 반드시 다룰 실제 장면
- 자기소개 첫 20초
- 경험 근거
- 지원동기
- 회사/직무 연결
- 꼬리질문
- 예상 밖 질문 회복
- 답변 길이 조절

### 진단 깊이
영어 표현 부족과 경험 정리 부족을 구분한다.
STAR를 외우는 것이 아니라 실제 경험에서 근거를 뽑고 질문이 바뀌어도 재구성하게 한다.

### Class Flow
채용 일정/직무 → 경험 근거 → 짧은 답변 블록 → 직무 연결 → 꼬리질문 변형 → 모의면접 기록

### Decision Proof
첫 답변 / 경험 근거 / 직무 연결 / 꼬리질문 회복 / 답변 길이 / 다음 모의질문

### Boundary
OPIc·TOEIC Speaking 제출 점수가 급하면 시험영어 우선.
일상회화가 목적이면 일반 성인회화가 더 직접적이다.

## 9. 직장인 Gold Standard — v4-worker-work-output-v2

### 반드시 다룰 실제 장면
- 회의
- 발표
- 전화/화상
- 고객 대응
- 협상/조건 확인

### 핵심
표현집 학습보다 다음 실제 업무 output을 남긴다.
실제 업무자료는 보안/고유명사를 일반화해 연습 재료로 바꾼다.

### Class Flow
다음 업무 장면 → 자료 일반화 → 핵심 문장 3~5개 → 질문/반론 재현 → 업무 후 기록

### Decision Proof
회의 / 발표 / 콜 / 고객 대응 / 자료 일반화 / 다음 업무에서 쓸 문장

### Boundary
시험 점수가 목표면 시험영어 우선.

## 10. 주부 Gold Standard — v4-housewife-lifefit-v2

### 반드시 다룰 실제 장면
- 여행
- 아이 영어 이해
- 영어 재시작
- 자기계발
- 재취업/해외생활 가능성
- 외국인 대화
- 생활 속 짧은 루틴

### 핵심
30·40·50·60대를 고정된 성향으로 묘사하지 않는다.
연령은 대표 상담 상황을 설명하는 참고 문맥으로만 사용한다.

### Class Flow
다시 시작하는 이유 → 기억나는 표현 → 짧은 생활 문장 → 장면 변경 반복 → 유지 가능한 시간/빈도 → 생활 재사용

### Decision Proof
여행 / 아이 영어 / 재시작 / 루틴 / 가능한 시간 / 생활 재사용

### Boundary
자격시험이나 학교 성적처럼 평가가 목표면 해당 시험/학교영어를 우선한다.

## 11. Full-depth 분량 배분 가이드

권장 visible text:
- Detailed Intro: 450~700자
- Real Situations: 700~1,000자
- Diagnosis: 900~1,400자
- Priority/Boundary: 450~700자
- Class Flow: 700~1,000자
- Decision Proof: 500~800자
- Sample Feedback: 350~600자
- Fit/Other Path: 300~500자
- FAQ: 600~900자
- Deep Guide: 800~1,200자
- CTA/Related: 200~350자

반복을 피하면서 전체 4,000~7,000자 범위에 들어오게 한다.

## 12. QA Hard Gate

대량 생성 전 5×7 pilot은 다음을 모두 통과해야 한다.

### Natural Korean
- malformed particle 0
- label-to-sentence grammar error 0
- duplicate ending sentence 0
- internal design jargon visible 0

### Content
- 35/35 visible text 4,000~7,000자 권장 범위
- 7 target intent separation PASS
- 5 locality variation structure PASS
- no fabricated locality facts
- sample feedback clearly labeled example

### SEO/Technical
- H1 exactly one
- localized H1 template
- title/meta/canonical intent preserved
- schema valid
- internal links valid
- noindex pilot
- live lead submit disabled
- reserved 95 URL conflict 0

### Duplicate
same-intent cross-locality:
- cosine < 0.82
- 5-shingle Jaccard < 0.24

### Render
35 desktop + 35 mobile
- horizontal overflow 0
- console/page error 0

이 Gate를 통과한 35개만 전국 5,149개 생성의 Gold Sample로 승격한다.
