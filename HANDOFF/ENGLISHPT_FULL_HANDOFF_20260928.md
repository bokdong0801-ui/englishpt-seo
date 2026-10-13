# ENGLISH PT 전국 SEO 대량생성 프로젝트 — 전체 인수인계
기준일: 2026-09-28
현재 단계: Stage 4 완료 / Stage 5 66,937페이지 전체 생성 직전
안전 상태: main merge=false / production_deploy=false / sitemap_live=false

## 새 채팅 첫 작업 지시
이 문서를 기준으로 프로젝트를 이어서 진행한다.
1. GitHub `bokdong0801-ui/englishpt-seo`의 `reset-english-service-seo-v3` 최신 head를 먼저 확인한다.
2. `PRODUCTION_13INTENT_BATCH_PLAN_V1.json`과 Stage 4 QA/Human Review를 확인한다.
3. Stage 4는 100지역×13 intent=1,300페이지까지 PASS 상태다.
4. 회귀가 없으면 이전 Stage를 재설계하지 말고 Stage 5 — 5,149×13=66,937 전체 생성으로 진행한다.
5. 새 디자인/콘텐츠 방향 수정은 중단한다.
6. 각 실행 단계마다 실제 예시페이지를 사용자에게 보여준다.
7. 사용자의 명시 승인 전 main merge/production deploy/index request를 하지 않는다.

## 프로젝트 기본
- 브랜드: ENGLISH PT
- 도메인: englishpt.kr
- 메인 repo: bokdong0801-ui/englishpt-seo
- 지역 DB repo: bokdong0801-ui/korea-region-db
- safe branch: reset-english-service-seo-v3
- 2026-09-28 확인 branch head: c24515ba6228668985b890d422ce173319e0e388
- 기존 보존 URL: 95
- 기존 redirect: 74
- 대표 기존 페이지: dalseo-songhyeondong.html
- 기존 95 URL/74 redirect regression PASS

## 운영 방향
2026-09-22부터 “새 디자인/콘텐츠 방향 수정”이 아니라 “배포 가능한 시스템 만들기” 단계로 전환.
허용 수정: generator/한국어/QA/duplicate/collision/URL/canonical/schema/internal-link/sitemap/redirect/deploy/rollback/package defect.
금지: 새 디자인, 새 content architecture, frozen Gold 임의 변경, production 승인 전 main/deploy.

## 최종 생성 범위
지역:
- resolver candidates 5,213
- production eligible 5,149
- HOLD 64 ADMIN_DONG 출장소
- 5,149 region_slug unique
- 5,149 locality_key unique
- reserved 95 collision 0

13 intents:
1. elem-tutor — {동} 초등학생영어과외
2. mid-conv — {동} 중학생영어회화
3. high-conv — {동} 고등학생영어회화
4. univ-conv — {동} 대학생영어회화
5. jobseeker-conv — {동} 취준생영어회화
6. biz-business-conv — {동} 직장인비즈니스영어
7. housewife-conv — {동} 주부영어회화
8. toeic — {동} 토익과외
9. toeic-speaking — {동} 토익스피킹과외
10. opic — {동} 오픽과외
11. ielts — {동} 아이엘츠과외
12. duolingo — {동} 듀오링고영어테스트
13. toefl — {동} 토플과외

TOS/토스는 TOEIC Speaking alias. standalone TOS page 금지.

최종 신규 페이지:
- 서비스 7: 36,043
- 시험 6: 30,894
- 합계 66,937
- region hub 5,149는 이 batch에 미포함

## URL contract
- service: /{region_slug}-{intent_slug}.html
- future hub: /{region_slug}.html
- place_id/official_code/좌표 public 노출 금지
- render-time romanization 금지
- slug는 preverified manifest가 소유

## V5 지역 DB 핵심
- places 68,790
- relations 127,664
- aliases 62,404
- CURRENT LEGAL_DONG 3,656
- CURRENT ADMIN_DONG 2,220
- current dong entities 5,876
- ABOLISHED LEGAL_DONG 6,660
- ABOLISHED ADMIN_DONG 3,525
- CURRENT ADMINISTERS 4,825
- same-jurisdiction legal/admin merge 663
- 435 valid LEGAL_DONG names do not end with 동

Synthetic hierarchy `전남광주통합특별시`:
- public URL 사용 금지
- 광주 5개 구→광주광역시
- 나머지 전남→전라남도
- correction 후보 517
- final eligible correction 490

## Stage 1 — 5,149 row manifest
PASS.
기록: PRODUCTION_LOCALITY_ROWS_5149_STAGE1_V1.json
원본: ENGLISHPT_slug_variation_gate_FINAL_v1_20260918.zip / dong_slug_manifest_5213_v1.csv
출력:
- production_locality_rows_5149_v1.csv
- production_locality_rows_5149_v1.jsonl
- hold_admin_branch_offices_64_v1.jsonl
- PRODUCTION_LOCALITY_ROWS_5149_QA_V1.json
- ENGLISHPT_PRODUCTION_LOCALITY_ROWS_5149_V1_20260922.zip

checksums:
- CSV b3c91537bb6a95206def1dfb524b1f9790939da0cf7bc31b50cdfae376b3cc4e
- JSONL 3fe392df02bf76e0a6f84ef220433f0b901f97ae09a0a091269deeb2eaf8e9f0
- HOLD 7ab82c7dcdeef3a07a3461c184a247cef86e18b41006e1e3b1808c8ba3751c8b
- ZIP c3d2fd8f52d08442cedef18d5bb2b610b5c1131561f2dce40f36c9c2b770da60

entity mix:
- LEGAL_DONG 2,993
- ADMIN_DONG 1,493
- ADMIN+LEGAL 663

사직동:
- locality_key 서울특별시 종로구|사직동
- slug seoul-jongno-sajikdong
- variation_pack_id Ve4a779a721
- content_seed 76bc829bb4fb1cf9

## Variation contract
각 locality에:
- variation_pack_id
- content_seed
- intro pattern
- section order
- local context mode
- case frame
- CTA frame
- sentence rhythm
- diagnosis emphasis
5,213 variation signature duplicate 0.
지역 사실을 상상하지 않고 설명 방식/순서로 차별화.

## 7-target Gold
Gold Standard: V4_5_FULL_DEPTH_7TARGET_GOLD_STANDARD.md
Freeze: V4_5_GOLD_SAMPLE_FREEZE_20260922.json
5지역×7=35.
Blueprint:
- v4-elem-parent-evidence-v2
- v4-mid-school-bridge-v2
- v4-high-priority-deadline-v2
- v4-univ-campus-output-v2
- v4-job-interview-evidence-v2
- v4-worker-work-output-v2
- v4-housewife-lifefit-v2
QA:
- visible 6,362~6,824, avg 6,551.3
- particle failures 0
- same-intent pairs 70
- max cosine 0.7566
- max 5-shingle 0.2149
- render 70/70 PASS
- human PASS

## 6-exam Gold
Gold Standard: V4_5_FULL_DEPTH_6_EXAM_GOLD_STANDARD.md
Freeze: pilot-v45-exam-5x6/PILOT_EXAM_5X6_GOLD_FREEZE_V1.md
Freeze ID: V4.5-EXAM-5X6-GOLD-SAMPLE-FROZEN
5지역×6=30.
TOEIC / TOEIC Speaking / OPIc / IELTS / DET / TOEFL.
QA:
- visible 6,299~7,137
- pairs 60
- max cosine 0.7871
- max Jaccard 0.2391
- static 0
- TOS standalone 0
- desktop 30/30, mobile 30/30
- run 35693687847
- human PASS

## Hero / CTA
Hero는 지역명+핵심키워드만 짧게.
긴 진단 질문은 Hero 아래.
전화:
- label: 전화 010-5006-8027
- href: tel:+821050068027
Hero CTA:
- 내용 보기
- 상담 신청

## Theme freeze
Neutral #50665B/#9C927D hero #EDEAE2 ink #18211D
Elementary #2F7E86/#78AEBE hero #153E46
Middle #256A74/#536EA7 hero #172F48
High #244967/#A99061 hero #111D2C
University #4C6987/#A9825E hero #17283A
Job #395D68/#B38B5D hero #13252B
Worker #315F4C/#B39A68 hero #101814
Housewife #77816B/#B99479 hero #303A31

## Reference URLs
- https://englishup.kr/ilsan-dong-pungdong-ielts
- https://englishup.kr/giheung-cheongdeokdong-toeic-speaking
- https://englishup.kr/dongjak-sangdodong-toeic
- https://englishup.kr/dongjak-sangdodong-toefl
- https://englishup.kr/dongjak-sangdodong-opic
저장 분석:
- EXAM_REFERENCE_ANALYSIS_V1.md
- REFERENCE_BENCHMARK_ENGLISHUP_MUNGYEONG_V1.md
주의: live HTML을 다시 못 연 시점이 있으므로 source benchmark 기반이라고 구분할 것.

## 사용자 “오른쪽 고친 버전” 선택지원 원칙
관련: PRODUCTION_DECISION_SUPPORT_13INTENT_V1.json
모든 13 intent에:
1. 잘 맞는 경우
2. 다른 선택이 더 나은 경우
3. 비용을 좌우하는 변수
4. 선생님/수업 비교 기준
5. 상담 전 준비자료

## 현재 최종 전환 흐름
Hero
→ 빠른 판단 요약
→ 자기상황 식별
→ 5가지 선택 기준
→ 학습/시험 맥락 이해
→ 판단 가이드
→ 지역별 판단 방식
→ 우선순위
→ 수업 흐름
→ 중간 CTA
→ Decision Proof
→ 피드백 예시
→ FAQ
→ Deep Guide
→ 동일 locality 12개 내부링크
→ 상담 전 체크
→ Final CTA

## 한국어 Hard Rule
조사 helper: 은/는, 이/가, 을/를, 과/와, 이나/나, 으로/로.
금지 예: 대학생영어회화을, 질문 이해과, 문항를, 페이지은, 합니다에서 무엇부터.
실제 수정:
'처음 보는 문장 읽기'을... → 다음 확인 기준으로는 '처음 보는 문장 읽기' 항목을...
Stage 4 최종:
- duplicate PASS 엔진 복원
- 짧은 quoted-label만 particle QA
- escaped quoted-label 교정
- hardcoded '{topic}'은 → dynamic subj_josa(topic)

## Stage 2 — 사직동 1×13
output: stage2-production-preview-sajik-13/
run 35698270506
Static PASS / Render 26/26 / Human PASS.

## Stage 3 — 10×13=130
output: stage3-production-dryrun-10x13/
run 35877014313
- pages 130
- visible 10,244~12,781
- static 0
- pairs 585
- cosine 0.7511
- Jaccard 0.1982
- render 260/260
- human PASS
핵심 교훈: 5 frame만 반복하지 말고 7-axis variation을 실제 서술에 연결.

## Stage 4 — 100×13=1,300
현재 최종 PASS.
output: stage4-preproduction-100x13/
final automated run: 36401775070
source head: 656efa5895f60b873f302e2bb28ef0f64406ccdc
generated output head: 802eb2420481628225f6d5207fd247112d15b2b3

QA:
- 1,300 pages / 100 localities / 13 intents
- static 0
- filenames unique 1,300
- canonicals unique 1,300
- reserved95 conflict 0
- duplicate pairs 64,350
- max cosine 0.8152 <0.82
- max 5-shingle 0.2123 <0.24
- visible 17,790~20,233 avg 18,740.7
Sitemap:
- 1,300 URLs
- shard 500
- 3 shards
- sitemap-stage4-index.xml
- live false
Size:
- HTML 68.31 MiB
- avg 55,099.6 bytes
- 66,937 HTML-only estimate 3.435 GiB
Render:
- sample pages 30
- desktop+mobile 60/60 PASS
- overflow 0
- console/page error 0
- benchmark block 0
- cluster-link 0
Human:
- stage4-preproduction-100x13/STAGE4_100X13_HUMAN_REVIEW_V1.md
- HUMAN_REVIEW_PASS
Shortest:
- daejeon-dong-jusandong-biz-business-conv.html 17,790
Longest:
- gangwon-samcheok-sajikdong-duolingo.html 20,233

## Stage 4 실패/수정 핵심
중간 성공 run 36297945545:
- cosine 0.8157
- Jaccard 0.2125
- render PASS
조사 교정:
- 36298277246 duplicate PASS 0.8159, static 404
- 36298484706 duplicate PASS 0.8159, static 263
- 36298703119 static 0 but cosine 0.8339 FAIL
최종 해법은 duplicate PASS 엔진을 복원하고 quoted-label particle 검사만 정확히 제한하는 것.
최종 run 36401775070 SUCCESS.
Stage 5에서 콘텐츠를 더 늘리지 말 것. 1.7만~2만자면 충분.

## 현재 Production Plan
PRODUCTION_13INTENT_BATCH_PLAN_V1.json
status:
STAGE4_1300_ALL_GATES_HUMAN_PASS_USER_REVIEW_PENDING_NOT_PRODUCTION
next:
USER_REVIEW_STAGE4_EXAMPLES_THEN_STAGE5_FULL_66937_GENERATION
Stage1/2/3/4 모두 PASS.

## Sample Review Policy
PRODUCTION_SAMPLE_REVIEW_POLICY_V1.json
각 단계에서 실제 예시를 보여준 뒤 다음 단계.
Stage 5 sample pack:
- 13 intents×3 regions=39
- deterministic 5 spot
- highest duplicate pair
- shortest/longest
- same-name samples
- page count/collision/QA report

## Stage 5 — 다음 실제 작업
목표: 5,149×13=66,937 HTML.
생성이지 deploy가 아님.
시작:
1. branch/Stage4 회귀 확인
2. Stage4 engine freeze
3. 5,149 manifest 연결
4. artifact/output sharding 설계
5. runtime/disk/artifact 한계 고려
6. full generation
생성 후:
- exact count 66,937
- unique filename/URL/canonical
- H1 exact
- malformed/dynamic particle 0
- JSON-LD parse
- locality 12 internal links
- TOS 0
- 95 collision 0
- 74 redirect regression
- no pilot wording
- sitemap shards
- package size
- duplicate QA
- representative render
- sample pack

Duplicate threshold는 유지:
- cosine <0.82
- 5-shingle <0.24
전체 pair 수가 매우 크므로 scalable QA 계산방식은 새로 설계 가능하나 threshold 자체 완화 금지.

## Stage 5 packaging
Stage4 추정 66,937 HTML-only ≈3.435 GiB.
단일 Git commit에 66,937 HTML 무작정 넣지 말 것.
GitHub Actions artifact, checkout, Netlify size 고려.
sharded artifact/directory 권장.
production root 바로 push 금지.

## Stage 5 이후
Stage6 Full Bulk QA
Stage7 Sitemap/Deploy Preview/Rollback
Stage8 Explicit Production Approval
사용자 승인 전 main/deploy/index 금지.

## 중요 파일
Gold:
- V4_5_FULL_DEPTH_7TARGET_GOLD_STANDARD.md
- V4_5_GOLD_SAMPLE_FREEZE_20260922.json
- V4_7TARGET_BLUEPRINTS.json
- V4_BLUEPRINT_GENERATOR_ALLOWLIST.json
- V4_5_FULL_DEPTH_6_EXAM_GOLD_STANDARD.md
- V4_5_EXAM_BLUEPRINTS.json
- V4_5_EXAM_GENERATOR_ALLOWLIST.json
- pilot-v45-exam-5x6/PILOT_EXAM_5X6_GOLD_FREEZE_V1.md
Production:
- PRODUCTION_66937_STAGE_GATES_V1.md
- PRODUCTION_SAMPLE_REVIEW_POLICY_V1.json
- PRODUCTION_13INTENT_BATCH_PLAN_V1.json
- PRODUCTION_LOCALITY_ROWS_5149_STAGE1_V1.json
- PRODUCTION_DECISION_SUPPORT_13INTENT_V1.json
Region:
- SLUG_VARIATION_GATE_V1.md
- DONG_GENERATION_APPROVAL_V1.md
- DONG_PRODUCTION_BATCH_MANIFEST_V1.json
Generators:
- scripts/generate-v45-full-depth-pilot.py
- scripts/generate-v45-exam-pilot.py
- scripts/generate-production-stage2-sajik-13.py
- scripts/generate-production-stage3-10x13.py
- scripts/generate-production-stage4-100x13.py
- scripts/materialize-stage4-localities-100.py
- scripts/render-production-stage4-100x13.mjs
Workflow:
- .github/workflows/v45-full-depth-generate.yml
- .github/workflows/v45-exam-pilot-render-qa.yml
- .github/workflows/stage2-sajik-13-preview.yml
- .github/workflows/stage4-100x13-preproduction.yml

## 안전 상태
robots noindex,nofollow
live lead false
sitemap live false
production deploy false
main merge false
Stage5 초기 생성에서도 유지.

## 절대 반복 금지
1. Gold 직접 덮어쓰기
2. slug 새 romanization
3. 지역 사실 상상
4. TOS 별도 page
5. 고정 조사 조립
6. 무의미 token/난수로 duplicate 낮추기
7. blind word replacement
8. 공통 문단 추가로 cosine 악화
9. Stage4 이후 분량 증가
10. example review 없이 자동 승격
11. main merge
12. production deploy

## 현재 한 문장 요약
ENGLISH PT는 5,149 검증 지역×13 intent=66,937페이지 전체 생성 직전이며 Stage1/2/3/4가 모두 PASS했다. 다음 작업은 Stage4 구조를 더 수정하지 않고 그대로 Stage5 production-scale generator에 연결해 66,937페이지를 생성·검증하는 것이다.
