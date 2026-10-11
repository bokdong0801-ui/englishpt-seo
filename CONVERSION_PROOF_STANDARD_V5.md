# CONVERSION PROOF STANDARD V5

기준일: 2026-09-20
상태: REVIEW CANDIDATE / NOT PRODUCTION DEPLOYED

## 목표
V4.2/Life-fit의 고객 공감·정보 구조는 유지하고,
상담 직전 부족했던 판단 근거를 보강한다.

EnglishUp에서 참고하는 것은 다음의 '기능'이다.
- Hero 진단 스냅샷
- 상단 판단 포인트
- 자기와 비슷한 상황을 찾는 장치
- 변화/피드백을 눈에 보이게 하는 장치
- FAQ
- 위험 부담을 낮추는 CTA
- 수업 흐름 공개

문장, 디자인, 후기, 성과 수치, 무료체험 약속은 복제하지 않는다.

## Decision Proof Layer
각 페이지는 타깃에 맞게 아래 5가지를 보여준다.
1. 가져오면 좋은 정보
2. 상담에서 정리할 것
3. 수업을 시작하면 확인할 변화
4. 설명용 피드백 예시
5. 상담 신청과 수업 등록을 구분하는 안내

## 절대 금지
- 가짜 후기
- 검증되지 않은 점수 상승
- 고정 기간 내 결과 약속
- 실제 강사처럼 보이는 가상 프로필
- 실제 제공하지 않는 무료 체험
- 실제 확정되지 않은 시간대 보장

## 실증 Proof 활성화 조건
PROOF_DATA_CONTRACT_V1.json을 통과한 데이터만 렌더한다.
강사/후기/실제수업자료/성과사례는 verified data가 없으면 숨긴다.

## CTA
반복되는 '무료 PT 진단' 한 문구만 쓰지 않는다.
- header: 무료 방향 상담
- hero: 타깃별 상황형 CTA
- final: 무료로 방향 확인하기
- sticky: 무료 방향 상담

## Measurement
CRO_MEASUREMENT_SPEC_V1.json을 기준으로
CTA click → modal open → form start → form submit funnel을 측정한다.

## 상태
현재 V5는 사직동 5개 대표 페이지의 noindex 검수본으로만 운영한다.
전국 생성기 allowlist에는 아직 강제 적용하지 않는다.
