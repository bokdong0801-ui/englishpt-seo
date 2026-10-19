# ENGLISH PT v23.5.2.1 — Small Review Draft PASS / Full-scale processing HOLD

Verified 2026-10-19 KST. The one-time user-approved 324-file diagnostic Draft **succeeded**, and current englishpt.kr Production remained unchanged.

## Actual successful evidence

- GitHub Action run: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39207370312 — completed **SUCCESS**.
- Draft deploy ID: `6ad5b1f18f8a0e9fbe6fb0b3`, **state ready**, `published_at=null`, context branch-deploy, zero errors.
- Actual browseable Draft: https://enptv23521tinyonce19--englishpt-final-ia-review-bokdong.netlify.app
- Detailed archived CLI/API/HTTP evidence Artifact ID **12165933732**: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39207370312/artifacts/12165933732
- Full small test package SHA256 `ef22d14e56c28a950dad5fd951d67c32856fef36a176408967e1857b32604d47`.
- Small pilot had 324 regular source files, 105 HTML, six actual tutoring static Netlify Forms, bundled actual Netlify Edge router, 141 PNG, globally enforced `X-Robots-Tag: noindex`, `robots.txt Disallow: /`. It **is not a replacement for full Production**.
- Before upload: SHA PASS, Review site ID `803550a8-03af-4776-bc8a-bd0bae85f5c7` PASS, old published Production deploy `6ac4bd517c30220008bb9661` PASS, Netlify credits 1000 remaining at precheck.
- Netlify CLI version 27.13.0, installed and options checked before upload; command had **no `--prod` and no `--context`**.
- Actual CLI: ~06:00:18 UTC prepared 322 static files/3 Edge metadata functions; ~06:00:19 requested **2 files + 1 Edge**, upload of 3 assets completed ~06:00:20; **Draft URL returned at 06:00:21**. This is in sharp contrast with the ~85m wait-to-go-live timeout on 180,797 static-file FULL Draft.
- HTTP QA: **39 GET-only validations** PASS, errors 0, including seven sample HTML/public routes (six tutor forms), `robots.txt`, SHA-verified `pilot.js`, **29 editorial OG PNG 1200×630**. All sample HTML had canonical and Draft `X-Robots-Tag:noindex` as required. No POST, no real form/email receipt test.
- Production `englishpt.kr` still published `6ac4bd517c30220008bb9661`; separate Review project's published deploy ID remained null. **Neither site was published or altered in Production**.
- Real small Preview/test proves CLI, Edge bundle and static routing can succeed at low file counts. It does not prove the full giant package can be posted or that Netlify's internal HTML Form scanning specifically caused the failure.

## Contrast with canceled full deploy

- Full sharded source package: **180,799 files**; CLI declares 180,797 static files plus Edge function assets, **158,574 HTML files**.
- Last failed full Draft run https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39197077688: CDN requested only **5 files + 1 Edge function**, all uploaded at 04:00:12 UTC, and Netlify backend did not make the Draft ready during the next 85 minutes; eventual canceled deploy ID `6ad59585ca10712de65abef7`.
- Successful small pilot: Netlify requested only 2 files + 1 Edge function and became ready ~1 second after upload.
- Most strongly supported finding: bottleneck scales with huge Netlify deploy **server-side processing of many file entries/HTML**, not upload bandwidth. Need platform trace to identify whether Forms detection, per-site limits, header/redirect processing, processing of thousands of OGs, or another mechanism is the dominant factor.

## Release path from here — separate authorization required for further Netlify actions

1. Prepare an alternative FULL-coverage delivery plan that avoids asking Netlify to postprocess 158,574 HTML files per atomic deploy. **Do not silently omit the 136,607 intentionally noindex pages or change their public URLs**. Options include edge/dynamic rendering of secondary routes or separate service for noindex pages with proper canonical/404 and navigation testing.
2. Consult Netlify Support with site `98d96cc5-f0b7-4d3d-8072-6476d93e55a3`, failed draft `6ad59585ca10712de65abef7`, CLI 27.13.0, successful small Draft `6ad5b1f18f8a0e9fbe6fb0b3`. Request timing traces of Form detection and finalization. New Netlify account credits cannot rule out a backend processing limit.
3. Before requesting any larger Draft, bench a middle-size isolated candidate under the same build configuration (e.g. 1,000, then 5,000 pages) with bounded test time; **only with user authorization**. Measure processing time as a function of file count to determine safe publishing architecture.
4. Ensure the real Production consultation form is registered and email notification delivered under an approved end-to-end test; this small Review has disabled Netlify Form detection and the QA only inspected HTML.
5. Publish `englishpt.kr` only once the new full-coverage delivery plan has passed actual Netlify runtime, SEO, Forms and rollback QA and user separately approves it. Submit Google/Naver sitemaps only after successful live Production publication.

**Current disposition: GO / small standalone Review Draft QA; HOLD / full Production release and search-engine registration.**
