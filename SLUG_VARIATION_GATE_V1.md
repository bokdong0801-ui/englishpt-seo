# ENGLISH PT 전국 동 Slug + Variation + Duplicate Gate V1

기준일: 2026-09-18  
상태: PHASE PASS / PRODUCTION NOT DEPLOYED

## 핵심 결과

- resolver/search-locality 후보: 5,213
- 구조상 자동 생성 허용 후보: 5,149
- HOLD: ADMIN_DONG 타입이지만 실제 이름이 `출장소`로 끝나는 후보 64
- V5 합성 상위계층 `전남광주통합특별시` 보정 후보 517
- 최종 `region_slug` 충돌 0
- 기존 95 URL 충돌 0
- variation signature 중복 0

## hierarchy correction

V5의 `전남광주통합특별시`는 public URL에 그대로 사용하지 않는다.
하위 관할이 광주의 5개 구(동구/서구/남구/북구/광산구)이면 `광주광역시`, 그 외 전남 시군이면 `전라남도`로 resolver 단계에서 보정한다.

## landing eligibility

5,213은 resolver 후보 수이며 곧바로 indexable 동 랜딩 수가 아니다.
ADMIN_DONG 중 이름이 출장소로 끝나는 64개는 `HOLD_ADMIN_BRANCH_OFFICE`로 분리한다.
법정동 `세종로`, `신문로1가`처럼 이름이 동으로 끝나지 않아도 LEGAL_DONG인 경우는 자동 제외하지 않는다.

## variation layer

각 locality에는 다음을 고유하게 부여한다.

- variation_pack_id
- content_seed
- intro pattern
- section order
- local context mode
- case frame
- CTA frame
- sentence rhythm
- diagnosis emphasis

5,213개 variation signature 중복은 0이다.

## duplicate gate calibration

- 청운동 승인 8페이지: PASS
- 지역명 단순치환 구조 파일럿 10페이지: 의도대로 FAIL
- variation probe v1: FAIL 후 variation 강화
- variation probe v2~v4: PASS
- v4 자동 failure 0, review warning 2
- warning 2쌍 수동 비교 PASS: shingle Jaccard 0.287 / 0.220, heading signature 상이

임계값을 낮춰 통과시키지 않는다.

## URL contract

- hub: `/{region_slug}.html`
- service: `/{region_slug}-{intent_slug}.html`
- public URL에 DB id/official_code 사용 금지
- slug는 manifest에서 사전 고정하고 render 단계에서 다시 추측하지 않음
- V1 manifest final collision 0

## 다음 실제 배포 후보

첫 public rollout 후보는 여러 지역이 아니라 `서울특별시 종로구 사직동` 1개 지역의 8페이지 완전 클러스터로 제한한다.

이유:
- CURRENT legal + admin same-name locality
- 안정적인 slug `seoul-jongno-sajikdong`
- hierarchy 보정 불필요
- 8페이지 내부링크를 한 지역 안에서 완결 가능
- blast radius가 작음

현재는 후보 manifest만 확정하며 HTML 생성/배포는 아직 하지 않는다.

## 금지 상태

- 전국 5,149/5,213 HTML 대량 생성 금지
- sitemap 대량 추가 금지
- main merge 금지
- production deploy 금지
