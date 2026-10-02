ENGLISH PT / NETLIFY-READY RELEASE
Updated: 2026-09-30

STATUS
- Existing preserved content pages: 95
- New Stage 5 pages: 66,937
- Final deploy HTML total: 67,032
- Legacy permanent redirects: 74
- GitHub repository: bokdong0801-ui/englishpt-seo
- Planned host: Netlify
- Final production domain: https://englishpt.kr
- Final domain status: CONFIRMED
- Stage 6 global cross-shard QA: PASS
- Stage 7 deploy preview / rollback gate: PASS
- Public production deployment: NOT YET EXECUTED
- Main branch merge: NOT YET EXECUTED

NETLIFY SETUP
- netlify.toml publishes the repository root as a static site.
- _redirects contains the root redirect and 74 legacy URL permanent redirects.
- No build framework is required; this is a static HTML/CSS/JS site.
- Canonical, sitemap and robots production host is locked to https://englishpt.kr.
- Stage 7 rollback baseline is packaged before any public bulk release.

CURRENT RELEASE GATE
1) Final domain confirmed: https://englishpt.kr
2) Canonical host check: required for all 67,032 deploy URLs
3) Stage 6 duplicate QA: PASS
4) Stage 7 preview / rollback QA: PASS
5) Next gate: Stage 8 explicit production approval
6) Production deploy remains false until the explicit production step is executed
7) Main merge remains false until the explicit production step is executed

PRODUCTION CHECKLIST AFTER EXPLICIT APPROVAL
1) Assemble the proven 26-shard release set and preserved 95-page baseline
2) Publish final sitemap-index.xml and sitemap shards for https://englishpt.kr
3) Publish production robots.txt with Sitemap: https://englishpt.kr/sitemap-index.xml
4) Preserve 74 permanent redirects and / -> /englishpt.html
5) Deploy to Netlify production
6) Attach/verify englishpt.kr and HTTPS
7) Verify representative pages, CSS/JS assets and redirects
8) Test one real EmailJS lead submission
9) Submit sitemap-index.xml to Google Search Console only after live HTTP verification
10) Keep the rollback package available until post-deploy verification is complete

IMPORTANT
- Visible FAQ content is retained; FAQPage schema is intentionally omitted.
- Illustrative cases are labeled as illustrative rather than testimonials.
- The original backup folder from the prior project was not modified.
- GitHub Pages is not the intended production host because this migration relies on server-side permanent redirects.
