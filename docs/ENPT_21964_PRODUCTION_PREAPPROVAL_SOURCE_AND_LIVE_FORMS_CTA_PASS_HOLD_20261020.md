# ENGLISH PT — 21,964 Thumbnail Production-Preapproval GO/HOLD Packet
Date: 2026-10-20. **Candidate source QA PASS + existing nonpublished runtime QA PASS; Production publication remains HOLD pending explicit user approval.**

## Source / metadata exhaustive verification — PASS
- Workflow: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39399897235
- Production-safe *source* assembled offline from the signed 180,800-file release plus 21,964 1200x1200 JPG thumbnails, total 202,764 files. Zero Netlify writes or deploy in this workflow.
- Preview-wide protections **not** copied into candidate: no `/* X-Robots-Tag: noindex, nofollow`, no robots `Disallow: /`, no preview router forced `X-Robots-Tag`.
- Original SHA1 + original per-page noindex metadata of **136,607** pages is exactly unchanged.
- **21,964** indexable URLs have their original indexed metadata and canonical, with exactly one planned correct `og:image` and original validated JPEG.
- 44 original sitemap XML shards all SHA1-match. Their canonical URL union equals exactly the 21,964 indexable URLs.
- Google and Naver ownership meta values each occur exactly once on both homepage representations.
- Netlify Forms static registration blueprint, all six sampled 1:1 tutoring forms, original Edge router/TOML, internal .page noindex, 75 301 redirects and `pilot.js` verified unchanged.
- Published Netlify production deploy `6ad5eb4918f9411c4d5e1ba4` verified intact.

## Real URL / browser smoke, existing review draft — PASS
- Workflow: https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39403690222
- Existing READY nonpublished review Draft ID `6ad725447da59d0766b71058`
- Live URL: https://enptog21964clifinalqa20--englishpt-seo.netlify.app/englishpt.html
- 42 actual route HTML responses HTTP 200, matching canonical and **page-level** robots: 18 source-indexable, 24 source-noindex (including six form pages). The preview deliberately adds global `X-Robots-Tag: noindex` *only in review*; this was checked, NOT recommended for Production.
- All six live tutor forms preserve `englishpt-consultation` registration markup and crucial fields `name`, `phone`, `form-name`, `requestType`, `subject`, `consent`.
- Ten actual live image assets SHA256 match signed original 1200x1200 JPEG.
- Real Chrome 390px and 1440px: clicked tutor CTA anchor `#consultation-preview`, scrolled into visible in-page form, confirmed form name/phone and submit UI; screen captures archived in workflow artifact `ENPT_21964_EXISTING_READY_PREVIEW_MIXED_NOINDEX_EDGE_FORMS_390_1440_REAL_GETONLY`.
- Zero email/form submissions, zero production mutations, zero new deployment.
- The tutor CTA is **an anchor to an in-page form, not a modal**. Earlier check expected a modal and failed; subsequent markup diagnosis https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39403472977 and corrected live QA PASS. No site code changes needed.

## Release HOLD: what is not yet proven
1. This real HTTP test targets an intentionally **noindex-protected draft**, while the production-safe bytes have passed **offline** validation. The production-safe exact bytes have not been uploaded as an additional production-intent nonpublished Draft during this step. The existing preview and offline candidate differ only by review-specific safety settings; avoid accidentally publishing preview.
2. No test submission or confirmation email was generated. Markup+click navigation QA does not establish Netlify Forms processing/email delivery for *this future candidate*. Previously working consultation on Production has not been modified.
3. No true 158,571-route HTTP crawl or 21,964 separate live image GET across the entire hosted candidate; exhaustive **offline** metadata/file QA and live representative sample QA have been carried out.
4. Neither Naver nor Google image choice or search indexing can be guaranteed by metadata QA.

## Before Production publish
- Establish immutable production-safe bytes and a unique Netlify **nonpublished** candidate draft with appropriate review-only crawler protection that cannot leak to Production; verify digest + CLI-bundled Edge (older manual Edge TAR had HTTP 502).
- Compare exact source digest/critical robots/Edge/header fingerprints between the candidate artifact and approved preflight.
- Confirm per-page indexed/noindex production semantics in **candidate without accidentally carrying review-wide crawler protection**; use offline parity + review protection as separate layers.
- Verify live mobile home/consultation/representative indexable/noindex/OG image sample; before go-live, verify Forms registration and submission only with explicit user consent for a test notification.
- Keep original production deploy `6ad5eb4918f9411c4d5e1ba4` as rollback ID and preserve Google/Naver verification, 44 sitemaps and current 136,607 noindex rules.
- Request a **new explicit user approval** to publish a specific exact verified draft ID; only after that may Production be modified.

Decision: **SEO source safety GO, sampled live Edge/CTA GO; PRODUCTION PUBLISH HOLD (awaiting exact candidate + explicit approval).**
