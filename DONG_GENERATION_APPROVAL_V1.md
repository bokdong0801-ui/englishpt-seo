# ENGLISH PT DONG GENERATION APPROVAL V1

기준일: 2026-09-18  
상태: LOCKED FOR PILOT QA / NOT PRODUCTION DEPLOYED

## 1. 승인 레퍼런스 8페이지

청운동을 기준으로 아래 8개 역할을 생성기 레퍼런스로 고정한다.

1. 지역 허브: `seoul-jongno-cheongundong.html`
2. 고등학생영어회화: `seoul-jongno-cheongundong-high-conv.html`
3. 중학생영어회화: `seoul-jongno-cheongundong-mid-conv.html`
4. 초등학생영어과외: `seoul-jongno-cheongundong-elem-tutor.html`
5. 대학생영어회화: `seoul-jongno-cheongundong-univ-conv.html`
6. 취준생영어회화: `seoul-jongno-cheongundong-jobseeker-conv.html`
7. 직장인비즈니스영어: `seoul-jongno-cheongundong-biz-business-conv.html`
8. 주부영어회화: `seoul-jongno-cheongundong-housewife-conv.html`

이 8개는 역할/URL/theme/content contract의 기준이며 현재 production root에 배포하는 작업을 의미하지 않는다.

## 2. URL CONTRACT

신규 전국 URL은 DB ID가 아니라 preverified locality slug tokens를 사용한다.

- 지역 허브: `/{region_slug}.html`
- 서비스: `/{region_slug}-{intent_slug}.html`
- `region_slug = sido + meaningful jurisdiction tokens + locality`
- 같은 동명이 다른 관할에 존재하면 상위 jurisdiction token으로 구분
- 같은 관할에서 legal/admin 이름이 같으면 public locality 1개
- 폐지 지역은 신규 indexable URL을 기본 생성하지 않음
- 기존 송현동 URL은 변경하지 않음

예:
- `/seoul-jongno-cheongundong.html`
- `/seoul-jongno-cheongundong-high-conv.html`
- `/seoul-seocho-naegokdong.html`
- `/gangwon-gangneung-naegokdong.html`
- `/sejong-goundong.html`

렌더 시 임의 romanization을 만들지 않는다. locality manifest가 slug tokens를 소유한다.

## 3. CONTENT CONTRACT

### mid-conv
핵심: 실제 말하기·듣기·질문 대응·문장 확장·말하기 수행평가.  
내신 문제풀이/문법 문제풀이는 supporting 또는 별도 tutor intent로 분리한다.

### high-conv
핵심: 수행평가 발표·의견 설명·추가 질문 대응·즉답·바꿔 말하기.  
내신/모의고사/수능 문제풀이는 별도 high tutor/school/suneung intent로 분리한다.

### elem-tutor
기초·읽기·어휘·학교영어·말하기 자신감·학습 루틴.

### univ-conv
캠퍼스 대화·발표·세미나 질문·교환학생·공인영어·진로 장면.

### jobseeker-conv
자기소개·지원동기·STAR·꼬리질문·영어면접·채용 일정.

### biz-business-conv
회의·발표·제안·협상·고객/이해관계자 대응.

### housewife-conv
생활영어·여행·영어 재시작·짧은 루틴·질문 이어가기.

서비스명과 실제 본문 intent가 다르면 생성 실패다.

## 4. THEME CONTRACT

- region hub → `theme-local + page-role-region`
- elem → `theme-elem`
- mid → `theme-mid`
- high → `theme-high`
- univ → `theme-univ`
- job → `theme-job`
- worker → `theme-worker`
- housewife → `theme-housewife`

지역 계층 깊이는 전체 색상 변경으로 표현하지 않는다. 지역 페이지는 중립 ENGLISH PT theme를 유지하고 대상 카드에서 목적지 accent만 preview한다.

## 5. STRUCTURAL PILOT

V5 exact relation을 사용해 다음 5개 동을 구조 테스트했다.

1. 서울특별시 서초구 내곡동 — same-name legal + admin
2. 강원특별자치도 강릉시 내곡동 — same visible name in another jurisdiction
3. 강원특별자치도 강릉시 강남동 — admin-only visible locality
4. 세종특별자치시 고운동 — special city hierarchy
5. 부산광역시 해운대구 중동 — legal dong with different related admin names

각 지역은 hub 1 + representative service 1로 총 10개 구조 파일을 생성해 QA했다.

결과:
- approval pages 8/8 PASS
- pilot localities 5/5 PASS
- pilot HTML 10/10 PASS
- pilot canonical 10 unique
- broken relative links 0
- stale Cheongun/Jongno source tokens 0
- theme mismatch 0
- JSON-LD area mismatch 0
- visible DB internals 0
- FAQPage schema 0

## 6. PILOT SAFETY

구조 파일럿은 반드시:
- `noindex,nofollow`
- live lead submission disabled
- sitemap 미포함
- production deploy 금지

파일럿은 승인 blueprint를 이용한 URL/resolver/theme/schema/link 테스트다. 지역명만 바꾼 파일을 production indexable 콘텐츠로 승격하지 않는다.

## 7. PRODUCTION HARD GATE

실제 indexable 동 페이지 생성 전에 모두 필요하다.

1. 전국 5,213 search locality slug manifest 및 collision QA
2. CURRENT/public-locality status gate
3. intent CORE/approved-CONDITIONAL gate
4. locality별 content variation layer
5. audience blueprint variants
6. duplicate similarity threshold
7. real internal-link existence check
8. title/H1/canonical/schema consistency
9. existing 95 URLs + 74 redirects regression
10. sitemap/canonical/redirect QA
11. production shared lead-form binding
12. explicit production approval

이 조건을 통과하기 전 전국 대량 생성 및 indexable 승격을 금지한다.
