# V4.5 EXAM 5×6 GOLD SAMPLE FREEZE V1

기준일: 2026-09-22

Freeze ID: `V4.5-EXAM-5X6-GOLD-SAMPLE-FROZEN`

상태: **GOLD_SAMPLE_FROZEN_ALL_GATES_PASS_NOT_PRODUCTION**

## Freeze 범위

- 5개 지역
- 6개 시험
- 30개 Full-depth 시험형 Pilot
- TOEIC / TOEIC Speaking / OPIc / IELTS / Duolingo English Test / TOEFL iBT
- TOS/토스는 TOEIC Speaking alias이며 독립 indexable 페이지 없음

## 통과 Gate

- Static QA: PASS
- Duplicate QA: PASS
- Human Content QA: PASS
- Desktop Render QA: 30/30 PASS
- Mobile Render QA: 30/30 PASS

## Render QA

Workflow run: `35693687847`

- render cases: 60
- failures: 0
- horizontal overflow failures: 0
- console/page error cases: 0
- H1 visibility failures: 0
- Hero phone CTA visibility failures: 0
- Hero "내용 보기" CTA visibility failures: 0
- Hero "상담 신청" CTA visibility failures: 0

## 콘텐츠/중복 QA

- 30 pages
- visible text: 6,299 ~ 7,137자
- same-exam locality comparisons: 60 pairs
- max cosine: 0.7871 < 0.82
- max 5-shingle Jaccard: 0.2391 < 0.24
- static failures: 0
- standalone TOS pages: 0

## Safety 상태

- robots: noindex,nofollow
- live lead submission: false
- sitemap inclusion: false
- main merge: false
- production deploy: false

## 동결 원칙

이 30페이지와 연결 generator/Blueprint/Gold Standard는 전국 시험형 확장의 Gold Sample 기준으로 사용한다.

전국 batch 작업에서 문구·구조·시험별 intent를 변경하려면 이 freeze를 직접 수정하지 않고 새 버전에서 검증한다.

이 freeze는 production 배포 승인이 아니다.
