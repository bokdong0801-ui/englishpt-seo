# ENGLISH PT v23.5.2.1 — Production GO/HOLD, rollback & post-launch playbook

Version: 2026-10-17. **No Production deploy has been authorized or performed in this preparation.**

## Immutable candidate and provenance

- Offline candidate source GitHub Actions run: [38992648694](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/38992648694)
- Artifact ID: `12085981996`; filename: `ENGLISHPT_v23.5.2.1_JSFIX_PRODUCTION_READY_NOT_DEPLOYED.tar.zst`; packaged size about 1.23 GB.
- New archive SHA256: `e06c6a7b33a3042c9c52e73e95f1ed8a25819dde8584873f939fa14cff9c4bba`.
- Corrected shared `pilot.js` SHA256: `d604994a74352a81978002fd6f6286c7d0f4f4c99278745bbf6dad1abce29ede`.
- Offline validation: 158,571 generated pages / 158,573 total HTML including index and 404; 21,964 indexable / 136,607 noindex; sitemap 21,964 URLs; 29 OG PNG; Chromium tutoring form checks 12 and CTA 24, 8 other-course regressions; SEO error count 0.
- Final isolated Review Draft run: [38934554110](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/38934554110) PASS. Review is not Production.
- Obsolete: **Do not deploy** old Production artifact from run 38903769454; it contains unpatched JS.

## Confirmed LIVE read-only findings

GitHub Actions [38999946448](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/38999946448) and sanitized evidence [39000032216](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39000032216).

- Netlify Production site UUID: `98d96cc5-f0b7-4d3d-8072-6476d93e55a3`.
- Published deploy ID at 2026-10-17 inspection: `6ac4bd517c30220008bb9661`. It was verified from Netlify `GET /api/v1/sites/englishpt.kr` and its individual deploy record; state `ready`.
- **Backup achieved:** immutable *restore-point metadata*, stored in GitHub Artifact `12088532792` / `ROLLBACK_PUBLISHED_DEPLOY_POINT.json`. This is **not an exported complete backup** of site files. Do not delete/prune this deployed revision while it may be needed.
- Netlify account status `in_operational_mode=false`; `usages_exceeded=[]`, `configurable_limits_exceeded=[]` (the exact cause or remaining deploy credits is not determined).
- Public live HTTP before new release: root /, /englishpt.html, /robots.txt, /sitemap-index.xml returned 200. Newly added /gyeongnam-milyang-naeidong-elem-tutor.html returned 404 because that URL is not yet published in Production.
- Netlify Forms GET succeeded and **returned 0 registered forms total**, not merely an unexpected form name. There is one generic `submission_created` email hook (unscoped). The Netlify production deployment has not registered a working consultation form yet; confirm Netlify Forms detection is enabled before launch and check registration immediately after deploy. Neither form capture nor actual email delivery has been proved.
- Exact sanitized forms evidence: GitHub Actions [39000230995](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39000230995), no submissions or recipient addresses fetched. 

## GO/HOLD gate

| Check | Decision |
| --- | --- |
| Frozen candidate SHA, corrected JS, 158,571 content, sitemap and 29 OG | GO (offline) |
| Review Draft live UI and links | GO (separate nonproduction site) |
| Existing published deploy restore ID captured | GO for metadata-only restore point |
| External portable full production-site backup | NOT DONE (optional; do not confuse with a Netlify restore point) |
| Netlify account can currently upload new Production | **HOLD: in_operational_mode false** |
| Remaining credits/capacity for 1.23 GB deploy | **HOLD: not verified** |
| Expected Netlify Forms registration | **HOLD: 0 forms registered in current Production** |
| Email hook configuration | CONFIGURED, but actual delivery untested |
| Existing deployed baseline HTTP root/sitemap | 200; new unreleased tutor route 404 is expected |
| Production rollback POST privilege | Unverified; cannot test without modifying Production |
| Explicit authorization for Production publication | **NOT GRANTED** |

Overall status: **HOLD**. Do not reinterpret an offline PASS as Production launch permission.

## Release prerequisites

1. Recheck Netlify Team **Usage & billing**; resolve `in_operational_mode=false` and verify actual remaining deployment capacity. The empty `usages_exceeded` array does not itself prove usable deployment credits.
2. Confirm `englishpt.kr` Production site UUID matches `98d96cc5-f0b7-4d3d-8072-6476d93e55a3`; keep the Review site `803550a8-03af-4776-bc8a-bd0bae85f5c7` entirely separate.
3. Confirm correct Netlify Forms detection for `englishpt-consultation` after publication. Form registration differs from configuring email notification hooks.
4. Preserve previous published deploy ID `6ac4bd517c30220008bb9661`, its metadata artifact and Netlify Deploys history. Check that the old deploy still exists immediately before public deploy.
5. Confirm fresh SHA256 matches the exact candidate above. Exclude any obsolete Stage 7 95-page rollback archive and earlier 140,391-page Stage 9 pipeline.
6. Obtain a **new, explicit user approval** for Production deployment; do not infer it from this document or the current prelaunch request.

## Portable backup of OLD published site — separate step NOT YET completed

To create an **independent ZIP backup** of the actual old live site, before releasing the new candidate:
1. Open Netlify **Deploys** for Production site `englishpt.kr`.
2. Open the specific old deploy ID `6ac4bd517c30220008bb9661` (check the ID, not simply the latest deploy).
3. In the deployment detail header select **Download**; wait for ZIP generation, then select **Download ready**.
4. Store that ZIP separately with the site ID, deployment ID and UTC timestamp. Compute its SHA256 and check it can be opened. This backup is **not** already downloaded; the current GitHub artifact is a rollback *pointer* only.
5. Preserve both the downloaded ZIP and Netlify's published deploy reference. Netlify deploy retention/deletion can make old links unavailable, so the independent archive adds protection.

Official instructions: https://docs.netlify.com/deploy/manage-deploys/manage-deploys-overview/#download-all-deployed-files

## Rollback procedure prepared, NOT executed

Prefer restoring the exact previous immutable Netlify deployment, not the outdated 95-page Stage 7 baseline.

**UI**: In Netlify open the `englishpt.kr` site's **Deploys** → find deploy `6ac4bd517c30220008bb9661` → review its timestamp, state and the currently published new deployment → choose **Publish deploy** on the OLD revision to restore. This is a Production change and requires an explicit user action.

**API option for a separately authorized emergency:**

- Endpoint: `POST https://api.netlify.com/api/v1/sites/98d96cc5-f0b7-4d3d-8072-6476d93e55a3/deploys/6ac4bd517c30220008bb9661/restore`
- Read actual current `published_deploy.id` first. Refuse restoration if it does not match the newly released deployment under investigation. Ensure OLD baseline is still available. Do not store access tokens in source or logs.
- After restoration: GET the site, `/englishpt.html`, `/robots.txt`, `/sitemap-index.xml`, old known-working pages and relevant forms; record the new published deployment ID. Do not assume rollback restores form submissions, notification rules, domain billing, or search engine index state.

Reference: [Netlify official API rollback](https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/#restore-deploy-rollback).

## Post-deploy execution order (only AFTER explicit Production approval)

### Gate A — publish verified artifact
- Reconfirm Site UUID and account operational status; compare candidate archive SHA256.
- Capture *fresh* previous published deploy ID again, because it can change.
- Upload **only to Production** after approval, using the final corrected package, never the obsolete Stage 9 workflow.
- Capture new Production deploy ID, context, published timestamp, job logs, and immutable deploy URL.
- If publication fails, do not rerun blindly; confirm whether Netlify site changed. Do not delete the old deploy.

### Gate B — automatic GET-only smoke
- Run `.github/workflows/stage9-v23521-after-prod-get-only-smoke.yml` via **Run workflow** with the *actual new Production deploy ID* and `READ-ONLY-SMOKE` in the separate approval input.
- It verifies the exact published deploy ID, 15 public URLs, JavaScript SHA256, `robots.txt`, sitemap index, 6 tutoring HTML pages, 29 PNG OG, registered Netlify form and email hook.
- It makes **NO POST**, NO deploy, NO real consultation form submission and NO search-engine registration. A failure is **HOLD**, not permission to publish again.
- Check response headers: newly indexable pages must not inherit the global Review `X-Robots-Tag: noindex`. Pages intentionally `noindex` remain noindex.

### Gate C — one explicitly authorized real Netlify form/email test
- Before any real POST, confirm the new site has a registered `englishpt-consultation` form and a `submission_created` email notification hook for the correct form.
- With a distinct, clearly labeled test name (e.g. `ENGLISHPT_QA_YYYYMMDD`) and test-only contact details, submit **one controlled test** on a representative English tutoring route. Do not use real student data.
- Check Netlify Forms for that single test submission, including `requestType=영어과외 상담 신청`, `subject=ENGLISH PT 영어과외 상담 신청`, source URL and school grade text; then verify the recipient received the alert with the correct region and grade.
- If form storage succeeds but no email arrives, treat notification delivery as a separate HOLD. Do not submit multiple tests reflexively. Do not delete real customer submissions.

### Gate D — Search Engine registration (after stable HTTP and lead flow)

**Google Search Console**
- Use property `https://englishpt.kr/` or the verified Domain property matching `englishpt.kr`.
- Submit exactly `https://englishpt.kr/sitemap-index.xml` in **Sitemaps**; avoid registering all 158,571 pages, since only 21,964 are intended for index.
- URL Inspection: main hub, student English hub, course hub and representative indexable URL; check canonical, HTTP, robots indexing decisions.
- Check the Pages indexing and Sitemaps reports after 24 hours and 7 days; indexing is not guaranteed on submission.
- Official guidance: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap

**Naver Search Advisor**
- Verify site ownership and both `robots.txt` and `https://englishpt.kr/sitemap-index.xml` can be fetched by robots.
- Use **요청 > 사이트맵 제출** where accepted. Use **웹페이지 수집** sparingly for representative, intended-index pages only, not all 158,571 or the 136,607 `noindex` pages.
- Track crawling and indexed pages in intervals rather than repeatedly resubmitting identical URLs.
- Official references: https://searchadvisor.naver.com/guide/request-feed and https://searchadvisor.naver.com/guide/request-crawl

### Gate E — rollback conditions
Rollback to prior immutable deploy ID if site-wide 404/canonical/robots errors, site-wide consultation broken, or widespread JS/OG problems remain after publication. First document trigger, newly published deployment ID, and evidence. Roll back only after separate explicit permission except in a separately pre-approved emergency-runbook. Revalidate public HTTP and lead intake afterwards.

## Items this preparation does NOT claim
- Production uploaded/published
- Full portable archive downloaded from the old Production Netlify site
- Actual form submission or email delivery verified
- Google or Naver ownership or sitemap submission completed
- Netlify billing/credits fixed
