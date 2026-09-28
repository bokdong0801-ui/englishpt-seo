# Stage 4 100×13 Human Review V1

기준일: 2026-09-28
상태: HUMAN_REVIEW_PASS_USER_REVIEW_PENDING_NOT_PRODUCTION
production_deploy: false

## 범위
100개 audited locality rows × 13 intents = 1,300페이지

최종 automated workflow:
- run: 36401775070
- source head: 656efa5895f60b873f302e2bb28ef0f64406ccdc
- generated output branch head: 802eb2420481628225f6d5207fd247112d15b2b3

## 자동 QA
- page_count: 1,300
- locality_count: 100
- intent_count: 13
- static failures: 0
- filenames unique: 1,300
- canonicals unique: 1,300
- reserved 95 conflicts: 0
- duplicate comparisons: 64,350
- max cosine: 0.8152 < 0.82
- max 5-shingle Jaccard: 0.2123 < 0.24
- visible text: 17,790 ~ 20,233자
- average visible text: 18,740.7자

## Sitemap prototype
- status: PASS
- URL count: 1,300
- shard size: 500
- shards: 3
- index: sitemap-stage4-index.xml
- live deployment: false

## Package sizing
- Stage 4 HTML: 68.31 MiB
- average HTML: 55,099.6 bytes
- min HTML: 52,783 bytes
- max HTML: 58,465 bytes
- estimated 66,937 HTML-only: 3.435 GiB
- shared assets / sitemap / redirects are not included in this HTML-only estimate

## Browser QA
30 representative pages × desktop/mobile = 60 render cases
- status: PASS
- desktop: 30/30
- mobile: 30/30
- failures: 0
- horizontal overflow: 0
- console/page errors: 0
- benchmark blocks: PASS
- internal cluster links: PASS

## 사람 검수 대표 13개
- 강남동 초등학생영어과외
- 고산동 중학생영어회화
- 상동동 고등학생영어회화
- 선도동 대학생영어회화
- 용봉동 취준생영어회화
- 태평로3가 직장인비즈니스영어
- 월평1동 주부영어회화
- 중동 토익과외
- 면목제5동 토익스피킹과외
- 남목3동 오픽과외
- 청라1동 아이엘츠과외
- 인월동 듀오링고영어테스트
- 초산동 토플과외

13개 대표본에서:
- H1 intent 정확
- concrete decision support 유지
- 동적 조사 오류 없음
- malformed Korean scan 없음
- generic marketing copy 없음
- TOS standalone 없음
- 동일 locality의 나머지 12 intent 내부링크 확인
- 상담 전 체크/중간 CTA/FAQ/Deep Guide 흐름 유지

## 최종 수정 이력
Stage 4 후반 실패는 콘텐츠 구조가 아니라 quoted label 조사 처리와 duplicate threshold의 동시 충족 문제였다.

최종본은:
1. duplicate PASS였던 variation engine을 복원
2. 짧은 quoted-label만 조사 검사
3. HTML-escaped quoted label 조사 교정
4. hard-coded `'{topic}'은`을 `'{topic}'{subj_josa(topic)}`으로 수정

결과:
- static failures 0
- max cosine 0.8152
- max Jaccard 0.2123
- render 60/60 PASS

## 사람 검수 메모
페이지 분량은 1.7만~2만자로 충분히 깊다. 일부 판단 어휘는 장문 안에서 반복되므로 Stage 5에서는 콘텐츠를 더 늘리지 않는다.
Stage 4에서 검증된 구조, Gold facts, decision-support blocks, variation engine과 QA thresholds를 production generator contract로 동결하고 추가 콘텐츠 확장은 중단한다.

## 결론
HUMAN_REVIEW_PASS

Stage 5 전체 66,937페이지 생성 전 사용자에게 Stage 4 예시와 QA 결과를 먼저 보여준다.

main_merge: false
production_deploy: false
sitemap_live: false
robots: noindex,nofollow
