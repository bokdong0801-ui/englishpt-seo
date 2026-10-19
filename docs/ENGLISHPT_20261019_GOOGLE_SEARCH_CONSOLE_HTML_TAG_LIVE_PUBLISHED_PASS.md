# ENGLISH PT v23.5.2.1 — Google Search Console HTML ownership meta LIVE, ready for user verification

Verified 2026-10-19 18:34 KST (09:34Z). The user explicitly approved **ONE** publication of immutable previously validated GSC-tagged Netlify Draft. **Production publication succeeded**. Google Search Console's "Verify ownership" button has not been clicked, and Google/Naver sitemap submissions remain pending.

## Netlify publication evidence

- [Approved GitHub publication workflow #39230662553](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39230662553): Netlify restore POST invoked **once**, API returned HTTP **200**; authenticated GET confirmed `published_deploy.id=6ad5dce289bf03bfba2b534c`.
- Prior production deploy remains rollback ID `6ad5ca0f1f2051f04bdd9287`, older restore candidate `6ac4bd517c30220008bb9661` and independently verified backup ZIP preserved. Exact source SHA256 `3ee78c417da2a91bc6f86d2cfd0c4be6c196334a0eaa89a222d99e83365a2acb`.
- The publication workflow itself reported failure because its **postpublication metadata check contained the PREVIOUS target ID**, not because the Netlify publication failed. No retries were issued. A newly created GET-only independent audit fully corrected the follow-up result.

## Independent live GET-only validation PASS

- [GitHub GET-only audit #39231047907](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39231047907) — **SUCCESS, 14/14 steps**.
- [Download audit JSON Artifact 12176912281](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39231047907/artifacts/12176912281).
- The exact token **`<meta name="google-site-verification" content="OTG-5ooTZYTm-HnTOi8I0TRV4bZHUD-uSYSOih3E8ig" />`** is in the returned `<head>` of BOTH https://englishpt.kr/index.html and https://englishpt.kr/englishpt.html, exactly once; both HTTP 200.
- `https://englishpt.kr/robots.txt` and `https://englishpt.kr/sitemap-index.xml` HTTP 200.
- 62 live production GETs: 12 indexable plus 18 intentionally noindex URL samples (30 real original page URLs) correct canonical, per-page robots and no accidental global X-Robots noindex; six tutor consultation Forms HTML; 29 OG PNG 1200×630. Zero HTTP QA errors.
- Netlify `englishpt-consultation` form registered and one `submission_created` email Hook still configured. Existing earlier real test Form submission and Naver inbox arrival were verified by the user; **not retested or resubmitted here**.
- Source patch only modified `index.html` and `__pages/23/englishpt.page`; all other 180,798 files SHA1 identical. 158,571 original routes and 21,964 sitemap-indexable URL policy unchanged.

## Google Search Console manual action

1. Open https://search.google.com/search-console under the Google account holding the URL-prefix property **`https://englishpt.kr/`**.
2. Under HTML-tag verification, click **확인 (Verify)**. The site is now live with the exact code in both entry and canonical homepage head, so it is technically ready.
3. Once Google reports ownership verified, use **색인 생성 > Sitemaps** and submit `sitemap-index.xml` (full URL: https://englishpt.kr/sitemap-index.xml). Record Google UI success and status; submission itself does not instantly index 21,964 pages.
4. Naver Search Advisor must be separately configured and sitemap submitted after verifying the site ownership.

**Final status:** Netlify Production live + exact Google meta PASS; **Google ownership verification and both Google/Naver sitemap submissions NOT YET PERFORMED**.
