# SAJIKDONG 8-PAGE QA V1

기준일: 2026-09-18  
상태: **READY_FOR_DEPLOY_REVIEW_NOT_DEPLOYED**

## 범위

사직동 지역 허브 + 고등 + 중등 + 초등 + 대학생 + 취준생 + 직장인 + 주부 총 8페이지를 noindex 상태로 검수했다.

## 결과

- structure/schema/theme/internal-link QA: PASS
- 실패 0 / 경고 0
- title / H1 / canonical 각 1개
- JSON-LD areaServed: 서울특별시 종로구 사직동
- broken relative links: 0
- Cheongundong/Songhyeondong stale token: 0
- FAQPage schema: 0
- visible DB internal field: 0

## 청운동 동일 intent 교차 중복

8개 모두 PASS, review warning 0.

- hub core cosine 0.4042
- high-conv 0.5526
- mid-conv 0.5742
- elem-tutor 0.5610
- univ-conv 0.5690
- jobseeker-conv 0.5686
- biz-business-conv 0.5892
- housewife-conv 0.5923

FAIL 기준은 core cosine >= 0.88, shingle Jaccard >= 0.78, intro cosine >= 0.93이다.

## Chromium 렌더

- desktop 8 / mobile 8 = 16 renders
- render QA: PASS
- horizontal overflow 0
- console/page error 0
- 상담 모달 open/close smoke test PASS

## 안전 상태

- noindex,nofollow 유지
- 실제 lead submission 비활성
- sitemap 미등록
- main merge 안 함
- production deploy 안 함

다음 gate는 shared assets 결합 -> 기존 95 URL/redirect 회귀검사 -> Netlify deploy preview -> sitemap/canonical 최종검사 -> 명시적 production 승인 순서다.
