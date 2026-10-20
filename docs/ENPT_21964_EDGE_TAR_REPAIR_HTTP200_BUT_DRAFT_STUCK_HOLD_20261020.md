# ENGLISH PT 21,964 Square OG — TAR Edge restored but stale uploading Draft HOLD (2026-10-20)

## Verified repair
- Exact previous production archive hash: `6d0272d1601a1a47abeccc4d740359af9e7678293ee0a3d257eecd2ca478d884`
- Previous nonpublished full-site Draft ID: `6ad6daf01389db1fbe596f74`
- Still-published untouched Production ID: `6ad5eb4918f9411c4d5e1ba4`
- Exact route from original `netlify.toml`: `^/[^/]+[.]html$` via `shard-router`
- Original pinned Netlify CLI 27.13.0 + edge-bundler 16.1.3, `edge_bundler_generate_tarball=true`, reproduced SHA256 `1359b9c72eadd149ad8cde014235de40b91e0d33e2132c2d5609bf76a6e4653b` (2137 bytes). Proven exact Netlify required Edge SHA.
- Exactly ONE binary PUT to this existing Draft's required edge SHA endpoint accepted HTTP **200**; no new Draft, no static file reuploads, no Production publish. Immediately after: `required=[]`, `required_edge_functions=[]`.

## HOLD: unsupported claim of full-site readiness
- Poll 28 times over ~84 seconds: Draft **`uploading`**, still not `ready`.
- Independent GET audit at 2026-10-20T05:57Z: same `uploading`; `updated_at=2026-10-20T03:08:30.944Z`, unchanged since before Edge repair.
- All tested full Draft public URLs returned **HTTP 404**: `/index.html`, `/englishpt.html`, `/sitemap-index.xml`, `/robots.txt`, sampled station TOEIC/IELTS pages, and new square JPEG path.
- **DO NOT PUBLISH THIS DRAFT**. Also contains preview-only global noindex; must never be restored to Production.
- Preserve existing 150-image small Draft: `6ad6f4c0202aee7c32247e88` ready with 150/150 real GET SHA and mobile 390px screenshot successful.

## Next efficient engineering step
1. GET-only audit of complete list of SHA1 files, statuses and expected compiled Edge assets of the stalled Draft (avoid missing `required` being misread as complete site readiness).
2. If precise 202,764+ file digest can be established, prepare a new **draft=true** asynchronous digest deploy with stored SHA hashes and exact TAR Edge code hash. Do not send original 43,932 files again blindly. Guard against missing files, registration metadata and Edge function.
3. Once READY and real HTTP responses PASS, prepare *separate Production-safe* candidate excluding global draft `noindex`; verify 158,571 route mapping, 136,607 noindex routes, 21,964 OG JPEGs, owner meta tags, sitemap, Forms before seeking fresh publication approval.

## Immutable evidence
- [Edge TAR exact SHA match](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39376642291)
- [One Edge PUT HTTP 200, but READY HOLD](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39377221316)
- [Independent HTTP 404 and stagnant Netlify state GET only](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39377660366)
- [150 sample ready draft live image GET and mobile QA](https://github.com/bokdong0801-ui/englishpt-seo/actions/runs/39373161709)
