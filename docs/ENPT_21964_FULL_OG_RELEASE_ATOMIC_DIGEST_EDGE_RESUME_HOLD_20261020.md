# ENGLISH PT — 21,964 Square Thumbnail Full-Release Safe Transfer Plan (2026-10-20)

Status: **OFFLINE PRE-FLIGHT COMPLETE, PRODUCTION HOLD**. This branch is a read-only preparation branch. Do not merge, deploy or auto-publish it as the site.

## Verified source and amount

- Current Production Deploy: `6ad5eb4918f9411c4d5e1ba4` (both Google and Naver ownership meta retained).
- Original full release archive SHA256: `6d0272d1601a1a47abeccc4d740359af9e7678293ee0a3d257eecd2ca478d884`.
- Original deployed static + Edge members: 180,800.
- Original SEO pages: 158,571 (21,964 indexable, 136,607 noindex).
- Verified square JPEGs: 21,964, aggregate 1,348,681,316 bytes; average 61,404 bytes; each ≤79,089 bytes.
- Original bytes of 21,964 indexable Edge-backed source pages: 751,670,970 bytes.
- Candidate deploy member count before possible bundler-generated files: 202,764.
- Expected changed/added paths in Production-source candidate: 21,964 Edge page content rewrites + 1 index homepage rewrite + 21,964 JPEGs = 43,929.
- 44 child sitemap XML files, Netlify Forms, canonical, `robots.txt`, `_redirects`, `_headers`, `netlify.toml`, and existing Edge router must be preserved.

## NETLIFY GET-only investigation at 2026-10-20 14:25 KST

Previous full-size preview `6ad6daf01389db1fbe596f74`: `state=uploading`; `required` ordinary files **0**; `required_edge_functions` **one**, SHA256 `1359b9c72eadd149ad8cde014235de40b91e0d33e2132c2d5609bf76a6e4653b`. No Production publish occurred. All-files present cannot be independently guaranteed from these fields alone.

The small 150-square-JPEG review `6ad6f4c0202aee7c32247e88` is READY; 150/150 image HTTP SHA256, 150/150 HTML meta links, 390px Chrome Hangul view QA PASS.

Read-only diagnostic: [GitHub Actions 39374853952](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39374853952).

## Correct recovery strategy (avoid repeating 43,932 CLI uploads)

1. **Do not** run another blind `netlify deploy` of the complete 202,764-file source.
2. First reconstruct the missing Edge Function bundle offline and compare its exact SHA256 against `1359...e4653b`. No file or Edge PUT should be sent before the exact bundle hash matches.
3. If reproducible, it is feasible to use Netlify's documented `PUT /api/v1/deploys/{deploy_id}/edge_functions/{code_sha}` for that **unpublished Draft only**. Guard: exact site ID, exact draft ID, unmodified published deploy ID, required ordinary files zero, required Edge code_sha exactly matches, explicit acknowledgement of costs, and verify uploaded binary SHA.
4. GET-only poll same Draft to READY and test actual station Edge rewrites, query canonical/noindex, image HTTP and Forms. The old preview contains **global Draft-only `X-Robots-Tag: noindex, nofollow`** and MUST NOT BE RESTORED/PUBLISHED.
5. Build a separate safe **production-candidate** release without preview global `noindex`. Its content contract must preserve immutable noindex pages (136,607), forms, both search verification meta tags, sitemap and Edge bundle.
6. Use Netlify atomic digest deployment (`async=true` if necessary), only uploads returned `required` SHA1 + required Edge bundle, with bounded concurrency, persistent upload checkpoints and resumable GET reconciliation. Any new API digest and uploads require a deliberate, guarded stage; do not silently run during a GET-only check.
7. Only when all files and Edge Function bundle are READY, visually verify 102px/156px search thumbnails, Chrome 390px, image metadata on 150 diversified samples and 911 station names across all 23 intents, noindex protection on excluded samples, canonical/sitemap/robots, Forms and owner verification.
8. Record before/after Production IDs and rollback deploy. Request explicit Production authorization before final restore.

## Specific risks

- Netlify ZIP uploads have a documented ~25,000-extracted-file constraint, far below the 202,764-member release.
- Edge Router is required to serve the sharded SEO `.page` files. A plain static-only upload can silently cause widespread 404s.
- Preview global noindex is useful for test-only, but catastrophic if carried to Production.
- Color variations on thumbnails do not prove SEO uniqueness or higher search impressions.
- Netlify may report zero ordinary required SHA1 while one required Edge bundle remains; do not declare READY or publish.

**Production stays unchanged until separate signed-off step.**
