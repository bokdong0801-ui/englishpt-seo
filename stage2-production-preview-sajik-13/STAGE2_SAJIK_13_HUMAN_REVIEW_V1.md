# Stage 2 Sajikdong 13-Intent Human Review V1

기준일: 2026-09-22
상태: HUMAN_REVIEW_PASS_USER_REVIEW_PENDING_NOT_PRODUCTION

## 범위
서울특별시 종로구 사직동 1개 production locality row를 사용해 생성한 13개 페이지를 검수했다.

- 7 service intents
- 6 exam intents
- 총 13 pages

대표 직접 검수:
- 사직동 초등학생영어과외
- 사직동 대학생영어회화
- 사직동 토익과외
- 사직동 아이엘츠과외

## 자동 QA
- Static: PASS
- page_count: 13
- visible text: 6,541 ~ 7,211자
- failures: 0
- Render: PASS
- desktop: 13/13
- mobile: 13/13
- horizontal overflow: 0
- console/page errors: 0

## 사람 검수에서 발견하고 수정한 결함
초기 preview의 시험형 공식정보 문장에 `이 배포 전 검수 페이지은`이라는 조사 오류가 있었다.

조치:
- generator postprocess를 `이 배포 전 검수 페이지는`으로 수정
- `페이지은`을 malformed Korean QA에 추가
- 13페이지 전체 재생성
- PC 13 + mobile 13 = 26-render 재실행
- 최종 PASS

## 대표 페이지 판정

### 사직동 초등학생영어과외
PASS.
읽기 / 뜻 설명 / 기억 / 직접 사용을 분리하고, 학부모가 확인할 수 있는 행동과 다음 수업 재확인 기준이 연결된다.

### 사직동 대학생영어회화
PASS.
발표 Q&A / 세미나 의견 / 팀프로젝트 / 교환학생 장면이 구분되고, 공인시험·취업면접과의 boundary가 유지된다.

### 사직동 토익과외
PASS.
LC / Part 5·6 / Part 7 / 실전 점수 변동을 병목 단위로 나누며, 문제량보다 오답 원인·시간 배분·새 세트 재검증을 중심으로 한다.

### 사직동 아이엘츠과외
PASS.
Listening / Reading / Writing / Speaking을 따로 보고 Overall Band 하나로 묶지 않는다. Writing 재작성, Speaking 새 질문, Reading·Listening 근거 기록이 분리되어 있다.

## Stage 2 결론
STATIC PASS
RENDER PASS
HUMAN REVIEW PASS
USER REVIEW PENDING

Stage 3 10-locality × 13-intent = 130 pages로 자동 승격하지 않는다.
사용자에게 13개 목록과 대표 본문 예시를 먼저 보여준 뒤 사용자 검토를 받는다.

production_deploy: false
main_merge: false
sitemap: false
robots: noindex,nofollow
