# ENGLISH PT v23.5.2.1 — FINAL PRODUCTION APPROVAL PACKET
Date: 2026-10-17. **This document DOES NOT approve or execute the Production deployment.**

## Frozen release (strict)

- Production target: `https://englishpt.kr` — Netlify site ID `98d96cc5-f0b7-4d3d-8072-6476d93e55a3`.
- Isolated Review site: `803550a8-03af-4776-bc8a-bd0bae85f5c7` — MUST NEVER be used as Production.
- Corrected immutable offline candidate GitHub run: [38992648694](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/38992648694).
- Artifact ID: `12085981996`, filename `ENGLISHPT_v23.5.2.1_JSFIX_PRODUCTION_READY_NOT_DEPLOYED.tar.zst`.
- Candidate SHA256: `e06c6a7b33a3042c9c52e73e95f1ed8a25819dde8584873f939fa14cff9c4bba`.
- pilot.js SHA256: `d604994a74352a81978002fd6f6286c7d0f4f4c99278745bbf6dad1abce29ede`.
- Pages: 158,571 generated and 158,573 total HTML; index 21,964; noindex 136,607; sitemap 21,964; OG 29.
- Live nonproduction Review QA: [38934554110](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/38934554110) PASS.
- Obsolete archive from run `38903769454` must NEVER be deployed (shared JS bug).

## Final candidate preapproval READ-ONLY proof (2026-10-17)

- [GitHub run 39002338827](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39002338827) SUCCESS, Artifact `12089318578` (`FINAL_PREAPPROVAL_GO_HOLD.json`).
- Verified exact complete 1.23GB candidate archive SHA256 again before sampling it.
- Actual previous published Production deploy `6ac4bd517c30220008bb9661`: current and `ready`.
- Candidate's exact `pilot.js` SHA256 and absence of global Draft `X-Robots-Tag: noindex`: PASS.
- Six real representative student tutor HTML pages: all 6 contained exactly one static `englishpt-consultation` `method=POST`, Netlify detection markup, `requestType`, `subject`, and hidden `form-name=englishpt-consultation`. PASS.
- Live Netlify `GET /sites/:id/forms`: 0 registered forms on **old** Production. This is not evidence that the *new* candidate lacks valid form markup.
- API `use_forms=null`; no explicit enable/disable state established. **Before authorizing Production, open Netlify site's Forms > Form detection and ensure it is ENABLED**. No live site settings were changed by this audit.
- The verified technical result is `PASS_TECHNICAL_PREAPPROVAL_WITH_EXPLICIT_HOLDS`: all code/SEO/account/rollback checks PASS and independent backup NOW PASS; only confirmation of UI Form detection, final deployment permissions, separate user approval and postdeploy lead-flow verification remain.
- This test did not deploy, submit forms, or alter Production.

## Netlify actual immutable Review deploy FULL content inventory (2026-10-17)

- Immutable Review deploy ID: `6ad2561619f2bc1574990fc9`, state `ready`, Netlify deployed manifest 180,796 files.
- Compared against the frozen final Production candidate by sha-verified archive and exact filename set.
- Original HTML count `158,574`, Netlify Review deployed HTML count `158,574`, **HTML missing `0`**.
- No real static content files are missing; the differences in the generic filename set were directory records, Netlify-processed `_headers`/`_redirects`, and uppercase QA JSON names normalized to lowercase.
- [Full evidence run 39005946939](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39005946939) returned a strict filename-identity failure for these expected transforms. [Normalized read-only verification run 39006124158](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39006124158) passed, artifact `12090534549`.
- Official Netlify documentation still states a limit of `54,000` files per directory; this successful immutable Review manifest contains 158,589 root entries. This conflict remains a **production implementation risk**; do not claim that a different Production deploy is guaranteed to succeed until it actually does.
- NONE of these checks uploaded to Netlify or altered the live site.

## Netlify account (corrected)

- Team: `bokdong0801`, Personal plan, API `credits.included=1000`, `credits.used=0`, computed available `1000`.
- `in_operational_mode=false` is not a limit violation and must not be switched to true.
- `usages_exceeded=[]`; `configurable_limits_exceeded=[]`.
- Team is shared by Review and Production, [verification 39001448213](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39001448213).
- Corrected read-only preflight [39001379598](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39001379598) PASS; **real 1.23 GB production upload was NOT attempted**.

## FINAL synchronized GO/HOLD (2026-10-17 14:28 KST)

- [One-shot final read-only gate 39006399416](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39006399416) SUCCESS, Artifact `12090639594` contains the signed-by-evidence JSON assessment.
- `technical_backup_and_review_gates=PASS`: source SHA, 1,791/1,791 original ZIP backup, Netlify same previous Production deploy ready, 158,574/158,574 HTML in immutable Review, 6 real static tutor Forms, ordinary credits 1,000 balance, no exceeded limits.
- **Overall `HOLD_ONLY_FOR_USER_UI_FORM_DETECTION_AND_EXPLICIT_PRODUCTION_AUTH`.**
- Netlify API site `use_forms=null`; current old Production `GET forms` returned 0 registered forms. The current API cannot verify the Form detection UI toggle.
- Before any Production upload, user must visit [Netlify Production Forms](https://app.netlify.com/sites/englishpt-seo/forms) and ensure **Enable form detection** was selected. If the UI offers **Disable form detection**, detection is already ON and should remain unchanged.
- User should download and retain the validated existing old Production ZIP (Artifact `12091475871`) locally before approval.
- Once UI setting and durable backup are confirmed, request **separate explicit one-time Production approval**. This package contains no deploying workflow trigger. DO NOT deploy from an old Stage 9 workflow.
- Official forms documentation: https://docs.netlify.com/manage/forms/setup/#enable-form-detection

## FULL independent old Production backup VERIFIED (2026-10-17)

- [GET-only verified backup run 39005690268](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39005690268) **PASS**, no site mutations.
- Old production site ID: `98d96cc5-f0b7-4d3d-8072-6476d93e55a3`; exact old published deploy ID: `6ac4bd517c30220008bb9661`; state READY.
- Netlify API original deployed files: **1,791 files**, original size sum **89,042,147 bytes**, **1,791/1,791 raw SHA1 digests verified**.
- Independent ZIP file: `ENGLISHPT_ORIGINAL_PRODUCTION_6ac4bd517c30220008bb9661.zip`, **15,426,238 bytes**, ZIP CRC check PASS, complete path-set equality.
- ZIP SHA256 `b490c4a19cb4deb04d3c6dd5927446cbda879991ba581e4654f2d5462686bac5`.
- GitHub independent full backup Artifact ID **12091475871**; manifest and SHA report Artifact ID **12091032928**. GitHub archives are not permanent; user should download and keep an independent copy.
- **Old no-portable-backup HOLD is resolved.** The restoration pointer `6ac4bd517c30220008bb9661` remains saved and was reverified.
- This was a reconstruction of every original deploy file via Netlify's authenticated GET API; it was not created by clicking Netlify's UI ZIP download and is independently SHA-verified.

## Production rollback baseline

- Current published Production Netlify deploy: `6ac4bd517c30220008bb9661` (`ready` on 2026-10-17).
- Existing restore metadata backup GitHub Artifact `12088532792`; this is NOT an independent full website backup.
- Independent full ZIP has NOW been generated and verified from all 1,791 original deploy files (Artifact 12091475871; see above). User should download and keep a separate durable copy; GitHub's 30-day artifact retention is not permanent.
- Verify the old immutable deploy still exists immediately before new release. Never roll back to the outdated 95-page Stage 7 archive.
- Production restore method if explicitly separately authorized: Netlify previous deploy → **Publish deploy**; verify current ID and page behavior after restoration.

## Form registration risk and handoff

- Read-only GET shows **zero existing registered forms** on current Production; one unscoped `submission_created` email hook exists.
- Netlify must have **Form detection enabled BEFORE the new deploy** in the Production site's Forms UI. Netlify documentation: https://docs.netlify.com/manage/forms/setup/.
- Full candidate contains static HTML tutoring consultation form(s) and fixed JS; verify exact six-page structural QA report in the final preapproval run.
- DO NOT infer registration or email delivery from static HTML. After the new deploy, confirm the `englishpt-consultation` form appears in Netlify Forms and a notification targets it.
- Only after explicit test submission approval, perform ONE clearly labeled test and verify Netlify stored entry and destination inbox. No student personal data in tests.

## STOP / GO (release operator)

Until all are true, Production remains HOLD:
- [ ] Final preapproval read-only run verified old deploy, 6 candidate forms, and latest ordinary credits.
- [x] Old published Production ZIP backup created, its exact 1,791-file content checked, hash recorded, ZIP tested (Artifact 12091475871). **User should download an external copy before release.**
- [ ] Production Form detection ENABLED in Netlify site UI, or independently verified already enabled.
- [ ] Confirm Netlify can accept manual upload to Production site and sufficient credits (GET alone cannot guarantee it).
- [ ] Ensure currently published deploy ID still matches rollback plan.
- [ ] Re-check frozen SHA256 of candidate and no global Draft `X-Robots-Tag: noindex`.
- [ ] **Explicit, separate user authorization for actual `englishpt.kr` Production deployment.**

## After explicit approval (not before)

1. Record current Production `published_deploy.id` as rollback baseline; preserve backup ZIP and artifact.
2. Upload *the frozen corrected archive contents* (not .tar.zst as a Netlify ZIP; unpack first; use Netlify CLI `--dir`, with fully verified target site ID and `--prod` only after approval). Netlify direct ZIP API extraction limit is 25,000 files, so do NOT try to deploy this 158,573-HTML site through a single Netlify ZIP API.
3. Capture new deployed ID and verify it is `ready` and the intended Production published deploy.
4. Run the existing **read-only** GitHub workflow `stage9-v23521-after-prod-get-only-smoke.yml` with new deploy ID and `READ-ONLY-SMOKE`. It verifies 15 public routes, patched pilot.js, 29 OG, Forms registration, headers and sitemap.
5. After *separate* user permission, submit ONE labeled test consultation, check stored Netlify Forms fields, `requestType`, `subject`, region/school grade, then email inbox arrival.
6. Once site and lead flow are stable, verify property ownership and submit `https://englishpt.kr/sitemap-index.xml` in Google Search Console and Naver Search Advisor; do not request indexing for 136,607 intentionally noindex pages.
7. If site-wide HTTP or lead flow fails, coordinate restore of previous immutable deploy ID, log evidence and re-test.

## User approval template — DO NOT auto-send or infer authorization

**If all nonauthorization gates above are verified**, ask the user to write:

`ENGLISH PT v23.5.2.1의 최종 후보 SHA256 e06c6a7b...를 확인했습니다. englishpt.kr Production 운영 배포를 승인합니다. 기존 운영 백업과 롤백 ID를 유지하고 1회만 배포해 주세요.`

This file intentionally contains **no executable Production deploy trigger**. The old Stage 9 workflow built for earlier 140,391-page source is not a valid substitute.

## Supporting sources
- Netlify deploy download and rollback: https://docs.netlify.com/deploy/manage-deploys/manage-deploys-overview/
- Netlify static form detection: https://docs.netlify.com/manage/forms/setup/
- Netlify API direct ZIP deploy max 25,000 files: https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/#zip-file-method
