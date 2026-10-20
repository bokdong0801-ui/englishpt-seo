# ENGLISH PT — Approved Production Publish and Live QA Final Signoff

**Date:** 2026-10-20 23:25 KST  
**Status: PRODUCTION PUBLISHED EXACT APPROVED DRAFT — LIVE QA PASS**

## Atomic publication (exactly once)
- User explicitly approved production publish of **Netlify Draft `6ad7506cdeb778280a54ee2a`** to `https://englishpt.kr`.
- Netlify site ID `98d96cc5-f0b7-4d3d-8072-6476d93e55a3`.
- Exact approved Draft was READY and unpublished at preflight; previous published ID matched approved baseline.
- Per official Netlify API, exactly **ONE** `POST /api/v1/sites/{site_id}/deploys/{deploy_id}/restore` was sent for that exact deploy ID. HTTP **200**, result deploy ID exactly matched `6ad7506cdeb778280a54ee2a`.
- Published site ID was independently read back as **`6ad7506cdeb778280a54ee2a`**. No archive rebuild, file upload, new Draft creation, extra restore call or new Forms test POST.
- Original Production deploy **`6ad5eb4918f9411c4d5e1ba4`** remains retrievable by Netlify API as the **rollback reference**. No automatic rollback attempted.
- Publication action evidence: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39438495712
- Note: publication workflow has a **failed overall conclusion solely due to a post-POST QA script KeyError**. The publish POST had already returned HTTP 200 and exact published ID was confirmed; no retry of the publication call occurred.

## Separate, read-only live Production QA — **PASS**
- Clean follow-up workflow: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39438983911
- Artifact: `ENPT_21964_PRODUCTION_EXACT_DEPLOY_READONLY_POSTLIVE_HTTP_SEO_IMAGE_FORMS_CHROME_390_1440` (90-day retention).
- Six real production pages `/index.html`, `/englishpt.html`, two station exam pages, two tutor pages: HTTP 200 and **byte-for-byte SHA256 identical** to the approved Draft, canonical URLs correct, robots page-level index/noindex correct, no global preview noindex.
- Homepage Google and Naver owner verification meta exactly correct on both homepage representations.
- `robots.txt` and `sitemap-index.xml` exact byte-identical to approved Draft, robots not blanket-disallowed, **44 unique sitemap XML shards**.
- Edge internal `/__pages/23/englishpt.page` remains protected by noindex.
- Two live 1200×1200 square JPEGs actual HTTP 200, `image/jpeg`, SHA256 identical to approved Draft:
  - `732c77f6e84d5cf0d8e4.jpg`: `bbd902eca0c52af5d905ba9036becb9b61d2dc84faac1c110e9c0827aad8d002`
  - `7ae6254c3f7d886231cc.jpg`: `5a4513b3e1bb615f5902ed08eb0e33cc80e86dca56814ecbf00a2a74951dc646`
- Netlify consultation form `englishpt-consultation` still registered, prior exact one synthetic test submission still verified, Naver `submission_created` mail notification hook still configured. **No second test application** was sent in production.
- Real Chrome Production mobile **390px** and desktop **1440px** navigated in-page consultation CTA and confirmed the visible form/name/phone/submit UI. Screenshots stored in evidence artifact.
- Final actual published ID read again **`6ad7506cdeb778280a54ee2a`**, old deploy retrievable, zero remaining QA errors.
- Read-only final status: `PASS_EXACT_USER_APPROVED_DEPLOY_LIVE_HTTP_SEO_SITEMAP_JPEG_FORM_MOBILE_DESKTOP`.

## Earlier exhaustive audit
- Full SEO candidate source: **158,571** original routes, **21,964** indexable OG image map, **136,607** noindex pages original SHA1, 44 sitemap shards, verified owner tags, Forms and Edge router — all offline PASS. Evidence: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39399897235
- Final production-safe nonpublished Draft and 42 live preview routes / 390+1440 screenshots: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39414952403 and https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39416389999
- User personally confirmed Naver test email received in this conversation. The assistant has not directly accessed the mailbox.

**Scope qualification:** 158,571 routes were exhaustively validated offline, not all individually crawled over public HTTP. The postpublish public HTTP tests sampled six HTML pages and two JPEGs. Search engine indexing and snippet/image selection depend on Google/Naver and are not guaranteed.

## Future operational follow-up
- Monitor GSC and Naver Webmaster Tools indexation and 404/5xx crawl anomalies during next days. Only modify SEO after reviewing actual fresh reports and avoiding destabilizing mass re-deploys.
- If an actual production failure emerges, inspect published ID and preserve the old deploy rollback reference. Do not auto-rollback without user approval.
