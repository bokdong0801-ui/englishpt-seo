# ENGLISH PT V3.1 · 2026-11-03 최종 GO/HOLD 및 네이버 수집 운영 지침

작성일: 2026-10-28 (Asia/Seoul)
상태: 승인 전, Production 게시 금지. 기술 검사만 자동으로 실행.

## 보존할 정확한 대상
- Domain: https://englishpt.kr
- Netlify Site ID: `98d96cc5-f0b7-4d3d-8072-6476d93e55a3`
- Production 기대 ID / 복구 기준: `6adafef5f2c6d196833683db`
- V3.1 비게시 Draft ID: `6ae06963f085b33a5ee903eb`
- V3.1 Draft title: `ENPT-V3-1-20261027-BYEONGMOKANDONG-7-CORRECTED-NONPUB`
- 검증된 구성: 기존 색인 허용 21,964개 / 기존 noindex 136,607개 / 기존 158,571개 라우트 / 하위 사이트맵 44개 / 대표 이미지 21,964개 / V3.1 신규 지역 허브 18개(noindex).
- 2026-10-28 read-only 실행 증거: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/40636319545
- GSC 대표 56개 read-only 실행 증거: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/40631989607
- 별도 검사 브랜치: `review/enpt-v31-gohold-preflight-20261028`

## 2026-11-03 GO/HOLD 검사 순서 (자동 검사 이후 반드시 사람이 승인)

1. **시작 전 잠금**: Netlify 현재 published_deploy ID가 위 Production 기대 ID와 다른 경우 STOP/HOLD. 사이트 custom_domain `englishpt.kr` 확인.
2. **Draft 검증**: Draft ID·title 정확히 일치하고, `ready`, `published_at=null`, 비게시이며 예기치 못한 Edge 의존성 없음. Draft 상태 변경 시 STOP/HOLD.
3. **원본 무결성**: 기존 158,571 라우트 정책과 해시, indexable 21,964/noindex 136,607, image 21,964 및 기존 Edge·robots·redirect·헤더 설정이 최종 후보와 원본에서 일치하는지 기존 signed SHA 결과 재확인. 증거가 최신 후보를 증명하지 못하면 HOLD. 운영본과 Draft의 모든 파일 바이트를 현 시점에 재검사했다는 주장 금지.
4. **Live GET-only**: Preview 28개 대표 URL, sitemap-index 1개 및 자식 44개, 총 21,964 loc, OG 대표이미지 3개, 상담 폼 정확히 1개 및 `submission_created` 이메일 Hook 최소 1개 검사. 별도의 운영 5개 대표 URL을 GET으로 검증: HTTP 200, 올바른 canonical, indexable에서 noindex 없음.
5. **안전통제**: 자동화/사전검사는 GET-only; POST·PUT·PATCH·DELETE·restore·deploy 명령 금지. 상담폼 실제 제출 반복 금지. 자동으로 색인 요청이나 네이버 제출도 하지 않음.
6. **전제 조건**: 2026-10-28 이후 크롤링·SEO 변경 또는 사용자 측 운영 배포가 존재하면 영향 분석 이전에 GO 금지. GSC 발견됨-미크롤링 수치 자체는 단독 HOLD 원인이 아님. 반복되는 핵심 URL 5xx/404, noindex 누수, 링크 장애는 HOLD.
7. **최종 결론**: 모든 필수 검사가 통과해도 상태는 `TECHNICAL_GO / PRODUCTION_HOLD_PENDING_USER_APPROVAL`. 검사 실행 링크·Production/Draft ID·통과/실패·변경파일 목록·복구 기준을 사용자에게 전달한 뒤 정확한 Draft ID 명시한 별도 Production 게시 승인을 받음.
8. **명시적 승인 이후에만 배포**: 사용자가 승인한 같은 Draft 한 번만 게시. 한 번의 API 요청 후 응답을 잃었을 경우 무조건 재호출하지 말고 현재 published_deploy ID부터 확인. 새 빌드·재업로드·여러 번 복구 호출 금지.
9. **게시 후 검증**: 운영 배포 ID 확인, 메인/과정/학생/역/지역 링크·Canonical·robots·44 sitemap·대표 OG·폼 설정·모바일 진입점 확인. 결함이 발견되면 추가 배포 HOLD, 기존 Production ID 기준 복구 방안 사용자에게 제시하고 별도 승인 전에는 복구 미실행.

## GO/HOLD 자동화 실행
- 2026-10-28 GitHub preflight job ID: `122644005080`, run: `40636319545`.
- 이 검사는 오직 읽기 전용이므로 해당 job의 rerun을 통한 재검증을 사용할 수 있음. 자동화 실행 시 성공 여부/최신 attempt와 Artifacts 확인.
- 독립 ChatGPT 예약 점검은 11월 3일 오전(Asia/Seoul) 중 이 실행을 재검증하고 사용자에게 기술적 GO/HOLD만 보고하도록 별도로 구성.
- GitHub 기본 브랜치에 `schedule`을 추가하여 운영 자동배포가 일어나도록 하지 않음.

## 네이버 Search Advisor: 중복 회피 우선순위
기존 수집 요청 기록이 있는 핵심 6개는 즉시 반복 요청하지 않음: `/`, `/courses.html`, `/student-english.html`, `/english-conversation.html`, `/exam-english.html`, `/stations.html`. 앞선 등록 이력은 요청 등록만 확인되었고 실제 수집·색인 여부는 현재 미확인. `/`는 대표 URL 정책과 redirect/canonical 확인 필요.

아래 새 후보는 모두 기존 56개 GET-only 검사 PASS와 사이트맵 포함 확인 대상. **네이버 URL 검사에서 아직 미수집·미색인이고 이전 제출 내역이 없는 경우에만** 신규 수집 요청. 이미 수집/색인되었거나 요청 대기 중인 경우 건너뛰기.

### 1차 (역 허브 5개)
1. https://englishpt.kr/station-bongcheon.html
2. https://englishpt.kr/station-gangbyeon.html
3. https://englishpt.kr/station-sangildong.html
4. https://englishpt.kr/station-ssangmun.html
5. https://englishpt.kr/station-yeokgok.html

### 2차 (과정별 실제 상세 5개)
6. https://englishpt.kr/station-sinmae-toeic-speaking.html
7. https://englishpt.kr/station-dadaepohang-high-conv.html
8. https://englishpt.kr/station-suwon-duolingo-academy.html
9. https://englishpt.kr/station-cheongu-toefl-academy.html
10. https://englishpt.kr/station-tanhyeon-opic.html

### 제출하지 않을 대상
- 18개 신규 `/regions/` 페이지: V3.1에서는 의도적으로 `noindex,follow` 정책이므로 검색 노출용 수집 요청 금지.
- 개인정보처리방침 및 기타 의도된 noindex 136,607개.
- 이미 등록된 핵심 6개(상태 변경 또는 실질적인 별도 수정이 없는 한 반복 신청 금지).
- `utm_source` 등 쿼리 매개변수가 붙은 URL.

최종 실제 접수는 사용자 명시 승인과 네이버 계정 상 제출 이력을 기준으로 판단. 수집 요청은 우선순위 전달이며 네이버 색인·랭킹 보장 아님.
