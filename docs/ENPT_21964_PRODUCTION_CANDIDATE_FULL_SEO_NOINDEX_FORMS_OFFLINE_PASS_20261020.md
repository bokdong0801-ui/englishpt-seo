# ENGLISH PT — 21,964-square-OG Production-Candidate SEO/Forms Safety Verification
Date: 2026-10-20 (KST). **Status: OFFLINE SOURCE QA PASS — NOT AUTHORIZED FOR PRODUCTION.**

## Verifiable execution
[GitHub Actions 39399897235](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39399897235) — success.
Artifact: `ENPT_21964_PRODUCTION_CANDIDATE_ALL_SEO_NOINDEX_OWNER_SITEMAPS_FORMS_OFFLINE_QA` (30-day retention).
Two independent output files:
- `CANDIDATE_21964_SOURCE_PRESERVATION_QA.json`
- `PRODUCTION_CANDIDATE_21964_SEO_NOINDEX_GOOGLE_NAVER_FORMS_QA.json`
Plus `NETLIFY_PRODUCTION_ID_GET_ONLY.json`.

## Construction and source
- Source: *exact SHA256-verified* original approved Netlify publication candidate,
  `6d0272d1601a1a47abeccc4d740359af9e7678293ee0a3d257eecd2ca478d884`
- Rebuilt 21,964 verified SEO square JPEG images plus 21,964 corresponding `og:image` metadata updates to 158,571 original Edge-backed URL set.
- Did **not** apply the preview-only global X-Robots-Tag, `Disallow: /`, or modified router. Source Edge JS and TOML were retained exactly.
- Reconstructed filesystem members: **202,764** = 180,800 original + 21,964 square JPEG.
- Verified source-original Edge JS SHA256:
  `5cb224d7693a92b2b65677bec3dbee780e7c30bcc03fcbeebc6842a873344470`

## Exact PASS evidence
1. **136,607 noindex URLs:** every original sharded payload SHA1 matches; each still has a `noindex` robots meta tag.
2. **21,964 indexable URLs:** each still has an indexable robots meta tag and the exact canonical `https://englishpt.kr/<route>`; each has exactly one planned, verified JPEG `og:image`, 1200x1200 image dimensions and Twitter metadata.
3. **Root index and Edge-sharded homepage:** both retain exactly one Google verification tag and exactly one Naver verification tag with original content. OG metadata present.
4. **Sitemaps:** all 44 sitemap XML shards match their original SHA1; union has 21,964 distinct canonical URLs equal to the exact indexable set. Sitemap index and critical files match original SHA1.
5. **Robots/Edge:** original `robots.txt` has no blanket `Disallow: /`; `_headers` root wildcard has no global noindex; internal `/__pages/*` and `/__internal/*` retain separate noindex rules; original `shard-router.js` removes raw payload `X-Robots-Tag` as intended; original Netlify Edge regex unchanged.
6. **Netlify Forms:** unchanged `__internal/consultation-blueprint.html` has the `englishpt-consultation` form and necessary detection inputs; six tutor page examples retain the form markup and `form-name`, `requestType`, `subject`.
7. **Legacy paths and resources:** 75 original 301 redirects; `pilot.js`, `_redirects`, `_headers`, `netlify.toml`, and original core config unchanged.
8. **Actual Production ID checked via GET only:** `6ad5eb4918f9411c4d5e1ba4` unchanged, domain `englishpt.kr`. No deployment uploads, publication or form submissions.

No QA blockers found. Offline status:
`PASS_LOCAL_PRODUCTION_CANDIDATE_SEO_FORMS_SITEMAPS_NOIDX_OG_ALL`.

## RELEASE HOLD / tests not claimed as done
- This is a **local production-candidate source audit**, **not** the public domain's newly deployed runtime.
- The earlier nonpublished **150-image review** was tested live, including HTTP 200, SHA and Chrome 390px; its **global preview-only noindex** settings must never be copied into Production.
- Full future production runtime 158,571 route HTTP/canonical robots behavior has **not** been re-tested on the new production-candidate build itself.
- No real consultation form submission or email receipt test was performed during this audit; only source markup and static Netlify form detection file were validated.
- No guarantee which image Naver/Google may select from search results.
- The next permitted action is a **guarded prepublication review of final production bytes/Netlify routing**, then separate **explicit user approval** before any Production publish. Keep rollback ID and preservation gates.
