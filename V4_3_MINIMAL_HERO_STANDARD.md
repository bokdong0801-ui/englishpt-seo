# V4.3 MINIMAL HERO / DEEP BODY STANDARD

기준일: 2026-09-20
상태: active presentation contract for new V4 pages
production_deploy: false

## 핵심 원칙

첫 화면(Hero)은 설명하는 곳이 아니라
'내가 어떤 페이지에 들어왔는지'를 1초 안에 확인하는 곳으로 사용한다.

긴 고민 질문, 긴 설명문, 진단 카드, 범위 설명은 Hero에서 제거하고
첫 본문 섹션으로 이동한다.

## Hero 표시 규칙

서비스 intent에 맞는 짧은 H1만 사용한다.

- 초등학생 영어회화: 초등학생영어회화
- 초등학생 영어과외: 초등학생영어과외
- 중학생 영어회화: 중학생영어회화
- 고등학생 영어회화: 고등학생영어회화
- 직장인 비즈니스영어: 직장인비즈니스영어
- 주부 영어회화: 주부영어회화

대상 안내 허브:
- 초등: 초등영어
- 중등: 중등영어
- 고등: 고등영어

지역명과 브랜드는 작은 eyebrow/breadcrumb로만 보조한다.

## Hero에 남기는 것

1. 작은 브랜드/지역 eyebrow
2. 짧은 H1 한 줄
3. 본문으로 이동하는 CTA
4. 상담 CTA

## Hero에서 빼는 것

- 긴 질문형 H1
- 2~4문장 설명문
- 진단/snapshot 카드
- 체크리스트
- 여러 개의 정보 카드
- 장문의 신뢰 문구

## 첫 본문으로 이동하는 것

기존 Hero에 있던:
- 사용자의 실제 고민
- 왜 이런 문제가 생기는지
- 현재 상태를 나누는 기준
- 진단/snapshot
- 서비스 범위
- 생활/학교/업무 맥락

첫 본문은 Hero 직후 바로 배치한다.

## SEO 원칙

Visible Hero를 짧게 만든다고
title/meta description/canonical/URL intent를 억지로 바꾸지 않는다.

예:
- /elem-tutor 페이지의 visible H1 = 초등학생영어과외
- 별도 /elem-conv 페이지의 visible H1 = 초등학생영어회화

검색 의도와 H1을 충돌시키지 않는다.

## Conversion 이유

Hero: 빠른 정체성 확인
Body 1: '내 얘기다' 공감
Body 2+: 판단에 필요한 구체적 정보
CTA: 충분한 정보 이후 상담

즉, 설명을 삭제하는 것이 아니라
설명의 위치를 Hero에서 본문으로 옮긴다.

## QA

- H1 concise
- Hero visible text should remain compact
- detailed previous Hero copy exists in first body section
- no loss of diagnostic/scope information
- desktop/mobile overflow 0
- modal works
- noindex preview before production
