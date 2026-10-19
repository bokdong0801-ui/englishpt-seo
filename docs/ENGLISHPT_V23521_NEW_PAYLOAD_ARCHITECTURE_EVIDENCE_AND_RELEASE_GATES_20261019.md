# ENGLISH PT v23.5.2.1 — New payload/Edge architecture, deployment gates, 2026-10-19

## Root cause narrowed

Prior full 180k-file HTML deployment failed AFTER only 6 requested assets finished uploading; Netlify post-processing/finalization waited approximately 85 minutes and canceled. The exact server-side underlying process remains unverified. The original Production remained on deploy ID 6ac4bd517c30220008bb9661.

Netlify docs say tens of thousands of HTML files can take time, and automatic Netlify Form detection parses static HTML during deploy: https://docs.netlify.com/build/configure-builds/troubleshooting-tips/ and https://docs.netlify.com/manage/forms/setup/ .

## NEW full 158,571-page candidate generated OFFLINE and QA PASS

- GitHub all-content full build+QA run https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39210125229 — SUCCESS.
- Actual NEW production-intended candidate Artifact **12167196909**:
  https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39210125229/artifacts/12167196909
- Inner tar.zst **SHA256 0f72556e20ed2e22b45f144b4ccf687937e1b15cedc4d2dd109819fef65db7e8**.
- Exact tar.zst size: **1,180,803,641 bytes**.
- All QA evidence Artifact **12167720683**:
  https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39210125229/artifacts/12167720683
- All **180,800 file bodies SHA1-verified** against original candidate.
- All original **158,571 SEO pages** unchanged in content and visible `/slug.html` URL; physically stored as `/__pages/HH/slug.page` to avoid Netlify scanning each as an HTML file.
- Netlify sees only **4 physically .html files** including one hidden static `englishpt-consultation` form blueprint, plus index, 404 and old nested HTML.
- Indexable **21,964**, noindex **136,607** unchanged per-page HTML meta; 44 sitemap parts plus sitemap index = 21,964 public URLs, no losses.
- PNG files **22,088**, editorial OG 29 dimensions 1200x630, six consultation-page form definitions, pilot.js SHA all PASS.
- Edge function returns `text/html; charset=utf-8` for old visible paths, removes internal raw-payload noindex response header, preserves original per-page meta robots. All **158,571 Edge routes** unit-checked, 1,158 actual mock Response tests and Forms POST bypass PASS.
- Direct physical `.page` and the hidden form blueprint are protected by Netlify `_headers` noindex. Netlify Forms must stay enabled on the final production site to parse the one form blueprint.
- **Not yet proven** for this full site: Netlify server accepting all 180,800 file metadata, production Forms registration and actual email, all 158k live routes, performance/cost of per-page Edge invocations.

## Actual isolated Netlify Review tests (no Production publication)

All tested against separate Review site 803550a8-03af-4776-bc8a-bd0bae85f5c7. Every successful pilot returned actual page HTML (text/html) with public URLs, global Draft noindex, 6 static tutor form HTML definitions, 29 OG PNGs; 39 GET smoke tests passed, 0 failures. No real lead POST occurred.

| Scope | Total files | Static .html | Run | Actual Draft |
|---|---:|---:|---|---|
| 103 original pages | 325 | 3 | [39209518097](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39209518097) PASS | https://enpt23521payload103--englishpt-final-ia-review-bokdong.netlify.app |
| 1,000 original pages | 1,346 | 4 | [39210820124](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39210820124) PASS | https://enpt23521paybench1k--englishpt-final-ia-review-bokdong.netlify.app |
| 5,000 original pages | 5,898 | 4 | [39211043332](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39211043332) PASS | https://enpt23521paybench5k--englishpt-final-ia-review-bokdong.netlify.app |

See original pilot and scoped benchmark build artifacts in runs 39209297306 and 39210594300.

## Full 180,800-file Review Draft gate

A one-time, timeout-bounded **isolated Review site only** operation is being tested from branch release/v23521-PAYLOAD-FULL-REVIEW-DRAFT-ONCE-V2-20261019, run https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39211863539.

Only the extracted Review working copy has forced global noindex and robots.txt Disallow; the frozen full production-intended artifact SHA above remains UNCHANGED.

- If status ready and real live HTTP QA pass, **GO for next separately approved full-site Production-site Draft to verify Netlify Forms detection/notifications. Still NOT approval to publish Production.**
- If Netlify timeout/errored, **HOLD**; no automatic retries. Preserve old live Production and contact Netlify Support with failed ID to inspect backend processing of large non-HTML file manifests.
- Do NOT publish any Review-only forced-noindex build to englishpt.kr.

## Form handling and release safety

Separate Review has Form detection OFF so static form HTML test on Review is not an actual submission test. Production has Form detection ON; real Form registrations and notification email require a controlled Production-site Draft and a separately authorized single test submission. The old 1,791-file Production backup Artifact 12091475871 (SHA256 b490c4a19cb4deb04d3c6dd5927446cbda879991ba581e4654f2d5462686bac5) and current Production deploy ID 6ac4bd517c30220008bb9661 are required rollback gates.

After full site, real form/email and rollback validation: obtain explicit separate Production publication approval. Only then submit verified https://englishpt.kr/sitemap-index.xml to Google Search Console and Naver Search Advisor. Do not index the 136,607 deliberately noindex pages.

**Status until actual full staging result: OFFLINE FULL SITE PASS; REAL 103/1000/5000 REVIEW PASS; PRODUCTION HOLD.**
