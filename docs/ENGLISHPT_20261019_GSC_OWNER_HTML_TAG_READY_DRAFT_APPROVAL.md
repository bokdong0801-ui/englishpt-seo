# ENGLISH PT — Google Search Console HTML meta ownership tag READY Draft

Prepared 2026-10-19 18:05 KST. **This document does not publish Production, verify Google property, or submit a sitemap.**

## Exact user-provided Google verification token

`<meta name="google-site-verification" content="OTG-5ooTZYTm-HnTOi8I0TRV4bZHUD-uSYSOih3E8ig" />`

The existing site root is a static redirect and the actual homepage is `https://englishpt.kr/englishpt.html` served by the Netlify Edge function from `__pages/23/englishpt.page`. Because Netlify snippet injection is not supported for function routes, the tag was surgically added to both `index.html` and `__pages/23/englishpt.page`, not by injecting scripts or modifying all SEO pages.

## Full 180800-file original-content QA

- Successful offline build and full-site SHA1 QA: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39225996525
- Exact **new** candidate SHA256: `3ee78c417da2a91bc6f86d2cfd0c4be6c196334a0eaa89a222d99e83365a2acb`.
- Source live candidate SHA256: `0f72556e20ed2e22b45f144b4ccf687937e1b15cedc4d2dd109819fef65db7e8`.
- Only changed paths: `index.html`, `__pages/23/englishpt.page`.
- The other **180798/180798** source files have identical SHA1; 158571 public original .html URLs, 21964 indexable, 136607 noindex, 44 child sitemaps+index, 6 real tutoring Forms and 29 OG unchanged.
- Production candidate full ZIP Artifact: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39225996525/artifacts/12174445272
- QA and source-to-target 2-file SHA1 proof Artifact: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39225996525/artifacts/12173707805

## Real immutable Draft QA — PASS

- GitHub Draft job: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39226966032 (SUCCESS 19 steps)
- Draft **ID** `6ad5dce289bf03bfba2b534c`, Netlify project/site ID `98d96cc5-f0b7-4d3d-8072-6476d93e55a3`.
- Actual Draft URL: https://enptgscmetaonceoct19--englishpt-seo.netlify.app
- State `ready`, unmodified currently published live deploy `6ad5ca0f1f2051f04bdd9287`.
- Real GET-only QA: /index.html, /englishpt.html, robots.txt, sitemap-index.xml, and one tutor form page — HTTP 200 with all checks PASS and no errors.
- Actual returned `<head>` has precisely ONE exact Google tag in both the redirect entry and canonical EnglishPT homepage.
- Verifier result Artifact: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39226966032/artifacts/12174352324

## Remaining user decision: publish READY Draft without re-upload

The user needs to authorize posting the **already READY** Draft `6ad5dce289bf03bfba2b534c` as the **new Production** version on `englishpt.kr`. Use a single Netlify restore/publish invocation, NOT another 180k-file upload, only after GET-only gates recheck:

1. The currently published deploy remains `6ad5ca0f1f2051f04bdd9287`, target Google-tag Draft still ready and unpublished, site domain is englishpt.kr and original site rollback deploy `6ac4bd517c30220008bb9661` still ready; independent ZIP backup SHA256 `b490c4a19cb4deb04d3c6dd5927446cbda879991ba581e4654f2d5462686bac5` intact.
2. Netlify credits and Forms detection are green.
3. Issue exactly ONE POST of `/api/v1/sites/98d96cc5-f0b7-4d3d-8072-6476d93e55a3/deploys/6ad5dce289bf03bfba2b534c/restore`, never automatically retry.
4. GET Netlify API published_deploy.id new target; GET https://englishpt.kr/ and https://englishpt.kr/englishpt.html ensuring Google tag in final homepage `<head>`, and GET sitemap, original Forms static and canonical/robots unchanged.
5. User can press **Google Search Console > 소유권 확인** only AFTER confirmed published. HTML tag method applies to URL prefix properties; DNS verification is required for domain-wide property.
6. User's Google Search Console property needs authenticated owner account; cannot mark verified without Google reporting success. Only after owner verification submit `https://englishpt.kr/sitemap-index.xml` and verify acceptance.

**No Production publication occurred during preparation; no Google ownership verification or sitemap submission yet.**
