# ENGLISH PT — full site Review is now READY; next Production GO/HOLD

Verified 2026-10-19 KST. **Do not deploy or index until explicitly approved and Production-specific QA is complete.**

## New decisive evidence found while preparing 1,000/5,000 page capacity tests

- SUCCESSFUL full-size isolated Netlify Review [GitHub run 39211863539](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39211863539).
- Actual Review Draft ID `6ad5bd194b108d5fa1bc1eac`, status `ready`, published_at null.
- [Review draft preview](https://enpt23521fullpayloadrev2--englishpt-final-ia-review-bokdong.netlify.app)
- [Detailed HTTP + CLI evidence Artifact 12167433778](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39211863539/artifacts/12167433778)
- GET-only live QA: 30 sampled pages HTTP 200 with proper canonical and static Forms HTML, 29 editorial OG images, correct pilot.js; zero errors, globally protected draft `noindex` and HTML Content-Type.
- **Key architectural change:** 158,571 original SEO page HTML bytes remain intact but saved as `.page` payloads; Netlify scans only 4 static HTML files. Actual Edge router returns the same public original `.html` URLs and correct `text/html` response. Full Review passed quickly.
- Distinguish the **Review extraction-only transform** from the original pre-Review candidate. The Review workflow forcibly added global `X-Robots-Tag: noindex`, robots Disallow and Edge public noindex. DO NOT publish the already-loaded Review deployment to Production.

## Actual full-site production candidate already frozen

- GitHub offline full payload creation + complete QA [run 39210125229](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39210125229): **SUCCESS**.
- [Actual Production-formatted candidate Artifact 12167196909](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39210125229/artifacts/12167196909)
- Actual frozen archive SHA256 `0f72556e20ed2e22b45f144b4ccf687937e1b15cedc4d2dd109819fef65db7e8`; 180,800 files and 158,571 page payloads.
- [All 180,800-file SHA1, 158,571 SEO pages, sitemap 44 + index, PNG 22,088 and Netlify Forms static blueprint QA Artifact 12167720683](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39210125229/artifacts/12167720683).
- Public indexable pages 21,964; intentional noindex pages 136,607. Source page robots/canonical original HTML preserved. Production candidate's edge intentionally clears the header noindex applicable to direct .page assets; a global Draft noindex must NOT be merged into it.
- The Production formatted candidate has one static `__internal/consultation-blueprint.html` Netlify Forms blueprint. The Preview test used a Review site with form detection OFF. Before any live Production cutover, actual Forms registration on Production and one authorized inbox test must be validated.

## Parallel capacity tiers — OFFLINE PASS, no further Netlify uploads

- [Tiered 1,000 and 5,000 candidate run 39215232862](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39215232862) PASS, [file Artifact 12169531819](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39215232862/artifacts/12169531819). Samples are SHA1-preserved, globally noindex, contain Edge and Forms HTML.
- **No staged uploads are recommended now** because full-scale Review is confirmed ready. Further small Draft tests would be duplicative and consume credits/time.

## Mandatory Production GO/HOLD before actual publication

1. Read-only recheck current Production `englishpt.kr` Netlify site ID `98d96cc5-f0b7-4d3d-8072-6476d93e55a3`, old currently published deploy `6ac4bd517c30220008bb9661`; stop on any drift.
2. Verify old full portable ZIP backup SHA256 `b490c4a19cb4deb04d3c6dd5927446cbda879991ba581e4654f2d5462686bac5` (Artifact `12091475871`) is intact, stored separately, and restore target remains available.
3. Verify newly frozen Production candidate SHA `0f72556e20ed2e22b45f144b4ccf687937e1b15cedc4d2dd109819fef65db7e8` and prove absence of Review-global noindex, `robots.txt Disallow: /` leakage; verify 21,964 intended-index URLs, 136,607 noindex, sitemap 21,964, 301/404 and file paths.
4. Verify current Netlify credits, forms detection enabled, expected `englishpt-consultation` registration and email notification. Preview pass of form *markup* is not actual Forms email delivery.
5. Prepare controlled Production site **Draft** with the exact production-formatted candidate only with separate permission; run live checks of indexable and noindex responses on that Draft. Never publish globally noindexed Preview. Keep the previous Production immutable deploy as rollback.
6. Only on a fresh, explicit user approval of Publication (not merely testing), publish the validated deploy and verify Production `published_deploy.id` new value; perform GET-only smoke first, a separate authorized form POST/email test, then submit sitemap to Google Search Console / Naver Search Advisor where authorized app access exists.

Current result: **FULL REVIEW TECHNICAL GO; PRODUCTION HOLD awaiting Production-specific gates and explicit publication authorization.**
