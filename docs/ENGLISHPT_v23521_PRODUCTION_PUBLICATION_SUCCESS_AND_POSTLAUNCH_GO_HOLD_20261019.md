# ENGLISH PT v23.5.2.1 — PRODUCTION PUBLISHED SUCCESS

Verified 2026-10-19 17:12 KST (08:12 UTC). The user explicitly authorized exactly **ONE Production publication**. All executions finished and the site's live Production points to the new approved release.

## Immutable evidence

- [GitHub workflow #39220944427](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39220944427) **SUCCESS** (16 steps successful, no failed).
- [Downloaded full immutable release audit Artifact 12171926558](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39220944427/artifacts/12171926558).
- Netlify **Production site ID** `98d96cc5-f0b7-4d3d-8072-6476d93e55a3`; domain https://englishpt.kr/.
- Netlify **prior published** `6ac4bd517c30220008bb9661` (restore/rollback reference retained).
- Netlify **new published** `6ad5ca0f1f2051f04bdd9287`. API GET confirmed `site.published_deploy.id` exactly equals approved target.
- Exactly **1 Netlify POST** (`POST /api/v1/sites/{site_id}/deploys/{deploy_id}/restore`), HTTP **200**, completed at ~08:12:31 UTC; no newly uploaded files, no netlify-cli deploy retry.
- Before POST: original full 1,791-file rollback ZIP SHA256 `b490c4a19cb4deb04d3c6dd5927446cbda879991ba581e4654f2d5462686bac5` with ZIP CRC PASS; new candidate SHA256 `0f72556e20ed2e22b45f144b4ccf687937e1b15cedc4d2dd109819fef65db7e8` PASS; old deploy ready, target Draft ready and unpublished, Form detection enabled, ordinary credits remaining 1,000.

## Actual public Production POST-launch QA

- **62 GET-only HTTPS tests, zero errors**, status `PASS_LIVE_ENGLISHPT_MIXED_INDEX_ROBOTS_CANONICAL_FORMS_OG`.
- 30 sampled real HTML routes have HTTP 200, HTML Content-Type and canonical `https://englishpt.kr/{original-path}.html`.
- Of them, 12 intended indexable pages had correct indexable meta robots; 18 intentionally noindex samples retained their policy.
- No incorrect **X-Robots-Tag: noindex** on intended-indexable pages.
- **6/6** real tutoring consultation forms' static HTML preserved; actual live Netlify `englishpt-consultation` registration confirmed via GET.
- All **29 editorial 1200x630 OG PNG**, patched `pilot.js` SHA256 `d604994a74352a81978002fd6f6286c7d0f4f4c99278745bbf6dad1abce29ede`, live robots.txt and sitemap-index.xml verified.
- Netlify API identified **1 `email` `submission_created` hook**; **real form POST and inbox receipt were NOT tested**, therefore email delivery is not claimed.
- Earlier full offline SHA1 validation covered **180,800 files**, **158,571 public SEO page routes**, **21,964 indexable**, **136,607 noindex**, sitemap 44 shards + index, 22,088 PNG. Real live HTTP checks were representative samples, not 158,571 GETs.

## Final state and remaining work

**Production publication GO: COMPLETE.** The release is live at https://englishpt.kr/.

**Still needed:**
1. With user permission and a verified test recipient and consent, submit **one real Netlify consultation form** on Production and confirm actual email delivery; GET metadata does not prove receipt.
2. Search-engine discovery: submit `https://englishpt.kr/sitemap-index.xml` to Google Search Console and Naver Search Advisor via authenticated service access. This has NOT been done in the publication workflow, nor have their UIs or credentials been used.
3. Monitor Google Search Console/Naver indexing status in following days; URL indexing is not instant and not guaranteed by sitemap submission.
4. Keep previous deploy ID `6ac4bd517c30220008bb9661` and portable backup ZIP available; **no rollback happened or was necessary**.

This note documents the completed user-authorized one-time publication. It does not launch further Netlify deploys, form submissions or Google/Naver actions.
